import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.auth.jwt import create_access_token
from app.auth.models import UserRole

pytestmark = pytest.mark.asyncio


async def test_labels_detailed_offline(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/labels/detailed", params={"chain": "ethereum", "address": "0xabc"})
        assert res.status_code == 200
        data = res.json()
        assert data["chain"] == "ethereum"
        assert data["address"] == "0xabc"
        assert isinstance(data["labels"], list)


async def test_labels_bulk(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"addresses": ["0x1", "0x2"]}
        res = await ac.post("/api/v1/labels/bulk", params={"chain": "ethereum"}, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["chain"] == "ethereum"
        assert set(data["results"].keys()) == {"0x1", "0x2"}


async def test_labels_admin_endpoints_guard_and_success(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Guard: no auth
        r1 = await ac.post("/api/v1/labels/admin/sanctions/refresh", params={"force": True})
        assert r1.status_code == 403
        # With admin JWT
        token_admin = create_access_token("u2", "admin@example.com", UserRole.ADMIN)
        r2 = await ac.post(
            "/api/v1/labels/admin/sanctions/refresh",
            params={"force": True, "authorization": f"Bearer {token_admin}"},
        )
        assert r2.status_code == 200
        # Cache invalidate without auth -> 403
        r3 = await ac.post("/api/v1/labels/admin/cache/invalidate", json={"address": "0xabc"})
        assert r3.status_code == 403
        # With admin JWT
        r4 = await ac.post(
            "/api/v1/labels/admin/cache/invalidate",
            params={"authorization": f"Bearer {token_admin}"},
            json={"address": "0xabc"},
        )
        assert r4.status_code == 200
        assert r4.json()["invalidated"] == "0xabc"
