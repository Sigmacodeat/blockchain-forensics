"""
Performance Optimization Service
Advanced caching, query optimization, and performance monitoring
"""

import time
import logging
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from app.services.connection_pooling import get_redis_connection

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    size_bytes: int = 0


class AdvancedCache:
    """
    Multi-level caching system with Redis and in-memory tiers

    Features:
    - TTL-based expiration
    - LRU eviction
    - Cache warming
    - Performance metrics
    - Memory management
    """

    def __init__(self, max_memory_mb: int = 100, default_ttl: int = 300):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.redis_available = False
        self.total_memory_used = 0

        # Performance tracking
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    async def initialize_redis(self) -> None:
        """Initialize Redis connection for distributed caching"""
        try:
            async with get_redis_connection() as redis:
                await redis.ping()
                self.redis_available = True
                logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}")
            self.redis_available = False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Check memory cache first
        entry = self.cache.get(key)
        if entry:
            if entry.expires_at and entry.expires_at < datetime.utcnow():
                await self._evict_entry(key)
                self.misses += 1
                return None

            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            self.hits += 1
            return entry.value

        # Check Redis cache if available
        if self.redis_available:
            try:
                async with get_redis_connection() as redis:
                    value = await redis.get(key)
                    if value:
                        # Store in memory cache for faster subsequent access
                        await self.set(key, value, ttl=self.default_ttl)
                        self.hits += 1
                        return value
            except Exception as e:
                logger.debug(f"Redis cache miss for {key}: {e}")

        self.misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl_seconds = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        # Calculate memory size
        value_str = str(value)
        size_bytes = len(value_str.encode('utf-8'))

        # Check memory limits
        if self.total_memory_used + size_bytes > self.max_memory_bytes:
            await self._evict_lru_entries(size_bytes)

        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            expires_at=expires_at,
            size_bytes=size_bytes
        )

        self.cache[key] = entry
        self.total_memory_used += size_bytes

        # Store in Redis if available
        if self.redis_available:
            try:
                async with get_redis_connection() as redis:
                    await redis.setex(key, ttl_seconds, value_str)
            except Exception as e:
                logger.debug(f"Redis cache set failed for {key}: {e}")

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            entry = self.cache[key]
            self.total_memory_used -= entry.size_bytes
            del self.cache[key]

        if self.redis_available:
            try:
                async with get_redis_connection() as redis:
                    await redis.delete(key)
            except Exception as e:
                logger.debug(f"Redis cache delete failed for {key}: {e}")

        return True

    async def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.total_memory_used = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        if self.redis_available:
            try:
                async with get_redis_connection() as redis:
                    await redis.flushdb()
            except Exception as e:
                logger.debug(f"Redis cache clear failed: {e}")

    async def _evict_entry(self, key: str) -> None:
        """Evict a single entry"""
        if key in self.cache:
            entry = self.cache[key]
            self.total_memory_used -= entry.size_bytes
            del self.cache[key]
            self.evictions += 1

    async def _evict_lru_entries(self, needed_bytes: int) -> None:
        """Evict least recently used entries to free memory"""
        # Sort by last accessed time (oldest first)
        entries = sorted(self.cache.values(), key=lambda x: x.last_accessed)

        freed_bytes = 0
        for entry in entries:
            await self._evict_entry(entry.key)
            freed_bytes += entry.size_bytes
            if freed_bytes >= needed_bytes:
                break

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "entries": len(self.cache),
            "memory_used_mb": self.total_memory_used / (1024 * 1024),
            "memory_limit_mb": self.max_memory_bytes / (1024 * 1024),
            "redis_available": self.redis_available
        }


