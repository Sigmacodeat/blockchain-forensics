import asyncio
import types
import pytest

from datetime import datetime

from app.streaming.monitor_consumer import process_event


class DummyConn:
    def __init__(self):
        self.insert_calls = 0
        self.update_calls = 0

    async def fetchrow(self, *args, **kwargs):
        # Return an id on first call to simulate insert success
        self.insert_calls += 1
        return {"id": "00000000-0000-0000-0000-000000000000"}

    async def execute(self, *args, **kwargs):
        self.update_calls += 1
        return None


class DummyAcquire:
    def __init__(self, conn: DummyConn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_monitor_process_event_creates_alert(monkeypatch):
    # Mock monitor_service.list_rules to return one enabled rule
    async def _list_rules():
        class R:
            def __init__(self):
                self.enabled = True
            def model_dump(self):
                return {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "name": "high_value", "severity": "high", "expression": {"gte": ["value_usd", 1000]}}
        return [R()]

    ms_mod = __import__("app.compliance.monitor_service", fromlist=["monitor_service"]).monitor_service
    monkeypatch.setattr(ms_mod, "list_rules", _list_rules)

    # Mock rule_engine.evaluate to always return True
    re_mod = __import__("app.compliance.rule_engine", fromlist=["rule_engine"]).rule_engine
    def _evaluate(expr, event):
        return True
    monkeypatch.setattr(re_mod, "evaluate", _evaluate)

    # Mock postgres_client.acquire to a dummy async context manager
    pc_mod = __import__("app.db.postgres", fromlist=["postgres_client"]).postgres_client
    dummy_conn = DummyConn()
    def _acquire():
        return DummyAcquire(dummy_conn)
    monkeypatch.setattr(pc_mod, "acquire", _acquire)

    # Build minimal event
    event = {
        "chain": "ethereum",
        "tx_hash": "0xabc",
        "from_address": "0x111",
        "to_address": "0x222",
        "value_usd": 5000,
        "labels": [],
        "metadata": {},
        "timestamp": datetime.utcnow().isoformat(),
    }

    created = await process_event(event)

    assert created >= 1
