"""Tests für neue Chain-Adapter (Fantom, Celo, Moonbeam, Aurora, Starknet, Cardano, NEAR, Sui, Aptos)"""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
class TestFantomAdapter:
    """Tests für Fantom Opera Adapter"""
    
    async def test_fantom_adapter_import(self):
        """Test: Fantom Adapter ist importierbar"""
        from app.adapters.fantom_adapter import FantomAdapter
        assert FantomAdapter is not None
    
    async def test_fantom_adapter_initialization(self):
        """Test: Fantom Adapter kann initialisiert werden"""
        from app.adapters.fantom_adapter import FantomAdapter
        adapter = FantomAdapter()
        assert adapter.chain_info.chain_id == "fantom"
        assert adapter.chain_info.symbol == "FTM"
        assert adapter.chain_info.chain_type == "evm"


@pytest.mark.asyncio
class TestCeloAdapter:
    """Tests für Celo Adapter"""
    
    async def test_celo_adapter_import(self):
        """Test: Celo Adapter ist importierbar"""
        from app.adapters.celo_adapter import CeloAdapter
        assert CeloAdapter is not None
    
    async def test_celo_adapter_initialization(self):
        """Test: Celo Adapter kann initialisiert werden"""
        from app.adapters.celo_adapter import CeloAdapter
        adapter = CeloAdapter()
        assert adapter.chain_info.chain_id == "celo"
        assert adapter.chain_info.symbol == "CELO"


@pytest.mark.asyncio
class TestMoonbeamAdapter:
    """Tests für Moonbeam Adapter"""
    
    async def test_moonbeam_adapter_import(self):
        """Test: Moonbeam Adapter ist importierbar"""
        from app.adapters.moonbeam_adapter import MoonbeamAdapter
        assert MoonbeamAdapter is not None
    
    async def test_moonbeam_adapter_initialization(self):
        """Test: Moonbeam Adapter kann initialisiert werden"""
        from app.adapters.moonbeam_adapter import MoonbeamAdapter
        adapter = MoonbeamAdapter()
        assert adapter.chain_info.chain_id == "moonbeam"
        assert adapter.chain_info.symbol == "GLMR"


@pytest.mark.asyncio
class TestAuroraAdapter:
    """Tests für Aurora Adapter"""
    
    async def test_aurora_adapter_import(self):
        """Test: Aurora Adapter ist importierbar"""
        from app.adapters.aurora_adapter import AuroraAdapter
        assert AuroraAdapter is not None
    
    async def test_aurora_adapter_initialization(self):
        """Test: Aurora Adapter kann initialisiert werden"""
        from app.adapters.aurora_adapter import AuroraAdapter
        adapter = AuroraAdapter()
        assert adapter.chain_info.chain_id == "aurora"
        assert adapter.chain_info.symbol == "ETH"


