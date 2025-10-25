import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_cross_chain_path_offline(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/graph/cross-chain/path", params={"source": "0xabc", "target": "0xdef"})
        assert res.status_code == 200
        data = res.json()
        assert "paths" in data
        assert isinstance(data["paths"], list)


async def test_cross_chain_neighbors_offline(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/graph/cross-chain/neighbors", params={"address": "0xabc"})
        assert res.status_code == 200
        data = res.json()
        assert data["address"] == "0xabc"
        assert data["nodes"] == []
        assert data["edges"] == []


async def test_cross_chain_summary_offline(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/graph/cross-chain/summary", params={"address": "0xabc"})
        assert res.status_code == 200
        data = res.json()
        assert data["address"] == "0xabc"
        assert data["chains"] == {}
        assert data["degree"] == {"in": 0, "out": 0}
        assert data["bridges"] == {"outbound": 0, "inbound": 0}


async def test_cluster_details_offline(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/graph/cluster", params={"address": "0xabc"})
        assert res.status_code == 200
        data = res.json()
        assert data["address"] == "0xabc"
        assert data["cluster_id"] is None
        assert data["size"] == 0
        assert data["members"] == []
