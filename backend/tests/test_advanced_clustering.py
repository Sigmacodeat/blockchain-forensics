"""
Tests for Advanced ML Clustering
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.ml.advanced_clustering import AdvancedClusteringEngine


@pytest.fixture
def clustering_engine():
    """Create clustering engine"""
    return AdvancedClusteringEngine()


@pytest.mark.asyncio
async def test_create_cluster(clustering_engine):
    """Test cluster creation"""
    addr = "0x1234567890123456789012345678901234567890"
    
    clustering_engine._create_cluster(addr)
    
    assert addr in clustering_engine.address_to_cluster
    cluster_id = clustering_engine.address_to_cluster[addr]
    assert addr in clustering_engine.clusters[cluster_id]


@pytest.mark.asyncio
async def test_merge_clusters(clustering_engine):
    """Test cluster merging"""
    addr1 = "0x1111111111111111111111111111111111111111"
    addr2 = "0x2222222222222222222222222222222222222222"
    
    clustering_engine._create_cluster(addr1)
    clustering_engine._create_cluster(addr2)
    
    cluster1 = clustering_engine.address_to_cluster[addr1]
    cluster2 = clustering_engine.address_to_cluster[addr2]
    
    assert cluster1 != cluster2
    
    # Merge
    clustering_engine._merge_clusters(cluster1, cluster2)
    
    # Both should now be in same cluster
    assert clustering_engine.address_to_cluster[addr1] == clustering_engine.address_to_cluster[addr2]


@pytest.mark.asyncio
async def test_cluster_wallet_workflow(clustering_engine):
    """Test full clustering workflow"""
    
    addr = "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
    
    # Mock Neo4j queries
    with patch('app.ml.advanced_clustering.neo4j_client.execute_read', new_callable=AsyncMock) as mock_neo4j:
        # Return empty results for all heuristics
        mock_neo4j.return_value = []
        
        result = await clustering_engine.cluster_wallet(addr, "ethereum")
        
        assert result["cluster_id"] is not None
        assert addr.lower() in result["addresses"]
        assert result["size"] >= 1
        assert "confidence" in result


@pytest.mark.asyncio
async def test_add_evidence(clustering_engine):
    """Test evidence tracking"""
    addr = "0x3333333333333333333333333333333333333333"
    
    clustering_engine._create_cluster(addr)
    clustering_engine._add_evidence(addr, 0.95)
    
    cluster_id = clustering_engine.address_to_cluster[addr]
    assert cluster_id in clustering_engine.cluster_confidence
    assert clustering_engine.cluster_confidence[cluster_id][addr] == 0.95


@pytest.mark.asyncio
async def test_confidence_calculation(clustering_engine):
    """Test cluster confidence calculation"""
    addr1 = "0x4444444444444444444444444444444444444444"
    addr2 = "0x5555555555555555555555555555555555555555"
    
    clustering_engine._create_cluster(addr1)
    clustering_engine._create_cluster(addr2, clustering_engine.address_to_cluster[addr1])
    
    clustering_engine._add_evidence(addr1, 0.9)
    clustering_engine._add_evidence(addr2, 0.85)
    
    cluster_id = clustering_engine.address_to_cluster[addr1]
    confidence = clustering_engine._calculate_cluster_confidence(cluster_id)
    
    assert "overall" in confidence
    assert 0 <= confidence["overall"] <= 1
    assert confidence["addresses_with_evidence"] == 2
