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
async def test_eth_get_address_transactions_in_range(monkeypatch):
    chain_info = ChainInfo(
        chain_id="ethereum",
        name="Ethereum",
        symbol="ETH",
        chain_type=ChainType.EVM,
        rpc_urls=["http://dummy"]
    )
    adapter = EthereumAdapter(chain_info)

    async def fake_make_request(self, method, params=None):
        if method == "eth_getBlockByNumber":
            bn = int(params[0], 16)
            # only include target on blocks 101, 100
            if bn in (100, 101):
                return {"result": {"transactions": [
                    {"hash": f"0x{bn}a", "from": "0xTARGET", "to": "0xabc"},
                    {"hash": f"0x{bn}b", "from": "0xabc", "to": "0xother"},
                ]}}
            return {"result": {"transactions": [
                {"hash": f"0x{bn}z", "from": "0xabc", "to": "0xother"}
            ]}}
        if method == "eth_getTransactionByHash":
            return {"result": {
                "blockNumber": hex(100),
                "from": "0xTARGET",
                "to": "0xabc",
                "value": hex(0),
                "gasPrice": hex(1),
                "gas": hex(21000),
            }}
        raise AssertionError(method)

    monkeypatch.setattr(EthereumAdapter, "make_request", fake_make_request, raising=True)

    txs = await adapter.get_address_transactions_in_range("0xtarget", 95, 105, limit=2)
    assert len(txs) == 2
    assert all(tx["chain_type"] == "evm" for tx in txs)


@pytest.mark.asyncio
async def test_btc_get_address_transactions_in_range(monkeypatch):
    chain_info = ChainInfo(
        chain_id="bitcoin",
        name="Bitcoin",
        symbol="BTC",
        chain_type=ChainType.UTXO,
        rpc_urls=["http://dummy"],
        native_currency={"name": "Bitcoin", "symbol": "BTC", "decimals": 8},
    )
    adapter = BitcoinAdapter(chain_info)

    async def fake_make_request(self, method, params=None):
        if method == "getblockhash":
            h = params[0]
            return {"result": f"hash{h}"}
        if method == "getblock":
            h = int(params[0].replace("hash", ""))
            # include target at heights 50 and 49
            if h in (49, 50):
                txs = [
                    {"txid": f"tx-{h}-a", "vin": [{}], "vout": [{"scriptPubKey": {"addresses": ["1TARGET"]}}]},
                    {"txid": f"tx-{h}-b", "vin": [{}], "vout": [{"scriptPubKey": {"addresses": ["1OTHER"]}}]},
                ]
            else:
                txs = [{"txid": f"tx-{h}-z", "vin": [{}], "vout": [{"scriptPubKey": {"addresses": ["1OTHER"]}}]}]
            return {"result": {"time": 1700000000, "tx": txs}}
        raise AssertionError(method)

    monkeypatch.setattr(BitcoinAdapter, "make_request", fake_make_request, raising=True)

    txs = await adapter.get_address_transactions_in_range("1TARGET", 45, 55, limit=3)
    assert len(txs) == 2
    assert all(tx["chain_type"] == "utxo" for tx in txs)
