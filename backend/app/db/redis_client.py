"""
Redis Client
Für Caching, Idempotency Keys, Rate Limiting und Session Storage
"""

import logging
import json
from typing import Optional, Any, Dict
try:
    from redis import asyncio as aioredis  # type: ignore
    _REDIS_AVAILABLE = True
except Exception:
    aioredis = None  # type: ignore
    _REDIS_AVAILABLE = False
from datetime import timedelta

from app.config import settings
from app.metrics import (
    WORKER_STATUS,
    WORKER_PROCESSED_TOTAL,
    WORKER_ERRORS_TOTAL,
    WORKER_LAST_HEARTBEAT,
)

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis Client für Caching und Session Management"""
    
    # Key prefixes
    CACHE_PREFIX = "cache:"
    IDEMPOTENCY_PREFIX = "idempotency:"
    RATE_LIMIT_PREFIX = "ratelimit:"
    SESSION_PREFIX = "session:"
    TRACE_RESULT_PREFIX = "trace:"
    
    # Worker monitoring
    WORKER_PREFIX = "worker:hb:"

    def __init__(self):
        # Use broad typing to avoid NameError when aioredis is not available
        self.client: Optional[Any] = None
        logger.info("Redis client initialized")
    
    async def connect(self):
        """Establish Redis connection"""
        # Skip connecting when running tests or when redis dependency is not available
        if (not _REDIS_AVAILABLE) or (getattr(settings, "TEST_MODE", False) or __import__("os").getenv("PYTEST_CURRENT_TEST")):
            logger.warning("Redis connect skipped (test mode or redis not available)")
            return
        if not self.client and _REDIS_AVAILABLE and aioredis is not None:
            try:
                self.client = await aioredis.from_url(  # type: ignore[attr-defined]
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis connected")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis disconnected")
    
    async def _ensure_connected(self):
        """Ensure Redis is connected"""
        # No-op in tests or when redis is not installed
        if (not _REDIS_AVAILABLE) or (getattr(settings, "TEST_MODE", False) or __import__("os").getenv("PYTEST_CURRENT_TEST")):
            return
        if not self.client:
            await self.connect()
    
    # Cache Operations
    async def cache_get(self, key: str) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        await self._ensure_connected()
        client = self.client
        if client is None:
            return None
        value = await client.get(f"{self.CACHE_PREFIX}{key}")
        
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ):
        """
        Set cache value with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 1 hour)
        """
        await self._ensure_connected()
        client = self.client
        if client is None:
            return
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        await client.setex(
            f"{self.CACHE_PREFIX}{key}",
            ttl,
            value
        )

    # Worker Heartbeats
    async def set_worker_heartbeat(self, name: str, payload: Dict[str, Any], ttl: int = 120) -> None:
        """Store a worker heartbeat payload with TTL.

        Key: worker:hb:{name}
        """
        await self._ensure_connected()
        client = self.client
        if client is None:
            return
        key = f"{self.WORKER_PREFIX}{name}"
        try:
            await client.setex(key, ttl, json.dumps(payload, default=str))
            # Update Prometheus worker metrics
            status = str(payload.get("status", "unknown")).lower()
            is_ok = 1.0 if status in ("running", "ok") else 0.0
            try:
                WORKER_STATUS.labels(worker=name).set(is_ok)
                # Counters: only increment when values increase
                processed = int(payload.get("processed_count", 0) or 0)
                errors = int(payload.get("error_count", 0) or 0)
                if processed:
                    WORKER_PROCESSED_TOTAL.labels(worker=name).inc(processed)
                if errors:
                    WORKER_ERRORS_TOTAL.labels(worker=name).inc(errors)
                # Last heartbeat timestamp
                from datetime import datetime as _dt
                ts_iso = payload.get("last_heartbeat")
                ts = _dt.fromisoformat(ts_iso).timestamp() if isinstance(ts_iso, str) else None
                if ts:
                    WORKER_LAST_HEARTBEAT.labels(worker=name).set(ts)
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Failed to set worker heartbeat {name}: {e}")

    async def get_worker_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get last heartbeat payload for a worker by name."""
        await self._ensure_connected()
        client = self.client
        if client is None:
            return None
        key = f"{self.WORKER_PREFIX}{name}"
        try:
            value = await client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Failed to get worker heartbeat {name}: {e}")
            return None

    async def list_worker_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Return all worker heartbeats keyed by worker name.

        Uses SCAN to iterate keys matching worker:hb:*
        """
        await self._ensure_connected()
        client = self.client
        results: Dict[str, Dict[str, Any]] = {}
        if client is None:
            return results
        try:
            # Use async scan iterator if available
            cursor = 0
            pattern = f"{self.WORKER_PREFIX}*"
            while True:
                cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    values = await client.mget(keys)
                    for k, v in zip(keys, values):
                        try:
                            name = k.replace(self.WORKER_PREFIX, "", 1)
                            results[name] = json.loads(v) if v else {}
                        except Exception:
                            continue
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Failed to list worker heartbeats: {e}")
        return results
    
    async def cache_delete(self, key: str):
        """Delete cache entry"""
        await self._ensure_connected()
        client = self.client
        if client is None:
            return
        await client.delete(f"{self.CACHE_PREFIX}{key}")
    
    async def clear_cache(self) -> int:
        """Clear all cache entries with the CACHE_PREFIX using SCAN.
        Returns number of deleted keys.
        """
        await self._ensure_connected()
        client = self.client
        if client is None:
            return 0
        deleted = 0
        try:
            cursor = 0
            pattern = f"{self.CACHE_PREFIX}*"
            while True:
                cursor, keys = await client.scan(cursor=cursor, match=pattern, count=200)
                if keys:
                    if len(keys) == 1:
                        deleted += int(await client.delete(keys[0]))
                    else:
                        # mdel not available; pipeline for efficiency
                        pipe = client.pipeline()
                        for k in keys:
                            pipe.delete(k)
                        results = await pipe.execute()
                        deleted += sum(int(bool(r)) for r in results)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Failed to clear cache namespace: {e}")
        return deleted
    
    async def clear_by_prefix(self, prefix: str, count: int = 200) -> int:
        """Delete keys by arbitrary prefix using SCAN. Returns number of deleted keys."""
        await self._ensure_connected()
        client = self.client
        if client is None:
            return 0
        deleted = 0
        try:
            cursor = 0
            pattern = f"{prefix}*"
            while True:
                cursor, keys = await client.scan(cursor=cursor, match=pattern, count=count)
                if keys:
                    if len(keys) == 1:
                        deleted += int(await client.delete(keys[0]))
                    else:
                        pipe = client.pipeline()
                        for k in keys:
                            pipe.delete(k)
                        results = await pipe.execute()
                        deleted += sum(int(bool(r)) for r in results)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Failed to clear keys by prefix '{prefix}': {e}")
        return deleted
    
    # Idempotency
    async def check_idempotency(
        self,
        idempotency_key: str,
        ttl: int = 86400  # 24 hours
    ) -> Optional[Dict]:
        """
        Check if request with idempotency key was already processed
        
        **Use Case:**
        - Prevent duplicate trace requests
        - Ensure exactly-once processing
        
        Returns:
            Previous result if exists, None otherwise
        """
        await self._ensure_connected()
        client = self.client
        if client is None:
            return None
        key = f"{self.IDEMPOTENCY_PREFIX}{idempotency_key}"
        value = await client.get(key)
        
        if value:
            return json.loads(value)
        return None
    
    async def store_idempotency_result(
        self,
        idempotency_key: str,
        result: Dict,
        ttl: int = 86400
    ):
        """Store result for idempotency check"""
        await self._ensure_connected()
        client = self.client
        if client is None:
            return
        key = f"{self.IDEMPOTENCY_PREFIX}{idempotency_key}"
        await client.setex(
            key,
            ttl,
            json.dumps(result)
        )
    
    # Rate Limiting
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int = 60
    ) -> bool:
        """
        Check if rate limit is exceeded
        
        Args:
            identifier: User/IP identifier
            limit: Max requests
            window: Time window in seconds
        
        Returns:
            True if under limit, False if exceeded
        """
        await self._ensure_connected()
        client = self.client
        if client is None:
            return False
        key = f"{self.RATE_LIMIT_PREFIX}{identifier}"
        
        current = await client.get(key)
        
        if current is None:
            # First request in window
            await client.setex(key, window, 1)
            return True
        
        current = int(current)
        
        if current >= limit:
            return False
        
        await client.incr(key)
        return True
    
    # Trace Results Storage
    async def store_trace_result(
        self,
        trace_id: str,
        result: Dict,
        ttl: int = 86400  # 24 hours
    ):
        """
        Store trace result temporarily
        
        **Use Case:**
        - Fast retrieval of recent traces
        - Reduce Neo4j queries
        - API response caching
        """
        await self._ensure_connected()
        client = self.client
        if client is None:
            return
        key = f"{self.TRACE_RESULT_PREFIX}{trace_id}"
        await client.setex(
            key,
            ttl,
            json.dumps(result, default=str)
        )
    
    async def get_trace_result(self, trace_id: str) -> Optional[Dict]:
        """Get cached trace result"""
        await self._ensure_connected()
        client = self.client
        if client is None:
            return None
        key = f"{self.TRACE_RESULT_PREFIX}{trace_id}"
        value = await client.get(key)
        
        if value:
            return json.loads(value)
        return None
    
    # Session Management
    async def create_session(
        self,
        session_id: str,
        data: Dict,
        ttl: int = 3600
    ):
        """Create user session"""
        await self._ensure_connected()
        client = self.client
        if client is None:
            return
        key = f"{self.SESSION_PREFIX}{session_id}"
        await client.setex(
            key,
            ttl,
            json.dumps(data)
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        await self._ensure_connected()
        client = self.client
        if client is None:
            return None
        key = f"{self.SESSION_PREFIX}{session_id}"
        value = await client.get(key)
        
        if value:
            return json.loads(value)
        return None
    
    async def delete_session(self, session_id: str):
        """Delete session"""
        await self._ensure_connected()
        client = self.client
        if client is None:
            return
        key = f"{self.SESSION_PREFIX}{session_id}"
        await client.delete(key)
    
    # Health Check
    async def verify_connectivity(self) -> bool:
        """Verify Redis connection"""
        try:
            # In tests, report healthy to avoid hard dependency
            if settings.TEST_MODE or __import__("os").getenv("PYTEST_CURRENT_TEST"):
                return True
            if not _REDIS_AVAILABLE:
                logger.warning("Redis not available: verify_connectivity -> False")
                return False
            await self._ensure_connected()
            client = self.client
            if client is None:
                return False
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connectivity check failed: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        await self.disconnect()


# Singleton instance
redis_client = RedisClient()
