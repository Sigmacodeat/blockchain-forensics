"""
Tests für Advanced Indirect Risk Detection
===========================================
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.analytics.advanced_indirect_risk import (
    advanced_indirect_risk_service,
    IndirectRiskResult,
    RiskPath,
    PathType,
    RiskCategory,
)


@pytest.mark.asyncio
async def test_advanced_indirect_risk_initialization():
    """Test Service-Initialisierung"""
    await advanced_indirect_risk_service.initialize()
    assert advanced_indirect_risk_service._initialized is True


@pytest.mark.asyncio
async def test_analyze_indirect_risk_success():
    """Test erfolgreiche Indirect Risk Analyse"""
    
    # Mock multi_chain_engine import
    mock_engine = Mock()
    mock_chain = Mock()
    mock_chain.chain_id = "ethereum"
    mock_engine.adapter_factory.get_supported_chains.return_value = [mock_chain]
    mock_engine.initialize_chains = AsyncMock()
    mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
        {
            "from": "0x123",
            "to": "0xabc",
            "value": "1000",
            "timestamp": "2025-10-18T10:00:00Z",
        }
    ])
    
    # Mock compliance_service
    mock_compliance = Mock()
    mock_result = Mock()
    mock_result.is_sanctioned = False
    mock_result.risk_score = 0.3
    mock_result.labels = []
    mock_compliance.screen.return_value = mock_result
    
    with patch('app.services.multi_chain.multi_chain_engine', mock_engine):
        with patch('app.services.compliance_service.service', mock_compliance):
            
            result = await advanced_indirect_risk_service.analyze_indirect_risk(
                target_address="0x123",
                max_hops=3,
                chains=["ethereum"],
                max_paths=1000,
            )
            
            assert isinstance(result, IndirectRiskResult)
            assert result.target_address == "0x123"
            assert result.max_hops == 3
            assert result.total_paths_found >= 0
            assert result.aggregate_risk_score >= 0.0
            assert result.aggregate_risk_score <= 1.0
            assert "ethereum" in result.chains_analyzed
            assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_path_agnostic_tracing():
    """Test Path-Agnostisches Tracing"""
    
    mock_engine = Mock()
    mock_chain = Mock()
    mock_chain.chain_id = "ethereum"
    mock_engine.adapter_factory.get_supported_chains.return_value = [mock_chain]
    mock_engine.initialize_chains = AsyncMock()
    
    # Mock Multi-Hop Counterparties
    # Target -> A -> B -> C (3 hops)
    async def mock_get_txs(chain_id, address, limit):
            if address == "0x123":  # Target
                return [{"from": "0x123", "to": "0xA", "value": "1000"}]
            elif address.lower() == "0xa":
                return [{"from": "0xA", "to": "0xB", "value": "900"}]
            elif address.lower() == "0xb":
                return [{"from": "0xB", "to": "0xC", "value": "800"}]
            return []
        
    mock_engine.get_address_transactions_paged = mock_get_txs
    
    # Mock compliance_service
    mock_compliance = Mock()
    mock_result = Mock()
    mock_result.is_sanctioned = False
    mock_result.risk_score = 0.1
    mock_result.labels = []
    mock_compliance.screen.return_value = mock_result
    
    with patch('app.services.multi_chain.multi_chain_engine', mock_engine):
        with patch('app.services.compliance_service.service', mock_compliance):
            result = await advanced_indirect_risk_service.analyze_indirect_risk(
                target_address="0x123",
                max_hops=3,
                chains=["ethereum"],
            )
            
            # Sollte Pfade gefunden haben
            assert result.total_paths_found > 0


@pytest.mark.asyncio
async def test_risk_decay_over_hops():
    """Test dass Risk über Hops decay't"""
    
    # Teste Decay-Formel
    base_risk = 1.0
    decay_factor = advanced_indirect_risk_service.RISK_DECAY_FACTOR
    
    # Hop 0: 1.0
    # Hop 1: 1.0 * 0.7 = 0.7
    # Hop 2: 1.0 * 0.7^2 = 0.49
    # Hop 3: 1.0 * 0.7^3 = 0.343
    
    for hops in range(4):
        expected_risk = base_risk * (decay_factor ** hops)
        
        # Simuliere Pfad mit X Hops
        path_data = {
            "from_address": "0x123",
            "to_address": "0xRISKY",
            "hop_count": hops,
            "intermediate_addresses": [],
            "chain": "ethereum",
            "counterparty_data": {},
        }
        
        with patch.object(
            advanced_indirect_risk_service,
            '_get_address_risk',
            return_value={
                "risk_score": base_risk,
                "categories": {RiskCategory.MIXER},
            }
        ):
            risk_path = await advanced_indirect_risk_service._analyze_path_risk(path_data)
            
            # Risk sollte decay'd sein
            # (mit Path Type Weight multipliziert, also nicht exakt gleich)
            assert risk_path.risk_score <= expected_risk


