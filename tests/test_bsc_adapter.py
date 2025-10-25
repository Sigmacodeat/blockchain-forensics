import pytest

from app.adapters.bsc_adapter import BscAdapter


@pytest.mark.asyncio
async def test_bsc_chain_and_transform_minimal():
    adapter = BscAdapter(rpc_url=None)
    # Force offline path to avoid real RPC during unit test
    adapter.w3 = None  # type: ignore

    raw_tx = {
        "hash": "0xabc123",
        "from": "0x0000000000000000000000000000000000000001",
        "to": "0x0000000000000000000000000000000000000002",
        "value": 1234567890000000000,  # ~1.23456789 BNB (wei-like)
        "gasPrice": 1_000_000_000,     # 1 gwei
        "input": "0x",
        "nonce": 1,
        "chainId": 56,
    }
    block = {
        "number": 123,
        "timestamp": 1_700_000_000,
        "transactions": [],
    }

    ev = await adapter.transform_transaction(raw_tx, block)

    assert ev.chain == "bsc"
    assert ev.block_number == 123
    assert ev.tx_hash.startswith("0x")
    assert ev.event_type in {"transfer", "contract_call", "unknown"}
