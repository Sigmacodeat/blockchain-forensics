from fastapi.testclient import TestClient
from app.main import app

def test_vasp_upsert_and_get():
    client = TestClient(app)

    payload = {
        "id": "vasp-test-1",
        "legal_name": "Test VASP GmbH",
        "jurisdiction": "DE"
    }
    r = client.post("/api/v1/vasp", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == payload["id"]
    assert data["legal_name"] == payload["legal_name"]

    r = client.get(f"/api/v1/vasp/{payload['id']}")
    assert r.status_code == 200
    got = r.json()
    assert got["id"] == payload["id"]
