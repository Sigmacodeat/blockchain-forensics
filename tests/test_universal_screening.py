"""
Tests für Universal Screening Service
=====================================

Vollständige Test-Suite für Universal Wallet Screening über 90+ Chains.
"""

import pytest
import asyncio
from datetime import datetime
from app.services.universal_screening import (
    universal_screening_service,
    UniversalScreeningResult,
    ChainScreeningResult,
    RiskLevel,
)


class TestUniversalScreeningService:
    """Test-Suite für Universal Screening Service"""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test Service-Initialisierung"""
        await universal_screening_service.initialize()
        
        assert universal_screening_service._initialized is True
        assert len(universal_screening_service.supported_chains) > 0
        assert 'ethereum' in universal_screening_service.supported_chains
        assert 'bitcoin' in universal_screening_service.supported_chains
    
    @pytest.mark.asyncio
    async def test_screen_ethereum_address(self):
        """Test Ethereum address screening"""
        result = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=["ethereum"],
            max_concurrent=5,
        )
        
        # Basic Assertions
        assert result is not None
        assert isinstance(result, UniversalScreeningResult)
        assert result.address.lower() == "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
        assert result.total_chains_checked >= 1
        
        # Risk Score Validation
        assert 0 <= result.aggregate_risk_score <= 1
        assert result.aggregate_risk_level in [
            RiskLevel.CRITICAL,
            RiskLevel.HIGH,
            RiskLevel.MEDIUM,
            RiskLevel.LOW,
            RiskLevel.MINIMAL,
        ]
        
        # Timestamp Validation
        assert result.screening_timestamp is not None
        assert isinstance(result.screening_timestamp, datetime)
        
        # Performance Validation
        assert result.processing_time_ms > 0
        assert result.processing_time_ms < 30000  # Max 30 seconds
    
    @pytest.mark.asyncio
    async def test_screen_bitcoin_address(self):
        """Test Bitcoin address screening"""
        result = await universal_screening_service.screen_address_universal(
            address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            chains=["bitcoin"],
        )
        
        assert result is not None
        assert "bitcoin" in result.screened_chains or len(result.chain_results) > 0
        assert result.total_chains_checked >= 1
    
    @pytest.mark.asyncio
    async def test_screen_multiple_chains(self):
        """Test multi-chain screening"""
        chains_to_test = ["ethereum", "polygon", "arbitrum"]
        
        result = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=chains_to_test,
            max_concurrent=10,
        )
        
        assert result.total_chains_checked == len(chains_to_test)
        
        # Cross-chain activity detection
        if len(result.screened_chains) > 1:
            assert result.cross_chain_activity is True
        
        # Validate chain results structure
        for chain_id, chain_result in result.chain_results.items():
            assert isinstance(chain_result, ChainScreeningResult)
            assert chain_result.chain_id == chain_id
            assert 0 <= chain_result.risk_score <= 1
            assert isinstance(chain_result.labels, list)
            assert isinstance(chain_result.attribution_evidence, list)
    
    @pytest.mark.asyncio
    async def test_sanctioned_address_detection(self):
        """Test sanctioned address detection (Tornado Cash)"""
        # Tornado Cash Router (bekannte sanctionierte Adresse)
        tornado_cash_address = "0x8589427373D6D84E98730D7795D8f6f8731FDA16"
        
        result = await universal_screening_service.screen_address_universal(
            address=tornado_cash_address,
            chains=["ethereum"],
        )
        
        # Tornado Cash sollte hohen Risk Score haben
        assert result.aggregate_risk_score >= 0.7  # Mindestens HIGH
        
        # Optional: Check if sanctioned flag is set (depends on sanctions DB)
        # Note: This might fail if sanctions DB not populated
        if result.is_sanctioned_any_chain:
            assert result.aggregate_risk_score >= 0.9  # CRITICAL
    
    @pytest.mark.asyncio
    async def test_invalid_address_handling(self):
        """Test error handling for invalid address"""
        with pytest.raises(Exception):
            await universal_screening_service.screen_address_universal(
                address="invalid_address_123",
                chains=["ethereum"],
            )
    
    @pytest.mark.asyncio
    async def test_empty_address_handling(self):
        """Test error handling for empty address"""
        with pytest.raises(Exception):
            await universal_screening_service.screen_address_universal(
                address="",
                chains=["ethereum"],
            )
    
    @pytest.mark.asyncio
    async def test_processing_performance(self):
        """Test that processing is fast (<5s for 3 chains)"""
        import time
        
        start = time.time()
        
        result = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=["ethereum", "polygon", "arbitrum"],
            max_concurrent=10,
        )
        
        elapsed = time.time() - start
        
        # Performance Assertions
        assert elapsed < 5.0  # Max 5 seconds for 3 chains
        assert result.processing_time_ms < 5000
        
        # Ensure parallel processing worked
        # (Serial would be ~3x slower)
        if result.total_chains_checked >= 3:
            assert elapsed < 3.0  # Should be much faster than serial
    
    @pytest.mark.asyncio
    async def test_attribution_evidence_structure(self):
        """Test Glass Box Attribution Evidence"""
        result = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=["ethereum"],
        )
        
        # Check attribution evidence structure
        for chain_result in result.chain_results.values():
            for evidence in chain_result.attribution_evidence:
                # Validate confidence score
                assert 0 <= evidence.confidence <= 1
                
                # Validate required fields
                assert evidence.source is not None
                assert evidence.label is not None
                assert evidence.evidence_type is not None
                assert evidence.timestamp is not None
                
                # Validate metadata
                assert isinstance(evidence.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_aggregate_metrics(self):
        """Test aggregated metrics calculation"""
        result = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=["ethereum", "polygon"],
        )
        
        # Validate summary metrics
        assert result.total_transactions >= 0
        assert result.total_value_usd >= 0
        assert result.unique_counterparties >= 0
        assert isinstance(result.all_labels, set)
        
        # Highest risk chain should match aggregate
        if result.highest_risk_chain:
            highest_chain_result = result.chain_results[result.highest_risk_chain]
            assert highest_chain_result.risk_score > 0
    
    @pytest.mark.asyncio
    async def test_cross_chain_activity_detection(self):
        """Test cross-chain activity detection"""
        # Test with address active on multiple chains
        result = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=["ethereum", "polygon", "arbitrum", "optimism"],
        )
        
        # If found on multiple chains
        if len(result.screened_chains) > 1:
            assert result.cross_chain_activity is True
        else:
            assert result.cross_chain_activity is False
    
    @pytest.mark.asyncio
    async def test_risk_level_classification(self):
        """Test risk level classification thresholds"""
        # We can't control exact risk scores, but we can validate logic
        test_cases = [
            (0.95, RiskLevel.CRITICAL),
            (0.85, RiskLevel.HIGH),
            (0.55, RiskLevel.MEDIUM),
            (0.25, RiskLevel.LOW),
            (0.05, RiskLevel.MINIMAL),
        ]
        
        for score, expected_level in test_cases:
            level = universal_screening_service._get_risk_level(score)
            assert level == expected_level
    
    @pytest.mark.asyncio
    async def test_chain_results_to_dict(self):
        """Test serialization to dict"""
        result = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=["ethereum"],
        )
        
        # Test to_dict() method
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "address" in result_dict
        assert "screened_chains" in result_dict
        assert "aggregate_risk_score" in result_dict
        assert "chain_results" in result_dict
        assert "summary" in result_dict
        
        # Validate nested structure
        summary = result_dict["summary"]
        assert "total_transactions" in summary
        assert "total_value_usd" in summary
        assert "all_labels" in summary
    
    @pytest.mark.asyncio
    async def test_max_concurrent_limiting(self):
        """Test concurrent request limiting"""
        # Test with low concurrency
        result_low = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=["ethereum", "polygon", "arbitrum"],
            max_concurrent=1,  # Sequential
        )
        
        # Test with high concurrency
        result_high = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=["ethereum", "polygon", "arbitrum"],
            max_concurrent=10,  # Parallel
        )
        
        # Both should succeed
        assert result_low is not None
        assert result_high is not None
        
        # High concurrency should be faster (usually)
        # Note: Can't guarantee due to network variance
        # assert result_high.processing_time_ms <= result_low.processing_time_ms * 2
    
    @pytest.mark.asyncio
    async def test_solana_address_screening(self):
        """Test Solana address screening"""
        # Solana address format (Base58)
        solana_address = "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R"
        
        result = await universal_screening_service.screen_address_universal(
            address=solana_address,
            chains=["solana"],
        )
        
        assert result is not None
        assert result.total_chains_checked >= 1
    
    @pytest.mark.asyncio
    async def test_screen_all_chains(self):
        """Test screening across ALL supported chains"""
        result = await universal_screening_service.screen_address_universal(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            chains=None,  # None = all chains
            max_concurrent=20,
        )
        
        assert result is not None
        assert result.total_chains_checked >= 10  # Should check many chains
        assert result.processing_time_ms < 60000  # Max 60 seconds


class TestUniversalScreeningAPI:
    """Integration Tests für Universal Screening API"""
    
    @pytest.mark.asyncio
    async def test_api_endpoint_screen(self, test_client, auth_headers):
        """Test /api/v1/universal-screening/screen endpoint"""
        response = await test_client.post(
            "/api/v1/universal-screening/screen",
            json={
                "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "chains": ["ethereum"],
                "max_concurrent": 10,
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "message" in data
        
        # Validate data structure
        result_data = data["data"]
        assert "address" in result_data
        assert "aggregate_risk_score" in result_data
        assert "chain_results" in result_data
    
    @pytest.mark.asyncio
    async def test_api_endpoint_chains(self, test_client):
        """Test /api/v1/universal-screening/chains endpoint"""
        response = await test_client.get("/api/v1/universal-screening/chains")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "total_chains" in data
        assert "chains" in data
        assert data["total_chains"] > 0
        assert len(data["chains"]) > 0


# Fixtures für Tests
@pytest.fixture
def test_client():
    """Test client fixture (placeholder - implement with actual test client)"""
    # TODO: Implement with actual FastAPI test client
    pass


@pytest.fixture
def auth_headers():
    """Auth headers fixture (placeholder)"""
    # TODO: Implement with actual auth token
    return {"Authorization": "Bearer test_token"}
