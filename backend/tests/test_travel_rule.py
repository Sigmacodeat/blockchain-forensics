"""
Tests für Travel Rule Service und API
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.travel_rule_service import TravelRuleService
from app.models.travel_rule import TravelRuleMessage, TravelRuleStatus


@pytest.fixture
def sample_ivms101_payload():
    return {
        "originator": {
            "name": "John Doe",
            "address": {"country": "US", "street": "123 Main St", "city": "New York"},
            "customer_id": "CUST123",
            "national_id": {"type": "SSN", "number": "123456789", "country": "US"},
            "country_of_residence": "US",
        },
        "beneficiary": {
            "name": "Jane Smith",
            "address": {"country": "US", "street": "456 Oak Ave", "city": "Los Angeles"},
            "customer_id": "CUST456",
            "national_id": {"type": "SSN", "number": "987654321", "country": "US"},
            "country_of_residence": "US",
        },
        "transaction": {"amount": 10000.50, "currency": "USD"},
    }


class TestTravelRuleService:
    """Tests für Travel Rule Service"""

    @pytest.fixture
    def service(self):
        return TravelRuleService()

    @pytest.fixture
    def sample_ivms101_payload(self):
        return {
            "originator": {
                "name": "John Doe",
                "address": {
                    "country": "US",
                    "street": "123 Main St",
                    "city": "New York"
                },
                "customer_id": "CUST123",
                "national_id": {
                    "type": "SSN",
                    "number": "123456789",
                    "country": "US"
                },
                "country_of_residence": "US"
            },
            "beneficiary": {
                "name": "Jane Smith",
                "address": {
                    "country": "US",
                    "street": "456 Oak Ave",
                    "city": "Los Angeles"
                },
                "customer_id": "CUST456",
                "national_id": {
                    "type": "SSN",
                    "number": "987654321",
                    "country": "US"
                },
                "country_of_residence": "US"
            },
            "transaction": {
                "amount": 10000.50,
                "currency": "USD"
            }
        }

    def test_prepare_message_success(self, service, sample_ivms101_payload):
        """Test erfolgreiche Nachrichten-Vorbereitung"""
        result = service.prepare_message(
            ivms101_payload=sample_ivms101_payload,
            originator_vasp_id="VASP001",
            beneficiary_vasp_id="VASP002"
        )

        assert result["success"] is True
        assert "prepared_payload" in result
        assert "message_id" in result["prepared_payload"]
        assert result["prepared_payload"]["originator_vasp_id"] == "VASP001"
        assert result["prepared_payload"]["beneficiary_vasp_id"] == "VASP002"
        assert result["prepared_payload"]["status"] == "prepared"

    def test_prepare_message_validation_errors(self, service):
        """Test Validierungsfehler bei Nachrichten-Vorbereitung"""
        invalid_payload = {
            "originator": {
                "name": "",  # Missing name
                "address": {}
            }
            # Missing beneficiary and transaction
        }

        result = service.prepare_message(
            ivms101_payload=invalid_payload,
            originator_vasp_id="VASP001",
            beneficiary_vasp_id="VASP002"
        )

        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Missing originator name" in result["errors"]
        assert "Missing beneficiary information" in result["errors"]

    def test_send_message_success(self, service, sample_ivms101_payload):
        """Test erfolgreiches Senden einer Nachricht"""
        message_id = "test-message-123"

        with patch('app.services.travel_rule_service.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            # Mock successful database operations
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.flush = MagicMock()

            result = service.send_message(
                message_id=message_id,
                ivms101_payload=sample_ivms101_payload
            )

            assert result["success"] is True
            assert result["message_id"] == message_id
            assert result["status"] == "sent"

            # Verify database operations were called
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    def test_send_message_duplicate_id(self, service, sample_ivms101_payload):
        """Test Fehler bei doppelter Message ID"""
        message_id = "duplicate-id"

        with patch('app.services.travel_rule_service.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            # Simulate IntegrityError
            from sqlalchemy.exc import IntegrityError
            mock_db.commit.side_effect = IntegrityError(None, None, None)

            result = service.send_message(
                message_id=message_id,
                ivms101_payload=sample_ivms101_payload
            )

            assert result["success"] is False
            assert "already exists" in result["error"]

    def test_get_message_status_found(self, service):
        """Test Abrufen einer gefundenen Nachricht"""
        message_id = "existing-message"

        with patch('app.services.travel_rule_service.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            mock_message = TravelRuleMessage(
                message_id=message_id,
                status=TravelRuleStatus.SENT,
                ivms101_payload={"test": "data"}
            )
            mock_db.query.return_value.filter.return_value.first.return_value = mock_message

            result = service.get_message_status(message_id)

            assert result is not None
            assert result["message_id"] == message_id
            assert result["status"] == "sent"

    def test_get_message_status_not_found(self, service):
        """Test Abrufen einer nicht gefundenen Nachricht"""
        message_id = "nonexistent-message"

        with patch('app.services.travel_rule_service.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None

            result = service.get_message_status(message_id)

            assert result is None

    def test_validate_ivms101_valid(self, service, sample_ivms101_payload):
        """Test IVMS101 Validierung mit gültiger Payload"""
        errors = service._validate_ivms101(sample_ivms101_payload)

        assert len(errors) == 0

    def test_validate_ivms101_invalid(self, service):
        """Test IVMS101 Validierung mit ungültiger Payload"""
        invalid_payload = {
            "originator": {
                "name": ""  # Missing required fields
            }
        }

        errors = service._validate_ivms101(invalid_payload)

        assert len(errors) > 0
        assert "Missing originator name" in errors
        assert "Missing beneficiary information" in errors

    def test_redact_ivms101(self, service, sample_ivms101_payload):
        """Test PII-Redaktion in IVMS101 Payload"""
        redacted = service._redact_ivms101(sample_ivms101_payload)

        # Check that PII is redacted
        assert redacted["originator"]["name"] == "REDACTED"
        assert redacted["beneficiary"]["name"] == "REDACTED"
        assert redacted["originator"]["address"]["country"] == "US"  # Non-PII preserved
        assert redacted["originator"]["national_id"]["country"] == "US"  # Non-PII preserved


class TestTravelRuleAPI:
    """Tests für Travel Rule API Endpunkte"""

    def test_prepare_message_endpoint_mock(self, sample_ivms101_payload):
        """Test POST /api/v1/travel-rule/prepare (mocked)"""
        with patch('app.api.v1.travel_rule.travel_rule_service') as mock_service:
            mock_service.prepare_message.return_value = {
                "success": True,
                "prepared_payload": {
                    "message_id": "test-123",
                    "status": "prepared"
                }
            }

            from fastapi.testclient import TestClient
            from app.main import app

            client = TestClient(app)

            response = client.post(
                "/api/v1/travel-rule/prepare",
                json={
                    "ivms101_payload": sample_ivms101_payload,
                    "originator_vasp_id": "VASP001",
                    "beneficiary_vasp_id": "VASP002"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message_id"] == "test-123"

    def test_validate_ivms101_endpoint_mock(self, sample_ivms101_payload):
        """Test GET /api/v1/travel-rule/validate-ivms101 (mocked)"""
        with patch('app.api.v1.travel_rule.travel_rule_service') as mock_service:
            mock_service._validate_ivms101.return_value = []

            from fastapi.testclient import TestClient
            from app.main import app

            client = TestClient(app)

            response = client.get(
                "/api/v1/travel-rule/validate-ivms101",
                params={"payload": str(sample_ivms101_payload)}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True


if __name__ == "__main__":
    pytest.main([__file__])
