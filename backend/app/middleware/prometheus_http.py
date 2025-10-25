from __future__ import annotations
import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "path", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=("method", "path", "status"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)


class PrometheusHTTPMiddleware(BaseHTTPMiddleware):
    """
    Instruments HTTP requests with Prometheus counter & histogram.
    Note: Path labels should be normalized in real-world (e.g. using route name);
    here we use raw path for simplicity.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        start = time.time()
        method = request.method
        # Prefer normalized route path (e.g. /api/v1/cases/{id}) to limit cardinality
        route_path = None
        try:
            route = request.scope.get("route")
            if route is not None and getattr(route, "path", None):
                route_path = route.path  # type: ignore[attr-defined]
        except Exception:
            route_path = None
        path = route_path or request.url.path
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.time() - start
            # Avoid label explosion: trim very long paths
            p = path if len(path) < 128 else path[:128]
            s = str(locals().get("status_code", 0))
            HTTP_REQUESTS_TOTAL.labels(method=method, path=p, status=s).inc()
            HTTP_REQUEST_DURATION.labels(method=method, path=p, status=s).observe(duration)
