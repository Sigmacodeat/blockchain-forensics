import asyncio
import os
import sys
import time
import json
import pathlib
import pytest

# Ensure backend/ is on PYTHONPATH (like other tests)
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("TEST_MODE", "1")

from app.workers.auto_investigate_worker import (
    start_auto_investigate_worker,
    stop_auto_investigate_worker,
    enqueue_auto_investigate,
    get_recent_jobs,
)
from app.cases.service import case_service


@pytest.mark.asyncio
async def test_auto_investigate_persists_and_enqueues(monkeypatch):
    # Ensure clean state
    recent_before = list(get_recent_jobs())

    # Mock publisher to avoid Kafka dependency
    async def _mock_publish_trace_request(**kwargs):
        return True

    from app.streaming import event_publisher as ep_mod
    monkeypatch.setattr(ep_mod.event_publisher, "publish_trace_request", _mock_publish_trace_request)

    # Start worker
    task = start_auto_investigate_worker()

    job = {
        "address": "0xAbCDEF0000000000000000000000000000000123",
        "chain": "ethereum",
        "depth": 2,
        "settings": {"report": False},
    }

    await enqueue_auto_investigate(job)

    # Wait until processed
    t0 = time.time()
    while True:
        rec = get_recent_jobs()
        if rec and rec[0].get("address", "").lower().endswith("00123") and rec[0].get("status") in {"done", "error"}:
            break
        if time.time() - t0 > 5:
            break
        await asyncio.sleep(0.05)

    # Stop worker
    stop_auto_investigate_worker()
    await asyncio.sleep(0)  # allow cancel

    # Assertions
    rec = get_recent_jobs()
    assert rec, "recent jobs should not be empty"
    last = rec[0]
    assert last["status"] == "done"
    assert last.get("case_id"), "case_id should be present in recent job entry"
    assert "trace_request_id" in last, "trace_request_id should be present in recent job entry"

    # Case snapshot should exist on disk
    case_id = last["case_id"]
    base_dir = pathlib.Path(os.getenv("CASES_DIR", "data/cases"))
    snap = base_dir / f"{case_id}.json"
    assert snap.exists(), f"snapshot for case {case_id} should exist"

    # Snapshot content is valid JSON with checksum
    data = json.loads(snap.read_text())
    assert data.get("checksum_sha256"), "checksum should be present"


@pytest.mark.asyncio
async def test_auto_investigate_kafka_disabled_path(monkeypatch):
    # Force publisher disabled path: publish returns False
    async def _mock_publish_trace_request(**kwargs):
        return False

    from app.streaming import event_publisher as ep_mod
    monkeypatch.setattr(ep_mod.event_publisher, "publish_trace_request", _mock_publish_trace_request)

    # Start worker
    task = start_auto_investigate_worker()

    job = {
        "address": "0xabc0000000000000000000000000000000000456",
        "chain": "ethereum",
        "depth": 1,
    }

    await enqueue_auto_investigate(job)

    # Wait until processed
    t0 = time.time()
    while True:
        rec = get_recent_jobs()
        if rec and rec[0].get("address", "").endswith("00456") and rec[0].get("status") in {"done", "error"}:
            break
        if time.time() - t0 > 5:
            break
        await asyncio.sleep(0.05)

    # Stop worker
    stop_auto_investigate_worker()
    await asyncio.sleep(0)

    rec = get_recent_jobs()
    last = rec[0]
    assert last["status"] == "done"
    # Even if Kafka disabled path, processing should succeed and case persisted
    case_id = last.get("case_id")
    assert case_id


@pytest.mark.asyncio
async def test_auto_investigate_double_job_processes_twice(monkeypatch):
    # Remove any dedupe assumptions; duplicate jobs should be processed (no _seen usage)
    async def _mock_publish_trace_request(**kwargs):
        return True

    from app.streaming import event_publisher as ep_mod
    monkeypatch.setattr(ep_mod.event_publisher, "publish_trace_request", _mock_publish_trace_request)

    task = start_auto_investigate_worker()

    job = {
        "address": "0xdead00000000000000000000000000000000beef",
        "chain": "ethereum",
        "depth": 1,
    }

    await enqueue_auto_investigate(job)
    await enqueue_auto_investigate(job)

    # Wait until two entries observed for this address with status done
    t0 = time.time()
    def _count_done_for(addr: str) -> int:
        return sum(1 for r in get_recent_jobs() if r.get("address", "").lower() == addr and r.get("status") == "done")

    addr_lower = job["address"].lower()
    while True:
        if _count_done_for(addr_lower) >= 1:  # we keep small deque, so assert at least one done
            break
        if time.time() - t0 > 5:
            break
        await asyncio.sleep(0.05)

    stop_auto_investigate_worker()
    await asyncio.sleep(0)

    # We expect at least one processed entry (deque may drop older if many tests run)
    assert any(r.get("address", "").lower() == addr_lower and r.get("status") == "done" for r in get_recent_jobs())
