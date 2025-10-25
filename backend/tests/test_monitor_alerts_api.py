import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.auth.dependencies import get_current_user_strict
import asyncio
import app.api.v1.monitor as monitor_service_module

client = TestClient(app)


# Provide test auth override for endpoints requiring strict auth
@pytest.fixture(autouse=True)
def _auth_override():
    app.dependency_overrides[get_current_user_strict] = lambda: {
        "id": "test-user",
        "email": "test@example.com",
        "role": "admin",
    }
    yield
    app.dependency_overrides.pop(get_current_user_strict, None)


def test_list_alerts_monkeypatch(monkeypatch):
    async def fake_list_alerts(status=None, severity=None, limit=100):
        return [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "rule_id": "00000000-0000-0000-0000-0000000000aa",
                "entity_type": "address",
                "entity_id": "0xabc",
                "chain": "ethereum",
                "severity": "high",
                "status": status or "open",
                "assignee": None,
                "first_seen_at": "2025-01-01T00:00:00",
                "last_seen_at": "2025-01-01T01:00:00",
                "hits": 3,
                "context": {"matched": True},
            }
        ]

    monkeypatch.setattr(
        monitor_service_module.monitor_service, "list_alerts", fake_list_alerts
    )

    res = client.get("/api/v1/monitor/alerts?status=open&severity=high&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert data[0]["status"] == "open"
    assert data[0]["severity"] == "high"


def test_list_alerts_monkeypatch(monkeypatch):
    async def fake_list_alerts(status=None, severity=None, limit=100):
        return [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "rule_id": "00000000-0000-0000-0000-0000000000aa",
                "entity_type": "address",
                "entity_id": "0xabc",
                "chain": "ethereum",
                "severity": "high",
                "status": status or "open",
                "assignee": None,
                "first_seen_at": "2025-01-01T00:00:00",
                "last_seen_at": "2025-01-01T01:00:00",
                "hits": 3,
                "context": {"matched": True},
            }
        ]

    monkeypatch.setattr(
        monitor_service_module.monitor_service, "list_alerts", fake_list_alerts
    )

    res = client.get("/api/v1/monitor/alerts?status=open&severity=high&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert data[0]["status"] == "open"
    assert data[0]["severity"] == "high"


def test_update_alert_monkeypatch(monkeypatch):
    async def fake_update_alert(alert_id, *, status=None, assignee=None, note=None):
        return {
            "id": alert_id,
            "rule_id": "00000000-0000-0000-0000-0000000000aa",
            "entity_type": "address",
            "entity_id": "0xabc",
            "chain": "ethereum",
            "severity": "high",
            "status": status or "assigned",
            "assignee": assignee,
            "first_seen_at": "2025-01-01T00:00:00",
            "last_seen_at": "2025-01-01T01:00:00",
            "hits": 4,
            "context": {"note": note} if note else None,
        }

    monkeypatch.setattr(
        monitor_service_module.monitor_service, "update_alert", fake_update_alert
    )

    payload = {"status": "assigned", "assignee": None, "note": "Übernahme"}
    res = client.patch("/api/v1/monitor/alerts/00000000-0000-0000-0000-000000000001", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "assigned"
    assert data["context"]["note"] == "Übernahme"


def test_realtime_alerts_dedup_suppression():
    """Test that realtime alerts endpoint works with dedup suppression"""
    # Import alert_engine here to avoid circular imports
    from app.services.alert_engine import alert_engine

    # Create a test event that should trigger an alert
    test_event = {
        "address": "0x1234567890abcdef",
        "risk_score": 0.85,
        "risk_factors": ["test"],
    }

    # Process the event twice - second should be suppressed
    with patch.object(alert_engine, 'enable_dedup', True):
        with patch.object(alert_engine, 'dedup_window_seconds', 300):
            run = asyncio.get_event_loop().run_until_complete
            alerts1 = run(alert_engine.process_event(test_event))
            alerts2 = run(alert_engine.process_event(test_event))

            # First should create alert, second should be suppressed
            assert len(alerts1) == 1
            assert len(alerts2) == 0


def test_realtime_alerts_endpoint():
    """Test that the realtime alerts endpoint returns properly formatted data"""
    from app.services.alert_engine import alert_engine

    # Create a test alert
    test_alert = {
        "address": "0x1234567890abcdef",
        "risk_score": 0.85,
        "risk_factors": ["test"],
    }
    run = asyncio.get_event_loop().run_until_complete
    alerts = run(alert_engine.process_event(test_alert))

    # Test the realtime endpoint
    res = client.get("/api/v1/monitor/alerts/realtime?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:  # If there are alerts
        alert = data[0]
        assert "id" in alert
        assert "rule_id" in alert
        assert "entity_type" in alert
        assert "entity_id" in alert
        assert "severity" in alert
        assert "status" in alert


def test_realtime_alerts_with_severity_filter():
    """Test filtering realtime alerts by severity"""
    from app.services.alert_engine import alert_engine

    # Create alerts with different severities
    critical_event = {"address": "0x123", "risk_score": 0.95}
    medium_event = {"address": "0x456", "risk_score": 0.75}

    run = asyncio.get_event_loop().run_until_complete
    run(alert_engine.process_event(critical_event))
    run(alert_engine.process_event(medium_event))

    # Test filtering by severity
    res = client.get("/api/v1/monitor/alerts/realtime?severity=critical")
    assert res.status_code == 200
    data = res.json()
def test_suppression_events_endpoint():
    """Test that the suppression events endpoint returns properly formatted data"""
    from app.services.alert_engine import alert_engine

    # Create a test event that should trigger an alert and then get suppressed
    test_event = {
        "address": "0x1234567890abcdef",
        "risk_score": 0.85,
        "risk_factors": ["test"],
    }

    # Process the event twice - second should be suppressed
    run = asyncio.get_event_loop().run_until_complete
    alerts1 = run(alert_engine.process_event(test_event))
    alerts2 = run(alert_engine.process_event(test_event))

    # First should create alert, second should be suppressed
    assert len(alerts1) == 1
    assert len(alerts2) == 0

    # Check that suppression events were created
    suppression_events = alert_engine.get_suppression_events(limit=10)
    assert len(suppression_events) >= 1

    # Test the suppression events endpoint
    res = client.get("/api/v1/alerts/suppressions?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:  # If there are suppression events
        event = data[0]
        assert "alert_id" in event
        assert "alert_type" in event
        assert "reason" in event
        assert "fingerprint" in event
        assert "suppression_count" in event


def test_suppression_events_with_reason_filter():
    """Test filtering suppression events by reason"""
    from app.services.alert_engine import alert_engine

    # Get suppression events with reason filter
    res = client.get("/api/v1/alerts/suppressions?reason=dedup_window&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    for event in data:
        assert event["reason"] == "dedup_window"


def test_suppression_export():
    """Test exporting suppression events"""
    from app.services.alert_engine import alert_engine

    # Create some suppression events by triggering duplicate alerts
    test_event = {
        "address": "0x1234567890abcdef",
        "risk_score": 0.85,
        "risk_factors": ["test"],
    }

    # Process twice to create suppression
    run = asyncio.get_event_loop().run_until_complete
    run(alert_engine.process_event(test_event))
    run(alert_engine.process_event(test_event))  # This should be suppressed

    # Test JSON export
    json_export = alert_engine.export_suppression_events(format="json", limit=10)
    assert isinstance(json_export, str)

    # Parse JSON to verify structure
    import json
    exported_data = json.loads(json_export)
    assert isinstance(exported_data, list)
    if exported_data:
        event = exported_data[0]
        assert "alert_id" in event
        assert "reason" in event

    # Test CSV export
    csv_export = alert_engine.export_suppression_events(format="csv", limit=10)
    assert isinstance(csv_export, str)
    assert "alert_id" in csv_export  # Should contain headers
    assert "reason" in csv_export


def test_suppression_statistics():
    """Test getting suppression statistics"""
    from app.services.alert_engine import alert_engine

    # Get statistics
    stats = alert_engine.get_suppression_statistics()

    # Verify structure
    assert "total_suppressions" in stats
    assert "suppressions_by_reason" in stats
    assert "suppressions_by_alert_type" in stats
    assert "top_suppressed_entities" in stats
    assert "suppression_rate" in stats

    # All should be valid types
    assert isinstance(stats["total_suppressions"], int)
    assert isinstance(stats["suppressions_by_reason"], dict)
    assert isinstance(stats["suppressions_by_alert_type"], dict)
    assert isinstance(stats["top_suppressed_entities"], list)
    assert isinstance(stats["suppression_rate"], (int, float))


def test_advanced_suppression_rules():
    """Test advanced suppression rules"""
    from app.services.alert_engine import alert_engine

    # Test global rate limiting
    alert_engine.suppression_rules["global"]["max_alerts_per_minute"] = 1

    # Create multiple alerts quickly
    test_event = {
        "address": "0x1111111111111111111111111111111111111111",
        "risk_score": 0.85,
    }

    run = asyncio.get_event_loop().run_until_complete
    alerts1 = run(alert_engine.process_event(test_event))
    alerts2 = run(alert_engine.process_event(test_event))  # Should be rate limited

    # First should create alert, second should be suppressed due to rate limit
    assert len(alerts1) >= 1
    assert len(alerts2) == 0  # Should be suppressed

    # Check that suppression events were created
    suppression_events = alert_engine.get_suppression_events(limit=10, reason="global_rate_limit")
    assert len(suppression_events) >= 1


def test_suppression_clear():
    """Test clearing suppression events"""
    from app.services.alert_engine import alert_engine

    # Create some suppression events first
    test_event = {"address": "0x2222222222222222222222222222222222222222", "risk_score": 0.85}
    run = asyncio.get_event_loop().run_until_complete
    run(alert_engine.process_event(test_event))
    run(alert_engine.process_event(test_event))  # Create suppression

    initial_count = len(alert_engine.suppression_events)
    assert initial_count > 0

    # Clear suppression events via API
    response = client.post("/api/v1/alerts/suppressions/clear")
    assert response.status_code == 200

    data = response.json()
    assert data["cleared_count"] == initial_count
    assert data["status"] == "success"

def test_correlation_rules_endpoint():
    """Test getting correlation rules"""
    response = client.get("/api/v1/alerts/correlation/rules")
    assert response.status_code == 200

    data = response.json()
    assert "rules" in data
    assert "total_rules" in data
    assert "supported_patterns" in data
    assert isinstance(data["rules"], dict)
    assert isinstance(data["total_rules"], int)


def test_correlation_test_endpoint():
    """Test testing correlation rules"""
    payload = {
        "rule_name": "flash_loan_exploit",
        "sample_alerts": [
            {
                "alert_type": "flash_loan_attack",
                "severity": "high",
                "title": "Flash Loan Attack",
                "address": "0x123",
                "tx_hash": "0xabc"
            },
            {
                "alert_type": "smart_contract_exploit",
                "severity": "critical",
                "title": "Contract Exploit",
                "address": "0x123",
                "tx_hash": "0xdef"
            }
        ]
    }

    response = client.post("/api/v1/alerts/correlation/test", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "rule_name" in data
    assert "matches" in data
    assert "rule_config" in data
    assert data["rule_name"] == "flash_loan_exploit"


def test_correlation_analysis_endpoint():
    """Test correlation analysis"""
    response = client.get("/api/v1/alerts/correlation/analysis?time_window=3600&min_severity=medium")
    assert response.status_code == 200

    data = response.json()
    assert "time_window_seconds" in data
    assert "min_severity" in data
    assert "total_alerts_analyzed" in data
    assert "correlations_found" in data
    assert "correlation_rate" in data
    assert data["time_window_seconds"] == 3600
    assert data["min_severity"] == "medium"


def test_extended_alert_rules_integration():
    """Test that extended alert rules are properly integrated"""
    from app.services.alert_engine import alert_engine

    # Check that all new rules are initialized
    rule_ids = [rule.rule_id for rule in alert_engine.rules]

    expected_new_rules = [
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

    for rule_id in expected_new_rules:
        assert rule_id in rule_ids, f"Extended rule {rule_id} not found"

    # Check correlation engine is initialized
    assert hasattr(alert_engine, 'correlation_engine')
    assert alert_engine.correlation_engine is not None

    # Check that correlation rules exist
    correlation_rules = alert_engine.correlation_engine.correlation_rules
    assert len(correlation_rules) > 0
    assert "flash_loan_exploit" in correlation_rules
    assert "money_laundering_chain" in correlation_rules


def test_anomaly_detection_with_ml_data():
    """Test anomaly detection rule with ML data"""
    from app.services.alert_engine import alert_engine

    # Test event with high anomaly score
    event = {
        "address": "0xanomaly1234567890abcdef",
        "anomaly_score": 0.95,
        "anomaly_factors": ["unusual_volume", "new_behavior_pattern"],
        "ml_model": "isolation_forest",
        "tx_hash": "0xanomaly_tx_123"
    }

    run = asyncio.get_event_loop().run_until_complete
    alerts = run(alert_engine.process_event(event))

    # Should create anomaly detection alert
    anomaly_alerts = [a for a in alerts if a.alert_type.value == "anomaly_detection"]
    assert len(anomaly_alerts) == 1

    alert = anomaly_alerts[0]
    assert alert.severity.value == "high"
    assert "Anomalie erkannt" in alert.title
    assert alert.metadata["anomaly_score"] == 0.95
    assert "unusual_volume" in alert.metadata["anomaly_factors"]


def test_smart_contract_exploit_detection():
    """Test smart contract exploit detection"""
    from app.services.alert_engine import alert_engine

    # Test event with exploit indicators
    event = {
        "contract_address": "0xexploit1234567890abcdef",
        "function_signature": "transferFrom(address,uint256)",
        "gas_used": 15000000,  # High gas usage
        "tx_hash": "0xexploit_tx_123"
    }

    run = asyncio.get_event_loop().run_until_complete
    alerts = run(alert_engine.process_event(event))

    # Should create smart contract exploit alert
    exploit_alerts = [a for a in alerts if a.alert_type.value == "smart_contract_exploit"]
    assert len(exploit_alerts) == 1

    alert = exploit_alerts[0]
    assert alert.severity.value == "critical"
    assert "Smart Contract Exploit Verdacht" in alert.title
    assert "gas_used" in alert.metadata
    assert alert.metadata["gas_used"] == 15000000


def test_whale_movement_detection():
    """Test whale movement detection"""
    from app.services.alert_engine import alert_engine

    # Add a whale address to the rule
    whale_rule = None
    for rule in alert_engine.rules:
        if rule.rule_id == "whale_movement":
            whale_rule = rule
            whale_rule.whale_addresses.add("0xwhale1234567890abcdef")
            break

    assert whale_rule is not None

    # Test event with whale movement
    event = {
        "from_address": "0xwhale1234567890abcdef",
        "to_address": "0xnormal1234567890abcdef",
        "value_usd": 2000000
    }

    run = asyncio.get_event_loop().run_until_complete
    alerts = run(alert_engine.process_event(event))

    # Should create whale movement alert
    whale_alerts = [a for a in alerts if a.alert_type.value == "whale_movement"]
    assert len(whale_alerts) == 1

    alert = whale_alerts[0]
    assert alert.severity.value == "high"
    assert "bekannter Whale" in alert.description


def test_flash_loan_attack_detection():
    """Test flash loan attack detection"""
    from app.services.alert_engine import alert_engine

    # Test event with flash loan indicators
    event = {
        "value_usd": 5000000,
        "flash_loan_indicators": ["rapid_borrow_return", "price_manipulation"],
        "loan_duration_seconds": 60,
        "profit_extracted": 100000,
        "tx_hash": "0xflash_tx_123"
    }

    run = asyncio.get_event_loop().run_until_complete
    alerts = run(alert_engine.process_event(event))

    # Should create flash loan attack alert
    flash_alerts = [a for a in alerts if a.alert_type.value == "flash_loan_attack"]
    assert len(flash_alerts) == 1

    alert = flash_alerts[0]
    assert alert.severity.value == "critical"
    assert "Flash Loan Attack Verdacht" in alert.title
    assert alert.metadata["profit_extracted"] == 100000


def test_money_laundering_pattern_detection():
    """Test money laundering pattern detection"""
    from app.services.alert_engine import alert_engine

    # Test layering pattern
    event = {
        "layering_count": 8,
        "total_volume_usd": 500000,
        "involved_addresses": ["0xaddr1", "0xaddr2", "0xaddr3"],
        "address": "0xlaundering1234567890abcdef"
    }

    run = asyncio.get_event_loop().run_until_complete
    alerts = run(alert_engine.process_event(event))

    # Should create money laundering alert
    ml_alerts = [a for a in alerts if a.alert_type.value == "money_laundering_pattern"]
    assert len(ml_alerts) == 1

    alert = ml_alerts[0]
    assert alert.severity.value == "high"
    assert "Money Laundering Pattern: layering" in alert.title


def test_rug_pull_detection():
    """Test rug pull detection"""
    from app.services.alert_engine import alert_engine

    # Test event with rug pull indicators
    event = {
        "token_address": "0xscam1234567890abcdef",
        "liquidity_removed_percentage": 0.95,
        "developer_wallet_percentage": 0.15,
        "rug_pull_indicators": ["sudden_liquidity_removal", "team_dump"],
        "contract_address": "0xcontract1234567890abcdef"
    }

    run = asyncio.get_event_loop().run_until_complete
    alerts = run(alert_engine.process_event(event))

    # Should create rug pull alert
    rug_alerts = [a for a in alerts if a.alert_type.value == "rug_pull"]
    assert len(rug_alerts) == 1

    alert = rug_alerts[0]
    assert alert.severity.value == "critical"
    assert "Rug Pull Verdacht" in alert.title


def test_get_recent_alerts():
    """Test getting recent alerts from Alert Engine"""
    res = client.get("/api/v1/alerts/recent?limit=10&severity=high")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_get_alert_stats():
    """Test getting alert statistics"""
    res = client.get("/api/v1/alerts/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_alerts" in data
    assert "by_severity" in data
    assert "by_type" in data
    assert "unacknowledged" in data


def test_acknowledge_alert():
    """Test acknowledging an alert"""
    # First create a test alert
    test_event = {
        "address": "0x0000000000000000000000000000000000000000",
        "risk_score": 0.95,
        "risk_factors": ["Test alert"],
        "labels": ["test"]
    }

    # Process the event to create an alert
    res = client.post("/api/v1/alerts/test")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "test_alert_triggered"

    # Get the alert ID
    alert_id = data["alert_ids"][0] if data["alert_ids"] else "test_alert_id"

    # Acknowledge the alert
    res = client.post(f"/api/v1/alerts/acknowledge/{alert_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "acknowledged"


def test_process_event_batch():
    """Test batch processing of events"""
    events = [
        {
            "entity_id": "test_entity_1",
            "address": "0x1234567890123456789012345678901234567890",
            "risk_score": 0.9,
            "chain": "ethereum"
        },
        {
            "entity_id": "test_entity_2",
            "address": "0x0987654321098765432109876543210987654321",
            "risk_score": 0.8,
            "chain": "ethereum"
        }
    ]

    res = client.post("/api/v1/alerts/process-batch", json={"events": events})
    assert res.status_code == 200
    data = res.json()
    assert "processed_events" in data
    assert "alerts_created" in data
    assert data["processed_events"] == 2
