import sys
import pathlib
import pytest
from unittest.mock import patch

# Ensure backend on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.workers.enrichment_consumer import EnrichmentConsumerWorker  # noqa: E402


def test_enrichment_consumer_retry_and_dlq_on_failure(monkeypatch):
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

    worker = EnrichmentConsumerWorker(group_id="test")

    # Patch _process_enrichment_request to always fail
    async def _failing_process(message):
        raise Exception("Processing failed")
    monkeypatch.setattr(worker, "_process_enrichment_request", _failing_process)

    # Patch KafkaProducerClient to use our mock
    from app.messaging.kafka_client import KafkaProducerClient
    class _MockClient:
        def __init__(self):
            self.producer = _MockProducer()
        def flush(self, timeout=5):
            self.producer.flushed = True
    with patch.object(KafkaProducerClient, '__init__', return_value=None):
        worker.producer = _MockClient()

    # Mock Consumer.poll to return a message, then None
    class _MockMsg:
        def key(self):
            return b"enrich_key"
        def value(self):
            return b'{"request_id": "req-1", "type": "address", "address": "0xabc"}'
        def error(self):
            return None
        def topic(self):
            return "enrich.requests"
        def partition(self):
            return 0
        def offset(self):
            return 7
        def timestamp(self):
            return (1, 1730000000000)
    # Dummy consumer with poll/commit
    class _DummyConsumer:
        def __init__(self):
            self.polled = 0
            self.commits = 0
        def poll(self, timeout):
            self.polled += 1
            return _MockMsg() if self.polled == 1 else None
        def commit(self, message=None, asynchronous=False):
            self.commits += 1
    worker.consumer = _DummyConsumer()

    # Run single consume
    ok = worker._consume_once()
    assert ok is False

    # Verify DLQ
    prod = worker.producer.producer
    assert len(prod.produced) == 1
    topic, key, value, headers = prod.produced[0]
    assert topic == "dlq.events"
    assert key == b"enrich_key"
    assert ("reason", b"processing_failed_after_3_retries") in headers
    assert prod.flushed is True
