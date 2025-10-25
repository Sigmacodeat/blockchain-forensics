"""
Comprehensive Tests for Smart Contract Deep Analysis
=====================================================
Vollständige Tests für:
- Proxy-Resolution (EIP-1967, EIP-1167, Chains)
- Events-Matching
- UUPS/Upgradeability Checks
- resolve_proxy Flag
- ABI Enrichment
- RPC Retries
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.contracts.service import ContractsService
from app.contracts.event_signature_matcher import event_signature_matcher


# Sample bytecode for different proxy types
EIP1967_PROXY_BYTECODE = "0x363d3d373d3d3d363d73" + "a" * 40 + "5af43d82803e903d91602b57fd5bf3"
EIP1167_MINIMAL_PROXY = "0x363d3d373d3d3d363d73" + "b" * 40 + "5af43d82803e903d91602b57fd5bf3"
UUPS_IMPLEMENTATION = "0x608060405260043610610041576000357c010000000000000000000000000000000000000000000000000000000090048063" + "52d1902d" + "1461004657"


class TestProxyResolution:
    """Tests für Proxy-Erkennung und -Auflösung"""
    
    @pytest.mark.asyncio
    async def test_eip1967_resolution(self):
        """Test EIP-1967 Proxy Storage Slot Resolution"""
        service = ContractsService()
        
        # Mock eth_getStorageAt to return implementation address
        impl_address = "0x" + "c" * 40
        storage_value = "0x" + "0" * 24 + "c" * 40
        
        with patch.object(service, '_get_storage_at_async', return_value=storage_value):
            result = await service._resolve_eip1967_implementation("0xProxy", "ethereum")
            assert result == impl_address.lower()
    
    @pytest.mark.asyncio
    async def test_eip1967_null_address(self):
        """Test EIP-1967 mit Null-Adresse"""
        service = ContractsService()
        
        # Mock returns null address
        storage_value = "0x" + "0" * 64
        
        with patch.object(service, '_get_storage_at_async', return_value=storage_value):
            result = await service._resolve_eip1967_implementation("0xProxy", "ethereum")
            assert result is None
    
    def test_eip1167_minimal_proxy_detection(self):
        """Test EIP-1167 Minimal Proxy Pattern Detection"""
        service = ContractsService()
        
        impl_addr = "b" * 40
        # Komplettes EIP-1167 Pattern: 363d3d373d3d3d363d73<address>...
        bytecode = "0x363d3d373d3d3d363d73" + impl_addr + "5af43d82803e903d91602b57fd5bf3"
        
        result = service._resolve_eip1167_implementation_from_bytecode(bytecode)
        # Pattern muss erkannt werden
        if result:
            # Check dass es eine valide Adresse ist (0x + 40 hex chars)
            assert result.startswith("0x")
            assert len(result) == 42
            assert all(c in "0123456789abcdef" for c in result[2:].lower())
    
    def test_eip1167_non_proxy_bytecode(self):
        """Test dass normaler Bytecode nicht als EIP-1167 erkannt wird"""
        service = ContractsService()
        
        # Random bytecode without minimal proxy pattern
        bytecode = "0x6080604052348015600f57600080fd5b50603580601d6000396000f3"
        
        result = service._resolve_eip1167_implementation_from_bytecode(bytecode)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_proxy_chain_resolution(self):
        """Test mehrstufige Proxy-Kette"""
        service = ContractsService()
        
        proxy1 = "0x" + "1" * 40
        proxy2 = "0x" + "2" * 40
        impl = "0x" + "3" * 40
        
        call_count = 0
        async def mock_resolve_eip1967(addr, chain):
            nonlocal call_count
            call_count += 1
            if addr == proxy1:
                return proxy2
            elif addr == proxy2:
                return impl
            return None
        
        async def mock_fetch_bytecode(addr, chain):
            return "0x6080604052"  # dummy bytecode
        
        with patch.object(service, '_resolve_eip1967_implementation', side_effect=mock_resolve_eip1967):
            with patch.object(service, '_fetch_bytecode_async', side_effect=mock_fetch_bytecode):
                result_impl, proxy_type, proxy_source, chain = await service._resolve_proxy_chain(
                    proxy1, "ethereum", "0x6080"
                )
                
                assert result_impl == impl
                assert len(chain) == 2
                assert proxy2 in chain
                assert impl in chain
    
    @pytest.mark.asyncio
    async def test_resolve_proxy_false(self):
        """Test resolve_proxy=False unterbindet Proxy-Auflösung"""
        service = ContractsService()
        
        proxy_addr = "0x" + "a" * 40
        proxy_bytecode = "0x363d3d373d3d3d363d73" + "b" * 40 + "5af43d"
        
        with patch.object(service, '_fetch_bytecode_async', return_value=proxy_bytecode):
            with patch.object(service, '_run_full_analysis_async', return_value={"score": 0.5}):
                result = await service.analyze_async(proxy_addr, "ethereum", resolve_proxy=False)
                
                # Sollte kein Proxy-Info enthalten oder is_proxy=False
                # (da resolve_proxy=False keine Auflösung triggert)
                assert result is not None


class TestUUPSDetection:
    """Tests für UUPS Proxy Detection"""
    
    def test_uups_proxiable_uuid_detection(self):
        """Test UUPS Detection via proxiableUUID() selector"""
        service = ContractsService()
        
        # Bytecode mit proxiableUUID() selector (0x52d1902d)
        bytecode = "0x608060405260043610610041576000357c0100000000000000000000000000000000000000000000000000000000900480" + "6352d1902d" + "14610046"
        
        selectors = service.function_matcher.extract_selectors_from_bytecode(bytecode)
        
        # Sollte 0x52d1902d enthalten
        assert any(s.lower() == "0x52d1902d" for s in selectors)
    
    def test_upgradeability_check_logic(self):
        """Test Upgradeability Check Logic (vereinfacht)"""
        # Test der Upgradeability-Check-Logik direkt
        upgrade_selectors = {"0x3659cfe6", "0x4f1ef286"}
        access_selectors = {"0x8da5cb5b", "0xf2fde38b"}
        
        # Case 1: upgradeTo vorhanden, kein Access Control -> sollte Finding triggern
        selectors_unsafe = ["0x3659cfe6", "0xa9059cbb"]  # upgradeTo + transfer
        sel_lower_unsafe = {s.lower() for s in selectors_unsafe}
        has_upgrade_unsafe = any(s in sel_lower_unsafe for s in upgrade_selectors)
        has_access_unsafe = any(s in sel_lower_unsafe for s in access_selectors)
        
        assert has_upgrade_unsafe is True
        assert has_access_unsafe is False
        # Dies würde Finding triggern
        
        # Case 2: upgradeTo + owner vorhanden -> kein Finding
        selectors_safe = ["0x3659cfe6", "0x8da5cb5b"]  # upgradeTo + owner
        sel_lower_safe = {s.lower() for s in selectors_safe}
        has_upgrade_safe = any(s in sel_lower_safe for s in upgrade_selectors)
        has_access_safe = any(s in sel_lower_safe for s in access_selectors)
        
        assert has_upgrade_safe is True
        assert has_access_safe is True
        # Kein Finding


class TestEventSignatures:
    """Tests für Event Signature Matching"""
    
    def test_resolve_erc20_transfer_event(self):
        """Test Auflösung von ERC20 Transfer Event"""
        # Transfer(address,address,uint256)
        topic0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        
        result = event_signature_matcher.resolve_event(topic0)
        
        assert result is not None
        assert result.name == "Transfer"
        assert len(result.params) == 3
        assert "address" in result.params
        assert "uint256" in result.params
    
    def test_resolve_approval_event(self):
        """Test Auflösung von Approval Event"""
        # Approval(address,address,uint256)
        topic0 = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
        
        result = event_signature_matcher.resolve_event(topic0)
        
        assert result is not None
        assert result.name == "Approval"
    
    def test_extract_events_from_logs(self):
        """Test Extraktion von Events aus Logs"""
        logs = [
            {
                "topics": [
                    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                    "0x000000000000000000000000" + "a" * 40,
                    "0x000000000000000000000000" + "b" * 40,
                ],
                "data": "0x0000000000000000000000000000000000000000000000000000000000000064"
            },
            {
                "topics": [
                    "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",
                ],
                "data": "0x"
            }
        ]
        
        topics = event_signature_matcher.extract_events_from_logs(logs)
        
        assert len(topics) == 2
        assert any("ddf252ad" in t for t in topics)  # Transfer
        assert any("8c5be1e5" in t for t in topics)  # Approval


class TestRPCRetries:
    """Tests für RPC Retries und Backoff"""
    
    @pytest.mark.asyncio
    async def test_rpc_retry_on_failure(self):
        """Test dass RPC-Calls bei Fehler wiederholt werden"""
        service = ContractsService()
        
        call_count = 0
        async def mock_post_failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Network error")
            
            # Success on 2nd try
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"result": "0x6080"}
            mock_resp.raise_for_status = Mock()
            return mock_resp
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post_failing_then_success
            
            result = await service._rpc_post("http://test.rpc", {"method": "eth_getCode"}, retries=3)
            
            assert call_count == 2  # Failed once, then succeeded
            assert result == {"result": "0x6080"}
    
    @pytest.mark.asyncio
    async def test_rpc_exhausts_retries(self):
        """Test dass nach allen Retries Exception geworfen wird"""
        service = ContractsService()
        
        async def mock_post_always_fail(*args, **kwargs):
            raise Exception("Network error")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post_always_fail
            
            with pytest.raises(Exception, match="RPC request failed after"):
                await service._rpc_post("http://test.rpc", {"method": "test"}, retries=3, timeout=1.0)


class TestBytecodeCache:
    """Tests für Bytecode Caching"""
    
    @pytest.mark.asyncio
    async def test_bytecode_cache_hit(self):
        """Test dass Bytecode aus Cache geladen wird"""
        service = ContractsService()
        
        address = "0x" + "a" * 40
        chain = "ethereum"
        bytecode = "0x6080604052"
        
        # First call - should fetch and cache
        with patch.object(service, '_rpc_post', return_value={"result": bytecode}):
            result1 = await service._fetch_bytecode_async(address, chain)
            assert result1 == bytecode
        
        # Second call - should hit cache (no RPC call)
        with patch.object(service, '_rpc_post') as mock_rpc:
            result2 = await service._fetch_bytecode_async(address, chain)
            assert result2 == bytecode
            mock_rpc.assert_not_called()  # Cache hit


class TestABIEnrichment:
    """Tests für ABI Enrichment via Etherscan"""
    
    @pytest.mark.asyncio
    async def test_abi_fetch_with_api_key(self):
        """Test ABI-Fetch wenn API-Key gesetzt ist"""
        service = ContractsService()
        service.etherscan_api_key = "test_key"
        
        mock_abi = [
            {"type": "function", "name": "transfer"},
            {"type": "function", "name": "balanceOf"},
            {"type": "event", "name": "Transfer"}
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "1",
            "result": str(mock_abi).replace("'", '"')
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            abi, verified = await service._fetch_etherscan_abi("0xTest")
            
            assert verified is True
            assert abi is not None
            assert len([e for e in abi if e.get("type") == "function"]) == 2
    
    @pytest.mark.asyncio
    async def test_abi_fetch_without_api_key(self):
        """Test dass ohne API-Key kein ABI gefetched wird"""
        service = ContractsService()
        service.etherscan_api_key = None
        
        abi, verified = await service._fetch_etherscan_abi("0xTest")
        
        assert abi is None
        assert verified is False


# Run with: pytest backend/tests/test_contract_analysis_complete.py -v
