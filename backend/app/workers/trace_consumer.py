"""
Trace Request Consumer Worker

Konsumiert Trace-Anfragen vom Kafka Topic und führt sie aus.
- Topic: trace.requests
- Verarbeitet Trace-Requests asynchron
- Speichert Ergebnisse in Neo4j
- Published Results zu trace.results
"""
from __future__ import annotations

import asyncio
import argparse
import logging
import sys
import json
from typing import Optional
from datetime import datetime

try:
    from confluent_kafka import Consumer, KafkaError, KafkaException  # type: ignore
    _KAFKA_AVAILABLE = True
except Exception:
    Consumer = None  # type: ignore
    KafkaError = None  # type: ignore
    KafkaException = Exception  # type: ignore
    _KAFKA_AVAILABLE = False

from app.config import settings
from app.messaging.kafka_client import KafkaProducerClient
from app.tracing.tracer import TransactionTracer
from app.tracing.models import TaintModel
from app.db.neo4j_client import neo4j_client
from app.observability.metrics import (
    KAFKA_CONSUMER_ERRORS,
    KAFKA_COMMITS_TOTAL,
    KAFKA_EVENTS_CONSUMED,
    KAFKA_PROCESSING_DURATION,
)
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, 
    format="[TRACE_CONSUMER] %(asctime)s %(levelname)s %(message)s"
)