@pytest.mark.asyncio
async def test_path_type_detection():
    """Test Path Type Detection"""
    
    # Test verschiedene Path Types
    path_data_direct = {
        "from_address": "0x123",
        "to_address": "0xabc",
        "hop_count": 0,
        "intermediate_addresses": [],
        "chain": "ethereum",
        "counterparty_data": {},
    }
    
    path_type = advanced_indirect_risk_service._determine_path_type(path_data_direct)
    assert path_type == PathType.DIRECT
    
    # Mit Intermediate Addresses
    path_data_multi_hop = {
        "from_address": "0x123",
        "to_address": "0xabc",
        "hop_count": 2,
        "intermediate_addresses": ["0xmiddle"],
        "chain": "ethereum",
        "counterparty_data": {},
    }
    
    path_type2 = advanced_indirect_risk_service._determine_path_type(path_data_multi_hop)
    assert path_type2 in [PathType.UNKNOWN, PathType.MIXER, PathType.EXCHANGE, PathType.DEFI]


@pytest.mark.asyncio
async def test_risk_category_detection():
    """Test Risk Category Detection aus Labels"""
    
    test_cases = [
        (["darkweb", "market"], RiskCategory.DARKWEB),
        (["ransomware", "attack"], RiskCategory.RANSOMWARE),
        (["scam", "phishing"], RiskCategory.SCAM),
        (["mixer", "tornado"], RiskCategory.MIXER),
        (["stolen", "hack"], RiskCategory.STOLEN_FUNDS),
    ]
    
    for labels, expected_category in test_cases:
        mock_compliance = Mock()
        mock_result = Mock()
        mock_result.is_sanctioned = False
        mock_result.risk_score = 0.8
        mock_result.labels = labels
        mock_compliance.screen.return_value = mock_result
        
        with patch('app.services.compliance_service.service', mock_compliance):
            risk_data = await advanced_indirect_risk_service._get_address_risk("0xtest", "ethereum")
            
            assert expected_category in risk_data["categories"]


@pytest.mark.asyncio
async def test_cross_chain_risk_propagation():
    """Test Cross-Chain Risk Propagation"""
    
    mock_engine = Mock()

    
    with patch('app.services.multi_chain.multi_chain_engine', mock_engine):
        # Mock 2 Chains
        chains = [Mock(chain_id="ethereum"), Mock(chain_id="polygon")]
        mock_engine.adapter_factory.get_supported_chains.return_value = chains
        mock_engine.initialize_chains = AsyncMock()
        
        # Mock Transactions auf beiden Chains
        mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
            {"from": "0x123", "to": "0xabc", "value": "1000"}
        ])
        
        mock_compliance = Mock()

        
        with patch('app.services.compliance_service.service', mock_compliance):
            mock_result = Mock()
            mock_result.is_sanctioned = False
            mock_result.risk_score = 0.5
            mock_result.labels = []
            mock_compliance.screen.return_value = mock_result
            
            result = await advanced_indirect_risk_service.analyze_indirect_risk(
                target_address="0x123",
                max_hops=2,
                chains=["ethereum", "polygon"],
            )
            
            # Sollte beide Chains analysiert haben
            assert len(result.chains_analyzed) == 2
            assert "ethereum" in result.chains_analyzed
            assert "polygon" in result.chains_analyzed


@pytest.mark.asyncio
async def test_sanctioned_entity_detection():
    """Test dass sanktionierte Entities erkannt werden"""
    
    mock_engine = Mock()

    
    with patch('app.services.multi_chain.multi_chain_engine', mock_engine):
        mock_chain = Mock()
        mock_chain.chain_id = "ethereum"
        mock_engine.adapter_factory.get_supported_chains.return_value = [mock_chain]
        mock_engine.initialize_chains = AsyncMock()
        
        # Mock Pfad zu sanktionierter Entity
        mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
            {"from": "0x123", "to": "0xSANCTIONED", "value": "1000"}
        ])
        
        mock_compliance = Mock()

        
        with patch('app.services.compliance_service.service', mock_compliance):
            # Mock dass Ziel-Adresse sanktioniert ist
            def mock_screen(chain, address):
                result = Mock()
                if "SANCTIONED" in address:
                    result.is_sanctioned = True
                    result.risk_score = 1.0
                    result.labels = ["OFAC", "sanctioned"]
                else:
                    result.is_sanctioned = False
                    result.risk_score = 0.1
                    result.labels = []
                return result
            
            mock_compliance.screen.side_effect = mock_screen
            
            result = await advanced_indirect_risk_service.analyze_indirect_risk(
                target_address="0x123",
                max_hops=2,
                chains=["ethereum"],
            )
            
            # Sollte hohen Risk Score haben
            assert result.aggregate_risk_score > 0.5
            
            # Sollte SANCTIONS Category haben
            assert RiskCategory.SANCTIONS in result.risk_by_category or \
                   len(result.high_risk_paths) > 0


