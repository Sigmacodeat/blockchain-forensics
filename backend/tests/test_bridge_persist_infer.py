import pytest
from types import SimpleNamespace
from decimal import Decimal

from app.api.v1.trace import save_trace_to_graph
from app.tracing.models import TraceResult, TraceNode, TraceEdge, TaintModel, TraceDirection

pytestmark = pytest.mark.asyncio


class DummySession:
    async def run(self, *args, **kwargs):
        class _R:
            async def single(self):
                return None
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration
        return _R()

class DummyCtx:
    async def __aenter__(self):
        return DummySession()
    async def __aexit__(self, exc_type, exc, tb):
        return False


async def test_bridge_persist_with_chain_infer(monkeypatch):
    # Build minimal TraceResult with a bridge edge without chain_from/to
    tr = TraceResult(
        trace_id="t1",
        source_address="0x1111111111111111111111111111111111111111",
        direction=TraceDirection.FORWARD,
        taint_model=TaintModel.PROPORTIONAL,
        max_depth=1,
        min_taint_threshold=0.1,
    )
    tr.nodes[tr.source_address] = TraceNode(address=tr.source_address)
    # Ethereum-like to Solana-like address
    edge = TraceEdge(
        from_address=tr.source_address,
        to_address="So11111111111111111111111111111111111111112",
        tx_hash="0xabc",
        value=Decimal("1"),
        taint_value=Decimal("1"),
        timestamp="2025-10-10T00:00:00Z",
        hop=1,
        event_type="bridge",
        # chain_from/chain_to intentionally None
    )
    tr.edges.append(edge)

    # Monkeypatch neo4j session to no-op
    # Patch instance via dotted-path to avoid attribute resolution on object
    monkeypatch.setattr("app.db.neo4j_client.neo4j_client", SimpleNamespace(get_session=lambda: DummyCtx()), raising=False)

    # Capture persist_bridge_link calls
    calls = {}
    async def fake_persist(from_address, to_address, *, bridge, chain_from, chain_to, tx_hash, timestamp_iso):
        calls["from"] = from_address
        calls["to"] = to_address
        calls["chain_from"] = chain_from
        calls["chain_to"] = chain_to
        calls["tx_hash"] = tx_hash
        calls["timestamp"] = timestamp_iso
        return True

    from app.bridge import hooks as bridge_hooks
    monkeypatch.setattr(bridge_hooks, "persist_bridge_link", fake_persist)

    await save_trace_to_graph(tr)

    # Assert chains inferred correctly
    assert calls.get("chain_from") == "ethereum"
    assert calls.get("chain_to") == "solana"
    assert calls.get("from").startswith("0x")
