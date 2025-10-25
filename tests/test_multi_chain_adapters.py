import asyncio
import os
import sys
import pathlib
import pytest

# Ensure backend/ is on PYTHONPATH so that 'app' package is importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.multi_chain import ChainInfo, ChainType, EthereumAdapter, BitcoinAdapter


@pytest.mark.asyncio
async def test_eth_get_address_transactions_filters_and_limits(monkeypatch):
    # Arrange
    chain_info = ChainInfo(
        chain_id="ethereum",
        name="Ethereum",
        symbol="ETH",
        chain_type=ChainType.EVM,
        rpc_urls=["http://localhost:8545"],
    )
    adapter = EthereumAdapter(chain_info)

    # Limit Scan depth env
    monkeypatch.setenv("ETH_SCAN_MAX_BLOCKS", "5")

    # Mock _get_block_timestamp to avoid extra RPCs
    async def _fake_ts(_self, _bn):
        return 1700000000

    monkeypatch.setattr(EthereumAdapter, "_get_block_timestamp", _fake_ts, raising=True)

    # Mock make_request
    async def fake_make_request(self, method, params=None):
        if method == "eth_blockNumber":
            return {"result": hex(20)}  # latest block = 32 decimal? Actually 0x14 = 20
        if method == "eth_getBlockByNumber":
            # Return two blocks with transactions
            block_hex = params[0]
            full = params[1]
            assert full is True
            bn = int(block_hex, 16)
            # Create tx where target is involved only in block 20 and 19
            if bn in (20, 19):
                txs = [
                    {"hash": f"0xhash{bn}a", "from": "0xabc", "to": "0xtarget"},
                    {"hash": f"0xhash{bn}b", "from": "0xtarget", "to": "0xdef"},
                    {"hash": f"0xhash{bn}c", "from": "0xother", "to": "0xother2"},
                ]
            else:
                txs = [
                    {"hash": f"0xhash{bn}z", "from": "0xother", "to": "0xother2"},
                ]
            return {"result": {"transactions": txs}}
        if method == "eth_getTransactionByHash":
            h = params[0]
            # Provide minimal fields expected by get_transaction
            return {
                "result": {
                    "blockNumber": hex(20),
                    "from": "0xabc",
                    "to": "0xtarget",
                    "value": hex(1000000000000000000),
                    "gasPrice": hex(1000000000),
                    "gas": hex(21000),
                }
            }
        raise AssertionError(f"Unexpected method {method}")

    monkeypatch.setattr(EthereumAdapter, "make_request", fake_make_request, raising=True)

    # Act
    txs = await adapter.get_address_transactions("0xTARGET", limit=3)

    # Assert
    assert len(txs) == 3
    for tx in txs:
        assert tx["chain"] == "ethereum"
        assert tx["chain_type"] == "evm"
        assert isinstance(tx["block_number"], int)
        assert "from_address" in tx and "to_address" in tx


@pytest.mark.asyncio
async def test_btc_get_address_transactions_filters_and_limits(monkeypatch):
    # Arrange
    chain_info = ChainInfo(
        chain_id="bitcoin",
        name="Bitcoin",
        symbol="BTC",
        chain_type=ChainType.UTXO,
        rpc_urls=["http://localhost:8332"],
        native_currency={"name": "Bitcoin", "symbol": "BTC", "decimals": 8},
    )
    adapter = BitcoinAdapter(chain_info)

    monkeypatch.setenv("BTC_SCAN_MAX_BLOCKS", "5")

    latest_height = 100

    async def fake_make_request(self, method, params=None):
        nonlocal latest_height
        if method == "getblockcount":
            return {"result": latest_height}
        if method == "getblockhash":
            height = params[0]
            return {"result": f"hash{height}"}
        if method == "getblock":
            block_hash, verbosity = params
            assert verbosity == 2
            # Synthesize txs: include address only in last 2 blocks
            if block_hash in ("hash100", "hash99"):
                txs = [
                    {
                        "txid": f"tx-{block_hash}-a",
                        "vin": [{}, {}],
                        "vout": [
                            {"scriptPubKey": {"addresses": ["1TARGETADDR"]}},
                            {"scriptPubKey": {"addresses": ["1OTHER"]}},
                        ],
                    },
                    {
                        "txid": f"tx-{block_hash}-b",
                        "vin": [{}],
                        "vout": [
                            {"scriptPubKey": {"addresses": ["1OTHER"]}},
                            {"scriptPubKey": {"addresses": ["1TARGETADDR"]}},
                        ],
                    },
                ]
            else:
                txs = [
                    {"txid": f"tx-{block_hash}-z", "vin": [{}], "vout": [{"scriptPubKey": {"addresses": ["1OTHER"]}}]},
                ]
            return {"result": {"time": 1700000000, "tx": txs}}
        raise AssertionError(f"Unexpected method {method}")

    monkeypatch.setattr(BitcoinAdapter, "make_request", fake_make_request, raising=True)

    # Act
    txs = await adapter.get_address_transactions("1TARGETADDR", limit=3)

    # Assert
    assert len(txs) == 3
    for tx in txs:
        assert tx["chain"] == "bitcoin"
        assert tx["chain_type"] == "utxo"
        assert "block_height" in tx
