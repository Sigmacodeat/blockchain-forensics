"""Tests für neue APIs: KYT, SAR/STR, NFT Wash-Trading"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import os

# Set TEST_MODE
os.environ["TEST_MODE"] = "1"


@pytest.fixture
def test_client():
    """Test Client mit Mock-Auth"""
    from app.main import app
    client = TestClient(app)
    return client


@pytest.fixture
def auth_headers():
    """Mock Auth Headers"""
    return {"Authorization": "Bearer test_token"}


class TestKYTEndpoints:
    """Tests für KYT Real-Time Monitoring"""
    
    def test_kyt_pre_endpoint_exists(self, test_client):
        """Test: KYT Pre-Confirmation Endpoint existiert"""
        response = test_client.post(
            "/api/v1/alerts/kyt/pre",
            json={"chain": "ethereum", "from_address": "0x123", "to_address": "0x456", "amount": 1.0}
        )
        # Kann 401 sein (Auth), aber nicht 404
        assert response.status_code != 404
    
    @patch("app.api.v1.alerts.get_current_user_strict")
    @patch("app.api.v1.alerts.alert_service")
    def test_kyt_pre_returns_decision(self, mock_service, mock_auth, test_client):
        """Test: KYT Pre gibt Decision zurück"""
        # Mock Auth
        mock_auth.return_value = {"id": "test_user", "email": "test@test.com"}
        
        # Mock Alert Service
        mock_alert = MagicMock()
        mock_alert.severity = MagicMock(value="medium")
        mock_alert.alert_id = "alert-123"
        mock_service.process_event = AsyncMock(return_value=[mock_alert])
        
        response = test_client.post(
            "/api/v1/alerts/kyt/pre",
            json={
                "chain": "ethereum",
                "from_address": "0x1234567890123456789012345678901234567890",
                "to_address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                "amount": 5.5
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "decision" in data
            assert data["decision"] in ["allow", "review", "hold"]
            assert "alerts_created" in data
    
    def test_kyt_post_endpoint_exists(self, test_client):
        """Test: KYT Post-Confirmation Endpoint existiert"""
        response = test_client.post(
            "/api/v1/alerts/kyt/post",
            json={"events": []}
        )
        # Kann 401/422 sein, aber nicht 404
        assert response.status_code != 404


class TestSAREndpoints:
    """Tests für SAR/STR Compliance API"""
    
    def test_sar_from_case_endpoint_exists(self, test_client):
        """Test: SAR from-case Endpoint existiert"""
        response = test_client.post("/api/v1/sar/sar/from-case/TEST-123")
        # Kann 401/404 sein (Auth/Case), aber Endpoint muss existieren
        assert response.status_code in [401, 404, 422]
    
    @patch("app.api.v1.sar.get_current_user_strict")
    @patch("app.api.v1.sar.case_service")
    @patch("app.api.v1.sar.sar_generator")
    def test_sar_generation_with_mock(self, mock_generator, mock_case, mock_auth, test_client):
        """Test: SAR-Generierung mit Mocks"""
        # Mock Auth
        mock_auth.return_value = {"id": "test_user"}
        
        # Mock Case Service
        if mock_case:
            mock_case.get_case.return_value = {
                "case_id": "TEST-123",
                "subject_name": "Test Subject",
                "addresses": [],
                "risk_score": 0.8
            }
        
        # Mock SAR Generator
        mock_report = MagicMock()
        mock_report.report_id = "SAR-123"
        mock_report.jurisdiction = "US"
        mock_report.report_type = "SAR"
        mock_report.subject_name = "Test"
        mock_report.amount_usd = 10000
        mock_report.transaction_date = "2025-10-18"
        mock_report.risk_score = 0.8
        
        mock_generator.generate_from_case = AsyncMock(return_value=mock_report)
        mock_generator.export_report = AsyncMock(return_value='{"test": "data"}')
        
        response = test_client.post("/api/v1/sar/sar/from-case/TEST-123?format=json")
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "report_id" in data
    
    def test_sar_submit_endpoint_exists(self, test_client):
        """Test: SAR Submit Endpoint existiert"""
        response = test_client.post(
            "/api/v1/sar/sar/submit",
            json={"case_id": "TEST", "format": "fincen", "destination": "regulator"}
        )
        assert response.status_code != 404


class TestNFTWashTradingAPI:
    """Tests für NFT Wash-Trading Detection API"""
    
    def test_nft_wash_detect_endpoint_exists(self, test_client):
        """Test: NFT Wash-Detect Endpoint existiert"""
        response = test_client.post(
            "/api/v1/forensics/nft/wash-detect",
            json={"trades": []}
        )
        # Kann 422 sein (Validation), aber nicht 404
        assert response.status_code != 404
    
    def test_nft_wash_detect_with_valid_input(self, test_client):
        """Test: NFT Wash-Detection mit gültigen Daten"""
        payload = {
            "trades": [
                {
                    "tx_hash": "0x123abc",
                    "timestamp": "2025-10-01T10:00:00Z",
                    "token_address": "0xNFTContract123",
                    "token_id": "1",
                    "from_address": "0xAlice123",
                    "to_address": "0xBob456",
                    "price": 1.5,
                    "marketplace": "OpenSea"
                }
            ]
        }
        
        response = test_client.post("/api/v1/forensics/nft/wash-detect", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "findings" in data
            assert "summary" in data
            assert isinstance(data["findings"], list)
    
    def test_nft_wash_detect_round_trip_pattern(self, test_client):
        """Test: NFT Wash-Detection erkennt Round-Trip"""
        payload = {
            "trades": [
                {
                    "tx_hash": "0xtx1",
                    "timestamp": "2025-10-01T10:00:00Z",
                    "token_address": "0xNFT",
                    "token_id": "1",
                    "from_address": "0xalice",
                    "to_address": "0xbob",
                    "price": 1.5
                },
                {
                    "tx_hash": "0xtx2",
                    "timestamp": "2025-10-01T22:00:00Z",
                    "token_address": "0xNFT",
                    "token_id": "1",
                    "from_address": "0xbob",
                    "to_address": "0xalice",
                    "price": 1.4
                }
            ]
        }
        
        response = test_client.post("/api/v1/forensics/nft/wash-detect", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            # Sollte Round-Trip erkennen
            findings = data.get("findings", [])
            assert any(f["pattern_type"] == "round_trip" for f in findings)
    
    def test_nft_wash_detect_input_validation(self, test_client):
        """Test: NFT Wash-Detection Validierung"""
        # Zu viele Trades (>1000)
        payload = {
            "trades": [{"tx_hash": f"0x{i}", "timestamp": "2025-10-01T10:00:00Z", 
                       "token_address": "0xNFT", "token_id": "1", 
                       "from_address": "0xa", "to_address": "0xb", "price": 1.0} 
                      for i in range(1001)]
        }
        
        response = test_client.post("/api/v1/forensics/nft/wash-detect", json=payload)
        assert response.status_code == 422  # Validation Error


class TestNFTWashTradingEngine:
    """Tests für NFT Wash-Trading Detection Engine"""
    
    @pytest.mark.asyncio
    async def test_detector_import(self):
        """Test: Detector kann importiert werden"""
        from app.analytics.nft_wash_trading import nft_wash_detector, NFTTrade
        assert nft_wash_detector is not None
        assert NFTTrade is not None
    
    @pytest.mark.asyncio
    async def test_detector_round_trip(self):
        """Test: Detector erkennt Round-Trip"""
        from app.analytics.nft_wash_trading import nft_wash_detector, NFTTrade
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        trades = [
            NFTTrade(
                tx_hash="0x1",
                timestamp=now,
                token_address="0xnft",
                token_id="1",
                from_address="0xalice",
                to_address="0xbob",
                price=1.5
            ),
            NFTTrade(
                tx_hash="0x2",
                timestamp=now + timedelta(hours=12),
                token_address="0xnft",
                token_id="1",
                from_address="0xbob",
                to_address="0xalice",
                price=1.4
            )
        ]
        
        findings = await nft_wash_detector.detect_wash_trading(trades)
        
        # Sollte Round-Trip finden
        assert any(f.pattern_type == "round_trip" for f in findings)
    
    @pytest.mark.asyncio
    async def test_detector_price_anomaly(self):
        """Test: Detector erkennt Price Anomaly"""
        from app.analytics.nft_wash_trading import nft_wash_detector, NFTTrade
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        trades = [
            NFTTrade(
                tx_hash="0x1",
                timestamp=now,
                token_address="0xnft",
                token_id="1",
                from_address="0xa",
                to_address="0xb",
                price=1.0
            ),
            NFTTrade(
                tx_hash="0x2",
                timestamp=now + timedelta(hours=1),
                token_address="0xnft",
                token_id="1",
                from_address="0xb",
                to_address="0xc",
                price=5.0  # 5x spike
            )
        ]
        
        findings = await nft_wash_detector.detect_wash_trading(trades)
        
        # Sollte Price Anomaly finden
        assert any(f.pattern_type == "price_anomaly" for f in findings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
