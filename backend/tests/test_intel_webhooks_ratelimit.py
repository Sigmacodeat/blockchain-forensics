import json
import hmac
import hashlib
import time
import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware

import sys
import importlib.util
from pathlib import Path
from types import ModuleType


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("INTEL_WEBHOOK_SECRET", "test-secret")
    yield


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


@pytest.fixture
def client():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    app.include_router(_load_intel_router(), prefix="/api/v1/intel")
    return TestClient(app)


def _legacy_sig(secret: str, body: str) -> str:
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


def test_ratelimit_intel_webhook_prefix(client):
    body = {"event": "ioc.update", "data": {}, "delivery_id": "d-x"}
    body_json = json.dumps(body, separators=(",", ":"))
    sig = _legacy_sig("test-secret", body_json)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": f"sha256={sig}",
    }

    # 60 requests should pass, 61st should be 429 due to endpoint limit 60/min
    ok = 0
    for i in range(60):
        r = client.post("/api/v1/intel/webhooks/trm", data=body_json, headers=headers)
        assert r.status_code == 200, r.text
        ok += 1
    r = client.post("/api/v1/intel/webhooks/trm", data=body_json, headers=headers)
    assert r.status_code == 429
