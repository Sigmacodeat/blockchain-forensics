"""
Streaming API Endpoints
========================

API for monitoring and managing Kafka event streaming.
Provides status, metrics, and manual event publishing.
"""

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

def _get_event_publisher():
    # Lazy import to avoid side effects when streaming is disabled
    from app.streaming.event_publisher import event_publisher as _ep
    return _ep

def _get_event_consumer():
    # Lazy import to avoid side effects when streaming is disabled
    from app.streaming.event_consumer import event_consumer as _ec
    return _ec
from app.schemas.canonical_event import CanonicalEvent
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models

class EventPublishRequest(BaseModel):
    """Request to manually publish an event"""
    event: CanonicalEvent
    topic: Optional[str] = Field(None, description="Kafka topic (default: ingest.events)")
    flush: bool = Field(False, description="Force immediate delivery")


class BatchPublishRequest(BaseModel):
    """Request to publish batch of events"""
    events: List[CanonicalEvent] = Field(..., min_length=1, max_length=1000)
    topic: Optional[str] = None


class TraceRequestPublish(BaseModel):
    """Publish trace request to queue"""
    address: str = Field(..., description="Address to trace")
    direction: str = Field("forward", description="forward or backward")
    max_depth: int = Field(5, ge=1, le=10)
    chain: str = Field("ethereum")
    metadata: Optional[Dict] = None


class AlertPublishRequest(BaseModel):
    """Publish alert event"""
    alert_type: str = Field(..., description="Type: high_risk, sanction, bridge, etc.")
    severity: str = Field(..., description="critical, high, medium, low")
    message: str
    metadata: Optional[Dict] = None


class StreamingStatusResponse(BaseModel):
    """Streaming system status"""
    enabled: bool
    producer_active: bool
    consumer_active: bool
    topics: List[str]
    group_id: Optional[str]


class StreamingMetricsResponse(BaseModel):
    """Streaming metrics"""
    events_published: int
    events_consumed: int
    events_failed: int
    dlq_count: int
    batch_size: int


# API Endpoints

@router.get("/status", response_model=StreamingStatusResponse)
async def get_streaming_status() -> StreamingStatusResponse:
    """
    Get Kafka streaming status
    
    Returns producer/consumer health and configuration
    """
    try:
        event_publisher = _get_event_publisher()
        event_consumer = _get_event_consumer()
        return StreamingStatusResponse(
            enabled=event_publisher.enabled and event_consumer.enabled,
            producer_active=event_publisher.producer is not None,
            consumer_active=event_consumer.consumer is not None and event_consumer.running,
            topics=event_consumer.topics if event_consumer.enabled else [],
            group_id=event_consumer.group_id if event_consumer.enabled else None,
        )
    except Exception as e:
        logger.error(f"Failed to get streaming status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def publish_event(request: EventPublishRequest) -> Dict:
    """
    Manually publish an event to Kafka
    
    Use for testing or manual event injection
    """
    try:
        event_publisher = _get_event_publisher()
        success = await event_publisher.publish_event(
            event=request.event,
            topic=request.topic,
            flush=request.flush
        )
        
        if success:
            return {
                "status": "published",
                "event_id": request.event.event_id,
                "topic": request.topic or event_publisher.TOPIC_INGEST_EVENTS
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to publish event (check logs)"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publish failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish-batch")
async def publish_batch(request: BatchPublishRequest) -> Dict:
    """
    Publish batch of events to Kafka
    
    Max 1000 events per batch
    """
    try:
        event_publisher = _get_event_publisher()
        success_count = await event_publisher.publish_batch(
            events=request.events,
            topic=request.topic
        )
        
        return {
            "status": "completed",
            "total_events": len(request.events),
            "published": success_count,
            "failed": len(request.events) - success_count,
            "topic": request.topic or event_publisher.TOPIC_INGEST_EVENTS
        }
    
    except Exception as e:
        logger.error(f"Batch publish failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trace-request")
async def publish_trace_request(request: TraceRequestPublish) -> Dict:
    """
    Publish trace request to processing queue
    
    Consumer will process asynchronously
    """
    try:
        event_publisher = _get_event_publisher()
        success = await event_publisher.publish_trace_request(
            address=request.address,
            direction=request.direction,
            max_depth=request.max_depth,
            chain=request.chain,
            metadata=request.metadata
        )
        
        if success:
            return {
                "status": "queued",
                "address": request.address,
                "topic": event_publisher.TOPIC_TRACE_REQUESTS
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to queue trace request"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trace request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alert")
async def publish_alert(request: AlertPublishRequest) -> Dict:
    """
    Publish alert event
    
    Used for high-priority notifications
    """
    try:
        event_publisher = _get_event_publisher()
        success = await event_publisher.publish_alert(
            alert_type=request.alert_type,
            severity=request.severity,
            message=request.message,
            metadata=request.metadata
        )
        
        if success:
            return {
                "status": "published",
                "alert_type": request.alert_type,
                "severity": request.severity,
                "topic": event_publisher.TOPIC_ALERTS
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to publish alert"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Alert publish failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
async def list_topics() -> Dict:
    """
    List available Kafka topics
    """
    try:
        topics = {
            "ingest.events": "Raw blockchain events",
            "trace.requests": "Trace processing requests",
            "enrichment.requests": "Enrichment requests",
            "alerts": "High-priority alerts",
            "dlq.events": "Dead letter queue for failed events",
        }
        
        event_publisher = _get_event_publisher()
        return {
            "topics": topics,
            "enabled": event_publisher.enabled
        }
    
    except Exception as e:
        logger.error(f"Failed to list topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flush")
async def flush_publisher() -> Dict:
    """
    Force flush publisher queue
    
    Ensures all pending events are delivered
    """
    try:
        event_publisher = _get_event_publisher()
        if event_publisher.enabled and event_publisher.producer:
            event_publisher.producer.flush(timeout=30)
            return {
                "status": "flushed",
                "message": "All pending events delivered"
            }
        else:
            return {
                "status": "disabled",
                "message": "Streaming not enabled"
            }
    
    except Exception as e:
        logger.error(f"Flush failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def streaming_health() -> Dict:
    """
    Health check for streaming service
    """
    try:
        event_publisher = _get_event_publisher()
        event_consumer = _get_event_consumer()
        producer_ok = event_publisher.enabled and event_publisher.producer is not None
        consumer_ok = event_consumer.enabled and event_consumer.consumer is not None
        
        status = "healthy" if (producer_ok and consumer_ok) else "degraded"
        
        if not event_publisher.enabled:
            status = "disabled"
        
        return {
            "status": status,
            "producer": "active" if producer_ok else "inactive",
            "consumer": "active" if consumer_ok else "inactive",
            "streaming_enabled": event_publisher.enabled,
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
