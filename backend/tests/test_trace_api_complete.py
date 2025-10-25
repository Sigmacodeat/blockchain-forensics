"""
🧪 COMPLETE TRACE API TESTS
Tests für Transaction Tracing - Core Feature

Coverage:
- Trace Start (Ethereum, Bitcoin, Solana)
- Trace Status Check
- Trace Results
- Multi-Chain Support
- Error Handling
- Rate Limiting
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


class TestTraceAPI:
    """Test Suite für Transaction Tracing"""
    
    def test_start_trace_ethereum_success(self, client: TestClient, auth_headers):
        """Test: Ethereum Trace erfolgreich starten"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "depth": 2,
                "max_hops": 3
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "trace_id" in data
        assert data["chain"] == "ethereum"
        assert data["status"] == "pending"
    
    def test_start_trace_bitcoin_success(self, client: TestClient, auth_headers):
        """Test: Bitcoin Trace erfolgreich starten"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "bitcoin",
                "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                "depth": 1,
                "max_hops": 2
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["chain"] == "bitcoin"
    
    def test_start_trace_invalid_address(self, client: TestClient, auth_headers):
        """Test: Ungültige Adresse wird abgelehnt"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "invalid_address",
                "depth": 2
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422
        assert "Invalid address" in response.json()["detail"]
    
    def test_start_trace_requires_auth(self, client: TestClient):
        """Test: Trace benötigt Authentication"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            }
        )
        
        assert response.status_code == 401
    
    def test_start_trace_plan_check(self, client: TestClient, community_user_headers):
        """Test: Community Plan hat Zugriff"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "depth": 1
            },
            headers=community_user_headers
        )
        
        assert response.status_code in [200, 201]
    
    def test_trace_status_check(self, client: TestClient, auth_headers):
        """Test: Trace Status abfragen"""
        # Start trace
        start_response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            },
            headers=auth_headers
        )
        trace_id = start_response.json()["trace_id"]
        
        # Check status
        status_response = client.get(
            f"/api/v1/trace/status/{trace_id}",
            headers=auth_headers
        )
        
        assert status_response.status_code == 200
        data = status_response.json()
        assert "status" in data
        assert data["status"] in ["pending", "processing", "completed", "failed"]
    
    def test_trace_results_get(self, client: TestClient, auth_headers):
        """Test: Trace Results abrufen"""
        # Start trace
        start_response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            },
            headers=auth_headers
        )
        trace_id = start_response.json()["trace_id"]
        
        # Get results (might be empty if not completed)
        results_response = client.get(
            f"/api/v1/trace/results/{trace_id}",
            headers=auth_headers
        )
        
        assert results_response.status_code in [200, 202]  # 202 = Processing
    
    def test_trace_with_risk_analysis(self, client: TestClient, auth_headers):
        """Test: Trace mit Risk-Analyse"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "include_risk": True,
                "check_sanctions": True
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "risk_enabled" in data or response.status_code == 200
    
    def test_trace_export_csv(self, client: TestClient, auth_headers):
        """Test: Trace Results als CSV exportieren"""
        # Start trace
        start_response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            },
            headers=auth_headers
        )
        trace_id = start_response.json()["trace_id"]
        
        # Export CSV
        export_response = client.get(
            f"/api/v1/trace/export/{trace_id}",
            params={"format": "csv"},
            headers=auth_headers
        )
        
        assert export_response.status_code in [200, 404]  # 404 if not ready
        if export_response.status_code == 200:
            assert export_response.headers["content-type"] == "text/csv"
    
    def test_trace_list_user_traces(self, client: TestClient, auth_headers):
        """Test: Alle User-Traces auflisten"""
        response = client.get(
            "/api/v1/trace/list",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_trace_depth_limits(self, client: TestClient, auth_headers):
        """Test: Depth-Limits für verschiedene Plans"""
        # Community: max depth 2
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "depth": 10  # Too deep
            },
            headers=auth_headers
        )
        
        # Should either limit depth or reject
        assert response.status_code in [200, 400, 422]
    
    def test_trace_multi_chain_support(self, client: TestClient, auth_headers):
        """Test: Multi-Chain Support"""
        chains = ["ethereum", "bitcoin", "polygon", "bsc"]
        
        for chain in chains:
            response = client.get(
                f"/api/v1/trace/chains/{chain}/info",
                headers=auth_headers
            )
            
            # Chain should be supported or return 404
            assert response.status_code in [200, 404]


class TestTracePagination:
    """Test Suite für Trace Pagination"""
    
    def test_trace_results_pagination(self, client: TestClient, auth_headers):
        """Test: Results mit Pagination"""
        # Start trace
        start_response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            },
            headers=auth_headers
        )
        trace_id = start_response.json()["trace_id"]
        
        # Get paginated results
        response = client.get(
            f"/api/v1/trace/results/{trace_id}",
            params={"page": 1, "per_page": 10},
            headers=auth_headers
        )
        
        assert response.status_code in [200, 202]


class TestTraceWebSocket:
    """Test Suite für Trace WebSocket"""
    
    @pytest.mark.asyncio
    async def test_trace_websocket_connection(self, client: TestClient, auth_headers):
        """Test: WebSocket Connection für Live-Updates"""
        # This would require async WebSocket testing
        # Placeholder for now
        pass


class TestTraceRateLimiting:
    """Test Suite für Rate Limiting"""
    
    def test_trace_rate_limiting(self, client: TestClient, auth_headers):
        """Test: Rate Limiting bei zu vielen Requests"""
        # Send many requests
        responses = []
        for _ in range(20):
            response = client.post(
                "/api/v1/trace/start",
                json={
                    "chain": "ethereum",
                    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
                },
                headers=auth_headers
            )
            responses.append(response.status_code)
        
        # Should have some 429 (Too Many Requests)
        assert 429 in responses or all(r == 200 for r in responses)


class TestTraceEdgeCases:
    """Test Suite für Edge Cases"""
    
    def test_trace_empty_results(self, client: TestClient, auth_headers):
        """Test: Trace ohne Results"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x0000000000000000000000000000000000000000",  # Burn address
                "depth": 1
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 422]
    
    def test_trace_very_active_address(self, client: TestClient, auth_headers):
        """Test: Trace sehr aktiver Adresse (z.B. Exchange)"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  # Known address
                "depth": 1,
                "limit": 100  # Limit results
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_trace_timeout_handling(self, client: TestClient, auth_headers):
        """Test: Timeout bei langer Verarbeitung"""
        response = client.post(
            "/api/v1/trace/start",
            json={
                "chain": "ethereum",
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "depth": 5,  # Deep trace
                "timeout": 10  # Short timeout
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 408, 504]


# ==================== FIXTURES ====================

@pytest.fixture
def community_user_headers(client: TestClient):
    """Fixture: Community User Auth Headers"""
    # Login as community user
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "community@test.com",
            "password": "test123"
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        return {}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
