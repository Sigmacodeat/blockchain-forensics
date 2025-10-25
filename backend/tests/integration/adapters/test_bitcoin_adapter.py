"""
Comprehensive Bitcoin Adapter Tests
Tests for UTXO tracing, change detection, CoinJoin detection, and co-spending heuristics
All tests use mock RPC responses from fixtures
"""

import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from datetime import datetime

from app.adapters.bitcoin_adapter import BitcoinAdapter


# Fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bitcoin"


def load_fixture(filename: str) -> dict:
    """Load a JSON fixture file"""
    with open(FIXTURES_DIR / filename) as f:
        return json.load(f)


class MockRPC:
    """Mock RPC client for Bitcoin tests"""
    
    def __init__(self):
        self.fixtures = {
            "block_simple": load_fixture("block_simple.json"),
            "block_coinjoin": load_fixture("block_coinjoin.json"),
            "block_multi_input": load_fixture("block_multi_input.json"),
            "tx_prev_1": load_fixture("tx_prev_1.json"),
            "tx_cj_prev_1": load_fixture("tx_cj_prev_1.json"),
            "tx_cj_prev_2": load_fixture("tx_cj_prev_2.json"),
            "tx_cj_prev_3": load_fixture("tx_cj_prev_3.json"),
            "tx_mi_prev_1": load_fixture("tx_mi_prev_1.json"),
            "tx_mi_prev_2": load_fixture("tx_mi_prev_2.json"),
        }
    
    async def json_rpc(self, url: str, method: str, params: list, user=None, password=None):
        """Mock JSON-RPC calls"""
        if method == "getblockcount":
            return {"result": 700005}
        
        elif method == "getblockhash":
            height = params[0]
            if height == 700000:
                return {"result": self.fixtures["block_simple"]["hash"]}
            elif height == 700001:
                return {"result": self.fixtures["block_coinjoin"]["hash"]}
            elif height == 700002:
                return {"result": self.fixtures["block_multi_input"]["hash"]}
            return {"result": f"hash_{height}"}
        
        elif method == "getblock":
            block_hash = params[0]
            if "0000000000000000000a" in block_hash:
                return {"result": self.fixtures["block_simple"]}
            elif "0000000000000000000b" in block_hash:
                return {"result": self.fixtures["block_coinjoin"]}
            elif "0000000000000000000c" in block_hash:
                return {"result": self.fixtures["block_multi_input"]}
            return {"result": {}}
        
        elif method == "getrawtransaction":
            txid = params[0]
            # Map txids to fixtures
            fixture_map = {
                "prev_tx_1": "tx_prev_1",
                "cj_prev_tx_1": "tx_cj_prev_1",
                "cj_prev_tx_2": "tx_cj_prev_2",
                "cj_prev_tx_3": "tx_cj_prev_3",
                "mi_prev_tx_1": "tx_mi_prev_1",
                "mi_prev_tx_2": "tx_mi_prev_2",
            }
            
            if txid in fixture_map:
                return {"result": self.fixtures[fixture_map[txid]]}
            
            # For transactions in blocks
            for block_fixture in [self.fixtures["block_simple"], 
                                 self.fixtures["block_coinjoin"],
                                 self.fixtures["block_multi_input"]]:
                for tx in block_fixture.get("tx", []):
                    if tx.get("txid") == txid:
                        return {"result": tx}
            
            return {"result": {}}
        
        return {"result": None}


@pytest.fixture
def mock_rpc():
    """Fixture providing mock RPC"""
    return MockRPC()


@pytest.fixture
def btc_adapter(mock_rpc):
    """Fixture providing Bitcoin adapter with mocked RPC"""
    return BitcoinAdapter(rpc_url="mock://bitcoin")


