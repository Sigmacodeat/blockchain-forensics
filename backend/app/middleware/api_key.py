from typing import Callable, Iterable, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from app.config import settings
import os
import time
import asyncio
import hashlib
from app.db.postgres import postgres_client
from app.db.redis_client import redis_client


def _load_keys() -> set[str]:
    # Prefer settings.API_KEYS (comma-separated), fallback to env API_KEYS
    raw = getattr(settings, "API_KEYS", None)
    if not raw:
        raw = os.getenv("API_KEYS", "")
    return {k.strip() for k in str(raw).split(",") if k and k.strip()}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exempt_paths: Iterable[str] | None = None):
        super().__init__(app)
        self._keys = _load_keys()
        # default exempt endpoints
        self._exempt = set(exempt_paths or [
            "/", "/docs", "/redoc", "/openapi.json",
            "/metrics", "/api/healthz",
        ])
        # simple in-memory TTL cache: hash -> (allowed(bool), tier(str|None), expires_at(float))
        self._cache: dict[str, tuple[bool, str | None, float]] = {}
        self._cache_ttl_seconds = 300.0
        self._lock = asyncio.Lock()
        # tier limits (req/sec)
        self._limits = {
            "free": int(os.getenv("API_RATE_LIMIT_FREE", "10")),
            "pro": int(os.getenv("API_RATE_LIMIT_PRO", "50")),
            "enterprise": int(os.getenv("API_RATE_LIMIT_ENTERPRISE", "200")),
        }

    async def _check_db_key(self, api_key: str) -> Tuple[bool, str | None]:
        # Compute SHA-256 of provided key and look up non-revoked record
        h = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        now = time.time()
        # cache hit
        cached = self._cache.get(h)
        if cached and cached[2] > now:
            return cached[0], cached[1]
        # no DB in test or no pool -> deny (fallback)
        if os.getenv("TEST_MODE") == "1" or not getattr(postgres_client, "pool", None):
            return False, None
        try:
            async with self._lock:
                # recheck cache after awaiting lock
                cached = self._cache.get(h)
                if cached and cached[2] > time.time():
                    return cached[0], cached[1]
                async with postgres_client.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT tier FROM api_keys WHERE hash_sha256 = $1 AND revoked = FALSE LIMIT 1",
                        h,
                    )
                allowed = bool(row)
                tier = row["tier"] if row else None
                self._cache[h] = (allowed, tier, now + self._cache_ttl_seconds)
                return allowed, tier
        except Exception:
            # On DB error, deny and short cache to avoid tight loops
            self._cache[h] = (False, None, now + 5.0)
            return False, None

    async def _rate_limit(self, api_key: str, tier: str) -> Tuple[bool, int, int, int]:
        """Return (allowed, limit, remaining, reset_seconds)."""
        limit = self._limits.get(tier, self._limits["pro"])
        try:
            await redis_client._ensure_connected()
            client = redis_client.client
            if not client or limit <= 0:
                return True, limit, limit, 1
            from datetime import datetime
            now = datetime.utcnow()
            sec = int(now.timestamp())
            prefix = api_key[:16]
            key = f"rl:{prefix}:{sec}"
            count = await client.incr(key)
            # expire just after this second window
            await client.expire(key, 2)
            remaining = max(limit - int(count), 0)
            return (count <= limit), limit, remaining, 1
        except Exception:
            # fail-open on rate limiter issues
            return True, limit, limit, 1

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Disable in TEST_MODE or when running under pytest
        if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            return await call_next(request)
        # Skip only if neither static keys nor DB-backed keys are available
        if not self._keys and (os.getenv("TEST_MODE") == "1" or not getattr(postgres_client, "pool", None)):
            return await call_next(request)
        # Exempt paths (exact match; plus treat entries as prefix roots)
        path = request.url.path
        # quick prefix check for any configured exempt entries
        for ex in list(self._exempt):
            if path == ex or path.startswith(ex + "/"):
                return await call_next(request)
        # Additional exemptions: docs assets, public NewsCases WS, and read-only public snapshot
        if path.startswith("/docs") or path.startswith("/api/v1/ws/news-cases") or (
            path.startswith("/api/v1/news-cases/") and path.endswith("/public")
        ):
            return await call_next(request)

        api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        if not api_key:
            return JSONResponse({"detail": "Unauthorized: missing or invalid API key"}, status_code=401)
        # allow if present in static configured keys (treat as enterprise tier)
        if api_key in self._keys:
            allowed, limit, remaining, reset = await self._rate_limit(api_key, "enterprise")
            if not allowed:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429, headers={
                    "Retry-After": str(reset),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                })
            response = await call_next(request)
            # best-effort usage counter
            try:
                await redis_client._ensure_connected()
                if redis_client.client:
                    from datetime import datetime
                    day = datetime.utcnow().strftime("%Y%m%d")
                    prefix = api_key[:16]
                    key = f"usage:req:{day}:{prefix}"
                    await redis_client.client.incr(key)
                    await redis_client.client.expire(key, 40 * 24 * 3600)
            except Exception:
                pass
            return response
        # otherwise check DB-backed keys
        allowed_db, tier = await self._check_db_key(api_key)
        if allowed_db:
            allowed, limit, remaining, reset = await self._rate_limit(api_key, tier or "pro")
            if not allowed:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429, headers={
                    "Retry-After": str(reset),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                })
            response = await call_next(request)
            # best-effort usage counter
            try:
                await redis_client._ensure_connected()
                if redis_client.client:
                    from datetime import datetime
                    day = datetime.utcnow().strftime("%Y%m%d")
                    prefix = api_key[:16]
                    key = f"usage:req:{day}:{prefix}"
                    await redis_client.client.incr(key)
                    await redis_client.client.expire(key, 40 * 24 * 3600)
            except Exception:
                pass
            return response
        return JSONResponse({"detail": "Unauthorized: missing or invalid API key"}, status_code=401)
