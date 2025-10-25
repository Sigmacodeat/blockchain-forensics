import os
import sys
import pathlib
import pytest
import json

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.bridge.detection import BridgeDetectionService  # noqa: E402
from app.bridge.registry import BridgeContract  # noqa: E402
from app.schemas.canonical_event import CanonicalEvent  # noqa: E402
from datetime import datetime  # noqa: E402


def _evt(meta: dict | None = None, to: str | None = None, contract: str | None = None):
    return CanonicalEvent(
        event_id="e",
        chain="ethereum",
        block_number=1,
        block_timestamp=datetime.utcnow(),
        tx_hash="0xabc",
        tx_index=0,
        from_address="0xfrom",
        to_address=to,
        value=0,
        value_usd=None,
        gas_used=0,
        gas_price=0,
        fee=0,
        status=1,
        error_message=None,
        event_type="bridge",
        contract_address=contract,
        method_name=None,
        token_address=None,
        token_symbol=None,
        token_decimals=None,
        risk_score=None,
        cluster_id=None,
        idempotency_key="k",
        source="rpc",
        metadata=meta or {},
    )


def test_infer_destination_from_metadata(monkeypatch):
    svc = BridgeDetectionService()
    contract = BridgeContract(address="0xbridge", chain="ethereum", name="TestBridge", bridge_type="lock", counterpart_chains=["solana", "polygon"], method_selectors=[])  # type: ignore
    ev = _evt(meta={"destination_chain": "solana"}, to="0xbridge")
    # Direct call of private method for focused test
    dest = svc._infer_destination_chain(ev, contract, raw_tx=None)
    assert dest == "solana"


def test_infer_destination_single_counterpart(monkeypatch):
    svc = BridgeDetectionService()
    contract = BridgeContract(address="0xbridge", chain="ethereum", name="TestBridge", bridge_type="lock", counterpart_chains=["polygon"], method_selectors=[])  # type: ignore
    ev = _evt(meta={}, to="0xbridge")
    dest = svc._infer_destination_chain(ev, contract, raw_tx=None)
    assert dest == "polygon"


def test_infer_destination_from_topics(monkeypatch):
    # Configure topic->chain mapping via env JSON
    monkeypatch.setenv("BRIDGE_TOPICS_CHAIN_HINTS", json.dumps({"0xdeadbeef": "arbitrum"}))

    svc = BridgeDetectionService()
    contract = BridgeContract(address="0xbridge", chain="ethereum", name="TestBridge", bridge_type="lock", counterpart_chains=["solana", "arbitrum"], method_selectors=[])  # type: ignore
    ev = _evt(meta={}, to="0xbridge")
    class _Topic:
        def __init__(self, s):
            self._s = s
        def hex(self):
            return self._s
    raw_tx = {"logs": [{"topics": [_Topic("0xdeadbeef")]}]}
    dest = svc._infer_destination_chain(ev, contract, raw_tx)
    assert dest == "arbitrum"
