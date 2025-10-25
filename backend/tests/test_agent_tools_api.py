import os
import pytest
from httpx import AsyncClient

# Ensure required settings
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ENABLE_AI_AGENTS", "true")
os.environ.setdefault("TEST_MODE", "1")  # skip external DB connects
os.environ.setdefault("API_KEYS", "test-key")
os.environ.setdefault("CORS_ORIGINS", "[\"http://test\"]")
# Configure Kilo/Grok credentials for client init
os.environ.setdefault("KILO_BASE_URL", "https://api.mock.local")
os.environ.setdefault("KILO_API_KEY", "mock-key")

from app.main import app  # noqa: E402
from app.integrations.kilo_client import KiloClient  # noqa: E402

pytestmark = pytest.mark.anyio("asyncio")


@pytest.fixture(autouse=True)
def _patch_kilo_client(monkeypatch):
    def _extract_from_code(self, code: str, *, language=None, task=None):
        return {
            "ok": True,
            "mode": "code",
            "language": language,
            "task": task,
        }

    def _extract_from_text(self, text: str, *, schema=None, task=None):
        return {
            "ok": True,
            "mode": "text",
            "task": task,
            "schema": bool(schema),
        }

    monkeypatch.setattr(KiloClient, "extract_from_code", _extract_from_code)
    monkeypatch.setattr(KiloClient, "extract_from_text", _extract_from_text)


async def test_tool_risk_score_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/api/v1/agent/tools/risk-score", json={
            "address": "0x0000000000000000000000000000000000000000"
        })
        assert res.status_code == 200
        body = res.json()
        assert "risk_score" in body
        assert body.get("address") == "0x0000000000000000000000000000000000000000"


async def test_tool_bridge_lookup_endpoint_lists_by_chain():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/api/v1/agent/tools/bridge-lookup", json={
            "chain": "polygon"
        })
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, dict)


async def test_tool_code_extract_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/api/v1/agent/tools/code-extract", json={
            "code": "function add(a,b){return a+b}",
            "language": "javascript",
            "task": "find_functions"
        })
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, dict)


async def test_tool_trigger_alert_endpoint_creates_alert():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/api/v1/agent/tools/trigger-alert", json={
            "alert_type": "high_risk",
            "severity": "high",
            "title": "High Risk Test",
            "description": "Automated test alert",
            "address": "0x0000000000000000000000000000000000000000",
            "metadata": {"risk_score": 0.95}
        })
        assert res.status_code == 200
        body = res.json()
        assert body.get("success") is True
        assert "alert" in body
        assert body["alert"].get("title") == "High Risk Test"
        assert body["alert"].get("address") == "0x0000000000000000000000000000000000000000"


async def test_tool_list_alert_rules_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/v1/agent/tools/alert-rules")
        assert res.status_code == 200
        body = res.json()
        assert "rules" in body
        assert isinstance(body["rules"], list)


async def test_tool_simulate_alerts_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/api/v1/agent/tools/simulate-alerts", json={
            "address": "0x0000000000000000000000000000000000000000",
            "labels": ["mixer"],
            "risk_score": 0.8,
            "value_usd": 100000
        })
        assert res.status_code == 200
        body = res.json()
        assert "triggered_count" in body or "error" in body or "message" in body
        if "alerts" in body:
            assert isinstance(body.get("alerts", []), list)


async def test_tool_text_extract_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/api/v1/agent/tools/text-extract", json={
            "text": "Transfer 12.5 ETH from 0xabc to 0xdef",
            "task": "ner",
            "schema": {"type": "object", "properties": {"amount": {"type": "number"}}}
        })
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, dict)
