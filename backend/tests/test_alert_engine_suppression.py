import asyncio
import os
import pytest

from app.services.alert_engine import alert_engine, AlertSeverity


@pytest.mark.asyncio
async def test_dedup_suppression_window_resets_in_testmode(monkeypatch):
    # Ensure clean state
    alert_engine.reset_state()
    # Disable per-rule and per-entity suppression to isolate dedup behavior
    alert_engine.suppression_rules["per_rule"]["enabled"] = False
    alert_engine.suppression_rules["per_entity"]["enabled"] = False
    # Remove any rule-specific silence for large_transfer during this test
    alert_engine.suppression_rules["per_rule"]["silence_rules"].pop("large_transfer", None)

    # Prepare two identical events to trigger LARGE_TRANSFER
    event = {
        "tx_hash": "0xabc",
        "from_address": "0x1",
        "to_address": "0x2",
        "value_usd": 100000.0,
    }

    # First event should trigger
    alerts1 = await alert_engine.process_event(dict(event))
    assert len(alerts1) == 1
    assert alerts1[0].severity in {AlertSeverity.MEDIUM, AlertSeverity.HIGH}

    # Second event within dedup window should be suppressed
    alerts2 = await alert_engine.process_event(dict(event))
    assert len(alerts2) == 0

    # Wait slightly beyond relaxed test stale threshold (2s) and try again
    await asyncio.sleep(2.1)
    alerts3 = await alert_engine.process_event(dict(event))
    # Should not be suppressed due to stale-state reset in test mode
    assert len(alerts3) == 1


@pytest.mark.asyncio
async def test_per_rule_suppression_silence_period(monkeypatch):
    alert_engine.reset_state()

    # Configure rule silence for large_transfer to small window
    alert_engine.suppression_rules["per_rule"]["enabled"] = True
    alert_engine.suppression_rules["per_rule"]["silence_rules"]["large_transfer"] = 1  # 1 minute

    event = {
        "tx_hash": "0xdef",
        "from_address": "0x3",
        "to_address": "0x4",
        "value_usd": 200000.0,
    }

    alerts1 = await alert_engine.process_event(dict(event))
    assert len(alerts1) == 1

    # Immediately sending same entity/rule should be suppressed by per-rule silence
    alerts2 = await alert_engine.process_event(dict(event))
    assert len(alerts2) == 0
