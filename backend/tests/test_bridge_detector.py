"""
Tests for Bridge Detection Module
"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.bridge.bridge_detector import (
    bridge_detector,
    BridgeDetector,
    BridgeRegistry,
    BridgeSignature,
)
from app.schemas.canonical_event import CanonicalEvent


@pytest.fixture
def sample_ethereum_bridge_event():
    """Sample Ethereum bridge transaction (Wormhole)"""
    return CanonicalEvent(
        event_id="eth_bridge_123",
        chain="ethereum",
        block_number=18000000,
        block_timestamp=datetime.utcnow(),
        tx_hash="0xabc123def456",
        tx_index=10,
        from_address="0x742d35cc6634c0532925a3b844bc454e4438f44e",
        to_address="0x3ee18b2214aff97000d974cf647e7c347e8fa585",  # Wormhole Token Bridge
        value=Decimal("1.5"),
        value_usd=None,
        gas_used=150000,
        gas_price=Decimal("50"),
        fee=Decimal("0.0075"),
        status=1,
        error_message=None,
        event_type="transfer",
        contract_address=None,
        method_name=None,
        token_address=None,
        token_symbol=None,
        token_decimals=None,
        risk_score=None,
        cluster_id=None,
        cross_chain_links=[],
        labels=[],
        tags=[],
        source="rpc",
        idempotency_key="eth_18000000_0xabc123def456",
        metadata={
            "logs": [
                {
                    "topics": [
                        "0x6eb224fb001ed210e379b335e35efe88672a8ce935d981a6896b27ffdf52a3b2"  # LogMessagePublished
                    ]
                }
            ]
        },
    )


@pytest.fixture
def sample_solana_bridge_event():
    """Sample Solana bridge transaction"""
    return CanonicalEvent(
        event_id="sol_bridge_123",
        chain="solana",
        block_number=200000000,
        block_timestamp=datetime.utcnow(),
        tx_hash="5J8K9L0M1N2P3Q4R5S6T7U8V9W0X1Y2Z",
        tx_index=0,
        from_address="abc123def456",
        to_address="wormdt3mdmotqcgv5hddso1ewqn5tqhdg9stkrdwp9",  # Wormhole on Solana
        value=Decimal("10.0"),
        value_usd=None,
        gas_used=None,
        gas_price=None,
        fee=None,
        status=1,
        error_message=None,
        event_type="bridge",
        contract_address=None,
        method_name=None,
        token_address=None,
        token_symbol=None,
        token_decimals=None,
        risk_score=None,
        cluster_id=None,
        cross_chain_links=[],
        labels=[],
        tags=[],
        source="rpc",
        idempotency_key="sol_200000000_5J8K9L0M1N2P3Q4R5S6T7U8V9W0X1Y2Z",
        metadata={"bridge_program": "wormdt3mdmotqcgv5hddso1ewqn5tqhdg9stkrdwp9"},
    )


@pytest.fixture
def sample_non_bridge_event():
    """Sample regular non-bridge transaction"""
    return CanonicalEvent(
        event_id="eth_regular_123",
        chain="ethereum",
        block_number=18000000,
        block_timestamp=datetime.utcnow(),
        tx_hash="0xregular123",
        tx_index=5,
        from_address="0x123abc",
        to_address="0x456def",
        value=Decimal("0.5"),
        value_usd=None,
        gas_used=21000,
        gas_price=Decimal("30"),
        fee=Decimal("0.00063"),
        status=1,
        error_message=None,
        event_type="transfer",
        contract_address=None,
        method_name=None,
        token_address=None,
        token_symbol=None,
        token_decimals=None,
        risk_score=None,
        cluster_id=None,
        cross_chain_links=[],
        labels=[],
        tags=[],
        source="rpc",
        idempotency_key="eth_18000000_0xregular123",
        metadata={},
    )


class TestBridgeRegistry:
    """Test Bridge Registry"""
    
    def test_registry_has_bridges(self):
        """Registry should have 10+ bridges"""
        assert len(BridgeRegistry.BRIDGES) >= 10
    
    def test_get_signatures_for_chain_ethereum(self):
        """Should return Ethereum bridges"""
        eth_sigs = BridgeRegistry.get_signatures_for_chain("ethereum")
        assert len(eth_sigs) > 0
        assert all(sig.chain == "ethereum" for sig in eth_sigs)
    
    def test_get_signatures_for_chain_solana(self):
        """Should return Solana bridges"""
        sol_sigs = BridgeRegistry.get_signatures_for_chain("solana")
        assert len(sol_sigs) > 0
        assert all(sig.chain == "solana" for sig in sol_sigs)
    
    def test_get_signature_by_address_wormhole(self):
        """Should find Wormhole bridge by contract address"""
        sig = BridgeRegistry.get_signature_by_address(
            "0x3ee18b2214aff97000d974cf647e7c347e8fa585",
            "ethereum"
        )
        assert sig is not None
        assert sig.bridge_name == "Wormhole"
    
    def test_get_signature_by_address_not_found(self):
        """Should return None for unknown address"""
        sig = BridgeRegistry.get_signature_by_address(
            "0xunknown123",
            "ethereum"
        )
        assert sig is None
    
    def test_all_bridges_have_required_fields(self):
        """All bridges should have required fields"""
        for sig in BridgeRegistry.BRIDGES:
            assert sig.bridge_name
            assert sig.chain
            assert len(sig.contract_addresses) > 0
            assert sig.pattern_type in ["lock_mint", "burn_unlock", "liquidity_pool"]
            assert isinstance(sig.metadata, dict)


class TestBridgeDetector:
    """Test Bridge Detector"""
    
    @pytest.mark.asyncio
    async def test_detect_ethereum_bridge_via_contract(self, sample_ethereum_bridge_event):
        """Should detect Ethereum bridge via contract address"""
        detector = BridgeDetector()
        result = await detector.detect_bridge(sample_ethereum_bridge_event)
        
        assert result is not None
        assert result["bridge_name"] == "Wormhole"
        assert result["chain_from"] == "ethereum"
        assert result["pattern_type"] == "lock_mint"
    
    @pytest.mark.asyncio
    async def test_detect_ethereum_bridge_via_event_signature(self, sample_ethereum_bridge_event):
        """Should detect Ethereum bridge via event signature"""
        detector = BridgeDetector()
        result = await detector.detect_bridge(sample_ethereum_bridge_event)
        
        assert result is not None
        assert "Wormhole" in result["bridge_name"]
    
    @pytest.mark.asyncio
    async def test_detect_solana_bridge_via_metadata(self, sample_solana_bridge_event):
        """Should detect Solana bridge via metadata or contract"""
        detector = BridgeDetector()
        result = await detector.detect_bridge(sample_solana_bridge_event)
        
        assert result is not None
        assert result["chain_from"] == "solana"
        # Can be detected via contract_address or metadata
        assert result["detected_via"] in ["contract_address", "metadata"]
    
    @pytest.mark.asyncio
    async def test_no_detection_for_regular_transaction(self, sample_non_bridge_event):
        """Should not detect bridge for regular transaction"""
        detector = BridgeDetector()
        result = await detector.detect_bridge(sample_non_bridge_event)
        
        assert result is None
    
    def test_wormhole_chain_id_mapping(self):
        """Should correctly map Wormhole chain IDs"""
        detector = BridgeDetector()
        
        assert detector._wormhole_chain_id_to_name(1) == "solana"
        assert detector._wormhole_chain_id_to_name(2) == "ethereum"
        assert detector._wormhole_chain_id_to_name(5) == "polygon"
        assert detector._wormhole_chain_id_to_name(999) == "wormhole_chain_999"
    
    def test_layerzero_chain_id_mapping(self):
        """Should correctly map LayerZero chain IDs"""
        detector = BridgeDetector()
        
        assert detector._layerzero_chain_id_to_name(101) == "ethereum"
        assert detector._layerzero_chain_id_to_name(109) == "polygon"
        assert detector._layerzero_chain_id_to_name(999) == "layerzero_chain_999"
    
    @pytest.mark.asyncio
    async def test_analyze_bridge_flow_empty(self):
        """Should handle address with no bridge transactions"""
        detector = BridgeDetector()
        # This will fail gracefully if Neo4j is not connected
        result = await detector.analyze_bridge_flow("0xunknownaddress123")
        
        # Should return valid structure even on error
        assert "address" in result
        assert "total_flows" in result


class TestBridgeSignature:
    """Test Bridge Signature dataclass"""
    
    def test_bridge_signature_creation(self):
        """Should create valid bridge signature"""
        sig = BridgeSignature(
            bridge_name="Test Bridge",
            chain="ethereum",
            contract_addresses={"0x123"},
            event_signatures={"0xabc"},
            pattern_type="lock_mint",
            metadata={"test": "data"}
        )
        
        assert sig.bridge_name == "Test Bridge"
        assert sig.chain == "ethereum"
        assert len(sig.contract_addresses) == 1
        assert sig.pattern_type == "lock_mint"


@pytest.mark.asyncio
async def test_global_bridge_detector_instance():
    """Global bridge_detector instance should be available"""
    assert bridge_detector is not None
    assert isinstance(bridge_detector, BridgeDetector)
