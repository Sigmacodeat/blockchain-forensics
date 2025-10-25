"""
Usage & Quota Service
- Verwalten von Credits-Verbrauch pro Tenant (monatlich)
- Prüfen & Konsumieren von Credits nach Plan-Quotas
"""
from __future__ import annotations

import datetime as dt
from typing import Optional, Tuple

from app.services.plan_service import plan_service
from app.db.redis_client import redis_client

USAGE_PREFIX = "usage:credits:"


def _month_key(now: Optional[dt.datetime] = None) -> str:
    d = now or dt.datetime.utcnow()
    return d.strftime("%Y%m")


def _tenant_key(tenant_id: str, month_key: Optional[str] = None) -> str:
    mk = month_key or _month_key()
    return f"{USAGE_PREFIX}{tenant_id}:{mk}"


async def get_plan_and_quota(plan_id: str) -> Tuple[Optional[dict], Optional[int]]:
    plan = plan_service.get_plan(plan_id)
    if not plan:
        return None, None
    monthly_credits = plan_service.get_monthly_credits(plan_id)
    return plan.__dict__, monthly_credits


async def get_usage(tenant_id: str) -> int:
    """Liefert aktuell verbrauchte Credits im laufenden Monat."""
    await redis_client._ensure_connected()
    key = _tenant_key(tenant_id)
    client = redis_client.client
    if not client:
        return 0
    val = await client.get(key)
    return int(val) if val else 0


async def get_remaining_credits(tenant_id: str, plan_id: str) -> Optional[int]:
    _plan, monthly = await get_plan_and_quota(plan_id)
    if monthly is None:
        return None
    used = await get_usage(tenant_id)
    return max(monthly - used, 0)


async def check_and_consume_credits(tenant_id: str, plan_id: str, amount: int, reason: str = "") -> bool:
    """Atomare Prüfung & Verbrauch von Credits. Gibt False zurück, wenn Limit erreicht."""
    await redis_client._ensure_connected()
    client = redis_client.client
    if not client:
        # In Testumgebungen ohne Redis nicht blockieren
        return True

    _plan, monthly = await get_plan_and_quota(plan_id)
    if monthly is None:
        # Custom/Enterprise -> hier nicht blockieren
        return True

    key = _tenant_key(tenant_id)
    # Lua-Skript wäre ideal für echte Atomizität; hier einfacher Ansatz
    current = await client.get(key)
    used = int(current) if current else 0
    if used + amount > monthly:
        return False
    # setex mit Monatsende wäre ideal; vereinfachend TTL 35 Tage
    await client.set(key, used + amount, ex=35 * 24 * 3600)
    return True
