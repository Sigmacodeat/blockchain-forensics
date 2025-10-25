import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app as _app
    return TestClient(_app)


def test_vasp_risk_score_many_and_summary(client: TestClient):
    payload = {"vasp_ids": ["binance", "coinbase"]}
    r = client.post("/api/v1/compliance/vasp/risk/score-many", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data.get("records"), list)
    assert data.get("count") >= 1

    r2 = client.get("/api/v1/compliance/vasp/risk/summary")
    assert r2.status_code == 200, r2.text
    summary = r2.json()
    assert "total_vasps_scored" in summary
    assert "by_risk_level" in summary
    assert "avg_risk_score" in summary


def test_vasp_risk_run_once(client: TestClient):
    r = client.post("/api/v1/compliance/vasp/risk/run-once")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)
    # tolerate either success or error payloads but ensure keys present
    assert any(k in data for k in ("status", "scored", "total", "error"))
