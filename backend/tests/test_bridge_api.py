"""
Tests for Bridge API Endpoints
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestBridgeAPIEndpoints:
    """Test Bridge API Endpoints"""
    
    def test_get_supported_bridges(self):
        """GET /api/v1/bridge/supported-bridges should return bridge registry"""
        response = client.get("/api/v1/bridge/supported-bridges")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_bridges" in data
        assert "supported_chains" in data
        assert "bridges" in data
        
        assert data["total_bridges"] >= 10
        assert len(data["bridges"]) >= 10
        assert "ethereum" in data["supported_chains"]
    
    def test_get_supported_bridges_filter_by_chain(self):
        """GET /api/v1/bridge/supported-bridges?chain=ethereum"""
        response = client.get("/api/v1/bridge/supported-bridges?chain=ethereum")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned bridges should be for ethereum
        for bridge in data["bridges"]:
            assert bridge["chain"] == "ethereum"
    
    def test_bridge_health_check(self):
        """GET /api/v1/bridge/health should return health status"""
        response = client.get("/api/v1/bridge/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "registered_bridges" in data
        assert "supported_chains" in data
        assert data["registered_bridges"] >= 10
    
    def test_get_bridge_statistics(self):
        """GET /api/v1/bridge/statistics should return stats"""
        response = client.get("/api/v1/bridge/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_bridge_transactions" in data
        assert "unique_addresses" in data
        assert "top_bridges" in data
        assert "chain_distribution" in data
        
        # Should return valid structure even if no data
        assert isinstance(data["total_bridge_transactions"], int)
        assert isinstance(data["unique_addresses"], int)
        assert isinstance(data["top_bridges"], list)
        assert isinstance(data["chain_distribution"], dict)
    
    def test_get_address_bridge_history(self):
        """GET /api/v1/bridge/address/{address}/bridges"""
        test_address = "0x742d35cc6634c0532925a3b844bc454e4438f44e"
        response = client.get(f"/api/v1/bridge/address/{test_address}/bridges")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "address" in data
        assert "total_bridge_transactions" in data
        assert "bridges" in data
        assert data["address"] == test_address
    
    def test_get_address_bridge_history_with_limit(self):
        """GET /api/v1/bridge/address/{address}/bridges?limit=10"""
        test_address = "0x123abc"
        response = client.get(
            f"/api/v1/bridge/address/{test_address}/bridges",
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not exceed limit
        assert len(data["bridges"]) <= 10
    
    def test_find_cross_chain_link(self):
        """GET /api/v1/bridge/cross-chain-link"""
        params = {
            "source_address": "0x742d35cc6634c0532925a3b844bc454e4438f44e",
            "source_chain": "ethereum",
            "target_chain": "solana"
        }
        response = client.get("/api/v1/bridge/cross-chain-link", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "source_address" in data
        assert "source_chain" in data
        assert "target_chain" in data
        assert "found_links" in data
        assert "links" in data
        
        assert data["source_address"] == params["source_address"]
        assert data["source_chain"] == params["source_chain"]
        assert data["target_chain"] == params["target_chain"]
    
    def test_find_cross_chain_link_missing_params(self):
        """GET /api/v1/bridge/cross-chain-link without params should fail"""
        response = client.get("/api/v1/bridge/cross-chain-link")
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_bridge_flow(self):
        """POST /api/v1/bridge/flow-analysis"""
        payload = {
            "address": "0x742d35cc6634c0532925a3b844bc454e4438f44e",
            "max_hops": 3
        }
        response = client.post("/api/v1/bridge/flow-analysis", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "address" in data
        assert "total_flows" in data
        assert "max_hops_found" in data
        assert "flows" in data
        assert "analysis_timestamp" in data
    
    def test_analyze_bridge_flow_invalid_max_hops(self):
        """POST /api/v1/bridge/flow-analysis with invalid max_hops"""
        payload = {
            "address": "0x123abc",
            "max_hops": 20  # Exceeds limit of 10
        }
        response = client.post("/api/v1/bridge/flow-analysis", json=payload)
        
        assert response.status_code == 422  # Validation error


class TestBridgeAPIIntegration:
    """Integration tests for Bridge API"""
    
    def test_workflow_get_bridges_then_stats(self):
        """Complete workflow: get bridges → get stats"""
        # 1. Get supported bridges
        bridges_response = client.get("/api/v1/bridge/supported-bridges")
        assert bridges_response.status_code == 200
        bridges_data = bridges_response.json()
        
        # 2. Get statistics
        stats_response = client.get("/api/v1/bridge/statistics")
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        
        # Should have consistent data
        assert bridges_data["total_bridges"] >= 10
        assert isinstance(stats_data["total_bridge_transactions"], int)
    
    def test_workflow_address_lookup_and_flow_analysis(self):
        """Complete workflow: address history → flow analysis"""
        test_address = "0x742d35cc6634c0532925a3b844bc454e4438f44e"
        
        # 1. Get bridge history
        history_response = client.get(f"/api/v1/bridge/address/{test_address}/bridges")
        assert history_response.status_code == 200
        
        # 2. Analyze flow
        flow_payload = {"address": test_address, "max_hops": 5}
        flow_response = client.post("/api/v1/bridge/flow-analysis", json=flow_payload)
        assert flow_response.status_code == 200
        flow_data = flow_response.json()
        
        assert flow_data["address"] == test_address
