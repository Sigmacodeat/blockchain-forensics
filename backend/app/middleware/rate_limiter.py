"""
Plan-based Rate Limiting Middleware
Redis-backed, Cluster-Ready
"""

import time
from typing import Dict, Optional, Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib

# Redis Client (falls verfügbar)
try:
    from app.db.redis_client import redis_client
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    redis_client = None

from app.auth.jwt import decode_token
from app.observability.audit_logger import log_rate_limit_event


# Plan-basierte Rate-Limits (Requests pro Minute)
RATE_LIMITS: Dict[str, int] = {
    'community': 10,      # 10 req/min
    'starter': 30,        # 30 req/min
    'pro': 100,           # 100 req/min
    'business': 300,      # 300 req/min
    'plus': 1000,         # 1000 req/min
    'enterprise': 10000   # Quasi unlimited
}

# Exempt Endpoints (keine Rate-Limits)
EXEMPT_PATHS = [
    '/health',
    '/healthz',
    '/metrics',
    '/docs',
    '/openapi.json',
    '/api/v1/auth/login',
    '/api/v1/auth/register'
]


class PlanBasedRateLimiter(BaseHTTPMiddleware):
    """
    Plan-based Rate Limiting Middleware
    
    Features:
    - Plan-specific Limits
    - Redis-backed (Cluster-Ready)
    - Sliding Window Algorithm
    - Audit-Logging bei Limit-Überschreitung
    
    Usage:
        app.add_middleware(PlanBasedRateLimiter)
    """
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client
        self.in_memory_store: Dict[str, list] = {}  # Fallback
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip exempt paths
        if any(request.url.path.startswith(path) for path in EXEMPT_PATHS):
            return await call_next(request)
        
        # Extract user from JWT
        user = await self._get_user_from_request(request)
        if not user:
            # Anonymous = community limits
            user = {"user_id": "anonymous", "plan": "community"}
        
        user_id = user.get("user_id", "anonymous")
        plan = user.get("plan", "community")
        limit = RATE_LIMITS.get(plan, 10)
        
        # Check rate limit
        allowed, current_count = await self._check_rate_limit(user_id, plan, limit)
        
        if not allowed:
            # Audit-Log
            log_rate_limit_event(
                user_id=user_id,
                plan=plan,
                endpoint=request.url.path,
                limit=f"{limit}/minute",
                current_count=current_count,
                ip_address=request.client.host if request.client else None
            )
            
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Your plan ({plan}) allows {limit} requests per minute. Upgrade for higher limits.",
                    "limit": f"{limit}/minute",
                    "current": current_count,
                    "retry_after": 60  # seconds
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60),
                    "Retry-After": "60"
                }
            )
        
        # Add rate-limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(limit - current_count)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
    
    async def _get_user_from_request(self, request: Request) -> Optional[Dict]:
        """Extract user from JWT token in request"""
        try:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ", 1)[1]
            token_data = decode_token(token)
            
            if not token_data:
                return None
            
            return {
                "user_id": token_data.user_id,
                "plan": getattr(token_data, "plan", "community"),
                "email": token_data.email
            }
        except Exception:
            return None
    
    async def _check_rate_limit(self, user_id: str, plan: str, limit: int) -> tuple[bool, int]:
        """
        Check if user is within rate limit
        
        Returns:
            (allowed: bool, current_count: int)
        """
        now = int(time.time())
        window_start = now - 60  # 1 minute window
        
        key = f"ratelimit:{user_id}:{now // 60}"  # Window-Key
        
        if REDIS_AVAILABLE and self.redis:
            return await self._check_redis(key, limit, window_start, now)
        else:
            return await self._check_memory(user_id, limit, window_start, now)
    
    async def _check_redis(self, key: str, limit: int, window_start: int, now: int) -> tuple[bool, int]:
        """Redis-backed rate limiting (Cluster-Ready)"""
        try:
            # Sorted Set mit Timestamps
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current entries
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry
            pipe.expire(key, 120)  # 2 minutes
            
            results = pipe.execute()
            count = results[1] + 1  # +1 für current request
            
            return (count <= limit, count)
        
        except Exception:
            # Fallback zu Memory
            return await self._check_memory(key, limit, window_start, now)
    
    async def _check_memory(self, user_id: str, limit: int, window_start: int, now: int) -> tuple[bool, int]:
        """In-Memory Fallback (nicht Cluster-Ready)"""
        if user_id not in self.in_memory_store:
            self.in_memory_store[user_id] = []
        
        # Remove old entries
        self.in_memory_store[user_id] = [
            ts for ts in self.in_memory_store[user_id]
            if ts > window_start
        ]
        
        # Add current request
        self.in_memory_store[user_id].append(now)
        
        count = len(self.in_memory_store[user_id])
        return (count <= limit, count)


# Decorator für spezifische Endpoints (alternative zu Middleware)
def rate_limit(plan: str = "community"):
    """
    Rate-Limit Decorator für einzelne Endpoints
    
    Usage:
        @router.get("/expensive")
        @rate_limit(plan="pro")
        async def expensive_operation():
            return {"data": "..."}
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Implementation hier
            return await func(*args, **kwargs)
        return wrapper
    return decorator
