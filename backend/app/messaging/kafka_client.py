"""Kafka Client for Event Streaming"""

import json
import logging
from typing import Optional, Dict, Any, Callable
import os
try:
    from confluent_kafka import Producer, Consumer, KafkaError, KafkaException  # type: ignore
    from confluent_kafka.admin import AdminClient, NewTopic  # type: ignore
    _KAFKA_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Producer = None  # type: ignore
    Consumer = None  # type: ignore
    KafkaError = None  # type: ignore
    KafkaException = Exception  # type: ignore
    AdminClient = None  # type: ignore
    NewTopic = None  # type: ignore
    _KAFKA_AVAILABLE = False
from io import BytesIO
import json as _json

# fastavro ist optional; Fallback auf die offizielle avro-Bibliothek, sonst JSON
try:
    import fastavro
    _HAS_FASTAVRO = True
except Exception:  # pragma: no cover - optional dependency
    fastavro = None
    _HAS_FASTAVRO = False
    try:
        from avro import schema as avro_schema  # type: ignore
        from avro.datafile import DataFileWriter, DataFileReader  # type: ignore
        from avro.io import DatumWriter, DatumReader  # type: ignore
        _HAS_AVRO = True
    except Exception:
        avro_schema = None  # type: ignore
        DataFileWriter = None  # type: ignore
        DataFileReader = None  # type: ignore
        DatumWriter = None  # type: ignore
        DatumReader = None  # type: ignore
        _HAS_AVRO = False

from app.config import settings
try:
    from app.messaging.schema_registry import try_register_avro_schema as _try_sr  # type: ignore
except Exception:
    _try_sr = None  # type: ignore
