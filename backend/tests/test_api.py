"""
API Tests für Blockchain Forensics Platform
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_trace_endpoint_validation():
    """Test trace endpoint validates address format"""
    response = client.post(
        "/api/v1/trace/start",
        json={
            "source_address": "invalid_address",
            "direction": "forward",
        }
    )
    assert response.status_code == 400


def test_ai_agent_capabilities():
    """Test AI agent capabilities endpoint"""
    response = client.get("/api/v1/agent/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "tools" in data


def test_enrichment_sanctions_check():
    """Test sanctions check endpoint"""
    response = client.get(
        "/api/v1/enrich/sanctions-check",
        params={"address": "0x0000000000000000000000000000000000000000"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "address" in data
    assert "is_sanctioned" in data
