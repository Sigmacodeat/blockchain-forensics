import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.auth.jwt import create_access_token
from app.auth.models import UserRole

pytestmark = pytest.mark.asyncio


async def test_admin_weights_requires_jwt_admin(monkeypatch):
    # No header, no debug -> 403
    monkeypatch.delenv("TEST_MODE", raising=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put("/api/v1/risk/weights/admin", json={"watchlist": 0.5})
        assert res.status_code == 403

    # Non-admin JWT -> 403
    token_user = create_access_token("u1", "user@example.com", UserRole.VIEWER)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            "/api/v1/risk/weights/admin",
            headers={"Authorization": f"Bearer {token_user}"},
            json={"watchlist": 0.5},
        )
        assert res.status_code == 403

    # Admin JWT -> 200
    token_admin = create_access_token("u2", "admin@example.com", UserRole.ADMIN)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.put(
            "/api/v1/risk/weights/admin",
            headers={"Authorization": f"Bearer {token_admin}"},
            json={"watchlist": 0.44, "graph": 0.12},
        )
        assert res.status_code == 200
        data = res.json()
        w = data["weights"]
        assert abs(w["watchlist"] - 0.44) < 1e-9
        assert abs(w["graph"] - 0.12) < 1e-9
