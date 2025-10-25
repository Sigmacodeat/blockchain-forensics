import os
import json
import pytest

from app.streaming.producer import EventProducer


def load_avsc(path: str):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback when running from repo root
        alt = f"backend/{path}"
        with open(alt, 'r') as f:
            return json.load(f)


def test_producer_avro_noop_in_test_mode(monkeypatch):
    # Ensure producer is disabled
    monkeypatch.setenv("TEST_MODE", "1")
    monkeypatch.setenv("USE_AVRO", "1")
    schema = load_avsc("app/streaming/schemas/canonical_event.avsc")
    p = EventProducer(bootstrap_servers=None)
    p.set_avro_schema(schema)
    ok = p.send({"event_id": "e1"})
    assert ok is False
