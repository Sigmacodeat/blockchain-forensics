from __future__ import annotations
import hashlib
import logging
import re
from typing import Optional, Iterable, List, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        header_name: str = "Idempotency-Key",
        ttl_seconds: int = 60,
        allowlist: Optional[Iterable[str]] = None,
        blocklist: Optional[Iterable[str]] = None,
        methods: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.header_name = header_name
        self.ttl = ttl_seconds
        self.methods: Tuple[str, ...] = tuple(m.upper() for m in (methods or ("POST", "PUT", "PATCH", "DELETE")))
        self._allow_re: Optional[List[re.Pattern[str]]] = (
            [re.compile(p) for p in allowlist] if allowlist else None
        )
        self._block_re: Optional[List[re.Pattern[str]]] = (
            [re.compile(p) for p in blocklist] if blocklist else None
        )

    def _path_enforced(self, path: str) -> bool:
        if self._block_re and any(r.match(path) for r in self._block_re):
            return False
        if self._allow_re is not None:
            return any(r.match(path) for r in self._allow_re)
        return True

    async def dispatch(self, request: Request, call_next):
        # Check HTTP method
        if request.method.upper() not in self.methods:
            return await call_next(request)
        # Check path policy
        if not self._path_enforced(request.url.path):
            return await call_next(request)

        idem_key = request.headers.get(self.header_name)
        if not idem_key:
            # No key → proceed without idempotency handling
            return await call_next(request)

        # Create a namespaced key (optionally include path and method)
        scope = f"{request.method}:{request.url.path}:{idem_key}"
        key = f"idem:{hashlib.sha256(scope.encode()).hexdigest()}"

        try:
            # Ensure redis connection (no-op in tests)
            await redis_client._ensure_connected()  # type: ignore[attr-defined]
            client = getattr(redis_client, "client", None)
            if client is not None:
                # SETNX pattern to guard duplicates
                was_set = await client.setnx(key, "1")
                if not was_set:
                    return JSONResponse(
                        status_code=409,
                        content={
                            "error": "Duplicate request (Idempotency-Key)",
                            "detail": "A request with the same Idempotency-Key was recently processed.",
                        },
                    )
                await client.expire(key, self.ttl)
        except Exception as e:
            # Fallback: if Redis is unavailable, proceed without blocking
            logger.warning(f"Idempotency middleware fallback (redis unavailable): {e}")

        response: Response = await call_next(request)
        return response
