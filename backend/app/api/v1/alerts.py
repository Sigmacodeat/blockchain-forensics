"""Alert Management API"""

from typing import Dict, List, Optional, Any, Literal
import logging
import time
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel, Field
from app.auth.dependencies import get_current_user_strict, get_current_user, require_plan
from app.services.alert_service import alert_service
from app.services.alert_annotation_service import alert_annotation_service
from app.services.kpi_service import kpi_service
from app.db.postgres import postgres_client
from app.models.audit_log import log_audit_event, AuditAction
try:
    from app.services.case_service import case_service
except Exception:
    case_service = None  # type: ignore
try:
    from app.observability.forensics_metrics import (
        KYT_SCREENING_TOTAL,
        KYT_SCREENING_DURATION,
        KYT_ALERTS_TRIGGERED,
        KYT_BATCH_SIZE
    )
except ImportError:
    # Metrics not available, use no-ops
    KYT_SCREENING_TOTAL = None  # type: ignore
    KYT_SCREENING_DURATION = None  # type: ignore
    KYT_ALERTS_TRIGGERED = None  # type: ignore
    KYT_BATCH_SIZE = None  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory operational annotations (ephemeral). For persistence, wire to DB later.
_ALERT_DISPOSITIONS: Dict[str, str] = {}
_ALERT_EVENT_TIMES: Dict[str, datetime] = {}

# Simple in-memory idempotency and rate-limiting stores (process-local)
_IDEMPOTENCY_CACHE: Dict[str, float] = {}
_RATE_LIMIT_BUCKETS: Dict[str, List[float]] = {}

_IDEMPOTENCY_TTL_SECONDS = 60.0
_RATE_LIMIT_WINDOW_SECONDS = 10.0
_RATE_LIMIT_MAX_REQUESTS = 15  # per user per window


def _validate_address(address: str) -> str:
    """Validate blockchain address format"""
    if not address or len(address) < 10:
        raise ValueError("Address must be at least 10 characters long")

    # Basic hex validation for Ethereum-style addresses
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        # Allow other formats (BTC, etc.) but at least check basic format
        if not re.match(r'^[a-zA-Z0-9]{26,}$', address):
            raise ValueError("Invalid address format")

    return address.lower()