from app.observability.metrics import (
    KAFKA_PRODUCER_ERRORS,
    KAFKA_CONSUMER_ERRORS,
    KAFKA_DLQ_MESSAGES,
    KAFKA_COMMITS_TOTAL,
)
from app.schemas import CanonicalEvent, CanonicalEventAvroSchema

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    """Kafka Producer with Avro serialization"""
    
    def __init__(self):
        self.config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'forensics-producer',
            'acks': 'all',  # strongest delivery guarantee
            'enable.idempotence': True,  # exactly-once within session
            'retries': 10,
            'retry.backoff.ms': 200,
            'max.in.flight.requests.per.connection': 1,  # preserve ordering
            'linger.ms': 50,
            'batch.num.messages': 1000,
            'compression.type': 'zstd',
            'message.timeout.ms': 60000,
        }
        if not _KAFKA_AVAILABLE or os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            logger.warning("KafkaProducerClient disabled (missing confluent_kafka or TEST_MODE)")
            self.producer = None  # type: ignore
        else:
            self.producer = Producer(self.config)  # type: ignore
        # Schema vorbereiten (fastavro oder avro), sonst JSON-Fallback
        if _HAS_FASTAVRO:
            self.avro_schema = fastavro.parse_schema(CanonicalEventAvroSchema.SCHEMA)
        elif _HAS_AVRO and avro_schema is not None:
            # avro (offizielle Bibliothek) hat eingeschränkte LogicalType-Unterstützung.
            # Entferne logicalType Felder (z.B. timestamp-millis), um Validierungsfehler zu vermeiden.
            def _strip_logical_types(node: Any) -> Any:
                if isinstance(node, dict):
                    node = {k: _strip_logical_types(v) for k, v in node.items() if k != 'logicalType'}
                elif isinstance(node, list):
                    node = [_strip_logical_types(v) for v in node]
                return node
            sanitized = _strip_logical_types(CanonicalEventAvroSchema.SCHEMA)
            # avro benötigt ein Schema-Objekt
            self.avro_schema = avro_schema.parse(_json.dumps(sanitized))  # type: ignore[union-attr]
        else:
            self.avro_schema = None
        self._sr_registered_topics: set[str] = set()
    
    def _serialize_avro(self, event: CanonicalEvent) -> bytes:
        """Serialize event to Avro format"""
        # If no Avro backend available, use JSON bytes fallback
        if not _HAS_FASTAVRO and not _HAS_AVRO:
            evt = event.model_dump()
            try:
                # Convert non-JSON types
                evt['block_timestamp'] = int(evt['block_timestamp'].timestamp() * 1000)
                evt['ingested_at'] = int(evt['ingested_at'].timestamp() * 1000)
            except Exception:
                pass
            try:
                if 'value' in evt:
                    evt['value'] = str(evt['value'])
                if evt.get('value_usd') is not None:
                    evt['value_usd'] = str(evt['value_usd'])
                if evt.get('fee') is not None:
                    evt['fee'] = str(evt['fee'])
            except Exception:
                pass
            return _json.dumps(evt).encode('utf-8')

        bio = BytesIO()
        event_dict = event.model_dump()

        # Convert datetime to timestamp milliseconds
        event_dict['block_timestamp'] = int(event_dict['block_timestamp'].timestamp() * 1000)
        event_dict['ingested_at'] = int(event_dict['ingested_at'].timestamp() * 1000)

        # Convert Decimal to string
        event_dict['value'] = str(event_dict['value'])
        if event_dict.get('value_usd'):
            event_dict['value_usd'] = str(event_dict['value_usd'])
        if event_dict.get('fee'):
            event_dict['fee'] = str(event_dict['fee'])

        if _HAS_FASTAVRO:
            fastavro.writer(bio, self.avro_schema, [event_dict])
            return bio.getvalue()
        elif _HAS_AVRO and DataFileWriter is not None and DatumWriter is not None:
            # Fallback: avro DataFileWriter
            writer = DataFileWriter(bio, DatumWriter(), self.avro_schema)  # type: ignore[arg-type]
            writer.append(event_dict)
            writer.flush()
            # get buffer BEFORE closing writer (closing may close underlying BytesIO)
            data = bio.getvalue()
            writer.close()
            return data
        else:
            # As ultimate fallback, return JSON bytes
            return _json.dumps(event_dict).encode('utf-8')
    
    def produce_event(
        self,
        topic: str,
        event: CanonicalEvent,
        key: Optional[str] = None,
        callback: Optional[Callable] = None
    ):
        """Produce an event to Kafka topic"""
        if self.producer is None:
            logger.info(f"Kafka disabled: skipping produce to {topic}")
            return
        try:
            # Serialize event
            value = self._serialize_avro(event)
            key_bytes = key.encode('utf-8') if key else event.idempotency_key.encode('utf-8')
            if _try_sr and topic not in self._sr_registered_topics and self.avro_schema is not None:
                try:
                    ok = _try_sr(topic, CanonicalEventAvroSchema.SCHEMA)  # type: ignore[arg-type]
                    if ok:
                        self._sr_registered_topics.add(topic)
                except Exception:
                    pass
            
            # Produce with simple backoff when local queue is full
            attempts = 0
            while True:
                try:
                    self.producer.produce(  # type: ignore[union-attr]
                        topic=topic,
                        key=key_bytes,
                        value=value,
                        callback=callback or self._delivery_report
                    )
                    break
                except BufferError:
                    attempts += 1
                    if attempts > 5:
                        raise
                    # allow delivery callbacks to drain queue
                    self.producer.poll(0.1)
            # Trigger callbacks promptly
            self.producer.poll(0)  # type: ignore[union-attr]
        
        except Exception as e:
            logger.error(f"Error producing event to {topic}: {e}")
            raise
    
    def flush(self, timeout: int = 30):
        """Wait for all messages to be delivered"""
        if self.producer is None:
            return 0
        remaining = self.producer.flush(timeout)  # type: ignore[union-attr]
        if remaining > 0:
            logger.warning(f"{remaining} messages were not delivered")
        return remaining
    
    @staticmethod
    def _delivery_report(err, msg):
        """Delivery callback"""
        if err:
            logger.error(f"Message delivery failed: {err}")
            try:
                KAFKA_PRODUCER_ERRORS.inc()
            except Exception:
                pass
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def close(self):
        """Close producer"""
        self.flush()


