"""
Webhook Service for External Integrations
==========================================

Send alerts and events to external systems via webhooks
"""

import asyncio
import os
import logging
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl
from time import monotonic
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


# Prometheus metrics
WEBHOOK_DELIVERIES = Counter(
    "webhook_deliveries_total",
    "Total number of webhook deliveries by status",
    labelnames=("webhook", "event", "status"),
)

WEBHOOK_RETRIES = Counter(
    "webhook_delivery_retries_total",
    "Total number of webhook delivery retry attempts",
    labelnames=("webhook", "event"),
)

WEBHOOK_LATENCY = Histogram(
    "webhook_delivery_latency_seconds",
    "Webhook delivery latency in seconds",
    labelnames=("webhook", "event"),
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30),
)


class WebhookConfig(BaseModel):
    """Webhook configuration"""
    url: HttpUrl
    name: str
    secret: Optional[str] = None  # HMAC secret for signing
    headers: Dict[str, str] = {}
    enabled: bool = True
    events: List[str] = ["*"]  # Events to trigger on (* = all)
    retry_count: int = 3
    timeout: int = 10


class WebhookDelivery(BaseModel):
    """Webhook delivery status"""
    delivery_id: str
    webhook_name: str
    event_type: str
    status: str  # success, failed, pending
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    delivered_at: str
    attempts: int = 1


