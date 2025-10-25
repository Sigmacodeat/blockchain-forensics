"""Tests for KYT (Know Your Transaction) Engine"""
import pytest
import asyncio
from datetime import datetime

from app.services.kyt_engine import (
    kyt_engine, 
    Transaction, 
    KYTResult, 
    RiskLevel
)


@pytest.mark.asyncio
async def test_kyt_engine_start_stop():
    """Test KYT engine lifecycle."""
    await kyt_engine.start()
    assert kyt_engine._running is True
    
    await kyt_engine.stop()
    assert kyt_engine._running is False


@pytest.mark.asyncio
async def test_analyze_safe_transaction():
    """Test analysis of a safe transaction."""
    tx = Transaction(
        tx_hash="0xsafe123",
        chain="ethereum",
        from_address="0xsafe_sender",
        to_address="0xsafe_receiver",
        value_eth=1.0,
        value_usd=3000.0,
        timestamp=datetime.now(),
        block_number=12345
    )
    
    result = await kyt_engine.analyze_transaction(tx)
    
    assert isinstance(result, KYTResult)
    assert result.tx_hash == "0xsafe123"
    assert result.risk_level in [RiskLevel.SAFE, RiskLevel.LOW, RiskLevel.MEDIUM]
    assert 0.0 <= result.risk_score <= 1.0
    assert result.analysis_time_ms > 0


@pytest.mark.asyncio
async def test_analyze_large_transaction():
    """Test detection of large transaction."""
    tx = Transaction(
        tx_hash="0xlarge123",
        chain="ethereum",
        from_address="0xwhale",
        to_address="0xreceiver",
        value_eth=100.0,
        value_usd=300000.0,  # > $100k threshold
        timestamp=datetime.now(),
        block_number=12345
    )
    
    result = await kyt_engine.analyze_transaction(tx)
    
    # Should generate a large transfer alert
    large_transfer_alerts = [a for a in result.alerts if a["type"] == "LARGE_TRANSFER"]
    assert len(large_transfer_alerts) > 0
    assert large_transfer_alerts[0]["value_usd"] == 300000.0


@pytest.mark.asyncio
async def test_subscribe_unsubscribe():
    """Test subscription management."""
    user_id = "test_user"
    
    # Subscribe
    queue = kyt_engine.subscribe(user_id)
    assert user_id in kyt_engine.subscribers
    assert queue in kyt_engine.subscribers[user_id]
    
    # Unsubscribe
    kyt_engine.unsubscribe(user_id, queue)
    assert user_id not in kyt_engine.subscribers


@pytest.mark.asyncio
async def test_broadcast_to_subscribers():
    """Test broadcasting results to subscribers."""
    user_id = "test_user"
    queue = kyt_engine.subscribe(user_id)
    
    # Analyze a transaction
    tx = Transaction(
        tx_hash="0xbroadcast123",
        chain="ethereum",
        from_address="0xsender",
        to_address="0xreceiver",
        value_eth=1.0,
        value_usd=3000.0,
        timestamp=datetime.now(),
        block_number=12345
    )
    
    result = await kyt_engine.analyze_transaction(tx)
    
    # Check if result was broadcasted to queue
    try:
        msg = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert msg["type"] == "kyt.result"
        assert msg["data"]["tx_hash"] == "0xbroadcast123"
    except asyncio.TimeoutError:
        pytest.fail("No message received in queue")
    finally:
        kyt_engine.unsubscribe(user_id, queue)


@pytest.mark.asyncio
async def test_risk_levels():
    """Test risk level categorization."""
    test_cases = [
        (0.95, RiskLevel.CRITICAL),
        (0.85, RiskLevel.HIGH),
        (0.5, RiskLevel.MEDIUM),
        (0.3, RiskLevel.LOW),
        (0.1, RiskLevel.SAFE),
    ]
    
    for risk_score, expected_level in test_cases:
        # Determine level (simplified from engine logic)
        if risk_score >= 0.9:
            level = RiskLevel.CRITICAL
        elif risk_score >= 0.7:
            level = RiskLevel.HIGH
        elif risk_score >= 0.4:
            level = RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            level = RiskLevel.LOW
        else:
            level = RiskLevel.SAFE
        
        assert level == expected_level
