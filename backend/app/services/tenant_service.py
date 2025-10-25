from __future__ import annotations

from typing import Optional
from app.db.redis_client import redis_client
from app.services.plan_service import plan_service

_TENANT_PLAN_KEY = "tenant:plan:{tenant_id}"


class TenantService:
    def __init__(self):
        self._default_plan = "community"

    def get_plan_id(self, tenant_id: str) -> str:
        if not tenant_id:
            return self._fallback_default()
        try:
            key = _TENANT_PLAN_KEY.format(tenant_id=tenant_id)
            val = redis_client.get_sync(key)
            if val:
                return val.decode("utf-8") if isinstance(val, (bytes, bytearray)) else str(val)
        except Exception:
            pass
        return self._fallback_default()

    def set_plan_id(self, tenant_id: str, plan_id: str) -> bool:
        try:
            # validate plan exists
            cfg = plan_service.get_config()
            if not any(p.id == plan_id for p in cfg.plans):
                return False
            key = _TENANT_PLAN_KEY.format(tenant_id=tenant_id)
            redis_client.set_sync(key, plan_id)
            return True
        except Exception:
            return False

    def _fallback_default(self) -> str:
        try:
            cfg = plan_service.get_config()
            # pick first plan marked default if available
            for p in cfg.plans:
                if getattr(p, "is_default", False):
                    return p.id
            # fallback to known id
            return self._default_plan
        except Exception:
            return self._default_plan


tenant_service = TenantService()
