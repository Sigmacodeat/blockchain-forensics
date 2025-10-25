import os
import sys
import pathlib
import pytest

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.multi_chain import MultiChainForensics, EthereumAdapter  # noqa: E402


@pytest.mark.asyncio
async def test_engine_caching_evmlike(monkeypatch):
    # Ensure caching enabled
    monkeypatch.setenv("ENABLE_SCAN_CACHE", "1")
    monkeypatch.setenv("SCAN_CACHE_TTL", "120")

    engine = MultiChainForensics()
    engine.active_chains = {"ethereum"}

    # Counter to track adapter calls
    call_counter = {"count": 0}

    def fake_get_adapter(self, chain_id):
        # Return a lightweight stub with the paged method
        class Stub(EthereumAdapter):
            async def get_address_transactions_paged(self, address: str, limit: int = 100, from_block=None, to_block=None):
                call_counter["count"] += 1
                return [{"tx_hash": "0xabc", "block_number": 123, "chain": chain_id, "chain_type": "evm"}]

        # Minimal ChainInfo for stub
        from app.services.multi_chain import ChainInfo, ChainType
        ci = ChainInfo(chain_id=chain_id, name="Ethereum", symbol="ETH", chain_type=ChainType.EVM, rpc_urls=["http://dummy"])
        return Stub(ci)

    monkeypatch.setattr(engine.adapter_factory, "get_adapter", fake_get_adapter.__get__(engine.adapter_factory))

    params = dict(from_block=1000, to_block=1010)
    res1 = await engine.get_address_transactions_paged("ethereum", "0xTARGET", limit=5, **params)
    res2 = await engine.get_address_transactions_paged("ethereum", "0xTARGET", limit=5, **params)

    assert res1 == res2
    # Adapter should be called only once due to cache hit
    assert call_counter["count"] == 1
