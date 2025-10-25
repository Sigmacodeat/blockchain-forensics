"""
Webhook Management API
======================

Manage webhook endpoints for external integrations
"""

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl

from app.services.webhook_service import webhook_service, WebhookConfig, WebhookDelivery

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== Request/Response Models =====

class RegisterWebhookRequest(BaseModel):
    """Request to register a new webhook"""
    name: str
    url: HttpUrl
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    events: Optional[List[str]] = None


class RegisterWebhookResponse(BaseModel):
    """Response after registering webhook"""
    status: str
    message: str
    webhook_name: str


class TestWebhookRequest(BaseModel):
    """Request to test a webhook"""
    webhook_name: Optional[str] = None
    payload: Optional[Dict] = None


class WebhookStatsResponse(BaseModel):
    """Webhook statistics response"""
    total_deliveries: int
    successful: int
    failed: int
    success_rate: float
    registered_webhooks: int
    enabled_webhooks: int


# ===== API Endpoints =====

@router.post("/register", response_model=RegisterWebhookResponse)
async def register_webhook(request: RegisterWebhookRequest) -> RegisterWebhookResponse:
    """
    Register a new webhook endpoint
    
    **Request Body:**
    ```json
    {
      "name": "my-webhook",
      "url": "https://my-system.com/webhooks/blockchain-forensics",
      "secret": "my-secret-key",
      "headers": {
        "Authorization": "Bearer token123"
      },
      "events": ["alert.high_risk", "trace.completed"]
    }
    ```
    
    **Events:**
    - `alert.triggered` - Any alert triggered
    - `alert.high_risk_address` - High-risk address detected
    - `alert.sanctioned_entity` - Sanctioned entity interaction
    - `trace.completed` - Trace completed
    - `risk.high_risk_detected` - High-risk score calculated
    - `*` - All events (default)
    
    **Security:**
    - HMAC signature in `X-Webhook-Signature` header
    - Format: `sha256=<signature>`
    """
    try:
        webhook_service.register_webhook(
            name=request.name,
            url=str(request.url),
            secret=request.secret,
            headers=request.headers,
            events=request.events
        )
        
        return RegisterWebhookResponse(
            status="success",
            message=f"Webhook '{request.name}' registered successfully",
            webhook_name=request.name
        )
    
    except Exception as e:
        logger.error(f"Webhook registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{webhook_name}")
async def unregister_webhook(webhook_name: str) -> Dict:
    """
    Unregister a webhook endpoint
    
    **Path Parameters:**
    - webhook_name: Name of webhook to unregister
    """
    try:
        webhook_service.unregister_webhook(webhook_name)
        
        return {
            "status": "success",
            "message": f"Webhook '{webhook_name}' unregistered"
        }
    
    except Exception as e:
        logger.error(f"Webhook unregistration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=List[Dict])
async def test_webhook(request: TestWebhookRequest) -> List[Dict]:
    """
    Test webhook delivery
    
    **Request Body:**
    ```json
    {
      "webhook_name": "my-webhook",
      "payload": {
        "test": true,
        "message": "Test webhook delivery"
      }
    }
    ```
    
    Sends a test event to verify webhook configuration
    """
    try:
        payload = request.payload or {
            "test": True,
            "message": "Test webhook delivery",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        deliveries = await webhook_service.send_webhook(
            event_type="webhook.test",
            payload=payload,
            webhook_name=request.webhook_name
        )
        
        return [delivery.dict() for delivery in deliveries]
    
    except Exception as e:
        logger.error(f"Webhook test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deliveries", response_model=List[Dict])
async def get_webhook_deliveries(
    limit: int = Query(100, ge=1, le=1000),
    webhook_name: Optional[str] = Query(None)
) -> List[Dict]:
    """
    Get recent webhook deliveries
    
    **Query Parameters:**
    - limit: Maximum number of deliveries to return (default: 100)
    - webhook_name: Filter by webhook name (optional)
    """
    try:
        deliveries = webhook_service.get_recent_deliveries(limit=limit)
        
        # Filter by webhook name if provided
        if webhook_name:
            deliveries = [d for d in deliveries if d.webhook_name == webhook_name]
        
        return [delivery.dict() for delivery in deliveries]
    
    except Exception as e:
        logger.error(f"Get deliveries failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deliveries/{delivery_id}")
async def get_delivery_status(delivery_id: str) -> Dict:
    """
    Get delivery status by ID
    
    **Path Parameters:**
    - delivery_id: Delivery ID
    """
    try:
        delivery = webhook_service.get_delivery_status(delivery_id)
        
        if delivery:
            return delivery.dict()
        else:
            raise HTTPException(status_code=404, detail="Delivery not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get delivery status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=WebhookStatsResponse)
async def get_webhook_stats() -> Dict:
    """
    Get webhook statistics
    
    Returns:
    - total_deliveries: Total webhook deliveries attempted
    - successful: Successful deliveries
    - failed: Failed deliveries
    - success_rate: Success rate (0-1)
    - registered_webhooks: Number of registered webhooks
    - enabled_webhooks: Number of enabled webhooks
    """
    try:
        stats = webhook_service.get_webhook_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Get webhook stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_webhooks() -> List[Dict]:
    """
    List all registered webhooks
    
    Returns basic information (no secrets)
    """
    try:
        webhooks = []
        for name, config in webhook_service.webhooks.items():
            webhooks.append({
                "name": config.name,
                "url": str(config.url),
                "enabled": config.enabled,
                "events": config.events,
                "has_secret": config.secret is not None
            })
        
        return webhooks
    
    except Exception as e:
        logger.error(f"List webhooks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import datetime for test endpoint
from datetime import datetime
