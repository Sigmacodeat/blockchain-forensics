from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.alert_engine import alert_engine, AlertSeverity, Alert, AlertType  # re-use engine types


class AlertService:
    """Facade über die Alert Engine für lose Kopplung der API/Worker.
    Ermöglicht spätere Migration/Ersetzung der Engine ohne API-Änderungen.
    """

    # Query operations
    def get_recent_alerts(self, *, limit: int, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        return alert_engine.get_recent_alerts(limit=limit, severity=severity)

    def get_recent_alerts_since(self, *, since: datetime, min_severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Return alerts after a cutoff time, optionally filtering by minimum severity."""
        alerts = [a for a in alert_engine.alerts if getattr(a, "timestamp", datetime.min) > since]
        if min_severity is not None:
            rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            alerts = [a for a in alerts if rank.get(a.severity.value, 0) >= rank.get(min_severity.value, 0)]
        return alerts

    def get_alert_stats(self) -> Dict[str, Any]:
        return alert_engine.get_alert_stats()

    def list_rules(self) -> List[Any]:
        """Return the current set of alert rules from the engine."""
        return list(getattr(alert_engine, "rules", []) or [])

    def reload_policies(self) -> Dict[str, Any]:
        """Reload active policy rules in the engine and return summary."""
        alert_engine.load_active_policies()
        rules = (alert_engine.policy_rules or {}).get("rules", []) if getattr(alert_engine, "policy_rules", None) else []
        return {"rules": rules, "total_rules": len(rules)}

    # Processing operations
    async def process_event_batch(self, events: List[Dict[str, Any]]) -> List[Alert]:
        return await alert_engine.process_event_batch(events)

    async def process_event(self, event: Dict[str, Any]) -> List[Alert]:
        return await alert_engine.process_event(event)

    # Alert management
    def acknowledge_alert(self, alert_id: str) -> bool:
        return alert_engine.acknowledge_alert(alert_id)

    async def dispatch_manual_alert(self, alert: Alert) -> None:
        """Append a manually created alert and best-effort notify sinks."""
        alert_engine.alerts.append(alert)
        try:
            await alert_engine._send_notifications(alert)
        except Exception:
            pass

    # Suppressions
    def get_suppression_events(self, *, limit: int, reason: Optional[str] = None) -> List[Any]:
        return alert_engine.get_suppression_events(limit=limit, reason=reason)

    def export_suppression_events(self, *, format: str, limit: int) -> str:
        return alert_engine.export_suppression_events(format=format, limit=limit)

    def get_suppression_statistics(self) -> Dict[str, Any]:
        return alert_engine.get_suppression_statistics()

    def clear_suppression_events(self) -> int:
        """Clear all suppression events and return cleared count."""
        try:
            count = len(alert_engine.suppression_events)
        except Exception:
            count = 0
        try:
            alert_engine.suppression_events.clear()
        except Exception:
            pass
        return count

    def get_suppression_events_count(self) -> int:
        try:
            return len(alert_engine.suppression_events)
        except Exception:
            return 0

    # Engine configuration passthrough (kept minimal)
    def get_max_rules_per_entity(self) -> Optional[int]:
        return getattr(alert_engine, "max_rules_per_entity", None)

    def set_max_rules_per_entity(self, value: int) -> None:
        setattr(alert_engine, "max_rules_per_entity", value)

    # Correlation access passthrough
    @property
    def correlation_rules(self) -> Dict[str, Any]:
        return alert_engine.correlation_engine.correlation_rules

    def matches_correlation_rule(self, trigger: Alert, candidates: List[Alert], rule_config: Dict[str, Any]) -> bool:
        return alert_engine.correlation_engine._matches_correlation_rule(trigger, candidates, rule_config)

    # Engine readiness / cache info
    def is_engine_ready(self) -> bool:
        return isinstance(getattr(alert_engine, "alerts", None), list)

    def cached_alerts_count(self) -> int:
        try:
            return len(alert_engine.alerts)
        except Exception:
            return 0


alert_service = AlertService()
