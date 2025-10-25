"""
Payment Service
Handles Stripe Integration, Payment Processing, and Subscription Management
"""
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False

from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException

from app.models.user import User, SubscriptionPlan, SubscriptionStatus

try:
    from app.core.config import settings
    if STRIPE_AVAILABLE and hasattr(settings, 'STRIPE_SECRET_KEY'):
        stripe.api_key = settings.STRIPE_SECRET_KEY
except Exception:
    pass  # Tests ohne Config


class PaymentService:
    """Service für Payment Processing"""
    
    # Plan Prices (in cents)
    PLAN_PRICES = {
        SubscriptionPlan.COMMUNITY: 0,
        SubscriptionPlan.STARTER: 1900,  # $19/mo
        SubscriptionPlan.PRO: 4900,  # $49/mo
        SubscriptionPlan.BUSINESS: 9900,  # $99/mo
        SubscriptionPlan.PLUS: 19900,  # $199/mo
        SubscriptionPlan.ENTERPRISE: 49900,  # $499/mo
    }
    
    ANNUAL_DISCOUNT = 0.2  # 20% discount for annual billing
    
    def calculate_price(self, plan: SubscriptionPlan, billing_cycle: str = 'monthly') -> int:
        """Calculate price in cents"""
        base_price = self.PLAN_PRICES.get(plan, 0)
        
        if billing_cycle == 'annual':
            # Annual: 12 months - 20% discount
            annual_price = base_price * 12
            discounted_price = int(annual_price * (1 - self.ANNUAL_DISCOUNT))
            return discounted_price
        
        return base_price
    
    async def create_payment_intent(
        self,
        user: User,
        plan: SubscriptionPlan,
        billing_cycle: str = 'monthly'
    ) -> Dict:
        """
        Create Stripe Payment Intent
        
        Returns:
            {
                'payment_intent_id': str,
                'client_secret': str,
                'amount': int,
                'plan': str,
                'billing_cycle': str
            }
        """
        # Validation: Prevent duplicate active subscriptions
        if user.subscription_status == SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=400,
                detail="User already has active subscription. Cancel first to upgrade/downgrade."
            )
        
        # Validation: Prevent downgrades via payment
        if user.plan and self._is_downgrade(user.plan, plan):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot downgrade from {user.plan} to {plan}. Use subscription management."
            )
        
        # Calculate amount
        amount = self.calculate_price(plan, billing_cycle)
        
        if amount == 0:
            raise HTTPException(
                status_code=400,
                detail="Community plan is free. No payment required."
            )
        
        # Create or retrieve Stripe Customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    'user_id': user.id,
                    'plan': plan.value
                }
            )
            user.stripe_customer_id = customer.id
            # Save to DB (simplified - in real app use user_service)
        
        # Create Payment Intent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            customer=user.stripe_customer_id,
            metadata={
                'user_id': user.id,
                'plan': plan.value,
                'billing_cycle': billing_cycle
            },
            description=f"{plan.value.title()} Plan - {billing_cycle.title()} Billing"
        )
        
        return {
            'payment_intent_id': payment_intent.id,
            'client_secret': payment_intent.client_secret,
            'amount': amount,
            'plan': plan.value,
            'billing_cycle': billing_cycle
        }
    
    async def handle_payment_success(self, payment_intent_id: str) -> Dict:
        """
        Handle successful payment
        - Update user plan
        - Create subscription
        """
        from app.services.user_service import user_service
        
        # Retrieve Payment Intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status != 'succeeded':
            raise HTTPException(
                status_code=400,
                detail=f"Payment failed: {payment_intent.status}"
            )
        
        # Extract metadata
        user_id = payment_intent.metadata.get('user_id')
        plan_str = payment_intent.metadata.get('plan')
        billing_cycle = payment_intent.metadata.get('billing_cycle', 'monthly')
        
        plan = SubscriptionPlan(plan_str)
        
        # Create Stripe Subscription
        period_days = 365 if billing_cycle == 'annual' else 30
        now = datetime.now()
        period_end = now + timedelta(days=period_days)
        
        subscription = stripe.Subscription.create(
            customer=payment_intent.customer,
            items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{plan.value.title()} Plan'
                    },
                    'unit_amount': payment_intent.amount,
                    'recurring': {
                        'interval': 'year' if billing_cycle == 'annual' else 'month'
                    }
                }
            }],
            metadata={
                'user_id': user_id,
                'plan': plan_str
            }
        )
        
        # Update User Plan
        await user_service.update_user_plan(
            user_id=user_id,
            plan=plan,
            subscription_id=subscription.id,
            subscription_status=SubscriptionStatus.ACTIVE,
            billing_cycle_start=now,
            billing_cycle_end=period_end
        )
        
        return {
            'status': 'success',
            'subscription_id': subscription.id,
            'plan': plan.value,
            'period_end': period_end.isoformat()
        }
    
    async def process_payment_with_retry(
        self,
        payment_intent_id: str,
        max_retries: int = 3
    ) -> Dict:
        """
        Process payment with retry logic
        After 3 failed attempts → downgrade to Community
        """
        from app.services.user_service import user_service
        
        retry_count = 0
        
        while retry_count < max_retries:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status == 'succeeded':
                return await self.handle_payment_success(payment_intent_id)
            
            if payment_intent.status == 'payment_failed':
                retry_count += 1
                
                if retry_count < max_retries:
                    # Retry payment (simplified - in real app use Stripe retry logic)
                    await self.retry_payment(payment_intent_id)
                    continue
                else:
                    # Max retries reached → downgrade
                    user_id = payment_intent.metadata.get('user_id')
                    await user_service.downgrade_to_community(user_id)
                    
                    raise HTTPException(
                        status_code=402,
                        detail=f"Payment failed after {max_retries} retries. Downgraded to Community plan."
                    )
            
            # Other statuses (requires_payment_method, etc.)
            retry_count += 1
        
        raise HTTPException(
            status_code=402,
            detail="Payment processing failed"
        )
    
    async def retry_payment(self, payment_intent_id: str) -> Dict:
        """Retry failed payment (simplified)"""
        # In real app: Stripe handles retries automatically
        # This is for testing purposes
        return {'status': 'retrying'}
    
    def _is_downgrade(self, current_plan: SubscriptionPlan, new_plan: SubscriptionPlan) -> bool:
        """Check if new plan is a downgrade"""
        plan_hierarchy = {
            SubscriptionPlan.COMMUNITY: 0,
            SubscriptionPlan.STARTER: 1,
            SubscriptionPlan.PRO: 2,
            SubscriptionPlan.BUSINESS: 3,
            SubscriptionPlan.PLUS: 4,
            SubscriptionPlan.ENTERPRISE: 5
        }
        
        current_level = plan_hierarchy.get(current_plan, 0)
        new_level = plan_hierarchy.get(new_plan, 0)
        
        return new_level < current_level


# Global instance
payment_service = PaymentService()
