import pytest

from app.adapters.gnosis_adapter import GnosisAdapter


@pytest.mark.asyncio
async def test_gnosis_chain_and_transform_minimal():
    adapter = GnosisAdapter(rpc_url=None)
    # Force offline path to avoid real RPC during unit test
    adapter.w3 = None  # type: ignore

    raw_tx = {
        "hash": "0xdef456",
        "from": "0x0000000000000000000000000000000000000001",
        "to": "0x0000000000000000000000000000000000000002",
        "value": 10**18,  # 1 xDAI (wei-like)
        "gasPrice": 1_000_000_000,     # 1 gwei
        "input": "0x",
        "nonce": 1,
        "chainId": 100,
    }
    block = {
        "number": 456,
        "timestamp": 1_700_000_100,
        "transactions": [],
    }

    ev = await adapter.transform_transaction(raw_tx, block)

    assert ev.chain == "gnosis"
    assert ev.block_number == 456
    assert ev.tx_hash.startswith("0x")
    assert ev.event_type in {"transfer", "contract_call", "unknown"}
