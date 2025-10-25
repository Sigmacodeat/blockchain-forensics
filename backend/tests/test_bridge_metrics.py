import os
import pytest
from app.api.v1.trace import save_trace_to_graph
from app.tracing.models import TraceResult, TraceNode, TraceEdge, TaintModel, TraceDirection
from app.observability.metrics import BRIDGE_EVENTS
from decimal import Decimal

pytestmark = pytest.mark.asyncio


async def test_bridge_persist_increments_metric(monkeypatch):
    os.environ["TEST_MODE"] = "1"

    # Monkeypatch persist to succeed
    async def ok_persist(*args, **kwargs):
        return True

    import app.bridge.hooks as hooks_mod
    monkeypatch.setattr(hooks_mod, "persist_bridge_link", ok_persist)

    # Capture current value
    persisted_before = BRIDGE_EVENTS.labels(stage="persisted")._value.get()

    # Build minimal trace with one bridge edge (has chain_from/to to pass guard)
    result = TraceResult(
        trace_id="t2",
        source_address="0xsource",
        direction=TraceDirection.FORWARD,
        taint_model=TaintModel.PROPORTIONAL,
        max_depth=1,
        min_taint_threshold=0.0,
        nodes={
            "0xsource": TraceNode(address="0xsource", taint_received=Decimal(1)),
            "0xdst": TraceNode(address="0xdst", taint_received=Decimal(0)),
        },
        edges=[
            TraceEdge(
                from_address="0xsource",
                to_address="0xdst",
                tx_hash="0xtx",
                value=Decimal(1),
                taint_value=Decimal(1),
                timestamp="2024-01-01T00:00:00Z",
                hop=1,
                event_type="bridge",
                bridge="wormhole",
                chain_from="ethereum",
                chain_to="solana",
            )
        ],
        total_nodes=2,
        total_edges=1,
        max_hop_reached=1,
        total_taint_traced=Decimal(1),
        high_risk_addresses=[],
        sanctioned_addresses=[],
        execution_time_seconds=0.0,
        completed=True,
    )

    await save_trace_to_graph(result)

    persisted_after = BRIDGE_EVENTS.labels(stage="persisted")._value.get()
    assert persisted_after == persisted_before + 1
