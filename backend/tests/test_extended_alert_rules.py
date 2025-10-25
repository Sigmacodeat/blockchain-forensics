"""
Tests for Extended Alert Rules
"""

import asyncio
from app.services.alert_engine import (
    AnomalyDetectionRule, SmartContractExploitRule, WhaleMovementRule,
    FlashLoanAttackRule, MoneyLaunderingPatternRule, CrossChainArbitrageRule,
    DarkWebConnectionRule, InsiderTradingRule, PonziSchemeRule, RugPullRule,
    AlertCorrelationEngine,
    Alert, AlertType, AlertSeverity
)


def _run(coro):
    """Run coroutine with a fresh event loop (safe in pytest threads)."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(asyncio.sleep(0))
        except Exception:
            pass
        loop.close()


def test_anomaly_detection_rule():
    """Test ML-basierte Anomalie-Erkennung"""
    rule = AnomalyDetectionRule()

    # High anomaly score should trigger alert
    event = {
        "address": "0x1234567890abcdef",
        "anomaly_score": 0.95,
        "anomaly_factors": ["unusual_volume", "new_behavior"],
        "ml_model": "isolation_forest"
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "anomaly_detection"
    assert alert.severity.value == "high"
    assert "Anomalie erkannt" in alert.title
    assert alert.metadata["anomaly_score"] == 0.95

    # Low anomaly score should not trigger
    event["anomaly_score"] = 0.3
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_smart_contract_exploit_rule():
    """Test Smart Contract Exploit Detection"""
    rule = SmartContractExploitRule()

    # High gas usage with exploit indicators should trigger
    event = {
        "contract_address": "0xabcdef1234567890",
        "function_signature": "transferFrom(address,uint256)",
        "gas_used": 15000000,
        "tx_hash": "0x1234567890abcdef"
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "smart_contract_exploit"
    assert alert.severity.value == "critical"
    assert "Exploit-Indikatoren gefunden" in alert.description

    # Normal gas usage should not trigger
    event["gas_used"] = 21000
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_whale_movement_rule():
    """Test Whale Movement Detection"""
    rule = WhaleMovementRule()
    rule.whale_addresses.add("0xwhale1234567890abcdef")

    # Whale movement should trigger
    event = {
        "from_address": "0xwhale1234567890abcdef",
        "to_address": "0xnormal1234567890abcdef",
        "value_usd": 2000000
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "whale_movement"
    assert alert.severity.value == "high"
    assert "bekannter Whale" in alert.description

    # Non-whale movement should not trigger
    event["from_address"] = "0xnormal1234567890abcdef"
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_flash_loan_attack_rule():
    """Test Flash Loan Attack Detection"""
    rule = FlashLoanAttackRule()

    # Flash loan attack indicators should trigger
    event = {
        "value_usd": 5000000,
        "flash_loan_indicators": ["rapid_borrow_return", "price_manipulation"],
        "loan_duration_seconds": 60,
        "profit_extracted": 100000,
        "tx_hash": "0xflash1234567890abcdef"
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "flash_loan_attack"
    assert alert.severity.value == "critical"
    assert "Flash Loan Attack Verdacht" in alert.title

    # Normal loan should not trigger
    event["loan_duration_seconds"] = 3600  # 1 hour
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_money_laundering_pattern_rule():
    """Test Money Laundering Pattern Detection"""
    rule = MoneyLaunderingPatternRule()

    # Layering pattern should trigger
    event = {
        "layering_count": 8,
        "total_volume_usd": 500000,
        "involved_addresses": ["0xaddr1", "0xaddr2", "0xaddr3"],
        "address": "0x1234567890abcdef"
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "money_laundering_pattern"
    assert alert.severity.value == "high"
    assert "Money Laundering Pattern: layering" in alert.title

    # Structuring pattern should also trigger
    event = {
        "structuring_indicators": ["equal_amounts", "frequent_small_tx"],
        "total_volume_usd": 15000,
        "address": "0xstructuring1234567890"
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert "structuring" in alert.title


def test_cross_chain_arbitrage_rule():
    """Test Cross-Chain Arbitrage Detection"""
    rule = CrossChainArbitrageRule()

    # Cross-chain arbitrage should trigger
    event = {
        "arbitrage_profit_usd": 25000,
        "chains_involved": ["ethereum", "polygon", "arbitrum"],
        "arbitrage_path": ["ETH", "USDC", "ARB"],
        "tokens_involved": ["0xa0b86a33e6c", "0xa0b86a33e6d"],
        "address": "0xarbitrage1234567890"
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "cross_chain_arbitrage"
    assert alert.severity.value == "medium"
    assert "Cross-Chain Arbitrage" in alert.title

    # Low profit should not trigger
    event["arbitrage_profit_usd"] = 500
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_dark_web_connection_rule():
    """Test Dark Web Connection Detection"""
    rule = DarkWebConnectionRule()

    # Dark web indicators should trigger
    event = {
        "address": "0xdarkweb1234567890abcdef",
        "labels": ["mixer", "tor", "anonymous"],
        "confidence_score": 0.85
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "dark_web_connection"
    assert alert.severity.value == "high"
    assert "Dark Web Verbindung" in alert.title

    # No dark web indicators should not trigger
    event["labels"] = ["exchange", "defi"]
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_insider_trading_rule():
    """Test Insider Trading Detection"""
    rule = InsiderTradingRule()

    # Insider trading pattern should trigger
    event = {
        "trade_value_usd": 500000,
        "volume_multiplier": 15,
        "insider_indicators": ["pre_announcement_volume", "wallet_cluster"],
        "token_address": "0xtoken1234567890abcdef",
        "exchange": "uniswap",
        "address": "0xinsider1234567890abcdef"
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "insider_trading"
    assert alert.severity.value == "high"
    assert "Insider Trading Verdacht" in alert.title

    # Normal trading should not trigger
    event["volume_multiplier"] = 2
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_ponzi_scheme_rule():
    """Test Ponzi Scheme Detection"""
    rule = PonziSchemeRule()

    # Ponzi indicators should trigger
    event = {
        "new_investors_24h": 150,
        "average_return_rate": 0.8,
        "ponzi_indicators": ["guaranteed_returns", "referral_bonus", "no_exit"],
        "contract_address": "0xponzi1234567890abcdef",
        "total_invested_usd": 1000000
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "ponzi_scheme"
    assert alert.severity.value == "critical"
    assert "Ponzi Scheme Verdacht" in alert.title

    # Legitimate investment should not trigger
    event["new_investors_24h"] = 5
    event["average_return_rate"] = 0.05
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_rug_pull_rule():
    """Test Rug Pull Detection"""
    rule = RugPullRule()

    # Rug pull indicators should trigger
    event = {
        "token_address": "0xcontract1234567890abcdef",
        "liquidity_removed_percentage": 0.95,
        "developer_wallet_percentage": 0.15,
        "rug_pull_indicators": ["sudden_liquidity_removal", "team_dump"],
        "contract_address": "0xcontract1234567890abcdef"
    }

    alert = _run(rule.evaluate(event))
    assert alert is not None
    assert alert.alert_type.value == "rug_pull"
    assert alert.severity.value == "critical"
    assert "Rug Pull Verdacht" in alert.title

    # Legitimate token should not trigger
    event["liquidity_removed_percentage"] = 0.1
    event["developer_wallet_percentage"] = 0.02
    event.pop("rug_pull_indicators", None)
    alert = _run(rule.evaluate(event))
    assert alert is None


def test_alert_correlation_engine():
    """Test Alert Correlation Engine"""
    engine = AlertCorrelationEngine()

    # Create test alerts
    # Use the Alert classes from alert_engine

    alert1 = Alert(
        alert_type=AlertType.FLASH_LOAN_ATTACK,
        severity=AlertSeverity.HIGH,
        title="Flash Loan Attack",
        description="Flash loan detected",
        metadata={},
        address="0x123",
        tx_hash="0xabc"
    )

    alert2 = Alert(
        alert_type=AlertType.SMART_CONTRACT_EXPLOIT,
        severity=AlertSeverity.CRITICAL,
        title="Smart Contract Exploit",
        description="Contract exploit detected",
        metadata={},
        address="0x123",
        tx_hash="0xdef"
    )

    # Test correlation
    correlated = engine.correlate_alerts(alert1, [alert2])

    # Should create correlated alert for flash loan exploit pattern
    assert correlated is not None
    assert correlated.alert_type.value == "suspicious_pattern"
    assert correlated.severity.value == "critical"
    assert "flash_loan_exploit" in correlated.metadata["correlation_rule"]


def test_rule_initialization():
    """Test that all rules are properly initialized"""
    from app.services.alert_engine import alert_engine

    # Check that all new rules are in the engine
    rule_types = [rule.rule_id for rule in alert_engine.rules]

    expected_rules = [
        "anomaly_detection",
        "smart_contract_exploit",
        "whale_movement",
        "flash_loan_attack",
        "money_laundering_pattern",
        "cross_chain_arbitrage",
        "dark_web_connection",
        "insider_trading",
        "ponzi_scheme",
        "rug_pull"
    ]

    for rule_type in expected_rules:
        assert rule_type in rule_types, f"Rule {rule_type} not found in initialized rules"


def test_correlation_engine_integration():
    """Test correlation engine integration with alert engine"""
    from app.services.alert_engine import alert_engine

    # Test that correlation engine is initialized
    assert hasattr(alert_engine, 'correlation_engine')
    assert alert_engine.correlation_engine is not None

    # Test correlation during alert processing
    event = {
        "address": "0x1234567890abcdef",
        "value_usd": 5000000,
        "flash_loan_indicators": ["rapid_borrow_return"],
        "loan_duration_seconds": 60,
        "profit_extracted": 100000
    }

    from app.services.alert_engine import alert_engine
    alerts = _run(alert_engine.process_event(event))

    # Should have processed the flash loan attack rule
    assert len(alerts) >= 1

    # Check that correlation engine was called (would need more setup for full test)
    # This is more of an integration test that the engine has the correlation capability
