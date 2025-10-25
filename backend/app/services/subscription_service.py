"""
Subscription Service
Manages subscription lifecycle, renewals, cancellations, and upgrades
"""
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException

from app.models.user import User, SubscriptionPlan, SubscriptionStatus

try:
    from app.core.config import settings
    if STRIPE_AVAILABLE and hasattr(settings, 'STRIPE_SECRET_KEY'):
        stripe.api_key = settings.STRIPE_SECRET_KEY
except Exception:
    pass  # Tests ohne Config


class SubscriptionService:
    """Service für Subscription Management"""
    
    GRACE_PERIOD_DAYS = 7
    
    async def create_subscription(
        self,
        user: User,
        plan: SubscriptionPlan,
        billing_cycle: str,
        subscription_id: str
    ) -> Dict:
        """Create new subscription"""
        if user.subscription_status == SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail="User already has active subscription"
            )
        
        # Calculate period
        period_start = datetime.now()
        period_days = 365 if billing_cycle == 'annual' else 30
        period_end = period_start + timedelta(days=period_days)
        
        # Update user
        user.plan = plan
        user.subscription_id = subscription_id
        user.subscription_status = SubscriptionStatus.ACTIVE
        user.billing_cycle_start = period_start
        user.billing_cycle_end = period_end
        
        return {
            'status': 'success',
            'plan': plan,
            'subscription_id': subscription_id,
            'subscription_status': SubscriptionStatus.ACTIVE,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat()
        }
    
    async def process_renewal(self, user: User) -> Dict:
        """Process subscription renewal"""
        if not user.subscription_id:
            raise HTTPException(400, "No active subscription")
        
        # Check Stripe subscription status
        stripe_sub = stripe.Subscription.retrieve(user.subscription_id)
        
        if stripe_sub.status == 'active':
            # Successful renewal
            new_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
            user.billing_cycle_start = datetime.now()
            user.billing_cycle_end = new_period_end
            
            return {
                'status': 'renewed',
                'new_period_end': new_period_end.isoformat()
            }
        
        elif stripe_sub.status == 'past_due':
            # Payment failed - enter grace period
            user.subscription_status = SubscriptionStatus.PAST_DUE
            grace_end = datetime.now() + timedelta(days=self.GRACE_PERIOD_DAYS)
            
            return {
                'status': 'grace_period',
                'grace_period_ends': grace_end.isoformat()
            }
        
        else:
            raise HTTPException(400, f"Unknown subscription status: {stripe_sub.status}")
    
    async def check_expired_subscriptions(self, user: User) -> Dict:
        """Check and handle expired subscriptions after grace period"""
        if user.subscription_status != SubscriptionStatus.PAST_DUE:
            return {'status': 'not_expired'}
        
        grace_period_end = user.billing_cycle_end + timedelta(days=self.GRACE_PERIOD_DAYS)
        
        if datetime.now() > grace_period_end:
            # Grace period expired - downgrade to Community
            user.plan = SubscriptionPlan.COMMUNITY
            user.subscription_status = SubscriptionStatus.CANCELLED
            user.subscription_id = None
            
            return {
                'status': 'downgraded',
                'new_plan': SubscriptionPlan.COMMUNITY
            }
        
        return {'status': 'in_grace_period'}
    
    async def cancel_subscription(
        self,
        user: User,
        immediate: bool = False
    ) -> Dict:
        """Cancel subscription"""
        if not user.subscription_id:
            raise HTTPException(400, "No active subscription")
        
        if immediate:
            # Immediate cancellation
            stripe.Subscription.delete(user.subscription_id)
            user.plan = SubscriptionPlan.COMMUNITY
            user.subscription_status = SubscriptionStatus.CANCELLED
            user.subscription_id = None
            
            return {'status': 'cancelled'}
        
        else:
            # Cancel at end of period
            stripe.Subscription.modify(
                user.subscription_id,
                cancel_at_period_end=True
            )
            user.subscription_status = SubscriptionStatus.CANCELLING
            
            return {
                'status': 'scheduled_cancellation',
                'downgrade_date': user.billing_cycle_end.isoformat()
            }
    
    async def upgrade_plan(
        self,
        user: User,
        new_plan: SubscriptionPlan,
        prorate: bool = True
    ) -> Dict:
        """Upgrade to higher plan"""
        if not user.subscription_id:
            raise HTTPException(400, "No active subscription")
        
        # Update Stripe subscription
        stripe.Subscription.modify(user.subscription_id)
        
        # Calculate proration
        days_remaining = (user.billing_cycle_end - datetime.now()).days
        proration_charge = self._calculate_proration(
            user.plan, new_plan, days_remaining
        ) if prorate else 0
        
        # Update user
        user.plan = new_plan
        
        return {
            'status': 'upgraded',
            'new_plan': new_plan.value,
            'proration_charge': proration_charge
        }
    
    async def downgrade_plan(
        self,
        user: User,
        new_plan: SubscriptionPlan
    ) -> Dict:
        """Downgrade to lower plan (scheduled at period end)"""
        # Downgrades are scheduled, not immediate
        return {
            'status': 'scheduled_downgrade',
            'new_plan_effective_date': user.billing_cycle_end.isoformat()
        }
    
    async def check_expiring_subscriptions(self) -> List[Dict]:
        """Cronjob: Check subscriptions expiring in 3 days"""
        # In real app: query DB for expiring subscriptions
        return []
    
    async def retry_failed_payments(self, users: List[User]) -> List[Dict]:
        """Cronjob: Retry payments for past_due subscriptions"""
        results = []
        for user in users:
            try:
                stripe.PaymentIntent.create(
                    amount=1000,  # Simplified
                    currency='usd',
                    customer=user.stripe_customer_id
                )
                results.append({'user_id': user.id, 'status': 'retried'})
            except Exception as e:
                results.append({'user_id': user.id, 'status': 'failed', 'error': str(e)})
        
        return results
    
    def is_valid_status_transition(
        self,
        from_status: SubscriptionStatus,
        to_status: SubscriptionStatus
    ) -> bool:
        """Validate status transitions"""
        valid_transitions = {
            SubscriptionStatus.NONE: [SubscriptionStatus.ACTIVE],
            SubscriptionStatus.ACTIVE: [
                SubscriptionStatus.PAST_DUE,
                SubscriptionStatus.CANCELLING,
                SubscriptionStatus.CANCELLED
            ],
            SubscriptionStatus.PAST_DUE: [
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.CANCELLED
            ],
            SubscriptionStatus.CANCELLING: [SubscriptionStatus.CANCELLED],
            SubscriptionStatus.CANCELLED: [SubscriptionStatus.ACTIVE]
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    def _calculate_proration(
        self,
        old_plan: SubscriptionPlan,
        new_plan: SubscriptionPlan,
        days_remaining: int
    ) -> int:
        """Calculate prorated charge for upgrade"""
        # Simplified - in real app use Stripe's proration
        from app.services.payment_service import payment_service
        
        old_price = payment_service.calculate_price(old_plan, 'monthly')
        new_price = payment_service.calculate_price(new_plan, 'monthly')
        
        price_diff = new_price - old_price
        proration = int((price_diff / 30) * days_remaining)
        
        return proration


# Global instance
subscription_service = SubscriptionService()
