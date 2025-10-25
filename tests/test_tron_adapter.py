import pytest

from app.adapters.tron_adapter import TronAdapter


@pytest.mark.asyncio
async def test_tron_transform_minimal_offline():
    adapter = TronAdapter(api_url=None)

    raw_tx = {
        "txID": "abcd1234",
        "from": "TA1b2c3d4e5f6g7h8i9j0k",
        "to": "TB1b2c3d4e5f6g7h8i9j0k",
        "amount": 2_500_000,  # 2.5 TRX in Sun
        "transactionIndex": 0,
    }
    block = {
        "number": 12345,
        "timestamp": 1_700_000_600,
    }

    ev = await adapter.transform_transaction(raw_tx, block)

    assert ev.chain == "tron"
    assert ev.block_number == 12345
    assert str(ev.value) == "2.5"
    assert ev.event_type in {"transfer", "contract_call"}
