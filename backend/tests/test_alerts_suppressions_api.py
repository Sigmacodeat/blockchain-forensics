import os
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


def test_suppressions_statistics_and_clear(monkeypatch):
    # Patch facade methods (module: app.services.alert_service)
    from app.services.alert_service import alert_service as _as

    monkeypatch.setattr(_as, "get_suppression_events_count", lambda: 5, raising=True)
    monkeypatch.setattr(_as, "get_suppression_statistics", lambda: {"total_suppressions": 5, "by_reason": {"dedup_window": 3}}, raising=True)
    monkeypatch.setattr(_as, "clear_suppression_events", lambda: 5, raising=True)

    client = TestClient(app)

    # statistics
    r2 = client.get("/api/v1/alerts/suppressions/statistics")
    assert r2.status_code == 200, r2.text
    stats = r2.json()
    assert stats["total_suppressions"] == 5
    assert stats["by_reason"]["dedup_window"] == 3

    # clear
    r3 = client.post("/api/v1/alerts/suppressions/clear")
    assert r3.status_code == 200, r3.text
    out = r3.json()
    assert out["cleared_count"] == 5
    assert out["status"] == "success"
