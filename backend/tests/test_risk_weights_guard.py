import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_set_risk_weights_forbidden_when_not_test_or_debug(monkeypatch):
    # Ensure guard active
    monkeypatch.delenv("TEST_MODE", raising=False)
    # Force DEBUG False via env override (pydantic settings may cache; assume default False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/risk/weights", json={"watchlist": 0.4})
        assert res.status_code == 403
