from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.services.alerts_v2 import alert_engine_v2, AlertRule, AlertCondition, AlertSeverity, AlertState
from app.auth.dependencies import require_plan

router = APIRouter()


class AlertConditionModel(BaseModel):
    field: str = Field(..., min_length=1)
    operator: str = Field(..., regex="^(eq|ne|gt|lt|gte|lte|contains|regex|in|not_in)$")
    value: Any
    weight: float = Field(1.0, ge=0.0)


class AlertRuleModel(BaseModel):
    rule_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field("", min_length=0)
    conditions: List[AlertConditionModel] = Field(..., min_items=1)
    severity: AlertSeverity = AlertSeverity.MEDIUM
    stateful: bool = True
    deduplication_window: int = Field(3600, ge=60)
    suppression_rules: List[Dict[str, Any]] = Field(default_factory=list)
    playbook_actions: List[Dict[str, Any]] = Field(default_factory=list)
    enabled: bool = True


class ProcessEventRequest(BaseModel):
    event: Dict[str, Any] = Field(..., description="Event data to process against alert rules")


@router.post("/rules", status_code=status.HTTP_201_CREATED, tags=["Alerts v2"])
async def create_alert_rule(rule: AlertRuleModel, current_user: dict = Depends(require_plan("plus"))):
    """Erstelle neue Alert-Regel"""
    try:
        alert_rule = AlertRule(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            conditions=[AlertCondition(**cond.dict()) for cond in rule.conditions],
            severity=rule.severity,
            stateful=rule.stateful,
            deduplication_window=rule.deduplication_window,
            suppression_rules=rule.suppression_rules,
            playbook_actions=rule.playbook_actions,
            enabled=rule.enabled
        )

        alert_engine_v2.add_rule(alert_rule)
        return {"status": "Rule created", "rule_id": rule.rule_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rule creation failed: {str(e)}")


@router.get("/rules", tags=["Alerts v2"])
async def list_alert_rules(current_user: dict = Depends(require_plan("plus"))):
    """Liste alle Alert-Regeln"""
    try:
        rules = alert_engine_v2.list_rules()
        return {"rules": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule listing failed: {str(e)}")


@router.post("/rules/validate", tags=["Alerts v2"])
async def validate_alert_rule(rule: AlertRuleModel, current_user: dict = Depends(require_plan("plus"))):
    """Validiert eine Alert-Regel strukturell und semantisch (Operatoren/Typen)."""
    try:
        # Pydantic stellt bereits Struktur/Typsicherheit sicher; wir validieren ergänzend die Operators/Values
        _ = [AlertCondition(**cond.dict()) for cond in rule.conditions]
        _ = AlertRule(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            conditions=[AlertCondition(**cond.dict()) for cond in rule.conditions],
            severity=rule.severity,
            stateful=rule.stateful,
            deduplication_window=rule.deduplication_window,
            suppression_rules=rule.suppression_rules,
            playbook_actions=rule.playbook_actions,
            enabled=rule.enabled,
        )
        return {"valid": True, "errors": []}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}


@router.get("/rules/{rule_id}", tags=["Alerts v2"])
async def get_alert_rule(rule_id: str, current_user: dict = Depends(require_plan("plus"))):
    """Hole spezifische Alert-Regel"""
    try:
        rule = alert_engine_v2.get_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        return {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "description": rule.description,
            "conditions": [
                {
                    "field": cond.field,
                    "operator": cond.operator,
                    "value": cond.value,
                    "weight": cond.weight
                }
                for cond in rule.conditions
            ],
            "severity": rule.severity.value,
            "stateful": rule.stateful,
            "deduplication_window": rule.deduplication_window,
            "enabled": rule.enabled
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule retrieval failed: {str(e)}")


@router.delete("/rules/{rule_id}", tags=["Alerts v2"])
async def delete_alert_rule(rule_id: str, current_user: dict = Depends(require_plan("plus"))):
    """Lösche Alert-Regel"""
    try:
        alert_engine_v2.remove_rule(rule_id)
        return {"status": "Rule deleted", "rule_id": rule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule deletion failed: {str(e)}")


@router.post("/process-event", tags=["Alerts v2"])
async def process_alert_event(req: ProcessEventRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(require_plan("plus"))):
    """Verarbeite Event gegen alle Alert-Regeln"""
    try:
        # Async processing für bessere Performance
        background_tasks.add_task(alert_engine_v2.process_event, req.event)

        return {"status": "Event queued for processing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event processing failed: {str(e)}")


@router.get("/alerts", tags=["Alerts v2"])
async def list_active_alerts(
    rule_id: Optional[str] = Query(None, description="Filter by rule ID"),
    state: Optional[AlertState] = Query(None, description="Filter by alert state"),
    limit: int = Query(50, ge=1, le=1000)
    ,
    current_user: dict = Depends(require_plan("plus"))
):
    """Liste aktive Alerts mit Filtern"""
    try:
        alerts = alert_engine_v2.get_active_alerts(rule_id, state)
        alerts = alerts[:limit]  # Pagination

        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert listing failed: {str(e)}")


@router.post("/alerts/{alert_id}/suppress", tags=["Alerts v2"])
async def suppress_alert(
    alert_id: str,
    duration_seconds: int = Query(3600, ge=60, le=604800),  # 1min to 7 days
    reason: str = Query(..., min_length=1, max_length=500),
    current_user: dict = Depends(require_plan("plus"))
):
    """Supprimiere Alert"""
    try:
        await alert_engine_v2.suppress_alert(alert_id, duration_seconds, reason)
        return {"status": "Alert suppressed", "alert_id": alert_id, "until": (datetime.now() + timedelta(seconds=duration_seconds)).isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert suppression failed: {str(e)}")


@router.post("/rules/{rule_id}/suppress-for-event", tags=["Alerts v2"])
async def suppress_rule_for_event(
    rule_id: str,
    req: ProcessEventRequest,
    duration_seconds: int = Query(3600, ge=60, le=604800),
    reason: str = Query(..., min_length=1, max_length=500),
    current_user: dict = Depends(require_plan("plus"))
):
    """Supprimiere eine Regel für ein spezifisches Event (stateful)."""
    try:
        info = await alert_engine_v2.suppress_rule_for_event(rule_id, req.event, duration_seconds, reason)
        return {"status": "Rule suppressed for event", **info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule suppression failed: {str(e)}")


@router.post("/rules/{rule_id}/unsuppress-for-event", tags=["Alerts v2"])
async def unsuppress_rule_for_event(
    rule_id: str,
    req: ProcessEventRequest,
    current_user: dict = Depends(require_plan("plus"))
):
    """Entferne Suppression für eine Regel und ein spezifisches Event."""
    try:
        info = await alert_engine_v2.unsuppress_rule_for_event(rule_id, req.event)
        return {"status": "Rule unsuppressed for event", **info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule unsuppression failed: {str(e)}")


@router.post("/alerts/{alert_id}/resolve", tags=["Alerts v2"])
async def resolve_alert(
    alert_id: str,
    resolution: str = Query(..., min_length=1, max_length=500),
    current_user: dict = Depends(require_plan("plus"))
):
    """Resolve Alert"""
    try:
        await alert_engine_v2.resolve_alert(alert_id, resolution)
        return {"status": "Alert resolved", "alert_id": alert_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert resolution failed: {str(e)}")


@router.get("/stats", tags=["Alerts v2"])
async def get_alerts_stats(current_user: dict = Depends(require_plan("plus"))):
    """Statistiken über Alert Engine"""
    try:
        active_alerts = alert_engine_v2.get_active_alerts()
        rules = alert_engine_v2.list_rules()

        stats = {
            "total_rules": len(rules),
            "enabled_rules": len([r for r in rules if r["enabled"]]),
            "total_active_alerts": len(active_alerts),
            "alerts_by_state": {},
            "alerts_by_severity": {},
            "alerts_by_rule": {}
        }

        for alert in active_alerts:
            # By state
            state = alert.state.value
            stats["alerts_by_state"][state] = stats["alerts_by_state"].get(state, 0) + 1

            # By severity
            severity = alert.severity.value
            stats["alerts_by_severity"][severity] = stats["alerts_by_severity"].get(severity, 0) + 1

            # By rule
            rule_id = alert.rule_id
            stats["alerts_by_rule"][rule_id] = stats["alerts_by_rule"].get(rule_id, 0) + 1

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.post("/test-rule", tags=["Alerts v2"])
async def test_alert_rule(rule: AlertRuleModel, test_event: Dict[str, Any], current_user: dict = Depends(require_plan("plus"))):
    """Teste Alert-Regel gegen Test-Event"""
    try:
        alert_rule = AlertRule(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            conditions=[AlertCondition(**cond.dict()) for cond in rule.conditions],
            severity=rule.severity,
            stateful=rule.stateful,
            deduplication_window=rule.deduplication_window,
            suppression_rules=rule.suppression_rules,
            playbook_actions=rule.playbook_actions,
            enabled=rule.enabled
        )

        result = alert_rule.evaluate(test_event)

        return {
            "rule_tested": rule.rule_id,
            "event": test_event,
            "match_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rule test failed: {str(e)}")
