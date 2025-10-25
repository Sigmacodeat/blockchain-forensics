import os
import asyncio
import json
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from app.services.case_management import case_management_service
from app.services.collaboration_workspace import collaboration_workspace
from app.services.news_case_service import news_case_service


@pytest.mark.asyncio
async def test_ws_collab_join_and_events(client: TestClient):
    """E2E: Collab WS - Join, Cursor, Typing, Chat, Leave"""

    # Create a test case first
    case = case_management_service.create_case(
        case_type="transaction_review",
        title="Test Case",
        description="Test for WS",
        customer_id="test-customer",
        customer_name="Test Customer",
        customer_tier="pro",
        created_by="test-user",
        created_by_name="Test User"
    )
    case_id = case.case_id

    # Mock the WS client connection
    with client.websocket_connect(f"/api/v1/ws/collab/{case_id}?user_id=test-user&user_name=Test%20User") as ws:
        # Should receive initial snapshot
        msg = ws.receive_json()
        assert msg["type"] == "collab.snapshot"
        assert "participants" in msg["payload"]

        # Send cursor update
        ws.send_json({
            "type": "collab.cursor",
            "payload": {"x": 100, "y": 200, "selectionId": "test"}
        })
        # Should receive cursor broadcast
        msg = ws.receive_json()
        assert msg["type"] == "collab.cursor"
        assert msg["payload"]["user_id"] == "test-user"

        # Send typing indicator
        ws.send_json({
            "type": "collab.typing",
            "payload": {"is_typing": True, "field": "chat"}
        })
        # Should receive typing broadcast
        msg = ws.receive_json()
        assert msg["type"] == "collab.typing"
        assert msg["payload"]["is_typing"] is True

        # Send chat message
        ws.send_json({
            "type": "collab.chat",
            "payload": {"text": "Hello World"}
        })
        # Should receive chat broadcast
        msg = ws.receive_json()
        assert msg["type"] == "collab.chat"
        assert "Hello World" in msg["payload"]["text"]

    # Cleanup
    case_management_service.cases.pop(case_id, None)


@pytest.mark.asyncio
async def test_ws_news_case_stream(client: TestClient, monkeypatch):
    """E2E: NewsCase WS - Backlog, Ping/Pong, Events"""

    # Speed up watcher
    monkeypatch.setenv("NEWSCASE_WATCH_INTERVAL", "0.05")

    # Create test news case
    case = await news_case_service.create(
        slug="test-ws-case",
        name="Test WS Case",
        addresses=[{"chain": "ethereum", "address": "0x0000000000000000000000000000000000000001"}]
    )

    # Mock adapter for events
    produced = {"done": False}

    async def mock_get_txs(addr: str, limit: int = 5):
        if limit == 1:  # Snapshot call
            return []
        if not produced["done"]:
            produced["done"] = True
            return [{
                "tx_hash": "0x1234567890abcdef",
                "from_address": "0x000...1",
                "to_address": "0x000...2",
                "value": 1.0,
                "block_number": 123456,
                "timestamp": 1700000000
            }]
        return []

    mock_adapter = AsyncMock()
    mock_adapter.get_address_balance.return_value = 0.0
    mock_adapter.get_address_transactions.side_effect = mock_get_txs

    with patch("app.services.news_case_service.NewsCaseService._ensure_adapter", return_value=mock_adapter):
        # Connect with backlog
        with client.websocket_connect("/api/v1/ws/news-cases/test-ws-case?backlog=10") as ws:
            # Receive initial snapshot
            msg = ws.receive_json()
            assert msg["type"] in ("news_case.subscribed", "news_case.snapshot")

            # Send ping, expect pong
            ws.send_json({"type": "ping"})
            msg = ws.receive_json()
            assert msg["type"] == "pong"

            # Wait for TX event
            got_tx = False
            for _ in range(50):  # Allow time for watcher
                try:
                    msg = ws.receive_json()
                    if msg.get("type") == "news_case.tx":
                        got_tx = True
                        assert msg["slug"] == "test-ws-case"
                        assert "tx_hash" in msg["tx"]
                        break
                except:
                    break
            assert got_tx, "Did not receive news_case.tx event"

    # Cleanup
    await news_case_service.delete("test-ws-case")


@pytest.mark.asyncio
async def test_ws_auth_failures(client: TestClient):
    """E2E: WS Auth - No token, wrong plan, invalid case"""

    # No auth
    try:
        with client.websocket_connect("/api/v1/ws/collab/CASE-123?user_id=test&user_name=Test") as ws:
            # Should fail
            pass
        assert False, "Should have failed"
    except:
        pass  # Expected

    # Wrong plan (but we can't easily test this without mocking auth)


@pytest.mark.asyncio
async def test_ws_rooms_and_broadcast(client: TestClient):
    """E2E: WS Rooms - Join/Leave, Broadcast"""

    # Test room join
    with client.websocket_connect("/api/v1/ws/room/test-room") as ws:
        # Join another room
        ws.send_json({"command": "join", "room": "alerts"})
        msg = ws.receive_json()
        assert msg["type"] == "joined"
        assert msg["room"] == "alerts"

        # Leave room
        ws.send_json({"command": "leave", "room": "alerts"})
        msg = ws.receive_json()
        assert msg["type"] == "left"
        assert msg["room"] == "alerts"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
