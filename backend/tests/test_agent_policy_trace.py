from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_agent_trace_policy_simulate_basic():
    payload = {
        "source_address": "0x0000000000000000000000000000000000000000",
        "max_depth": 2,
        "max_nodes": 50,
        "min_taint_threshold": 0.0,
        "enable_native": True,
        "enable_token": False,
        "enable_bridge": False,
        "enable_utxo": False,
        "native_decay": 1.0,
        "token_decay": 1.0,
        "bridge_decay": 0.9,
        "utxo_decay": 1.0,
    }
    res = client.post("/api/v1/agent/trace/policy-simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data and "result" in data
    assert data["summary"].get("completed") in (True, False)
    # ensure toggles echoed in result request portion if present
    result = data["result"]
    assert result.get("source_address").lower() == payload["source_address"].lower()


def test_agent_trace_policy_simulate_with_token_bridge_utxo():
    payload = {
        "source_address": "0x1111111111111111111111111111111111111111",
        "max_depth": 1,
        "max_nodes": 20,
        "min_taint_threshold": 0.0,
        "enable_native": True,
        "enable_token": True,
        "enable_bridge": True,
        "enable_utxo": True,
        "native_decay": 0.9,
        "token_decay": 0.8,
        "bridge_decay": 0.7,
        "utxo_decay": 0.95,
    }
    res = client.post("/api/v1/agent/trace/policy-simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    # presence of edges/nodes counts, even if zero in test environment
    assert "nodes" in data["summary"] and "edges" in data["summary"]
