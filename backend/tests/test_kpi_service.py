import os
from datetime import datetime, timedelta
from types import SimpleNamespace
import pytest

os.environ["TEST_MODE"] = "1"

from app.services.kpi_service import kpi_service


class DummyAlert:
    def __init__(self, alert_id: str, ts: datetime, address: str | None = None):
        self.alert_id = alert_id
        self.timestamp = ts
        self.address = address


@pytest.mark.asyncio
async def test_kpis_basic_monkeypatched(monkeypatch):
    now = datetime.utcnow()
    # Use timestamps near 'now' so that event_time (earlier) yields positive MTTD
    alerts = [
        DummyAlert("a1", now - timedelta(hours=1), address="0xabc"),
        DummyAlert("a2", now - timedelta(hours=1), address="0xdef"),
        DummyAlert("a3", now - timedelta(hours=1), address=None),
    ]

    # Patch alert_service.get_recent_alerts
    monkeypatch.setattr("app.services.kpi_service.alert_service.get_recent_alerts", lambda limit=10000: alerts)

    # Patch sanctions repo
    async def _count_hits(addresses):
        # return number of distinct non-empty addresses
        return len({a for a in addresses if a})

    monkeypatch.setattr("app.services.kpi_service.sanctions_repository.count_distinct_hits", _count_hits)

    # Patch annotations
    class Ann:
        def __init__(self, aid, disp=None, ev=None):
            self.alert_id = aid
            self.disposition = disp
            self.event_time = ev
            self.created_at = now

    def _get_map(ids):
        # mark one FP, one TP, one unlabeled; set event_time for MTTD for two
        return {
            "a1": Ann("a1", disp="false_positive", ev=now - timedelta(hours=5)),
            "a2": Ann("a2", disp="true_positive", ev=now - timedelta(hours=3)),
            # a3 absent
        }

    monkeypatch.setattr("app.services.kpi_service.alert_annotation_service.get_annotations_map", lambda ids: _get_map(ids))

    # Patch redis cache to no-op
    async def _cache_get(_):
        return None

    async def _cache_set(*args, **kwargs):
        return True

    monkeypatch.setattr("app.services.kpi_service.redis_client.cache_get", _cache_get)
    monkeypatch.setattr("app.services.kpi_service.redis_client.cache_set", _cache_set)

    res = await kpi_service.get_kpis(days=7, sla_hours=48)

    assert res.sanctions_hits == 2
    # FPR: labeled = 2 (a1 FP, a2 TP) -> 1/2
    assert 0.49 <= res.fpr <= 0.51
    # MTTD: avg hours across a1 (1h - 5h -> 4h) & a2 (1h - 3h -> 2h) = 3h, tolerance
    assert 2.5 <= res.mttd <= 3.5
    # MTTR is 0 due to no case_service in test
    assert res.mttr == 0.0
    # SLA breach rate 0 by default
    assert res.sla_breach_rate == 0.0
