import pytest

from app.adapters.linea_adapter import LineaAdapter


@pytest.mark.asyncio
async def test_linea_chain_and_transform_minimal():
    adapter = LineaAdapter(rpc_url=None)
    # Force offline path to avoid real RPC during unit test
    adapter.w3 = None  # type: ignore

    raw_tx = {
        "hash": "0xlin01",
        "from": "0x0000000000000000000000000000000000000001",
        "to": "0x0000000000000000000000000000000000000002",
        "value": 10**18,
        "gasPrice": 1_000_000_000,
        "input": "0x",
        "nonce": 1,
        "chainId": 59144,
    }
    block = {
        "number": 3030,
        "timestamp": 1_700_000_500,
        "transactions": [],
    }

    ev = await adapter.transform_transaction(raw_tx, block)

    assert ev.chain == "linea"
    assert ev.block_number == 3030
    assert ev.tx_hash.startswith("0x")
    assert ev.event_type in {"transfer", "contract_call", "unknown"}
