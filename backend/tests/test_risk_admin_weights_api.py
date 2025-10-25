import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_admin_weights_requires_header(monkeypatch):
    monkeypatch.delenv("TEST_MODE", raising=False)  # ensure normal guard
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Without header should be forbidden (unless DEBUG True which defaults False)
        res = await ac.put("/api/v1/risk/weights/admin", json={"watchlist": 0.4})
        assert res.status_code == 403


async def test_admin_weights_with_header(monkeypatch):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            "/api/v1/risk/weights/admin",
            headers={"X-Admin": "1"},
            json={"watchlist": 0.33, "graph": 0.11},
        )
        assert res.status_code == 200
        data = res.json()
        assert "weights" in data
        w = data["weights"]
        assert abs(w["watchlist"] - 0.33) < 1e-9
        assert abs(w["graph"] - 0.11) < 1e-9
