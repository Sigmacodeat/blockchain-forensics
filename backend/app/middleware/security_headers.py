from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds strict security headers to every response.
    Notes:
    - HSTS should only be enabled when served over HTTPS/behind TLS-terminating proxy.
    - CSP is kept reasonably strict for API responses; static site CSP is set in Nginx.
    """

    def __init__(self, app, *, enable_hsts: bool = False):
        super().__init__(app)
        self.enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Clickjacking/XSS/MIME sniffing
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # Legacy XSS header (harmless for modern browsers)
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        # Cross-origin isolation and resource policy
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Embedder-Policy", "require-corp")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")

        # Extra hardening
        response.headers.setdefault("X-Download-Options", "noopen")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.headers.setdefault("Origin-Agent-Cluster", "?1")

        # API-safe CSP (no inline; allow self and data: for images)
        # Static assets CSP is handled by Nginx; this one protects API/HTML fallbacks
        csp = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'self'; "
            "form-action 'self'; "
            "connect-src 'self'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)

        # Permissions-Policy to restrict powerful features
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        )

        # Remove Server header to avoid version leakage
        try:
            del response.headers["server"]
        except Exception:
            pass

        # HSTS (only when TLS is used at the edge)
        if self.enable_hsts and request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")

        return response
