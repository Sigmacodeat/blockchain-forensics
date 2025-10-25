from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_agent_rules_list():
    res = client.get("/api/v1/agent/rules")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data or "rules" in data


def test_agent_rules_simulate():
    res = client.post("/api/v1/agent/rules/simulate", json={
        "address": "0x0000000000000000000000000000000000000000",
        "risk_score": 0.95,
        "labels": []
    })
    assert res.status_code == 200
    data = res.json()
    assert "triggered_count" in data


def test_agent_risk_score():
    res = client.get("/api/v1/agent/risk/score", params={"address": "0x0000000000000000000000000000000000000000"})
    assert res.status_code == 200
    data = res.json()
    assert "risk_score" in data


def test_agent_bridge_lookup():
    res = client.get("/api/v1/agent/bridge/lookup", params={"chain": "polygon"})
    assert res.status_code == 200
    data = res.json()
    assert "contracts" in data or "stats" in data


def test_agent_alerts_trigger():
    res = client.post("/api/v1/agent/alerts/trigger", json={
        "alert_type": "mixer",
        "address": "0x1111111111111111111111111111111111111111",
        "tx_hash": "0xabc",
        "labels": ["mixer"]
    })
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