class KafkaConsumerClient:
    """Kafka Consumer with Avro deserialization"""
    
    def __init__(self, group_id: str, topics: list[str]):
        self.config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,  # manual commit for at-least-once
            'enable.partition.eof': True,
            'session.timeout.ms': 10000,
            'max.poll.interval.ms': 300000,
            'fetch.wait.max.ms': 500,
        }
        self.consumer = None
        if _KAFKA_AVAILABLE and not (os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST")):
            try:
                self.consumer = Consumer(self.config)  # type: ignore
                self.consumer.subscribe(topics)  # type: ignore[union-attr]
            except Exception:
                self.consumer = None
        # DLQ producer for error routing (will be disabled if kafka off)
        self._dlq_topic = getattr(settings, 'KAFKA_DLQ_TOPIC', 'dlq.events')
        self._dlq_producer = KafkaProducerClient()
        if _HAS_FASTAVRO:
            self.avro_schema = fastavro.parse_schema(CanonicalEventAvroSchema.SCHEMA)
        elif _HAS_AVRO and avro_schema is not None:
            # Align with producer fallback: strip logicalType fields for compatibility
            def _strip_logical_types(node: Any) -> Any:
                if isinstance(node, dict):
                    node = {k: _strip_logical_types(v) for k, v in node.items() if k != 'logicalType'}
                elif isinstance(node, list):
                    node = [_strip_logical_types(v) for v in node]
                return node
            sanitized = _strip_logical_types(CanonicalEventAvroSchema.SCHEMA)
            self.avro_schema = avro_schema.parse(_json.dumps(sanitized))
        else:
            # No Avro backend available; deserialization will fallback to JSON
            self.avro_schema = None
        logger.info(f"Consumer {group_id} subscribed to {topics} (enabled={bool(self.consumer)})")
    
    def _deserialize_avro(self, data: bytes) -> Dict[str, Any]:
        """Deserialize Avro data"""
        bio = BytesIO(data)
        if _HAS_FASTAVRO:
            reader = fastavro.reader(bio, self.avro_schema)
            try:
                return next(reader)
            except StopIteration:
                return {}
        elif _HAS_AVRO and DataFileReader is not None and DatumReader is not None:
            reader = DataFileReader(bio, DatumReader())
            try:
                it = iter(reader)
                try:
                    return next(it)
                except StopIteration:
                    return {}
            finally:
                reader.close()
        else:
            # No Avro backend available
            try:
                return _json.loads(bio.getvalue().decode('utf-8'))
            except Exception:
                return {}
    
    def consume_events(self, timeout: float = 1.0):
        """Consume events from Kafka"""
        if self.consumer is None:
            return None
        try:
            msg = self.consumer.poll(timeout)  # type: ignore[union-attr]
            
            if msg is None:
                return None
            
            if msg.error():
                if KafkaError is not None and msg.error().code() == KafkaError._PARTITION_EOF:  # type: ignore[union-attr]
                    logger.debug(f"Reached end of partition {msg.partition()}")
                else:
                    try:
                        KAFKA_CONSUMER_ERRORS.inc()
                    except Exception:
                        pass
                    # Route to DLQ with reason
                    try:
                        self._route_to_dlq(msg, reason="poll_error")
                    except Exception:
                        pass
                    raise KafkaException(msg.error())  # type: ignore[arg-type]
                return None
            
            # Deserialize
            try:
                event_dict = self._deserialize_avro(msg.value())
            except Exception as de:
                logger.error(f"Deserialization exception: {de}")
                try:
                    KAFKA_CONSUMER_ERRORS.inc()
                except Exception:
                    pass
                # Route to DLQ and commit to skip poison message
                try:
                    self._route_to_dlq(msg, reason="deserialize_exc")
                except Exception:
                    pass
                self.commit(msg)
                return None
            if not event_dict:
                # skip malformed/empty
                logger.warning("Received empty or malformed Avro payload; skipping")
                # commit to avoid poison-pill loops
                try:
                    self._route_to_dlq(msg, reason="deserialize")
                except Exception:
                    pass
                self.commit(msg)
                return None
            
            # Convert timestamps back to datetime
            from datetime import datetime
            event_dict['block_timestamp'] = datetime.fromtimestamp(event_dict['block_timestamp'] / 1000)
            event_dict['ingested_at'] = datetime.fromtimestamp(event_dict['ingested_at'] / 1000)
            
            return {
                'event': CanonicalEvent(**event_dict),
                'key': msg.key().decode('utf-8') if msg.key() else None,
                'partition': msg.partition(),
                'offset': msg.offset(),
                'message': msg  # For manual commit
            }
            
        except Exception as e:
            logger.error(f"Error consuming event: {e}")
            raise
    
    def commit(self, msg):
        """Commit offset manually"""
        try:
            if self.consumer is None:
                return
            self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
            try:
                KAFKA_COMMITS_TOTAL.inc()
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            try:
                KAFKA_CONSUMER_ERRORS.inc()
            except Exception:
                pass
    
    def close(self):
        """Close consumer"""
        if self.consumer is None:
            return
        self.consumer.close()  # type: ignore[union-attr]

    def get_lag(self, msg) -> Optional[int]:
        """Compute consumer lag for the given message: high_watermark - (offset+1).
        Returns None if consumer is disabled or watermark unavailable.
        """
        try:
            if self.consumer is None or msg is None:
                return None
            tp = (msg.topic(), msg.partition())
            # get_watermark_offsets returns (low, high)
            low, high = self.consumer.get_watermark_offsets(tp)  # type: ignore[arg-type]
            current_next = int(msg.offset()) + 1
            if high is None:
                return None
            lag = max(0, int(high) - current_next)
            return lag
        except Exception:
            return None
    
    def _route_to_dlq(self, msg, reason: str):
        _route_to_dlq_internal(msg, reason)


class KafkaTopics:
    """Kafka Topic Names"""
    INGEST_EVENTS = "ingest.events"
    PROCESS_TRACE_REQUESTS = "process.trace_requests"
    ENRICH_RESULTS = "enrich.results"
    FRAUD_ALERTS = "fraud_alerts"
    POLICY_EVALUATIONS = "policy.evaluations"
    CROSS_CHAIN_ALERTS = "cross_chain.alerts"
    ML_TRAINING = "ml_training"
    AUDIT_LOG = "audit_log"
    DLQ = getattr(settings, 'KAFKA_DLQ_TOPIC', 'dlq.events')


def create_topics():
    """Create Kafka topics if they don't exist"""
    if not _KAFKA_AVAILABLE or os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        logger.warning("Kafka admin disabled (missing confluent_kafka or TEST_MODE)")
        return
    admin_client = AdminClient({'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS})  # type: ignore
    
    topics = [
        NewTopic(KafkaTopics.INGEST_EVENTS, num_partitions=3, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '604800000',  # 7 days
            'cleanup.policy': 'delete',
            'segment.bytes': '134217728',
            'min.insync.replicas': '1',
        }),
        NewTopic(KafkaTopics.PROCESS_TRACE_REQUESTS, num_partitions=3, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '259200000',  # 3 days
            'cleanup.policy': 'delete',
            'segment.bytes': '134217728',
            'min.insync.replicas': '1',
        }),
        NewTopic(KafkaTopics.ENRICH_RESULTS, num_partitions=3, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '259200000',
            'cleanup.policy': 'delete',
            'segment.bytes': '134217728',
            'min.insync.replicas': '1',
        }),
        NewTopic(KafkaTopics.FRAUD_ALERTS, num_partitions=1, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '1209600000',  # 14 days
            'cleanup.policy': 'delete',
        }),
        NewTopic(KafkaTopics.POLICY_EVALUATIONS, num_partitions=2, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '604800000',  # 7 days
            'cleanup.policy': 'delete',
        }),
        NewTopic(KafkaTopics.CROSS_CHAIN_ALERTS, num_partitions=1, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '1209600000',  # 14 days
            'cleanup.policy': 'delete',
        }),
        NewTopic(KafkaTopics.ML_TRAINING, num_partitions=1, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '604800000',
        }),
        NewTopic(KafkaTopics.AUDIT_LOG, num_partitions=1, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '2592000000',  # 30 days
            'cleanup.policy': 'delete',
        }),
        NewTopic(KafkaTopics.DLQ, num_partitions=1, replication_factor=1, config={
            'compression.type': 'zstd',
            'retention.ms': '2592000000',  # 30 days
            'cleanup.policy': 'delete',
        }),
    ]
    
    fs = admin_client.create_topics(topics)  # type: ignore[union-attr]
    
    for topic, f in fs.items():
        try:
            f.result()
            logger.info(f"Topic {topic} created")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Topic {topic} already exists")
            else:
                logger.error(f"Failed to create topic {topic}: {e}")

