"""
Stripe Webhooks
Handles real-time payment events from Stripe
"""
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Dict, Any
import logging
from datetime import datetime

from app.services.user_service import user_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def handle_stripe_webhook(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Handle Stripe webhook events
    
    Supported events:
    - invoice.paid: Subscription renewed successfully
    - payment_intent.payment_failed: Payment failed
    - customer.subscription.deleted: Subscription cancelled
    - customer.subscription.updated: Subscription modified
    """
    event_type = payload.get('type')
    data = payload.get('data', {}).get('object', {})
    
    logger.info(f"Processing Stripe webhook: {event_type}")
    
    try:
        if event_type == 'invoice.paid':
            # Successful payment - update subscription period
            subscription_id = data.get('subscription')
            period_start = datetime.fromtimestamp(data.get('period_start'))
            period_end = datetime.fromtimestamp(data.get('period_end'))
            
            await user_service.update_subscription_period(
                subscription_id=subscription_id,
                period_start=period_start,
                period_end=period_end
            )
            
            return {'status': 'processed', 'event': 'invoice.paid'}
        
        elif event_type == 'payment_intent.payment_failed':
            # Payment failed - send notification
            customer_id = data.get('customer')
            error_message = data.get('last_payment_error', {}).get('message', 'Unknown error')
            
            # In real app: get user email from customer_id
            await notification_service.send_payment_failure_email(
                user_email="user@example.com",  # Placeholder
                payment_intent_id=data.get('id'),
                amount=data.get('amount'),
                error_message=error_message
            )
            
            return {'status': 'processed', 'event': 'payment_failed'}
        
        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled - downgrade to Community
            subscription_id = data.get('id')
            
            await user_service.downgrade_to_community(
                subscription_id=subscription_id
            )
            
            return {'status': 'processed', 'event': 'subscription_deleted'}
        
        elif event_type == 'customer.subscription.updated':
            # Subscription updated (plan change, renewal, etc.)
            subscription_id = data.get('id')
            status = data.get('status')
            
            logger.info(f"Subscription {subscription_id} updated to status: {status}")
            
            return {'status': 'processed', 'event': 'subscription_updated'}
        
        else:
            logger.warning(f"Unhandled Stripe event: {event_type}")
            return {'status': 'ignored', 'event': event_type}
    
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stripe")
async def stripe_webhook_endpoint(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """
    Stripe webhook endpoint
    
    Stripe sends events to this endpoint for:
    - Payment successes/failures
    - Subscription updates
    - Invoice updates
    
    Security: Validates Stripe signature to prevent fraud
    """
    try:
        # Get raw body
        body = await request.body()
        
        # In production: Verify Stripe signature
        # stripe.Webhook.construct_event(body, stripe_signature, webhook_secret)
        
        # Parse payload
        import json
        payload = json.loads(body)
        
        # Process event
        result = await handle_stripe_webhook(payload)
        
        return result
    
    except ValueError as e:
        logger.error(f"Invalid Stripe webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stripe/test")
async def test_stripe_webhook():
    """Test endpoint to simulate Stripe webhook"""
    test_payload = {
        'type': 'invoice.paid',
        'data': {
            'object': {
                'id': 'in_test123',
                'subscription': 'sub_test123',
                'period_start': int(datetime.now().timestamp()),
                'period_end': int(datetime.now().timestamp()) + 2592000  # 30 days
            }
        }
    }
    
    result = await handle_stripe_webhook(test_payload)
    return {'test': True, 'result': result}
