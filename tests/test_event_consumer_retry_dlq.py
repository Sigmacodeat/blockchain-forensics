import sys
import pathlib
import types
import pytest
from unittest.mock import patch

# Ensure backend on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.streaming.event_consumer import EventConsumer  # noqa: E402


def test_event_consumer_retry_and_dlq_on_failure(monkeypatch):
    # Mock labels_service.get_labels to avoid real calls
    ls_mod = __import__("app.enrichment.labels_service", fromlist=["labels_service"]).labels_service
    async def _get_labels(addr):
        return []
    monkeypatch.setattr(ls_mod, "get_labels", _get_labels)

    # Mock bridge_detector.detect_bridge
    bd_mod = __import__("app.bridge.bridge_detector", fromlist=["bridge_detector"]).bridge_detector
    async def _detect_bridge(event):
        return None
    monkeypatch.setattr(bd_mod, "detect_bridge", _detect_bridge)

    # Mock alert_policy_service.get_active_rules
    aps_mod = __import__("app.services.alert_policy_service", fromlist=["alert_policy_service"]).alert_policy_service
    def _get_active_rules():
        return []
    monkeypatch.setattr(aps_mod, "get_active_rules", _get_active_rules)

    # Mock neo4j_client.store_event
    n4j_mod = __import__("app.db.neo4j_client", fromlist=["neo4j_client"]).neo4j_client
    async def _store_event(evt):
        return None
    monkeypatch.setattr(n4j_mod, "store_event", _store_event)

    # Mock Kafka Producer
    class _MockProducer:
        def __init__(self):
            self.produced = []
            self.flushed = False

        def produce(self, topic, key, value, headers=None, callback=None):
            self.produced.append((topic, key, value, headers))
            if callback:
                callback(None, None)

        def flush(self, timeout=5):
            self.flushed = True

    consumer = EventConsumer()

    # Patch KafkaProducerClient
    from app.messaging.kafka_client import KafkaProducerClient
    class _MockClient:
        def __init__(self):
            self.producer = _MockProducer()
        def flush(self, timeout=5):
            self.producer.flushed = True
    with patch.object(KafkaProducerClient, '__init__', return_value=None):
        consumer.producer = _MockClient()

    # Mock Consumer with poll/commit
    class _MockMsg:
        def key(self):
            return b"test_key"
        def value(self):
            return b"ignored"
        def error(self):
            return None
        def topic(self):
            return "ingest.events"
        def partition(self):
            return 0
        def offset(self):
            return 42
        def timestamp(self):
            return (1, 1730000000000)
    class _DummyConsumer:
        def __init__(self):
            self.polled = 0
            self.commits = 0
        def poll(self, timeout):
            self.polled += 1
            return _MockMsg() if self.polled == 1 else None
        def commit(self, message=None):
            self.commits += 1
    consumer.consumer = _DummyConsumer()

    # Bypass Avro
    async def _failing_process(ev):
        raise Exception("Processing failed")
    monkeypatch.setattr(consumer, "process_event", _failing_process)
    monkeypatch.setattr(consumer, "_deserialize_avro", lambda b: {"event_id": "e1", "chain": "ethereum", "tx_hash": "0xabc"})

    # Run one consumption cycle
    result = consumer._consume_once()

    # Should be False due to failure after retries
    assert result is False

    # Check DLQ was called with correct reason header
    mock_prod = consumer.producer.producer
    assert len(mock_prod.produced) == 1
    topic, key, value, headers = mock_prod.produced[0]
    assert topic == "dlq.events"
    assert key == b"test_key"
    assert headers is not None
    assert ("reason", b"processing_failed_after_3_retries") in headers
    # Value ist JSON mit DLQ-Metadaten
    import json as _json
    dlq_obj = _json.loads(value.decode("utf-8"))
    assert dlq_obj["original_topic"] == "ingest.events"
    assert dlq_obj["partition"] == 0
    assert dlq_obj["offset"] == 42
    assert dlq_obj["key"] == "test_key"
    assert "error" in dlq_obj

    # Producer flushed
    assert mock_prod.flushed is True
