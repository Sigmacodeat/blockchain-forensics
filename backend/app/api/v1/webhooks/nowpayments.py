"""
NOWPayments Webhook Handler
Processes Instant Payment Notifications (IPN) from NOWPayments
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

from app.services.crypto_payments import crypto_payment_service
from app.services.email_notifications import email_service
from app.db.postgres_client import postgres_client
from app.services.partner_service import partner_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def handle_payment_update(payment_data: Dict[str, Any]) -> None:
    """
    Handle payment status update
    
    Updates database and triggers actions based on payment status:
    - finished: Activate subscription, update user plan
    - failed/expired: Send notification
    - confirming: Log progress
    """
    try:
        payment_id = payment_data.get("payment_id")
        payment_status = payment_data.get("payment_status")
        
        if not payment_id:
            logger.error("Payment ID missing in webhook data")
            return
        
        # Update payment in database
        update_query = """
            UPDATE crypto_payments
            SET payment_status = $1,
                actual_pay_amount = $2,
                pay_in_hash = $3,
                outcome_amount = $4,
                last_webhook_at = NOW(),
                webhook_count = webhook_count + 1,
                updated_at = NOW()
            WHERE payment_id = $5
            RETURNING user_id, plan_name, order_id
        """
        
        result = await postgres_client.fetchrow(
            update_query,
            payment_status,
            float(payment_data.get("actually_paid", 0)) if payment_data.get("actually_paid") else None,
            payment_data.get("payin_hash"),
            float(payment_data.get("outcome_amount", 0)) if payment_data.get("outcome_amount") else None,
            payment_id
        )
        
        if not result:
            logger.warning(f"Payment {payment_id} not found in database")
            return
        
        user_id = result["user_id"]
        plan_name = result["plan_name"]
        order_id = result["order_id"]
        
        logger.info(f"Payment {payment_id} updated to {payment_status} for order {order_id}")
        
        # Broadcast real-time update to any connected WebSocket clients (best-effort)
        try:
            from app.api.v1.websockets.payment import broadcast_payment_update  # lazy import to avoid cycles
            try:
                # NOWPayments uses 'payin_hash' key, map to our tx hash param
                await broadcast_payment_update(payment_id=payment_id, status=payment_status, tx_hash=payment_data.get("payin_hash"))
            except Exception as _ws_err:
                logger.debug(f"Broadcast skipped: {_ws_err}")
        except Exception:
            # WebSocket router may not be available in all environments
            pass

        # Get user email for notifications
        user_email = await get_user_email(user_id)
        
        # Handle finished payments
        if payment_status == "finished":
            await activate_subscription(user_id, plan_name, payment_id)
            # Send success email
            if user_email:
                await email_service.send_payment_success(
                    user_email,
                    {**payment_data, "plan_name": plan_name, "order_id": order_id}
                )
            # Record partner commission (best-effort)
            try:
                # Prefer DB price_amount in USD to avoid manipulations
                amt_row = await postgres_client.fetchrow(
                    "SELECT price_amount, price_currency FROM crypto_payments WHERE payment_id = $1",
                    payment_id,
                )
                amount_usd = None
                if amt_row and (amt_row.get("price_amount") is not None):
                    amount_usd = float(amt_row["price_amount"])  # stored in USD
                else:
                    # Fallback to webhook payload
                    amount_usd = float(payment_data.get("price_amount") or 0)
                if amount_usd and amount_usd > 0:
                    await partner_service.record_commission_on_payment(
                        user_id=str(user_id),
                        plan_name=str(plan_name),
                        amount_usd=float(amount_usd),
                        payment_id=int(payment_id),
                        order_id=str(order_id),
                    )
            except Exception as _comm_err:
                logger.debug(f"Partner commission recording skipped: {_comm_err}")
        
        # Handle failed/expired payments
        elif payment_status in ["failed", "expired"]:
            await handle_failed_payment(user_id, order_id, payment_status)
            # Send failure email
            if user_email:
                reason = "Zahlung abgelaufen" if payment_status == "expired" else "Zahlung fehlgeschlagen"
                await email_service.send_payment_failed(
                    user_email,
                    {**payment_data, "plan_name": plan_name, "order_id": order_id},
                    reason
                )
        
        # Update subscription stats if recurring
        subscription = await postgres_client.fetchrow(
            """
            SELECT id FROM crypto_subscriptions
            WHERE user_id = $1 AND plan_name = $2 AND is_active = TRUE
            LIMIT 1
            """,
            user_id,
            plan_name
        )
        
        if subscription:
            if payment_status == "finished":
                await postgres_client.execute(
                    """
                    UPDATE crypto_subscriptions
                    SET successful_payments = successful_payments + 1,
                        last_payment_date = NOW(),
                        updated_at = NOW()
                    WHERE id = $1
                    """,
                    subscription["id"]
                )
            elif payment_status in ["failed", "expired"]:
                await postgres_client.execute(
                    """
                    UPDATE crypto_subscriptions
                    SET failed_payments = failed_payments + 1,
                        updated_at = NOW()
                    WHERE id = $1
                    """,
                    subscription["id"]
                )
    except Exception as e:
        logger.error(f"Error handling payment update: {e}", exc_info=True)


async def get_user_email(user_id: str) -> str:
    """
    Get user email by ID
    
    Args:
        user_id: User ID
        
    Returns:
        User email address
    """
    try:
        user = await postgres_client.fetchrow(
            "SELECT email FROM users WHERE id = $1",
            user_id
        )
        return user["email"] if user else ""
    except Exception as e:
        logger.error(f"Error getting user email: {e}")
        return ""


async def activate_subscription(user_id: str, plan_name: str, payment_id: int) -> None:
    """
    Activate user subscription after successful payment
    
    Updates user's plan and subscription status
    """
    try:
        # Update user's plan
        await postgres_client.execute(
            """
            UPDATE users
            SET plan = $1,
                subscription_status = 'active',
                billing_cycle_start = NOW(),
                billing_cycle_end = NOW() + INTERVAL '30 days'
            WHERE id = $2
            """,
            plan_name,
            user_id
        )
        
        logger.info(f"Activated {plan_name} plan for user {user_id} (payment {payment_id})")
        
        # Future: Send confirmation email (email_service.send_subscription_confirmation)
        # Future: Trigger onboarding workflow (onboarding_service.start_workflow)
        
    except Exception as e:
        logger.error(f"Error activating subscription: {e}")


async def handle_failed_payment(user_id: str, order_id: str, status: str) -> None:
    """
    Handle failed or expired payment
    
    Logs failure and sends notification
    """
    try:
        logger.warning(f"Payment {status} for user {user_id}, order {order_id}")
        
        # Future: Send failure notification email (email_service.send_payment_failure)
        # Future: Update user notification preferences (notification_service.update_prefs)
        
    except Exception as e:
        logger.error(f"Error handling failed payment: {e}")


@router.post("/nowpayments")
async def nowpayments_webhook(request: Request):
    """
    NOWPayments IPN (Instant Payment Notification) webhook
    
    **Receives payment status updates from NOWPayments:**
    - waiting: Customer hasn't sent crypto yet
    - confirming: Transaction seen, waiting for confirmations
    - confirmed: Transaction confirmed
    - sending: Sending to our wallet
    - finished: Payment completed ✅
    - failed: Payment failed ❌
    - expired: Payment expired (timeout) ⏱️
    
    **Security:**
    - Verifies HMAC signature from x-nowpayments-sig header
    - Only accepts valid signatures
    """
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("x-nowpayments-sig")
        
        if not signature:
            logger.warning("Webhook received without signature")
            raise HTTPException(status_code=401, detail="Signature missing")
        
        # Verify signature
        if not crypto_payment_service.verify_ipn_signature(body, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse JSON
        import json
        payment_data = json.loads(body.decode())
        
        logger.info(f"Webhook received: payment_id={payment_data.get('payment_id')}, status={payment_data.get('payment_status')}")
        
        # Handle payment update asynchronously
        await handle_payment_update(payment_data)
        
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        # Return 200 to prevent NOWPayments from retrying
        # (we log the error for investigation)
        return {"status": "error", "message": str(e)}
