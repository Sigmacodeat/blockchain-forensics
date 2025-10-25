"""Monitor Consumer (WP1)
Consumes canonical events, evaluates rules, and persists alerts.
This module exposes a `process_event` function for unit/integration tests
and a `run_once` helper that polls Kafka a single message (optional).
"""
from __future__ import annotations
import json
import logging
from typing import Any, Dict, Optional, Tuple

from app.compliance.rule_engine import rule_engine
from app.compliance.monitor_service import monitor_service
from app.db.postgres import postgres_client
from app.metrics import (
    RULE_EVAL_TOTAL,
    RULE_EVAL_LATENCY,
    E2E_EVENT_ALERT_LATENCY,
    ALERTS_CREATED_TOTAL,
    KAFKA_EVENTS_CONSUMED,
    KAFKA_PROCESSING_DURATION,
    KAFKA_CONSUMER_LAG,
)

logger = logging.getLogger(__name__)


async def _list_enabled_rules() -> list[dict]:
    rules = await monitor_service.list_rules()
    return [r.model_dump() for r in rules if r.enabled]


def _derive_entity(event: Dict[str, Any]) -> Tuple[str, str, str]:
    """Derive entity_type, entity_id, chain from canonical event-like dict.
    Fallbacks are conservative. This function assumes an EVM-style event may include
    `from_address`, `to_address`, `tx_hash`, and `chain`.
    """
    chain = event.get("chain") or "unknown"
    tx_hash = event.get("tx_hash") or event.get("transaction_hash")
    from_addr = (event.get("from_address") or "").lower()
    to_addr = (event.get("to_address") or "").lower()

    # Prefer transaction entity if tx_hash present; otherwise address
    if tx_hash:
        return ("tx", tx_hash, chain)
    if to_addr:
        return ("address", to_addr, chain)
    if from_addr:
        return ("address", from_addr, chain)
    return ("unknown", "n/a", chain)


def _enrich_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort enrichment for cross-chain/bridge fields used by rules.
    - Propagate metadata.event_type/bridge/chain_from/chain_to
    - Derive chains_involved and cross_chain_hops if possible
    """
    enriched = dict(event)
    meta = event.get("metadata") or {}
    # event_type
    if not enriched.get("event_type") and isinstance(meta, dict):
        et = meta.get("event_type")
        if et:
            enriched["event_type"] = et
    # bridge name
    if not enriched.get("bridge") and isinstance(meta, dict):
        br = meta.get("bridge")
        if br:
            enriched["bridge"] = br
    # chains
    chain_from = event.get("chain_from") or meta.get("chain_from")
    chain_to = event.get("chain_to") or meta.get("chain_to")
    if chain_from:
        enriched["chain_from"] = chain_from
    if chain_to:
        enriched["chain_to"] = chain_to
    # chains_involved heuristic
    if not enriched.get("chains_involved"):
        if chain_from and chain_to and str(chain_from) != str(chain_to):
            enriched["chains_involved"] = 2
        else:
            enriched["chains_involved"] = 1 if (chain_from or chain_to or event.get("chain")) else 0
    # cross_chain_hops best-effort
    if enriched.get("cross_chain_hops") is None:
        hop = event.get("hop") or meta.get("hop")
        try:
            if hop is not None:
                enriched["cross_chain_hops"] = int(hop)
        except Exception:
            pass
    return enriched


async def _persist_alert(rule: dict, entity_type: str, entity_id: str, chain: str, context: Dict[str, Any]) -> Optional[str]:
    """Insert or update alert hit window (increments `hits`, updates `last_seen_at`)."""
    async with postgres_client.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO monitor_alerts (rule_id, entity_type, entity_id, chain, severity, status, first_seen_at, last_seen_at, hits, context)
            VALUES ($1::uuid, $2, $3, $4, $5, 'open', NOW(), NOW(), 1, $6::jsonb)
            ON CONFLICT DO NOTHING
            RETURNING id::text
            """,
            rule["id"], entity_type, entity_id, chain, rule["severity"], json.dumps(context)
        )
        if row and row.get("id"):
            alert_id = row["id"]
            await conn.execute(
                """
                INSERT INTO monitor_alert_events (alert_id, type, payload)
                VALUES ($1::uuid, 'created', $2::jsonb)
                """,
                alert_id, json.dumps({"reason": "rule_hit"})
            )
            return alert_id
        # If already exists, update last_seen and increment hits
        await conn.execute(
            """
            UPDATE monitor_alerts
            SET last_seen_at = NOW(), hits = hits + 1
            WHERE rule_id = $1::uuid AND entity_type = $2 AND entity_id = $3
            """,
            rule["id"], entity_type, entity_id
        )
        return None


