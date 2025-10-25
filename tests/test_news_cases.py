import os
import json
import asyncio
import time
import uuid
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_news_case_crud_and_snapshot(client: TestClient):
    # Create
    slug = f"case-demo-{uuid.uuid4().hex[:8]}"
    # cleanup leftover if any
    client.delete(f"/api/v1/news-cases/{slug}")

    payload = {
        "slug": slug,
        "name": "Demo Case",
        "description": "Öffentlicher Test-Case",
        "addresses": [
            {"chain": "ethereum", "address": "0x0000000000000000000000000000000000000001"}
        ],
    }
    resp = client.post("/api/v1/news-cases", json=payload)
    assert resp.status_code in (200, 201)

    # Patch adapter to avoid real RPC in snapshot
    mock_adapter = AsyncMock()
    mock_adapter.get_address_balance.return_value = 1.234
    mock_adapter.get_address_transactions.return_value = [
        {
            "tx_hash": "0xabc",
            "from_address": "0x000...1",
            "to_address": "0x000...2",
            "value": 0.01,
            "block_number": 1,
        }
    ]
    with patch("app.services.news_case_service.NewsCaseService._ensure_adapter", return_value=mock_adapter):
        snap = client.get(f"/api/v1/news-cases/{slug}/snapshot")
        assert snap.status_code == 200
        data = snap.json()
        assert data["slug"] == slug
        assert isinstance(data.get("addresses"), list)
        assert len(data["addresses"]) == 1
        addr = data["addresses"][0]
        assert addr["chain"] == "ethereum"
        assert addr.get("balance") is not None

    # Delete
    resp = client.delete(f"/api/v1/news-cases/{slug}")
    assert resp.status_code in (200, 204)


@pytest.mark.asyncio
async def test_news_case_ws_stream_basic(client: TestClient, monkeypatch):
    # Speed up watcher loop
    monkeypatch.setenv("NEWSCASE_WATCH_INTERVAL", "0.05")

    # Create case
    slug = f"case-ws-{uuid.uuid4().hex[:8]}"
    client.delete(f"/api/v1/news-cases/{slug}")

    payload = {
        "slug": slug,
        "name": "WS Case",
        "addresses": [
            {"chain": "ethereum", "address": "0x0000000000000000000000000000000000000002"}
        ],
    }
    resp = client.post("/api/v1/news-cases", json=payload)
    assert resp.status_code in (200, 201)

    # Mock adapter to produce a new tx once
    produced = {"done": False}

    async def _get_txs(_addr: str, limit: int = 5):
        # Snapshot ruft mit limit=1 (nur Anzeige) auf -> keine Events erzeugen
        if limit and limit <= 1:
            return []
        # Watcher ruft mit limit=5 auf -> genau einmal eine TX liefern
        if not produced["done"]:
            produced["done"] = True
            return [
                {
                    "tx_hash": "0xbeef",
                    "from_address": "0xfeed",
                    "to_address": "0xcafe",
                    "value": 0.02,
                    "block_number": 123,
                }
            ]
        return []

    mock_adapter = AsyncMock()
    mock_adapter.get_address_balance.return_value = 0.0
    mock_adapter.get_address_transactions.side_effect = _get_txs

    with patch("app.services.news_case_service.NewsCaseService._ensure_adapter", return_value=mock_adapter):
        # Connect WS
        with client.websocket_connect(f"/api/v1/ws/news-cases/{slug}") as ws:
            # subscribed + initial snapshot
            first = ws.receive_json()
            assert first["type"] in ("news_case.subscribed", "news_case.snapshot")

            # Wait for a tx event (allow some time for watcher to tick)
            got_tx = False
            for _ in range(40):  # up to ~2s
                msg = ws.receive_json()
                if msg.get("type") == "news_case.tx":
                    got_tx = True
                    assert msg["slug"] == slug
                    assert msg["tx"]["tx_hash"] == "0xbeef"
                    break
            assert got_tx, "did not receive news_case.tx in time"

    # Cleanup
    client.delete("/api/v1/news-cases/case-ws-1")


@pytest.mark.asyncio
async def test_news_case_ws_stream_auto_trace(client: TestClient, monkeypatch):
    if not os.environ.get("AUTO_TRACE_ENABLED"):
        pytest.skip("AUTO_TRACE_ENABLED is not set")

    # Speed up watcher loop
    monkeypatch.setenv("NEWSCASE_WATCH_INTERVAL", "0.05")

    # Create case
    slug = f"case-ws-{uuid.uuid4().hex[:8]}"
    client.delete(f"/api/v1/news-cases/{slug}")

    payload = {
        "slug": slug,
        "name": "WS Case",
        "addresses": [
            {"chain": "ethereum", "address": "0x0000000000000000000000000000000000000002"}
        ],
    }
    resp = client.post("/api/v1/news-cases", json=payload)
    assert resp.status_code in (200, 201)

    # Mock adapter to produce a new tx once
    produced = {"done": False}

    async def _get_txs(_addr: str, limit: int = 5):
        # Snapshot ruft mit limit=1 (nur Anzeige) auf -> keine Events erzeugen
        if limit and limit <= 1:
            return []
        # Watcher ruft mit limit=5 auf -> genau einmal eine TX liefern
        if not produced["done"]:
            produced["done"] = True
            return [
                {
                    "tx_hash": "0xbeef",
                    "from_address": "0xfeed",
                    "to_address": "0xcafe",
                    "value": 0.02,
                    "block_number": 123,
                }
            ]
        return []

    mock_adapter = AsyncMock()
    mock_adapter.get_address_balance.return_value = 0.0
    mock_adapter.get_address_transactions.side_effect = _get_txs

    with patch("app.services.news_case_service.NewsCaseService._ensure_adapter", return_value=mock_adapter):
        # Connect WS
        with client.websocket_connect(f"/api/v1/ws/news-cases/{slug}?auto_trace=true") as ws:
            # subscribed + initial snapshot
            first = ws.receive_json()
            assert first["type"] in ("news_case.subscribed", "news_case.snapshot")

            # Wait for a tx event (allow some time for watcher to tick)
            got_tx = False
            for _ in range(40):  # up to ~2s
                msg = ws.receive_json()
                if msg.get("type") == "news_case.tx":
                    got_tx = True
                    assert msg["slug"] == slug
                    assert msg["tx"]["tx_hash"] == "0xbeef"
                    break
            assert got_tx, "did not receive news_case.tx in time"

    # Cleanup
    client.delete("/api/v1/news-cases/case-ws-1")
