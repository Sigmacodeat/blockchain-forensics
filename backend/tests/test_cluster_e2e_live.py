import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

pytestmark = pytest.mark.asyncio

LIVE = os.getenv("LIVE_NEO4J") == "1"


@pytest.mark.skipif(not LIVE, reason="LIVE_NEO4J=1 required for E2E cluster test")
async def test_cluster_resolve_live():
    # Assumes Neo4j has some data; this is a smoke test only
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # pick any address present in your dataset
        addr = os.getenv("E2E_SEED_ADDRESS", "0x0000000000000000000000000000000000000000")
        res = await ac.post("/api/v1/graph/cluster/resolve", params={"address": addr})
        assert res.status_code == 200
        data = res.json()
        assert "cluster_id" in data
        # fetch details
        det = await ac.get("/api/v1/graph/cluster", params={"address": addr})
        assert det.status_code == 200
        d = det.json()
        assert "members" in d
