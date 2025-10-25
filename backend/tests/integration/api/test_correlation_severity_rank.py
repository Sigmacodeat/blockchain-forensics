from app.services.alert_engine import AlertCorrelationEngine, Alert, AlertType, AlertSeverity
from datetime import datetime


def make_alert(alert_type: AlertType, severity: AlertSeverity) -> Alert:
    a = Alert(
        alert_type=alert_type,
        severity=severity,
        title="t",
        description="d",
        metadata={},
        address="0x1",
        tx_hash="0x2",
    )
    # force recent timestamp
    a.timestamp = datetime.utcnow()
    return a


def test_min_severity_filter_blocks_lower_alerts():
    eng = AlertCorrelationEngine()
    rule = {
        "patterns": ["flash_loan_attack", "smart_contract_exploit"],
        "time_window": 300,
        "min_severity": "high",
    }
    low_alert = make_alert(AlertType.FLASH_LOAN_ATTACK, AlertSeverity.MEDIUM)
    recent = [make_alert(AlertType.SMART_CONTRACT_EXPLOIT, AlertSeverity.CRITICAL)]

    assert eng._matches_correlation_rule(low_alert, recent, rule) is False


def test_min_severity_allows_equal_or_higher():
    eng = AlertCorrelationEngine()
    rule = {
        "patterns": ["flash_loan_attack", "smart_contract_exploit"],
        "time_window": 300,
        "min_severity": "high",
    }
    high_alert = make_alert(AlertType.FLASH_LOAN_ATTACK, AlertSeverity.HIGH)
    recent = [make_alert(AlertType.SMART_CONTRACT_EXPLOIT, AlertSeverity.HIGH)]

    assert eng._matches_correlation_rule(high_alert, recent, rule) is True
