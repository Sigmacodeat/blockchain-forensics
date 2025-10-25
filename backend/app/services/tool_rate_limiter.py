"""
Tool-Specific Rate Limiting
============================

Rate limits for AI tool calls based on user plan.
"""

import logging
import time
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    from app.db.redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis_client = None


class ToolRateLimiter:
    """Rate limiting for AI tool execution"""
    
    # Tool-specific limits (requests per hour)
    LIMITS = {
        "create_case": {
            "community": 5,
            "starter": 20,
            "pro": 50,
            "business": 150,
            "plus": 200,
            "enterprise": 1000,
            "window": 3600  # 1 hour
        },
        "generate_trace_report": {
            "community": 5,
            "starter": 10,
            "pro": 50,
            "business": 150,
            "plus": 200,
            "enterprise": 1000,
            "window": 3600
        },
        "export_case": {
            "community": 10,
            "starter": 30,
            "pro": 100,
            "business": 300,
            "plus": 500,
            "enterprise": 2000,
            "window": 3600
        },
        "trace_address": {
            "community": 10,
            "starter": 50,
            "pro": 200,
            "business": 500,
            "plus": 1000,
            "enterprise": 5000,
            "window": 3600
        }
    }
    
    def __init__(self):
        self.redis = redis_client if REDIS_AVAILABLE else None
        self.memory_store: Dict[str, list] = {}  # Fallback
    
    async def check_limit(
        self,
        user_id: str,
        tool_name: str,
        plan: str = "community"
    ) -> Tuple[bool, int, int]:
        """
        Check if user is within tool-specific rate limit
        
        Args:
            user_id: User ID
            tool_name: Name of the tool
            plan: User's plan (community, pro, etc.)
        
        Returns:
            (allowed: bool, current_count: int, limit: int)
        """
        # Get limit config for this tool
        limit_config = self.LIMITS.get(tool_name)
        
        if not limit_config:
            # No limit defined for this tool
            return (True, 0, 999999)
        
        # Get limit for user's plan
        limit = limit_config.get(plan, 10)  # Default to 10 if plan not found
        window = limit_config["window"]
        
        # Check rate limit
        if self.redis:
            return await self._check_redis(user_id, tool_name, limit, window)
        else:
            return await self._check_memory(user_id, tool_name, limit, window)
    
    async def _check_redis(
        self,
        user_id: str,
        tool_name: str,
        limit: int,
        window: int
    ) -> Tuple[bool, int, int]:
        """Redis-backed rate limiting"""
        try:
            now = int(time.time())
            window_key = now // window  # Current window
            
            key = f"tool_limit:{user_id}:{tool_name}:{window_key}"
            
            # Increment counter
            count = await self.redis.incr(key)
            
            # Set expiry on first increment
            if count == 1:
                await self.redis.expire(key, window)
            
            allowed = count <= limit
            
            return (allowed, count, limit)
        
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to memory
            return await self._check_memory(user_id, tool_name, limit, window)
    
    async def _check_memory(
        self,
        user_id: str,
        tool_name: str,
        limit: int,
        window: int
    ) -> Tuple[bool, int, int]:
        """In-memory fallback (not cluster-safe)"""
        now = int(time.time())
        window_start = now - window
        
        key = f"{user_id}:{tool_name}"
        
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Remove old timestamps
        self.memory_store[key] = [
            ts for ts in self.memory_store[key]
            if ts > window_start
        ]
        
        # Add current timestamp
        self.memory_store[key].append(now)
        
        count = len(self.memory_store[key])
        allowed = count <= limit
        
        return (allowed, count, limit)
    
    def get_retry_after(self, window: int = 3600) -> int:
        """
        Calculate seconds until rate limit resets
        
        Args:
            window: Window size in seconds
        
        Returns:
            Seconds until reset
        """
        now = int(time.time())
        window_key = now // window
        window_end = (window_key + 1) * window
        
        return window_end - now


# Global singleton
tool_rate_limiter = ToolRateLimiter()
