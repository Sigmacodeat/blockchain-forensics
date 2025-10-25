import pytest

from app.adapters.zksync_adapter import ZkSyncAdapter


@pytest.mark.asyncio
async def test_zksync_chain_and_transform_minimal():
    adapter = ZkSyncAdapter(rpc_url=None)
    # Force offline path to avoid real RPC during unit test
    adapter.w3 = None  # type: ignore

    raw_tx = {
        "hash": "0xzk01",
        "from": "0x0000000000000000000000000000000000000001",
        "to": "0x0000000000000000000000000000000000000002",
        "value": 10**18,  # 1 ETH equivalent
        "gasPrice": 1_000_000_000,
        "input": "0x",
        "nonce": 1,
        "chainId": 324,
    }
    block = {
        "number": 1010,
        "timestamp": 1_700_000_300,
        "transactions": [],
    }

    ev = await adapter.transform_transaction(raw_tx, block)

    assert ev.chain == "zksync"
    assert ev.block_number == 1010
    assert ev.tx_hash.startswith("0x")
    assert ev.event_type in {"transfer", "contract_call", "unknown"}
