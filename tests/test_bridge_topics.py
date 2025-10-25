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
async def test_bridge_topics_filter(monkeypatch):
    engine = MultiChainForensics()
    engine.active_chains = {"ethereum"}

    addr = "0xBridge1234567890abcdef1234567890abcdef1234"
    topic0 = "0x1111111111111111111111111111111111111111111111111111111111111111"

    monkeypatch.setenv("BRIDGE_CONTRACTS_JSON", f'{{"ethereum": ["{addr}"]}}')
    monkeypatch.setenv("BRIDGE_TOPICS_JSON", f'{{"ethereum": {{"{addr}": ["{topic0}"]}}}}')

    # capture last filter
    seen_filters = []

    async def fake_estimate(self, start_ts, end_ts, max_scan=5000):
        return {"from_block": 2000, "to_block": 2001}

    async def fake_make_request(self, method, params=None):
        if method == "eth_getLogs":
            seen_filters.append(params[0])
            return {"result": []}
        if method == "eth_blockNumber":
            return {"result": hex(2001)}
        if method == "eth_getBlockByNumber":
            return {"result": {"timestamp": hex(int(datetime.utcnow().timestamp()))}}
        raise AssertionError(method)

    monkeypatch.setattr(EthereumAdapter, "estimate_block_range_for_time", fake_estimate, raising=True)
    monkeypatch.setattr(EthereumAdapter, "make_request", fake_make_request, raising=True)

    start = datetime.utcnow() - timedelta(hours=1)
    end = datetime.utcnow()
    _ = await engine.get_cross_chain_transfers(start, end)

    assert seen_filters, "eth_getLogs was not called"
    f = seen_filters[-1]
    assert f["address"].lower() == addr.lower()
    assert f.get("topics") == [topic0]
