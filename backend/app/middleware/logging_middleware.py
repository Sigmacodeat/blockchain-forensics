"""
Logging Middleware für automatisches Request/Response Logging

Loggt alle HTTP Requests mit:
- Request ID (für Tracing)
- Method, Path, Status Code
- Duration (ms)
- User ID (wenn authenticated)
- IP Address
"""

import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.structured_logging import (
    get_logger,
    set_request_context,
    clear_request_context,
    log_request
)

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware für strukturiertes Request/Response Logging
    
    Features:
    - Automatisches Request ID Generation
    - Request/Response Timing
    - User Context Tracking
    - Structured Logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate Request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract User ID (wenn authenticated)
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = getattr(request.state.user, 'id', None)
        
        # Set Context for Logging
        set_request_context(request_id, user_id)
        
        # Start Timer
        start_time = time.time()
        
        # Log Request Start
        logger.debug(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "http": {
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_ip": request.client.host if request.client else None,
                }
            }
        )
        
        # Process Request
        try:
            response = await call_next(request)
        except Exception:
            # Log Exception
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "http": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                    }
                }
            )
            raise
        
        # Calculate Duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        
        # Log Request Completion
        log_request(
            logger,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id
        )
        
        # Performance Warning für langsame Requests
        if duration_ms > 1000:  # > 1 Sekunde
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} ({duration_ms:.0f}ms)",
                extra={
                    "performance": {
                        "slow_request": True,
                        "threshold_ms": 1000,
                        "actual_ms": duration_ms,
                        "path": request.url.path,
                    }
                }
            )
        
        # Clear Context
        clear_request_context()
        
        return response
