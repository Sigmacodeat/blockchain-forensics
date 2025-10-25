from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_monitor_rules_validate():
    payload = {
        "name": "HighRiskLargeTx",
        "scope": "tx",
        "severity": "high",
        "enabled": True,
        "expression": {
            "all": [
                {"tx.value_usd": {">=": 10000}},
                {"risk_score": {">=": 0.8}}
            ]
        }
    }
    res = client.post("/api/v1/monitor/rules/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data.get("valid") is True
    assert "dry_run" in data
