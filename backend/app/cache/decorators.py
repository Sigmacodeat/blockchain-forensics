"""
Caching Decorators
Redis-based caching for functions
"""

import logging
import functools
import json
from typing import Callable, Any, Optional
import hashlib

logger = logging.getLogger(__name__)


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """
    Cache function result in Redis
    
    **Usage:**
    ```python
    @cache_result(ttl=300, key_prefix="labels")
    async def get_labels(address: str):
        # Expensive operation
        return labels
    ```
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name + args
            key_parts = [key_prefix or func.__name__]
            
            # Add positional args
            key_parts.extend(str(arg) for arg in args)
            
            # Add keyword args (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            # Create hash for long keys
            key_str = ":".join(key_parts)
            if len(key_str) > 100:
                key_hash = hashlib.md5(key_str.encode()).hexdigest()
                cache_key = f"{key_prefix}:{key_hash}"
            else:
                cache_key = key_str
            
            # Try to get from cache
            try:
                from app.db.redis_client import redis_client
                
                cached = await redis_client.cache_get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached
                
                # Cache miss - execute function
                logger.debug(f"Cache MISS: {cache_key}")
                result = await func(*args, **kwargs)
                
                # Store in cache
                await redis_client.cache_set(cache_key, result, ttl)
                
                return result
                
            except Exception as e:
                logger.warning(f"Cache error: {e}. Executing without cache.")
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str):
    """
    Invalidate cache entries
    
    **Usage:**
    ```python
    await invalidate_cache("labels:0x123...")
    ```
    """
    async def invalidator(*args, **kwargs):
        try:
            from app.db.redis_client import redis_client
            deleted = await redis_client.clear_by_prefix(key_prefix)
            logger.info(f"Cache invalidated for prefix '{key_prefix}', deleted={deleted}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    return invalidator
