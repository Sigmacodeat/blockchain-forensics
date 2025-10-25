"""
Event Consumer Service
======================

Background worker that consumes events from Kafka and processes them.
Handles transaction enrichment, tracing triggers, and alert generation.

Features:
- Multi-threaded consumption
- Auto-commit with error handling
- DLQ for failed processing
- Graceful shutdown
- Prometheus metrics
"""

import logging
import asyncio
import signal
from typing import Optional, Dict, Any
from confluent_kafka import Consumer, KafkaError
from io import BytesIO
import json

# Optional Confluent Schema Registry imports
try:
    from confluent_kafka.schema_registry import SchemaRegistryClient  # type: ignore
    from confluent_kafka.schema_registry.avro import AvroDeserializer  # type: ignore
    from confluent_kafka.serialization import SerializationContext, MessageField  # type: ignore
    _HAS_SR = True
except Exception:
    SchemaRegistryClient = None  # type: ignore
    AvroDeserializer = None  # type: ignore
    SerializationContext = None  # type: ignore
    MessageField = None  # type: ignore
    _HAS_SR = False

try:
    import fastavro
    _HAS_FASTAVRO = True
except Exception:
    fastavro = None
    _HAS_FASTAVRO = False
    from avro import schema as avro_schema
    from avro.datafile import DataFileReader
    from avro.io import DatumReader

