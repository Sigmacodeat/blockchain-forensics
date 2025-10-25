import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from app.tracing.tracer import TransactionTracer
from app.tracing.models import TraceRequest, TraceDirection, TaintModel


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_utxo_outgoing_propagation(monkeypatch):
    tracer = TransactionTracer(db_client=DummyDB())

    # Patch same-chain txs to empty, focus on UTXO
    import app.tracing.tracer as tracer_mod
    tracer_mod.TransactionTracer._get_outgoing_transactions = AsyncMock(return_value=[])
    tracer_mod.TransactionTracer._get_incoming_transactions = AsyncMock(return_value=[])

    # Patch UTXO spends from source to next address
    utxo_rows = [
        {
            "from_address": "bc1src",
            "to_address": "bc1dest",
            "value": 0.5,
            "timestamp": "2024-01-01T00:00:00Z",
            "tx_hash": "0xutxotx1",
            "event_type": "utxo_spend",
        },
        {
            "from_address": "bc1src",
            "to_address": "bc1dest2",
            "value": 0.5,
            "timestamp": "2024-01-01T00:00:10Z",
            "tx_hash": "0xutxotx2",
            "event_type": "utxo_spend",
        },
    ]
    tracer_mod.TransactionTracer._get_utxo_outgoing = AsyncMock(return_value=utxo_rows)

    # Labels
    tracer_mod.labels_service = MagicMock()
    tracer_mod.labels_service.get_labels = AsyncMock(return_value=["wallet"]) 

    req = TraceRequest(
        source_address="bc1SRC",
        direction=TraceDirection.FORWARD,
        taint_model=TaintModel.PROPORTIONAL,
        max_depth=1,
        min_taint_threshold=0.0,
        max_nodes=10,
    )

    res = await tracer.trace(req)

    # Two edges for two utxo spends
    utxo_edges = [e for e in res.edges if e.event_type in (None, "utxo_spend")]
    assert len(utxo_edges) >= 2

    # Nodes created and taint propagated (split proportionally)
    n1 = res.nodes.get("bc1dest")
    n2 = res.nodes.get("bc1dest2")
    assert n1 and n2
    # With proportional model and equal values, each receives ~0.5 taint
    assert n1.taint_received >= Decimal("0.4")
    assert n2.taint_received >= Decimal("0.4")
