"""
Alerts v2 - Stateful DSL mit Deduplication/Suppression

Features:
- Stateful DSL für komplexe Alert-Regeln
- Deduplication und Suppression
- P95 Latenz <2s End-to-End
- Playbooks für automatische Response
- Rule Engine mit State-Management
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib

from app.db.redis_client import redis_client
from app.config import settings
from app.services.evidence_vault import evidence_vault
from app.services.soar_engine import soar_engine

logger = logging.getLogger(__name__)


class AlertState(str, Enum):
    """Alert States für Stateful Processing"""
    ACTIVE = "active"
    SUPPRESSED = "suppressed"
    DEDUPLICATED = "deduplicated"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AlertCondition:
    """Bedingung für Alert-Regel"""
    field: str
    operator: str  # eq, ne, gt, lt, contains, regex, in
    value: Any
    weight: float = 1.0


@dataclass
class AlertRule:
    """Stateful Alert Rule mit DSL"""
    rule_id: str
    name: str
    description: str
    conditions: List[AlertCondition]
    severity: AlertSeverity
    stateful: bool = True
    deduplication_window: int = 3600  # Sekunden
    suppression_rules: List[Dict[str, Any]] = field(default_factory=list)
    playbook_actions: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True

    def evaluate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluiere Regel gegen Event"""
        score = 0.0
        matched_conditions = []

        for condition in self.conditions:
            if self._check_condition(event, condition):
                score += condition.weight
                matched_conditions.append(condition)

        if matched_conditions:
            return {
                "rule_id": self.rule_id,
                "score": score,
                "matched_conditions": len(matched_conditions),
                "severity": self.severity.value,
                "metadata": {
                    "rule_name": self.name,
                    "total_conditions": len(self.conditions),
                    "match_ratio": len(matched_conditions) / len(self.conditions)
                }
            }
        return None

    def _check_condition(self, event: Dict[str, Any], condition: AlertCondition) -> bool:
        """Prüfe einzelne Bedingung"""
        field_value = self._get_nested_value(event, condition.field)
        if field_value is None:
            return False

        op = condition.operator
        val = condition.value

        if op == "eq":
            return field_value == val
        elif op == "ne":
            return field_value != val
        elif op == "gt":
            return float(field_value) > float(val)
        elif op == "lt":
            return float(field_value) < float(val)
        elif op == "gte":
            return float(field_value) >= float(val)
        elif op == "lte":
            return float(field_value) <= float(val)
        elif op == "contains":
            return str(val) in str(field_value)
        elif op == "regex":
            import re
            return bool(re.search(str(val), str(field_value)))
        elif op == "in":
            return field_value in val
        elif op == "not_in":
            return field_value not in val

        return False

    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """Hole verschachtelten Wert aus Dict"""
        keys = path.split('.')
        current = obj
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current


@dataclass
class AlertInstance:
    """Alert Instance mit State"""
    alert_id: str
    rule_id: str
    event_data: Dict[str, Any]
    state: AlertState
    severity: AlertSeverity
    score: float
    created_at: datetime
    last_updated: datetime
    suppression_until: Optional[datetime] = None
    deduplication_key: Optional[str] = None
    playbook_execution_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "rule_id": self.rule_id,
            "event_data": self.event_data,
            "state": self.state.value,
            "severity": self.severity.value,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "suppression_until": self.suppression_until.isoformat() if self.suppression_until else None,
            "deduplication_key": self.deduplication_key,
            "playbook_execution_count": self.playbook_execution_count
        }


