"""
Tests für Universal Screening Service
======================================
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.universal_screening import (
    universal_screening_service,
    UniversalScreeningResult,
    ChainScreeningResult,
    RiskLevel,
    AttributionSource,
    AttributionEvidence,
)


@pytest.mark.asyncio
async def test_universal_screening_initialization():
    """Test Service-Initialisierung"""
    await universal_screening_service.initialize()
    assert universal_screening_service._initialized is True
    assert len(universal_screening_service.supported_chains) > 0


@pytest.mark.asyncio
async def test_screen_address_universal_success():
    """Test erfolgreiches Universal Screening"""
    
    # Mock Multi-Chain Engine
    with patch('app.services.universal_screening.multi_chain_engine') as mock_engine:
        # Mock Chain Info
        mock_chain = Mock()
        mock_chain.chain_id = "ethereum"
        mock_engine.adapter_factory.get_supported_chains.return_value = [mock_chain]
        
        # Mock Compliance Service
        with patch('app.services.universal_screening.compliance_service') as mock_compliance:
            mock_result = Mock()
            mock_result.is_sanctioned = False
            mock_result.risk_score = 0.3
            mock_result.labels = ["exchange"]
            mock_compliance.screen.return_value = mock_result
            
            # Mock Exposure Service
            with patch('app.services.universal_screening.exposure_service') as mock_exposure:
                mock_exposure_result = Mock()
                mock_exposure_result.to_dict.return_value = {
                    "direct_exposure": {},
                    "indirect_exposure": {},
                    "total_exposure_score": 0.0,
                }
                mock_exposure.calculate = AsyncMock(return_value=mock_exposure_result)
                
                # Mock Transaction Data
                mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
                    {
                        "from": "0xabc",
                        "to": "0xdef",
                        "value": "1000000000000000000",
                        "timestamp": "2025-10-18T10:00:00Z",
                    }
                ])
                
                # Test Screening
                result = await universal_screening_service.screen_address_universal(
                    address="0x123",
                    chains=["ethereum"],
                    max_concurrent=10,
                )
                
                # Assertions
                assert isinstance(result, UniversalScreeningResult)
                assert result.address == "0x123"
                assert result.total_chains_checked == 1
                assert result.aggregate_risk_score >= 0.0
                assert result.aggregate_risk_score <= 1.0
                assert not result.is_sanctioned_any_chain
                assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_screen_sanctioned_address():
    """Test Screening von sanktionierter Adresse"""
    
    with patch('app.services.universal_screening.multi_chain_engine') as mock_engine:
        mock_chain = Mock()
        mock_chain.chain_id = "ethereum"
        mock_engine.adapter_factory.get_supported_chains.return_value = [mock_chain]
        
        with patch('app.services.universal_screening.compliance_service') as mock_compliance:
            mock_result = Mock()
            mock_result.is_sanctioned = True
            mock_result.risk_score = 1.0
            mock_result.labels = ["OFAC", "sanctioned"]
            mock_result.sanctions_list = "OFAC"
            mock_compliance.screen.return_value = mock_result
            
            with patch('app.services.universal_screening.exposure_service') as mock_exposure:
                mock_exposure_result = Mock()
                mock_exposure_result.to_dict.return_value = {
                    "direct_exposure": {"sanctions": 1.0},
                    "indirect_exposure": {},
                    "total_exposure_score": 1.0,
                }
                mock_exposure.calculate = AsyncMock(return_value=mock_exposure_result)
                
                mock_engine.get_address_transactions_paged = AsyncMock(return_value=[])
                
                result = await universal_screening_service.screen_address_universal(
                    address="0xSANCTIONED",
                    chains=["ethereum"],
                )
                
                assert result.is_sanctioned_any_chain is True
                assert result.aggregate_risk_score == 1.0
                assert result.aggregate_risk_level == RiskLevel.CRITICAL


@pytest.mark.asyncio
async def test_attribution_evidence_collection():
    """Test Glass Box Attribution Evidence"""
    
    with patch('app.services.universal_screening.multi_chain_engine') as mock_engine:
        mock_chain = Mock()
        mock_chain.chain_id = "ethereum"
        mock_engine.adapter_factory.get_supported_chains.return_value = [mock_chain]
        
        with patch('app.services.universal_screening.compliance_service') as mock_compliance:
            mock_result = Mock()
            mock_result.is_sanctioned = False
            mock_result.risk_score = 0.7
            mock_result.labels = ["mixer", "high_volume"]
            mock_compliance.screen.return_value = mock_result
            
            with patch('app.services.universal_screening.exposure_service') as mock_exposure:
                mock_exposure_result = Mock()
                mock_exposure_result.to_dict.return_value = {
                    "direct_exposure": {"mixer": 0.7},
                    "indirect_exposure": {},
                }
                mock_exposure.calculate = AsyncMock(return_value=mock_exposure_result)
                
                mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
                    {"from": "0xabc", "to": "0xdef", "value": "1000", "timestamp": "2025-10-18T10:00:00Z"}
                    for _ in range(100)
                ])
                
                result = await universal_screening_service.screen_address_universal(
                    address="0xMIXER",
                    chains=["ethereum"],
                )
                
                # Check Attribution Evidence
                chain_result = result.chain_results["ethereum"]
                assert len(chain_result.attribution_evidence) > 0
                
                # Check for different evidence sources
                sources = {e.source for e in chain_result.attribution_evidence}
                assert AttributionSource.BEHAVIORAL_ANALYSIS in sources or \
                       AttributionSource.EXCHANGE_LABEL in sources


@pytest.mark.asyncio
async def test_risk_level_calculation():
    """Test Risk Level Berechnung"""
    
    # Test alle Risk Levels
    test_cases = [
        (0.95, RiskLevel.CRITICAL),
        (0.85, RiskLevel.HIGH),
        (0.50, RiskLevel.MEDIUM),
        (0.15, RiskLevel.LOW),
        (0.05, RiskLevel.MINIMAL),
    ]
    
    for risk_score, expected_level in test_cases:
        level = universal_screening_service._get_risk_level(risk_score)
        assert level == expected_level


@pytest.mark.asyncio
async def test_cross_chain_activity_detection():
    """Test Cross-Chain Activity Detection"""
    
    with patch('app.services.universal_screening.multi_chain_engine') as mock_engine:
        # Mock 2 Chains
        chains = [Mock(chain_id="ethereum"), Mock(chain_id="polygon")]
        mock_engine.adapter_factory.get_supported_chains.return_value = chains
        
        with patch('app.services.universal_screening.compliance_service') as mock_compliance:
            mock_result = Mock()
            mock_result.is_sanctioned = False
            mock_result.risk_score = 0.3
            mock_result.labels = []
            mock_compliance.screen.return_value = mock_result
            
            with patch('app.services.universal_screening.exposure_service') as mock_exposure:
                mock_exposure_result = Mock()
                mock_exposure_result.to_dict.return_value = {
                    "direct_exposure": {},
                    "indirect_exposure": {},
                }
                mock_exposure.calculate = AsyncMock(return_value=mock_exposure_result)
                
                mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
                    {"from": "0xabc", "to": "0xdef", "value": "1000", "timestamp": "2025-10-18T10:00:00Z"}
                ])
                
                result = await universal_screening_service.screen_address_universal(
                    address="0xCROSSCHAIN",
                    chains=["ethereum", "polygon"],
                )
                
                # Should detect cross-chain activity if found on multiple chains
                assert len(result.screened_chains) == 2


@pytest.mark.asyncio
async def test_max_addresses_limit():
    """Test dass MAX_ADDRESSES_PER_ENTITY respektiert wird"""
    
    # Dieser Test ist für Custom Entities, aber wir testen das Limit-Konzept
    max_concurrent = 50
    
    with patch('app.services.universal_screening.multi_chain_engine') as mock_engine:
        mock_engine.adapter_factory.get_supported_chains.return_value = [
            Mock(chain_id=f"chain_{i}") for i in range(100)
        ]
        
        # Screening sollte max_concurrent respektieren
        result = await universal_screening_service.screen_address_universal(
            address="0xTEST",
            chains=None,  # alle Chains
            max_concurrent=max_concurrent,
        )
        
        # Service sollte funktionieren auch mit vielen Chains
        assert result.total_chains_checked > 0


@pytest.mark.asyncio
async def test_error_handling_for_failed_chains():
    """Test dass fehlgeschlagene Chain-Screenings nicht alles blockieren"""
    
    with patch('app.services.universal_screening.multi_chain_engine') as mock_engine:
        chains = [Mock(chain_id="ethereum"), Mock(chain_id="failing_chain")]
        mock_engine.adapter_factory.get_supported_chains.return_value = chains
        
        # Mock dass eine Chain fehlschlägt
        async def mock_screen_chain(address, chain_id):
            if chain_id == "failing_chain":
                raise Exception("Chain failed")
            # Erfolgreicher Mock für ethereum
            return universal_screening_service._create_minimal_result(address, chain_id)
        
        with patch.object(
            universal_screening_service,
            '_screen_chain',
            side_effect=mock_screen_chain
        ):
            result = await universal_screening_service.screen_address_universal(
                address="0xTEST",
                chains=["ethereum", "failing_chain"],
            )
            
            # Sollte mindestens die erfolgreiche Chain enthalten
            # Fehlgeschlagene Chains werden gefiltert
            assert result.total_chains_checked == 2


def test_attribution_evidence_to_dict():
    """Test AttributionEvidence Serialisierung"""
    
    evidence = AttributionEvidence(
        source=AttributionSource.SANCTIONS_LIST,
        confidence=1.0,
        label="OFAC SDN",
        evidence_type="ofac_sdn_list",
        timestamp=datetime.utcnow(),
        metadata={"list": "OFAC"},
        verification_method="direct_match",
    )
    
    result = evidence.to_dict()
    
    assert result["source"] == "sanctions_list"
    assert result["confidence"] == 1.0
    assert result["label"] == "OFAC SDN"
    assert "timestamp" in result
    assert result["metadata"]["list"] == "OFAC"


@pytest.mark.asyncio
async def test_performance_benchmark():
    """Test dass Performance-Anforderungen erfüllt werden"""
    import time
    
    with patch('app.services.universal_screening.multi_chain_engine') as mock_engine:
        # Mock 10 Chains
        chains = [Mock(chain_id=f"chain_{i}") for i in range(10)]
        mock_engine.adapter_factory.get_supported_chains.return_value = chains
        
        with patch('app.services.universal_screening.compliance_service') as mock_compliance:
            mock_result = Mock()
            mock_result.is_sanctioned = False
            mock_result.risk_score = 0.3
            mock_result.labels = []
            mock_compliance.screen.return_value = mock_result
            
            with patch('app.services.universal_screening.exposure_service') as mock_exposure:
                mock_exposure_result = Mock()
                mock_exposure_result.to_dict.return_value = {"direct_exposure": {}}
                mock_exposure.calculate = AsyncMock(return_value=mock_exposure_result)
                
                mock_engine.get_address_transactions_paged = AsyncMock(return_value=[])
                
                start = time.time()
                result = await universal_screening_service.screen_address_universal(
                    address="0xPERF",
                    chains=[f"chain_{i}" for i in range(10)],
                    max_concurrent=10,
                )
                elapsed = (time.time() - start) * 1000
                
                # Performance Check: Sollte < 5000ms für 10 Chains sein
                assert elapsed < 5000
                assert result.processing_time_ms < 5000
