"""
Multi-Layer Tool Caching System.
Optimizes AI agent tool performance with L1 (in-memory), L2 (Redis), and L3 (Postgres) caching.
Target: <100ms tool execution time.
"""

import logging
import hashlib
import json
import asyncio
from typing import Any, Callable, Optional, Dict
from functools import wraps
from datetime import datetime, timedelta
from cachetools import LRUCache

logger = logging.getLogger(__name__)


class ToolCache:
    """
    Multi-Layer Caching für AI Agent Tools.
    
    Architecture:
    - L1: In-Memory LRU (10MB, <1ms access)
    - L2: Redis (100MB, <10ms access)
    - L3: Postgres (persistent, <50ms access)
    
    Performance Goals:
    - Cache Hit Rate: >80%
    - Average Tool Latency: <100ms
    - L1 Hit: <1ms
    - L2 Hit: <10ms
    - L3 Hit: <50ms
    """
    
    def __init__(self, max_l1_size: int = 1000):
        """
        Initialize multi-layer cache.
        
        Args:
            max_l1_size: Maximum number of entries in L1 cache
        """
        # L1: In-Memory LRU Cache
        self.l1_cache: LRUCache = LRUCache(maxsize=max_l1_size)
        
        # Statistics
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "total_requests": 0,
        }
        
        logger.info(f"✅ ToolCache initialized (L1 size: {max_l1_size})")
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        Generate deterministic cache key from function name and arguments.
        
        Args:
            func_name: Name of the tool function
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            SHA256 hash of serialized key data
        """
        try:
            # Create deterministic key
            key_data = {
                "func": func_name,
                "args": args,
                "kwargs": kwargs
            }
            
            # Serialize with sorted keys for consistency
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            
            # Hash for compact key
            key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
            
            return f"tool:{func_name}:{key_hash}"
            
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            # Fallback: use function name only
            return f"tool:{func_name}:fallback"
    
    def _get_l1(self, key: str) -> Optional[Any]:
        """Get from L1 cache (in-memory)"""
        try:
            value = self.l1_cache.get(key)
            if value is not None:
                self.stats["l1_hits"] += 1
                logger.debug(f"L1 cache HIT: {key}")
            return value
        except Exception as e:
            logger.error(f"L1 cache error: {e}")
            return None
    
    def _set_l1(self, key: str, value: Any) -> None:
        """Set in L1 cache (in-memory)"""
        try:
            self.l1_cache[key] = value
            logger.debug(f"L1 cache SET: {key}")
        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
    
    async def _get_l2(self, key: str) -> Optional[Any]:
        """Get from L2 cache (Redis)"""
        try:
            from app.services.cache_service import cache_service
            
            value = await cache_service.get(key)
            if value is not None:
                self.stats["l2_hits"] += 1
                logger.debug(f"L2 cache HIT: {key}")
                
                # Promote to L1
                self._set_l1(key, value)
            
            return value
            
        except Exception as e:
            logger.error(f"L2 cache error: {e}")
            return None
    
    async def _set_l2(self, key: str, value: Any, ttl: int) -> None:
        """Set in L2 cache (Redis)"""
        try:
            from app.services.cache_service import cache_service
            
            await cache_service.set(key, value, ttl=ttl)
            logger.debug(f"L2 cache SET: {key} (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
    
    async def _get_l3(self, key: str) -> Optional[Any]:
        """Get from L3 cache (Postgres - persistent)"""
        try:
            from app.db.postgres import postgres_client
            
            # Check if table exists
            result = await postgres_client.fetchrow("""
                SELECT value, expires_at 
                FROM tool_cache 
                WHERE key = $1 
                AND (expires_at IS NULL OR expires_at > NOW())
            """, key)
            
            if result:
                self.stats["l3_hits"] += 1
                logger.debug(f"L3 cache HIT: {key}")
                
                # Parse value
                value = json.loads(result["value"])
                
                # Promote to L2 and L1
                self._set_l1(key, value)
                await self._set_l2(key, value, ttl=300)  # 5 min in L2
                
                return value
            
            return None
            
        except Exception as e:
            logger.error(f"L3 cache error: {e}")
            return None
    
    async def _set_l3(self, key: str, value: Any, ttl: Optional[int]) -> None:
        """Set in L3 cache (Postgres)"""
        try:
            from app.db.postgres import postgres_client
            
            value_json = json.dumps(value, default=str)
            expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
            
            await postgres_client.execute("""
                INSERT INTO tool_cache (key, value, created_at, expires_at)
                VALUES ($1, $2, NOW(), $3)
                ON CONFLICT (key) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    created_at = NOW(),
                    expires_at = EXCLUDED.expires_at
            """, key, value_json, expires_at)
            
            logger.debug(f"L3 cache SET: {key}")
            
        except Exception as e:
            logger.error(f"L3 cache set error: {e}")
    
    async def get(
        self,
        func_name: str,
        args: tuple,
        kwargs: dict,
        use_l1: bool = True,
        use_l2: bool = True,
        use_l3: bool = False
    ) -> Optional[Any]:
        """
        Get value from cache (multi-layer).
        
        Args:
            func_name: Tool function name
            args: Function arguments
            kwargs: Function keyword arguments
            use_l1: Check L1 cache
            use_l2: Check L2 cache
            use_l3: Check L3 cache (persistent)
        
        Returns:
            Cached value or None if not found
        """
        self.stats["total_requests"] += 1
        
        key = self._generate_key(func_name, args, kwargs)
        
        # L1: In-Memory (fastest)
        if use_l1:
            value = self._get_l1(key)
            if value is not None:
                return value
        
        # L2: Redis (fast)
        if use_l2:
            value = await self._get_l2(key)
            if value is not None:
                return value
        
        # L3: Postgres (persistent)
        if use_l3:
            value = await self._get_l3(key)
            if value is not None:
                return value
        
        # Cache miss
        self.stats["misses"] += 1
        return None
    
    async def set(
        self,
        func_name: str,
        args: tuple,
        kwargs: dict,
        value: Any,
        ttl: int = 300,
        use_l1: bool = True,
        use_l2: bool = True,
        use_l3: bool = False
    ) -> None:
        """
        Set value in cache (multi-layer).
        
        Args:
            func_name: Tool function name
            args: Function arguments
            kwargs: Function keyword arguments
            value: Value to cache
            ttl: Time to live in seconds
            use_l1: Store in L1 cache
            use_l2: Store in L2 cache
            use_l3: Store in L3 cache
        """
        key = self._generate_key(func_name, args, kwargs)
        
        # Store in all enabled layers
        if use_l1:
            self._set_l1(key, value)
        
        if use_l2:
            await self._set_l2(key, value, ttl)
        
        if use_l3:
            await self._set_l3(key, value, ttl)
    
    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "tool:risk_score:*")
        
        Returns:
            Number of keys invalidated
        """
        count = 0
        
        try:
            # L1: Clear matching keys
            keys_to_remove = [k for k in self.l1_cache.keys() if pattern.replace("*", "") in k]
            for key in keys_to_remove:
                del self.l1_cache[key]
                count += 1
            
            # L2: Redis pattern delete
            from app.services.cache_service import cache_service
            await cache_service.delete_pattern(pattern)
            
            # L3: Postgres pattern delete
            from app.db.postgres import postgres_client
            await postgres_client.execute(
                "DELETE FROM tool_cache WHERE key LIKE $1",
                pattern.replace("*", "%")
            )
            
            logger.info(f"Invalidated cache pattern: {pattern} ({count} L1 keys)")
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats["total_requests"]
        if total == 0:
            hit_rate = 0.0
        else:
            hits = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]
            hit_rate = (hits / total) * 100
        
        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "l1_size": len(self.l1_cache)
        }
    
    def cached_tool(
        self,
        ttl: int = 300,
        use_l1: bool = True,
        use_l2: bool = True,
        use_l3: bool = False
    ):
        """
        Decorator for caching tool results.
        
        Usage:
            @tool_cache.cached_tool(ttl=600)
            @tool("my_tool")
            async def my_tool_func(address: str):
                # expensive operation
                return result
        
        Args:
            ttl: Time to live in seconds
            use_l1: Use L1 cache
            use_l2: Use L2 cache
            use_l3: Use L3 cache (persistent)
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Try cache first
                cached = await self.get(
                    func.__name__,
                    args,
                    kwargs,
                    use_l1=use_l1,
                    use_l2=use_l2,
                    use_l3=use_l3
                )
                
                if cached is not None:
                    logger.debug(f"Cache HIT for {func.__name__}")
                    return cached
                
                # Cache miss - execute function
                logger.debug(f"Cache MISS for {func.__name__}")
                result = await func(*args, **kwargs)
                
                # Store in cache (fire-and-forget)
                asyncio.create_task(self.set(
                    func.__name__,
                    args,
                    kwargs,
                    result,
                    ttl=ttl,
                    use_l1=use_l1,
                    use_l2=use_l2,
                    use_l3=use_l3
                ))
                
                return result
            
            return wrapper
        return decorator


# Global singleton instance
tool_cache = ToolCache(max_l1_size=1000)


# Convenience decorator
def cached_tool(ttl: int = 300, use_l1: bool = True, use_l2: bool = True, use_l3: bool = False):
    """
    Convenience decorator for tool caching.
    
    Usage:
        from app.ai_agents.performance.tool_cache import cached_tool
        
        @cached_tool(ttl=600)
        @tool("my_tool")
        async def my_tool_func(address: str):
            return {"result": "expensive computation"}
    """
    return tool_cache.cached_tool(ttl=ttl, use_l1=use_l1, use_l2=use_l2, use_l3=use_l3)


logger.info("✅ Tool Cache System initialized")