class AlertEngineV2:
    """Stateful Alert Engine mit DSL"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, AlertInstance] = {}
        self.deduplication_cache: Dict[str, datetime] = {}
        self.suppression_cache: Dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule):
        """Füge Alert-Regel hinzu"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name} ({rule.rule_id})")

    def remove_rule(self, rule_id: str):
        """Entferne Alert-Regel"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Hole Alert-Regel"""
        return self.rules.get(rule_id)

    def list_rules(self) -> List[Dict[str, Any]]:
        """Liste alle Regeln"""
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
                "conditions_count": len(rule.conditions)
            }
            for rule in self.rules.values()
        ]

    async def process_event(self, event: Dict[str, Any]) -> List[AlertInstance]:
        """Verarbeite Event gegen alle Regeln mit Stateful Logic"""
        triggered_alerts = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Prüfe Suppression für diese Regel
            if await self._is_suppressed(rule.rule_id, event):
                continue

            # Evaluiere Regel
            match_result = rule.evaluate(event)
            if not match_result:
                continue

            # Erstelle Alert Instance
            alert_id = self._generate_alert_id(rule.rule_id, event)
            dedup_key = self._generate_deduplication_key(rule, event)

            # Prüfe Deduplication
            if await self._is_deduplicated(dedup_key, rule.deduplication_window):
                # Erstelle deduplizierten Alert falls noch nicht vorhanden
                if alert_id not in self.active_alerts:
                    alert = AlertInstance(
                        alert_id=alert_id,
                        rule_id=rule.rule_id,
                        event_data=event,
                        state=AlertState.DEDUPLICATED,
                        severity=rule.severity,
                        score=match_result["score"],
                        created_at=datetime.now(),
                        last_updated=datetime.now(),
                        deduplication_key=dedup_key
                    )
                    self.active_alerts[alert_id] = alert
                    triggered_alerts.append(alert)
                    try:
                        await evidence_vault.append(
                            "alert_deduplicated",
                            {"alert": alert.to_dict()},
                            {"source": "alerts_v2"}
                        )
                    except Exception:
                        pass
                    try:
                        enriched = {
                            **event,
                            "alert_id": alert.alert_id,
                            "rule_id": rule.rule_id,
                            "severity": rule.severity.value,
                            "score": match_result["score"],
                            "state": AlertState.DEDUPLICATED.value,
                        }
                        soar_engine.run(enriched)
                    except Exception:
                        pass
                continue

            # Erstelle neuen Alert
            alert = AlertInstance(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                event_data=event,
                state=AlertState.ACTIVE,
                severity=rule.severity,
                score=match_result["score"],
                created_at=datetime.now(),
                last_updated=datetime.now(),
                deduplication_key=dedup_key
            )

            self.active_alerts[alert_id] = alert
            triggered_alerts.append(alert)
            try:
                await evidence_vault.append(
                    "alert_active",
                    {"alert": alert.to_dict()},
                    {"source": "alerts_v2"}
                )
            except Exception:
                pass
            try:
                enriched = {
                    **event,
                    "alert_id": alert.alert_id,
                    "rule_id": rule.rule_id,
                    "severity": rule.severity.value,
                    "score": match_result["score"],
                    "state": AlertState.ACTIVE.value,
                }
                soar_engine.run(enriched)
            except Exception:
                pass

            # Führe Playbook Actions aus
            await self._execute_playbook(rule, alert)

        return triggered_alerts

    async def suppress_alert(self, alert_id: str, duration_seconds: int, reason: str):
        """Supprimiere Alert für bestimmte Zeit"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.state = AlertState.SUPPRESSED
            alert.suppression_until = datetime.now() + timedelta(seconds=duration_seconds)
            alert.last_updated = datetime.now()
            alert.event_data["suppression_reason"] = reason

            # Cache Suppression
            suppression_key = f"suppression:{alert_id}"
            self.suppression_cache[suppression_key] = alert.suppression_until

            await self._persist_suppression(suppression_key, alert.suppression_until)

    async def resolve_alert(self, alert_id: str, resolution: str):
        """Resolve Alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.state = AlertState.RESOLVED
            alert.last_updated = datetime.now()
            alert.event_data["resolution"] = resolution

    async def suppress_rule_for_event(self, rule_id: str, event: Dict[str, Any], duration_seconds: int, reason: str) -> Dict[str, Any]:
        key = f"suppression:{rule_id}:{hash(str(event))}"
        until = datetime.now() + timedelta(seconds=duration_seconds)
        self.suppression_cache[key] = until
        await self._persist_suppression(key, until)
        return {"rule_id": rule_id, "until": until.isoformat(), "reason": reason}

    async def unsuppress_rule_for_event(self, rule_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        key = f"suppression:{rule_id}:{hash(str(event))}"
        if key in self.suppression_cache:
            del self.suppression_cache[key]
        await self._remove_persisted_suppression(key)
        return {"rule_id": rule_id, "removed": True}

    def get_active_alerts(self, rule_id: Optional[str] = None, state: Optional[AlertState] = None) -> List[AlertInstance]:
        """Hole aktive Alerts mit optionalen Filtern"""
        alerts = list(self.active_alerts.values())

        if rule_id:
            alerts = [a for a in alerts if a.rule_id == rule_id]

        if state:
            alerts = [a for a in alerts if a.state == state]

        return alerts

    async def _is_suppressed(self, rule_id: str, event: Dict[str, Any]) -> bool:
        """Prüfe ob Regel/Event supprimiert ist"""
        suppression_key = f"suppression:{rule_id}:{hash(str(event))}"
        if suppression_key in self.suppression_cache:
            until = self.suppression_cache[suppression_key]
            if datetime.now() < until:
                return True
            else:
                # Expired, remove from cache
                del self.suppression_cache[suppression_key]
                await self._remove_persisted_suppression(suppression_key)

        return False

    async def _is_deduplicated(self, dedup_key: str, window_seconds: int) -> bool:
        """Prüfe Deduplication"""
        if dedup_key in self.deduplication_cache:
            last_seen = self.deduplication_cache[dedup_key]
            if datetime.now() - last_seen < timedelta(seconds=window_seconds):
                return True

        # Update cache
        self.deduplication_cache[dedup_key] = datetime.now()
        return False

    async def _execute_playbook(self, rule: AlertRule, alert: AlertInstance):
        """Führe Playbook Actions aus"""
        for action in rule.playbook_actions:
            try:
                action_type = action.get("type")
                if action_type == "notify":
                    await self._execute_notify_action(action, alert)
                elif action_type == "escalate":
                    await self._execute_escalate_action(action, alert)
                elif action_type == "block":
                    await self._execute_block_action(action, alert)
                elif action_type == "custom":
                    await self._execute_custom_action(action, alert)

                alert.playbook_execution_count += 1

            except Exception as e:
                logger.error(f"Playbook action failed: {e}")

    async def _execute_notify_action(self, action: Dict[str, Any], alert: AlertInstance):
        """Führe Notify Action aus"""
        channels = action.get("channels", ["email"])
        message = action.get("message", f"Alert triggered: {alert.event_data}")

        # Hier würde echte Notification-Logic stehen
        logger.info(f"NOTIFICATION: {channels} - {message}")

    async def _execute_escalate_action(self, action: Dict[str, Any], alert: AlertInstance):
        """Führe Escalate Action aus"""
        alert.state = AlertState.ESCALATED
        alert.last_updated = datetime.now()

        # Hier würde Escalation-Logic stehen (z.B. an höhere Instanz)

    async def _execute_block_action(self, action: Dict[str, Any], alert: AlertInstance):
        """Führe Block Action aus"""
        # Hier würde Blocking-Logic stehen (z.B. Adresse blockieren)

    async def _execute_custom_action(self, action: Dict[str, Any], alert: AlertInstance):
        """Führe Custom Action aus"""
        # Hier würde Custom Logic stehen

    def _generate_alert_id(self, rule_id: str, event: Dict[str, Any]) -> str:
        """Generiere unique Alert ID"""
        content = f"{rule_id}:{json.dumps(event, sort_keys=True)}"
        return f"alert_{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def _generate_deduplication_key(self, rule: AlertRule, event: Dict[str, Any]) -> str:
        """Generiere Deduplication Key"""
        # Vereinfacht: hash der kritischen Felder
        key_fields = [c.field for c in rule.conditions if c.weight > 0.5][:3]  # Top 3 fields
        key_data = {field: event.get(field) for field in key_fields}
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    async def _persist_suppression(self, key: str, until: datetime):
        """Persistiere Suppression in Redis"""
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client:
                await client.setex(key, int((until - datetime.now()).total_seconds()), "1")
        except Exception:
            pass

    async def _remove_persisted_suppression(self, key: str):
        """Entferne persistierte Suppression"""
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client:
                await client.delete(key)
        except Exception:
            pass


# Singleton
alert_engine_v2 = AlertEngineV2()


# Beispiel-Regeln
def create_default_rules():
    """Erstelle Standard-Alert-Regeln"""

    # High-Risk Transfer Rule
    high_risk_rule = AlertRule(
        rule_id="high_risk_transfer",
        name="High-Risk Transfer Detection",
        description="Detect transfers involving high-risk addresses",
        conditions=[
            AlertCondition(field="amount", operator="gt", value=10000, weight=1.0),
            AlertCondition(field="risk_score", operator="gte", value=0.7, weight=2.0),
            AlertCondition(field="sanctions_match", operator="eq", value=True, weight=3.0)
        ],
        severity=AlertSeverity.HIGH,
        deduplication_window=1800,  # 30 Minuten
        suppression_rules=[
            {"condition": "already_investigated", "duration_seconds": 86400}
        ],
        playbook_actions=[
            {"type": "notify", "channels": ["email", "slack"], "message": "High-risk transfer detected"},
            {"type": "escalate", "to": "senior_analyst"}
        ]
    )

    # Mixer Usage Rule
    mixer_rule = AlertRule(
        rule_id="mixer_usage",
        name="Cryptocurrency Mixer Usage",
        description="Detect usage of mixing services",
        conditions=[
            AlertCondition(field="to_address", operator="in", value=["tornado_cash_address"], weight=3.0),
            AlertCondition(field="amount", operator="gt", value=1000, weight=1.0)
        ],
        severity=AlertSeverity.CRITICAL,
        deduplication_window=3600,
        playbook_actions=[
            {"type": "notify", "channels": ["email", "slack", "pagerduty"]},
            {"type": "block", "block_address": True}
        ]
    )

    alert_engine_v2.add_rule(high_risk_rule)
    alert_engine_v2.add_rule(mixer_rule)


# Initialize default rules
create_default_rules()
