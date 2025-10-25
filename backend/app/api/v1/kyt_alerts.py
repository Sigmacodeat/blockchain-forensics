"""
KYT Alerts History API
Returns recent KYT/alert-engine alerts filtered by address with minimal persistence requirements
by leveraging the existing alert_service store.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_strict
from app.services.alert_service import alert_service

logger = logging.getLogger(__name__)
router = APIRouter()


class KYTAlertItem(BaseModel):
    tx_hash: Optional[str] = None
    risk_level: str = Field(..., description="critical|high|medium|low|safe")
    title: str
    description: Optional[str] = None
    address: Optional[str] = None
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KYTAlertsResponse(BaseModel):
    success: bool
    total: int
    alerts: List[KYTAlertItem]


@router.get("/kyt/alerts", response_model=KYTAlertsResponse)
async def get_kyt_alerts(
    address: Optional[str] = Query(None, description="Filter by address (from/to/address)"),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Returns recent KYT alerts pulled from the alert engine's history.

    - address: if provided, filters by `alert.address == address` or present in metadata (from/to)
    - days: lookback window (default 7 days)
    - limit: max number of items
    """
    try:
        until = datetime.utcnow()
        since = until - timedelta(days=days)
        raw_alerts = alert_service.get_recent_alerts_since(since=since)

        norm_addr = (address or "").lower()

        def match_addr(a) -> bool:
            if not norm_addr:
                return True
            try:
                addr = getattr(a, "address", None)
                if isinstance(addr, str) and addr.lower() == norm_addr:
                    return True
                md = getattr(a, "metadata", {}) or {}
                src = (md.get("from") or md.get("from_address") or md.get("source_address") or "").lower()
                dst = (md.get("to") or md.get("to_address") or md.get("destination_address") or "").lower()
                return src == norm_addr or dst == norm_addr
            except Exception:
                return False

        items: List[KYTAlertItem] = []
        for a in raw_alerts:
            if not match_addr(a):
                continue
            sev = getattr(a, "severity", "low")
            sev = getattr(sev, "value", str(sev))
            risk_map = {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "low": "low",
            }
            risk_level = risk_map.get(sev, "low")
            items.append(
                KYTAlertItem(
                    tx_hash=getattr(a, "tx_hash", None),
                    risk_level=risk_level,
                    title=str(getattr(a, "title", "Alert")),
                    description=str(getattr(a, "description", "")),
                    address=getattr(a, "address", None),
                    timestamp=str(getattr(a, "timestamp", until.isoformat())),
                    metadata=getattr(a, "metadata", {}) or {},
                )
            )
            if len(items) >= limit:
                break

        return KYTAlertsResponse(success=True, total=len(items), alerts=items)
    except Exception as e:
        logger.error(f"Failed to get KYT alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
