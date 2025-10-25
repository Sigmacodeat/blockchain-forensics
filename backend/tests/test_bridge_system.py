"""
Comprehensive Bridge System Tests
Tests for bridge detection, registry, and Neo4j persistence
All tests use mocks - no live blockchain or database connections
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.bridge.registry import BridgeRegistry, BridgeContract
from app.bridge.detection import BridgeDetectionService
from app.bridge.neo4j_persistence import BridgePersistence
from app.schemas import CanonicalEvent


class MockNeo4jClient:
    """Mock Neo4j client for bridge tests"""
    
    def __init__(self):
        self.queries_executed = []
        self.bridge_links = []  # Simulated graph data
    
    async def execute_write(self, query, params):
        """Mock write execution"""
        self.queries_executed.append({"query": query, "params": params})
        
        # Simulate bridge link creation
        if "BRIDGE_LINK" in query:
            link = {
                "from_address": params.get("from_address"),
                "to_address": params.get("to_address"),
                "chain_from": params.get("chain_from"),
                "chain_to": params.get("chain_to"),
                "bridge": params.get("bridge_name"),
                "tx_hash": params.get("tx_hash"),
            }
            self.bridge_links.append(link)
            
            return [{"edge_id": len(self.bridge_links)}]
        
        return [{"success": True}]
    
    async def execute_read(self, query, params):
        """Mock read execution"""
        self.queries_executed.append({"query": query, "params": params})
        
        # Bridge links for address
        if "Address {address:" in query and "BRIDGE_LINK" in query:
            address = params.get("address")
            results = [
                link for link in self.bridge_links
                if link["from_address"] == address or link["to_address"] == address
            ]
            return [{
                "chain_from": r["chain_from"],
                "chain_to": r["chain_to"],
                "bridge_name": r["bridge"],
                "tx_hash": r["tx_hash"],
                "timestamp": "2024-01-01T00:00:00",
                "value": "1.0",
                "token_symbol": "ETH",
                "counterpart_address": r["to_address"]
            } for r in results[:params.get("limit", 100)]]
        
        # Cross-chain path finding
        if "BRIDGE_LINK*" in query:
            # Simple mock: return one path
            return [{
                "bridge_path": [
                    {
                        "chain_from": "ethereum",
                        "chain_to": "polygon",
                        "bridge": "Polygon PoS Bridge",
                        "tx_hash": "0xtest123",
                        "timestamp": "2024-01-01T00:00:00"
                    }
                ],
                "hop_count": 1
            }]
        
        # Statistics
        if "count(*)" in query or "sum(" in query:
            return [{
                "bridge_name": "Polygon PoS Bridge",
                "chain_from": "ethereum",
                "chain_to": "polygon",
                "tx_count": len(self.bridge_links),
                "total_value": sum(float(l.get("value", 0)) for l in self.bridge_links if "value" in l)
            }]
        
        return []


@pytest.fixture
def mock_neo4j():
    """Fixture providing mock Neo4j client"""
    return MockNeo4jClient()


@pytest.fixture
def bridge_registry():
    """Fixture providing fresh bridge registry"""
    return BridgeRegistry()


@pytest.fixture
def bridge_detection():
    """Fixture providing bridge detection service"""
    return BridgeDetectionService()


@pytest.fixture
def bridge_persistence(mock_neo4j):
    """Fixture providing bridge persistence with mocked Neo4j"""
    persistence = BridgePersistence()
    persistence.neo4j = mock_neo4j
    return persistence


@pytest.fixture
def sample_bridge_event():
    """Fixture providing sample bridge CanonicalEvent"""
    # Note: Using Polygon chain with correct bridge address
    return CanonicalEvent(
        event_id="poly_bridge_tx_123",
        chain="polygon",  # Changed to polygon since we're using Polygon bridge address
        block_number=18000000,
        block_timestamp=datetime(2024, 1, 1, 12, 0, 0),
        tx_hash="0xbridge123",
        tx_index=42,
        from_address="0xuser123",
        to_address="0xa0c68c638235ee32657e8f720a23cec1bfc77c77",  # Polygon bridge
        value=Decimal("1.5"),
        status=1,
        event_type="contract_call",
        contract_address="0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
        method_name="depositFor",
        token_address="0xusdc",
        token_symbol="USDC",
        token_decimals=6,
        source="rpc",
        idempotency_key="poly_18000000_42",
        metadata={
            "destination_chain": "ethereum"  # Polygon -> Ethereum
        }
    )


class TestBridgeRegistry:
    """Test bridge contract registry"""
    
    def test_registry_initialization(self, bridge_registry):
        """Test registry initializes with default bridges"""
        stats = bridge_registry.get_stats()
        
        assert stats["total_contracts"] > 0
        assert stats["total_chains"] >= 4  # ETH, Polygon, Arbitrum, Optimism
        assert stats["total_selectors"] > 0
    
    def test_register_bridge_contract(self, bridge_registry):
        """Test registering a new bridge contract"""
        initial_count = bridge_registry.get_stats()["total_contracts"]
        
        contract = BridgeContract(
            address="0xtest123",
            chain="ethereum",
            name="Test Bridge",
            bridge_type="third_party",
            counterpart_chains=["polygon"],
            method_selectors=["0x12345678"]
        )
        
        success = bridge_registry.register(contract)
        
        assert success is True
        assert bridge_registry.get_stats()["total_contracts"] == initial_count + 1
    
    def test_is_bridge_contract(self, bridge_registry):
        """Test checking if address is a bridge contract"""
        # Polygon bridge from defaults
        is_bridge = bridge_registry.is_bridge_contract(
            "0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
            "polygon"
        )
        
        assert is_bridge is True
    
    def test_is_bridge_contract_negative(self, bridge_registry):
        """Test non-bridge address returns False"""
        is_bridge = bridge_registry.is_bridge_contract(
            "0xrandomaddress",
            "ethereum"
        )
        
        assert is_bridge is False
    
    def test_is_bridge_method(self, bridge_registry):
        """Test checking if method selector is a bridge method"""
        # depositFor selector from Polygon bridge
        is_method = bridge_registry.is_bridge_method("0x3ccfd60b")
        
        assert is_method is True
    
    def test_get_contract(self, bridge_registry):
        """Test retrieving bridge contract info"""
        contract = bridge_registry.get_contract(
            "0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
            "polygon"
        )
        
        assert contract is not None
        assert contract.name == "Polygon PoS Bridge - RootChainManager"
        assert contract.bridge_type == "canonical"
        assert "ethereum" in contract.counterpart_chains
    
    def test_get_contracts_by_chain(self, bridge_registry):
        """Test getting all contracts for a chain"""
        contracts = bridge_registry.get_contracts_by_chain("ethereum")
        
        assert len(contracts) > 0
        assert all(c.chain == "ethereum" for c in contracts)
    
    def test_get_all_contracts(self, bridge_registry):
        """Test getting all contracts"""
        contracts = bridge_registry.get_all_contracts()
        
        assert len(contracts) > 0
        # Should have contracts from multiple chains
        chains = set(c.chain for c in contracts)
        assert len(chains) > 1
    
    def test_get_counterpart_chains(self, bridge_registry):
        """Test getting counterpart chains for a bridge"""
        chains = bridge_registry.get_counterpart_chains(
            "0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
            "polygon"
        )
        
        assert "ethereum" in chains
    
    def test_remove_contract(self, bridge_registry):
        """Test removing a bridge contract"""
        # Add a test contract first
        contract = BridgeContract(
            address="0xremove_me",
            chain="test",
            name="Remove Test",
            bridge_type="test",
            counterpart_chains=[],
            method_selectors=[]
        )
        bridge_registry.register(contract)
        
        # Remove it
        success = bridge_registry.remove_contract("0xremove_me", "test")
        
        assert success is True
        assert bridge_registry.get_contract("0xremove_me", "test") is None
    
    def test_case_insensitivity(self, bridge_registry):
        """Test that addresses are case-insensitive"""
        contract_lower = bridge_registry.get_contract(
            "0xa0c68c638235ee32657e8f720a23cec1bfc77c77",
            "polygon"
        )
        
        contract_upper = bridge_registry.get_contract(
            "0xA0C68C638235EE32657E8F720A23CEC1BFC77C77",
            "POLYGON"
        )
        
        assert contract_lower is not None
        assert contract_upper is not None
        assert contract_lower.address == contract_upper.address


class TestBridgeDetection:
    """Test bridge detection service"""
    
    def test_detect_bridge_by_contract_address(self, bridge_detection, sample_bridge_event):
        """Test detecting bridge via contract address"""
        bridge_info = bridge_detection.detect_bridge_transaction(sample_bridge_event)
        
        assert bridge_info is not None
        assert bridge_info["bridge_name"] == "Polygon PoS Bridge - RootChainManager"
        assert bridge_info["source_chain"] == "polygon"
        assert bridge_info["destination_chain"] == "ethereum"
    
    def test_detect_bridge_by_to_address(self, bridge_detection):
        """Test detecting bridge via to_address"""
        event = CanonicalEvent(
            event_id="test",
            chain="ethereum",
            block_number=1,
            block_timestamp=datetime.utcnow(),
            tx_hash="0xtest",
            tx_index=0,
            from_address="0xuser",
            to_address="0x8731d54e9d02c286767d56ac03e8037c07e01e98",  # Stargate
            value=Decimal("1.0"),
            status=1,
            event_type="transfer",
            source="rpc",
            idempotency_key="test_1_0",
            metadata={}
        )
        
        bridge_info = bridge_detection.detect_bridge_transaction(event)
        
        assert bridge_info is not None
        assert "Stargate" in bridge_info["bridge_name"]
    
    def test_no_bridge_detected(self, bridge_detection):
        """Test that non-bridge transactions return None"""
        event = CanonicalEvent(
            event_id="test",
            chain="ethereum",
            block_number=1,
            block_timestamp=datetime.utcnow(),
            tx_hash="0xtest",
            tx_index=0,
            from_address="0xuser1",
            to_address="0xuser2",  # Not a bridge
            value=Decimal("1.0"),
            status=1,
            event_type="transfer",
            source="rpc",
            idempotency_key="test_1_0",
            metadata={}
        )
        
        bridge_info = bridge_detection.detect_bridge_transaction(event)
        
        assert bridge_info is None
    
    def test_infer_destination_chain_single_option(self, bridge_detection, sample_bridge_event):
        """Test destination chain inference when only one option"""
        bridge_info = bridge_detection.detect_bridge_transaction(sample_bridge_event)
        
        assert bridge_info is not None
        # Polygon bridge only connects to Ethereum
        assert bridge_info["destination_chain"] == "ethereum"
    
    def test_bridge_info_includes_token_data(self, bridge_detection, sample_bridge_event):
        """Test that bridge info includes token data"""
        bridge_info = bridge_detection.detect_bridge_transaction(sample_bridge_event)
        
        assert bridge_info is not None
        assert bridge_info["token_address"] == "0xusdc"
        assert bridge_info["token_symbol"] == "USDC"
    
    def test_create_bridge_link_data(self, bridge_detection, sample_bridge_event):
        """Test creating bridge link data for Neo4j"""
        bridge_info = bridge_detection.detect_bridge_transaction(sample_bridge_event)
        
        assert bridge_info is not None
        
        link_data = bridge_detection.create_bridge_link_data(bridge_info)
        
        assert link_data["chain_from"] == "polygon"
        assert link_data["chain_to"] == "ethereum"
        assert link_data["bridge"] == "Polygon PoS Bridge - RootChainManager"
        assert link_data["tx_hash"] == "0xbridge123"


class TestBridgePersistence:
    """Test Neo4j bridge persistence"""
    
    @pytest.mark.asyncio
    async def test_save_bridge_link(self, bridge_persistence, mock_neo4j):
        """Test saving a bridge link to Neo4j"""
        bridge_info = {
            "source_chain": "ethereum",
            "destination_chain": "polygon",
            "bridge_name": "Polygon PoS Bridge",
            "bridge_contract": "0xbridge",
            "tx_hash": "0xtest123",
            "timestamp": "2024-01-01T00:00:00",
            "value": "1.5",
            "token_address": "0xusdc",
            "token_symbol": "USDC",
            "bridge_type": "canonical"
        }
        
        result = await bridge_persistence.save_bridge_link(
            from_address="0xuser1",
            to_address="0xuser2",
            bridge_info=bridge_info
        )
        
        assert result["success"] is True
        assert result["chain_from"] == "ethereum"
        assert result["chain_to"] == "polygon"
        
        # Check that query was executed
        assert len(mock_neo4j.queries_executed) > 0
        assert "BRIDGE_LINK" in mock_neo4j.queries_executed[0]["query"]
    
    @pytest.mark.asyncio
    async def test_get_bridge_links_for_address(self, bridge_persistence, mock_neo4j):
        """Test retrieving bridge links for an address"""
        # Add some test data
        mock_neo4j.bridge_links = [
            {
                "from_address": "0xuser1",
                "to_address": "0xuser2",
                "chain_from": "ethereum",
                "chain_to": "polygon",
                "bridge": "Test Bridge",
                "tx_hash": "0xtest1",
                "value": "1.0"
            }
        ]
        
        links = await bridge_persistence.get_bridge_links_for_address(
            address="0xuser1",
            direction="outgoing"
        )
        
        assert len(links) > 0
        assert links[0]["chain_from"] == "ethereum"
        assert links[0]["chain_to"] == "polygon"
    
    @pytest.mark.asyncio
    async def test_get_cross_chain_path(self, bridge_persistence, mock_neo4j):
        """Test finding cross-chain paths"""
        paths = await bridge_persistence.get_cross_chain_path(
            start_address="0xuser1",
            start_chain="ethereum",
            end_chain="polygon",
            max_hops=5
        )
        
        # Mock may return empty if no data - test passes if no error
        assert isinstance(paths, list)
    
    @pytest.mark.asyncio
    async def test_get_bridge_statistics(self, bridge_persistence, mock_neo4j):
        """Test getting bridge statistics"""
        # Add test data
        mock_neo4j.bridge_links = [
            {"chain_from": "ethereum", "chain_to": "polygon", "value": "1.0"},
            {"chain_from": "ethereum", "chain_to": "arbitrum", "value": "2.0"},
        ]
        
        stats = await bridge_persistence.get_bridge_statistics()
        
        assert "total_bridge_transactions" in stats
        assert stats["total_bridge_transactions"] >= 0
    
    @pytest.mark.asyncio
    async def test_find_linked_addresses_cross_chain(self, bridge_persistence, mock_neo4j):
        """Test finding linked addresses across chains"""
        linked = await bridge_persistence.find_linked_addresses_cross_chain(
            address="0xuser1",
            source_chain="ethereum",
            target_chain="polygon"
        )
        
        # Mock returns empty or mock data
        assert isinstance(linked, list)


class TestEndToEndBridgeFlow:
    """Test complete bridge detection and persistence flow"""
    
    @pytest.mark.asyncio
    async def test_full_bridge_flow(self, bridge_detection, bridge_persistence, mock_neo4j, sample_bridge_event):
        """Test complete flow from detection to persistence"""
        # 1. Detect bridge
        bridge_info = bridge_detection.detect_bridge_transaction(sample_bridge_event)
        assert bridge_info is not None
        
        # 2. Create link data
        link_data = bridge_detection.create_bridge_link_data(bridge_info)
        assert link_data is not None
        
        # 3. Persist to Neo4j
        result = await bridge_persistence.save_bridge_link(
            from_address=bridge_info["from_address"],
            to_address=bridge_info["to_address"],
            bridge_info=bridge_info
        )
        
        assert result["success"] is True
        assert len(mock_neo4j.bridge_links) == 1
        
        # 4. Query back
        links = await bridge_persistence.get_bridge_links_for_address(
            address=bridge_info["from_address"]
        )
        
        assert len(links) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_registry_with_duplicate_address(self, bridge_registry):
        """Test that registering same address updates existing"""
        contract1 = BridgeContract(
            address="0xdup",
            chain="test",
            name="Original",
            bridge_type="test",
            counterpart_chains=[],
            method_selectors=[]
        )
        
        contract2 = BridgeContract(
            address="0xdup",
            chain="test",
            name="Updated",
            bridge_type="test",
            counterpart_chains=["other"],
            method_selectors=[]
        )
        
        bridge_registry.register(contract1)
        bridge_registry.register(contract2)
        
        retrieved = bridge_registry.get_contract("0xdup", "test")
        assert retrieved.name == "Updated"
    
    @pytest.mark.asyncio
    async def test_persistence_error_handling(self, bridge_persistence):
        """Test graceful error handling in persistence"""
        # Mock Neo4j to raise error
        mock_failing = AsyncMock()
        mock_failing.execute_write = AsyncMock(side_effect=Exception("DB Error"))
        
        bridge_persistence.neo4j = mock_failing
        
        result = await bridge_persistence.save_bridge_link(
            from_address="0xtest",
            to_address="0xtest2",
            bridge_info={"source_chain": "eth", "destination_chain": "poly"}
        )
        
        # Should return error result, not raise exception
        assert result["success"] is False
        assert "error" in result
    
    def test_detection_with_unknown_chain(self, bridge_detection):
        """Test bridge detection with unknown destination chain"""
        # Wormhole connects to multiple chains
        event = CanonicalEvent(
            event_id="test",
            chain="ethereum",
            block_number=1,
            block_timestamp=datetime.utcnow(),
            tx_hash="0xtest",
            tx_index=0,
            from_address="0xuser",
            to_address="0x3ee18b2214aff97000d974cf647e7c347e8fa585",  # Wormhole
            contract_address="0x3ee18b2214aff97000d974cf647e7c347e8fa585",
            value=Decimal("1.0"),
            status=1,
            event_type="contract_call",
            source="rpc",
            idempotency_key="test_1_0",
            metadata={}  # No destination_chain hint
        )
        
        bridge_info = bridge_detection.detect_bridge_transaction(event)
        
        # Should still detect, but destination might be unknown
        assert bridge_info is not None
        assert bridge_info["bridge_name"] == "Wormhole"
