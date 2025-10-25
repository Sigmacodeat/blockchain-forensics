from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, field_validator

from app.db.postgres import postgres_client
from app.compliance.rule_engine import rule_engine


class MonitorRule(BaseModel):
    id: str
    name: str
    version: int
    enabled: bool
    scope: str
    severity: str
    expression: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @field_validator("expression", mode="before")
    @classmethod
    def _parse_expression(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return v
        return v


class MonitorService:
    async def list_rules(self) -> List[MonitorRule]:
        async with postgres_client.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id::text, name, version, enabled, scope, severity, expression, created_at, updated_at
                FROM monitor_rules
                ORDER BY updated_at DESC
                """
            )
        return [
            MonitorRule(
                id=r["id"],
                name=r["name"],
                version=r["version"],
                enabled=r["enabled"],
                scope=r["scope"],
                severity=r["severity"],
                expression=r["expression"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    async def create_rule(self, name: str, scope: str, severity: str, expression: Dict[str, Any], enabled: bool) -> MonitorRule:
        # basic validation by attempting evaluation against empty data
        _ = rule_engine.evaluate(expression, {})
        async with postgres_client.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO monitor_rules (name, scope, severity, expression, enabled)
                VALUES ($1, $2, $3, $4::jsonb, $5)
                RETURNING id::text, name, version, enabled, scope, severity, expression, created_at, updated_at
                """,
                name, scope, severity, json.dumps(expression), enabled,
            )
        return MonitorRule(**row)

    async def toggle_rule(self, rule_id: str) -> MonitorRule:
        async with postgres_client.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE monitor_rules
                SET enabled = NOT enabled, updated_at = NOW()
                WHERE id = $1::uuid
                RETURNING id::text, name, version, enabled, scope, severity, expression, created_at, updated_at
                """,
                rule_id,
            )
        if not row:
            raise ValueError("rule not found")
        return MonitorRule(**row)

    async def validate_rule(self, expression: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ok = rule_engine.evaluate(expression, {})
            return {"valid": True, "dry_run": ok}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        rule_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        chain: Optional[str] = None,
        age_bucket: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        query = [
            "SELECT id::text, rule_id::text, entity_type, entity_id, chain, severity, status, assignee::text, first_seen_at, last_seen_at, hits, context",
            "FROM monitor_alerts",
        ]
        conds = []
        params: List[Any] = []
        if status:
            conds.append("status = $%d" % (len(params) + 1))
            params.append(status)
        if severity:
            conds.append("severity = $%d" % (len(params) + 1))
            params.append(severity)
        if rule_id:
            conds.append("rule_id::text ILIKE $%d" % (len(params) + 1))
            params.append(f"%{rule_id}%")
        if entity_id:
            conds.append("entity_id ILIKE $%d" % (len(params) + 1))
            params.append(f"%{entity_id}%")
        if chain:
            conds.append("chain = $%d" % (len(params) + 1))
            params.append(chain)
        if age_bucket:
            # Age bucket filter based on first_seen_at
            now = datetime.utcnow()
            if age_bucket == "24h":
                conds.append("first_seen_at >= $%d" % (len(params) + 1))
                params.append(now - timedelta(hours=24))
            elif age_bucket == "3d":
                conds.append("first_seen_at >= $%d" % (len(params) + 1))
                params.append(now - timedelta(days=3))
            elif age_bucket == "7d":
                conds.append("first_seen_at >= $%d" % (len(params) + 1))
                params.append(now - timedelta(days=7))
            elif age_bucket == ">7d":
                conds.append("first_seen_at < $%d" % (len(params) + 1))
                params.append(now - timedelta(days=7))
        if conds:
            query.append("WHERE " + " AND ".join(conds))
        query.append("ORDER BY last_seen_at DESC LIMIT $%d" % (len(params) + 1))
        params.append(limit)
        sql = "\n".join(query)
        async with postgres_client.acquire() as conn:
            rows = await conn.fetch(sql, *params)
        return [dict(r) for r in rows]

    async def update_alert(
        self,
        alert_id: str,
        *,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        async with postgres_client.acquire() as conn:
            # Update main alert
            sets = []
            params: List[Any] = []
            if status:
                sets.append("status = $%d" % (len(params) + 1))
                params.append(status)
            if assignee:
                sets.append("assignee = $%d::uuid" % (len(params) + 1))
                params.append(assignee)
            if sets:
                params.append(alert_id)
                row = await conn.fetchrow(
                    f"""
                    UPDATE monitor_alerts SET {', '.join(sets)}, last_seen_at = NOW()
                    WHERE id = ${len(params)}::uuid
                    RETURNING id::text, rule_id::text, entity_type, entity_id, chain, severity, status, assignee::text, first_seen_at, last_seen_at, hits, context
                    """,
                    *params,
                )
                if not row:
                    raise ValueError("alert not found")
            else:
                row = await conn.fetchrow(
                    """
                    SELECT id::text, rule_id::text, entity_type, entity_id, chain, severity, status, assignee::text, first_seen_at, last_seen_at, hits, context
                    FROM monitor_alerts WHERE id = $1::uuid
                    """,
                    alert_id,
                )
                if not row:
                    raise ValueError("alert not found")

            # Add note event if provided
            if note:
                await conn.execute(
                    """
                    INSERT INTO monitor_alert_events (alert_id, type, payload)
                    VALUES ($1::uuid, 'note_added', $2::jsonb)
                    """,
                    alert_id,
                    json.dumps({"note": note})
                )
        return dict(row)

    async def list_alert_events(self, alert_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        async with postgres_client.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, alert_id::text, created_at, actor::text, type, payload
                FROM monitor_alert_events
                WHERE alert_id = $1::uuid
                ORDER BY created_at DESC
                LIMIT $2
                """,
                alert_id, limit,
            )
        return [dict(r) for r in rows]


monitor_service = MonitorService()
