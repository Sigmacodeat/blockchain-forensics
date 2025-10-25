"""
Tests für Threat Intelligence Feeds Service
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.integrations.feeds import ThreatIntelService, FeedSource


class TestThreatIntelService:
    """Tests für Threat Intelligence Service"""

    @pytest.fixture
    def service(self):
        return ThreatIntelService()

    def test_initialize_feeds(self, service):
        """Test Feed-Initialisierung"""
        assert len(service.feeds) > 0
        assert "ofac_sanctions" in service.feeds
        assert "tor_exit_nodes" in service.feeds

        # Check TOR exit nodes configuration
        tor_feed = service.feeds["tor_exit_nodes"]
        assert tor_feed.name == "TOR Exit Nodes"
        assert tor_feed.format == "text"
        assert tor_feed.enabled is True

    def test_get_address_intel_empty_cache(self, service):
        """Test Address-Intel ohne Cache"""
        intel = service.get_address_intel("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
        assert intel == []

    def test_get_risk_score_boost_no_intel(self, service):
        """Test Risk-Score-Boost ohne Intel"""
        boost = service.get_risk_score_boost("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
        assert boost == 0.0

    def test_process_feed_data_tor_exit_nodes(self, service):
        """Test TOR Exit Nodes Datenverarbeitung"""
        raw_data = """# TOR Exit Node List
192.168.1.1
10.0.0.1
"""

        processed = service._process_feed_data("tor_exit_nodes", raw_data)

        assert len(processed) == 2
        assert processed[0]["address"] == "192.168.1.1"
        assert processed[0]["type"] == "tor_exit_node"
        assert processed[0]["risk_level"] == "HIGH"

    def test_process_feed_data_sanctions(self, service):
        """Test Sanctions Datenverarbeitung"""
        raw_data = {
            "data": [
                {
                    "name": "Evil Corp",
                    "addresses": ["0x1234567890abcdef"],
                    "date": "2023-01-01"
                }
            ]
        }

        processed = service._process_feed_data("ofac_sanctions", raw_data)

        assert len(processed) == 1
        assert processed[0]["address"] == "0x1234567890abcdef"
        assert processed[0]["type"] == "sanctioned_entity"
        assert processed[0]["risk_level"] == "CRITICAL"
        assert processed[0]["description"] == "Sanctioned entity: Evil Corp"

    def test_get_feed_stats(self, service):
        """Test Feed-Statistiken"""
        stats = service.get_feed_stats()

        assert "total_feeds" in stats
        assert "enabled_feeds" in stats
        assert "total_entries" in stats
        assert "feeds" in stats

        assert stats["total_feeds"] == len(service.feeds)
        assert isinstance(stats["feeds"], dict)

    @pytest.mark.asyncio
    async def test_update_feed_tor_success(self, service):
        """Test erfolgreiche TOR Feed-Aktualisierung"""
        tor_feed = service.feeds["tor_exit_nodes"]

        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.text = MagicMock(return_value=asyncio.coroutine(lambda: "# TOR Exit Nodes\n192.168.1.1\n10.0.0.1")())

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            success = await service.update_feed("tor_exit_nodes")

            assert success is True
            assert tor_feed.last_updated is not None
            assert tor_feed.error_count == 0

            # Check cached data
            cache_entry = service.intel_cache.get("tor_exit_nodes")
            assert cache_entry is not None
            assert len(cache_entry["data"]) == 2

    @pytest.mark.asyncio
    async def test_update_feed_http_error(self, service):
        """Test Feed-Aktualisierung mit HTTP-Fehler"""
        tor_feed = service.feeds["tor_exit_nodes"]

        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = MagicMock()
            mock_response.status = 404
            mock_response.text = MagicMock(return_value=asyncio.coroutine(lambda: "Not Found")())

            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

            success = await service.update_feed("tor_exit_nodes")

            assert success is False
            assert tor_feed.error_count == 1

    @pytest.mark.asyncio
    async def test_update_all_feeds(self, service):
        """Test Update aller Feeds"""
        # Mock successful updates for all feeds
        with patch.object(service, 'update_feed', return_value=True) as mock_update:
            results = await service.update_all_feeds()

            assert results["updated_feeds"] == list(service.feeds.keys())
            assert results["failed_feeds"] == []
            assert results["total_processed"] == len(service.feeds)

    def test_feed_source_dataclass(self):
        """Test FeedSource Dataclass"""
        feed = FeedSource(
            name="Test Feed",
            url="https://example.com",
            update_interval_hours=24,
            format="json"
        )

        assert feed.name == "Test Feed"
        assert feed.enabled is True  # Default value
        assert feed.last_updated is None  # Default value
        assert feed.error_count == 0  # Default value


class TestRiskServiceIntegration:
    """Tests für Integration von Threat Intel in Risk Service"""

    @pytest.fixture
    def service(self):
        from app.services.risk_service import RiskService
        return RiskService()

    def test_threat_intel_in_factors(self, service):
        """Test dass Threat Intel in Factors enthalten ist"""
        weights = service.get_weights()
        assert "threat_intel" in weights
        assert weights["threat_intel"] == 0.8  # Default value

    def test_set_threat_intel_weight(self, service):
        """Test Setzen von Threat Intel Gewicht"""
        service.set_weights(threat_intel=0.5)
        weights = service.get_weights()
        assert weights["threat_intel"] == 0.5

        # Test bounds checking
        service.set_weights(threat_intel=1.5)  # Should be clamped to 1.0
        weights = service.get_weights()
        assert weights["threat_intel"] == 1.0

        service.set_weights(threat_intel=-0.5)  # Should be clamped to 0.0
        weights = service.get_weights()
        assert weights["threat_intel"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
