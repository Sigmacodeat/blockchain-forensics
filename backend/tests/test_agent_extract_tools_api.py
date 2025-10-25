import os
import pytest
from httpx import AsyncClient

# Ensure minimal required env
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


async def test_agent_tool_code_extract_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/agent/tools/code-extract",
            headers={"x-api-key": "test-key"},
            json={
                "code": "pragma solidity ^0.8.0; contract X { function foo() public {} }",
                "language": "solidity",
                "task": "functions",
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body.get("ok") is True
        assert body.get("mode") == "code"
        assert body.get("language") == "solidity"


async def test_agent_tool_text_extract_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/agent/tools/text-extract",
            headers={"x-api-key": "test-key"},
            json={
                "text": "Transfer 10 ETH from 0xabc to 0xdef",
                "task": "ner",
                "extraction_schema": {"type": "object"},
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body.get("ok") is True
        assert body.get("mode") == "text"
        assert body.get("schema") is True
