import os
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

os.environ["TEST_MODE"] = "1"
os.environ["PYTEST_CURRENT_TEST"] = "1"

from app.main import app
from app.auth.dependencies import get_current_user_strict


@pytest.fixture(autouse=True)
def _patch_auth():
    app.dependency_overrides[get_current_user_strict] = lambda: {"id": "test-user"}
    yield
    app.dependency_overrides.pop(get_current_user_strict, None)


@pytest.mark.asyncio
async def test_kpis_endpoint_with_case_mttr_and_sla(monkeypatch):
    # Patch alert_service recent alerts (used for sanctions + annotations mapping)
    now = datetime.utcnow()

    class DummyAlert:
        def __init__(self, alert_id, ts, address=None):
            self.alert_id = alert_id
            self.timestamp = ts
            self.address = address

    alerts = [
        DummyAlert("a1", now - timedelta(hours=1), address="0xabc"),
        DummyAlert("a2", now - timedelta(hours=1), address="0xdef"),
    ]

    from app.services.kpi_service import alert_service as kpi_alert_service
    monkeypatch.setattr(kpi_alert_service, "get_recent_alerts", lambda limit=10000: alerts)

    # Patch sanctions repo
    async def _count_hits(addresses):
        return len({a for a in addresses if a})

    from app.services.kpi_service import sanctions_repository as kpi_sanctions_repo
    monkeypatch.setattr(kpi_sanctions_repo, "count_distinct_hits", _count_hits)

    # Patch annotations for MTTD computation
    class Ann:
        def __init__(self, aid, disp=None, ev=None):
            self.alert_id = aid
            self.disposition = disp
            self.event_time = ev
            self.created_at = now

    def _get_map(ids):
        return {
            "a1": Ann("a1", disp="false_positive", ev=now - timedelta(hours=5)),
            "a2": Ann("a2", disp="true_positive", ev=now - timedelta(hours=3)),
        }

    from app.services.kpi_service import alert_annotation_service as kpi_ann_service
    monkeypatch.setattr(kpi_ann_service, "get_annotations_map", lambda ids: _get_map(ids))

    # Patch redis cache (no-op)
    from app.services.kpi_service import redis_client

    async def _cache_get(_):
        return None

    async def _cache_set(*args, **kwargs):
        return True

    monkeypatch.setattr(redis_client, "cache_get", _cache_get)
    monkeypatch.setattr(redis_client, "cache_set", _cache_set)

    # Patch case_service for MTTR/SLA
    class DummyCaseService:
        def query_cases(self, limit: int, offset: int):
            # Two closed cases: 24h (within SLA 48h), 72h (breach)
            return {
                "cases": [
                    {"created_at": (now - timedelta(hours=80)).isoformat(), "closed_at": (now - timedelta(hours=56)).isoformat()},  # 24h
                    {"created_at": (now - timedelta(hours=78)).isoformat(), "closed_at": (now - timedelta(hours=6)).isoformat()},   # 72h
                ]
            }

    from app.services import kpi_service as kpi_mod
    monkeypatch.setattr(kpi_mod, "case_service", DummyCaseService(), raising=False)

    client = TestClient(app)
    resp = client.get("/api/v1/alerts/kpis?days=7&sla_hours=48")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Sanctions hits = 2 distinct addresses
    assert data["sanctions_hits"] == 2
    # FPR = 0.5 (1 FP / 2 labeled)
    assert 0.49 <= data["fpr"] <= 0.51
    # MTTD ~ 3h
    assert 2.5 <= data["mttd"] <= 3.5
    # MTTR median of [24, 72] = (24+72)/2=48h
    assert 47.5 <= data["mttr"] <= 48.5
    # SLA breach rate: 1 of 2 (>48h)
    assert 0.49 <= data["sla_breach_rate"] <= 0.51
