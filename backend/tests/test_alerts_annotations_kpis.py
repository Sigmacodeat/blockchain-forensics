import os
import pytest
from fastapi.testclient import TestClient

os.environ["TEST_MODE"] = "1"
os.environ["PYTEST_CURRENT_TEST"] = "1"

from app.main import app
from app.auth.dependencies import get_current_user_strict


@pytest.fixture(autouse=True)
def _patch_auth(monkeypatch):
    # Bypass strict auth dependency using FastAPI overrides
    app.dependency_overrides[get_current_user_strict] = lambda: {"id": "test-user", "email": "test@example.com"}
    yield
    app.dependency_overrides.pop(get_current_user_strict, None)


def test_kpis_annotations_endpoint(monkeypatch):
    # Patch summary to deterministic payload
    from app.services import alert_annotation_service as svc_mod
    monkeypatch.setattr(
        svc_mod.alert_annotation_service,
        "get_kpi_summary",
        lambda since=None, until=None: {
            "dispositions": {"counts": {"false_positive": 1, "true_positive": 1}, "reviewed": 2, "false_positive_rate": 0.5, "window": {}},
            "mttd": {"count": 2, "average_seconds": 7200.0, "window": {}},
        },
        raising=True,
    )

    with TestClient(app) as client:
        resp = client.get("/api/v1/alerts/kpis/annotations?days=7")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "dispositions" in data and "mttd" in data
        assert data["dispositions"]["false_positive_rate"] == 0.5
        assert data["mttd"]["average_seconds"] == 7200.0