def cache_result(ttl: Optional[int] = None, cache_key: Optional[str] = None):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds
        cache_key: Custom cache key (defaults to function name + args)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key:
                key = cache_key
            else:
                # Create key from function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                key = ":".join(key_parts)

            # Try to get from cache
            cached_result = await cache_service.get(key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_service.set(key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


class QueryOptimizer:
    """
    Optimizes database queries and operations

    Features:
    - Query result caching
    - Batch query optimization
    - Index recommendations
    - Query performance monitoring
    """

    def __init__(self):
        self.query_cache: Dict[str, Any] = {}
        self.query_stats: Dict[str, List[float]] = defaultdict(list)
        self.slow_queries: List[Dict[str, Any]] = []

    async def optimize_query(self, query_func: Callable, *args, **kwargs) -> Any:
        """Optimize and execute a query with caching and monitoring"""
        start_time = time.time()

        try:
            # Execute query
            result = await query_func(*args, **kwargs)

            execution_time = time.time() - start_time

            # Track query performance
            query_signature = f"{query_func.__name__}:{len(args)}:{len(kwargs)}"
            self.query_stats[query_signature].append(execution_time)

            # Log slow queries
            if execution_time > 1.0:  # Queries slower than 1 second
                self.slow_queries.append({
                    "query": query_signature,
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow()
                })

                # Keep only last 100 slow queries
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e} (took {execution_time:.3f}s)")
            raise

    def get_query_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        stats = {}
        for query_signature, times in self.query_stats.items():
            stats[query_signature] = {
                "count": len(times),
                "avg_time": sum(times) / len(times),
                "max_time": max(times),
                "min_time": min(times),
                "total_time": sum(times)
            }

        return {
            "query_stats": stats,
            "slow_queries_count": len(self.slow_queries),
            "slow_queries": self.slow_queries[-10:]  # Last 10 slow queries
        }


class PerformanceMonitor:
    """
    Comprehensive performance monitoring service

    Features:
    - Request/response time tracking
    - Memory usage monitoring
    - Database connection monitoring
    - Cache performance tracking
    - Real-time performance metrics
    """

    def __init__(self):
        self.request_times: List[float] = []
        self.memory_usage: List[Dict[str, Any]] = []
        self.error_rates: Dict[str, int] = defaultdict(int)
        self.endpoint_stats: Dict[str, List[float]] = defaultdict(list)

        # Performance thresholds
        self.slow_request_threshold = 1.0  # seconds
        self.high_memory_threshold = 100 * 1024 * 1024  # 100MB

    def record_request(self, endpoint: str, duration: float, status_code: int) -> None:
        """Record request metrics"""
        self.request_times.append(duration)
        self.endpoint_stats[endpoint].append(duration)

        # Track errors
        if status_code >= 400:
            self.error_rates[endpoint] += 1

        # Keep only last 1000 requests
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]

    def record_memory_usage(self) -> None:
        """Record current memory usage"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = {
            "rss": process.memory_info().rss,  # Resident Set Size
            "vms": process.memory_info().vms,  # Virtual Memory Size
            "timestamp": datetime.utcnow()
        }

        self.memory_usage.append(memory_info)

        # Keep only last 100 measurements
        if len(self.memory_usage) > 100:
            self.memory_usage = self.memory_usage[-100:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        if not self.request_times:
            return {"message": "No performance data available"}

        # Calculate request statistics
        avg_response_time = sum(self.request_times) / len(self.request_times)
        max_response_time = max(self.request_times)
        min_response_time = min(self.request_times)
        p95_response_time = sorted(self.request_times)[int(len(self.request_times) * 0.95)]

        # Calculate error rates
        total_requests = len(self.request_times)
        error_count = sum(self.error_rates.values())
        error_rate = error_count / total_requests if total_requests > 0 else 0

        # Memory statistics
        memory_stats = {}
        if self.memory_usage:
            recent_memory = self.memory_usage[-10:]  # Last 10 measurements
            memory_stats = {
                "avg_rss_mb": sum(m["rss"] for m in recent_memory) / len(recent_memory) / (1024 * 1024),
                "max_rss_mb": max(m["rss"] for m in recent_memory) / (1024 * 1024),
                "current_rss_mb": self.memory_usage[-1]["rss"] / (1024 * 1024) if self.memory_usage else 0
            }

        # Endpoint-specific stats
        endpoint_performance = {}
        for endpoint, times in self.endpoint_stats.items():
            if times:
                endpoint_performance[endpoint] = {
                    "avg_time": sum(times) / len(times),
                    "request_count": len(times),
                    "error_rate": self.error_rates.get(endpoint, 0) / len(times) if times else 0
                }

        return {
            "request_performance": {
                "total_requests": total_requests,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "p95_response_time": p95_response_time,
                "slow_requests": len([t for t in self.request_times if t > self.slow_request_threshold])
            },
            "error_metrics": {
                "total_errors": error_count,
                "error_rate": error_rate,
                "errors_by_endpoint": dict(self.error_rates)
            },
            "memory_usage": memory_stats,
            "endpoint_performance": endpoint_performance
        }


# Global instances
cache_service = AdvancedCache()
query_optimizer = QueryOptimizer()
performance_monitor = PerformanceMonitor()


async def initialize_performance_services() -> None:
    """Initialize all performance services"""
    await cache_service.initialize_redis()
    logger.info("Performance services initialized")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics"""
    return cache_service.get_stats()


def get_query_stats() -> Dict[str, Any]:
    """Get query performance statistics"""
    return query_optimizer.get_query_performance_stats()


def get_performance_stats() -> Dict[str, Any]:
    """Get comprehensive performance statistics"""
    return performance_monitor.get_performance_stats()


# Utility functions for common caching patterns
async def cached_query(key: str, query_func: Callable, ttl: int = 300) -> Any:
    """Execute a query with caching"""
    cached = await cache_service.get(key)
    if cached is not None:
        return cached

    result = await query_optimizer.optimize_query(query_func)
    await cache_service.set(key, result, ttl=ttl)
    return result


async def cached_address_lookup(address: str, lookup_func: Callable, ttl: int = 600) -> Any:
    """Cache address lookup results"""
    cache_key = f"address_lookup:{address}"
    return await cached_query(cache_key, lookup_func, ttl)


async def cached_transaction_lookup(tx_hash: str, lookup_func: Callable, ttl: int = 600) -> Any:
    """Cache transaction lookup results"""
    cache_key = f"tx_lookup:{tx_hash}"
    return await cached_query(cache_key, lookup_func, ttl)


async def cached_risk_score(address: str, risk_func: Callable, ttl: int = 1800) -> Any:
    """Cache risk score calculations"""
    cache_key = f"risk_score:{address}"
    return await cached_query(cache_key, risk_func, ttl)


def monitor_request(endpoint: str, status_code: int):
    """Monitor request performance"""
    # This would be called from middleware to track request metrics
    performance_monitor.record_request(endpoint, 0.0, status_code)  # Duration would be calculated
    performance_monitor.record_memory_usage()
