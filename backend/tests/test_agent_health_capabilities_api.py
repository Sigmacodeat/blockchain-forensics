import os
import pytest
from httpx import AsyncClient

# Minimal settings
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ENABLE_AI_AGENTS", "true")

from app.main import app  # noqa: E402

pytestmark = pytest.mark.anyio("asyncio")


async def test_agent_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/v1/agent/health")
        assert res.status_code == 200
        body = res.json()
        assert body.get("enabled") in (True, False)
        assert isinstance(body.get("tools_registered", 0), int)
        assert isinstance(body.get("tools", []), list)


async def test_agent_capabilities_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/v1/agent/capabilities")
        assert res.status_code == 200
        body = res.json()
        assert body.get("enabled") in (True, False)
        assert isinstance(body.get("tools", []), list)
        # each tool entry should have a name
        if body["tools"]:
            assert all("name" in t for t in body["tools"])  
