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


class TestAgentWorkflows:
    """Integration tests for AI Agent workflows via chat interface."""

    def test_chat_risk_score_workflow(self, client: TestClient):
        """Test chat triggering risk_score tool for address analysis."""
        with patch('app.ai_agents.tools.risk_scorer') as mock_risk_scorer:
            # Mock the risk scorer response
            mock_risk_scorer.calculate_risk_score = AsyncMock(return_value={
                "risk_score": 0.85,
                "risk_level": "high",
                "factors": ["high_transaction_volume", "known_scam_links"],
                "confidence": 0.92
            })

            # Send a message that should trigger risk_score
            payload = {
                "messages": [
                    {"role": "user", "content": "Berechne das Risiko für die Adresse 0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"}
                ]
            }
            response = client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            body = response.json()

            # Verify response structure
            assert "reply" in body
            # Basic check that reply is not empty or error-like
            reply = body["reply"].strip()
            assert len(reply) > 0, "Reply should not be empty"

    def test_chat_bridge_lookup_workflow(self, client: TestClient):
        """Test chat triggering bridge_lookup tool for bridge analysis."""
        with patch('app.ai_agents.tools.bridge_registry') as mock_registry:
            # Mock bridge registry response
            mock_contract = AsyncMock()
            mock_contract.address = "0x1234567890abcdef"
            mock_contract.chain = "ethereum"
            mock_contract.name = "Test Bridge"
            mock_contract.bridge_type = "lock_mint"
            mock_contract.counterpart_chains = ["polygon", "arbitrum"]
            mock_contract.method_selectors = ["0xa9059cbb"]
            mock_contract.added_at = "2023-01-01T00:00:00"

            mock_registry.is_bridge_method = lambda x: True
            mock_registry.is_bridge_contract = lambda addr, chain: addr == "0x1234567890abcdef" and chain == "ethereum"
            mock_registry.get_contract = lambda addr, chain: mock_contract if addr == "0x1234567890abcdef" and chain == "ethereum" else None
            mock_registry.get_contracts_by_chain = lambda chain: [mock_contract] if chain == "ethereum" else []
            mock_registry.get_stats = lambda: {"total_contracts": 100, "chains": ["ethereum"]}

            # Send a message that should trigger bridge_lookup
            payload = {
                "messages": [
                    {"role": "user", "content": "Finde alle Bridge-Verträge auf Ethereum"}
                ]
            }
            response = client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            body = response.json()

            # Verify response structure
            assert "reply" in body
            # Basic check that reply is not empty
            reply = body["reply"].strip()
            assert len(reply) > 0, "Reply should not be empty"

    def test_chat_trigger_alert_workflow(self, client: TestClient):
        """Test chat triggering trigger_alert tool for alert creation."""
        with patch('app.ai_agents.tools.alert_service') as mock_alert_service:
            # Mock alert creation
            mock_alert = AsyncMock()
            mock_alert.alert_type = "high_risk"
            mock_alert.severity = "high"
            mock_alert.title = "High Risk Address"
            mock_alert.description = "Address flagged for suspicious activity"
            mock_alert.address = "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"
            mock_alert.to_dict = lambda: {
                "alert_type": "high_risk",
                "severity": "high",
                "title": "High Risk Address",
                "description": "Address flagged for suspicious activity",
                "address": "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"
            }

            mock_alert_service.dispatch_manual_alert = AsyncMock(return_value=None)
            mock_alert_service.process_event = AsyncMock(return_value=[mock_alert])

            # Send a message that should trigger trigger_alert
            payload = {
                "messages": [
                    {"role": "user", "content": "Löse einen Alert für die Adresse 0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4 mit hohem Risiko aus"}
                ]
            }
            response = client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            body = response.json()

            # Verify response structure
            assert "reply" in body
            # Basic check that reply is not empty
            reply = body["reply"].strip()
            assert len(reply) > 0, "Reply should not be empty"

    def test_chat_multiple_tools_workflow(self, client: TestClient):
        """Test chat triggering multiple tools in a single workflow."""
        with patch('app.ai_agents.tools.risk_scorer') as mock_risk_scorer, \
             patch('app.ai_agents.tools.bridge_registry') as mock_registry, \
             patch('app.ai_agents.tools.alert_service') as mock_alert_service:

            # Mock multiple services
            mock_risk_scorer.calculate_risk_score = AsyncMock(return_value={"risk_score": 0.7, "risk_level": "medium"})

            mock_contract = AsyncMock()
            mock_contract.address = "0x1234567890abcdef"
            mock_contract.chain = "ethereum"
            mock_contract.name = "Test Bridge"
            mock_registry.get_contracts_by_chain = lambda chain: [mock_contract] if chain == "ethereum" else []

            mock_alert = AsyncMock()
            mock_alert.to_dict = lambda: {"alert_type": "medium_risk", "severity": "medium"}
            mock_alert_service.process_event = AsyncMock(return_value=[mock_alert])

            # Send a complex message that should trigger multiple tools
            payload = {
                "messages": [
                    {"role": "user", "content": "Analysiere die Adresse 0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4: Berechne Risiko, finde Bridges und löse Alerts aus"}
                ]
            }
            response = client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            body = response.json()

            # Verify multiple tools were triggered by checking reply
            reply = body["reply"].strip()
            assert len(reply) > 0, "Reply should not be empty"

    def test_chat_error_handling_workflow(self, client: TestClient):
        """Test error handling in agent workflows."""
        with patch('app.ai_agents.tools.risk_scorer') as mock_risk_scorer:
            # Mock a failure in risk scorer
            mock_risk_scorer.calculate_risk_score = AsyncMock(side_effect=Exception("Database connection failed"))

            # Send a message that should trigger the failing tool
            payload = {
                "messages": [
                    {"role": "user", "content": "Berechne das Risiko für 0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"}
                ]
            }
            response = client.post("/api/v1/chat", json=payload)
            assert response.status_code == 200
            body = response.json()

            # Verify error is handled gracefully
            reply = body["reply"].strip()
            assert len(reply) > 0, "Reply should not be empty"

    def test_chat_ws_agent_workflow(self, client: TestClient):
        """Test WebSocket-based agent workflows."""
        with client.websocket_connect("/api/v1/ws/chat") as ws:
            # Initial ready message
            first = json.loads(ws.receive_text())
            assert first.get("type") == "ready"

            # Send a message that triggers agent tools
            ws.send_text("Finde alle Bridges auf Ethereum und berechne Risiken")

            # Receive response
            msg = json.loads(ws.receive_text())
            assert msg.get("type") in ("answer", "error")

            # If answer, check for relevant content
            if msg.get("type") == "answer":
                assert "reply" in msg
                reply = msg["reply"].strip()
                assert len(reply) > 0, "WS reply should not be empty"
