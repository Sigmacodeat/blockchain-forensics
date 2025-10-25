import pytest

from app.adapters.celo_adapter import CeloAdapter


@pytest.mark.asyncio
async def test_celo_chain_and_transform_minimal():
    adapter = CeloAdapter()
    # Force offline path to avoid real RPC during unit test
    adapter.w3 = None  # type: ignore

    raw_tx = {
        "hash": "0xfeed01",
        "from": "0x0000000000000000000000000000000000000001",
        "to": "0x0000000000000000000000000000000000000002",
        "value": 10**18,  # 1 CELO
        "gasPrice": 1_000_000_000,
        "input": "0x",
        "nonce": 1,
        "chainId": 42220,
    }
    block = {
        "number": 789,
        "timestamp": 1_700_000_200,
        "transactions": [],
    }

    ev = await adapter.transform_transaction(raw_tx, block)

    assert ev.chain == "celo"
    assert ev.block_number == 789
    assert ev.tx_hash.startswith("0x")
    assert ev.event_type in {"transfer", "contract_call", "unknown"}
