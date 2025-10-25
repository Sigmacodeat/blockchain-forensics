import sys
import pathlib
import types
import pytest
from datetime import datetime

# Ensure backend on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.streaming.event_consumer import EventConsumer  # noqa: E402


@pytest.mark.asyncio
async def test_event_consumer_process_event_minimal(monkeypatch):
    # Mocks for dependencies used inside process_event
    # labels_service
    ls_mod = __import__("app.enrichment.labels_service", fromlist=["labels_service"]).labels_service
    async def _get_labels(addr):
        return []
    monkeypatch.setattr(ls_mod, "get_labels", _get_labels)

    # bridge_detector
    bd_mod = __import__("app.bridge.bridge_detector", fromlist=["bridge_detector"]).bridge_detector
    async def _detect_bridge(event):
        return None
    monkeypatch.setattr(bd_mod, "detect_bridge", _detect_bridge)

    # alert_policy_service
    aps_mod = __import__("app.services.alert_policy_service", fromlist=["alert_policy_service"]).alert_policy_service
    def _get_active_rules():
        return []
    monkeypatch.setattr(aps_mod, "get_active_rules", _get_active_rules)

    # neo4j_client
    n4j_mod = __import__("app.db.neo4j_client", fromlist=["neo4j_client"]).neo4j_client
    async def _store_event(evt):
        return None
    monkeypatch.setattr(n4j_mod, "store_event", _store_event)

    # Build minimal canonical-like dict
    now = datetime.utcnow()
    event_data = {
        "event_id": "e-test",
        "chain": "ethereum",
        "block_number": 1,
        "block_timestamp": now,
        "tx_hash": "0xabc",
        "tx_index": 0,
        "from_address": "0x1111111111111111111111111111111111111111",
        "to_address": "0x2222222222222222222222222222222222222222",
        "value": "0",
        "value_usd": None,
        "gas_used": 0,
        "gas_price": 0,
        "fee": "0",
        "status": 1,
        "error_message": None,
        "event_type": "transfer",
        "contract_address": None,
        "method_name": None,
        "token_address": None,
        "token_symbol": None,
        "token_decimals": None,
        "risk_score": None,
        "cluster_id": None,
        "idempotency_key": "k-test",
        "source": "test",
        "metadata": {},
        "ingested_at": now,
    }

    consumer = EventConsumer()
    ok = await consumer.process_event(event_data)
    assert ok is True
