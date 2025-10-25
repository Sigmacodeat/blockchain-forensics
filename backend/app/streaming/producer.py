"""Kafka Producer (optional)

- Sends Canonical Events to Kafka when enabled.
- In TEST/OFFLINE mode or when config is missing, acts as no-op.
"""
from __future__ import annotations

import json
import os
from typing import Optional, Dict, Any

try:
    from confluent_kafka import Producer  # type: ignore
except Exception:  # pragma: no cover
    Producer = None  # fallback for environments without kafka client

try:
    import fastavro  # type: ignore
except Exception:  # pragma: no cover
    fastavro = None


class EventProducer:
    def __init__(self,
                 bootstrap_servers: Optional[str] = None,
                 default_topic: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
        self.default_topic = default_topic or os.getenv("KAFKA_TOPIC_EVENTS", "ingest.events")
        self._enabled = bool(self.bootstrap_servers) and os.getenv("OFFLINE_MODE") != "1" and os.getenv("TEST_MODE") != "1"
        self._producer = None
        if self._enabled and Producer is not None:
            self._producer = Producer({"bootstrap.servers": self.bootstrap_servers})
        # Avro optional (enable if fastavro is available)
        self._use_avro = bool(fastavro)
        self._avro_schema: Optional[Dict[str, Any]] = None

    def set_avro_schema(self, schema: Dict[str, Any]) -> None:
        """Set schema for Avro encoding (parsed for fastavro)."""
        if fastavro is not None:
            # Parse once for writer usage
            self._avro_schema = fastavro.parse_schema(schema)  # type: ignore[attr-defined]
        else:
            self._avro_schema = schema

    def send(self, event: Dict[str, Any], topic: Optional[str] = None, key: Optional[str] = None) -> bool:
        if not self._enabled or self._producer is None:
            return False
        # Encode payload
        if self._use_avro and self._avro_schema is not None and fastavro is not None:
            import io
            buf = io.BytesIO()
            try:
                # Write single-record OCF container to align with consumer fastavro.reader
                fastavro.writer(buf, self._avro_schema, [event])  # type: ignore[attr-defined]
                payload = buf.getvalue()
            except Exception:
                # Fallback auf JSON, wenn Schema nicht passt
                payload = json.dumps(event).encode("utf-8")
        else:
            payload = json.dumps(event).encode("utf-8")
        self._producer.produce(topic or self.default_topic, value=payload, key=key)
        self._producer.poll(0)
        return True

    def flush(self, timeout: float = 2.0) -> None:
        if self._enabled and self._producer is not None:
            self._producer.flush(timeout)


producer = EventProducer()
