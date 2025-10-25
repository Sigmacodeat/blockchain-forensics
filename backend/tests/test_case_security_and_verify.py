import os
import sys
import pathlib
import importlib
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402
from app.api.v1 import forensics as forensics_mod  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_api_key_and_rate_limit(monkeypatch, client):
    # Configure API key and low rate limit directly on module globals
    forensics_mod._API_KEY = "secret123"
    forensics_mod._RL_LIMIT = 2  # 2 req/min per IP+path
    forensics_mod._rl_store.clear()

    # Create case requires API key
    payload = {
        "case_id": "CASE-SEC-1",
        "title": "Sec Test",
        "description": "desc",
        "lead_investigator": "alice"
    }

    # Missing API key -> 401
    r = client.post("/api/v1/forensics/cases/create", json=payload)
    assert r.status_code == 401

    # Correct API key -> 200
    r = client.post(
        "/api/v1/forensics/cases/create",
        headers={"X-API-Key": "secret123"},
        json=payload,
    )
    assert r.status_code == 200

    # Rate limit test on checksum endpoint
    # First 2 requests should pass, 3rd should 429
    path = f"/api/v1/forensics/cases/{payload['case_id']}/checksum"
    forensics_mod._rl_store.clear()
    ok1 = client.get(path, headers={"X-API-Key": "secret123"})
    ok2 = client.get(path, headers={"X-API-Key": "secret123"})
    over = client.get(path, headers={"X-API-Key": "secret123"})
    assert ok1.status_code == 200
    assert ok2.status_code == 200
    assert over.status_code == 429


def test_export_and_verify_signature(monkeypatch, client):
    # Enable signatures
    monkeypatch.setenv("CASES_SIGNING_SECRET", "topsecret")

    # Create case with API key enforced
    forensics_mod._API_KEY = "secret123"
    forensics_mod._RL_LIMIT = 0  # disable RL for this test
    forensics_mod._rl_store.clear()

    payload = {
        "case_id": "CASE-VERIFY-1",
        "title": "Verify Test",
        "description": "desc",
        "lead_investigator": "bob"
    }

    r = client.post(
        "/api/v1/forensics/cases/create",
        headers={"X-API-Key": "secret123"},
        json=payload,
    )
    assert r.status_code == 200

    # Export JSON (contains checksum and signature)
    r = client.get(
        f"/api/v1/forensics/cases/{payload['case_id']}/export",
        headers={"X-API-Key": "secret123"},
    )
    assert r.status_code == 200
    data = r.json()["export"]
    checksum = data.get("checksum_sha256")
    signature = data.get("signature_hmac_sha256")
    assert isinstance(checksum, str) and len(checksum) == 64
    assert isinstance(signature, str) and len(signature) == 64

    # Verify endpoint should confirm checksum and signature
    r = client.post(
        f"/api/v1/forensics/cases/{payload['case_id']}/verify",
        headers={"X-API-Key": "secret123"},
        json={
            "checksum_sha256": checksum,
            "signature_hmac_sha256": signature,
        },
    )
    assert r.status_code == 200
    res = r.json()
    assert res.get("match") is True
    assert res.get("signature_match") is True
