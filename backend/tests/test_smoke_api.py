import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/metrics")
        assert res.status_code == 200
        body = res.text
        assert "chain_requests_total" in body or "# HELP chain_request_latency_seconds" in body


async def test_compliance_screen_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/compliance/screen", params={"chain": "ethereum", "address": "0x0000000000000000000000000000000000000000"})
        assert res.status_code == 200
        data = res.json()
        assert "result" in data
        assert set(["chain", "address", "risk_score", "categories", "reasons", "watchlisted"]).issubset(data["result"].keys())


async def test_labels_lookup_smoke():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/labels/", params={"chain": "ethereum", "address": "0xdeadbeef"})
        if res.status_code != 200:
            pytest.skip("Labels DB not configured in test env")
        data = res.json()
        assert data["chain"] == "ethereum"
        assert data["address"] == "0xdeadbeef"
        assert "labels" in data


async def test_compliance_watchlist_smoke():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/compliance/watchlist")
        if res.status_code != 200:
            pytest.skip("Compliance DB not configured in test env")
        data = res.json()
        assert "items" in data
        assert isinstance(data["items"], list)


async def test_labels_add_and_lookup():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"chain": "ethereum", "address": "0xfeedface", "label": "test_label", "category": "test"}
        res_add = await ac.post("/api/v1/labels/", json=payload)
        if res_add.status_code != 200:
            pytest.skip("Labels DB not configured in test env")
        created = res_add.json().get("created", {})
        assert created.get("label") == "test_label"

        res_get = await ac.get("/api/v1/labels/", params={"chain": "ethereum", "address": "0xfeedface"})
        assert res_get.status_code == 200
        data = res_get.json()
        assert any(l.get("label") == "test_label" for l in data.get("labels", []))


async def test_compliance_watchlist_add_and_filter():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {"chain": "ethereum", "address": "0xadd2watch", "reason": "test"}
        res_add = await ac.post("/api/v1/compliance/watchlist", json=payload)
        if res_add.status_code != 200:
            pytest.skip("Compliance DB not configured in test env")
        created = res_add.json().get("created", {})
        assert created.get("address") == "0xadd2watch"

        res_filter = await ac.get("/api/v1/compliance/watchlist", params={"chain": "ethereum", "address": "0xadd2watch"})
        assert res_filter.status_code == 200
        items = res_filter.json().get("items", [])
        assert any(i.get("address") == "0xadd2watch" for i in items)


async def test_compliance_watchlist_pagination():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # request first page
        res1 = await ac.get("/api/v1/compliance/watchlist", params={"limit": 2, "offset": 0})
        if res1.status_code != 200:
            pytest.skip("Compliance DB not configured in test env")
        page1 = res1.json()
        assert "items" in page1 and isinstance(page1["items"], list)
        assert "total" in page1 and isinstance(page1["total"], int)

        # request second page
        res2 = await ac.get("/api/v1/compliance/watchlist", params={"limit": 2, "offset": 2})
        assert res2.status_code == 200
        page2 = res2.json()
        assert "items" in page2 and isinstance(page2["items"], list)
        assert "total" in page2 and isinstance(page2["total"], int)
        # sanity: total >= len(items)
        assert page1["total"] >= len(page1["items"]) >= 0
        assert page2["total"] >= len(page2["items"]) >= 0


async def test_compliance_watchlist_pagination_invalid_params():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # invalid limit (too small)
        res = await ac.get("/api/v1/compliance/watchlist", params={"limit": 0, "offset": 0})
        assert res.status_code == 422
        # invalid limit (too large)
        res = await ac.get("/api/v1/compliance/watchlist", params={"limit": 10000, "offset": 0})
        assert res.status_code == 422
        # invalid offset (negative)
        res = await ac.get("/api/v1/compliance/watchlist", params={"limit": 10, "offset": -1})
        assert res.status_code == 422