class TraceConsumerWorker:
    """Worker für Trace Request Processing"""
    
    def __init__(self, group_id: str = "trace-consumer"):
        self.group_id = group_id
        self.topic = getattr(settings, "KAFKA_TOPIC_TRACE_REQUESTS", "trace.requests")
        self.results_topic = getattr(settings, "KAFKA_TOPIC_TRACE_RESULTS", "trace.results")
        
        # Kafka Consumer Config
        self.config = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 600000,  # 10 min (für lange Traces)
            "session.timeout.ms": 30000,
        }
        
        import os
        if _KAFKA_AVAILABLE and not (os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST")):
            self.consumer = Consumer(self.config)  # type: ignore
        else:
            self.consumer = None  # type: ignore
        self.producer = KafkaProducerClient()
        self.tracer = TransactionTracer(db_client=neo4j_client)
        self.running = False
        self.processed_count = 0
        self.error_count = 0
        self._last_hb_ts = 0.0
        # Retry/Backoff Settings
        try:
            self.max_retries = int(getattr(settings, "KAFKA_MAX_PROCESS_RETRIES", 3))
        except Exception:
            self.max_retries = 3
        try:
            self.backoff_base = float(getattr(settings, "KAFKA_RETRY_BACKOFF_BASE", 0.2))
        except Exception:
            self.backoff_base = 0.2
        try:
            self.backoff_cap = float(getattr(settings, "KAFKA_RETRY_BACKOFF_CAP", 2.0))
        except Exception:
            self.backoff_cap = 2.0
    
    async def _process_trace_request(self, message: dict) -> Optional[dict]:
        """
        Verarbeitet eine Trace-Request
        
        Args:
            message: Trace Request Message
            
        Returns:
            Trace Result oder None bei Fehler
        """
        try:
            # Extract parameters
            address = message.get("address")
            direction = message.get("direction", "forward")
            max_depth = message.get("max_depth", 5)
            taint_model = message.get("taint_model", "proportional")
            trace_id = message.get("trace_id")
            
            logger.info(f"Processing trace request: {trace_id} for {address}")
            
            # Map taint model
            model_map = {
                "fifo": TaintModel.FIFO,
                "proportional": TaintModel.PROPORTIONAL,
                "haircut": TaintModel.HAIRCUT
            }
            model = model_map.get(taint_model.lower(), TaintModel.PROPORTIONAL)
            
            # Execute trace
            result = await self.tracer.trace(
                address=address,
                direction=direction,
                max_depth=max_depth,
                taint_model=model
            )

            # Helper to await AsyncMocks/coroutines
            async def _maybe_await(x):
                import asyncio as _aio
                return await x if _aio.iscoroutine(x) else x

            # Add trace_id to result (support AsyncMock)
            if hasattr(result, "model_dump"):
                result_dict = await _maybe_await(result.model_dump())
            elif hasattr(result, "dict"):
                result_dict = await _maybe_await(result.dict())
            else:
                # Fallback: assume already a dict-like
                result_dict = dict(result)
            result_dict["trace_id"] = trace_id
            result_dict["processed_at"] = datetime.utcnow().isoformat()
            
            # Save to Neo4j (background)
            asyncio.create_task(self._save_trace_to_neo4j(trace_id, result_dict))
            
            logger.info(f"Trace {trace_id} completed: {len(result_dict.get('nodes', []))} nodes")
            
            return result_dict
            
        except Exception as e:
            logger.error(f"Error processing trace request: {e}", exc_info=True)
            return None

    def _send_heartbeat_sync(self, status: str = "running"):
        """Sendet einen Heartbeat synchron über den aktuellen Event Loop."""
        try:
            loop = asyncio.get_event_loop()
            coro = redis_client.set_worker_heartbeat(
                name="trace_consumer",
                payload={
                    "status": status,
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_count": self.processed_count,
                    "error_count": self.error_count,
                },
                ttl=30,
            )
            loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Failed to send heartbeat sync: {e}")
    
    async def _save_trace_to_neo4j(self, trace_id: str, result: dict):
        """Speichert Trace-Ergebnis in Neo4j"""
        try:
            async with neo4j_client.get_session() as session:
                # Create Trace node
                await session.run(
                    """
                    MERGE (t:Trace {trace_id: $trace_id})
                    SET t.source = $source,
                        t.direction = $direction,
                        t.max_depth = $max_depth,
                        t.taint_model = $taint_model,
                        t.total_nodes = $total_nodes,
                        t.total_edges = $total_edges,
                        t.created_at = datetime($created_at)
                    """,
                    trace_id=trace_id,
                    source=result.get("source_address"),
                    direction=result.get("direction"),
                    max_depth=result.get("max_depth"),
                    taint_model=result.get("taint_model"),
                    total_nodes=len(result.get("nodes", [])),
                    total_edges=len(result.get("edges", [])),
                    created_at=result.get("processed_at")
                )
                
                # Create Address nodes and relationships
                for node in result.get("nodes", []):
                    await session.run(
                        """
                        MERGE (a:Address {address: $address})
                        SET a.taint_received = $taint,
                            a.risk_level = $risk_level,
                            a.labels = $labels
                        WITH a
                        MATCH (t:Trace {trace_id: $trace_id})
                        MERGE (t)-[:INCLUDES]->(a)
                        """,
                        address=node["address"].lower(),
                        taint=node.get("taint_received", 0.0),
                        risk_level=node.get("risk_level", "LOW"),
                        labels=node.get("labels", []),
                        trace_id=trace_id
                    )
                
                # Create transaction relationships
                for edge in result.get("edges", []):
                    await session.run(
                        """
                        MATCH (from:Address {address: $from_addr})
                        MATCH (to:Address {address: $to_addr})
                        MERGE (from)-[tx:TRANSACTION {tx_hash: $tx_hash}]->(to)
                        SET tx.value = $value,
                            tx.taint = $taint,
                            tx.timestamp = datetime($timestamp)
                        """,
                        from_addr=edge["from"].lower(),
                        to_addr=edge["to"].lower(),
                        tx_hash=edge.get("tx_hash", "unknown"),
                        value=edge.get("value", 0.0),
                        taint=edge.get("taint", 0.0),
                        timestamp=edge.get("timestamp", datetime.utcnow().isoformat())
                    )
                
                logger.info(f"Saved trace {trace_id} to Neo4j")
                
        except Exception as e:
            logger.error(f"Error saving trace to Neo4j: {e}")
    
    def _consume_once(self) -> bool:
        """Konsumiert eine Nachricht"""
        if self.consumer is None:
            return False
        msg = self.consumer.poll(1.0)  # type: ignore[union-attr]
        
        if msg is None:
            return False
        
        if msg.error():
            if KafkaError is not None and msg.error().code() == KafkaError._PARTITION_EOF:  # type: ignore[union-attr]
                return False
            logger.error(f"Consumer error: {msg.error()}")
            try:
                KAFKA_CONSUMER_ERRORS.inc()
            except Exception as e:
                logger.error(f"Failed to increment consumer errors: {e}")
            self._send_heartbeat_sync(status="error")
            return False
        
        try:
            # Parse message
            value = msg.value().decode('utf-8')
            message = json.loads(value)

            # Process trace request with retry/backoff
            import time as _t
            _start_ts = _t.time()
            loop = asyncio.get_event_loop()
            attempt = 0
            result = None
            while attempt <= self.max_retries:
                attempt += 1
                try:
                    result = loop.run_until_complete(self._process_trace_request(message))
                    if result:
                        break
                except Exception as pe:
                    logger.error(f"_process_trace_request exception (attempt {attempt}/{self.max_retries}): {pe}")
                    result = None
                if not result and attempt <= self.max_retries:
                    import time as _t
                    delay = min(self.backoff_cap, self.backoff_base * (2 ** (attempt - 1)))
                    _t.sleep(delay)

            if result:
                # Publish result (best-effort, raw JSON)
                try:
                    if getattr(self.producer, "producer", None) is not None:
                        payload = json.dumps(result).encode("utf-8")
                        self.producer.producer.produce(  # type: ignore[union-attr]
                            topic=self.results_topic,
                            key=(result.get("trace_id") or "").encode("utf-8", "ignore"),
                            value=payload,
                            callback=self.producer._delivery_report,  # type: ignore[attr-defined]
                        )
                        self.producer.producer.poll(0)  # type: ignore[union-attr]
                except Exception as pub_e:
                    logger.warning(f"Publish trace result failed: {pub_e}")

                # Commit offset
                self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
                try:
                    KAFKA_COMMITS_TOTAL.labels(topic=self.topic).inc()
                    KAFKA_EVENTS_CONSUMED.labels(topic=self.topic).inc()
                    KAFKA_PROCESSING_DURATION.labels(topic=self.topic).observe(max(0.0, _t.time() - _start_ts))
                except Exception as e:
                    logger.error(f"Failed to observe processing duration: {e}")
                # Erfolgreich verarbeitet
                self.processed_count += 1
                return True
            else:
                # Final failure: route to DLQ and commit
                try:
                    self._send_to_dlq(msg, reason=f"processing_failed_after_{self.max_retries}_retries")
                except Exception as dlq_e:
                    logger.error(f"DLQ routing failed: {dlq_e}")
                try:
                    self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
                    KAFKA_COMMITS_TOTAL.labels(topic=self.topic).inc()
                except Exception as e:
                    logger.error(f"Failed to increment commits total: {e}")
                self.error_count += 1
                return False
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            # Commit um stuck messages zu vermeiden
            self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
            return False
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            try:
                KAFKA_CONSUMER_ERRORS.inc()
            except Exception as e:
                logger.error(f"Failed to increment consumer errors: {e}")
            # Route to DLQ und commit
            try:
                self._send_to_dlq(msg, reason=str(e))
            except Exception as e:
                logger.error(f"Failed to send to DLQ: {e}")
            self.consumer.commit(message=msg, asynchronous=False)
            self.error_count += 1
            return False

    def _send_to_dlq(self, msg, reason: str) -> None:
        """Sendet die Original-Nachricht in das DLQ-Topic mit Reason-Header."""
        try:
            if getattr(self.producer, "producer", None) is None:
                return
            topic = getattr(settings, "KAFKA_DLQ_TOPIC", "dlq.events")
            self.producer.producer.produce(  # type: ignore[union-attr]
                topic=topic,
                key=msg.key(),
                value=msg.value(),
                headers=[("reason", reason.encode("utf-8", "ignore"))],
                callback=self.producer._delivery_report,  # type: ignore[attr-defined]
            )
            self.producer.flush(5)
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    def run(self):
        """Startet Consumer Loop"""
        if self.consumer is None:
            logger.info("Trace consumer disabled (TEST_MODE or Kafka not available)")
            return
        self.consumer.subscribe([self.topic])  # type: ignore[union-attr]
        self.running = True
        logger.info(f"Trace consumer started: topic={self.topic} group={self.group_id}")
        
        try:
            while self.running:
                self._consume_once()
                # Heartbeat alle 5 Sekunden
                import time as _t
                now = _t.time()
                if now - self._last_hb_ts > 5.0:
                    self._send_heartbeat_sync(status="running")
                    self._last_hb_ts = now
        except KeyboardInterrupt:
            logger.info("Stopping trace consumer...")
        finally:
            if self.consumer is not None:
                self.consumer.close()  # type: ignore[union-attr]
        self.producer.flush()
        # Finaler Heartbeat
        self._send_heartbeat_sync(status="stopped")
    
    def stop(self):
        """Stoppt Consumer"""
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Trace Request Consumer Worker")
    parser.add_argument("--group", default="trace-consumer", help="Consumer group ID")
    args = parser.parse_args()
    
    worker = TraceConsumerWorker(group_id=args.group)
    worker.run()


if __name__ == "__main__":
    sys.exit(main())
