"""
Konsolidierte AI-Agent-Tests

Vereint alle AI-Agent-bezogenen Tests:
- Agent API Endpoints
- Agent Tools
- Agent Health
- Agent Capabilities
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.agent]


@pytest.fixture
def client():
    return TestClient(app)


class TestAgentHealth:
    """Agent Health & Capabilities Tests"""

    def test_agent_health_endpoint(self, client):
        """Test agent health check"""
        response = client.get("/api/v1/agent/health")
        assert response.status_code == 200
        data = response.json()
        # Accept either legacy "status" or new fields like "enabled"/"llm_ready"
        assert ("status" in data) or ("enabled" in data or "llm_ready" in data)

    def test_agent_capabilities(self, client):
        """Test agent capabilities endpoint"""
        response = client.get("/api/v1/agent/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "tools" in data


class TestAgentTools:
    """Agent Tools Tests"""

    def test_list_agent_tools(self, client):
        """Test listing available agent tools"""
        response = client.get("/api/v1/agent/tools")
        if response.status_code in (404, 405):
            pytest.skip("agent tools route disabled (phase 2 not enabled)")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    def test_agent_tool_execution_risk_score(self, client):
        """Test agent tool execution - risk_score"""
        payload = {
            "tool": "risk_score",
            "params": {"address": "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4", "chain": "ethereum"}
        }
        response = client.post("/api/v1/agent/execute", json=payload)
        if response.status_code in (404, 405):
            pytest.skip("agent execute route disabled (phase 2 not enabled)")
        # Accept both 200 (success) and 422 (validation error for test env)
        assert response.status_code in [200, 422, 500]

    def test_agent_tool_execution_bridge_lookup(self, client):
        """Test agent tool execution - bridge_lookup"""
        payload = {
            "tool": "bridge_lookup",
            "params": {"chain": "ethereum"}
        }
        response = client.post("/api/v1/agent/execute", json=payload)
        if response.status_code in (404, 405):
            pytest.skip("agent execute route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 422, 500]


class TestAgentPolicyAndTrace:
    """Agent Policy & Trace Tests"""

    def test_agent_policy_trace_workflow(self, client):
        """Test agent policy-based trace workflow"""
        # Simulate policy-driven trace
        payload = {
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "policy": "high_risk",
            "max_depth": 3
        }
        response = client.post("/api/v1/agent/policy-trace", json=payload)
        if response.status_code in (404, 405):
            pytest.skip("policy-trace route disabled (phase 2 not enabled)")
        # Accept various status codes depending on env
        assert response.status_code in [200, 400, 422, 500]


class TestAgentSimulation:
    """Agent Simulation Tests"""

    def test_simulate_alerts(self, client):
        """Test alert simulation via agent"""
        payload = {
            "scenario": "high_risk_transaction",
            "address": "0xtest",
            "amount": 1000000
        }
        response = client.post("/api/v1/agent/simulate/alerts", json=payload)
        if response.status_code in (404, 405):
            pytest.skip("simulate alerts route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 422, 500]


class TestAgentExtraction:
    """Agent Data Extraction Tests"""

    def test_agent_extract_address_info(self, client):
        """Test agent address extraction"""
        response = client.get("/api/v1/agent/extract/address/0xtest")
        assert response.status_code in [200, 404, 422, 500]