class TestBitcoinAdapterBasics:
    """Test basic adapter functionality"""
    
    @pytest.mark.asyncio
    async def test_chain_name(self, btc_adapter):
        """Test chain name property"""
        assert btc_adapter.chain_name == "bitcoin"
    
    @pytest.mark.asyncio
    async def test_health_no_rpc(self):
        """Test health check without RPC URL"""
        adapter = BitcoinAdapter()
        health = await adapter.health()
        assert health["chain"] == "bitcoin"
        assert health["status"] == "stub"
        assert health["rpc"] is False
    
    @pytest.mark.asyncio
    async def test_health_with_rpc(self, btc_adapter, mock_rpc):
        """Test health check with RPC"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            health = await btc_adapter.health()
            assert health["chain"] == "bitcoin"
            assert health["status"] == "ready"
            assert health["rpc"] is True
            assert health["height"] == 700005
    
    @pytest.mark.asyncio
    async def test_get_latest_block_number(self, btc_adapter, mock_rpc):
        """Test fetching latest block number"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            latest = await btc_adapter.get_latest_block_number()
            assert latest == 700005
    
    @pytest.mark.asyncio
    async def test_is_contract(self, btc_adapter):
        """Test is_contract always returns False for Bitcoin"""
        assert await btc_adapter.is_contract("1SomeAddress") is False


class TestChangeDetection:
    """Test change output detection heuristic"""
    
    def test_detect_change_output_simple(self, btc_adapter):
        """Test change detection with simple transaction"""
        tx = load_fixture("block_simple.json")["tx"][0]
        input_addresses = ["1ChangeAddress456"]
        
        change_vout = btc_adapter.detect_change_output(tx, input_addresses)
        assert change_vout == 1  # Second output is change
    
    def test_detect_change_output_no_match(self, btc_adapter):
        """Test change detection with no matching addresses"""
        tx = load_fixture("block_simple.json")["tx"][0]
        input_addresses = ["1DifferentAddress"]
        
        change_vout = btc_adapter.detect_change_output(tx, input_addresses)
        assert change_vout is None
    
    def test_detect_change_output_empty_inputs(self, btc_adapter):
        """Test change detection with empty input addresses"""
        tx = load_fixture("block_simple.json")["tx"][0]
        
        change_vout = btc_adapter.detect_change_output(tx, [])
        assert change_vout is None


class TestCoinJoinDetection:
    """Test CoinJoin detection heuristic"""
    
    def test_detect_coinjoin_positive(self, btc_adapter):
        """Test CoinJoin detection with CoinJoin transaction"""
        tx = load_fixture("block_coinjoin.json")["tx"][0]
        
        is_coinjoin = btc_adapter.detect_coinjoin(tx)
        assert is_coinjoin is True  # 3 outputs with equal value 0.1
    
    def test_detect_coinjoin_simple_transfer(self, btc_adapter):
        """Test CoinJoin detection with simple transfer"""
        tx = load_fixture("block_simple.json")["tx"][0]
        
        is_coinjoin = btc_adapter.detect_coinjoin(tx)
        assert is_coinjoin is False  # Only 1 input, different output values
    
    def test_detect_coinjoin_insufficient_mixing(self, btc_adapter):
        """Test CoinJoin detection with insufficient inputs/outputs"""
        tx = {
            "vin": [{"txid": "a", "vout": 0}, {"txid": "b", "vout": 0}],  # Only 2 inputs
            "vout": [
                {"n": 0, "value": 0.1},
                {"n": 1, "value": 0.1},
            ]
        }
        
        is_coinjoin = btc_adapter.detect_coinjoin(tx)
        assert is_coinjoin is False  # Not enough inputs


class TestCoSpendAddresses:
    """Test co-spending address extraction"""
    
    def test_extract_co_spend_addresses(self, btc_adapter):
        """Test extracting unique addresses from inputs"""
        tx = load_fixture("block_multi_input.json")["tx"][0]
        input_addresses = ["1CommonOwner", "1CommonOwner", "1AnotherAddr"]
        
        co_spend = btc_adapter.extract_co_spend_addresses(tx, input_addresses)
        assert len(co_spend) == 2  # Unique addresses
        assert "1CommonOwner" in co_spend
        assert "1AnotherAddr" in co_spend
    
    def test_extract_co_spend_addresses_empty(self, btc_adapter):
        """Test with empty input addresses"""
        tx = load_fixture("block_simple.json")["tx"][0]
        
        co_spend = btc_adapter.extract_co_spend_addresses(tx, [])
        assert co_spend == []