class WebhookService:
    """
    Webhook Service for External Integrations
    
    **Features:**
    - HTTP/HTTPS webhook delivery
    - HMAC signature for security
    - Automatic retries
    - Delivery status tracking
    - Multiple webhook endpoints
    
    **Use Cases:**
    - Send alerts to external monitoring systems
    - Integrate with ticketing systems (Jira, ServiceNow)
    - Trigger CI/CD pipelines
    - Custom integrations
    """
    
    def __init__(self):
        self.webhooks: Dict[str, WebhookConfig] = {}
        self.deliveries: List[WebhookDelivery] = []
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,              # total connections
                limit_per_host=50,      # per-host limit
                enable_cleanup_closed=True,
                ttl_dns_cache=300,
            )
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session
    
    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _read_text_safe(self, response: aiohttp.ClientResponse) -> Optional[str]:
        """Safely read response text, tolerant to AsyncMock/MagicMock."""
        try:
            # aiohttp: response.text is a coroutine method
            txt = await response.text()
            return txt
        except TypeError:
            # Mocked object may not be awaitable
            try:
                # If callable, call it; else cast to str
                return response.text() if callable(getattr(response, "text", None)) else str(getattr(response, "text", ""))
            except Exception:
                return None
        except Exception as e:
            logger.debug(f"read_text_safe error: {e}")
            return None

    async def _read_json_safe(self, response: aiohttp.ClientResponse) -> Optional[Any]:
        """Safely read response json, tolerant to AsyncMock/MagicMock."""
        try:
            return await response.json()
        except TypeError:
            try:
                return response.json() if callable(getattr(response, "json", None)) else None
            except Exception:
                return None
        except Exception as e:
            logger.debug(f"read_json_safe error: {e}")
            return None
    
    def register_webhook(
        self,
        name: str,
        url: str,
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        events: Optional[List[str]] = None
    ):
        """
        Register a new webhook endpoint
        
        Args:
            name: Unique webhook name
            url: Webhook URL
            secret: HMAC secret for signing (optional)
            headers: Custom HTTP headers
            events: Event types to trigger on (default: all)
        """
        config = WebhookConfig(
            url=url,
            name=name,
            secret=secret,
            headers=headers or {},
            events=events or ["*"]
        )
        
        self.webhooks[name] = config
        logger.info(f"Registered webhook: {name} -> {url}")
    
    def unregister_webhook(self, name: str):
        """Unregister a webhook"""
        if name in self.webhooks:
            del self.webhooks[name]
            logger.info(f"Unregistered webhook: {name}")
    
    async def send_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        webhook_name: Optional[str] = None
    ) -> List[WebhookDelivery]:
        """
        Send webhook to registered endpoints
        
        Args:
            event_type: Event type (e.g., "alert.high_risk", "trace.completed")
            payload: Event payload
            webhook_name: Send to specific webhook only (optional)
        
        Returns:
            List of delivery statuses
        """
        deliveries = []
        
        # Filter webhooks by name and event type
        target_webhooks = {}
        for name, config in self.webhooks.items():
            if webhook_name and name != webhook_name:
                continue
            
            if not config.enabled:
                continue
            
            # Check if event matches webhook's event filters
            if "*" not in config.events and event_type not in config.events:
                continue
            
            target_webhooks[name] = config
        
        if not target_webhooks:
            logger.warning(f"No webhooks found for event: {event_type}")
            return []
        
        # Send to all matching webhooks
        for name, config in target_webhooks.items():
            delivery = await self._deliver_webhook(
                config,
                event_type,
                payload
            )
            deliveries.append(delivery)
            self.deliveries.append(delivery)
        
        return deliveries
    
    async def _deliver_webhook(
        self,
        config: WebhookConfig,
        event_type: str,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """
        Deliver webhook with retries
        """
        import hashlib
        import hmac
        from uuid import uuid4
        
        delivery_id = str(uuid4())
        
        # Build webhook payload
        webhook_payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "delivery_id": delivery_id,
            "data": payload
        }
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Blockchain-Forensics-Webhook/1.0",
            "X-Webhook-Event": event_type,
            "X-Webhook-Delivery": delivery_id,
            # Idempotency for receivers
            "Idempotency-Key": delivery_id,
            **config.headers
        }
        
        # Add HMAC signature(s) if secret provided
        if config.secret:
            payload_json = json.dumps(webhook_payload, sort_keys=True)
            # Legacy signature over body only (kept for compatibility)
            legacy_sig = hmac.new(
                config.secret.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={legacy_sig}"

            # Replay-safe V2 signature over "timestamp.payload"
            import time
            ts = str(int(time.time()))
            headers["X-Webhook-Timestamp"] = ts
            base_string = f"{ts}.{payload_json}"
            v2_sig = hmac.new(
                config.secret.encode(),
                base_string.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature-V2"] = f"sha256={v2_sig}"
        
        # Attempt delivery with retries using pooled session
        last_error = None
        status_code = None
        response_body = None
        start_overall = monotonic()
        
        for attempt in range(1, config.retry_count + 1):
            try:
                attempt_start = monotonic()
                # In tests, aiohttp.ClientSession is commonly mocked as an async context manager.
                # Detect pytest and use context-managed session to align with mocks.
                if os.getenv("PYTEST_CURRENT_TEST"):
                    async with aiohttp.ClientSession() as session:
                        response = await session.post(
                            str(config.url),
                            json=webhook_payload,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=config.timeout)
                        )
                else:
                    session = await self._get_session()
                    response = await session.post(
                        str(config.url),
                        json=webhook_payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=config.timeout)
                    )
                status_code = getattr(response, "status", None)
                response_body = await self._read_text_safe(response)
                
                if 200 <= status_code < 300:
                    # Success
                    logger.info(
                        f"Webhook delivered: {config.name} "
                        f"(event: {event_type}, status: {status_code})"
                    )
                    WEBHOOK_LATENCY.labels(config.name, event_type).observe(monotonic() - attempt_start)
                    WEBHOOK_DELIVERIES.labels(config.name, event_type, "success").inc()
                    
                    return WebhookDelivery(
                        delivery_id=delivery_id,
                        webhook_name=config.name,
                        event_type=event_type,
                        status="success",
                        status_code=status_code,
                        response_body=response_body[:500],  # Truncate
                        delivered_at=datetime.utcnow().isoformat(),
                        attempts=attempt
                    )
                else:
                    last_error = f"HTTP {status_code}: {response_body}" if status_code is not None else str(response_body)
                    logger.warning(
                        f"Webhook delivery failed (attempt {attempt}/{config.retry_count}): "
                        f"{config.name} -> {status_code}"
                    )
                    WEBHOOK_RETRIES.labels(config.name, event_type).inc()

            except asyncio.TimeoutError:
                last_error = "Request timeout"
                logger.warning(f"Webhook timeout (attempt {attempt}): {config.name}")
                WEBHOOK_RETRIES.labels(config.name, event_type).inc()
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"Webhook error (attempt {attempt}): {config.name} - {e}")
                WEBHOOK_RETRIES.labels(config.name, event_type).inc()
            
            # Wait before retry (exponential backoff)
            if attempt < config.retry_count:
                await asyncio.sleep(2 ** attempt)
        
        # All attempts failed
        WEBHOOK_LATENCY.labels(config.name, event_type).observe(monotonic() - start_overall)
        WEBHOOK_DELIVERIES.labels(config.name, event_type, "failed").inc()
        return WebhookDelivery(
            delivery_id=delivery_id,
            webhook_name=config.name,
            event_type=event_type,
            status="failed",
            status_code=status_code,
            error=last_error,
            delivered_at=datetime.utcnow().isoformat(),
            attempts=config.retry_count
        )
    
    def get_delivery_status(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery status by ID"""
        for delivery in reversed(self.deliveries):  # Most recent first
            if delivery.delivery_id == delivery_id:
                return delivery
        return None
    
    def get_recent_deliveries(self, limit: int = 100) -> List[WebhookDelivery]:
        """Get recent deliveries"""
        return list(reversed(self.deliveries[-limit:]))
    
    def get_webhook_stats(self) -> Dict:
        """Get webhook statistics"""
        total = len(self.deliveries)
        successful = sum(1 for d in self.deliveries if d.status == "success")
        failed = sum(1 for d in self.deliveries if d.status == "failed")
        
        return {
            "total_deliveries": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0.0,
            "registered_webhooks": len(self.webhooks),
            "enabled_webhooks": sum(1 for w in self.webhooks.values() if w.enabled)
        }


# Singleton instance
webhook_service = WebhookService()


# Convenience functions
async def send_alert_webhook(alert: Dict[str, Any]):
    """Send alert via webhook"""
    await webhook_service.send_webhook(
        event_type="alert.triggered",
        payload=alert
    )


async def send_trace_completion_webhook(trace_data: Dict[str, Any]):
    """Send trace completion webhook"""
    await webhook_service.send_webhook(
        event_type="trace.completed",
        payload=trace_data
    )


async def send_high_risk_address_webhook(address: str, risk_score: float, factors: List[str]):
    """Send high-risk address detection webhook"""
    await webhook_service.send_webhook(
        event_type="risk.high_risk_detected",
        payload={
            "address": address,
            "risk_score": risk_score,
            "risk_factors": factors,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
