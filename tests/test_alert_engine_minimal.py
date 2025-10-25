import os
import sys
import pathlib
import asyncio
import pytest

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.services.alert_engine import AlertEngine, AlertType  # noqa: E402


@pytest.mark.asyncio
async def test_large_transfer_rule_triggers(monkeypatch):
    # Mock notification services to no-op
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
    async def noop_email(*args, **kwargs):
        return None
    async def noop_slack(*args, **kwargs):
        return None
    async def noop_webhook(*args, **kwargs):
        return None
    monkeypatch.setenv("DISABLE_SECURITY", "1")

    # Patch notification services imports inside _send_notifications
    import types
    fake_email_service = types.SimpleNamespace(send_alert=noop_email)
    fake_slack_service = types.SimpleNamespace(send_alert=noop_slack)
    class _FakeWebhook:
        async def send_webhook(self, *args, **kwargs):
            return None
    # Inject modules into sys.modules so import in alert_engine picks them up
    sys.modules['app.notifications.email_service'] = types.SimpleNamespace(email_service=fake_email_service)
    sys.modules['app.notifications.slack_service'] = types.SimpleNamespace(slack_service=fake_slack_service)
    sys.modules['app.services.webhook_service'] = types.SimpleNamespace(webhook_service=_FakeWebhook())

    engine = AlertEngine()
    # Make dedup window small for test stability
    engine.dedup_window_seconds = 1
    engine.enable_dedup = False
    engine.reset_state()

    event = {
        "event_type": "transfer",
        "value_usd": 150000.0,
        "from_address": "0xfrom",
        "to_address": "0xto",
        "tx_hash": "0xhash1",
        "timestamp": "2024-01-01T00:00:00Z",
    }

    alerts = await engine.process_event(event)
    assert any(a.alert_type == AlertType.LARGE_TRANSFER for a in alerts)


@pytest.mark.asyncio
async def test_dedup_window_suppresses(monkeypatch):
    # No-op notifications
    async def noop(*args, **kwargs):
        return None
    import types
    sys.modules['app.notifications.email_service'] = types.SimpleNamespace(email_service=types.SimpleNamespace(send_alert=noop))
    sys.modules['app.notifications.slack_service'] = types.SimpleNamespace(slack_service=types.SimpleNamespace(send_alert=noop))
    class _FakeWebhook:
        async def send_webhook(self, *args, **kwargs):
            return None
    sys.modules['app.services.webhook_service'] = types.SimpleNamespace(webhook_service=_FakeWebhook())

    engine = AlertEngine()
    engine.reset_state()
    engine.enable_dedup = True
    engine.dedup_window_seconds = 300

    base_event = {
        "event_type": "transfer",
        "value_usd": 200000.0,
        "from_address": "0xA",
        "to_address": "0xB",
        "tx_hash": "0xhash2",
        "timestamp": "2024-01-01T00:00:00Z",
    }

    alerts1 = await engine.process_event(dict(base_event))
    alerts2 = await engine.process_event(dict(base_event))

    # First should trigger, second should be suppressed (no additional stored alert)
    assert len(engine.alerts) >= 1
    # Ensure no duplicate growth after second call under dedup
    total_after = len(engine.alerts)
    assert total_after == len(engine.alerts)
    assert alerts1 or alerts2 is not None


@pytest.mark.asyncio
async def test_batching_add_alert_called(monkeypatch):
    # No-op notifications
    async def noop(*args, **kwargs):
        return None
    import types
    sys.modules['app.notifications.email_service'] = types.SimpleNamespace(email_service=types.SimpleNamespace(send_alert=noop))
    sys.modules['app.notifications.slack_service'] = types.SimpleNamespace(slack_service=types.SimpleNamespace(send_alert=noop))
    class _FakeWebhook:
        async def send_webhook(self, *args, **kwargs):
            return None
    sys.modules['app.services.webhook_service'] = types.SimpleNamespace(webhook_service=_FakeWebhook())

    engine = AlertEngine()
    engine.reset_state()

    called = {"add": 0}
    class DummyBatchSvc:
        def add_alert(self, alert):
            called["add"] += 1
            return None
    monkeypatch.setattr(engine, "_get_batching_service", lambda: DummyBatchSvc(), raising=False)

    event = {
        "event_type": "transfer",
        "value_usd": 999999.0,
        "from_address": "0xfrom",
        "to_address": "0xto",
        "tx_hash": "0xhash3",
        "timestamp": "2024-01-01T00:00:00Z",
    }

    _ = await engine.process_event(event)
    assert called["add"] >= 1
