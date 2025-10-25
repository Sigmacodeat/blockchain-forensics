import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.tracing.tracer import TransactionTracer
from app.tracing.models import TraceRequest, TraceDirection, TaintModel


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_erc20_token_flow_tainting(monkeypatch):
    tracer = TransactionTracer(db_client=DummyDB())

    import app.tracing.tracer as tracer_mod

    # Construct a single tx with ERC20 transfers metadata
    tx = {
        "from_address": "0xsender",
        "to_address": "0xcontract",  # contract call triggers token transfers
        "value": 0,  # native value irrelevant here
        "timestamp": "2024-01-01T00:00:00Z",
        "tx_hash": "0xtoken_tx",
        "metadata": {
            "erc20_transfers": [
                {"token": "0xtoken", "from": "0xsender", "to": "0xrcp1", "amount": 60},
                {"token": "0xtoken", "from": "0xsender", "to": "0xrcp2", "amount": 40},
            ]
        },
    }

    # Only return this tx as outgoing
    tracer_mod.TransactionTracer._get_outgoing_transactions = AsyncMock(return_value=[tx])
    tracer_mod.TransactionTracer._get_incoming_transactions = AsyncMock(return_value=[])
    tracer_mod.TransactionTracer._get_utxo_outgoing = AsyncMock(return_value=[])
    tracer_mod.TransactionTracer._get_utxo_incoming = AsyncMock(return_value=[])

    # Labels mock
    tracer_mod.labels_service = MagicMock()
    tracer_mod.labels_service.get_labels = AsyncMock(side_effect=lambda addr: ["defi"] if addr == "0xcontract" else ["wallet"]) 

    req = TraceRequest(
        source_address="0xSENDER",
        direction=TraceDirection.FORWARD,
        taint_model=TaintModel.PROPORTIONAL,
        max_depth=2,
        min_taint_threshold=0.0,
        max_nodes=20,
    )

    res = await tracer.trace(req)

    # Expect token_transfer edges splitting taint by 60/40
    edges = [e for e in res.edges if e.event_type == "token_transfer"]
    assert len(edges) == 2

    n1 = res.nodes.get("0xrcp1")
    n2 = res.nodes.get("0xrcp2")
    assert n1 and n2

    # Proportional split: rcp1 ~ 0.6, rcp2 ~ 0.4 (allow some tolerance)
    assert n1.taint_received >= Decimal("0.6") - Decimal("0.01")
    assert n2.taint_received >= Decimal("0.4") - Decimal("0.01")
