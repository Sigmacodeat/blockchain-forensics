import os
import json
import time
import hmac
import hashlib
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sys
import importlib.util
from pathlib import Path
from types import ModuleType
from app.db.redis_client import redis_client


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("INTEL_WEBHOOK_SECRET", "test-secret")
    # Ensure RateLimit middleware is present if needed; not required for these tests
    yield


@pytest.fixture
def client():
    backend_dir = Path(__file__).resolve().parents[1]
    intel_path = backend_dir / "app" / "api" / "v1" / "intel.py"
    # Prepare dummy package hierarchy to avoid executing app.api.v1.__init__
    for pkg in ["app", "app.api", "app.api.v1"]:
        if pkg not in sys.modules:
            sys.modules[pkg] = ModuleType(pkg)
    spec = importlib.util.spec_from_file_location("app.api.v1.intel", intel_path)
    intel_mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(intel_mod)  # type: ignore
    sys.modules["app.api.v1.intel"] = intel_mod
    _app = FastAPI()
    _app.include_router(intel_mod.router, prefix="/api/v1/intel")
    return TestClient(_app)


class _IdemStore:
    def __init__(self):
        self.store = {}

    async def check(self, key, ttl=86400):
        return self.store.get(key)

    async def put(self, key, result, ttl=86400):
        self.store[key] = result


@pytest.fixture
def stub_idempotency(monkeypatch):
    idem = _IdemStore()
    monkeypatch.setattr(redis_client, "check_idempotency", idem.check)
    monkeypatch.setattr(redis_client, "store_idempotency_result", idem.put)
    return idem


def _sig_v2(secret: str, body: str, ts: str) -> str:
    base = f"{ts}.{body}"
    return hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()


def test_ingest_webhook_v2_valid(client, stub_idempotency):
    body = {"event": "ioc.update", "data": {"addresses": ["0xabc"]}, "delivery_id": "d-1"}
    body_json = json.dumps(body, separators=(",", ":"))
    ts = str(int(time.time()))
    sig = _sig_v2("test-secret", body_json, ts)

    r = client.post(
        "/api/v1/intel/webhooks/trm",
        data=body_json,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": ts,
            "X-Webhook-Signature-V2": f"sha256={sig}",
            "Idempotency-Key": "d-1",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "ok"
    # Second call returns same (idempotent)
    r2 = client.post(
        "/api/v1/intel/webhooks/trm",
        data=body_json,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": ts,
            "X-Webhook-Signature-V2": f"sha256={sig}",
            "Idempotency-Key": "d-1",
        },
    )
    assert r2.status_code == 200
    assert r2.json() == data


def test_ingest_webhook_invalid_signature(client):
    body = {"event": "ioc.update", "data": {}, "delivery_id": "d-2"}
    body_json = json.dumps(body, separators=(",", ":"))
    ts = str(int(time.time()))

    r = client.post(
        "/api/v1/intel/webhooks/trm",
        data=body_json,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": ts,
            "X-Webhook-Signature-V2": "sha256=deadbeef",
        },
    )
    assert r.status_code == 401


def test_ingest_webhook_legacy_signature(client):
    body = {"event": "ioc.update", "data": {}, "delivery_id": "d-3"}
    body_json = json.dumps(body, separators=(",", ":"))
    sig = hmac.new(b"test-secret", body_json.encode(), hashlib.sha256).hexdigest()

    r = client.post(
        "/api/v1/intel/webhooks/trm",
        data=body_json,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={sig}",
        },
    )
    assert r.status_code == 200
