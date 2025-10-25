import os
import json
import pytest
from fastapi.testclient import TestClient

# Ensure test-friendly environment before importing app
os.environ.setdefault("DISABLE_LIFESPAN", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")
os.environ.setdefault("TEST_MODE", "1")

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


def test_chat_post_message(client: TestClient):
    r = client.post("/api/v1/chat", json={"message": "Bewerte das Risiko von 0xabc"})
    assert r.status_code == 200
    body = r.json()
    assert "reply" in body
    # tool_calls optional
    assert "tool_calls" in body


def test_chat_post_messages_history(client: TestClient):
    payload = {
        "messages": [
            {"role": "system", "content": "Du bist Forensiker."},
            {"role": "user", "content": "Finde Bridge-Links für 0xabc"},
        ]
    }
    r = client.post("/api/v1/chat", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("reply"), str)


def test_chat_ws_basic(client: TestClient):
    with client.websocket_connect("/api/v1/ws/chat") as ws:
        # initial ready message
        first = json.loads(ws.receive_text())
        assert first.get("type") == "ready"
        ws.send_text("Trace 0xabc depth=2")
        msg = json.loads(ws.receive_text())
        # either answer or error depending on agent init
        assert msg.get("type") in ("answer", "error")


def test_chat_sse_stream_headers_and_ready(client: TestClient):
    # SSE streaming endpoint should return event-stream and include a ready event
    with client.stream("GET", "/api/v1/chat/stream", params={"q": "Risk 0xabc"}) as resp:
        assert resp.status_code == 200
        ctype = resp.headers.get("content-type", "")
        assert "text/event-stream" in ctype
        # Read a few bytes and ensure 'event: chat.ready' appears
        chunks = []
        for i, chunk in enumerate(resp.iter_bytes()):  # type: ignore[attr-defined]
            chunks.append(chunk)
            if i > 10:
                break
        blob = b"".join(chunks).decode(errors="ignore")
        assert "event: chat.ready" in blob