def _safe_bytes(x: Any) -> bytes:
    try:
        if isinstance(x, bytes):
            return x
        if isinstance(x, str):
            return x.encode('utf-8', 'ignore')
        return json.dumps(x).encode('utf-8', 'ignore')
    except Exception:
        return b''

def _dlq_key(msg) -> Optional[str]:
    try:
        k = msg.key()
        return k.decode('utf-8') if k else None
    except Exception:
        return None

def _dlq_value(msg) -> bytes:
    try:
        return msg.value() or b''
    except Exception:
        return b''

def _dlq_headers(reason: str) -> list[tuple[str, bytes]]:
    try:
        return [("reason", reason.encode('utf-8'))]
    except Exception:
        return []

def _dlq_topic_name() -> str:
    return getattr(settings, 'KAFKA_DLQ_TOPIC', 'dlq.events')

def _inc_dlq(reason: str) -> None:
    try:
        KAFKA_DLQ_MESSAGES.labels(reason=reason).inc()
    except Exception:
        pass

def _producer_send_raw(topic: str, key: Optional[str], value: bytes, headers: Optional[list[tuple[str, bytes]]] = None):
    p = KafkaProducerClient()
    # direct pass-through without Avro when routing to DLQ
    try:
        if not _KAFKA_AVAILABLE or os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            logger.info("Kafka disabled: skipping DLQ produce")
            return
        p.producer.produce(  # type: ignore[union-attr]
            topic=topic,
            key=(key.encode('utf-8') if isinstance(key, str) else key),
            value=value,
            headers=headers or [],
            callback=p._delivery_report,
        )
    except BufferError:
        p.producer.poll(0.1)  # type: ignore[union-attr]
        p.producer.produce(  # type: ignore[union-attr]
            topic=topic,
            key=(key.encode('utf-8') if isinstance(key, str) else key),
            value=value,
            headers=headers or [],
            callback=p._delivery_report,
        )
    p.flush(5)

def _route_to_dlq_internal(msg, reason: str):
    try:
        key = _dlq_key(msg)
        val = _dlq_value(msg)
        headers = _dlq_headers(reason)
        _producer_send_raw(_dlq_topic_name(), key, val, headers)
        _inc_dlq(reason)
    except Exception:
        try:
            KAFKA_PRODUCER_ERRORS.inc()
        except Exception:
            pass

 
