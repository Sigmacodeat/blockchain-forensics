import sys
import pathlib
import types
import pytest
from unittest.mock import patch, AsyncMock

# Ensure backend on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.workers.trace_consumer import TraceConsumerWorker  # noqa: E402


def test_trace_consumer_retry_and_dlq_on_failure(monkeypatch):
    # Mock Kafka Producer
    class _MockProducer:
        def __init__(self):
            self.produced = []
            self.flushed = False

        def produce(self, topic, key, value, headers=None, callback=None):
            self.produced.append((topic, key, value, headers))
            if callback:
                callback(None, None)  # Simulate success

        def flush(self, timeout=5):
            self.flushed = True

    # Mock _process_trace_request to always fail
    async def _failing_process(message):
        raise Exception("Processing failed")

    worker = TraceConsumerWorker(group_id="test")

    # Patch _process_trace_request to fail
    monkeypatch.setattr(worker, "_process_trace_request", _failing_process)

    # Patch KafkaProducerClient to use our mock
    from app.messaging.kafka_client import KafkaProducerClient
    class _MockClient:
        def __init__(self):
            self.producer = _MockProducer()
            self._delivery_report = lambda err, msg: None
        def flush(self, timeout=5):
            self.producer.flushed = True
    with patch.object(KafkaProducerClient, '__init__', return_value=None):
        worker.producer = _MockClient()

    # Mock Consumer.poll to return a message, then None
    class _MockMsg:
        def key(self):
            return b"test_key"
        def value(self):
            return b'{"trace_id": "test", "tx_hash": "0xabc"}'
        def error(self):
            return None
        def topic(self):
            return "trace.requests"
        def partition(self):
            return 0
        def offset(self):
            return 5
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

    # Run one consumption cycle
    result = worker._consume_once()

    # Should be False due to failure after retries
    assert result is False

    # Check DLQ was called with correct reason header
    mock_prod = worker.producer.producer
    assert len(mock_prod.produced) == 1
    topic, key, value, headers = mock_prod.produced[0]
    assert topic == "dlq.events"
    assert key == b"test_key"
    assert value == b'{"trace_id": "test", "tx_hash": "0xabc"}'
    assert headers is not None
    assert ("reason", b"processing_failed_after_3_retries") in headers

    # Producer flushed
    assert mock_prod.flushed is True
