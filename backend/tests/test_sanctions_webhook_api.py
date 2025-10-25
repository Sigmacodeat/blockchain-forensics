import os
import sys
import pathlib
from fastapi.testclient import TestClient

# Ensure backend on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Set TEST mode to relax auth
os.environ.setdefault("TEST_MODE", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.main import app  # noqa: E402

client = TestClient(app)


def test_sanctions_webhook_addresses(monkeypatch):
    def _mock_bulk_upsert(items):
        # return inserted, existing
        return len(items), 0
    # Patch bulk_upsert in service import path
    from app.compliance.sanctions import service as svc
    monkeypatch.setattr(svc, "bulk_upsert", _mock_bulk_upsert, raising=False)

    payload = {
        "chain": "ethereum",
        "label": "sanctioned",
        "category": "OFAC",
        "addresses": [
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
        ],
    }
    r = client.post("/api/v1/sanctions/webhook/ofac", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["inserted"] == 2
    assert data["existing"] == 0
    assert data["total"] == 2


def test_sanctions_webhook_items(monkeypatch):
    def _mock_bulk_upsert(items):
        return len(items), 1
    from app.compliance.sanctions import service as svc
    monkeypatch.setattr(svc, "bulk_upsert", _mock_bulk_upsert, raising=False)

    payload = {
        "items": [
            {"chain": "ethereum", "address": "0x1111111111111111111111111111111111111111", "label": "sanctioned", "category": "EU"},
            {"chain": "bitcoin", "address": "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080", "label": "sanctioned", "category": "UN"},
        ]
    }
    r = client.post("/api/v1/sanctions/webhook/eu", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["inserted"] == 2
    assert data["existing"] == 1
    assert data["total"] == 2


def test_sanctions_webhook_invalid_json():
    # Send invalid JSON body
    r = client.post("/api/v1/sanctions/webhook/ofac", data="{not-json}", headers={"content-type": "application/json"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid JSON body"


def test_sanctions_webhook_payload_too_large(monkeypatch):
    # Set environment variable before creating client to ensure it's picked up
    monkeypatch.setenv("MAX_SANCTIONS_WEBHOOK_BODY_KB", "1")  # 1 KB
    
    # Create a new client after setting the env var
    from fastapi.testclient import TestClient
    from app.main import app
    test_client = TestClient(app)
    
    big_body = {"addresses": ["0x" + "a" * 2048]}  # ~2 KB
    r = test_client.post("/api/v1/sanctions/webhook/ofac", json=big_body)
    assert r.status_code == 413
    assert r.json()["detail"] == "Payload too large"
