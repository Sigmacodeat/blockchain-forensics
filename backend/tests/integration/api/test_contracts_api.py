from fastapi.testclient import TestClient
from app.main import app

def test_contracts_analyze_stub():
    client = TestClient(app)

    r = client.post("/api/v1/contracts/analyze", params={"address": "0xdeadbeef"})
    assert r.status_code == 200
    data = r.json()
    assert "score" in data
    assert "findings" in data
