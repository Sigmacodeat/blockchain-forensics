"""
Tests for Webhook Service
==========================

Test webhook registration, delivery, and error handling
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.webhook_service import (
    WebhookService,
    WebhookConfig,
    WebhookDelivery,
    webhook_service
)


@pytest.fixture
def webhook_svc():
    """Create fresh webhook service instance"""
    service = WebhookService()
    yield service
    # Cleanup
    service.webhooks.clear()
    service.deliveries.clear()


def test_register_webhook(webhook_svc):
    """Test webhook registration"""
    webhook_svc.register_webhook(
        name="test-webhook",
        url="https://example.com/webhook",
        secret="test-secret",
        headers={"Authorization": "Bearer token"},
        events=["alert.high_risk"]
    )
    
    assert "test-webhook" in webhook_svc.webhooks
    config = webhook_svc.webhooks["test-webhook"]
    assert config.name == "test-webhook"
    assert str(config.url) == "https://example.com/webhook"
    assert config.secret == "test-secret"
    assert config.events == ["alert.high_risk"]


def test_unregister_webhook(webhook_svc):
    """Test webhook unregistration"""
    webhook_svc.register_webhook(
        name="test-webhook",
        url="https://example.com/webhook"
    )
    
    assert "test-webhook" in webhook_svc.webhooks
    
    webhook_svc.unregister_webhook("test-webhook")
    
    assert "test-webhook" not in webhook_svc.webhooks


@pytest.mark.asyncio
async def test_send_webhook_success(webhook_svc):
    """Test successful webhook delivery"""
    webhook_svc.register_webhook(
        name="test-webhook",
        url="https://example.com/webhook",
        events=["test.event"]
    )
    
    # Mock aiohttp session
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")
        
        mock_post = AsyncMock(return_value=mock_response)
        mock_session.return_value.__aenter__.return_value.post = mock_post
        
        deliveries = await webhook_svc.send_webhook(
            event_type="test.event",
            payload={"test": "data"}
        )
        
        assert len(deliveries) == 1
        assert deliveries[0].status == "success"
        assert deliveries[0].webhook_name == "test-webhook"


@pytest.mark.asyncio
async def test_send_webhook_http_error(webhook_svc):
    """Test webhook delivery with HTTP error"""
    webhook_svc.register_webhook(
        name="test-webhook",
        url="https://example.com/webhook",
        events=["test.event"]
    )
    
    # Mock failed HTTP response
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        mock_post = AsyncMock(return_value=mock_response)
        mock_session.return_value.__aenter__.return_value.post = mock_post
        
        deliveries = await webhook_svc.send_webhook(
            event_type="test.event",
            payload={"test": "data"}
        )
        
        assert len(deliveries) == 1
        assert deliveries[0].status == "failed"
        assert "500" in deliveries[0].error


@pytest.mark.asyncio
async def test_send_webhook_event_filtering(webhook_svc):
    """Test webhook event filtering"""
    # Register webhook for specific events only
    webhook_svc.register_webhook(
        name="alert-webhook",
        url="https://example.com/webhook",
        events=["alert.high_risk", "alert.sanctions"]
    )
    
    # Mock successful delivery
    with patch.object(webhook_svc, '_deliver_webhook', new_callable=AsyncMock) as mock_deliver:
        mock_deliver.return_value = WebhookDelivery(
            delivery_id="test-id",
            webhook_name="alert-webhook",
            event_type="alert.high_risk",
            status="success",
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Send matching event
        deliveries = await webhook_svc.send_webhook(
            event_type="alert.high_risk",
            payload={}
        )
        
        assert len(deliveries) == 1
        assert mock_deliver.called
        
        # Send non-matching event
        mock_deliver.reset_mock()
        
        deliveries = await webhook_svc.send_webhook(
            event_type="trace.completed",
            payload={}
        )
        
        assert len(deliveries) == 0
        assert not mock_deliver.called


@pytest.mark.asyncio
async def test_send_webhook_wildcard_events(webhook_svc):
    """Test webhook with wildcard event filter"""
    webhook_svc.register_webhook(
        name="all-events-webhook",
        url="https://example.com/webhook",
        events=["*"]  # All events
    )
    
    with patch.object(webhook_svc, '_deliver_webhook', new_callable=AsyncMock) as mock_deliver:
        mock_deliver.return_value = WebhookDelivery(
            delivery_id="test-id",
            webhook_name="all-events-webhook",
            event_type="any.event",
            status="success",
            delivered_at=datetime.utcnow().isoformat()
        )
        
        # Send any event - should trigger
        deliveries = await webhook_svc.send_webhook(
            event_type="any.event",
            payload={}
        )
        
        assert len(deliveries) == 1


def test_webhook_stats(webhook_svc):
    """Test webhook statistics"""
    webhook_svc.register_webhook("webhook1", "https://example.com/1")
    webhook_svc.register_webhook("webhook2", "https://example.com/2")
    
    # Add some deliveries
    webhook_svc.deliveries.append(
        WebhookDelivery(
            delivery_id="1",
            webhook_name="webhook1",
            event_type="test",
            status="success",
            delivered_at=datetime.utcnow().isoformat()
        )
    )
    webhook_svc.deliveries.append(
        WebhookDelivery(
            delivery_id="2",
            webhook_name="webhook1",
            event_type="test",
            status="failed",
            delivered_at=datetime.utcnow().isoformat()
        )
    )
    
    stats = webhook_svc.get_webhook_stats()
    
    assert stats["total_deliveries"] == 2
    assert stats["successful"] == 1
    assert stats["failed"] == 1
    assert stats["success_rate"] == 0.5
    assert stats["registered_webhooks"] == 2


@pytest.mark.asyncio
async def test_webhook_hmac_signature(webhook_svc):
    """Test HMAC signature generation"""
    webhook_svc.register_webhook(
        name="secure-webhook",
        url="https://example.com/webhook",
        secret="my-secret-key",
        events=["test.event"]
    )
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="OK")
        
        # Capture the POST call
        call_args = None
        
        async def capture_post(*args, **kwargs):
            nonlocal call_args
            call_args = kwargs
            return mock_response
        
        mock_session.return_value.__aenter__.return_value.post = capture_post
        
        await webhook_svc.send_webhook(
            event_type="test.event",
            payload={"data": "test"}
        )
        
        # Verify signature header was added
        assert call_args is not None
        headers = call_args.get('headers', {})
        assert 'X-Webhook-Signature' in headers
        assert headers['X-Webhook-Signature'].startswith('sha256=')


def test_get_delivery_status(webhook_svc):
    """Test getting delivery status by ID"""
    delivery = WebhookDelivery(
        delivery_id="test-delivery-123",
        webhook_name="test",
        event_type="test",
        status="success",
        delivered_at=datetime.utcnow().isoformat()
    )
    
    webhook_svc.deliveries.append(delivery)
    
    result = webhook_svc.get_delivery_status("test-delivery-123")
    
    assert result is not None
    assert result.delivery_id == "test-delivery-123"
    
    # Non-existent delivery
    result = webhook_svc.get_delivery_status("non-existent")
    assert result is None


def test_get_recent_deliveries(webhook_svc):
    """Test getting recent deliveries with limit"""
    # Add multiple deliveries
    for i in range(150):
        webhook_svc.deliveries.append(
            WebhookDelivery(
                delivery_id=f"delivery-{i}",
                webhook_name="test",
                event_type="test",
                status="success",
                delivered_at=datetime.utcnow().isoformat()
            )
        )
    
    # Get recent with limit
    recent = webhook_svc.get_recent_deliveries(limit=50)
    
    assert len(recent) == 50
    # Should be most recent (reversed order)
    assert recent[0].delivery_id == "delivery-149"
