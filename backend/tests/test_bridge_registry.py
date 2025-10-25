"""Tests for Bridge Registry and Detection"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.bridge.registry import BridgeRegistry, BridgeContract, bridge_registry
from app.bridge.detection import BridgeDetectionService, bridge_detection_service
from app.schemas import CanonicalEvent


class TestBridgeRegistry:
    """Tests for Bridge Registry"""
    
    @pytest.fixture
    def fresh_registry(self):
        """Create a fresh registry instance for testing"""
        registry = BridgeRegistry()
        # Clear default contracts for isolated testing
        registry._contracts = {}
        registry._method_selectors = set()
        return registry
    
    def test_registry_initialization(self):
        """Test that global registry initializes with default contracts"""
        stats = bridge_registry.get_stats()
        assert stats["total_contracts"] > 0
        assert stats["total_chains"] > 0
        assert stats["total_selectors"] > 0
    
    def test_register_bridge_contract(self, fresh_registry):
        """Test registering a new bridge contract"""
        contract = BridgeContract(
            address="0x1234567890123456789012345678901234567890",
            chain="ethereum",
            name="Test Bridge",
            bridge_type="third_party",
            counterpart_chains=["polygon"],
            method_selectors=["0xabcdef12"]
        )
        
        success = fresh_registry.register(contract)
        assert success is True
        
        # Verify registration
        assert fresh_registry.is_bridge_contract(contract.address, "ethereum")
        assert fresh_registry.is_bridge_method("0xabcdef12")
    
    def test_address_normalization(self, fresh_registry):
        """Test that addresses are normalized to lowercase"""
        contract = BridgeContract(
            address="0xABCDEF1234567890ABCDEF1234567890ABCDEF12",
            chain="ETHEREUM",
            name="Test Bridge",
            bridge_type="canonical",
            counterpart_chains=["polygon"],
            method_selectors=["0x12345678"]
        )
        
        fresh_registry.register(contract)
        
        # Should find with any case
        assert fresh_registry.is_bridge_contract("0xabcdef1234567890abcdef1234567890abcdef12", "ethereum")
        assert fresh_registry.is_bridge_contract("0xABCDEF1234567890ABCDEF1234567890ABCDEF12", "ETHEREUM")
    
    def test_get_contract(self, fresh_registry):
        """Test retrieving contract information"""
        contract = BridgeContract(
            address="0x1111111111111111111111111111111111111111",
            chain="polygon",
            name="Polygon Bridge",
            bridge_type="canonical",
            counterpart_chains=["ethereum", "arbitrum"],
            method_selectors=["0x11111111"]
        )
        
        fresh_registry.register(contract)
        
        retrieved = fresh_registry.get_contract(contract.address, "polygon")
        assert retrieved is not None
        assert retrieved.name == "Polygon Bridge"
        assert retrieved.bridge_type == "canonical"
        assert "ethereum" in retrieved.counterpart_chains
    
    def test_get_contracts_by_chain(self, fresh_registry):
        """Test filtering contracts by chain"""
        contract1 = BridgeContract(
            address="0x1111111111111111111111111111111111111111",
            chain="ethereum",
            name="ETH Bridge 1",
            bridge_type="canonical",
            counterpart_chains=["polygon"],
            method_selectors=[]
        )
        
        contract2 = BridgeContract(
            address="0x2222222222222222222222222222222222222222",
            chain="ethereum",
            name="ETH Bridge 2",
            bridge_type="third_party",
            counterpart_chains=["arbitrum"],
            method_selectors=[]
        )
        
        contract3 = BridgeContract(
            address="0x3333333333333333333333333333333333333333",
            chain="polygon",
            name="Polygon Bridge",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=[]
        )
        
        fresh_registry.register(contract1)
        fresh_registry.register(contract2)
        fresh_registry.register(contract3)
        
        eth_contracts = fresh_registry.get_contracts_by_chain("ethereum")
        assert len(eth_contracts) == 2
        
        polygon_contracts = fresh_registry.get_contracts_by_chain("polygon")
        assert len(polygon_contracts) == 1
    
    def test_remove_contract(self, fresh_registry):
        """Test removing a contract from registry"""
        contract = BridgeContract(
            address="0x4444444444444444444444444444444444444444",
            chain="arbitrum",
            name="Temp Bridge",
            bridge_type="third_party",
            counterpart_chains=["ethereum"],
            method_selectors=[]
        )
        
        fresh_registry.register(contract)
        assert fresh_registry.is_bridge_contract(contract.address, "arbitrum")
        
        success = fresh_registry.remove_contract(contract.address, "arbitrum")
        assert success is True
        assert not fresh_registry.is_bridge_contract(contract.address, "arbitrum")
    
    def test_get_counterpart_chains(self, fresh_registry):
        """Test retrieving counterpart chains"""
        contract = BridgeContract(
            address="0x5555555555555555555555555555555555555555",
            chain="optimism",
            name="Multi-Chain Bridge",
            bridge_type="third_party",
            counterpart_chains=["ethereum", "polygon", "arbitrum"],
            method_selectors=[]
        )
        
        fresh_registry.register(contract)
        
        chains = fresh_registry.get_counterpart_chains(contract.address, "optimism")
        assert len(chains) == 3
        assert "ethereum" in chains
        assert "polygon" in chains
        assert "arbitrum" in chains
    
    def test_method_selector_detection(self, fresh_registry):
        """Test method selector detection across contracts"""
        contract1 = BridgeContract(
            address="0x6666666666666666666666666666666666666666",
            chain="ethereum",
            name="Bridge A",
            bridge_type="canonical",
            counterpart_chains=["polygon"],
            method_selectors=["0xaaaaaaaa", "0xbbbbbbbb"]
        )
        
        contract2 = BridgeContract(
            address="0x7777777777777777777777777777777777777777",
            chain="polygon",
            name="Bridge B",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],
            method_selectors=["0xcccccccc"]
        )
        
        fresh_registry.register(contract1)
        fresh_registry.register(contract2)
        
        assert fresh_registry.is_bridge_method("0xaaaaaaaa")
        assert fresh_registry.is_bridge_method("0xbbbbbbbb")
        assert fresh_registry.is_bridge_method("0xcccccccc")
        assert not fresh_registry.is_bridge_method("0xdddddddd")


class TestBridgeDetectionService:
    """Tests for Bridge Detection Service"""
    
    @pytest.fixture
    def detection_service(self):
        """Create detection service instance"""
        return BridgeDetectionService()
    
    @pytest.fixture
    def sample_bridge_event(self):
        """Create a sample bridge transaction event"""
        return CanonicalEvent(
            event_id="test_bridge_1",
            chain="polygon",
            block_number=50000000,
            block_timestamp=datetime(2024, 1, 15, 10, 0, 0),
            tx_hash="0xaabbccdd",
            tx_index=1,
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0xa0c68c638235ee32657e8f720a23cec1bfc77c77",  # Known Polygon bridge
            value=Decimal("1.5"),
            status=1,
            event_type="bridge",
            contract_address="0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
            idempotency_key="polygon_50000000_1",
            source="rpc",
            metadata={"bridge_method": "0x3ccfd60b"}
        )
    
    def test_detect_bridge_via_contract_address(self, detection_service, sample_bridge_event):
        """Test bridge detection via known contract address"""
        bridge_info = detection_service.detect_bridge_transaction(sample_bridge_event)
        
        assert bridge_info is not None
        assert bridge_info["source_chain"] == "polygon"
        assert bridge_info["bridge_name"] == "Polygon PoS Bridge - RootChainManager"
        assert bridge_info["bridge_type"] == "canonical"
        assert bridge_info["tx_hash"] == "0xaabbccdd"
    
    def test_detect_bridge_via_to_address(self, detection_service):
        """Test bridge detection when contract_address is None but to_address is bridge"""
        event = CanonicalEvent(
            event_id="test_bridge_2",
            chain="arbitrum",
            block_number=150000000,
            block_timestamp=datetime(2024, 1, 15, 11, 0, 0),
            tx_hash="0x11223344",
            tx_index=0,
            from_address="0x9999999999999999999999999999999999999999",
            to_address="0x72ce9c846789fdb6fc1f34ac4ad25dd9ef7031ef",  # Arbitrum Gateway
            value=Decimal("2.0"),
            status=1,
            event_type="bridge",
            contract_address=None,
            idempotency_key="arbitrum_150000000_0",
            source="rpc",
            metadata={}
        )
        
        bridge_info = detection_service.detect_bridge_transaction(event)
        
        assert bridge_info is not None
        assert bridge_info["source_chain"] == "arbitrum"
        assert "Gateway" in bridge_info["bridge_name"]
    
    def test_no_bridge_detected(self, detection_service):
        """Test that non-bridge transactions return None"""
        event = CanonicalEvent(
            event_id="test_normal_tx",
            chain="ethereum",
            block_number=18000000,
            block_timestamp=datetime(2024, 1, 15, 12, 0, 0),
            tx_hash="0x55667788",
            tx_index=5,
            from_address="0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            to_address="0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            value=Decimal("0.1"),
            status=1,
            event_type="transfer",
            contract_address=None,
            idempotency_key="ethereum_18000000_5",
            source="rpc",
            metadata={}
        )
        
        bridge_info = detection_service.detect_bridge_transaction(event)
        assert bridge_info is None
    
    def test_create_bridge_link_data(self, detection_service):
        """Test creation of bridge link data for Neo4j"""
        bridge_info = {
            "source_chain": "ethereum",
            "destination_chain": "polygon",
            "bridge_name": "Test Bridge",
            "bridge_contract": "0x1234",
            "tx_hash": "0xabcd",
            "timestamp": "2024-01-15T10:00:00",
            "from_address": "0xaaaa",
            "to_address": "0xbbbb",
            "value": "1.5",
            "token_address": "0xcccc",
            "token_symbol": "TEST"
        }
        
        link_data = detection_service.create_bridge_link_data(bridge_info)
        
        assert link_data["chain_from"] == "ethereum"
        assert link_data["chain_to"] == "polygon"
        assert link_data["bridge"] == "Test Bridge"
        assert link_data["tx_hash"] == "0xabcd"
        assert link_data["token_address"] == "0xcccc"
    
    def test_infer_destination_chain_single_counterpart(self, detection_service):
        """Test destination chain inference when only one option"""
        # Create a test contract with single counterpart
        from app.bridge.registry import BridgeContract, bridge_registry
        
        test_contract = BridgeContract(
            address="0xtest1234567890123456789012345678901234",
            chain="base",
            name="Base to Ethereum Bridge",
            bridge_type="canonical",
            counterpart_chains=["ethereum"],  # Only one option
            method_selectors=[]
        )
        
        bridge_registry.register(test_contract)
        
        event = CanonicalEvent(
            event_id="test_inference",
            chain="base",
            block_number=8000000,
            block_timestamp=datetime(2024, 1, 15, 13, 0, 0),
            tx_hash="0x99aabbcc",
            tx_index=0,
            from_address="0xdddddddddddddddddddddddddddddddddddddddd",
            to_address="0xtest1234567890123456789012345678901234",
            value=Decimal("5.0"),
            status=1,
            event_type="bridge",
            contract_address="0xtest1234567890123456789012345678901234",
            idempotency_key="base_8000000_0",
            source="rpc",
            metadata={}
        )
        
        bridge_info = detection_service.detect_bridge_transaction(event)
        
        assert bridge_info is not None
        assert bridge_info["destination_chain"] == "ethereum"


class TestBridgeIntegration:
    """Integration tests for bridge detection in trace pipeline"""
    
    def test_registry_has_l2_bridges(self):
        """Test that registry contains bridges for all L2s"""
        stats = bridge_registry.get_stats()
        
        # Should have bridges for multiple chains
        assert stats["total_chains"] >= 4  # At least Polygon, Arbitrum, Optimism, Base
        
        # Check specific chains
        polygon_bridges = bridge_registry.get_contracts_by_chain("polygon")
        assert len(polygon_bridges) > 0
        
        arbitrum_bridges = bridge_registry.get_contracts_by_chain("arbitrum")
        assert len(arbitrum_bridges) > 0
        
        optimism_bridges = bridge_registry.get_contracts_by_chain("optimism")
        assert len(optimism_bridges) > 0
        
        base_bridges = bridge_registry.get_contracts_by_chain("base")
        assert len(base_bridges) > 0
    
    def test_canonical_vs_third_party_bridges(self):
        """Test differentiation between canonical and third-party bridges"""
        all_contracts = bridge_registry.get_all_contracts()
        
        canonical = [c for c in all_contracts if c.bridge_type == "canonical"]
        third_party = [c for c in all_contracts if c.bridge_type == "third_party"]
        
        # Should have both types
        assert len(canonical) > 0
        assert len(third_party) > 0
    
    def test_method_selectors_unique(self):
        """Test that method selectors are tracked correctly"""
        stats = bridge_registry.get_stats()
        assert stats["total_selectors"] > 0
        
        # Common bridge methods should be registered
        assert bridge_registry.is_bridge_method("0x3ccfd60b")  # Polygon
        assert bridge_registry.is_bridge_method("0x0f4d14e9")  # Arbitrum
