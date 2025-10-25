import os
import pytest
from httpx import AsyncClient

# Ensure minimal required env
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ENABLE_AI_AGENTS", "true")
os.environ.setdefault("TEST_MODE", "1")  # skip external DB connects
os.environ.setdefault("API_KEYS", "test-key")
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
            "summary": "extracted",
        }

    def _extract_from_text(self, text: str, *, schema=None, task=None):
        return {
            "ok": True,
            "mode": "text",
            "task": task,
            "schema": bool(schema),
            "summary": "extracted",
        }

    monkeypatch.setattr(KiloClient, "extract_from_code", _extract_from_code)
    monkeypatch.setattr(KiloClient, "extract_from_text", _extract_from_text)


async def test_post_extraction_code():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/extraction/code",
            headers={"x-api-key": "test-key"},
            json={
                "code": "function foo(){}",
                "language": "javascript",
                "task": "functions",
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body.get("ok") is True
        assert body.get("mode") == "code"
        assert body.get("language") == "javascript"


async def test_post_extraction_text():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/extraction/text",
            headers={"x-api-key": "test-key"},
            json={
                "text": "Transfer 10 ETH from A to B",
                "task": "ner",
                "schema": {"type": "object"},
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body.get("ok") is True
        assert body.get("mode") == "text"
        assert body.get("schema") is True