from app.messaging.kafka_client import KafkaProducerClient, create_topics, KafkaTopics
from app.schemas import CanonicalEvent, CanonicalEventAvroSchema
from app.config import settings
from app.metrics import (
    KAFKA_EVENTS_CONSUMED,
    KAFKA_CONSUMER_ERRORS,
    KAFKA_DLQ_MESSAGES,
    KAFKA_COMMITS_TOTAL,
    KAFKA_PROCESSING_DURATION,
    KAFKA_CONSUMER_LAG,
    KAFKA_CONSUMER_STATUS,
)
from app.enrichment.labels_service import labels_service
from app.bridge.detection import bridge_detection_service
from app.db.neo4j_client import neo4j_client
from app.ml.anomaly_detector import anomaly_detector
from app.services.alert_policy_service import alert_policy_service
from app.services.alert_service import alert_service, Alert, AlertType, AlertSeverity

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Kafka consumer for blockchain events
    Processes events in background
    """
    
    def __init__(self, group_id: str = "forensics-consumer-group"):
        self.group_id = group_id
        self.consumer: Optional[Consumer] = None
        self.producer: Optional[KafkaProducerClient] = None
        self.running = False
        self.enabled = getattr(settings, "ENABLE_KAFKA_STREAMING", False)
        # Schema Registry (optional)
        self._sr_client = None
        self._avro_deser = None
        try:
            sr_url = getattr(settings, "KAFKA_SCHEMA_REGISTRY_URL", "")
            if _HAS_SR and sr_url:
                self._sr_client = SchemaRegistryClient({"url": sr_url})  # type: ignore[arg-type]
                # Support different AvroDeserializer signatures across versions
                try:
                    # Newer versions may accept (client) only
                    self._avro_deser = AvroDeserializer(self._sr_client)  # type: ignore[call-arg]
                except TypeError:
                    try:
                        # Older signature: (schema_str, client, from_dict=None)
                        self._avro_deser = AvroDeserializer(None, self._sr_client)  # type: ignore[arg-type]
                    except Exception:
                        self._avro_deser = None
                logger.info("✅ Schema Registry client initialized for consumer")
        except Exception as _sr_err:
            logger.warning(f"⚠️ Schema Registry init skipped: {_sr_err}")
        
        # Topics to consume (limit to Avro-encoded canonical events)
        self.topics = [
            "ingest.events",
        ]
        
        if self.enabled:
            self._init_consumer()
    
    def _init_consumer(self):
        """Initialize Kafka consumer"""
        try:
            config = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'group.id': self.group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False,  # Manual commit for reliability
                'max.poll.interval.ms': 300000,  # 5 minutes
                'session.timeout.ms': 60000,
                'heartbeat.interval.ms': 3000,
            }
            
            # Ensure topics exist before subscribing
            try:
                create_topics()
            except Exception as te:
                logger.warning(f"Topic creation failed or already exists: {te}")

            self.consumer = Consumer(config)
            self.consumer.subscribe(self.topics)
            
            # Init producer for DLQ
            self.producer = KafkaProducerClient()
            
            logger.info(f"EventConsumer initialized for topics: {self.topics}")
            try:
                KAFKA_CONSUMER_STATUS.labels(group_id=self.group_id).set(1)
            except Exception:
                pass
        
        except Exception as e:
            logger.error(f"Failed to initialize consumer: {e}")
            self.enabled = False
            try:
                KAFKA_CONSUMER_STATUS.labels(group_id=self.group_id).set(0)
            except Exception:
                pass
    
    def _deserialize_avro(self, data: bytes, topic: Optional[str] = None) -> Optional[Dict]:
        """Deserialize Avro data to dict"""
        try:
            # Fast path: JSON payloads
            try:
                if data and data[:1] in (b"{", b"["):
                    return json.loads(data.decode("utf-8"))
            except Exception:
                pass

            # Confluent wire format (magic byte 0) with Schema Registry
            try:
                if self._avro_deser is not None and data and data[:1] == b"\x00":
                    ctx_topic = topic or (self.topics[0] if self.topics else "unknown")
                    ctx = SerializationContext(ctx_topic, MessageField.VALUE)  # type: ignore[arg-type]
                    rec = self._avro_deser(data, ctx)  # type: ignore[operator]
                    if isinstance(rec, dict):
                        return rec
            except Exception as _sr_de:
                logger.warning(f"Schema Registry deserialization failed, falling back: {_sr_de}")

            bio = BytesIO(data)

            if _HAS_FASTAVRO:
                try:
                    reader = fastavro.reader(bio)
                    return next(reader)
                except Exception:
                    pass
            # Fallback to standard avro reader
            try:
                def _strip_logical_types(node):
                    if isinstance(node, dict):
                        return {k: _strip_logical_types(v) for k, v in node.items() if k != 'logicalType'}
                    if isinstance(node, list):
                        return [_strip_logical_types(v) for v in node]
                    return node
                sanitized = _strip_logical_types(CanonicalEventAvroSchema.SCHEMA)
                _ = avro_schema.parse(json.dumps(sanitized))
                reader = DataFileReader(bio, DatumReader())
                return next(reader)
            except Exception:
                pass
            return None
        
        except Exception as e:
            logger.error(f"Failed to deserialize Avro: {e}")
            return None
    
    async def process_event(self, event_data: Dict) -> bool:
        """
        Process a single event
        
        Returns:
            True if processed successfully
        """
        try:
            # Convert to CanonicalEvent
            event = CanonicalEvent(**event_data)
            
            # Enrichment pipeline
            await self._enrich_event(event)
            
            # Bridge detection
            await self._detect_bridge(event)
            
            # Risk scoring
            await self._score_risk(event)

            # Policy evaluation (boolean + weighted)
            await self._evaluate_policies(event)
            
            # Store in Neo4j (async)
            asyncio.create_task(self._store_event(event))
            
            logger.debug(f"Processed event {event.event_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return False
    
    async def _enrich_event(self, event: CanonicalEvent):
        """Add labels and entity information"""
        try:
            # Get labels
            labels = await labels_service.get_labels(event.from_address)
            if labels:
                if event.labels is None:
                    event.labels = []
                event.labels.extend(labels)
            
            # Check sanctions
            is_sanctioned = await labels_service.is_sanctioned(event.from_address)
            if is_sanctioned:
                event.labels.append("OFAC_SANCTIONED")
                if event.tags is None:
                    event.tags = []
                event.tags.append("high_risk")
        
        except Exception as e:
            logger.warning(f"Enrichment failed: {e}")
    
    async def _detect_bridge(self, event: CanonicalEvent):
        """Detect bridge transactions"""
        try:
            bridge = bridge_detection_service.detect_bridge_transaction(event, None)
            if bridge:
                # Persist link best-effort
                try:
                    edge = bridge_detection_service.create_bridge_link_data(bridge)
                    bridge_detection_service.persist_bridge_link(
                        bridge.get("from_address") or event.from_address,
                        bridge.get("to_address") or event.to_address or "",
                        edge,
                    )
                except Exception:
                    pass

                # Tag event for downstream risk/policy
                event.labels.append(f"Bridge:{bridge.get('bridge_name', 'unknown')}")
                event.metadata = event.metadata or {}
                event.metadata["bridge"] = bridge
        
        except Exception as e:
            logger.warning(f"Bridge detection failed: {e}")
    
    async def _score_risk(self, event: CanonicalEvent):
        """Calculate risk score with ML anomaly detection"""
        try:
            # Simple heuristic-based scoring (existing)
            risk_score = 0.0

            # High value = higher risk
            if float(event.value) > 100:
                risk_score += 0.2

            # Sanctioned = max risk
            if "OFAC_SANCTIONED" in event.labels:
                risk_score = 1.0

            # Bridge = medium risk
            if any("Bridge:" in label for label in event.labels):
                risk_score += 0.3

            # ML Anomaly Detection - add to risk score
            try:
                event_dict = event.model_dump()
                anomaly_score = anomaly_detector.predict_anomaly(event_dict)

                # Add anomaly score as additional risk factor (weighted)
                risk_score = (risk_score * 0.8) + (anomaly_score * 0.2)

                # Store anomaly score in metadata for downstream use
                if event.metadata is None:
                    event.metadata = {}
                event.metadata['anomaly_score'] = anomaly_score
                # keep backward-compatibility with any readers using ml_anomaly_score
                event.metadata['ml_anomaly_score'] = anomaly_score

            except Exception as e:
                logger.warning(f"ML anomaly detection failed: {e}")

            event.risk_score = min(risk_score, 1.0)

        except Exception as e:
            logger.warning(f"Risk scoring failed: {e}")
    
    async def _evaluate_policies(self, event: CanonicalEvent):
        """Evaluate active policies for a single event and publish results.
        This is best-effort and non-blocking for Kafka-disabled envs.
        """
        try:
            active = alert_policy_service.get_active_rules()
            if not active:
                return

            # Build feature dict for simulation
            ev_features: Dict[str, Any] = {
                "event_id": event.event_id,
                "chain": event.chain,
                "from_address": event.from_address,
                "to_address": event.to_address,
                "value": float(event.value) if event.value is not None else 0.0,
                "labels": event.labels or [],
                "risk_score": float(getattr(event, "risk_score", 0.0) or 0.0),
                "cluster_size": int(getattr(event, "cluster_size", 1) or 1),
                "bridge_activity": bool((event.metadata or {}).get("bridge") is not None) or any("Bridge:" in l for l in (event.labels or [])),
                "mixer_usage": bool((event.metadata or {}).get("mixer", False)),
                "anomaly_score": float((event.metadata or {}).get("anomaly_score", 0.0)),
                "whale_movement": bool((event.metadata or {}).get("whale_movement", False)),
                "suspicious_patterns": (event.metadata or {}).get("suspicious_patterns", []) or [],
            }

            result = alert_policy_service.simulate(active, [ev_features])

            # Publish evaluation summary
            if self.producer and self.producer.producer:
                try:
                    payload = json.dumps({
                        "event_id": event.event_id,
                        "chain": event.chain,
                        "summary": result,
                    }).encode("utf-8")
                    self.producer.producer.produce(  # type: ignore[union-attr]
                        topic=KafkaTopics.POLICY_EVALUATIONS,
                        key=event.event_id.encode("utf-8"),
                        value=payload,
                    )
                    self.producer.producer.poll(0)  # type: ignore[union-attr]
                except Exception as pe:
                    logger.warning(f"Policy evaluation publish failed: {pe}")

            # If there are hits (boolean or weighted threshold), publish alert
            hits = int(result.get("hits", 0))
            scores = result.get("scores") or []
            score_threshold = float(result.get("score_threshold") or 0.0)
            score_flag = bool(scores) and float(scores[0]) >= score_threshold > 0
            if hits > 0 or score_flag:
                alert_payload = {
                    "alert_type": AlertType.NEW_HIGH_RISK_CONNECTION.value if ev_features["bridge_activity"] else AlertType.HIGH_RISK_ADDRESS.value,
                    "severity": AlertSeverity.HIGH.value if score_flag or ev_features["risk_score"] >= 0.8 else AlertSeverity.MEDIUM.value,
                    "title": "Policy match detected",
                    "description": "Active policies matched for event",
                    "event_id": event.event_id,
                    "address": event.from_address,
                    "chain": event.chain,
                    "risk_score": ev_features["risk_score"],
                    "policy_summary": result,
                }
                # Select topic
                topic = KafkaTopics.CROSS_CHAIN_ALERTS if ev_features["bridge_activity"] else KafkaTopics.FRAUD_ALERTS
                if self.producer and self.producer.producer:
                    try:
                        self.producer.producer.produce(  # type: ignore[union-attr]
                            topic=topic,
                            key=event.event_id.encode("utf-8"),
                            value=json.dumps(alert_payload).encode("utf-8"),
                        )
                        self.producer.producer.poll(0)  # type: ignore[union-attr]
                    except Exception as ae:
                        logger.warning(f"Alert publish failed: {ae}")

                # Persist alert via alert_engine/alert_service (best-effort)
                try:
                    sev = AlertSeverity.HIGH if alert_payload["severity"] == AlertSeverity.HIGH.value else AlertSeverity.MEDIUM
                    a = Alert(
                        alert_type=AlertType.NEW_HIGH_RISK_CONNECTION if ev_features["bridge_activity"] else AlertType.HIGH_RISK_ADDRESS,
                        severity=sev,
                        title=alert_payload["title"],
                        description=alert_payload["description"],
                        metadata={
                            "policy_summary": result,
                            "chain": event.chain,
                            "event_id": event.event_id,
                        },
                        address=event.from_address,
                        tx_hash=getattr(event, "tx_hash", None),
                    )
                    # fire-and-forget
                    asyncio.create_task(alert_service.dispatch_manual_alert(a))
                except Exception as pe:
                    logger.warning(f"Alert persistence failed: {pe}")
        except Exception as e:
            logger.warning(f"Policy evaluation failed: {e}")
        
    async def _store_event(self, event: CanonicalEvent):
        """Store event in Neo4j"""
        try:
            await neo4j_client.store_event(event)
        except Exception as e:
            logger.warning(f"Neo4j storage failed: {e}")
    
    async def _send_to_dlq(self, message, error: str):
        """Send failed message to DLQ"""
        try:
            if self.producer:
                dlq_data = {
                    "original_topic": message.topic(),
                    "partition": message.partition(),
                    "offset": message.offset(),
                    "error": error,
                    "timestamp": message.timestamp()[1] if message.timestamp()[0] >= 0 else None,
                    "key": message.key().decode('utf-8') if message.key() else None,
                }
                
                self.producer.producer.produce(
                    topic="dlq.events",
                    key=message.key(),
                    value=json.dumps(dlq_data).encode('utf-8'),
                    headers=[("reason", (error or "error").encode('utf-8', 'ignore'))],
                )
                self.producer.flush(timeout=5)
                
                try:
                    KAFKA_DLQ_MESSAGES.labels(reason=(error or "error")).inc()
                except Exception:
                    pass
        
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    async def consume_loop(self):
        """Main consumption loop"""
        if not self.enabled or not self.consumer:
            logger.info("Consumer disabled, skipping consumption")
            return
        
        self.running = True
        logger.info("Starting event consumption loop...")
        
        # Retry/Backoff Settings (configurable via settings)
        try:
            max_retries = int(getattr(settings, "KAFKA_MAX_PROCESS_RETRIES", 3))
        except Exception:
            max_retries = 3
        try:
            backoff_base = float(getattr(settings, "KAFKA_RETRY_BACKOFF_BASE", 0.2))
        except Exception:
            backoff_base = 0.2
        try:
            backoff_cap = float(getattr(settings, "KAFKA_RETRY_BACKOFF_CAP", 2.0))
        except Exception:
            backoff_cap = 2.0

        while self.running:
            try:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        try:
                            KAFKA_CONSUMER_ERRORS.inc()
                        except Exception:
                            pass
                        continue
                
                # Process message
                start_time = asyncio.get_event_loop().time()
                
                try:
                    # Deserialize
                    event_data = self._deserialize_avro(msg.value(), msg.topic())
                    
                    if event_data:
                        # Process event with retry/backoff
                        attempt = 0
                        success = False
                        while attempt <= max_retries:
                            attempt += 1
                            try:
                                success = await self.process_event(event_data)
                                if success:
                                    break
                            except Exception as pe:
                                logger.error(f"process_event exception (attempt {attempt}/{max_retries}): {pe}")
                                success = False
                            if not success and attempt <= max_retries:
                                # exponential backoff sleep
                                delay = min(backoff_cap, backoff_base * (2 ** (attempt - 1)))
                                try:
                                    await asyncio.sleep(delay)
                                except Exception:
                                    pass
                        
                        if success:
                            # Commit offset
                            self.consumer.commit(message=msg)
                            
                            # Metrics
                            try:
                                KAFKA_EVENTS_CONSUMED.labels(
                                    topic=msg.topic()
                                ).inc()
                                KAFKA_COMMITS_TOTAL.inc()
                                
                                duration = asyncio.get_event_loop().time() - start_time
                                KAFKA_PROCESSING_DURATION.labels(
                                    topic=msg.topic()
                                ).observe(duration)
                                # Consumer lag: high watermark - (current offset + 1)
                                try:
                                    low, high = self.consumer.get_watermark_offsets((msg.topic(), msg.partition()))
                                    current_next = int(msg.offset()) + 1
                                    if high is not None:
                                        lag = max(0, int(high) - current_next)
                                        KAFKA_CONSUMER_LAG.labels(topic=msg.topic(), partition=str(msg.partition())).set(lag)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        else:
                            # Final failure after retries: send to DLQ
                            await self._send_to_dlq(msg, f"processing_failed_after_{max_retries}_retries")
                    else:
                        # Deserialization failed
                        await self._send_to_dlq(msg, "deserialization_failed")
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self._send_to_dlq(msg, str(e))
                    try:
                        KAFKA_CONSUMER_ERRORS.inc()
                    except Exception:
                        pass
            
            except Exception as e:
                logger.error(f"Error in consume loop: {e}")
                await asyncio.sleep(1)
        
        logger.info("Event consumption loop stopped")
    
    def _consume_once(self) -> bool:
        """Synchroner Einzelschritt für Tests: verarbeitet genau eine Nachricht, falls vorhanden."""
        if not self.consumer:
            return False
        # Retry/Backoff Settings
        try:
            max_retries = int(getattr(settings, "KAFKA_MAX_PROCESS_RETRIES", 3))
        except Exception:
            max_retries = 3
        try:
            backoff_base = float(getattr(settings, "KAFKA_RETRY_BACKOFF_BASE", 0.2))
        except Exception:
            backoff_base = 0.2
        try:
            backoff_cap = float(getattr(settings, "KAFKA_RETRY_BACKOFF_CAP", 2.0))
        except Exception:
            backoff_cap = 2.0

        msg = self.consumer.poll(timeout=1.0)
        if msg is None:
            return False
        if hasattr(msg, 'error') and msg.error():
            return False

        start_time = 0.0
        try:
            loop = asyncio.get_event_loop()
            start_time = loop.time() if hasattr(loop, 'time') else 0.0
        except Exception:
            pass

        try:
            event_data = self._deserialize_avro(msg.value(), msg.topic())
            if event_data:
                attempt = 0
                success = False
                while attempt <= max_retries:
                    attempt += 1
                    try:
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(self.process_event(event_data))
                        success = True
                        break
                    except Exception as pe:
                        logger.error(f"process_event exception (attempt {attempt}/{max_retries}): {pe}")
                        success = False
                    if not success and attempt <= max_retries:
                        import time as _t
                        delay = min(backoff_cap, backoff_base * (2 ** (attempt - 1)))
                        _t.sleep(delay)

                if success:
                    try:
                        self.consumer.commit(message=msg)
                    except Exception:
                        pass
                    try:
                        if start_time:
                            duration = (asyncio.get_event_loop().time() - start_time)
                            KAFKA_PROCESSING_DURATION.labels(topic=getattr(msg, 'topic', lambda: 'unknown')()).observe(duration)
                        KAFKA_COMMITS_TOTAL.inc()
                    except Exception:
                        pass
                    return True
                else:
                    try:
                        loop = asyncio.get_event_loop()
                        loop.run_until_complete(self._send_to_dlq(msg, f"processing_failed_after_{max_retries}_retries"))
                    except Exception:
                        pass
                    return False
            else:
                try:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(self._send_to_dlq(msg, "deserialization_failed"))
                except Exception:
                    pass
                return False
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self._send_to_dlq(msg, str(e)))
            except Exception:
                pass
            return False
    
    def stop(self):
        """Stop consumer gracefully"""
        logger.info("Stopping consumer...")
        self.running = False
        
        if self.consumer:
            self.consumer.close()
        
        if self.producer:
            self.producer.flush(timeout=30)
        try:
            KAFKA_CONSUMER_STATUS.labels(group_id=self.group_id).set(0)
        except Exception:
            pass


# Global consumer instance
event_consumer = EventConsumer()


# Background task runner
async def start_consumer_worker():
    """Start consumer as background task"""
    await event_consumer.consume_loop()


# Graceful shutdown handler
def shutdown_handler(signum, frame):
    """Handle shutdown signal"""
    logger.info(f"Received signal {signum}, shutting down...")
    event_consumer.stop()


# Register signal handlers
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)
