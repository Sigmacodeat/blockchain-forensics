"""
Advanced Cache Manager
======================

Multi-layer caching with Redis, in-memory, and intelligent invalidation

Features:
- Multi-layer caching (Redis + in-memory)
- Smart cache invalidation
- Cache warming
- TTL management
- Hit rate tracking
"""

import logging
import hashlib
import json
import pickle
from typing import Any, Optional, Callable, Dict
from datetime import datetime, timedelta
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Advanced multi-layer cache management
    
    **Layers:**
    1. In-memory (fastest, ~1ms)
    2. Redis (fast, ~5-10ms)
    3. Database fallback
    
    **Features:**
    - Automatic cache warming
    - Intelligent invalidation
    - Cache hit rate tracking
    - TTL management
    - Compression for large objects
    """
    
    def __init__(self):
        self.local_cache: Dict[str, Any] = {}
        self.local_cache_ttl: Dict[str, datetime] = {}
        self.max_local_cache_size = 1000
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'local_hits': 0,
            'redis_hits': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate deterministic cache key"""
        key_parts = [str(prefix)]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        
        key_string = ":".join(key_parts)
        
        # Hash if too long
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_string
    
    async def get(
        self,
        key: str,
        default: Any = None,
        use_local: bool = True
    ) -> Optional[Any]:
        """
        Get value from cache (multi-layer)
        
        Args:
            key: Cache key
            default: Default value if not found
            use_local: Check local cache first
        
        Returns:
            Cached value or default
        """
        # Layer 1: Local in-memory cache
        if use_local and key in self.local_cache:
            # Check TTL
            if key in self.local_cache_ttl:
                if datetime.utcnow() < self.local_cache_ttl[key]:
                    self.stats['hits'] += 1
                    self.stats['local_hits'] += 1
                    logger.debug(f"Cache HIT (local): {key}")
                    return self.local_cache[key]
                else:
                    # Expired - remove
                    del self.local_cache[key]
                    del self.local_cache_ttl[key]
        
        # Layer 2: Redis cache
        try:
            from app.db.redis_client import redis_client
            
            value = await redis_client.get(key)
            
            if value is not None:
                self.stats['hits'] += 1
                self.stats['redis_hits'] += 1
                logger.debug(f"Cache HIT (redis): {key}")
                
                # Deserialize
                try:
                    deserialized = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Try pickle for complex objects
                    try:
                        deserialized = pickle.loads(value)
                    except:
                        deserialized = value
                
                # Store in local cache for next time
                if use_local:
                    self._add_to_local_cache(key, deserialized, ttl_seconds=60)
                
                return deserialized
        
        except Exception as e:
            logger.error(f"Redis cache error: {e}")
        
        # Cache miss
        self.stats['misses'] += 1
        logger.debug(f"Cache MISS: {key}")
        return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 300,
        use_local: bool = True
    ):
        """
        Set value in cache (multi-layer)
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (default 5 min)
            use_local: Also store in local cache
        """
        self.stats['sets'] += 1
        
        # Store in Redis
        try:
            from app.db.redis_client import redis_client
            
            # Serialize
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                # Use pickle for non-JSON serializable objects
                serialized = pickle.dumps(value)
            
            await redis_client.set(key, serialized, ex=ttl_seconds)
            logger.debug(f"Cache SET (redis): {key} (TTL: {ttl_seconds}s)")
        
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")
        
        # Store in local cache
        if use_local:
            self._add_to_local_cache(key, value, ttl_seconds)
    
    def _add_to_local_cache(self, key: str, value: Any, ttl_seconds: int):
        """Add to local in-memory cache"""
        # Check size limit
        if len(self.local_cache) >= self.max_local_cache_size:
            # Evict oldest
            self._evict_local_cache()
        
        self.local_cache[key] = value
        self.local_cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        logger.debug(f"Cache SET (local): {key}")
    
    def _evict_local_cache(self):
        """Evict oldest entries from local cache"""
        if not self.local_cache_ttl:
            return
        
        # Remove 10% oldest entries
        num_to_evict = max(1, len(self.local_cache) // 10)
        
        # Sort by expiry time
        sorted_keys = sorted(
            self.local_cache_ttl.keys(),
            key=lambda k: self.local_cache_ttl[k]
        )
        
        for key in sorted_keys[:num_to_evict]:
            del self.local_cache[key]
            del self.local_cache_ttl[key]
            self.stats['evictions'] += 1
    
    async def delete(self, key: str):
        """Delete from all cache layers"""
        self.stats['deletes'] += 1
        
        # Remove from local
        if key in self.local_cache:
            del self.local_cache[key]
            if key in self.local_cache_ttl:
                del self.local_cache_ttl[key]
        
        # Remove from Redis
        try:
            from app.db.redis_client import redis_client
            await redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        try:
            from app.db.redis_client import redis_client
            
            # Get matching keys
            keys = []
            async for key in redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Deleted {len(keys)} keys matching pattern: {pattern}")
            
            # Also clear matching local cache entries
            local_keys_to_delete = [
                k for k in self.local_cache.keys()
                if self._pattern_match(k, pattern)
            ]
            
            for key in local_keys_to_delete:
                del self.local_cache[key]
                if key in self.local_cache_ttl:
                    del self.local_cache_ttl[key]
        
        except Exception as e:
            logger.error(f"Delete pattern error: {e}")
    
    def _pattern_match(self, key: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)"""
        import re
        regex_pattern = pattern.replace('*', '.*')
        return re.match(f"^{regex_pattern}$", key) is not None
    
    async def warm_cache(
        self,
        key: str,
        loader_func: Callable,
        ttl_seconds: int = 300
    ):
        """
        Warm cache by preloading data
        
        Args:
            key: Cache key
            loader_func: Function to load data
            ttl_seconds: TTL
        """
        try:
            # Check if already cached
            existing = await self.get(key)
            if existing is not None:
                logger.debug(f"Cache already warm: {key}")
                return
            
            # Load data
            logger.info(f"Warming cache: {key}")
            data = await loader_func() if asyncio.iscoroutinefunction(loader_func) else loader_func()
            
            # Cache it
            await self.set(key, data, ttl_seconds)
            
        except Exception as e:
            logger.error(f"Cache warming failed for {key}: {e}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': self.stats['hits'] / total_requests if total_requests > 0 else 0,
            'local_cache_size': len(self.local_cache),
            'local_cache_hit_rate': (
                self.stats['local_hits'] / self.stats['hits']
                if self.stats['hits'] > 0 else 0
            )
        }
    
    def clear_local_cache(self):
        """Clear local in-memory cache"""
        self.local_cache.clear()
        self.local_cache_ttl.clear()
        logger.info("Local cache cleared")
    
    async def clear_all(self):
        """Clear all caches"""
        self.clear_local_cache()
        
        try:
            from app.db.redis_client import redis_client
            await redis_client.flushdb()
            logger.warning("Redis cache flushed (all data deleted)")
        except Exception as e:
            logger.error(f"Redis flush error: {e}")


# Singleton instance
cache_manager = CacheManager()


# Caching decorator
def cached(
    key_prefix: str,
    ttl_seconds: int = 300,
    use_local: bool = True
):
    """
    Decorator for caching function results
    
    Usage:
        @cached(key_prefix="address_data", ttl_seconds=600)
        async def get_address_data(address: str):
            # ... expensive operation
            return data
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                key_prefix, *args, **kwargs
            )
            
            # Try cache first
            cached_value = await cache_manager.get(
                cache_key,
                use_local=use_local
            )
            
            if cached_value is not None:
                return cached_value
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(
                cache_key,
                result,
                ttl_seconds=ttl_seconds,
                use_local=use_local
            )
            
            return result
        
        return wrapper
    return decorator