def _sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input"""
    if not isinstance(value, str):
        raise ValueError("Must be a string")

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\'\`]', '', value)
    return sanitized[:max_length].strip()


def _check_rate_limit(user: Optional[dict]) -> None:
    uid = str((user or {}).get("id") or (user or {}).get("email") or "anonymous")
    now = time.time()
    bucket = _RATE_LIMIT_BUCKETS.get(uid, [])
    # drop old
    bucket = [t for t in bucket if now - t <= _RATE_LIMIT_WINDOW_SECONDS]
    if len(bucket) >= _RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)
    _RATE_LIMIT_BUCKETS[uid] = bucket


def _check_idempotency(request_id: Optional[str]) -> None:
    if not request_id:
        return
    now = time.time()
    ts = _IDEMPOTENCY_CACHE.get(request_id)
    if ts is not None and (now - ts) <= _IDEMPOTENCY_TTL_SECONDS:
        raise HTTPException(status_code=409, detail="Duplicate request (Idempotency-Key)")
    _IDEMPOTENCY_CACHE[request_id] = now


class AlertResponse(BaseModel):
    """Alert response model"""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    metadata: Dict[str, Any]
    address: Optional[str] = None
    tx_hash: Optional[str] = None
    acknowledged: bool
    timestamp: str


class BatchProcessRequest(BaseModel):
    """Batch process request model"""
    events: List[Dict[str, Any]]
    max_alerts_per_entity: Optional[int] = None


class KYTPrecheckRequest(BaseModel):
    """Pre-confirmation KYT screening request"""
    chain: Optional[str] = Field(None, description="Chain ID, e.g., ethereum, polygon")
    from_address: Optional[str] = Field(None, description="Sender address")
    to_address: Optional[str] = Field(None, description="Recipient address")
    amount: Optional[float] = Field(None, ge=0.0, description="Transfer amount in native units")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KYTPrecheckResponse(BaseModel):
    """Pre-confirmation KYT response with decision hint"""
    success: bool
    alerts_created: int
    decision: str  # allow|review|hold
    details: Dict[str, Any] = Field(default_factory=dict)


class KYTPostEvent(BaseModel):
    """Post-confirmation event item (confirmed tx)"""
    chain: Optional[str] = None
    tx_hash: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount: Optional[float] = None
    block_number: Optional[int] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KYTBatchRequest(BaseModel):
    """Post-confirmation KYT batch request"""
    events: List[KYTPostEvent]
    max_alerts_per_entity: Optional[int] = None


class AlertStatsResponse(BaseModel):
    """Alert statistics response model"""
    total_alerts: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    unacknowledged: int


class SuppressionEventResponse(BaseModel):
    """Suppression event response model"""
    alert_id: str
    alert_type: str
    severity: str
    address: Optional[str] = None
    tx_hash: Optional[str] = None
    title: str
    reason: str
    fingerprint: str
    suppressed_at: str
    suppression_count: int


class AlertKpiResponse(BaseModel):
    """KPI response model for dashboard KPIs"""
    fpr: float = Field(0.0, ge=0.0, le=1.0, description="False Positive Rate (0-1)")
    mttr: float = Field(0.0, ge=0.0, description="Mean Time To Respond in hours")
    mttd: float = Field(0.0, ge=0.0, description="Mean Time To Detect in hours")
    sla_breach_rate: float = Field(0.0, ge=0.0, le=1.0, description="SLA breach rate (0-1)")
    sanctions_hits: int = Field(0, ge=0, description="Number of sanctions screening hits")


@router.get("/kpis", response_model=AlertKpiResponse)
async def get_alert_kpis(
    days: int = Query(30, ge=1, le=365, description="Time window in days for KPI calculations"),
    sla_hours: int = Query(48, ge=1, le=720, description="SLA target in hours for case resolution"),
    response: Response = None,
    current_user: dict = Depends(get_current_user_strict)
) -> AlertKpiResponse:
    """
    Get key performance indicators for alerts/cases used by the dashboard.

    Notes:
    - FPR (False Positive Rate) requires dispositions; if unavailable, returns 0.0 as placeholder.
    - MTTR calculated from cases (closed_at - created_at) median in hours.
    - MTTD requires event timestamps; if unavailable, returns 0.0 as placeholder.
    - SLA Breach Rate computed as share of closed cases exceeding sla_hours.
    - Sanctions Hits counted from current alert history of type SANCTIONED_ENTITY.
    """
    try:
        result = await kpi_service.get_kpis(days=days, sla_hours=sla_hours)

        if response is not None:
            try:
                response.headers["Cache-Control"] = "public, max-age=300"
                response.headers["ETag"] = f'"kpis-{sla_hours}-{days}"'
            except Exception:
                pass

        return AlertKpiResponse(
            fpr=round(float(result.fpr), 4),
            mttr=round(float(result.mttr), 2),
            mttd=round(float(result.mttd), 2),
            sla_breach_rate=round(float(result.sla_breach_rate), 4),
            sanctions_hits=int(result.sanctions_hits),
        )
    except Exception as e:
        logger.error(f"Error computing alert KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kyt/pre", response_model=KYTPrecheckResponse)
async def kyt_precheck(
    req: KYTPrecheckRequest,
    current_user: dict = Depends(get_current_user_strict)
) -> KYTPrecheckResponse:
    """
    KYT Pre-Confirmation Screening.
    Nutzt die bestehende Alert-Engine, um vor Broadcast/Bestätigung eine Entscheidung zu liefern.
    """
    try:
        _check_rate_limit(current_user)
        event = {
            "chain": req.chain,
            "from": (req.from_address or "").lower() if req.from_address else None,
            "to": (req.to_address or "").lower() if req.to_address else None,
            "amount": req.amount,
            "stage": "pre",
            "metadata": req.metadata or {},
        }
        alerts = await alert_service.process_event(event)
        # naive decision heuristic: any high/critical -> hold, any medium -> review, else allow
        decision = "allow"
        severities = [getattr(a.severity, "value", str(a.severity)) for a in alerts]
        if any(s in ("high", "critical") for s in severities):
            decision = "hold"
        elif any(s == "medium" for s in severities):
            decision = "review"
        return KYTPrecheckResponse(
            success=True,
            alerts_created=len(alerts),
            decision=decision,
            details={"severities": severities, "alert_ids": [a.alert_id for a in alerts]},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in KYT precheck: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kyt/post")
async def kyt_post_confirmation(
    req: KYTBatchRequest,
    current_user: dict = Depends(get_current_user_strict)
) -> Dict[str, Any]:
    """
    KYT Post-Confirmation Monitoring.
    Verarbeitet bestätigte Transaktionen als Batch über die bestehende Alert-Engine.
    """
    try:
        _check_rate_limit(current_user)
        events = []
        for it in req.events:
            events.append({
                "chain": it.chain,
                "tx_hash": it.tx_hash,
                "from": (it.from_address or "").lower() if it.from_address else None,
                "to": (it.to_address or "").lower() if it.to_address else None,
                "amount": it.amount,
                "block_number": it.block_number,
                "timestamp": it.timestamp,
                "stage": "post",
                "metadata": it.metadata or {},
            })
        # optional override
        original_limit = None
        if req.max_alerts_per_entity is not None:
            original_limit = alert_service.get_max_rules_per_entity()
            alert_service.set_max_rules_per_entity(req.max_alerts_per_entity)
        alerts = await alert_service.process_event_batch(events)
        if original_limit is not None:
            alert_service.set_max_rules_per_entity(original_limit)
        return {
            "processed_events": len(events),
            "alerts_created": len(alerts),
            "alert_ids": [a.alert_id for a in alerts]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in KYT post-confirmation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ops")
async def get_alerts_ops(
    days: int = Query(7, ge=1, le=90),
    buckets: str = Query("24h,3d,7d,>7d"),
    current_user: dict = Depends(get_current_user_strict)
) -> Dict[str, Any]:
    """
    Operational alerts breakdown for dashboard ops widgets.

    Returns counts per age bucket and severity.
    """
    try:
        # Parse buckets like "24h,3d,7d,>7d"
        bucket_list = [b.strip() for b in buckets.split(",") if b.strip()]
        # Use alert_service to fetch recent alerts and aggregate
        until = datetime.utcnow()
        since = until - timedelta(days=days)
        alerts = alert_service.get_recent_alerts_since(since=since)
        out: Dict[str, Any] = {b: {"total": 0, "by_severity": {s.value: 0 for s in AlertSeverity}} for b in bucket_list}

        def bucket_for(ts: datetime) -> str:
            age = until - ts
            if age <= timedelta(hours=24) and "24h" in out:
                return "24h"
            if age <= timedelta(days=3) and "3d" in out:
                return "3d"
            if age <= timedelta(days=7) and "7d" in out:
                return "7d"
            return ">7d" if ">7d" in out else bucket_list[-1]

        for a in alerts:
            try:
                ts = datetime.fromisoformat(str(a.timestamp))  # AlertEngine uses isoformat
            except Exception:
                ts = until
            b = bucket_for(ts)
            out[b]["total"] += 1
            sev = getattr(a.severity, "value", str(a.severity))
            if sev not in out[b]["by_severity"]:
                out[b]["by_severity"][sev] = 0
            out[b]["by_severity"][sev] += 1

        # Build flat alias used by FE widget (bucket->total)
        alert_aging = {bucket: data.get("total", 0) for bucket, data in out.items()}

        return {
            "since": since.isoformat(),
            "until": until.isoformat(),
            "buckets": out,
            "alert_aging": alert_aging,
        }
    except Exception as e:
        logger.error(f"Error computing alerts ops: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/effectiveness")
async def get_rule_effectiveness(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user_strict)
) -> List[Dict[str, Any]]:
    """
    Returns a simple effectiveness ranking per rule id.
    """
    try:
        until = datetime.utcnow()
        since = until - timedelta(days=days)
        alerts = alert_service.get_recent_alerts_since(since=since)
        stat: Dict[str, Dict[str, Any]] = {}
        for a in alerts:
            rid = getattr(a, "alert_type", None)
            rid = getattr(rid, "value", str(rid or "unknown"))
            s = stat.setdefault(rid, {"rule": rid, "total_alerts": 0, "fp_rate": 0.0, "acknowledged": 0})
            s["total_alerts"] += 1
            if getattr(a, "acknowledged", False):
                s["acknowledged"] += 1
        # naive fp_rate proxy: unacknowledged ratio
        for s in stat.values():
            total = max(1, s["total_alerts"])
            s["fp_rate"] = (total - s["acknowledged"]) / total
        items = sorted(stat.values(), key=lambda x: (x["fp_rate"], x["total_alerts"]), reverse=True)
        return items[:limit]
    except Exception as e:
        logger.error(f"Error computing rule effectiveness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_alerts_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user_strict)
) -> Dict[str, Any]:
    """
    Summary for dashboard: totals, by_severity and last_activity.
    """
    try:
        until = datetime.utcnow()
        since = until - timedelta(days=days)
        alerts = alert_service.get_recent_alerts_since(since=since)
        total = len(alerts)
        by_sev: Dict[str, int] = {s.value: 0 for s in AlertSeverity}
        by_type: Dict[str, int] = {}
        last_ts = None
        # build recent list with minimal fields used by FE
        recent_items: List[Dict[str, Any]] = []
        for a in alerts:
            sev = getattr(a.severity, "value", str(a.severity))
            by_sev[sev] = by_sev.get(sev, 0) + 1
            atype = getattr(getattr(a, "alert_type", None), "value", str(getattr(a, "alert_type", "unknown")))
            by_type[atype] = by_type.get(atype, 0) + 1
            title = getattr(a, "title", None) or atype.replace("_", " ").title()
            recent_items.append({
                "title": title,
                "severity": sev,
                "timestamp": str(getattr(a, "timestamp", ""))
            })
            try:
                ts = datetime.fromisoformat(str(a.timestamp))
                if not last_ts or ts > last_ts:
                    last_ts = ts
            except Exception:
                pass
        # sort recent by timestamp descending best-effort
        try:
            recent_items.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        except Exception:
            pass
        # best-effort suppression rate (0.0 if not available)
        suppression_rate = 0.0
        try:
            # if suppression data exists, compute share suppr. vs total in window (optional)
            se = alert_service.get_suppression_events(limit=1000)
            suppression_rate = min(1.0, (len(se) / max(1, total))) if se else 0.0
        except Exception:
            suppression_rate = 0.0
        return {
            "total_alerts": total,
            "by_severity": by_sev,
            "by_type": by_type,
            "suppression_rate": suppression_rate,
            "recent_alerts": recent_items[:10],
            "last_activity": (last_ts or until).isoformat(),
            "window": {"since": since.isoformat(), "until": until.isoformat()},
        }
    except Exception as e:
        logger.error(f"Error computing alerts summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis/annotations")
async def get_annotation_kpis(
    days: int = Query(30, ge=1, le=365, description="Time window in days for KPI calculations"),
    current_user: dict = Depends(get_current_user_strict)
) -> Dict[str, Any]:
    """
    Returns annotation-based KPI summary (disposition stats and MTTD) for the given window.
    """
    try:
        until = datetime.utcnow()
        since = until - timedelta(days=days)
        summary = alert_annotation_service.get_kpi_summary(since=since, until=until)
        return summary
    except Exception as e:
        logger.error(f"Error computing annotation KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ... rest of the code remains the same ...
@router.get("/recent", response_model=List[AlertResponse])
async def get_recent_alerts(
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    current_user: dict = Depends(get_current_user_strict)
) -> List[AlertResponse]:
    """
    Get recent alerts
    
    **Query Parameters:**
    - limit: Maximum number of alerts to return (default: 100)
    - severity: Filter by severity (low, medium, high, critical)
    """
    try:
        severity_enum = AlertSeverity(severity) if severity else None
        alerts = alert_service.get_recent_alerts(limit=limit, severity=severity_enum)
        
        return [AlertResponse(**alert.to_dict()) for alert in alerts]
    
    except Exception as e:
        logger.error(f"Error getting recent alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(current_user: dict = Depends(get_current_user_strict)) -> AlertStatsResponse:
    """
    Get alert statistics
    
    Returns:
    - total_alerts: Total number of alerts
    - by_severity: Alert count by severity level
    - by_type: Alert count by type
    - unacknowledged: Number of unacknowledged alerts
    """
    try:
        stats = alert_service.get_alert_stats()
        return AlertStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting alert stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-batch")
async def process_event_batch(request: BatchProcessRequest, current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Process a batch of events
    
    **Request Body:**
    - events: List of events to process
    - max_alerts_per_entity: Optional override for entity limit
    """
    try:
        # Temporarily override entity limit if specified
        original_limit = None
        if request.max_alerts_per_entity is not None:
            original_limit = alert_service.get_max_rules_per_entity()
            alert_service.set_max_rules_per_entity(request.max_alerts_per_entity)
        
        alerts = await alert_service.process_event_batch(request.events)
        
        # Restore original limit
        if original_limit is not None:
            alert_service.set_max_rules_per_entity(original_limit)
        
        return {
            "processed_events": len(request.events),
            "alerts_created": len(alerts),
            "alert_ids": [alert.alert_id for alert in alerts]
        }
    except Exception as e:
        logger.error(f"Error processing event batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Acknowledge an alert
    
    **Path Parameters:**
    - alert_id: Alert ID to acknowledge
    """
    try:
        success = alert_service.acknowledge_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"status": "acknowledged", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def trigger_test_alert(current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Trigger a test alert (for testing notification channels)
    """
    try:
        # Create test event
        test_event = {
            "address": "0x0000000000000000000000000000000000000000",
            "risk_score": 0.95,
            "risk_factors": ["Test alert"],
            "labels": ["test"],
            "test_mode": True
        }
        
        alerts = await alert_service.process_event(test_event)
        
        return {
            "status": "test_alert_triggered",
            "alerts_triggered": len(alerts),
            "alert_ids": [a.alert_id for a in alerts]
        }
    
    except Exception as e:
        logger.error(f"Error triggering test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    
@router.get("/suppressions", response_model=List[SuppressionEventResponse])
async def get_suppression_events(
    limit: int = Query(100, ge=1, le=1000),
    reason: Optional[str] = Query(None, description="Filter by suppression reason"),
    current_user: dict = Depends(get_current_user_strict)
) -> List[Dict]:
    """
    Get suppression events for audit purposes

    **Query Parameters:**
    - limit: Maximum number of suppression events to return (default: 100)
    - reason: Filter by suppression reason (e.g., "dedup_window")
    """
    try:
        suppression_events = alert_service.get_suppression_events(limit=limit, reason=reason)

        return [event.to_dict() for event in suppression_events]
    except Exception as e:
        logger.error(f"Error getting suppression events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suppressions/export")
async def export_suppression_events(
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(1000, ge=1, le=10000),
    current_user: dict = Depends(get_current_user_strict)
) -> Dict[str, str]:
    """
    Export suppression events for analysis

    **Query Parameters:**
    - format: Export format (json or csv)
    - limit: Maximum number of events to export (default: 1000)
    """
    try:
        exported_data = alert_service.export_suppression_events(format=format, limit=limit)
        return {
            "format": format,
            "count": min(limit, alert_service.get_suppression_events_count()),
            "data": exported_data
        }
    except Exception as e:
        logger.error(f"Error exporting suppression events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suppressions/statistics")
async def get_suppression_statistics(current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Get detailed suppression statistics and analysis
    """
    try:
        stats = alert_service.get_suppression_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting suppression statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suppressions/clear")
async def clear_suppression_events(current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Clear all suppression events (for testing/debugging)
    """
    try:
        cleared_count = alert_service.clear_suppression_events()
        logger.info(f"Cleared {cleared_count} suppression events")
        return {"cleared_count": cleared_count, "status": "success"}
    except Exception as e:
        logger.error(f"Error clearing suppression events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/correlation/rules")
async def get_correlation_rules(current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Get available correlation rules and their configurations
    """
    try:
        rules = alert_service.correlation_rules

        return {
            "rules": rules,
            "total_rules": len(rules),
            "supported_patterns": list(set(
                pattern
                for rule in rules.values()
                for pattern in rule["patterns"]
            ))
        }
    except Exception as e:
        logger.error(f"Error getting correlation rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/correlation/test")
async def test_correlation_rule(request: Dict[str, Any], current_user: dict = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """
    Test a correlation rule with sample alerts

    **Request Body:**
    - rule_name: Name of the correlation rule to test
    - sample_alerts: List of sample alerts to test against
    """
    try:
        rule_name = request.get("rule_name")
        sample_alerts = request.get("sample_alerts", [])

        if not rule_name or rule_name not in alert_service.correlation_rules:
            raise HTTPException(status_code=400, detail="Invalid correlation rule name")

        rule_config = alert_service.correlation_rules[rule_name]

        # Convert sample alerts to Alert objects (use engine types)
        from app.services.alert_engine import Alert, AlertType, AlertSeverity

        alerts = []
        for alert_data in sample_alerts:
            alert = Alert(
                alert_type=AlertType(alert_data.get("alert_type", "high_risk_address")),
                severity=AlertSeverity(alert_data.get("severity", "medium")),
                title=alert_data.get("title", "Test Alert"),
                description=alert_data.get("description", "Test Description"),
                metadata=alert_data.get("metadata", {}),
                address=alert_data.get("address"),
                tx_hash=alert_data.get("tx_hash")
            )
            alerts.append(alert)

        # Test the correlation
        result = alert_service.matches_correlation_rule(
            alerts[0] if alerts else Alert(
                alert_type=AlertType.HIGH_RISK_ADDRESS,
                severity=AlertSeverity.MEDIUM,
                title="Test",
                description="Test",
                metadata={},
                address="0x123"
            ),
            alerts,
            rule_config
        )

        return {
            "rule_name": rule_name,
            "matches": result,
            "rule_config": rule_config,
            "sample_alerts_count": len(alerts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing correlation rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation/analysis")
async def get_correlation_analysis(
    time_window: int = Query(3600, ge=60, le=86400, description="Time window in seconds"),
    min_severity: str = Query("medium", pattern="^(low|medium|high|critical)$"),
    current_user: dict = Depends(get_current_user_strict)
) -> Dict[str, Any]:
    """
    Get correlation analysis for recent alerts

    **Query Parameters:**
    - time_window: Time window in seconds (default: 3600 = 1 hour)
    - min_severity: Minimum severity level to consider
    """
    try:
        # Get recent alerts within time window via service
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        severity_map = {
            "low": AlertSeverity.LOW,
            "medium": AlertSeverity.MEDIUM,
            "high": AlertSeverity.HIGH,
            "critical": AlertSeverity.CRITICAL,
        }
        min_sev = severity_map[min_severity]
        filtered_alerts = alert_service.get_recent_alerts_since(since=cutoff_time, min_severity=min_sev)

        # Analyze correlations via service facade
        correlations_found = 0
        correlation_details = []

        for rule_name, rule_config in alert_service.correlation_rules.items():
            for i, alert in enumerate(filtered_alerts):
                remaining_alerts = filtered_alerts[i+1:]
                if alert_service.matches_correlation_rule(alert, remaining_alerts, rule_config):
                    correlations_found += 1
                    correlation_details.append({
                        "rule_name": rule_name,
                        "triggering_alert": alert.alert_type.value,
                        "matched_alerts": len(rule_config.get("patterns", [])),
                        "severity": alert.severity.value,
                    })
                    break

        return {
            "time_window_seconds": time_window,
            "min_severity": min_severity,
            "total_alerts_analyzed": len(filtered_alerts),
            "correlations_found": correlations_found,
            "correlation_rate": correlations_found / max(1, len(filtered_alerts)),
            "correlation_details": correlation_details[:10],
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting correlation analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


    
