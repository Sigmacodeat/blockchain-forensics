import os
import pytest
from fastapi.testclient import TestClient

# Ensure lifespan is disabled and pytest flags are set
os.environ.setdefault("DISABLE_LIFESPAN", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.main import app  # noqa: E402


def test_alerts_requires_auth_without_override():
    client = TestClient(app)
    # No dependency override here -> should be 401 for protected routes
    r = client.get("/api/v1/alerts/stats")
    assert r.status_code in (401, 403)


@pytest.fixture()
def with_auth_override():
    from app.auth import dependencies as deps
    app.dependency_overrides[deps.get_current_user_strict] = lambda: {"user": "test"}
    yield
    app.dependency_overrides = {}


def test_alerts_stats_with_auth(with_auth_override):
    client = TestClient(app)
    r = client.get("/api/v1/alerts/stats")
    assert r.status_code == 200
    body = r.json()
    assert "total_alerts" in body
    assert "by_severity" in body


def test_alerts_recent_with_auth(with_auth_override):
    client = TestClient(app)
    r = client.get("/api/v1/alerts/recent?limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
