import os
from fastapi.testclient import TestClient

# Ensure lifespan is disabled and pytest flags are set
os.environ.setdefault("DISABLE_LIFESPAN", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.main import app  # noqa: E402

client = TestClient(app)


def test_webvitals_accepts_valid_payload():
    payload = {
        "name": "LCP",
        "id": "v1-abc",
        "value": 2500.5,
        "rating": "good",
        "navigationType": "navigate",
        "ts": 1700000000000,
    }
    r = client.post("/api/v1/metrics/webvitals", json=payload, headers={"user-agent": "pytest"})
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_webvitals_rejects_invalid_payload():
    # Missing required fields should yield 422 from Pydantic validation
    r = client.post("/api/v1/metrics/webvitals", json={})
    assert r.status_code in (400, 422)
