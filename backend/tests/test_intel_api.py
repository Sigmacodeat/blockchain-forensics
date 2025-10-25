import os
import sys
import pathlib
import json
import types
from fastapi.testclient import TestClient

# Ensure backend on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Test mode for relaxed auth or other guards
os.environ.setdefault("TEST_MODE", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.main import app  # noqa: E402
from app.api.v1 import intel as intel_api  # noqa: E402

client = TestClient(app)


def test_publish_and_policies(monkeypatch):
    # Mock intel_service
    class _StubIntelService:
        def publish(self, ev):
            return {"ok": True, "echo": ev}
        def policies(self):
            return [
                {"id": "p1", "name": "Default", "rules": [], "approvers": [], "status": "active"}
            ]
    monkeypatch.setattr(intel_api, "intel_service", _StubIntelService())

    # Publish
    payload = {"type": "label", "payload": {"k": "v"}, "tlp": "GREEN"}
    r = client.post("/api/v1/intel/publish", json=payload)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # Policies
    r2 = client.get("/api/v1/intel/policies")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
    assert r2.json()[0]["id"] == "p1"


def test_webhook_missing_secret(monkeypatch):
    # Ensure no secret set
    os.environ.pop("INTEL_WEBHOOK_SECRET", None)
    os.environ.pop("INTEL_WEBHOOK_SECRET_TEST", None)

    # Mock verify_signature not used due to missing secret
    r = client.post(
        "/api/v1/intel/webhooks/test",
        data=json.dumps({"a": 1}),
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Missing webhook secret"


def test_webhook_invalid_signature(monkeypatch):
    os.environ["INTEL_WEBHOOK_SECRET_TEST"] = "s3cr3t"

    # Force signature verification to fail
    monkeypatch.setattr(intel_api, "verify_signature", lambda secret, headers, body: False)

    r = client.post(
        "/api/v1/intel/webhooks/test",
        data=json.dumps({"a": 1}),
        headers={"content-type": "application/json", "X-Sig": "bad"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid signature"


def test_webhook_ingest_success_with_idempotency(monkeypatch):
    os.environ["INTEL_WEBHOOK_SECRET_TEST"] = "s3cr3t"

    # Signature ok
    monkeypatch.setattr(intel_api, "verify_signature", lambda secret, headers, body: True)

    # Mock redis idempotency
    class _StubRedis:
        async def check_idempotency(self, key, ttl=86400):
            return None
        async def store_idempotency_result(self, key, result, ttl=86400):
            self.stored = (key, result)
    monkeypatch.setattr(intel_api, "redis_client", _StubRedis())

    # Mock threats ingester
    class _StubThreat:
        def ingest_inbound_event(self, source, payload):
            return {"received_at": "now", "payload": payload}
        def recent_inbound_events(self, limit=100):
            return [{"source": "test", "received_at": "now"}]
    monkeypatch.setattr(intel_api, "threat_intel_service", _StubThreat())

    # Mock audit trail to no-op
    class _Audit:
        def log_action(self, **kwargs):
            pass
    monkeypatch.setattr(intel_api, "audit_trail_service", _Audit())

    headers = {
        "content-type": "application/json",
        "Idempotency-Key": "DELIV-123",
    }
    body = {"a": 1}
    r = client.post("/api/v1/intel/webhooks/test", data=json.dumps(body), headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["source"] == "test"

    # Recent
    r2 = client.get("/api/v1/intel/webhooks/recent?limit=1")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
    assert r2.json()[0]["source"] == "test"


def test_admin_run_once_endpoints(monkeypatch):
    # Mock feeds.run_once and labels.run_once
    async def _feeds():
        return {"inserted": 1}
    async def _labels():
        return {"inserted": 2}

    # Patch lazy imports by injecting modules in sys.modules
    feeds_mod = types.ModuleType("app.intel.feeds")
    feeds_mod.run_once = _feeds
    labels_mod = types.ModuleType("app.ingest.labels_ingester")
    labels_mod.run_once = _labels
    sys.modules["app.intel.feeds"] = feeds_mod
    sys.modules["app.ingest.labels_ingester"] = labels_mod

    r1 = client.post("/api/v1/intel/feeds/run-once")
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"

    r2 = client.post("/api/v1/intel/labels/run-once")
    assert r2.status_code == 200
    assert r2.json()["status"] == "ok"
