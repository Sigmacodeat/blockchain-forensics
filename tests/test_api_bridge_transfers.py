import os
import sys
import pathlib
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.main import app  # noqa: E402
from app.api.v1.forensics import BridgeTransfer  # noqa: E402
from app.services import multi_chain as mc_mod  # noqa: E402
from app.services.compliance import compliance_manager  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_bridge_transfers_basic(monkeypatch, client):
    # Fake transfers
    fake_transfers = [
        {
            "chain": "ethereum",
            "address": "0xBridge",
            "tx_hash": "0xabc",
            "log_index": 1,
            "block_number": 12345,
            "event_name": "Transfer",
            "sender": "0xfrom",
            "receiver": "0xto",
            "amount": 1000,
            "token": "0xtoken",
            "confidence": 0.95,
            "topics": ["0xddf..."],
            "data": "0x...",
        }
    ]

    async def fake_get_transfers(start_time, end_time):
        assert isinstance(start_time, datetime)
        assert isinstance(end_time, datetime)
        return fake_transfers

    monkeypatch.setattr(mc_mod.multi_chain_engine, "get_cross_chain_transfers", fake_get_transfers, raising=True)

    st = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    et = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()

    resp = client.get(
        "/api/v1/forensics/bridge/transfers",
        params={"start_time": st, "end_time": et},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["transfers"][0]["event_name"] == "Transfer"


def test_bridge_transfers_with_evidence(monkeypatch, client):
    async def fake_get_transfers(start_time, end_time):
        return []

    class E:
        def __init__(self):
            self.evidence_id = "evid-123"
            self.collection_timestamp = datetime.now(timezone.utc)
            self.chain_of_custody = []

    def fake_create_evidence_record(**kwargs):
        return E()

    monkeypatch.setattr(mc_mod.multi_chain_engine, "get_cross_chain_transfers", fake_get_transfers, raising=True)
    monkeypatch.setattr(compliance_manager, "create_evidence_record", fake_create_evidence_record, raising=True)

    st = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    et = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()

    resp = client.get(
        "/api/v1/forensics/bridge/transfers",
        params={"start_time": st, "end_time": et, "case_id": "CASE-1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["evidence_id"] == "evid-123"
