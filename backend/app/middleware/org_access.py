from __future__ import annotations
import logging
import os
from typing import List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status

from app.auth.jwt import decode_token
from app.services.org_service import org_service

logger = logging.getLogger(__name__)


class OrgAccessMiddleware(BaseHTTPMiddleware):
    """
    Enforces that authenticated users are members of an organization for selected path prefixes.
    - Reads org_id from X-Org-Id header (preferred). If missing, allows request (public endpoints or legacy mode).
    - If org_id present: verifies membership via org_service; otherwise 403.
    - Skips for health, docs, auth, billing webhook and other public endpoints.
    """

    def __init__(self, app, protected_prefixes: Optional[List[str]] = None):
        super().__init__(app)
        self.protected_prefixes = protected_prefixes or [
            "/api/v1/cases",
            "/api/v1/alerts",
            "/api/v1/graph",
            "/api/v1/graph-analytics",
            "/api/v1/reports",
            "/api/v1/performance",
        ]
        self._public_prefixes = set([
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/health",
            "/api/health",
            "/api/v1/system/health",
            "/api/v1/auth",
            "/api/v1/password",
            "/api/v1/webhooks",
            "/api/v1/billing/webhook",
            "/api/v1/i18n",
        ])

    def _is_protected(self, path: str) -> bool:
        if any(path.startswith(p) for p in self._public_prefixes):
            return False
        return any(path.startswith(p) for p in self.protected_prefixes)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Skip enforcement if not on protected paths
        if not self._is_protected(path):
            return await call_next(request)

        org_id = request.headers.get("X-Org-Id")
        if not org_id:
            # Allow legacy by default; optionally enforce strict via env flag
            if os.getenv("ENFORCE_ORG_ID_STRICT", "0") == "1":
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "MissingOrgId",
                        "detail": "X-Org-Id header is required on this endpoint",
                    },
                )
            return await call_next(request)

        # Decode token to identify user
        user_id: Optional[str] = None
        try:
            auth = request.headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                token = auth.split(" ", 1)[1].strip()
                data = decode_token(token)
                if data:
                    user_id = getattr(data, "user_id", None)
        except Exception as e:
            logger.warning(f"OrgAccess token decode failed: {e}")
            user_id = None

        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Unauthorized", "detail": "Missing or invalid token"},
            )

        try:
            orgs = await org_service.list_orgs_for_user(str(user_id))
            member_ids = {o["id"] for o in orgs}
            if org_id not in member_ids:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Forbidden", "detail": "Not a member of organization"},
                )
        except Exception as e:
            logger.error(f"Org membership check failed: {e}")
            return JSONResponse(status_code=500, content={"error": "Org check error"})

        return await call_next(request)
