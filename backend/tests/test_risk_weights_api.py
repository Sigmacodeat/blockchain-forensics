import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_get_risk_weights():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/risk/weights")
        assert res.status_code == 200
        data = res.json()
        assert "weights" in data
        w = data["weights"]
        for k in ("watchlist", "labels", "taint", "exposure"):
            assert k in w
            assert isinstance(w[k], (int, float))
