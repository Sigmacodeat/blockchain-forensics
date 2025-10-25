import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.tracing.tracer import TransactionTracer
from app.tracing.models import TraceRequest, TraceDirection, TaintModel


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_erc721_token_flow_even_split(monkeypatch):
    tracer = TransactionTracer(db_client=DummyDB())

    import app.tracing.tracer as tracer_mod

    # Outgoing tx with two ERC721 transfers
    tx = {
        "from_address": "0xsender",
        "to_address": "0xcontract",
        "value": 0,
        "timestamp": "2024-01-01T00:00:00Z",
        "tx_hash": "0xnft721_tx",
        "metadata": {
            "erc721_transfers": [
                {"token": "0xnft", "from": "0xsender", "to": "0xrcp1", "tokenId": "1"},
                {"token": "0xnft", "from": "0xsender", "to": "0xrcp2", "tokenId": "2"},
            ]
        },
    }

    tracer_mod.TransactionTracer._get_outgoing_transactions = AsyncMock(return_value=[tx])
    tracer_mod.TransactionTracer._get_incoming_transactions = AsyncMock(return_value=[])
    tracer_mod.TransactionTracer._get_utxo_outgoing = AsyncMock(return_value=[])
    tracer_mod.TransactionTracer._get_utxo_incoming = AsyncMock(return_value=[])

    tracer_mod.labels_service = MagicMock()
    tracer_mod.labels_service.get_labels = AsyncMock(return_value=["wallet"]) 

    req = TraceRequest(
        source_address="0xSENDER",
        direction=TraceDirection.FORWARD,
        taint_model=TaintModel.PROPORTIONAL,
        max_depth=2,
        min_taint_threshold=0.0,
        max_nodes=20,
        token_decay=1.0,
    )

    res = await tracer.trace(req)

    edges = [e for e in res.edges if e.event_type == "nft_transfer"]
    assert len(edges) == 2

    n1 = res.nodes.get("0xrcp1")
    n2 = res.nodes.get("0xrcp2")
    assert n1 and n2
    # Even split ~0.5 each
    assert n1.taint_received >= Decimal("0.49")
    assert n2.taint_received >= Decimal("0.49")


@pytest.mark.asyncio
async def test_erc1155_token_flow_weighted(monkeypatch):
    tracer = TransactionTracer(db_client=DummyDB())

    import app.tracing.tracer as tracer_mod

    tx = {
        "from_address": "0xsender",
        "to_address": "0xcontract",
        "value": 0,
        "timestamp": "2024-01-01T00:00:10Z",
        "tx_hash": "0xnft1155_tx",
        "metadata": {
            "erc1155_transfers": [
                {"token": "0xnft1155", "from": "0xsender", "to": "0xrcpA", "id": "10", "amount": 2},
                {"token": "0xnft1155", "from": "0xsender", "to": "0xrcpB", "id": "11", "amount": 3},
            ]
        },
    }

    tracer_mod.TransactionTracer._get_outgoing_transactions = AsyncMock(return_value=[tx])
    tracer_mod.TransactionTracer._get_incoming_transactions = AsyncMock(return_value=[])
    tracer_mod.TransactionTracer._get_utxo_outgoing = AsyncMock(return_value=[])
    tracer_mod.TransactionTracer._get_utxo_incoming = AsyncMock(return_value=[])

    tracer_mod.labels_service = MagicMock()
    tracer_mod.labels_service.get_labels = AsyncMock(return_value=["wallet"]) 

    req = TraceRequest(
        source_address="0xSENDER",
        direction=TraceDirection.FORWARD,
        taint_model=TaintModel.PROPORTIONAL,
        max_depth=2,
        min_taint_threshold=0.0,
        max_nodes=20,
        token_decay=1.0,
    )

    res = await tracer.trace(req)

    edges = [e for e in res.edges if e.event_type == "nft1155_transfer"]
    assert len(edges) == 2

    nA = res.nodes.get("0xrcpa")
    nB = res.nodes.get("0xrcpb")
    assert nA and nB
    # Weighted 2/5 and 3/5 of taint ~0.4 and ~0.6
    assert nA.taint_received >= Decimal("0.39")
    assert nB.taint_received >= Decimal("0.59")
