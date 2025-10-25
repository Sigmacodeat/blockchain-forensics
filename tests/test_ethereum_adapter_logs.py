import pytest
import asyncio
from datetime import datetime

from app.adapters.ethereum_adapter import EthereumAdapter


@pytest.mark.asyncio
async def test_transform_transaction_includes_compact_logs(monkeypatch):
    adapter = EthereumAdapter(rpc_url="mock://ethereum")

    # Mock get_transaction_receipt to return logs with topics as bytes-like and strings
    async def _mock_get_tx_receipt(tx_hash: str):
        class _Topic:
            def __init__(self, h: str):
                self._h = h
            def hex(self):
                return self._h
        return {
            "status": 1,
            "gasUsed": 21000,
            "logs": [
                {
                    "address": "0xAABBccDdEEFF0011223344556677889900AABBCC",
                    "topics": [
                        _Topic("0xDDf252ad1BE2C89B69C2B068FC378DAA952BA7F163C4A11628F55A4DF523B3EF"),
                        _Topic("0x0000000000000000000000001111111111111111111111111111111111111111"),
                    ],
                },
                {
                    "address": "0x1234567890abcdef1234567890abcdef12345678",
                    "topics": [
                        "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1",
                    ],
                },
            ],
        }

    monkeypatch.setattr(adapter, "get_transaction_receipt", _mock_get_tx_receipt)

    raw_tx = {
        "hash": b"\x12\x34\x56\x78",
        "from": "0x1111111111111111111111111111111111111111",
        "to": "0x2222222222222222222222222222222222222222",
        "gasPrice": 1,
        "value": 0,
        "input": "0x",
        "transactionIndex": 0,
        "chainId": 1,
        "nonce": 42,
    }
    block_data = {
        "number": 12345678,
        "timestamp": int(datetime.utcnow().timestamp()),
        "transactions": [raw_tx],
    }

    event = await adapter.transform_transaction(raw_tx, block_data)

    assert event.metadata is not None
    assert "logs" in event.metadata
    logs = event.metadata["logs"]
    assert isinstance(logs, list) and len(logs) == 2

    # Check address normalization and topics hex lowercased
    l0 = logs[0]
    assert l0["address"] == "0xaabbccddeeff0011223344556677889900aabbcc"
    assert l0["topics"][0] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    assert l0["topics"][1].startswith("0x")

    l1 = logs[1]
    assert l1["address"] == "0x1234567890abcdef1234567890abcdef12345678"
    assert l1["topics"][0] == "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
