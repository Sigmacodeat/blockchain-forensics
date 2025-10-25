import os
import pytest
import types
from typing import List, Dict, Any

from app.enrichment.labels_service import LabelsService

pytestmark = pytest.mark.asyncio


class FakeRedis:
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}
        self._pipe_cmds: List[tuple] = []

    # set methods
    async def sadd(self, key: str, *members):
        s = self.data.setdefault(key, set())
        if not isinstance(s, set):
            s = set()
        for m in members:
            s.add(m)
        self.data[key] = s

    async def smembers(self, key: str):
        val = self.data.get(key, set())
        return set(val) if isinstance(val, set) else set()

    async def expire(self, key: str, ttl: int):
        # no-op in fake
        return True

    async def hset(self, key: str, mapping: Dict[str, str]):
        h = self.data.setdefault(key, {})
        h.update(mapping)
        self.data[key] = h

    async def hgetall(self, key: str):
        return dict(self.data.get(key, {}))

    async def delete(self, key: str):
        self.data.pop(key, None)

    def pipeline(self):
        self._pipe_cmds = []
        fake = self

        class Pipe:
            def __init__(self):
                self.cmds: List[tuple] = []

            def smembers(self, key: str):
                self.cmds.append(("smembers", key))

            async def execute(self):
                out = []
                for cmd, key in self.cmds:
                    if cmd == "smembers":
                        out.append(await fake.smembers(key))
                return out

        return Pipe()

    async def close(self):
        return True


async def test_get_labels_detailed_offline(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    svc = LabelsService()
    # no redis -> detailed falls back to cache
    await svc.initialize()
    # ensure no network usage
    svc.redis_client = None
    # preload sample data
    svc.exchange_addresses["0xabc"] = "Binance Hot Wallet"
    det = await svc.get_labels_detailed("0xAbC")
    # order not guaranteed; convert to dict by label
    dmap = {d["label"]: d for d in det}
    assert "exchange" in dmap
    assert dmap["exchange"]["source"] == "cache"
    assert float(dmap["exchange"]["confidence"]) == 1.0


async def test_bulk_get_labels_with_redis_pipeline(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "1")
    svc = LabelsService()
    await svc.initialize()
    # attach fake redis with preloaded sets
    fake = FakeRedis({
        "labels:0x1": {"exchange", "binance"},
        "labels:0x2": {"sanctioned", "ofac"},
    })
    svc.redis_client = fake

    res = await svc.bulk_get_labels(["0x1", "0x2", "0x3"])  # 0x3 missing -> computed via get_labels
    assert set(res["0x1"]) == {"exchange", "binance"}
    assert set(res["0x2"]) == {"sanctioned", "ofac"}
    # 0x3 should be empty list (no labels known)
    assert res["0x3"] == []

    # ensure local cache populated for 0x1
    cached = svc.local_cache.get("labels:0x1")
    assert cached is not None and set(cached) == {"exchange", "binance"}
