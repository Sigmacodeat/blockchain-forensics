import sys
import pathlib
import pytest

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.multi_chain import ChainInfo, ChainType, EthereumAdapter, BitcoinAdapter  # noqa: E402


@pytest.mark.asyncio
async def test_eth_get_address_transactions_paged_range(monkeypatch):
    ci = ChainInfo(chain_id="ethereum", name="Ethereum", symbol="ETH", chain_type=ChainType.EVM, rpc_urls=["http://dummy"])
    adapter = EthereumAdapter(ci)

    async def fake_make_request(self, method, params=None):
        if method == "eth_getBlockByNumber":
            bn = int(params[0], 16)
            # address appears in 200..198
            if bn in (200, 199, 198):
                return {"result": {"transactions": [
                    {"hash": f"0x{bn}a", "from": "0xTARGET", "to": "0xabc"}
                ]}}
            return {"result": {"transactions": []}}
        if method == "eth_getTransactionByHash":
            return {"result": {
                "blockNumber": hex(200),
                "from": "0xTARGET",
                "to": "0xabc",
                "value": hex(0),
                "gasPrice": hex(1),
                "gas": hex(21000),
            }}
        raise AssertionError(method)

    monkeypatch.setattr(EthereumAdapter, "make_request", fake_make_request, raising=True)

    txs = await adapter.get_address_transactions_paged("0xtarget", limit=2, from_block=198, to_block=200)
    assert len(txs) == 2


@pytest.mark.asyncio
async def test_btc_get_address_transactions_paged_range(monkeypatch):
    ci = ChainInfo(chain_id="bitcoin", name="Bitcoin", symbol="BTC", chain_type=ChainType.UTXO, rpc_urls=["http://dummy"], native_currency={"name": "Bitcoin", "symbol": "BTC", "decimals": 8})
    adapter = BitcoinAdapter(ci)

    async def fake_make_request(self, method, params=None):
        if method == "getblockhash":
            h = params[0]
            return {"result": f"hash{h}"}
        if method == "getblock":
            h = int(params[0].replace("hash", ""))
            if h in (300, 299):
                txs = [{"txid": f"tx-{h}", "vin": [{}], "vout": [{"scriptPubKey": {"addresses": ["1TARGET"]}}]}]
            else:
                txs = []
            return {"result": {"time": 1700000000, "tx": txs}}
        raise AssertionError(method)

    monkeypatch.setattr(BitcoinAdapter, "make_request", fake_make_request, raising=True)

    txs = await adapter.get_address_transactions_paged("1TARGET", limit=5, start_height=295, end_height=300)
    assert len(txs) == 2