@pytest.mark.asyncio
async def test_max_paths_limit():
    """Test dass Max Paths Limit respektiert wird"""
    
    mock_engine = Mock()

    
    with patch('app.services.multi_chain.multi_chain_engine', mock_engine):
        mock_chain = Mock()
        mock_chain.chain_id = "ethereum"
        mock_engine.adapter_factory.get_supported_chains.return_value = [mock_chain]
        mock_engine.initialize_chains = AsyncMock()
        
        # Mock viele Counterparties
        mock_counterparties = [
            (f"0x{i:040x}", {"interactions": 1})
            for i in range(100)
        ]
        
        with patch.object(
            advanced_indirect_risk_service,
            '_get_counterparties',
            return_value=mock_counterparties
        ):
            mock_compliance = Mock()

            with patch('app.services.compliance_service.service', mock_compliance):
                mock_result = Mock()
                mock_result.is_sanctioned = False
                mock_result.risk_score = 0.1
                mock_result.labels = []
                mock_compliance.screen.return_value = mock_result
                
                result = await advanced_indirect_risk_service.analyze_indirect_risk(
                    target_address="0x123",
                    max_hops=2,
                    chains=["ethereum"],
                    max_paths=50,  # Limit auf 50
                )
                
                # Sollte nicht mehr als max_paths finden
                assert result.total_paths_found <= 50


@pytest.mark.asyncio
async def test_performance_with_deep_analysis():
    """Test Performance bei tiefer Analyse"""
    import time
    
    mock_engine = Mock()

    
    with patch('app.services.multi_chain.multi_chain_engine', mock_engine):
        mock_chain = Mock()
        mock_chain.chain_id = "ethereum"
        mock_engine.adapter_factory.get_supported_chains.return_value = [mock_chain]
        mock_engine.initialize_chains = AsyncMock()
        
        # Mock einige Counterparties
        mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
            {"from": "0x123", "to": f"0x{i:040x}", "value": "1000"}
            for i in range(10)
        ])
        
        mock_compliance = Mock()

        
        with patch('app.services.compliance_service.service', mock_compliance):
            mock_result = Mock()
            mock_result.is_sanctioned = False
            mock_result.risk_score = 0.1
            mock_result.labels = []
            mock_compliance.screen.return_value = mock_result
            
            start = time.time()
            result = await advanced_indirect_risk_service.analyze_indirect_risk(
                target_address="0x123",
                max_hops=3,
                chains=["ethereum"],
                max_paths=100,
            )
            elapsed = (time.time() - start) * 1000
            
            # Sollte in vernünftiger Zeit fertig sein (<10s)
            assert elapsed < 10000
            assert result.processing_time_ms < 10000


def test_risk_path_to_dict():
    """Test RiskPath Serialisierung"""
    
    path = RiskPath(
        from_address="0x123",
        to_address="0xabc",
        hop_count=2,
        path_type=PathType.MIXER,
        risk_categories={RiskCategory.MIXER, RiskCategory.DARKWEB},
        intermediate_addresses=["0xmiddle"],
        chains_involved=["ethereum"],
        risk_score=0.72,
        confidence=0.85,
    )
    
    result = path.to_dict()
    
    assert result["from_address"] == "0x123"
    assert result["to_address"] == "0xabc"
    assert result["hop_count"] == 2
    assert result["path_type"] == "mixer"
    assert "mixer" in result["risk_categories"]
    assert "darkweb" in result["risk_categories"]
    assert result["risk_score"] == 0.72
    assert result["confidence"] == 0.85


@pytest.mark.asyncio
async def test_min_risk_threshold():
    """Test dass MIN_RISK_THRESHOLD respektiert wird"""
    
    min_threshold = advanced_indirect_risk_service.MIN_RISK_THRESHOLD
    
    # Simuliere Low-Risk Pfad
    path_data = {
        "from_address": "0x123",
        "to_address": "0xLOWRISK",
        "hop_count": 1,
        "intermediate_addresses": [],
        "chain": "ethereum",
        "counterparty_data": {},
    }
    
    with patch.object(
        advanced_indirect_risk_service,
        '_get_address_risk',
        return_value={
            "risk_score": min_threshold - 0.01,  # Unter Threshold
            "categories": set(),
        }
    ):
        risk_path = await advanced_indirect_risk_service._analyze_path_risk(path_data)
        
        # Sollte None sein wegen niedrigem Risk
        assert risk_path is None or risk_path.risk_score < min_threshold
