import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app as _app
    return TestClient(_app)


def test_vasp_risk_score_and_last(client: TestClient):
    # Use known VASP id from service (e.g., 'binance')
    vasp_id = "binance"

    # Score now
    r = client.post(f"/api/v1/compliance/vasp/{vasp_id}/risk/score")
    assert r.status_code == 200
    data = r.json()
    assert "record" in data
    rec = data["record"]
    assert rec["vasp_id"] == vasp_id
    assert 0.0 <= rec["risk_score"] <= 1.0

    # Get last
    r2 = client.get(f"/api/v1/compliance/vasp/{vasp_id}/risk/last")
    assert r2.status_code == 200
    data2 = r2.json()
    assert "record" in data2
    assert data2["record"]["vasp_id"] == vasp_id


def test_vasp_risk_history(client: TestClient):
    vasp_id = "coinbase"
    # Ensure at least one record exists
    client.post(f"/api/v1/compliance/vasp/{vasp_id}/risk/score")

    r = client.get(f"/api/v1/compliance/vasp/risk/history", params={"vasp_id": vasp_id, "limit": 10})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("items"), list)
    assert data.get("count") >= 1
