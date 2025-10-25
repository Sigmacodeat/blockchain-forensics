import asyncio
import sys
import types
import pytest

from app.services.alert_engine import AlertEngine, AlertSeverity, AlertType


@pytest.fixture()
def engine():
    eng = AlertEngine()
    # make deterministic for tests
    eng.enable_dedup = True
    eng.dedup_window_seconds = 300
    try:
        eng._testing_mode = True  # relax certain suppression in tests
    except Exception:
        pass
    yield eng
    try:
        eng.reset_state()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def mock_notifications(monkeypatch):
    # Provide dummy async services to avoid external calls
    email_mod = types.SimpleNamespace()
    slack_mod = types.SimpleNamespace()
    webhook_mod = types.SimpleNamespace()

    async def _email_send_alert(**kwargs):
        return True

    async def _slack_send_alert(**kwargs):
        return True

    # default webhook succeeds; tests can override via monkeypatch
    async def _webhook_send_webhook(**kwargs):
        return True

    email_mod.send_alert = _email_send_alert
    slack_mod.send_alert = _slack_send_alert
    webhook_mod.send_webhook = _webhook_send_webhook

    sys.modules['app.notifications.email_service'] = types.SimpleNamespace(email_service=email_mod)
    sys.modules['app.notifications.slack_service'] = types.SimpleNamespace(slack_service=slack_mod)
    sys.modules['app.services.webhook_service'] = types.SimpleNamespace(webhook_service=webhook_mod)

    yield


@pytest.mark.asyncio
async def test_rule_hit_high_risk(engine: AlertEngine):
    event = {
        "address": "0xdeadbeef00000000000000000000000000000001",
        "risk_score": 0.95,
        "timestamp": "2025-01-01T00:00:00Z",
    }
    engine.enable_dedup = False
    alerts = await engine.process_event(event)
    assert len(alerts) >= 1
    assert any(a.alert_type == AlertType.HIGH_RISK_ADDRESS for a in alerts)


@pytest.mark.asyncio
async def test_dedup_suppression(engine: AlertEngine):
    engine.enable_dedup = True
    engine.dedup_window_seconds = 300
    event = {
        "address": "0xdeadbeef0000000000000000000000000000cafe",
        "risk_score": 0.95,
        "timestamp": "2025-01-01T00:00:00Z",
    }
    alerts1 = await engine.process_event(event)
    alerts2 = await engine.process_event(event)
    # First triggers, second should be dedup-suppressed
    assert len(alerts1) >= 1
    assert len(alerts2) == 0
    assert any(se.reason in ("dedup_window", "global_rate_limit", "rule_suppression", "entity_suppression") for se in engine.suppression_events)


@pytest.mark.asyncio
async def test_process_event_batch(engine: AlertEngine):
    events = [
        {"address": "0x111", "risk_score": 0.95, "timestamp": "2025-01-01T00:00:00Z"},
        {"address": "0x222", "value_usd": 250000, "tx_hash": "0xabc", "timestamp": "2025-01-01T00:00:00Z"},
        {"address": "0x333", "risk_score": 0.1, "timestamp": "2025-01-01T00:00:00Z"},
    ]
    engine.enable_dedup = False
    alerts = await engine.process_event_batch(events)
    # Expect at least one alert (high risk or large transfer)
    assert len(alerts) >= 1


@pytest.mark.asyncio
async def test_webhook_error_handled(engine: AlertEngine, monkeypatch):
    # Force webhook error path by patching the actual webhook service module used inside alert_engine
    from app.services import webhook_service as wh_mod
    async def _fail_webhook(**kwargs):
        raise RuntimeError("webhook down")
    wh_mod.webhook_service.send_webhook = _fail_webhook  # type: ignore[attr-defined]

    event = {"address": "0x444", "risk_score": 0.99, "timestamp": "2025-01-01T00:00:00Z"}
    engine.enable_dedup = False
    alerts = await engine.process_event(event)
    # Alert should still be created despite webhook failure
    assert len(alerts) >= 1
    assert any(a.alert_type == AlertType.HIGH_RISK_ADDRESS for a in alerts)
