import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_risk_address_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/risk/address", params={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
        })
        assert res.status_code == 200
        data = res.json()
        assert "result" in data
        r = data["result"]
        assert set(["chain", "address", "score", "factors", "categories", "reasons"]).issubset(r)
        assert r["chain"] == "ethereum"


async def test_risk_address_invalid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/risk/address", params={
            "chain": "ethereum",
            "address": "not_an_address",
        })
        assert res.status_code == 200
        r = res.json()["result"]
        assert r["score"] in (0,)
        assert "invalid" in r.get("categories", [])


async def test_risk_batch():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "items": [
                {"chain": "ethereum", "address": "0x0000000000000000000000000000000000000000"},
                {"chain": "solana", "address": "So11111111111111111111111111111111111111112"},
            ]
        }
        res = await ac.post("/api/v1/risk/batch", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert "results" in body and isinstance(body["results"], list)
        assert len(body["results"]) == 2
