import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_set_risk_weights_allowed_in_test_mode(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # read current
        before = await ac.get("/api/v1/risk/weights")
        assert before.status_code == 200
        # set new weights
        res = await ac.post("/api/v1/risk/weights", json={"watchlist": 0.5, "labels": 0.2, "taint": 0.1, "exposure": 0.2})
        assert res.status_code == 200
        data = res.json()
        w = data["weights"]
        assert w["watchlist"] == 0.5
        assert w["labels"] == 0.2
        assert w["taint"] == 0.1
        assert w["exposure"] == 0.2
