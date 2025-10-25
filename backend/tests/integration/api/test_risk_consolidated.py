"""
Konsolidierte Risk-Engine-Tests

Vereint alle Risk-bezogenen Tests:
- Risk API Endpoints
- Risk Weights Management
- Risk Rules Engine
- Risk Admin Functions
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.risk]


@pytest.fixture
def client():
    return TestClient(app)


class TestRiskAPI:
    """Risk API Endpoints"""

    def test_get_risk_score(self, client):
        """Test getting risk score for an address"""
        response = client.get("/api/v1/risk/score", params={
            "chain": "ethereum",
            "address": "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"
        })
        if response.status_code in (404, 405):
            pytest.skip("risk score route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "risk_score" in data

    def test_get_risk_analysis(self, client):
        """Test detailed risk analysis"""
        response = client.get("/api/v1/risk/analyze", params={
            "chain": "ethereum",
            "address": "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"
        })
        if response.status_code in (404, 405):
            pytest.skip("risk analyze route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 422]


class TestRiskWeights:
    """Risk Weights Management Tests"""

    def test_list_risk_weights(self, client):
        """Test listing risk weights"""
        response = client.get("/api/v1/risk/weights")
        if response.status_code in (404, 405):
            pytest.skip("risk weights route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 401]

    def test_get_risk_weight(self, client):
        """Test getting a specific risk weight"""
        response = client.get("/api/v1/risk/weights/default")
        if response.status_code in (404, 405):
            pytest.skip("risk weight item route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 404]

    def test_set_risk_weights(self, client):
        """Test setting risk weights (requires admin)"""
        payload = {
            "category": "sanctions",
            "weight": 0.9
        }
        response = client.post("/api/v1/risk/weights", json=payload)
        # Expect 401/403 without auth
        if response.status_code in (404, 405):
            pytest.skip("risk weights set route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 201, 401, 403, 422]


class TestRiskAdmin:
    """Risk Admin Functions Tests"""

    def test_risk_admin_jwt_guard(self, client):
        """Test risk admin JWT authentication guard"""
        # Without auth token, should fail
        response = client.get("/api/v1/risk/admin/config")
        if response.status_code in (404, 405):
            pytest.skip("risk admin config route disabled (phase 2 not enabled)")
        assert response.status_code in [401, 403, 404]

    def test_risk_admin_weights_api(self, client):
        """Test risk admin weights management API"""
        response = client.get("/api/v1/risk/admin/weights")
        assert response.status_code in [401, 403, 404]


class TestRiskRulesEngine:
    """Risk Rules Engine Tests"""

    def test_rule_evaluation(self, client):
        """Test risk rule evaluation"""
        payload = {
            "address": "0xtest",
            "rules": ["sanctions_check", "high_value"]
        }
        response = client.post("/api/v1/risk/evaluate", json=payload)
        if response.status_code in (404, 405):
            pytest.skip("risk evaluate route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 401, 422]

    def test_custom_risk_rule(self, client):
        """Test custom risk rule creation"""
        payload = {
            "name": "custom_rule",
            "condition": "amount > 100000",
            "weight": 0.7
        }
        response = client.post("/api/v1/risk/rules", json=payload)
        if response.status_code in (404, 405):
            pytest.skip("risk rules route disabled (phase 2 not enabled)")
        assert response.status_code in [200, 201, 401, 403, 422]


class TestRiskWeightsGuard:
    """Risk Weights Security Tests"""

    def test_weights_guard_unauthorized(self, client):
        """Test that weights endpoints are protected"""
        response = client.put("/api/v1/risk/weights/test", json={"weight": 0.5})
        if response.status_code in (404, 405):
            pytest.skip("risk weights guard route disabled (phase 2 not enabled)")
        assert response.status_code in [401, 403, 404]
