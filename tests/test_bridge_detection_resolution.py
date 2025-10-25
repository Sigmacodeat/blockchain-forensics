import os
import json
import pytest

from app.bridge.detection import resolve_counterpart_chain
from app.bridge.bridge_detector import bridge_detector
from app.schemas.canonical_event import CanonicalEvent
from datetime import datetime


def test_resolve_counterpart_chain_with_topic_hint(monkeypatch):
    # Map a dummy topic to 'arbitrum'
    topic0 = "0x23be8e12e420b5da9fb98d8102572f640fb3c11a0085060472dfc0ed194b3cf7"  # Arbitrum MessageDelivered in registry
    hints = {topic0: "arbitrum"}
    monkeypatch.setenv("BRIDGE_TOPICS_CHAIN_HINTS", json.dumps(hints))

    receipt = {
        "logs": [
            {
                "address": "0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a",
                "topics": [topic0],
            }
        ]
    }

    dest = resolve_counterpart_chain(receipt, to_addr="0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a", chain="ethereum")
    assert dest == "arbitrum"


@pytest.mark.asyncio
async def test_bridge_detector_matches_event_signature_from_metadata_logs():
    # Use Wormhole LogMessagePublished topic from registry
    topic0 = "0x6eb224fb001ed210e379b335e35efe88672a8ce935d981a6896b27ffdf52a3b2"
    event = CanonicalEvent(
        event_id="e1",
        chain="ethereum",
        block_number=1,
        block_timestamp=datetime.utcnow(),
        tx_hash="0xabc",
        tx_index=0,
        from_address="0x1111111111111111111111111111111111111111",
        to_address="0x98f3c9e6e3face36baad05fe09d375ef1464288b",  # Wormhole Core Bridge from registry
        value="0",
        value_usd=None,
        gas_used=0,
        gas_price=0,
        fee="0",
        status=1,
        error_message=None,
        event_type="contract_call",
        contract_address="0x98f3c9e6e3face36baad05fe09d375ef1464288b",
        method_name=None,
        token_address=None,
        token_symbol=None,
        token_decimals=None,
        risk_score=None,
        cluster_id=None,
        idempotency_key="k1",
        source="test",
        metadata={
            "logs": [
                {
                    "address": "0x98f3c9e6e3face36baad05fe09d375ef1464288b",
                    "topics": [topic0],
                }
            ]
        },
    )

    bridge = await bridge_detector.detect_bridge(event)
    assert bridge is not None
    assert bridge.get("bridge_name") == "Wormhole"
    assert bridge.get("chain_from") == "ethereum"
