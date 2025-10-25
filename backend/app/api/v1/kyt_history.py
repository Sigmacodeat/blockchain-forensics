"""
KYT Historical Time-Series API
Aggregates risk and exposure over time from alert_service history (best-effort).
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_strict
from app.services.alert_service import alert_service

logger = logging.getLogger(__name__)
router = APIRouter()


class RiskPoint(BaseModel):
    date: str
    risk_max: float = Field(0.0, ge=0.0, le=1.0)
    risk_avg: float = Field(0.0, ge=0.0, le=1.0)


class ExposurePoint(BaseModel):
    date: str
    direct_mixer: float = 0.0
    direct_sanctions: float = 0.0
    indirect_scam: float = 0.0
    indirect_darkweb: float = 0.0


class KYTHistoryResponse(BaseModel):
    success: bool
    range: str
    risk_series: List[RiskPoint]
    exposure_series: List[ExposurePoint]


@router.get("/kyt/history", response_model=KYTHistoryResponse)
async def get_kyt_history(
    address: Optional[str] = Query(None, description="Filter by address"),
    range: str = Query("30d", pattern=r"^(7d|30d|90d)$"),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Returns simplified time-series for risk/exposure based on recent alerts.
    - Buckets by day.
    - Risk: derives from alert severity (critical=1.0, high=0.85, medium=0.6, low=0.3).
    - Exposure: sums category scores if present in metadata (direct/indirect categories).
    """
    try:
        days = 30 if range == "30d" else (7 if range == "7d" else 90)
        until = datetime.utcnow()
        since = until - timedelta(days=days)

        alerts = alert_service.get_recent_alerts_since(since=since)
        norm_addr = (address or "").lower()

        def matches(a) -> bool:
            if not norm_addr:
                return True
            try:
                addr = getattr(a, "address", None)
                if isinstance(addr, str) and addr.lower() == norm_addr:
                    return True
                md = getattr(a, "metadata", {}) or {}
                src = (md.get("from") or md.get("from_address") or "").lower()
                dst = (md.get("to") or md.get("to_address") or "").lower()
                return src == norm_addr or dst == norm_addr
            except Exception:
                return False

        # Prepare daily buckets
        buckets: Dict[str, Dict[str, Any]] = {}
        def daykey(dt: datetime) -> str:
            d = dt.date().isoformat()
            return d

        def sev_to_risk(sev: str) -> float:
            sev = sev.lower()
            if sev == "critical":
                return 1.0
            if sev == "high":
                return 0.85
            if sev == "medium":
                return 0.6
            return 0.3

        for a in alerts:
            if not matches(a):
                continue
            # timestamp parsing best-effort
            try:
                ts = getattr(a, "timestamp", None)
                dt = datetime.fromisoformat(str(ts)) if ts else until
            except Exception:
                dt = until
            k = daykey(dt)
            b = buckets.setdefault(k, {
                "risks": [],
                "direct_mixer": 0.0,
                "direct_sanctions": 0.0,
                "indirect_scam": 0.0,
                "indirect_darkweb": 0.0,
            })
            sev = getattr(a, "severity", "low")
            sev = getattr(sev, "value", str(sev))
            b["risks"].append(sev_to_risk(sev))
            md = getattr(a, "metadata", {}) or {}
            # optional exposure scores if provided by engine
            dexp = md.get("direct_exposure") or {}
            iexp = md.get("indirect_exposure") or {}
            b["direct_mixer"] += float(dexp.get("mixer", 0.0))
            b["direct_sanctions"] += float(dexp.get("sanctions", 0.0))
            b["indirect_scam"] += float(iexp.get("scam", 0.0))
            b["indirect_darkweb"] += float(iexp.get("darkweb", 0.0))

        # Build series sorted by date ascending
        days_list = [since.date() + timedelta(days=i) for i in range(days + 1)]
        risk_series: List[RiskPoint] = []
        exposure_series: List[ExposurePoint] = []
        for d in days_list:
            key = d.isoformat()
            b = buckets.get(key, None)
            if not b:
                risk_series.append(RiskPoint(date=key, risk_max=0.0, risk_avg=0.0))
                exposure_series.append(ExposurePoint(date=key))
                continue
            risks = b["risks"]
            risk_max = max(risks) if risks else 0.0
            risk_avg = (sum(risks) / len(risks)) if risks else 0.0
            risk_series.append(RiskPoint(date=key, risk_max=risk_max, risk_avg=risk_avg))
            exposure_series.append(ExposurePoint(
                date=key,
                direct_mixer=b["direct_mixer"],
                direct_sanctions=b["direct_sanctions"],
                indirect_scam=b["indirect_scam"],
                indirect_darkweb=b["indirect_darkweb"],
            ))

        return KYTHistoryResponse(success=True, range=range, risk_series=risk_series, exposure_series=exposure_series)
    except Exception as e:
        logger.error(f"Failed to compute KYT history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
