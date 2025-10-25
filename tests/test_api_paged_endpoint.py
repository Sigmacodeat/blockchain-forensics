import os
import sys
import pathlib
import pytest
from fastapi.testclient import TestClient

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.main import app  # noqa: E402
from app.services.multi_chain import multi_chain_engine  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_forensics_paged_endpoint_evmlike(monkeypatch, client):
    # Mock engine to return deterministic data
    async def fake_paged(chain_id, address, limit=100, **kwargs):
        assert chain_id == "ethereum"
        assert address.lower() == "0xtarget"
        assert kwargs.get("from_block") == 100
        assert kwargs.get("to_block") == 110
        return [
            {"tx_hash": "0x1", "block_number": 105, "chain": chain_id, "chain_type": "evm"},
            {"tx_hash": "0x2", "block_number": 104, "chain": chain_id, "chain_type": "evm"},
        ]

    monkeypatch.setattr(
        multi_chain_engine, "get_address_transactions_paged", fake_paged, raising=True
    )

    resp = client.get(
        "/api/v1/forensics/address/ethereum/0xTARGET/transactions",
        params={"from_block": 100, "to_block": 110, "limit": 2},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["chain"] == "ethereum"
    assert data["address"].lower() == "0xtarget"
    assert data["total"] == 2
    assert len(data["result"]) == 2


def test_forensics_paged_endpoint_utxo(monkeypatch, client):
    # Mock engine to return deterministic data
    async def fake_paged(chain_id, address, limit=100, **kwargs):
        assert chain_id == "bitcoin"
        assert address == "1TARGET"
        assert kwargs.get("start_height") == 1000
        assert kwargs.get("end_height") == 1010
        return [
            {"tx_hash": "tx1", "block_height": 1005, "chain": chain_id, "chain_type": "utxo"}
        ]

    monkeypatch.setattr(
        multi_chain_engine, "get_address_transactions_paged", fake_paged, raising=True
    )

    resp = client.get(
        "/api/v1/forensics/address/bitcoin/1TARGET/transactions",
        params={"start_height": 1000, "end_height": 1010, "limit": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["chain"] == "bitcoin"
    assert data["address"] == "1TARGET"
    assert data["total"] == 1
    assert len(data["result"]) == 1
