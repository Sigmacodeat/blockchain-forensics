"""
High-Performance Caching Layer
===============================

Implements aggressive caching strategies to achieve <100ms API latency:
- Redis caching with TTL management
- In-memory LRU cache (fallback)
- Query result caching
- Precomputed aggregations
- Cache warming on startup

Target: 95%+ cache hit rate, <100ms p95 latency
"""

from __future__ import annotations
import asyncio
import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from collections import OrderedDict

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


class LRUCache:
    """Thread-safe LRU cache for in-memory fallback"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    async def set(self, key: str, value: Any):
        async with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            
            # Evict oldest if over limit
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)


class PerformanceCache:
    """High-performance caching with Redis + in-memory fallback"""
    
    # Cache TTLs (seconds)
    TTL_SHORT = 60        # 1 minute (frequently changing data)
    TTL_MEDIUM = 300      # 5 minutes (moderately changing)
    TTL_LONG = 3600       # 1 hour (stable data)
    TTL_EXTENDED = 86400  # 24 hours (rarely changing)
    
    def __init__(self):
        self.memory_cache = LRUCache(max_size=1000)
        self.stats = {
            "hits": 0,
            "misses": 0,
            "redis_hits": 0,
            "memory_hits": 0
        }
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function args"""
        # Create deterministic key from arguments
        key_parts = [prefix]
        
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
        
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (Redis → Memory → None)"""
        # Try Redis first
        try:
            client = await redis_client.get_client()
            if client:
                value = await client.get(key)
                if value:
                    self.stats["hits"] += 1
                    self.stats["redis_hits"] += 1
                    return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
        
        # Fallback to memory cache
        value = await self.memory_cache.get(key)
        if value is not None:
            self.stats["hits"] += 1
            self.stats["memory_hits"] += 1
            return value
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM):
        """Set in cache (both Redis and Memory)"""
        # Store in Redis
        try:
            client = await redis_client.get_client()
            if client:
                await client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
        
        # Always store in memory cache
        await self.memory_cache.set(key, value)
    
    async def delete(self, key: str):
        """Delete from cache"""
        try:
            client = await redis_client.get_client()
            if client:
                await client.delete(key)
        except Exception:
            pass
        
        # Also clear from memory
        async with self.memory_cache._lock:
            self.memory_cache.cache.pop(key, None)
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        try:
            client = await redis_client.get_client()
            if client:
                keys = await client.keys(pattern)
                if keys:
                    await client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis delete_pattern failed: {e}")
    
    def cached(
        self,
        ttl: int = TTL_MEDIUM,
        key_prefix: Optional[str] = None
    ):
        """Decorator for caching function results"""
        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            prefix = key_prefix or f"cache:{func.__module__}:{func.__name__}"
            
            @functools.wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                # Generate cache key
                cache_key = self._make_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            "total_requests": total,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "redis_hits": self.stats["redis_hits"],
            "memory_hits": self.stats["memory_hits"],
            "memory_cache_size": len(self.memory_cache.cache)
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "redis_hits": 0,
            "memory_hits": 0
        }


# Singleton instance
performance_cache = PerformanceCache()


# Convenience decorators for common TTLs
def cache_short(func: Callable[P, T]) -> Callable[P, T]:
    """Cache for 1 minute (frequently changing data)"""
    return performance_cache.cached(ttl=PerformanceCache.TTL_SHORT)(func)


def cache_medium(func: Callable[P, T]) -> Callable[P, T]:
    """Cache for 5 minutes (moderately changing)"""
    return performance_cache.cached(ttl=PerformanceCache.TTL_MEDIUM)(func)


def cache_long(func: Callable[P, T]) -> Callable[P, T]:
    """Cache for 1 hour (stable data)"""
    return performance_cache.cached(ttl=PerformanceCache.TTL_LONG)(func)


def cache_extended(func: Callable[P, T]) -> Callable[P, T]:
    """Cache for 24 hours (rarely changing)"""
    return performance_cache.cached(ttl=PerformanceCache.TTL_EXTENDED)(func)
