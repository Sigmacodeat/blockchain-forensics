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


def _load_intel_router():
    backend_dir = Path(__file__).resolve().parents[1]
    intel_path = backend_dir / "app" / "api" / "v1" / "intel.py"
    for pkg in ["app", "app.api", "app.api.v1"]:
        if pkg not in sys.modules:
            sys.modules[pkg] = ModuleType(pkg)
    spec = importlib.util.spec_from_file_location("app.api.v1.intel", intel_path)
    intel_mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(intel_mod)  # type: ignore
    sys.modules["app.api.v1.intel"] = intel_mod
    return intel_mod.router


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("INTEL_WEBHOOK_SECRET", "test-secret")
    yield


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(_load_intel_router(), prefix="/api/v1/intel")
    return TestClient(app)


def _sig_v2(secret: str, body: str, ts: str) -> str:
    base = f"{ts}.{body}"
    return hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()


def test_recent_endpoint(client):
    # Ensure it returns list, even when empty at start
    r = client.get("/api/v1/intel/webhooks/recent?limit=5")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_content_type_enforced(client):
    body = '{"event":"x","data":{}}'
    ts = str(int(time.time()))
    sig = _sig_v2("test-secret", f"{ts}.{body}".split(".",1)[1], ts)  # compute correctly
    r = client.post(
        "/api/v1/intel/webhooks/trm",
        data=body,
        headers={
            "Content-Type": "text/plain",
            "X-Webhook-Timestamp": ts,
            "X-Webhook-Signature-V2": f"sha256={sig}",
        },
    )
    assert r.status_code == 415


def test_payload_too_large(client, monkeypatch):
    monkeypatch.setenv("MAX_INTEL_WEBHOOK_BODY_KB", "1")  # 1KB
    body = "{\"x\":\"" + ("a" * 2048) + "\"}"
    ts = str(int(time.time()))
    sig = _sig_v2("test-secret", f"{ts}.{body}".split(".",1)[1], ts)
    r = client.post(
        "/api/v1/intel/webhooks/trm",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": ts,
            "X-Webhook-Signature-V2": f"sha256={sig}",
        },
    )
    assert r.status_code == 413
