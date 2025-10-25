import os
import sys
import pathlib
import pytest
from datetime import datetime, timedelta

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.services.alert_engine import AlertEngine, Alert, AlertSeverity, AlertType  # noqa: E402


@pytest.mark.asyncio
async def test_entity_silence_window_suppresses_followups():
    eng = AlertEngine()
    # enable per-entity silence
    eng.suppression_rules["per_entity"]["enabled"] = True
    eng.suppression_rules["per_entity"]["silence_duration_minutes"] = 60

    # Submit first alert via rule path by crafting an event that triggers DexSwapRule
    event = {"event_type": "dex_swap", "from_address": "0xdead", "tx_hash": "0x1", "metadata": {"dex_swaps": [{}]}}
    created = await eng.submit_event(event)
    assert any(a.alert_type.value == "dex_swap" for a in created)

    # Inject a manual alert with same address and type within silence window and check suppression
    a2 = Alert(alert_type=AlertType.DEX_SWAP, severity=AlertSeverity.MEDIUM, title="t", description="d", address="0xdead")
    fp = eng._fingerprint(a2)
    assert eng._should_suppress(a2, fp) is True


@pytest.mark.asyncio
async def test_rule_silence_window_blocks_repeats():
    eng = AlertEngine()
    # enable per-rule silence for high_risk_address
    eng.suppression_rules["per_rule"]["enabled"] = True
    eng.suppression_rules["per_rule"]["silence_rules"]["dex_swap"] = 30  # minutes

    # First alert for rule type
    a1 = Alert(alert_type=AlertType.DEX_SWAP, severity=AlertSeverity.MEDIUM, title="a", description="b")
    fp1 = eng._fingerprint(a1)
    assert eng._should_suppress(a1, fp1) is False

    # Immediate repeat should be silenced
    a2 = Alert(alert_type=AlertType.DEX_SWAP, severity=AlertSeverity.MEDIUM, title="a2", description="b2")
    fp2 = eng._fingerprint(a2)
    assert eng._should_suppress(a2, fp2) is True


@pytest.mark.asyncio
async def test_global_rate_limit_per_rule():
    eng = AlertEngine()
    # configure strict global rate limit: 1 per minute
    eng.suppression_rules["global"]["max_alerts_per_minute"] = 1
    eng.suppression_rules["global"]["max_alerts_per_hour"] = 1000

    a1 = Alert(alert_type=AlertType.LARGE_TRANSFER, severity=AlertSeverity.MEDIUM, title="x", description="y")
    assert eng._should_suppress(a1, eng._fingerprint(a1)) is False

    # second within same minute should be limited
    a2 = Alert(alert_type=AlertType.LARGE_TRANSFER, severity=AlertSeverity.MEDIUM, title="x2", description="y2")
    assert eng._should_suppress(a2, eng._fingerprint(a2)) is True
