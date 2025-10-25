import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.tracing.tracer import TransactionTracer
from app.tracing.models import TraceRequest, TraceDirection, TaintModel


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_cross_chain_expansion_via_bridge_links(monkeypatch):
    tracer = TransactionTracer(db_client=DummyDB())

    # Patch Postgres transactions to empty to focus on bridge expansion
    import app.tracing.tracer as tracer_mod
    async def empty_out(*args, **kwargs):
        return []
    tracer_mod.TransactionTracer._get_outgoing_transactions = AsyncMock(return_value=[])
    tracer_mod.TransactionTracer._get_incoming_transactions = AsyncMock(return_value=[])

    # Patch labels_service
    tracer_mod.labels_service = MagicMock()
    tracer_mod.labels_service.get_labels = AsyncMock(return_value=["bridge"])

    # Patch Neo4j bridge links
    bridge_rows = [{
        "counterparty": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        "chain_from": "ethereum",
        "chain_to": "polygon",
        "bridge": "Polygon PoS Bridge",
        "tx_hash": "0xbridgehash",
        "timestamp": "2024-01-01T00:00:00Z",
    }]
    tracer_mod.neo4j_client = MagicMock()
    tracer_mod.neo4j_client.run_query = AsyncMock(return_value=bridge_rows)

    req = TraceRequest(
        source_address="0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        direction=TraceDirection.FORWARD,
        taint_model=TaintModel.PROPORTIONAL,
        max_depth=2,
        min_taint_threshold=0.0,
        max_nodes=10,
    )

    res = await tracer.trace(req)

    # Should have one bridge edge
    bridge_edges = [e for e in res.edges if e.event_type == "bridge"]
    assert len(bridge_edges) >= 1
    assert bridge_edges[0].chain_from == "ethereum"
    assert bridge_edges[0].chain_to == "polygon"

    # Target node should have taint_received ~ 0.9 * 1.0
    node = res.nodes.get("0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    assert node is not None
    assert node.taint_received >= Decimal("0.9")
