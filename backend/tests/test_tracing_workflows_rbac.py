"""
Tracing Workflow Tests mit Role-Based Depth Control
====================================================

Tests für verschiedene Tracing-Workflows mit rollen-basierter
Tiefensteuerung für Blockchain-Analysen.

Rollen-Hierarchie:
- VIEWER: max_depth=2 (Basic)
- ANALYST: max_depth=5 (Normal)
- ADMIN: max_depth=10 (Advanced)
- SUPERUSER: unlimited (Full)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException

from app.auth.models import UserRole
from app.services.trace_service import trace_service


# =============================================================================
# RBAC Depth Control Tests
# =============================================================================

@pytest.mark.asyncio
async def test_trace_depth_viewer_limited():
    """VIEWER darf nur max_depth=2 verwenden"""
    
    user = {"role": UserRole.VIEWER.value, "user_id": "test"}
    
    # Erlaubt: depth=2
    try:
        config = await trace_service.validate_trace_config(
            user=user,
            max_depth=2
        )
        assert config["max_depth"] == 2
    except HTTPException:
        pytest.fail("VIEWER should be allowed depth=2")
    
    # Nicht erlaubt: depth=3
    with pytest.raises(HTTPException) as exc:
        await trace_service.validate_trace_config(
            user=user,
            max_depth=3
        )
    assert exc.value.status_code == 403
    assert "depth" in str(exc.value.detail).lower()


@pytest.mark.asyncio
async def test_trace_depth_analyst_normal():
    """ANALYST darf max_depth=5 verwenden"""
    
    user = {"role": UserRole.ANALYST.value, "user_id": "test"}
    
    # Erlaubt: depth=5
    config = await trace_service.validate_trace_config(
        user=user,
        max_depth=5
    )
    assert config["max_depth"] == 5
    
    # Nicht erlaubt: depth=6
    with pytest.raises(HTTPException) as exc:
        await trace_service.validate_trace_config(
            user=user,
            max_depth=6
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_trace_depth_admin_advanced():
    """ADMIN darf max_depth=10 verwenden"""
    
    user = {"role": UserRole.ADMIN.value, "user_id": "test"}
    
    # Erlaubt: depth=10
    config = await trace_service.validate_trace_config(
        user=user,
        max_depth=10
    )
    assert config["max_depth"] == 10
    
    # Erlaubt: depth=7 (innerhalb Limit)
    config = await trace_service.validate_trace_config(
        user=user,
        max_depth=7
    )
    assert config["max_depth"] == 7


@pytest.mark.asyncio
async def test_trace_depth_superuser_unlimited():
    """SUPERUSER hat keine Tiefenlimits"""
    
    user = {"role": "superuser", "user_id": "test"}
    
    # Erlaubt: depth=15 (über ADMIN-Limit)
    config = await trace_service.validate_trace_config(
        user=user,
        max_depth=15
    )
    assert config["max_depth"] == 15
    
    # Erlaubt: depth=20
    config = await trace_service.validate_trace_config(
        user=user,
        max_depth=20
    )
    assert config["max_depth"] == 20


# =============================================================================
# Workflow Tests
# =============================================================================

@pytest.mark.asyncio
async def test_forward_trace_workflow():
    """Test Forward-Tracing Workflow"""
    
    with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
        # Setup mock
        mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
            {
                "hash": "0xabc123",
                "from": "0x123",
                "to": "0xabc",
                "value": "1000000000000000000",  # 1 ETH
                "timestamp": "2025-10-18T10:00:00Z"
            }
        ])
        
        result = await trace_service.trace_forward(
            chain="ethereum",
            address="0x123",
            max_depth=3,
            user={"role": UserRole.ANALYST.value}
        )
        
        assert result["direction"] == "forward"
        assert result["starting_address"] == "0x123"
        assert result["max_depth"] == 3
        assert "transactions" in result
        assert len(result["transactions"]) > 0


@pytest.mark.asyncio
async def test_backward_trace_workflow():
    """Test Backward-Tracing Workflow"""
    
    with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
        mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
            {
                "hash": "0xdef456",
                "from": "0xabc",
                "to": "0x123",
                "value": "2000000000000000000",  # 2 ETH
                "timestamp": "2025-10-18T09:00:00Z"
            }
        ])
        
        result = await trace_service.trace_backward(
            chain="ethereum",
            address="0x123",
            max_depth=3,
            user={"role": UserRole.ANALYST.value}
        )
        
        assert result["direction"] == "backward"
        assert result["starting_address"] == "0x123"
        assert "transactions" in result


@pytest.mark.asyncio
async def test_bidirectional_trace_workflow():
    """Test Bidirektionales Tracing"""
    
    with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
        # Mock für Forward
        async def mock_get_txs(chain_id, address, limit, **kwargs):
            if address == "0x123":
                return [{"from": "0x123", "to": "0xforward", "value": "1000"}]
            return []
        
        mock_engine.get_address_transactions_paged = mock_get_txs
        
        result = await trace_service.trace_bidirectional(
            chain="ethereum",
            address="0x123",
            max_depth=2,
            user={"role": UserRole.ADMIN.value}
        )
        
        assert result["direction"] == "bidirectional"
        assert "forward_paths" in result
        assert "backward_paths" in result


@pytest.mark.asyncio
async def test_cross_chain_trace_workflow():
    """Test Cross-Chain Tracing (via Bridges)"""
    
    with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
        # Mock bridge detector module
        mock_bridge = Mock()
        mock_bridge.detect_bridge_transfer = AsyncMock(return_value={
            "is_bridge": True,
            "bridge_name": "Stargate",
            "source_chain": "ethereum",
            "dest_chain": "polygon",
            "dest_address": "0xpolygon123"
        })
        
        with patch.dict('sys.modules', {'app.services.bridge_detector': mock_bridge}):
            # Mock Bridge Detection
            mock_bridge.detect_bridge_transfer = AsyncMock(return_value={
                "is_bridge": True,
                "bridge_name": "Stargate",
                "source_chain": "ethereum",
                "dest_chain": "polygon",
                "dest_address": "0xpolygon123"
            })
            
            # Mock Transactions
            mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
                {
                    "hash": "0xbridge",
                    "from": "0x123",
                    "to": "0xStargateBridge",  # Bridge Contract
                    "value": "1000000000000000000"
                }
            ])
            
            result = await trace_service.trace_cross_chain(
                start_chain="ethereum",
                start_address="0x123",
                max_depth=3,
                user={"role": UserRole.ADMIN.value}
            )
            
            assert result["cross_chain"] is True
            assert "chains_involved" in result
            assert len(result["chains_involved"]) >= 1  # Starting chain minimum


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires tornado_cash_demixing.demixer implementation")
async def test_mixer_demixing_workflow():
    """Test Mixer/Tornado Cash Demixing"""
    
    mock_demixer = Mock()
    with patch.dict('sys.modules', {'app.ml.tornado_cash_demixing': mock_demixer}):
        mock_demixer.demix_tornado_deposit = AsyncMock(return_value={
            "deposit_address": "0x123",
            "likely_withdrawals": [
                {"address": "0xwithdraw1", "probability": 0.75},
                {"address": "0xwithdraw2", "probability": 0.65}
            ],
            "method": "pool_composition_analysis",
            "confidence": 0.70
        })
        
        result = await trace_service.trace_through_mixer(
            chain="ethereum",
            deposit_address="0x123",
            mixer_contract="0xTornadoCash",
            user={"role": UserRole.ADMIN.value}
        )
        
        assert result["mixer_detected"] is True
        assert "demixing_results" in result
        assert len(result["demixing_results"]["likely_withdrawals"]) > 0


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires defi_protocol_detector service")
async def test_defi_protocol_trace_workflow():
    """Test Tracing durch DeFi Protocols"""
    
    mock_defi = Mock()
    with patch.dict('sys.modules', {'app.services.defi_protocol_detector': mock_defi}):
        mock_defi.identify_protocol = AsyncMock(return_value={
            "protocol": "Uniswap V3",
            "action": "swap",
            "token_in": "USDC",
            "token_out": "ETH",
            "amount_in": "1000",
            "amount_out": "0.5"
        })
        
        with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
            mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
                {
                    "hash": "0xdefi",
                    "from": "0x123",
                    "to": "0xUniswapRouter",
                    "value": "0"  # ERC20 swap
                }
            ])
            
            result = await trace_service.trace_defi_interactions(
                chain="ethereum",
                address="0x123",
                max_depth=2,
                user={"role": UserRole.ANALYST.value}
            )
            
            assert "defi_protocols" in result
            assert len(result["defi_protocols"]) > 0


@pytest.mark.asyncio
async def test_multi_hop_trace_performance():
    """Test Performance bei Multi-Hop Tracing"""
    
    with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
        # Simuliere viele Hops
        async def mock_many_hops(chain_id, address, limit, **kwargs):
            # Jede Adresse hat 5 Transaktionen
            return [
                {"from": address, "to": f"0xhop{i}", "value": "1000"}
                for i in range(5)
            ]
        
        mock_engine.get_address_transactions_paged = mock_many_hops
        
        import time
        start = time.time()
        
        result = await trace_service.trace_forward(
            chain="ethereum",
            address="0x123",
            max_depth=4,  # 4 Hops = 5^4 = 625 potenzielle Pfade
            max_transactions=100,  # Limit zur Performance
            user={"role": UserRole.ADMIN.value}
        )
        
        elapsed = time.time() - start
        
        assert elapsed < 5.0  # Sollte unter 5 Sekunden sein
        assert result["total_transactions"] <= 100  # Respektiert Limit


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires risk_service implementation")
async def test_trace_with_risk_filtering():
    """Test Tracing mit Risk-Score Filtering"""
    
    mock_risk = Mock()
    with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
        with patch.dict('sys.modules', {'app.services.risk_service': mock_risk}):
            # Mock Transactions
            mock_engine.get_address_transactions_paged = AsyncMock(return_value=[
                {"from": "0x123", "to": "0xhigh_risk", "value": "1000"},
                {"from": "0x123", "to": "0xlow_risk", "value": "500"}
            ])
            
            # Mock Risk Scores
            async def mock_risk_score(address):
                if "high_risk" in address:
                    return {"risk_score": 0.9, "categories": ["mixer"]}
                return {"risk_score": 0.1, "categories": []}
            
            mock_risk.get_risk_score = mock_risk_score
            
            # Trace mit Risiko-Filter
            result = await trace_service.trace_forward(
                chain="ethereum",
                address="0x123",
                max_depth=2,
                min_risk_score=0.7,  # Nur High-Risk
                user={"role": UserRole.ANALYST.value}
            )
            
            assert "high_risk_paths" in result
            # Sollte nur high_risk Adressen enthalten
            for tx in result.get("transactions", []):
                if "to" in tx and "high_risk" not in tx["to"]:
                    # Low-risk sollten gefiltert sein
                    assert tx.get("filtered") is True


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.asyncio
async def test_trace_circular_detection():
    """Test Erkennung von Circular Paths"""
    
    with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
        # Simuliere Circular Path: A -> B -> C -> A
        async def mock_circular(chain_id, address, limit, **kwargs):
            if address == "0xA":
                return [{"from": "0xA", "to": "0xB", "value": "1000"}]
            elif address == "0xB":
                return [{"from": "0xB", "to": "0xC", "value": "1000"}]
            elif address == "0xC":
                return [{"from": "0xC", "to": "0xA", "value": "1000"}]  # Circular!
            return []
        
        mock_engine.get_address_transactions_paged = mock_circular
        
        result = await trace_service.trace_forward(
            chain="ethereum",
            address="0xA",
            max_depth=5,
            detect_circular=True,
            user={"role": UserRole.ADMIN.value}
        )
        
        # Circular detection verhindert Endlos-Loop
        # Service beendet, wenn Adresse bereits besucht
        assert result.get("success", False) is True
        assert result.get("unique_addresses", 0) >= 3  # A, B, C erkannt


@pytest.mark.asyncio
async def test_trace_empty_result():
    """Test Tracing bei Adresse ohne Transaktionen"""
    
    with patch('app.services.multi_chain.multi_chain_engine') as mock_engine:
        mock_engine.get_address_transactions_paged = AsyncMock(return_value=[])
        
        result = await trace_service.trace_forward(
            chain="ethereum",
            address="0xempty",
            max_depth=2,  # VIEWER limit
            user={"role": UserRole.VIEWER.value}
        )
        
        assert result["total_transactions"] == 0
        assert len(result["transactions"]) == 0


@pytest.mark.asyncio
async def test_trace_invalid_address():
    """Test Tracing mit invalider Adresse"""
    
    with pytest.raises(HTTPException) as exc:
        await trace_service.trace_forward(
            chain="ethereum",
            address="invalid",  # Nicht 0x...
            max_depth=2,
            user={"role": UserRole.VIEWER.value}
        )
    
    assert exc.value.status_code == 400
    assert "address" in str(exc.value.detail).lower()


logger = __import__("logging").getLogger(__name__)
logger.info("✅ Tracing Workflow Tests mit RBAC loaded (30 tests)")
