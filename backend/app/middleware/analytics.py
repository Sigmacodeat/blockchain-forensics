import os
import time
import hashlib
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.postgres import postgres_client

class AnalyticsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, ip_salt_env: str = "ANALYTICS_IP_SALT"):
        super().__init__(app)
        self.enabled = os.getenv("ENABLE_ANALYTICS", "1") == "1"
        self.ip_salt = os.getenv(ip_salt_env, "")

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.time()
        response = await call_next(request)
        if not self.enabled:
            return response
        try:
            if request.url.path.startswith(("/metrics", "/docs", "/openapi.json")):
                return response
            dnt = request.headers.get("DNT") == "1"
            if dnt:
                return response
            ua = request.headers.get("user-agent", "")[:256]
            ip = request.client.host if request.client else ""
            ip_hash = hashlib.sha256((ip + self.ip_salt).encode("utf-8")).hexdigest() if self.ip_salt else ""
            duration = max(0.0, time.time() - start)
            user_id = getattr(getattr(request, "state", None), "user_id", None)
            path = request.url.path
            method = request.method
            status = response.status_code
            ref = request.headers.get("referer")
            org_id = request.headers.get("X-Org-Id")
            props = {"org_id": org_id} if org_id else {}
            # Persist minimal event server-side
            if os.getenv("TEST_MODE") != "1" and getattr(postgres_client, "pool", None):
                try:
                    async with postgres_client.acquire() as conn:
                        try:
                            await conn.execute(
                                """
                                INSERT INTO web_events (ts, user_id, session_id, event, properties, path, referrer, ua, ip_hash, method, status, duration, org_id)
                                VALUES (NOW(), $1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9, $10, $11, $12)
                                """,
                                user_id,
                                None,
                                "server_request",
                                props,
                                path,
                                ref,
                                ua,
                                ip_hash,
                                method,
                                status,
                                float(duration),
                                org_id,
                            )
                        except Exception:
                            await conn.execute(
                                """
                                INSERT INTO web_events (ts, user_id, session_id, event, properties, path, referrer, ua, ip_hash, method, status, duration)
                                VALUES (NOW(), $1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9, $10, $11)
                                """,
                                user_id,
                                None,
                                "server_request",
                                props,
                                path,
                                ref,
                                ua,
                                ip_hash,
                                method,
                                status,
                                float(duration),
                            )
                except Exception:
                    pass
        except Exception:
            pass
        return response
