from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from app.db.redis_client import redis_client
from app.auth.dependencies import require_admin, get_current_user_strict
from app.services.usage_tracking import usage_tracking_service

router = APIRouter()


async def _scan_sum(prefix: Optional[str], day: str) -> int:
    await redis_client._ensure_connected()
    client = redis_client.client
    if not client:
        return 0
    pattern = f"usage:req:{day}:{prefix or '*'}"
    cursor: int = 0
    total = 0
    while True:
        cursor, keys = await client.scan(cursor=cursor, match=pattern, count=200)
        if keys:
            values = await client.mget(*keys)
            for v in values:
                try:
                    total += int(v or 0)
                except Exception:
                    continue
        if cursor == 0:
            break
    return total


@router.get("/usage")
async def get_usage_summary(
    days: int = Query(7, ge=1, le=30),
    key_prefix: Optional[str] = Query(None, min_length=4, max_length=32),
    _user: dict = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Aggregated API usage (request counts) over the last N days.
    Optionally filter by API key prefix (first 16 chars shown to clients).
    Admin-only.
    """
    try:
        now = datetime.utcnow()
        daily: Dict[str, int] = {}
        total = 0
        for i in range(days):
            d = now - timedelta(days=i)
            ds = d.strftime("%Y%m%d")
            c = await _scan_sum(key_prefix, ds)
            daily[ds] = c
            total += c
        return {
            "days": days,
            "key_prefix": key_prefix,
            "total": total,
            "daily": dict(sorted(daily.items())),
        }
    except HTTPException:
        raise
    except Exception as e:
        # Non-fatal; return empty aggregate if Redis not available
        return {"days": days, "key_prefix": key_prefix, "total": 0, "daily": {}}


# ============================================================================
# USER-SPEZIFISCHE USAGE-ENDPUNKTE
# ============================================================================

@router.get("/current")
async def get_current_usage(user: dict = Depends(get_current_user_strict)):
    """
    Aktueller Token-Usage des eingeloggten Users
    
    Returns:
    {
        "tokens_used": 90,
        "quota": 100,
        "quota_percentage": 90.0,
        "resets_at": "2025-11-01T00:00:00Z"
    }
    """
    try:
        user_id = user.get("user_id") or user.get("id")
        plan = user.get("plan", "community")
        
        usage_data = await usage_tracking_service.get_current_usage(user_id, plan)
        return usage_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get usage: {str(e)}")


@router.get("/breakdown")
async def get_usage_breakdown(user: dict = Depends(get_current_user_strict)):
    """
    Usage-Breakdown nach Feature
    
    Returns:
    {
        "trace_start": 50,
        "ai_agent_query": 25,
        "graph_query": 15,
        "total": 90
    }
    """
    try:
        user_id = user.get("user_id") or user.get("id")
        
        breakdown = await usage_tracking_service.get_usage_breakdown(user_id)
        return breakdown
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get breakdown: {str(e)}")
