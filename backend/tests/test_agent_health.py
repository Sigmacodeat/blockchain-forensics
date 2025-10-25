"""
Tests für AI Agent Health/Heartbeat Endpunkte
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_agent_health_endpoint():
    resp = client.get("/api/v1/agent/health")
    assert resp.status_code in (200, 503)
    data = resp.json()
    # Bei deaktivierten Agents liefern wir trotzdem Basisstruktur
    assert "enabled" in data
    # Wenn enabled, sollten zusätzliche Felder vorhanden sein
    if data.get("enabled"):
        assert "model" in data
        assert "tools_available" in data


def test_agent_heartbeat_endpoint():
    resp = client.post("/api/v1/agent/heartbeat")
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        assert resp.json().get("ok") is True
