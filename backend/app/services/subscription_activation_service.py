"""
Subscription Activation Service
Automatically activates subscriptions after successful crypto payments
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.btc_invoice_service import btc_invoice_service
from app.config import settings

logger = logging.getLogger(__name__)


class SubscriptionActivationService:
    """Service to activate subscriptions after successful payments."""

    def activate_subscription_after_payment(self, order_id: str) -> Dict[str, any]:
        """
        Activate subscription for a paid invoice.
        Returns activation result.
        """
        db: Session = next(get_db())
        try:
            # Get invoice details
            from app.models.crypto_payment import CryptoDepositAddress
            invoice = db.query(CryptoDepositAddress).filter(
                CryptoDepositAddress.order_id == order_id,
                CryptoDepositAddress.status == "paid"
            ).first()

            if not invoice:
                return {"success": False, "error": "Invoice not found or not paid"}

            # Check if subscription already exists
            from app.models.user import UserSubscription
            existing_sub = db.query(UserSubscription).filter(
                UserSubscription.user_id == invoice.user_id,
                UserSubscription.status == "active"
            ).first()

            if existing_sub:
                return {"success": False, "error": "User already has active subscription"}

            # Map plan names to subscription details
            plan_config = self._get_plan_config(invoice.plan_name)
            if not plan_config:
                return {"success": False, "error": f"Unknown plan: {invoice.plan_name}"}

            # Create subscription
            subscription = UserSubscription(
                user_id=invoice.user_id,
                plan_name=invoice.plan_name,
                status="active",
                payment_method="crypto",
                crypto_txid=invoice.txid,
                crypto_amount=invoice.expected_amount_btc,
                crypto_currency="BTC",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=plan_config["duration_days"]),
                cancel_at_period_end=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(subscription)
            db.commit()
            db.refresh(subscription)

            # Update user role if needed
            user = db.query(UserSubscription).filter(UserSubscription.id == invoice.user_id).first()
            if user and plan_config.get("role"):
                user.role = plan_config["role"]
                db.commit()

            logger.info(f"Activated subscription for user {invoice.user_id}, plan {invoice.plan_name}")

            return {
                "success": True,
                "subscription_id": str(subscription.id),
                "plan_name": invoice.plan_name,
                "period_end": subscription.current_period_end.isoformat(),
                "payment_method": "crypto"
            }

        except Exception as e:
            logger.error(f"Subscription activation failed for order {order_id}: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def _get_plan_config(self, plan_name: str) -> Optional[Dict[str, any]]:
        """Get configuration for a plan."""
        plans = {
            "community": {
                "duration_days": 30,
                "role": "user",
                "features": ["basic_search", "basic_reports"]
            },
            "pro": {
                "duration_days": 30,
                "role": "pro",
                "features": ["advanced_search", "ai_insights", "priority_support"]
            },
            "business": {
                "duration_days": 30,
                "role": "business",
                "features": ["bulk_analysis", "api_access", "custom_reports"]
            },
            "plus": {
                "duration_days": 30,
                "role": "plus",
                "features": ["unlimited_queries", "real_time_alerts", "enterprise_support"]
            },
            "enterprise": {
                "duration_days": 365,
                "role": "enterprise",
                "features": ["all_features", "dedicated_support", "custom_integrations"]
            }
        }
        return plans.get(plan_name)

    def extend_subscription(self, user_id: str, additional_days: int) -> Dict[str, any]:
        """Extend existing subscription by additional days."""
        db: Session = next(get_db())
        try:
            from app.models.user import UserSubscription
            subscription = db.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "active"
            ).first()

            if not subscription:
                return {"success": False, "error": "No active subscription found"}

            subscription.current_period_end += timedelta(days=additional_days)
            subscription.updated_at = datetime.utcnow()
            db.commit()

            return {
                "success": True,
                "new_period_end": subscription.current_period_end.isoformat(),
                "extended_days": additional_days
            }

        except Exception as e:
            logger.error(f"Subscription extension failed for user {user_id}: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    def cancel_subscription(self, user_id: str, immediate: bool = False) -> Dict[str, any]:
        """Cancel subscription."""
        db: Session = next(get_db())
        try:
            from app.models.user import UserSubscription
            subscription = db.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "active"
            ).first()

            if not subscription:
                return {"success": False, "error": "No active subscription found"}

            if immediate:
                subscription.status = "cancelled"
                subscription.cancelled_at = datetime.utcnow()
            else:
                subscription.cancel_at_period_end = True

            subscription.updated_at = datetime.utcnow()
            db.commit()

            return {"success": True, "cancelled_at": subscription.cancelled_at.isoformat() if immediate else None}

        except Exception as e:
            logger.error(f"Subscription cancellation failed for user {user_id}: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
        finally:
            db.close()


# Global instance
subscription_activation_service = SubscriptionActivationService()


# Integration function for invoice monitor
async def handle_paid_invoice(order_id: str):
    """Handle paid invoice - activate subscription automatically."""
    try:
        result = subscription_activation_service.activate_subscription_after_payment(order_id)
        if result["success"]:
            logger.info(f"Successfully activated subscription for order {order_id}")
            # Could send email notification here
        else:
            logger.error(f"Failed to activate subscription for order {order_id}: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error handling paid invoice {order_id}: {e}")
