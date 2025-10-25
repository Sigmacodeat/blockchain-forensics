"""
Event Publisher Service
=======================

Publishes blockchain events to Kafka for real-time processing.
Integrates with Chain Adapters for automatic event streaming.

Features:
- Auto-publish from Chain Adapters
- Topic Management (ingest.events, trace.requests, etc.)
- Batch Publishing for Performance
- Error Recovery & DLQ
- Prometheus Metrics
"""

import logging
import asyncio
from typing import List, Optional
from datetime import datetime

from app.messaging.kafka_client import KafkaProducerClient
from app.schemas.canonical_event import CanonicalEvent
from app.config import settings
from app.observability.metrics import (
    KAFKA_EVENTS_PUBLISHED,
    KAFKA_EVENTS_FAILED,
    KAFKA_PUBLISH_DURATION,
)

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes blockchain events to Kafka topics
    """
    
    # Topic constants
    TOPIC_INGEST_EVENTS = "ingest.events"
    TOPIC_TRACE_REQUESTS = "trace.requests"
    TOPIC_ENRICHMENT_REQUESTS = "enrichment.requests"
    TOPIC_ALERTS = "alerts"
    TOPIC_DLQ = "dlq.events"
    
    def __init__(self):
        self.producer: Optional[KafkaProducerClient] = None
        self.enabled = getattr(settings, "ENABLE_KAFKA_STREAMING", False)
        self.batch_size = 100
        self.batch_timeout = 5.0  # seconds
        self._batch: List[CanonicalEvent] = []
        self._batch_task: Optional[asyncio.Task] = None
        
        if self.enabled:
            try:
                self.producer = KafkaProducerClient()
                logger.info("EventPublisher initialized with Kafka streaming enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Kafka producer: {e}")
                self.enabled = False
    
    async def publish_event(
        self,
        event: CanonicalEvent,
        topic: str = None,
        flush: bool = False
    ) -> bool:
        """
        Publish single event to Kafka
        
        Args:
            event: Canonical event to publish
            topic: Kafka topic (default: TOPIC_INGEST_EVENTS)
            flush: Force immediate delivery
        
        Returns:
            True if published successfully
        """
        if not self.enabled or not self.producer:
            logger.debug("Kafka streaming disabled, skipping publish")
            return False
        
        topic = topic or self.TOPIC_INGEST_EVENTS
        
        try:
            start_time = datetime.utcnow()
            
            # Publish to Kafka
            self.producer.produce_event(
                topic=topic,
                event=event,
                key=event.idempotency_key
            )
            
            if flush:
                self.producer.flush(timeout=5)
            
            # Metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            try:
                KAFKA_EVENTS_PUBLISHED.labels(topic=topic, chain=event.chain).inc()
                KAFKA_PUBLISH_DURATION.labels(topic=topic).observe(duration)
            except Exception:
                pass
            
            logger.debug(f"Published event {event.event_id} to {topic}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            try:
                KAFKA_EVENTS_FAILED.labels(topic=topic, chain=event.chain).inc()
            except Exception:
                pass
            
            # Try DLQ
            await self._send_to_dlq(event, str(e))
            return False
    
    async def publish_batch(
        self,
        events: List[CanonicalEvent],
        topic: str = None
    ) -> int:
        """
        Publish batch of events
        
        Args:
            events: List of events
            topic: Kafka topic
        
        Returns:
            Number of successfully published events
        """
        if not self.enabled or not self.producer:
            return 0
        
        topic = topic or self.TOPIC_INGEST_EVENTS
        success_count = 0
        
        for event in events:
            if await self.publish_event(event, topic=topic, flush=False):
                success_count += 1
        
        # Flush batch
        self.producer.flush(timeout=10)
        
        logger.info(f"Published {success_count}/{len(events)} events to {topic}")
        return success_count
    
    async def add_to_batch(self, event: CanonicalEvent):
        """
        Add event to batch for deferred publishing
        Automatically flushes when batch_size reached or timeout
        """
        if not self.enabled:
            return
        
        self._batch.append(event)
        
        # Start batch timer if not running
        if not self._batch_task or self._batch_task.done():
            self._batch_task = asyncio.create_task(self._batch_timer())
        
        # Flush if batch full
        if len(self._batch) >= self.batch_size:
            await self._flush_batch()
    
    async def _batch_timer(self):
        """Timer to flush batch after timeout"""
        try:
            await asyncio.sleep(self.batch_timeout)
            await self._flush_batch()
        except asyncio.CancelledError:
            pass
    
    async def _flush_batch(self):
        """Flush current batch to Kafka"""
        if not self._batch:
            return
        
        batch = self._batch.copy()
        self._batch.clear()
        
        await self.publish_batch(batch)
        
        # Cancel timer
        if self._batch_task and not self._batch_task.done():
            self._batch_task.cancel()
    
    async def _send_to_dlq(self, event: CanonicalEvent, error: str):
        """Send failed event to Dead Letter Queue"""
        try:
            event.metadata = event.metadata or {}
            event.metadata["dlq_error"] = error
            event.metadata["dlq_timestamp"] = datetime.utcnow().isoformat()
            
            if self.producer:
                self.producer.produce_event(
                    topic=self.TOPIC_DLQ,
                    event=event,
                    key=f"dlq_{event.idempotency_key}"
                )
                self.producer.flush(timeout=5)
                
                logger.warning(f"Sent event {event.event_id} to DLQ: {error}")
        
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    async def publish_trace_request(
        self,
        address: str,
        direction: str,
        max_depth: int,
        chain: str = "ethereum",
        metadata: dict = None
    ) -> bool:
        """
        Publish trace request to be processed by consumer
        
        Args:
            address: Address to trace
            direction: forward or backward
            max_depth: Max hops
            chain: Blockchain
            metadata: Additional metadata
        
        Returns:
            True if published
        """
        if not self.enabled or not self.producer:
            return False
        
        try:
            request = {
                "address": address,
                "direction": direction,
                "max_depth": max_depth,
                "chain": chain,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            import json
            self.producer.producer.produce(
                topic=self.TOPIC_TRACE_REQUESTS,
                key=address.encode('utf-8'),
                value=json.dumps(request).encode('utf-8')
            )
            self.producer.flush(timeout=5)
            
            logger.info(f"Published trace request for {address}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish trace request: {e}")
            return False
    
    async def publish_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        metadata: dict = None
    ) -> bool:
        """
        Publish alert event
        
        Args:
            alert_type: Type of alert (high_risk, sanction, bridge, etc.)
            severity: critical, high, medium, low
            message: Alert message
            metadata: Additional context
        
        Returns:
            True if published
        """
        if not self.enabled or not self.producer:
            return False
        
        try:
            alert = {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            import json
            self.producer.producer.produce(
                topic=self.TOPIC_ALERTS,
                key=alert_type.encode('utf-8'),
                value=json.dumps(alert).encode('utf-8')
            )
            self.producer.flush(timeout=5)
            
            logger.info(f"Published alert: {alert_type} ({severity})")
            return True
        
        except Exception as e:
            logger.error(f"Failed to publish alert: {e}")
            return False
    
    async def close(self):
        """Flush and close publisher"""
        if self._batch:
            await self._flush_batch()
        
        if self.producer:
            self.producer.flush(timeout=30)
            logger.info("EventPublisher closed")


# Global singleton
event_publisher = EventPublisher()
