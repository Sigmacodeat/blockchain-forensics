import os
import pytest

from app.api.v1.trace import save_trace_to_graph
from app.tracing.models import TraceResult, TraceNode, TraceEdge, TaintModel, TraceDirection
from decimal import Decimal

pytestmark = pytest.mark.asyncio


async def test_save_trace_persists_bridge_link(monkeypatch):
    os.environ["TEST_MODE"] = "1"

    called = {"count": 0, "args": None}

    async def mock_persist_bridge_link(*args, **kwargs):
        called["count"] += 1
        called["args"] = (args, kwargs)
        return True

    # monkeypatch in hooks module (trace imports it at call time)
    import app.bridge.hooks as hooks_mod
    monkeypatch.setattr(hooks_mod, "persist_bridge_link", mock_persist_bridge_link)

    # Build a minimal TraceResult with one bridge edge
    result = TraceResult(
        trace_id="t1",
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

    assert called["count"] == 1
