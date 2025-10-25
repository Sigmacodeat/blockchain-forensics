import os
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

# Ensure lifespan doesn't try to initialize external services
os.environ.setdefault("DISABLE_LIFESPAN", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def override_auth_dependency(monkeypatch):
    from app.auth import dependencies as deps
    app.dependency_overrides[deps.get_current_user_strict] = lambda: {"user": "test"}
    yield
    app.dependency_overrides = {}


def test_healthz_liveness():
    client = TestClient(app)
    r = client.get("/api/v1/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body
    assert "platform" in body


def test_readyz_readiness(monkeypatch):
    client = TestClient(app)

    # Mock DB/Redis healthy and worker heartbeat
    from app.db import postgres
    from app.db import redis_client as redis_mod
    
    async def _ok():
        return True
    monkeypatch.setattr(postgres.postgres_client, "health_check", _ok, raising=True)

    async def _verify():
        return True
    async def _list_worker_statuses():
        return {
            "monitor_worker": {"status": "running", "last_heartbeat": datetime.utcnow().isoformat(), "processed_count": 10, "error_count": 0}
        }
    monkeypatch.setattr(redis_mod, "verify_connectivity", _verify, raising=True)
    monkeypatch.setattr(redis_mod, "list_worker_statuses", _list_worker_statuses, raising=True)

    r = client.get("/api/v1/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ready", "not_ready")
    assert body["database"]["healthy"] is True
    assert body["redis"]["healthy"] is True
    assert "workers" in body
    assert "alert_engine" in body
