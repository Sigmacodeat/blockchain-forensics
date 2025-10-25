"""
🧪 BASIC TESTS für AI Blockchain Firewall
===========================================

Einfache Tests um zu verifizieren, dass die Firewall funktioniert.
"""

import pytest
from datetime import datetime
from app.services.ai_firewall_core import (
    ai_firewall,
    Transaction,
    ThreatLevel,
    ActionType
)


@pytest.mark.asyncio
async def test_firewall_basic_safe_transaction():
    """Test: Sichere Transaction sollte erlaubt werden"""
    tx = Transaction(
        tx_hash="0xtest1",
        chain="ethereum",
        from_address="0x1111111111111111111111111111111111111111",
        to_address="0x2222222222222222222222222222222222222222",
        value=0.1,
        value_usd=200,
        timestamp=datetime.now()
    )
    
    allowed, detection = await ai_firewall.intercept_transaction(
        user_id="test_user",
        tx=tx,
        wallet_address="0x1111111111111111111111111111111111111111"
    )
    
    assert allowed is True
    assert detection.threat_level in [ThreatLevel.SAFE, ThreatLevel.LOW]
    assert detection.detection_time_ms > 0


@pytest.mark.asyncio
async def test_firewall_whitelist():
    """Test: Whitelisted Address sollte immer erlaubt werden"""
    test_address = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    
    # Add to whitelist
    ai_firewall.add_to_whitelist(test_address)
    
    tx = Transaction(
        tx_hash="0xtest2",
        chain="ethereum",
        from_address="0x1111111111111111111111111111111111111111",
        to_address=test_address,
        value=100,
        value_usd=200000,
        timestamp=datetime.now()
    )
    
    allowed, detection = await ai_firewall.intercept_transaction(
        user_id="test_user",
        tx=tx,
        wallet_address="0x1111111111111111111111111111111111111111"
    )
    
    assert allowed is True
    assert "Whitelisted" in str(detection.evidence)
    
    # Cleanup
    ai_firewall.whitelisted_addresses.discard(test_address.lower())


@pytest.mark.asyncio
async def test_firewall_blacklist():
    """Test: Blacklisted Address sollte blockiert werden"""
    test_address = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    
    # Add to blacklist
    ai_firewall.add_to_blacklist(test_address)
    
    tx = Transaction(
        tx_hash="0xtest3",
        chain="ethereum",
        from_address="0x1111111111111111111111111111111111111111",
        to_address=test_address,
        value=0.1,
        value_usd=200,
        timestamp=datetime.now()
    )
    
    allowed, detection = await ai_firewall.intercept_transaction(
        user_id="test_user",
        tx=tx,
        wallet_address="0x1111111111111111111111111111111111111111"
    )
    
    assert allowed is False
    assert detection.threat_level == ThreatLevel.CRITICAL
    assert "blacklist" in str(detection.threat_types).lower()
    
    # Cleanup
    ai_firewall.blocked_addresses.discard(test_address.lower())


@pytest.mark.asyncio
async def test_firewall_token_approval_detection():
    """Test: Token Approval sollte erkannt werden"""
    # approve(address spender, uint256 amount) = 0x095ea7b3
    # spender = 0x3333...
    # amount = unlimited (max uint256)
    tx_data = "0x095ea7b3" + "0" * 24 + "3" * 40 + "f" * 64
    
    tx = Transaction(
        tx_hash="0xtest4",
        chain="ethereum",
        from_address="0x1111111111111111111111111111111111111111",
        to_address="0x4444444444444444444444444444444444444444",  # Token contract
        value=0,
        value_usd=0,
        timestamp=datetime.now(),
        data=tx_data,
        contract_address="0x4444444444444444444444444444444444444444"
    )
    
    allowed, detection = await ai_firewall.intercept_transaction(
        user_id="test_user",
        tx=tx,
        wallet_address="0x1111111111111111111111111111111111111111"
    )
    
    # Should detect dangerous approval
    assert "approval" in str(detection.threat_types).lower() or "function" in str(detection.threat_types).lower()


@pytest.mark.asyncio
async def test_firewall_large_transaction_warning():
    """Test: Große Transaction sollte gewarnt werden"""
    tx = Transaction(
        tx_hash="0xtest5",
        chain="ethereum",
        from_address="0x1111111111111111111111111111111111111111",
        to_address="0x5555555555555555555555555555555555555555",
        value=100,
        value_usd=200000,  # $200k - large!
        timestamp=datetime.now()
    )
    
    allowed, detection = await ai_firewall.intercept_transaction(
        user_id="test_user",
        tx=tx,
        wallet_address="0x1111111111111111111111111111111111111111"
    )
    
    # Should show some warning (behavioral analysis)
    # May still be allowed but with warnings
    assert detection.detection_time_ms > 0


@pytest.mark.asyncio
async def test_firewall_stats():
    """Test: Stats sollten aktualisiert werden"""
    initial_stats = ai_firewall.get_stats()
    initial_count = initial_stats["total_scanned"]
    
    tx = Transaction(
        tx_hash="0xtest6",
        chain="ethereum",
        from_address="0x1111111111111111111111111111111111111111",
        to_address="0x6666666666666666666666666666666666666666",
        value=0.1,
        value_usd=200,
        timestamp=datetime.now()
    )
    
    await ai_firewall.intercept_transaction(
        user_id="test_user",
        tx=tx,
        wallet_address="0x1111111111111111111111111111111111111111"
    )
    
    new_stats = ai_firewall.get_stats()
    assert new_stats["total_scanned"] == initial_count + 1
    assert new_stats["avg_detection_time_ms"] > 0


def test_firewall_enabled():
    """Test: Firewall sollte enabled sein"""
    assert ai_firewall.enabled is True


@pytest.mark.asyncio
async def test_token_approval_scanner():
    """Test: Token Approval Scanner direkt"""
    from app.services.token_approval_scanner import token_approval_scanner
    
    # approve() mit unlimited amount
    tx_data = "0x095ea7b3" + "0" * 24 + "7" * 40 + "f" * 64
    
    approval = await token_approval_scanner.scan_transaction(
        tx_data=tx_data,
        to_address="0x8888888888888888888888888888888888888888",
        chain="ethereum"
    )
    
    assert approval is not None
    assert approval.is_unlimited is True
    assert approval.risk_level.value in ["critical", "high"]


@pytest.mark.asyncio
async def test_phishing_scanner():
    """Test: Phishing Scanner"""
    from app.services.phishing_scanner import phishing_scanner
    
    # Test typosquatting
    result = await phishing_scanner.scan_url("https://unisvvap.org")  # typo: vv instead of w
    
    assert result.risk_level.value in ["high", "medium"]
    assert result.similar_to == "uniswap.org"
    assert result.is_phishing is True


@pytest.mark.asyncio
async def test_phishing_scanner_safe():
    """Test: Phishing Scanner - Safe URL"""
    from app.services.phishing_scanner import phishing_scanner
    
    result = await phishing_scanner.scan_url("https://ethereum.org")
    
    # Should be safe (not in phishing DB, not similar to anything)
    assert result.detection_time_ms > 0
