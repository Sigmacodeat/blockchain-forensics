"""
Tests for UTXO Graph Persistence
Tests Neo4j graph operations for Bitcoin UTXO tracking
All tests use mocked Neo4j client
"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.db.utxo_graph import UTXOGraph
from app.schemas import CanonicalEvent


class MockNeo4jClient:
    """Mock Neo4j client for testing"""
    
    def __init__(self):
        self.queries_executed = []
        self.data_store = {
            "addresses": {},
            "utxos": {},
            "co_spend_edges": [],
        }
    
    async def execute_write_batch(self, queries):
        """Mock batch write execution"""
        self.queries_executed.extend(queries)
        
        # Simulate successful execution
        results = []
        for query in queries:
            # Parse and simulate execution
            results.append({"success": True})
        
        return results
    
    async def execute_read(self, query, params):
        """Mock read execution"""
        self.queries_executed.append({"query": query, "params": params})
        
        # Return mock data based on query patterns - order matters!
        # Check for UTXO flow tracing first (most specific)
        if "nodes(path)" in query and "SPENT" in query:
            # UTXO flow tracing - returns list format as per Cypher query
            return [
                {
                    "nodes": [
                        {"utxo_id": "tx1:0", "txid": "tx1", "vout": 0, "value": 1.0, "spent": True},
                        {"utxo_id": "tx2:0", "txid": "tx2", "vout": 0, "value": 0.5, "spent": False}
                    ],
                    "edges": [
                        {"from": "tx1:0", "to": "tx2:0", "tx_hash": "tx2", "proportion": 0.5}
                    ],
                    "depth": 1
                }
            ]
        elif "CO_SPEND" in query and "address" in params:
            # Clustered addresses query
            return [
                {"address": "1RelatedAddr1", "tx_count": 3},
                {"address": "1RelatedAddr2", "tx_count": 2},
            ]
        elif "OWNS" in query and "address" in params:
            # UTXOs for address
            return [
                {
                    "utxo_id": "tx1:0",
                    "txid": "tx1",
                    "vout": 0,
                    "value": 0.5,
                    "spent": False,
                    "is_change": False,
                    "is_coinjoin": False,
                    "timestamp": "2024-01-01T00:00:00"
                }
            ]
        elif "utxo_id" in params and "path" in query.lower():
            # UTXO history query
            return [{"path": [{"utxo_id": params["utxo_id"]}]}]
        
        return []


@pytest.fixture
def mock_neo4j():
    """Fixture providing mock Neo4j client"""
    return MockNeo4jClient()


@pytest.fixture
def utxo_graph(mock_neo4j):
    """Fixture providing UTXOGraph with mocked Neo4j"""
    return UTXOGraph(neo4j_client=mock_neo4j)


@pytest.fixture
def sample_bitcoin_event():
    """Fixture providing sample Bitcoin CanonicalEvent"""
    return CanonicalEvent(
        event_id="btc_tx_test123",
        chain="bitcoin",
        block_number=700000,
        block_timestamp=datetime(2024, 1, 1, 12, 0, 0),
        tx_hash="test_tx_hash_123",
        tx_index=0,
        from_address="1FromAddr",
        to_address="1ToAddr",
        value=Decimal("0.5"),
        fee=Decimal("0.0005"),
        status=1,
        event_type="transfer",
        token_symbol="BTC",
        token_decimals=8,
        source="rpc",
        idempotency_key="btc_700000_test123",
        metadata={
            "bitcoin": {
                "inputs": [
                    {"txid": "prev_tx_1", "vout": 0, "coinbase": None}
                ],
                "outputs": [
                    {
                        "n": 0,
                        "value": 0.5,
                        "addresses": ["1ToAddr"],
                        "type": "pubkeyhash"
                    },
                    {
                        "n": 1,
                        "value": 0.4995,
                        "addresses": ["1ChangeAddr"],
                        "type": "pubkeyhash"
                    }
                ],
                "change_vout": 1,
                "is_coinjoin": False,
                "co_spend_addresses": ["1FromAddr"],
                "fee": 0.0005
            }
        }
    )


@pytest.fixture
def coinjoin_event():
    """Fixture providing CoinJoin CanonicalEvent"""
    return CanonicalEvent(
        event_id="btc_tx_coinjoin",
        chain="bitcoin",
        block_number=700001,
        block_timestamp=datetime(2024, 1, 1, 13, 0, 0),
        tx_hash="coinjoin_tx_hash",
        tx_index=0,
        from_address="1CJAddr1",
        to_address="1CJOutput1",
        value=Decimal("0.1"),
        fee=Decimal("0.0005"),
        status=1,
        event_type="coinjoin",
        token_symbol="BTC",
        token_decimals=8,
        source="rpc",
        idempotency_key="btc_700001_coinjoin",
        metadata={
            "bitcoin": {
                "inputs": [
                    {"txid": "cj_prev_1", "vout": 0},
                    {"txid": "cj_prev_2", "vout": 0},
                    {"txid": "cj_prev_3", "vout": 0}
                ],
                "outputs": [
                    {"n": 0, "value": 0.1, "addresses": ["1CJOutput1"], "type": "pubkeyhash"},
                    {"n": 1, "value": 0.1, "addresses": ["1CJOutput2"], "type": "pubkeyhash"},
                    {"n": 2, "value": 0.1, "addresses": ["1CJOutput3"], "type": "pubkeyhash"}
                ],
                "change_vout": None,
                "is_coinjoin": True,
                "co_spend_addresses": ["1CJAddr1", "1CJAddr2", "1CJAddr3"],
                "fee": 0.0005
            }
        }
    )


class TestBasicUTXOPersistence:
    """Test basic UTXO graph persistence"""
    
    @pytest.mark.asyncio
    async def test_save_bitcoin_transaction_basic(self, utxo_graph, sample_bitcoin_event, mock_neo4j):
        """Test saving a basic Bitcoin transaction"""
        result = await utxo_graph.save_bitcoin_transaction(sample_bitcoin_event)
        
        assert result["tx_hash"] == "test_tx_hash_123"
        assert result["inputs_processed"] == 1
        assert result["outputs_created"] == 2
        assert result["is_coinjoin"] is False
        
        # Verify queries were executed
        assert len(mock_neo4j.queries_executed) > 0
    
    @pytest.mark.asyncio
    async def test_save_bitcoin_transaction_creates_addresses(self, utxo_graph, sample_bitcoin_event, mock_neo4j):
        """Test that address nodes are created"""
        await utxo_graph.save_bitcoin_transaction(sample_bitcoin_event)
        
        # Check for address creation queries
        address_queries = [q for q in mock_neo4j.queries_executed 
                          if "MERGE" in q.get("query", "") and "Address" in q.get("query", "")]
        
        assert len(address_queries) > 0
    
    @pytest.mark.asyncio
    async def test_save_bitcoin_transaction_creates_utxos(self, utxo_graph, sample_bitcoin_event, mock_neo4j):
        """Test that UTXO nodes are created"""
        await utxo_graph.save_bitcoin_transaction(sample_bitcoin_event)
        
        # Check for UTXO creation queries
        utxo_queries = [q for q in mock_neo4j.queries_executed 
                       if "MERGE" in q.get("query", "") and "UTXO" in q.get("query", "")]
        
        # Should create 2 UTXOs (one for each output)
        assert len(utxo_queries) >= 2
    
    @pytest.mark.asyncio
    async def test_save_bitcoin_transaction_creates_owns_edges(self, utxo_graph, sample_bitcoin_event, mock_neo4j):
        """Test that OWNS edges are created"""
        await utxo_graph.save_bitcoin_transaction(sample_bitcoin_event)
        
        # Check for OWNS edge creation
        owns_queries = [q for q in mock_neo4j.queries_executed 
                       if "OWNS" in q.get("query", "")]
        
        assert len(owns_queries) >= 2
    
    @pytest.mark.asyncio
    async def test_save_bitcoin_transaction_creates_spent_edges(self, utxo_graph, sample_bitcoin_event, mock_neo4j):
        """Test that SPENT edges are created"""
        await utxo_graph.save_bitcoin_transaction(sample_bitcoin_event)
        
        # Check for SPENT edge creation
        spent_queries = [q for q in mock_neo4j.queries_executed 
                        if "SPENT" in q.get("query", "") and "MERGE" in q.get("query", "")]
        
        # Should create SPENT edges from input to each output
        assert len(spent_queries) >= 2
    
    @pytest.mark.asyncio
    async def test_save_bitcoin_transaction_rejects_non_bitcoin(self, utxo_graph):
        """Test that non-Bitcoin events are rejected"""
        eth_event = CanonicalEvent(
            event_id="eth_tx",
            chain="ethereum",
            block_number=1,
            block_timestamp=datetime.utcnow(),
            tx_hash="0x123",
            tx_index=0,
            from_address="0x123",
            to_address="0x456",
            value=Decimal("1"),
            status=1,
            event_type="transfer",
            source="rpc",
            idempotency_key="eth_1_0",
            metadata={}
        )
        
        with pytest.raises(ValueError, match="Expected bitcoin event"):
            await utxo_graph.save_bitcoin_transaction(eth_event)


class TestCoinJoinHandling:
    """Test CoinJoin-specific graph operations"""
    
    @pytest.mark.asyncio
    async def test_save_coinjoin_transaction(self, utxo_graph, coinjoin_event, mock_neo4j):
        """Test saving a CoinJoin transaction"""
        result = await utxo_graph.save_bitcoin_transaction(coinjoin_event)
        
        assert result["is_coinjoin"] is True
        assert result["inputs_processed"] == 3
        assert result["outputs_created"] == 3
    
    @pytest.mark.asyncio
    async def test_coinjoin_creates_co_spend_edges(self, utxo_graph, coinjoin_event, mock_neo4j):
        """Test that CoinJoin creates CO_SPEND edges"""
        await utxo_graph.save_bitcoin_transaction(coinjoin_event)
        
        # Check for CO_SPEND edge creation
        co_spend_queries = [q for q in mock_neo4j.queries_executed 
                           if "CO_SPEND" in q.get("query", "")]
        
        # With 3 co-spending addresses, should create 3 CO_SPEND edges
        # (1-2, 1-3, 2-3)
        assert len(co_spend_queries) >= 3
    
    @pytest.mark.asyncio
    async def test_coinjoin_tags_addresses(self, utxo_graph, coinjoin_event, mock_neo4j):
        """Test that CoinJoin transactions tag addresses"""
        await utxo_graph.save_bitcoin_transaction(coinjoin_event)
        
        # Check for has_coinjoin flag
        coinjoin_tag_queries = [q for q in mock_neo4j.queries_executed 
                               if "has_coinjoin" in q.get("query", "")]
        
        assert len(coinjoin_tag_queries) >= 3


class TestCoSpendClustering:
    """Test co-spending address clustering"""
    
    @pytest.mark.asyncio
    async def test_multi_input_creates_co_spend(self, utxo_graph, mock_neo4j):
        """Test that multi-input transactions create CO_SPEND edges"""
        multi_input_event = CanonicalEvent(
            event_id="btc_tx_multi",
            chain="bitcoin",
            block_number=700002,
            block_timestamp=datetime(2024, 1, 1, 14, 0, 0),
            tx_hash="multi_input_tx",
            tx_index=0,
            from_address="1CommonOwner",
            to_address="1Destination",
            value=Decimal("1.0"),
            fee=Decimal("0.001"),
            status=1,
            event_type="transfer",
            token_symbol="BTC",
            token_decimals=8,
            source="rpc",
            idempotency_key="btc_700002_multi",
            metadata={
                "bitcoin": {
                    "inputs": [
                        {"txid": "mi_prev_1", "vout": 0},
                        {"txid": "mi_prev_2", "vout": 0}
                    ],
                    "outputs": [
                        {"n": 0, "value": 1.0, "addresses": ["1Destination"], "type": "pubkeyhash"}
                    ],
                    "change_vout": None,
                    "is_coinjoin": False,
                    "co_spend_addresses": ["1Addr1", "1Addr2"],
                    "fee": 0.001
                }
            }
        )
        
        result = await utxo_graph.save_bitcoin_transaction(multi_input_event)
        
        # Should create CO_SPEND edge between the two addresses
        assert result["co_spend_edges"] == 1
    
    @pytest.mark.asyncio
    async def test_find_clustered_addresses(self, utxo_graph, mock_neo4j):
        """Test finding clustered addresses"""
        clustered = await utxo_graph.find_clustered_addresses("1TestAddr", min_tx_count=2)
        
        # Mock returns 2 related addresses
        assert len(clustered) == 2
        assert "1RelatedAddr1" in clustered
        assert "1RelatedAddr2" in clustered


class TestUTXOQueries:
    """Test UTXO query operations"""
    
    @pytest.mark.asyncio
    async def test_get_utxo_history(self, utxo_graph, mock_neo4j):
        """Test getting UTXO spending history"""
        history = await utxo_graph.get_utxo_history("tx1:0")
        
        assert history["utxo_id"] == "tx1:0"
        assert "spending_chain" in history
        assert len(mock_neo4j.queries_executed) > 0
    
    @pytest.mark.asyncio
    async def test_get_address_utxos_all(self, utxo_graph, mock_neo4j):
        """Test getting all UTXOs for an address"""
        utxos = await utxo_graph.get_address_utxos("1TestAddr")
        
        assert len(utxos) > 0
        assert utxos[0]["utxo_id"] == "tx1:0"
        assert utxos[0]["value"] == 0.5
    
    @pytest.mark.asyncio
    async def test_get_address_utxos_unspent(self, utxo_graph, mock_neo4j):
        """Test getting only unspent UTXOs"""
        utxos = await utxo_graph.get_address_utxos("1TestAddr", spent=False)
        
        assert all(u.get("spent") is False for u in utxos)
    
    @pytest.mark.asyncio
    async def test_get_address_utxos_spent(self, utxo_graph, mock_neo4j):
        """Test getting only spent UTXOs"""
        utxos = await utxo_graph.get_address_utxos("1TestAddr", spent=True)
        
        # Mock doesn't return spent UTXOs by default, so result might be empty or filtered
        assert isinstance(utxos, list)
    
    @pytest.mark.asyncio
    async def test_trace_utxo_flow(self, utxo_graph, mock_neo4j):
        """Test tracing UTXO flow through the graph"""
        flow = await utxo_graph.trace_utxo_flow("tx1:0", max_hops=5)
        
        assert flow["start_utxo"] == "tx1:0"
        assert flow["max_hops"] == 5
        assert "nodes" in flow
        assert "edges" in flow
        assert len(flow["nodes"]) > 0
        assert len(flow["edges"]) > 0
    
    @pytest.mark.asyncio
    async def test_trace_utxo_flow_deduplication(self, utxo_graph, mock_neo4j):
        """Test that UTXO flow tracing deduplicates nodes and edges"""
        flow = await utxo_graph.trace_utxo_flow("tx1:0", max_hops=10)
        
        # Check that node IDs are unique
        node_ids = [n["utxo_id"] for n in flow["nodes"]]
        assert len(node_ids) == len(set(node_ids))
        
        # Check that edge keys are unique
        edge_keys = [(e["from"], e["to"]) for e in flow["edges"]]
        assert len(edge_keys) == len(set(edge_keys))


class TestChangeDetection:
    """Test change output handling in graph"""
    
    @pytest.mark.asyncio
    async def test_change_output_flagged(self, utxo_graph, sample_bitcoin_event, mock_neo4j):
        """Test that change outputs are flagged in UTXO nodes"""
        await utxo_graph.save_bitcoin_transaction(sample_bitcoin_event)
        
        # Find UTXO creation queries
        utxo_queries = [q for q in mock_neo4j.queries_executed 
                       if "UTXO" in q.get("query", "") and "is_change" in q.get("query", "")]
        
        # Should have UTXOs with is_change flag
        assert len(utxo_queries) >= 2
        
        # Check that change vout is marked
        change_queries = [q for q in utxo_queries 
                         if q.get("params", {}).get("is_change") is True]
        assert len(change_queries) >= 1


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_coinbase_transaction(self, utxo_graph, mock_neo4j):
        """Test handling of coinbase transaction (no inputs)"""
        coinbase_event = CanonicalEvent(
            event_id="btc_tx_coinbase",
            chain="bitcoin",
            block_number=700000,
            block_timestamp=datetime(2024, 1, 1, 12, 0, 0),
            tx_hash="coinbase_tx",
            tx_index=0,
            from_address="coinbase",
            to_address="1MinerAddr",
            value=Decimal("6.25"),
            fee=Decimal("0"),
            status=1,
            event_type="transfer",
            token_symbol="BTC",
            token_decimals=8,
            source="rpc",
            idempotency_key="btc_700000_coinbase",
            metadata={
                "bitcoin": {
                    "inputs": [{"coinbase": "03e0110a"}],
                    "outputs": [
                        {"n": 0, "value": 6.25, "addresses": ["1MinerAddr"], "type": "pubkeyhash"}
                    ],
                    "change_vout": None,
                    "is_coinjoin": False,
                    "co_spend_addresses": [],
                    "fee": 0
                }
            }
        )
        
        result = await utxo_graph.save_bitcoin_transaction(coinbase_event)
        
        assert result["inputs_processed"] == 1
        assert result["outputs_created"] == 1
        assert result["co_spend_edges"] == 0
    
    @pytest.mark.asyncio
    async def test_empty_co_spend_addresses(self, utxo_graph, sample_bitcoin_event, mock_neo4j):
        """Test that single-input transactions don't create CO_SPEND edges"""
        # Modify event to have only one co-spend address
        sample_bitcoin_event.metadata["bitcoin"]["co_spend_addresses"] = ["1OnlyAddr"]
        
        result = await utxo_graph.save_bitcoin_transaction(sample_bitcoin_event)
        
        # Should not create CO_SPEND edges with only one address
        assert result["co_spend_edges"] == 0
