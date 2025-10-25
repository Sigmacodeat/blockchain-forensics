"""
Tests für Graph Analytics Module
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.analytics.graph_analytics_service import GraphAnalyticsService
from app.analytics.pattern_detector import PatternDetector
from app.analytics.network_stats import NetworkStats


class TestGraphAnalyticsService:
    """Tests für GraphAnalyticsService"""
    
    @pytest.fixture
    def service(self):
        return GraphAnalyticsService()
    
    @pytest.mark.asyncio
    async def test_detect_communities_louvain(self, service):
        """Test Community Detection mit Louvain"""
        # Mock Neo4j driver
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = [
            {
                "communityId": 1,
                "address": "0x123",
                "taint": 0.5,
                "risk_level": "MEDIUM"
            },
            {
                "communityId": 1,
                "address": "0x456",
                "taint": 0.3,
                "risk_level": "LOW"
            },
            {
                "communityId": 2,
                "address": "0x789",
                "taint": 0.8,
                "risk_level": "HIGH"
            }
        ]
        mock_session.run.return_value = mock_result
        
        with patch.object(service.client.driver, 'session', return_value=mock_session):
            result = await service.detect_communities(
                algorithm="louvain",
                min_community_size=2
            )
            
            assert result["algorithm"] == "louvain"
            assert "communities" in result
            assert "statistics" in result
            assert len(result["communities"]) >= 1
    
    @pytest.mark.asyncio
    async def test_calculate_centrality_pagerank(self, service):
        """Test PageRank Centrality"""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = [
            {
                "address": "0xabc",
                "score": 0.15,
                "taint": 0.2,
                "labels": ["Exchange"]
            },
            {
                "address": "0xdef",
                "score": 0.10,
                "taint": 0.0,
                "labels": []
            }
        ]
        mock_session.run.return_value = mock_result
        
        with patch.object(service.client.driver, 'session', return_value=mock_session):
            result = await service.calculate_centrality(
                algorithm="pagerank",
                top_n=20
            )
            
            assert result["algorithm"] == "pagerank"
            assert "top_addresses" in result
            assert len(result["top_addresses"]) == 2
            assert result["top_addresses"][0]["score"] == 0.15
    
    @pytest.mark.asyncio
    async def test_get_network_statistics(self, service):
        """Test Network Statistics"""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_record = {
            "node_count": 100,
            "edge_count": 250,
            "active_nodes": 80
        }
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        
        with patch.object(service.client.driver, 'session', return_value=mock_session):
            result = await service.get_network_statistics()
            
            assert result["nodes"] == 100
            assert result["edges"] == 250
            assert result["active_nodes"] == 80
            assert "density" in result
            assert "avg_degree" in result


class TestPatternDetector:
    """Tests für PatternDetector"""
    
    @pytest.fixture
    def detector(self):
        return PatternDetector()
    
    @pytest.mark.asyncio
    async def test_detect_circles(self, detector):
        """Test Circle Detection"""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = [
            {
                "addresses": ["0xa", "0xb", "0xc", "0xa"],
                "values": [1.0, 0.9, 0.8],
                "total_value": 2.7,
                "circle_length": 3
            }
        ]
        mock_session.run.return_value = mock_result
        
        with patch.object(detector.client.driver, 'session', return_value=mock_session):
            result = await detector.detect_circles(
                min_circle_length=3,
                max_circle_length=10
            )
            
            assert result["pattern"] == "circles"
            assert "detected" in result
            assert len(result["detected"]) == 1
            assert result["detected"][0]["length"] == 3
            assert "risk_score" in result["detected"][0]
    
    def test_calculate_circle_risk(self, detector):
        """Test Circle Risk Calculation"""
        risk = detector._calculate_circle_risk(length=5, total_value=10.0)
        assert isinstance(risk, int)
        assert 0 <= risk <= 100
        
        # Longer circle = higher risk
        risk_short = detector._calculate_circle_risk(length=3, total_value=1.0)
        risk_long = detector._calculate_circle_risk(length=8, total_value=1.0)
        assert risk_long > risk_short
    
    @pytest.mark.asyncio
    async def test_detect_layering(self, detector):
        """Test Layering Detection"""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = [
            {
                "address": "0xsource",
                "depth": 1,
                "split_count": 5,
                "target_addresses": ["0x1", "0x2", "0x3", "0x4", "0x5"]
            },
            {
                "address": "0x1",
                "depth": 2,
                "split_count": 3,
                "target_addresses": ["0xa", "0xb", "0xc"]
            }
        ]
        mock_session.run.return_value = mock_result
        
        with patch.object(detector.client.driver, 'session', return_value=mock_session):
            result = await detector.detect_layering(
                source_address="0xsource",
                max_depth=5,
                min_split_count=3
            )
            
            assert result["pattern"] == "layering"
            assert result["source_address"] == "0xsource"
            assert len(result["layers"]) == 2
            assert "risk_score" in result["statistics"]
    
    def test_calculate_smurf_risk(self, detector):
        """Test Smurf Risk Calculation"""
        risk = detector._calculate_smurf_risk(tx_count=20, total_value=2.0)
        assert isinstance(risk, int)
        assert 0 <= risk <= 100
        
        # More transactions = higher risk
        risk_low = detector._calculate_smurf_risk(tx_count=5, total_value=0.5)
        risk_high = detector._calculate_smurf_risk(tx_count=50, total_value=5.0)
        assert risk_high > risk_low
    
    def test_calculate_peel_risk(self, detector):
        """Test Peel Chain Risk Calculation"""
        risk = detector._calculate_peel_risk(chain_length=10, avg_peel_rate=0.1)
        assert isinstance(risk, int)
        assert 0 <= risk <= 100
        
        # Longer chain = higher risk
        risk_short = detector._calculate_peel_risk(chain_length=5, avg_peel_rate=0.1)
        risk_long = detector._calculate_peel_risk(chain_length=15, avg_peel_rate=0.1)
        assert risk_long > risk_short
    
    def test_calculate_rapid_risk(self, detector):
        """Test Rapid Movement Risk Calculation"""
        risk = detector._calculate_rapid_risk(hop_count=5, duration_seconds=60)
        assert isinstance(risk, int)
        assert 0 <= risk <= 100
        
        # Faster movement = higher risk
        risk_slow = detector._calculate_rapid_risk(hop_count=5, duration_seconds=300)
        risk_fast = detector._calculate_rapid_risk(hop_count=5, duration_seconds=30)
        assert risk_fast > risk_slow


class TestNetworkStats:
    """Tests für NetworkStats"""
    
    @pytest.fixture
    def stats(self):
        return NetworkStats()
    
    @pytest.mark.asyncio
    async def test_get_degree_distribution(self, stats):
        """Test Degree Distribution"""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = [
            {"degree": 1, "count": 50},
            {"degree": 2, "count": 30},
            {"degree": 3, "count": 20},
            {"degree": 5, "count": 10}
        ]
        mock_session.run.return_value = mock_result
        
        with patch.object(stats.client.driver, 'session', return_value=mock_session):
            result = await stats.get_degree_distribution(direction="both")
            
            assert result["direction"] == "both"
            assert "distribution" in result
            assert len(result["distribution"]) == 4
            assert result["statistics"]["total_nodes"] == 110
            assert "avg_degree" in result["statistics"]
    
    @pytest.mark.asyncio
    async def test_get_hub_analysis(self, stats):
        """Test Hub Analysis"""
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.__aiter__.return_value = [
            {
                "address": "0xhub1",
                "out_degree": 50,
                "in_degree": 30,
                "total_degree": 80,
                "labels": ["Exchange"],
                "risk_level": "MEDIUM"
            },
            {
                "address": "0xhub2",
                "out_degree": 20,
                "in_degree": 40,
                "total_degree": 60,
                "labels": [],
                "risk_level": "LOW"
            }
        ]
        mock_session.run.return_value = mock_result
        
        with patch.object(stats.client.driver, 'session', return_value=mock_session):
            result = await stats.get_hub_analysis(min_degree=10, top_n=20)
            
            assert "hubs" in result
            assert len(result["hubs"]) == 2
            assert result["hubs"][0]["total_degree"] == 80
            assert result["statistics"]["max_degree"] == 80
            assert "avg_degree" in result["statistics"]


# Integration Tests
class TestGraphAnalyticsIntegration:
    """Integration Tests für Graph Analytics"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_analysis_workflow(self):
        """Test kompletter Analyse-Workflow"""
        service = GraphAnalyticsService()
        detector = PatternDetector()
        network_stats = NetworkStats()
        
        # Mock all services
        with patch.object(service.client.driver, 'session') as mock_session:
            # 1. Get Network Stats
            mock_result = AsyncMock()
            mock_result.single.return_value = {
                "node_count": 50,
                "edge_count": 100,
                "active_nodes": 45
            }
            mock_session.return_value.run.return_value = mock_result
            
            stats = await service.get_network_statistics()
            assert stats["nodes"] == 50
            assert stats["edges"] == 100
        
        # Weitere Workflow-Schritte würden hier folgen
        # (Community Detection → Centrality → Pattern Detection)
