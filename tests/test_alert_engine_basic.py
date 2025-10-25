import os
import sys
import pathlib
import pytest

# Ensure backend/ is on PYTHONPATH
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Enable test mode behaviors inside services
os.environ.setdefault("TEST_MODE", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")

from app.services.alert_engine import AlertEngine  # noqa: E402


@pytest.mark.asyncio
async def test_submit_event_creates_dex_swap_alert():
    engine = AlertEngine()
    # DexSwapRule triggers when event_type == "dex_swap"
    event = {
        "event_type": "dex_swap",
        "metadata": {"dex_swaps": [{"pair_or_pool": "0xpool"}], "dex_router": "0xrouter"},
        "from_address": "0x123",
        "tx_hash": "0xabc",
    }
    created = await engine.submit_event(event)
    assert isinstance(created, list)
    assert len(created) >= 1
    # First alert appended by dispatch_alert as well
    assert any(a.alert_type.value == "dex_swap" for a in created)
    assert any(a.alert_type.value == "dex_swap" for a in engine.alerts)


@pytest.mark.asyncio
async def test_dedup_window_suppresses_duplicate_alerts():
    engine = AlertEngine()
    event = {"event_type": "dex_swap", "metadata": {"dex_swaps": [{}]}, "from_address": "0xabc", "tx_hash": "0x1"}
    first = await engine.submit_event(event)
    assert len(first) >= 1
    # immediate duplicate should be suppressed by dedup window
    second = await engine.submit_event(event)
    # allowed: correlation may add alerts only if patterns differ; here it's same type once
    assert len(second) == 0


@pytest.mark.asyncio
async def test_process_batch_counts_events():
    engine = AlertEngine()
    # Preload buffer with two events
    engine._pending_events.append({"event_type": "dex_swap", "metadata": {"dex_swaps": [{}]}})
    engine._pending_events.append({"event_type": "dex_swap", "metadata": {"dex_swaps": [{}]}})
    processed = await engine.process_batch(max_items=10)
    assert processed == 2
    assert len(engine._pending_events) == 0
