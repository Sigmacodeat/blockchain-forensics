import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Ensure test-friendly environment before importing app
os.environ.setdefault("DISABLE_LIFESPAN", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")
os.environ.setdefault("TEST_MODE", "1")

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


class TestPremiumAgentTools:
    """Tests for premium agent tools: advanced_trace, cluster_analysis, cross_chain_analysis."""

    def test_advanced_trace_tool(self, client: TestClient):
        """Test advanced trace tool with clustering and cross-chain."""
        with patch('app.ai_agents.tools.wallet_clusterer') as mock_clusterer, \
             patch('app.ai_agents.tools.neo4j_client') as mock_neo4j:

            # Mock clustering
            mock_clusterer.cluster_addresses = AsyncMock(return_value={"cluster1": ["addr1", "addr2"]})

            # Mock cross-chain
            mock_neo4j.get_cross_chain_summary = AsyncMock(return_value={"chains": {"ethereum": 50}, "degree": {"in": 20, "out": 30}})

            payload = {
                "messages": [
                    {"role": "user", "content": "Advanced trace for 0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"}
                ]
            }
            response = client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            body = response.json()

            # Verify response
            assert "reply" in body
            reply = body["reply"].strip()
            assert len(reply) > 0, "Reply should not be empty"

    def test_cluster_analysis_tool(self, client: TestClient):
        """Test cluster analysis tool."""
        with patch('app.ai_agents.tools.wallet_clusterer') as mock_clusterer:
            mock_clusterer.cluster_addresses = AsyncMock(return_value={
                "cluster1": ["addr1", "addr2", "addr3"],
                "cluster2": ["addr4"]
            })
            mock_clusterer.calculate_cluster_stats = AsyncMock(return_value={"total_balance": 1000, "avg_risk_score": 0.3})

            payload = {
                "messages": [
                    {"role": "user", "content": "Analyze clusters for addr1, addr2, addr3"}
                ]
            }
            response = client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            body = response.json()

            # Verify response
            assert "reply" in body
            reply = body["reply"].strip()
            assert len(reply) > 0, "Reply should not be empty"

    def test_cross_chain_analysis_tool(self, client: TestClient):
        """Test cross-chain analysis tool."""
        with patch('app.ai_agents.tools.neo4j_client') as mock_neo4j:
            mock_neo4j.get_cross_chain_summary = AsyncMock(return_value={
                "chains": {"ethereum": 50, "polygon": 30},
                "degree": {"in": 20, "out": 30},
                "bridges": {"outbound": 5, "inbound": 3}
            })
            mock_neo4j.get_address_neighbors = AsyncMock(return_value=["addr1", "addr2"])
            mock_neo4j.find_cross_chain_paths = AsyncMock(return_value=[{"path": ["addr1", "addr2"], "hops": 2}])

            payload = {
                "messages": [
                    {"role": "user", "content": "Cross-chain analysis for 0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"}
                ]
            }
            response = client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            body = response.json()

            # Verify response
            assert "reply" in body
            reply = body["reply"].strip()
            assert len(reply) > 0, "Reply should not be empty"