async def process_event(event: Dict[str, Any]) -> int:
    """Evaluate all enabled rules against the provided event dict.
    Returns number of alerts (new) created.
    """
    import time
    e2e_start = time.time()
    enabled = await _list_enabled_rules()
    created = 0
    # Enrich for cross-chain/bridge rules
    event_enriched = _enrich_event(event)
    entity_type, entity_id, chain = _derive_entity(event_enriched)

    for rule in enabled:
        rule_name = rule.get("name", "unknown")
        try:
            t0 = time.time()
            hit = rule_engine.evaluate(rule["expression"], event_enriched)
            try:
                RULE_EVAL_LATENCY.labels(rule=rule_name).observe(time.time() - t0)
            except Exception:
                pass
            if hit:
                ctx = {"matched": True, "event_keys": list(event_enriched.keys())}
                alert_id = await _persist_alert(rule, entity_type, entity_id, chain, ctx)
                if alert_id:
                    try:
                        ALERTS_CREATED_TOTAL.labels(severity=rule.get("severity", "unknown")).inc()
                    except Exception:
                        pass
                    created += 1
                try:
                    RULE_EVAL_TOTAL.labels(rule=rule_name, outcome="hit").inc()
                except Exception:
                    pass
            else:
                try:
                    RULE_EVAL_TOTAL.labels(rule=rule_name, outcome="miss").inc()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"rule evaluation error (rule={rule.get('name')}): {e}")
            try:
                RULE_EVAL_TOTAL.labels(rule=rule_name, outcome="error").inc()
            except Exception:
                pass
            continue
    try:
        E2E_EVENT_ALERT_LATENCY.observe(time.time() - e2e_start)
    except Exception:
        pass
    return created


async def run_once(timeout: float = 0.5) -> int:
    """Poll Kafka once from `ingest.events` and process a single event if available.
    Returns number of newly created alerts from that message.
    """
    # Import Kafka client directly to avoid fragile reflection
    from app.messaging.kafka_client import KafkaConsumerClient, KafkaTopics  # type: ignore
    import time as _t
    consumer = KafkaConsumerClient(group_id="monitor-consumer", topics=[KafkaTopics.INGEST_EVENTS])
    try:
        _start = _t.time()
        msg = consumer.consume_events(timeout=timeout)
        if not msg:
            return 0
        event = msg["event"].model_dump()
        created = await process_event(event)
        consumer.commit(msg["message"])  # commit only on success
        # Metrics best-effort
        try:
            KAFKA_EVENTS_CONSUMED.labels(topic=KafkaTopics.INGEST_EVENTS).inc()
            KAFKA_PROCESSING_DURATION.labels(topic=KafkaTopics.INGEST_EVENTS).observe(max(0.0, _t.time() - _start))
            # consumer lag gauge
            lag = consumer.get_lag(msg["message"]) if hasattr(consumer, "get_lag") else None
            if lag is not None:
                try:
                    part = msg["message"].partition()
                    KAFKA_CONSUMER_LAG.labels(topic=KafkaTopics.INGEST_EVENTS, partition=str(part)).set(lag)
                except Exception:
                    pass
        except Exception:
            pass
        return created
    finally:
        consumer.close()
