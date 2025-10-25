import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_cluster_resolve_offline(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/graph/cluster/resolve", params={"address": "0xabc"})
        assert res.status_code == 200
        data = res.json()
        assert data == {"cluster_id": None, "members": []}