class TestTransactionTransformation:
    """Test transformation to CanonicalEvent"""
    
    @pytest.mark.asyncio
    async def test_transform_simple_transaction(self, btc_adapter, mock_rpc):
        """Test transforming simple Bitcoin transaction"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            block_data = load_fixture("block_simple.json")
            raw_tx = block_data["tx"][0]
            
            event = await btc_adapter.transform_transaction(raw_tx, block_data)
            
            # Basic assertions
            assert event.chain == "bitcoin"
            assert event.tx_hash == "tx1_simple_transfer"
            assert event.block_number == 700000
            assert event.status == 1
            assert event.token_symbol == "BTC"
            assert event.token_decimals == 8
            
            # Check addresses
            assert event.from_address == "1ChangeAddress456"
            assert event.to_address == "1DestinationAddress123"
            
            # Check value
            assert event.value == Decimal("0.5")
            
            # Check fee (1.0 - 0.5 - 0.4995 = 0.0005)
            assert event.fee >= Decimal("0.0004")
            assert event.fee <= Decimal("0.0006")
            
            # Check event type
            assert event.event_type == "transfer"
            
            # Check metadata
            assert "bitcoin" in event.metadata
            btc_meta = event.metadata["bitcoin"]
            assert btc_meta["change_vout"] == 1
            assert btc_meta["is_coinjoin"] is False
            assert len(btc_meta["outputs"]) == 2
    
    @pytest.mark.asyncio
    async def test_transform_coinjoin_transaction(self, btc_adapter, mock_rpc):
        """Test transforming CoinJoin transaction"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            block_data = load_fixture("block_coinjoin.json")
            raw_tx = block_data["tx"][0]
            
            event = await btc_adapter.transform_transaction(raw_tx, block_data)
            
            # Check CoinJoin detection
            assert event.event_type == "coinjoin"
            assert "coinjoin" in event.tags
            
            # Check metadata
            btc_meta = event.metadata["bitcoin"]
            assert btc_meta["is_coinjoin"] is True
            assert len(btc_meta["inputs"]) == 3
            assert len(btc_meta["outputs"]) == 4
    
    @pytest.mark.asyncio
    async def test_transform_multi_input_transaction(self, btc_adapter, mock_rpc):
        """Test transforming multi-input transaction (co-spending)"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            block_data = load_fixture("block_multi_input.json")
            raw_tx = block_data["tx"][0]
            
            event = await btc_adapter.transform_transaction(raw_tx, block_data)
            
            # Check co-spending addresses
            btc_meta = event.metadata["bitcoin"]
            assert "1CommonOwner" in btc_meta["co_spend_addresses"]
            
            # Check change detection
            assert btc_meta["change_vout"] == 1  # Second output is change
            
            # Main transfer should be to first non-change output
            assert event.to_address == "1Destination"
            assert event.value == Decimal("0.8")


class TestBlockFetching:
    """Test block and transaction fetching"""
    
    @pytest.mark.asyncio
    async def test_fetch_block(self, btc_adapter, mock_rpc):
        """Test fetching a block"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            block = await btc_adapter.fetch_block(700000)
            
            assert block["height"] == 700000
            assert block["status"] == "ok"
            assert block["tx_count"] == 1
            assert "hash" in block
            assert "raw" in block
    
    @pytest.mark.asyncio
    async def test_fetch_tx(self, btc_adapter, mock_rpc):
        """Test fetching a transaction"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            tx = await btc_adapter.fetch_tx("tx1_simple_transfer")
            
            assert tx["txid"] == "tx1_simple_transfer"
            assert "vin" in tx
            assert "vout" in tx
    
    @pytest.mark.asyncio
    async def test_normalize_tx(self, btc_adapter):
        """Test transaction normalization"""
        raw_tx = load_fixture("block_simple.json")["tx"][0]
        
        normalized = btc_adapter.normalize_tx(raw_tx)
        
        assert normalized["txid"] == "tx1_simple_transfer"
        assert len(normalized["vin"]) == 1
        assert len(normalized["vout"]) == 2
        assert normalized["vout"][0]["value"] == 0.5
        assert "1DestinationAddress123" in normalized["vout"][0]["addresses"]


class TestUTXOEdges:
    """Test UTXO edge building"""
    
    @pytest.mark.asyncio
    async def test_build_tx_edges_proportional(self, btc_adapter, mock_rpc):
        """Test building transaction edges with proportional method"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            tx = load_fixture("block_simple.json")["tx"][0]
            
            result = await btc_adapter.build_tx_edges(tx, method="proportional")
            
            assert result["txid"] == "tx1_simple_transfer"
            assert "edges" in result
            assert "fee" in result
            assert result["method"] == "proportional"
            
            # Should have edges from input to outputs
            edges = result["edges"]
            assert len(edges) > 0
            
            # Check edge structure
            for edge in edges:
                assert "from" in edge
                assert "to" in edge
                assert "value" in edge
                assert edge["from"]["txid"] == "prev_tx_1"
    
    @pytest.mark.asyncio
    async def test_build_tx_edges_heuristic(self, btc_adapter, mock_rpc):
        """Test building transaction edges with heuristic method (excludes change)"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            tx = load_fixture("block_simple.json")["tx"][0]
            
            result = await btc_adapter.build_tx_edges(tx, method="heuristic")
            
            assert result["method"] == "heuristic"
            
            # With heuristic, change output should be excluded
            edges = result["edges"]
            for edge in edges:
                # All edges should go to non-change output (vout 0)
                assert edge["to"]["vout"] == 0


class TestStreamBlocks:
    """Test block streaming"""
    
    @pytest.mark.asyncio
    async def test_stream_blocks_simple(self, btc_adapter, mock_rpc):
        """Test streaming blocks"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            events = []
            async for event in btc_adapter.stream_blocks(700000, 700000):
                events.append(event)
            
            assert len(events) == 1
            assert events[0].chain == "bitcoin"
            assert events[0].block_number == 700000
    
    @pytest.mark.asyncio
    async def test_stream_blocks_multiple(self, btc_adapter, mock_rpc):
        """Test streaming multiple blocks"""
        with patch("app.adapters.bitcoin_adapter.json_rpc", side_effect=mock_rpc.json_rpc):
            events = []
            async for event in btc_adapter.stream_blocks(700000, 700002):
                events.append(event)
            
            # Should have 3 events (one per block)
            assert len(events) == 3
            assert events[0].block_number == 700000
            assert events[1].block_number == 700001
            assert events[2].block_number == 700002


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_no_rpc_url(self):
        """Test adapter behavior without RPC URL"""
        adapter = BitcoinAdapter()
        
        block = await adapter.fetch_block(1)
        assert block["status"] == "no_rpc"
        
        tx = await adapter.fetch_tx("test")
        assert tx["status"] == "no_rpc"
        
        latest = await adapter.get_latest_block_number()
        assert latest == 0
    
    @pytest.mark.asyncio
    async def test_coinbase_transaction(self, btc_adapter):
        """Test handling of coinbase transaction"""
        # Coinbase tx has no previous inputs
        coinbase_tx = {
            "txid": "coinbase_tx",
            "vin": [{"coinbase": "0370110a"}],
            "vout": [
                {
                    "n": 0,
                    "value": 6.25,
                    "scriptPubKey": {
                        "addresses": ["1MinerAddress"]
                    }
                }
            ]
        }
        
        block_data = {
            "height": 700003,
            "hash": "test_hash",
            "time": 1631234567
        }
        
        event = await btc_adapter.transform_transaction(coinbase_tx, block_data)
        
        assert event.from_address == "coinbase"
        assert event.to_address == "1MinerAddress"
        assert event.value == Decimal("6.25")
