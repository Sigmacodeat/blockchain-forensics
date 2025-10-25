import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_trace_taint_proportional_smoke():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Uses placeholder address; endpoint should validate and may 400 on invalid
        res = await ac.get("/api/v1/trace/taint", params={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
            "depth": 2,
            "threshold": 0.1,
            "model": "proportional",
        })
        # accept 200 (env with data) or 400 (invalid addr) gracefully
        assert res.status_code in (200, 400)
        if res.status_code == 200:
            data = res.json()
            assert data.get("model") == "proportional"
            assert "paths" in data and "summary" in data and "targets" in data


async def test_trace_taint_fifo_smoke():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/trace/taint", params={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
            "depth": 2,
            "threshold": 0.1,
            "model": "fifo",
        })
        assert res.status_code in (200, 400)
        if res.status_code == 200:
            data = res.json()
            assert data.get("model") == "fifo"
            assert "paths" in data and "summary" in data


async def test_trace_taint_haircut_smoke():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/trace/taint", params={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
            "depth": 2,
            "threshold": 0.1,
            "model": "haircut",
        })
        assert res.status_code in (200, 400)
        if res.status_code == 200:
            data = res.json()
            assert data.get("model") == "haircut"
            assert "paths" in data and "summary" in data


async def test_trace_taint_models_invalid_model():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/trace/taint", params={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
            "depth": 2,
            "threshold": 0.1,
            "model": "invalid",
        })
        # FastAPI should 422 on invalid enum/regex
        assert res.status_code == 422


async def test_trace_cluster_smoke():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/trace/cluster", params={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
        })
        # accept 200 (env with graph) or 400 if address rejected by validation
        assert res.status_code in (200, 400)
        if res.status_code == 200:
            data = res.json()
            assert "cluster_id" in data
            assert "members" in data


async def test_trace_taint_depth3_performance_smoke():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/trace/taint", params={
            "chain": "ethereum",
            "address": "0x0000000000000000000000000000000000000000",
            "depth": 3,
            "threshold": 0.05,
            "model": "proportional",
        })
        assert res.status_code in (200, 400)
