"""
Audit Middleware
===============

Automatically logs API access and security events for compliance.
"""

import time
import logging
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.audit.logger import log_api_access, log_security_event, AuditSeverity
from app.auth.jwt import decode_token

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically audit API requests
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract request details
        user_id = None
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        # Try to extract user_id from JWT (simplified)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                token_data = decode_token(token)
                if token_data:
                    user_id = getattr(token_data, "user_id", None)
            except Exception:
                # ignore and keep user_id None
                pass
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT here
            # For now, we'll use a placeholder
            pass

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time = time.time() - start_time

        # Log API access
        try:
            await log_api_access(
                user_id=user_id,
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                response_time=response_time,
                details={
                    "query_params": dict(request.query_params),
                    "response_size": response.headers.get("Content-Length"),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log API access: {e}")

        # Security events: elevate for 401/403/429
        try:
            if response.status_code in (401, 403, 429):
                event_type = {
                    401: "unauthorized",
                    403: "forbidden",
                    429: "rate_limited",
                }.get(response.status_code, "security_event")
                severity = AuditSeverity.CRITICAL if response.status_code in (401, 403) else AuditSeverity.HIGH
                await log_security_event(
                    event_type=event_type,
                    severity=severity,
                    user_id=user_id,
                    details={
                        "method": request.method,
                        "endpoint": str(request.url.path),
                        "status_code": response.status_code,
                    },
                    ip_address=ip_address,
                )
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

        return response
