"""
Security Middleware für automatische Audit-Logging und Security-Checks
"""

import logging
import time
from typing import List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.services.security_compliance import audit_trail_service, security_service

logger = logging.getLogger(__name__)


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Middleware für automatische Security-Audit-Logging"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        path = request.url.path
        method = request.method

        # Check for suspicious activity
        request_data = {
            "ip_address": client_ip,
            "user_agent": user_agent,
            "path": path,
            "method": method,
            "timestamp": time.time()
        }

        suspicious_indicators = security_service.detect_suspicious_activity(request_data)

        # Log the request
        audit_trail_service.log_action(
            action=f"api_request_{method.lower()}",
            resource_type="api_endpoint",
            resource_id=path,
            details={
                "method": method,
                "path": path,
                "query_params": dict(request.query_params),
                "suspicious_indicators": suspicious_indicators
            },
            ip_address=client_ip,
            user_agent=user_agent,
            severity="info" if not suspicious_indicators else "warning"
        )

        # Add security headers to response
        response = await call_next(request)
        self._add_security_headers(response)

        # Log response
        process_time = time.time() - start_time
        status_code = response.status_code

        audit_trail_service.log_action(
            action="api_response",
            resource_type="api_endpoint",
            resource_id=path,
            details={
                "status_code": status_code,
                "response_time_ms": round(process_time * 1000, 2),
                "response_size": response.headers.get("content-length", "unknown")
            },
            ip_address=client_ip,
            severity="info"
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded IP headers
        forwarded_ips = request.headers.get("x-forwarded-for")
        if forwarded_ips:
            return forwarded_ips.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        # Check for CF-Connecting-IP (Cloudflare)
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()

        # Fallback to client host
        return request.client.host if request.client else "unknown"

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced Rate Limiting Middleware"""

    def __init__(self, app, exempt_paths: List[str] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or []
        self.rate_limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "auth": {"requests": 5, "window": 60},      # 5 auth attempts per minute
            "admin": {"requests": 50, "window": 60},    # 50 admin requests per minute
            "api": {"requests": 200, "window": 60},     # 200 API requests per minute
        }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = self._get_client_ip(request)

        # Check if path is exempt from rate limiting
        if any(exempt_path in path for exempt_path in self.exempt_paths):
            return await call_next(request)

        # Determine rate limit category
        rate_limit_key = self._get_rate_limit_key(path)

        # Check rate limit
        if not security_service.check_rate_limiting(f"{rate_limit_key}:{client_ip}", "api_request"):
            # Log rate limit violation
            audit_trail_service.log_action(
                action="rate_limit_exceeded",
                resource_type="rate_limit",
                details={"path": path, "client_ip": client_ip},
                ip_address=client_ip,
                severity="warning"
            )

            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_ips = request.headers.get("x-forwarded-for")
        if forwarded_ips:
            return forwarded_ips.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_rate_limit_key(self, path: str) -> str:
        """Determine rate limit category based on path"""
        if path.startswith("/auth") or "login" in path or "register" in path:
            return "auth"
        elif path.startswith("/admin"):
            return "admin"
        elif path.startswith("/api"):
            return "api"
        else:
            return "default"


class GDPRComplianceMiddleware(BaseHTTPMiddleware):
    """Middleware for GDPR compliance checks"""

    async def dispatch(self, request: Request, call_next):
        # Check for data deletion requests
        if request.method == "DELETE" and "user" in request.url.path:
            # Log GDPR data deletion request
            audit_trail_service.log_action(
                action="gdpr_data_deletion_requested",
                resource_type="user_data",
                details={"path": request.url.path},
                severity="info"
            )

        # Check for data export requests
        elif request.method == "GET" and "export" in request.url.path:
            audit_trail_service.log_action(
                action="gdpr_data_export_requested",
                resource_type="user_data",
                details={"path": request.url.path},
                severity="info"
            )

        response = await call_next(request)
        return response
