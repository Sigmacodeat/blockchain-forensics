import os
import sys
import pathlib
from fastapi.testclient import TestClient
import types
import pytest

# Ensure backend on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Set TEST mode to relax auth
os.environ.setdefault("TEST_MODE", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.main import app  # noqa: E402
from app.api.v1 import travel_rule as tr_api  # noqa: E402

client = TestClient(app)


def test_prepare_ok(monkeypatch):
    def _mock_prepare(ivms101_payload, originator_vasp_id, beneficiary_vasp_id):
        return {
            "success": True,
            "prepared_payload": {
                "message_id": "msg-1",
                "status": "prepared",
                "ivms101_payload": ivms101_payload,
            },
            "errors": []
        }
    monkeypatch.setattr(tr_api.travel_rule_service, "prepare_message", _mock_prepare)

    payload = {
        "ivms101_payload": {
            "originator": {"name": "Alice", "address": {"country": "US", "street": "s"}},
            "beneficiary": {"name": "Bob", "address": {"country": "US", "city": "c"}},
            "transaction": {"amount": 10, "currency": "USD"},
        },
        "originator_vasp_id": "VASP_A",
        "beneficiary_vasp_id": "VASP_B",
    }
    r = client.post("/api/v1/travel-rule/prepare", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["prepared_payload"]["message_id"] == "msg-1"


def test_prepare_invalid(monkeypatch):
    def _mock_prepare(ivms101_payload, originator_vasp_id, beneficiary_vasp_id):
        return {"success": False, "prepared_payload": None, "errors": ["Missing originator"]}
    monkeypatch.setattr(tr_api.travel_rule_service, "prepare_message", _mock_prepare)

    payload = {
        "ivms101_payload": {},
        "originator_vasp_id": "VASP_A",
        "beneficiary_vasp_id": "VASP_B",
    }
    r = client.post("/api/v1/travel-rule/prepare", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert data["prepared_payload"] is None
    assert data["errors"]


def test_send_ok(monkeypatch):
    def _mock_send(message_id, ivms101_payload):
        return {"success": True, "message_id": message_id, "status": "sent"}
    monkeypatch.setattr(tr_api.travel_rule_service, "send_message", _mock_send)

    payload = {"message_id": "msg-1", "ivms101_payload": {"transaction": {"amount": 1, "currency": "USD"}}}
    r = client.post("/api/v1/travel-rule/send", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["status"] == "sent"


def test_get_status_not_found(monkeypatch):
    def _mock_get(message_id):
        return None
    monkeypatch.setattr(tr_api.travel_rule_service, "get_message_status", _mock_get)

    r = client.get("/api/v1/travel-rule/messages/does-not-exist")
    assert r.status_code == 404
    assert r.json()["detail"] == "message_not_found"


def test_get_status_ok(monkeypatch):
    def _mock_get(message_id):
        return {
            "message_id": message_id,
            "status": "sent",
            "created_at": None,
            "sent_at": "2025-01-01T00:00:00Z",
            "ivms101_payload": {"transaction": {"amount": 1, "currency": "USD"}},
        }
    monkeypatch.setattr(tr_api.travel_rule_service, "get_message_status", _mock_get)

    r = client.get("/api/v1/travel-rule/messages/msg-1")
    assert r.status_code == 200
    data = r.json()
    assert data["message_id"] == "msg-1"
    assert data["status"] == "sent"
