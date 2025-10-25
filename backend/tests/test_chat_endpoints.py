import os
import json
import pytest
from fastapi.testclient import TestClient

os.environ["TEST_MODE"] = "1"

from app.main import app
from types import SimpleNamespace

client = TestClient(app)

class FakeAgent:
    async def health(self):
        return {"enabled": True, "tools_available": 3, "model": "Cascade", "llm_ready": True}
    async def investigate(self, text: str, chat_history=None):
        # simple echo response to trigger delta streaming
        return {"success": True, "response": f"ECHO: {text}", "tool_calls": []}

@pytest.fixture
def patch_agent(monkeypatch):
    # Patch get_agent inside chat module to return our FakeAgent
    from app.api.v1 import chat as chat_mod
    monkeypatch.setattr(chat_mod, "get_agent", lambda: FakeAgent())
    yield


def test_chat_post_rate_limit_retry_after(monkeypatch):
    # Ensure a session key to keep same client bucket
    headers = {"Content-Type": "application/json", "x-session-id": "test-sess"}
    payload = {"message": "hello"}
    # Force strict rate limit via settings
    from app.api.v1 import chat as chat_mod
    # Replace settings with a minimal namespace exposing only the needed field
    monkeypatch.setattr(chat_mod, "settings", SimpleNamespace(CHAT_RATE_LIMIT_PER_MIN=1), raising=False)
    # Clear rate limit bucket for deterministic behavior
    chat_mod._RATE_LIMIT_BUCKET.clear()
    # First request should pass under limit 1
    r1 = client.post("/api/v1/chat", data=json.dumps(payload), headers=headers)
    assert r1.status_code == 200, r1.text
    # Second immediate request should be rate-limited
    r2 = client.post("/api/v1/chat", data=json.dumps(payload), headers=headers)
    assert r2.status_code == 429
    assert r2.headers.get("Retry-After") is not None


def test_chat_stream_rate_limit(monkeypatch):
    headers = {"x-session-id": "stream-sess"}
    from app.api.v1 import chat as chat_mod
    chat_mod._RATE_LIMIT_BUCKET.clear()
    monkeypatch.setattr(chat_mod, "settings", SimpleNamespace(CHAT_RATE_LIMIT_PER_MIN=1), raising=False)
    # First stream request ok
    with client.stream("GET", "/api/v1/chat/stream", params={"q": "test"}, headers=headers) as r1:
        assert r1.status_code == 200
    # Second call should 429
    r2 = client.get("/api/v1/chat/stream", params={"q": "test"}, headers=headers)
    assert r2.status_code == 429
    assert r2.headers.get("Retry-After") is not None


def test_chat_ws_delta_stream(patch_agent, monkeypatch):
    # With fake agent, we should receive typing, deltas and final answer
    from app.api.v1 import chat as chat_mod
    # Ensure rate limit is not interfering
    chat_mod._RATE_LIMIT_BUCKET.clear()
    monkeypatch.setattr(chat_mod, "settings", SimpleNamespace(CHAT_RATE_LIMIT_PER_MIN=1000, CHAT_WS_CHUNK_SIZE=16), raising=False)
    with client.websocket_connect("/api/v1/ws/chat") as ws:
        # initial ready event
        ready = json.loads(ws.receive_text())
        assert (ready.get("type") == "ready") or (ready.get("ok") in (True, False))
        # send a message
        ws.send_text("Hallo Welt")
        # expect typing
        evt1 = json.loads(ws.receive_text())
        assert evt1.get("type") in ("chat.typing", "answer", "chat.delta")
        # receive a few messages until final answer
        got_answer = False
        # Cap reads to avoid infinite loop
        for _ in range(20):
            evt = json.loads(ws.receive_text())
            if evt.get("type") == "answer":
                got_answer = True
                assert evt.get("reply", "").startswith("ECHO:")
                break
            elif evt.get("type") == "chat.delta":
                # delta chunk should be non-empty
                assert isinstance(evt.get("delta"), str)
        assert got_answer
