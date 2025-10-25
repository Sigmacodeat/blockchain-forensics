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


def _sig_v2(secret: str, body: str, ts: str) -> str:
    base = f"{ts}.{body}"
    return hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("INTEL_WEBHOOK_SECRET_TRM", "secret-trm")
    monkeypatch.setenv("INTEL_WEBHOOK_SECRET", "secret-default")
    yield


@pytest.fixture
def client(monkeypatch):
    # Configure per-source rate limits: trm=2/min, default=1/min for test
    monkeypatch.setenv("INTEL_WEBHOOK_RATE_LIMITS", "trm:2,default:1")
    from app.middleware.rate_limit import RateLimitMiddleware
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    app.include_router(_load_intel_router(), prefix="/api/v1/intel")
    return TestClient(app)


def test_verify_endpoint_ok(client):
    body = json.dumps({"event": "ping"}, separators=(",", ":"))
    ts = str(int(time.time()))
    sig = _sig_v2("secret-trm", body, ts)
    r = client.post(
        "/api/v1/intel/webhooks/trm/verify",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": ts,
            "X-Webhook-Signature-V2": f"sha256={sig}",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "verified"


def test_per_source_rate_limit_trm_vs_default(client):
    # TRM has 2/min
    body_trm = json.dumps({"x": 1}, separators=(",", ":"))
    ts = str(int(time.time()))
    sig_trm = _sig_v2("secret-trm", body_trm, ts)
    headers_trm = {
        "Content-Type": "application/json",
        "X-Webhook-Timestamp": ts,
        "X-Webhook-Signature-V2": f"sha256={sig_trm}",
    }
    # First two should pass
    assert client.post("/api/v1/intel/webhooks/trm", data=body_trm, headers=headers_trm).status_code == 200
    assert client.post("/api/v1/intel/webhooks/trm", data=body_trm, headers=headers_trm).status_code == 200
    # Third should 429
    assert client.post("/api/v1/intel/webhooks/trm", data=body_trm, headers=headers_trm).status_code == 429

    # Default source: use global default secret and limit 1/min
    body_other = json.dumps({"y": 2}, separators=(",", ":"))
    sig_def = _sig_v2("secret-default", body_other, ts)
    headers_def = {
        "Content-Type": "application/json",
        "X-Webhook-Timestamp": ts,
        "X-Webhook-Signature-V2": f"sha256={sig_def}",
    }
    # First ok
    assert client.post("/api/v1/intel/webhooks/other", data=body_other, headers=headers_def).status_code == 200
    # Second should 429 due to default:1
    assert client.post("/api/v1/intel/webhooks/other", data=body_other, headers=headers_def).status_code == 429
