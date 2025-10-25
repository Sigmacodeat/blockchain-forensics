from fastapi.testclient import TestClient
from app.main import app

def test_intel_publish_and_policies():
    client = TestClient(app)

    # publish
    payload = {
        "type": "label",
        "payload": {"address": "0xabc", "label": "Scam"},
        "tlp": "GREEN",
        "publisher": "tester"
    }
    r = client.post("/api/v1/intel/publish", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == payload["type"]
    assert "id" in data

    # policies
    r = client.get("/api/v1/intel/policies")
    assert r.status_code == 200
    pols = r.json()
    assert isinstance(pols, list)
    assert len(pols) >= 1
