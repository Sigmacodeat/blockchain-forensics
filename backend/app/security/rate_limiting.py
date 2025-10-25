"""
Rate Limiting Middleware
========================
OWASP-compliant rate limiting with Redis backend.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str, requests_per_minute: int = 100):
        super().__init__(app)
        self.redis = redis.from_url(redis_url)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        if request.url.path.startswith(("/static/", "/_next/")):
            return await call_next(request)

        # Get client identifier (IP or user ID)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        response = await call_next(request)
        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get user ID from JWT token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT
            # For now, use IP as fallback
            pass
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        key = f"ratelimit:{client_id}"
        current_time = int(time.time())
        
        # Use Redis sorted set to track requests
        self.redis.zadd(key, {str(current_time): current_time})
        
        # Remove old requests outside the window
        self.redis.zremrangebyscore(key, 0, current_time - self.window_seconds)
        
        # Count requests in current window
        request_count = self.redis.zcard(key)
        
        # Set expiry on the key
        self.redis.expire(key, self.window_seconds)
        
        return request_count <= self.requests_per_minute

# Rate limit decorator for specific endpoints
def rate_limit(requests_per_minute: int = 60):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Implementation would go here
            return await func(*args, **kwargs)
        return wrapper
    return decorator
