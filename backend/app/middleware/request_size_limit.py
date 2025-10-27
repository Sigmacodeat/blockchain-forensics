from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from typing import Iterable
import os


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Einfache Middleware zur Begrenzung der Request-Größe anhand des Content-Length-Headers.
    - Standardlimit: 2 MiB (konfigurierbar über MAX_REQUEST_SIZE_BYTES)
    - Standardmethoden: POST, PUT, PATCH
    Hinweis: Für Streaming-Uploads ohne Content-Length greift diese Middleware nicht.
    """

    def __init__(self, app, max_bytes: int | None = None, methods: Iterable[str] | None = None):
        super().__init__(app)
        self.max_bytes = max_bytes or int(os.getenv("MAX_REQUEST_SIZE_BYTES", "2097152"))
        self.methods = set((m.upper() for m in (methods or ["POST", "PUT", "PATCH"])) )

    async def dispatch(self, request: Request, call_next):
        try:
            if request.method.upper() in self.methods:
                cl = request.headers.get("content-length")
                if cl is not None:
                    try:
                        size = int(cl)
                        if size > self.max_bytes:
                            return JSONResponse(
                                status_code=413,
                                content={
                                    "detail": f"Payload too large. Maximum allowed is {self.max_bytes} bytes",
                                    "max_bytes": self.max_bytes,
                                },
                                headers={"Retry-After": "1"},
                            )
                    except Exception:
                        # Unparsable header -> fallback: allow
                        pass
            response: Response = await call_next(request)
            return response
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": str(e)})
