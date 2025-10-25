import os
import sys
import pathlib
import pytest
from datetime import datetime, timedelta

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.multi_chain import MultiChainForensics, EthereumAdapter  # noqa: E402


@pytest.mark.asyncio
async def test_get_cross_chain_transfers_evmlogs(monkeypatch):
    engine = MultiChainForensics()

    # Nur Ethereum aktiv
    engine.active_chains = {"ethereum"}

    # Bridge-Konfiguration per Env
    monkeypatch.setenv(
        "BRIDGE_CONTRACTS_JSON",
        '{"ethereum": ["0xBridge1234567890abcdef1234567890abcdef1234"]}'
    )

    # Mock estimate_block_range_for_time und make_request auf EthereumAdapter Ebene
    async def fake_estimate(self, start_ts, end_ts, max_scan=5000):
        return {"from_block": 1000, "to_block": 1010}

    async def fake_make_request(self, method, params=None):
        if method == "eth_getLogs":
            flt = params[0]
            assert flt["address"].lower() == "0xbridge1234567890abcdef1234567890abcdef1234".lower()
            assert flt["fromBlock"] == hex(1000)
            assert flt["toBlock"] == hex(1010)
            return {
                "result": [
                    {
                        "transactionHash": "0xtx1",
                        "logIndex": hex(1),
                        "blockNumber": hex(1001),
                        "data": "0xdeadbeef",
                        "topics": [
                            "0x1111111111111111111111111111111111111111111111111111111111111111"
                        ],
                    },
                    {
                        "transactionHash": "0xtx2",
                        "logIndex": hex(0),
                        "blockNumber": hex(1002),
                        "data": "0xcafebabe",
                        "topics": [],
                    },
                ]
            }
        if method == "eth_blockNumber":
            return {"result": hex(1010)}
        if method == "eth_getBlockByNumber":
            # Used potentially by timestamp helper if called (should not be necessary due to fake_estimate)
            return {"result": {"timestamp": hex(int(datetime.utcnow().timestamp()))}}
        raise AssertionError(f"Unexpected method {method}")

    monkeypatch.setattr(EthereumAdapter, "estimate_block_range_for_time", fake_estimate, raising=True)
    monkeypatch.setattr(EthereumAdapter, "make_request", fake_make_request, raising=True)

    start = datetime.utcnow() - timedelta(hours=1)
    end = datetime.utcnow()

    transfers = await engine.get_cross_chain_transfers(start, end)

    assert len(transfers) == 2
    assert {t["tx_hash"] for t in transfers} == {"0xtx1", "0xtx2"}
    for t in transfers:
        assert t["chain"] == "ethereum"
        assert t["address"].lower() == "0xbridge1234567890abcdef1234567890abcdef1234".lower()
        assert isinstance(t["block_number"], int)
        assert "topics" in t