@pytest.mark.asyncio
class TestStarknetAdapter:
    """Tests für Starknet Adapter"""
    
    async def test_starknet_adapter_import(self):
        """Test: Starknet Adapter ist importierbar"""
        from app.adapters.starknet_adapter import StarknetAdapter
        assert StarknetAdapter is not None
    
    async def test_starknet_adapter_initialization(self):
        """Test: Starknet Adapter kann initialisiert werden"""
        from app.adapters.starknet_adapter import StarknetAdapter
        adapter = StarknetAdapter()
        assert adapter.chain_info.chain_id == "starknet"
        assert adapter.chain_info.chain_type == "layer2"
    
    async def test_starknet_get_block_height(self):
        """Test: Starknet Block-Height Abruf"""
        from app.adapters.starknet_adapter import StarknetAdapter
        adapter = StarknetAdapter()
        
        with patch.object(adapter, 'make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"result": 123456}
            height = await adapter.get_block_height()
            assert height == 123456
            mock_request.assert_called_once_with("starknet_blockNumber")


@pytest.mark.asyncio
class TestCardanoAdapter:
    """Tests für Cardano Adapter"""
    
    async def test_cardano_adapter_import(self):
        """Test: Cardano Adapter ist importierbar"""
        from app.adapters.cardano_adapter import CardanoAdapter
        assert CardanoAdapter is not None
    
    async def test_cardano_adapter_initialization(self):
        """Test: Cardano Adapter kann initialisiert werden"""
        from app.adapters.cardano_adapter import CardanoAdapter
        adapter = CardanoAdapter()
        assert adapter.chain_info.chain_id == "cardano"
        assert adapter.chain_info.symbol == "ADA"
        assert adapter.chain_info.chain_type == "utxo"


@pytest.mark.asyncio
class TestNearAdapter:
    """Tests für NEAR Protocol Adapter"""
    
    async def test_near_adapter_import(self):
        """Test: NEAR Adapter ist importierbar"""
        from app.adapters.near_adapter import NearAdapter
        assert NearAdapter is not None
    
    async def test_near_adapter_initialization(self):
        """Test: NEAR Adapter kann initialisiert werden"""
        from app.adapters.near_adapter import NearAdapter
        adapter = NearAdapter()
        assert adapter.chain_info.chain_id == "near"
        assert adapter.chain_info.symbol == "NEAR"


@pytest.mark.asyncio
class TestSuiAdapter:
    """Tests für Sui Adapter"""
    
    async def test_sui_adapter_import(self):
        """Test: Sui Adapter ist importierbar"""
        from app.adapters.sui_adapter import SuiAdapter
        assert SuiAdapter is not None
    
    async def test_sui_adapter_initialization(self):
        """Test: Sui Adapter kann initialisiert werden"""
        from app.adapters.sui_adapter import SuiAdapter
        adapter = SuiAdapter()
        assert adapter.chain_info.chain_id == "sui"
        assert adapter.chain_info.symbol == "SUI"


@pytest.mark.asyncio
class TestAptosAdapter:
    """Tests für Aptos Adapter"""
    
    async def test_aptos_adapter_import(self):
        """Test: Aptos Adapter ist importierbar"""
        from app.adapters.aptos_adapter import AptosAdapter
        assert AptosAdapter is not None
    
    async def test_aptos_adapter_initialization(self):
        """Test: Aptos Adapter kann initialisiert werden"""
        from app.adapters.aptos_adapter import AptosAdapter
        adapter = AptosAdapter()
        assert adapter.chain_info.chain_id == "aptos"
        assert adapter.chain_info.symbol == "APT"


@pytest.mark.asyncio
class TestMultiChainRegistry:
    """Tests für Multi-Chain Registry mit neuen Chains"""
    
    async def test_registry_contains_all_21_chains(self):
        """Test: Registry enthält alle 21+ Chains"""
        from app.services.multi_chain import ChainAdapterFactory
        
        factory = ChainAdapterFactory()
        chains = factory.get_supported_chains()
        chain_ids = [c.chain_id for c in chains]
        
        # Neue Chains müssen vorhanden sein
        assert "fantom" in chain_ids
        assert "celo" in chain_ids
        assert "moonbeam" in chain_ids
        assert "aurora" in chain_ids
        assert "starknet" in chain_ids
        assert "cardano" in chain_ids
        assert "near" in chain_ids
        assert "sui" in chain_ids
        assert "aptos" in chain_ids
        
        # Mindestens 21 Chains
        assert len(chain_ids) >= 21
    
    async def test_factory_creates_fantom_adapter(self):
        """Test: Factory erstellt Fantom-Adapter korrekt"""
        from app.services.multi_chain import ChainAdapterFactory
        
        factory = ChainAdapterFactory()
        adapter = factory.get_adapter("fantom")
        
        assert adapter is not None
        assert adapter.chain_info.chain_id == "fantom"
    
    async def test_factory_creates_starknet_adapter(self):
        """Test: Factory erstellt Starknet-Adapter korrekt"""
        from app.services.multi_chain import ChainAdapterFactory
        
        factory = ChainAdapterFactory()
        adapter = factory.get_adapter("starknet")
        
        assert adapter is not None
        assert adapter.chain_info.chain_id == "starknet"
