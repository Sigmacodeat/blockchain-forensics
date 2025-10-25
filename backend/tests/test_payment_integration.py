"""
Payment Integration Tests
Tests für Stripe Payment Flow, Webhooks, und Plan-Updates
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi import HTTPException

# Models
from app.models.user import User, SubscriptionPlan, SubscriptionStatus


@pytest.fixture
def mock_stripe():
    """Mock Stripe SDK"""
    with patch('stripe.PaymentIntent') as mock_pi, \
         patch('stripe.Customer') as mock_customer, \
         patch('stripe.Subscription') as mock_sub:
        yield {
            'payment_intent': mock_pi,
            'customer': mock_customer,
            'subscription': mock_sub
        }


@pytest.fixture
def test_user():
    """Test User mit Community Plan"""
    return User(
        id="test-user-123",
        email="test@example.com",
        plan=SubscriptionPlan.COMMUNITY,
        subscription_status=SubscriptionStatus.ACTIVE,
        subscription_id=None,
        stripe_customer_id=None
    )


# ============================================================================
# TEST SUITE 1: Payment Intent Creation
# ============================================================================

@pytest.mark.asyncio
async def test_create_payment_intent_pro_plan(mock_stripe, test_user):
    """Test Payment Intent für Pro Plan ($49/Monat)"""
    from app.services.payment_service import payment_service
    
    # Mock Stripe Customer Creation
    mock_stripe['customer'].create.return_value = Mock(id='cus_test123')
    
    # Mock Payment Intent Creation
    mock_payment_intent = Mock(
        id='pi_test123',
        client_secret='secret_test123',
        amount=4900,  # $49 in cents
        currency='usd',
        status='requires_payment_method'
    )
    mock_stripe['payment_intent'].create.return_value = mock_payment_intent
    
    # Create Payment Intent
    result = await payment_service.create_payment_intent(
        user=test_user,
        plan=SubscriptionPlan.PRO,
        billing_cycle='monthly'
    )
    
    # Assertions
    assert result['payment_intent_id'] == 'pi_test123'
    assert result['client_secret'] == 'secret_test123'
    assert result['amount'] == 4900
    assert result['plan'] == 'pro'
    
    # Verify Stripe calls
    mock_stripe['customer'].create.assert_called_once()
    mock_stripe['payment_intent'].create.assert_called_once()


@pytest.mark.asyncio
async def test_create_payment_intent_plus_plan(mock_stripe, test_user):
    """Test Payment Intent für Plus Plan ($99/Monat)"""
    from app.services.payment_service import payment_service
    
    mock_stripe['customer'].create.return_value = Mock(id='cus_test123')
    mock_payment_intent = Mock(
        id='pi_test456',
        client_secret='secret_test456',
        amount=9900,
        currency='usd'
    )
    mock_stripe['payment_intent'].create.return_value = mock_payment_intent
    
    result = await payment_service.create_payment_intent(
        user=test_user,
        plan=SubscriptionPlan.PLUS,
        billing_cycle='monthly'
    )
    
    assert result['amount'] == 9900
    assert result['plan'] == 'plus'


@pytest.mark.asyncio
async def test_create_payment_intent_annual_discount(mock_stripe, test_user):
    """Test Annual Billing mit 20% Discount"""
    from app.services.payment_service import payment_service
    
    mock_stripe['customer'].create.return_value = Mock(id='cus_test123')
    mock_payment_intent = Mock(
        id='pi_annual',
        amount=47040,  # $49 * 12 * 0.8 = $470.40
        currency='usd'
    )
    mock_stripe['payment_intent'].create.return_value = mock_payment_intent
    
    result = await payment_service.create_payment_intent(
        user=test_user,
        plan=SubscriptionPlan.PRO,
        billing_cycle='annual'
    )
    
    # $49 * 12 = $588, mit 20% Discount = $470.40
    assert result['amount'] == 47040
    assert result['billing_cycle'] == 'annual'


# ============================================================================
# TEST SUITE 2: Payment Success → Plan Update
# ============================================================================

@pytest.mark.asyncio
async def test_payment_success_updates_user_plan(mock_stripe, test_user):
    """Test dass erfolgreiche Payment User-Plan updated"""
    from app.services.payment_service import payment_service
    from app.services.user_service import user_service
    
    # Mock Payment Intent als succeeded
    mock_payment_intent = Mock(
        id='pi_succeeded',
        status='succeeded',
        amount=4900,
        metadata={'user_id': test_user.id, 'plan': 'pro'}
    )
    mock_stripe['payment_intent'].retrieve.return_value = mock_payment_intent
    
    # Mock Subscription Creation
    mock_subscription = Mock(
        id='sub_test123',
        status='active',
        current_period_start=int(datetime.now().timestamp()),
        current_period_end=int((datetime.now() + timedelta(days=30)).timestamp())
    )
    mock_stripe['subscription'].create.return_value = mock_subscription
    
    # Process Payment Success
    with patch.object(user_service, 'update_user_plan', new_callable=AsyncMock) as mock_update:
        await payment_service.handle_payment_success(
            payment_intent_id='pi_succeeded'
        )
        
        # Verify Plan wurde geupdated
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[1]['plan'] == SubscriptionPlan.PRO
        assert call_args[1]['subscription_id'] == 'sub_test123'
        assert call_args[1]['subscription_status'] == SubscriptionStatus.ACTIVE


@pytest.mark.asyncio
async def test_payment_failure_keeps_community_plan(mock_stripe, test_user):
    """Test dass failed Payment Plan NICHT updated"""
    from app.services.payment_service import payment_service
    from app.services.user_service import user_service
    
    mock_payment_intent = Mock(
        id='pi_failed',
        status='payment_failed',
        metadata={'user_id': test_user.id, 'plan': 'pro'}
    )
    mock_stripe['payment_intent'].retrieve.return_value = mock_payment_intent
    
    with patch.object(user_service, 'update_user_plan', new_callable=AsyncMock) as mock_update:
        with pytest.raises(HTTPException) as exc_info:
            await payment_service.handle_payment_success('pi_failed')
        
        assert exc_info.value.status_code == 400
        assert "payment failed" in str(exc_info.value.detail).lower()
        
        # Plan wurde NICHT geupdated
        mock_update.assert_not_called()


# ============================================================================
# TEST SUITE 3: Webhook Handling
# ============================================================================

@pytest.mark.asyncio
async def test_webhook_invoice_paid(mock_stripe):
    """Test Stripe Webhook: invoice.paid"""
    from app.api.v1.webhooks import handle_stripe_webhook
    from app.services.user_service import user_service
    
    webhook_payload = {
        'type': 'invoice.paid',
        'data': {
            'object': {
                'id': 'in_test123',
                'customer': 'cus_test123',
                'subscription': 'sub_test123',
                'amount_paid': 4900,
                'period_start': int(datetime.now().timestamp()),
                'period_end': int((datetime.now() + timedelta(days=30)).timestamp())
            }
        }
    }
    
    with patch.object(user_service, 'update_subscription_period', new_callable=AsyncMock) as mock_update:
        await handle_stripe_webhook(webhook_payload)
        
        # Verify Subscription Period wurde geupdated
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == 'sub_test123'  # subscription_id


@pytest.mark.asyncio
async def test_webhook_payment_failed(mock_stripe):
    """Test Stripe Webhook: payment_intent.payment_failed"""
    from app.api.v1.webhooks import handle_stripe_webhook
    from app.services.notification_service import notification_service
    
    webhook_payload = {
        'type': 'payment_intent.payment_failed',
        'data': {
            'object': {
                'id': 'pi_failed',
                'customer': 'cus_test123',
                'amount': 4900,
                'last_payment_error': {
                    'message': 'Insufficient funds'
                }
            }
        }
    }
    
    with patch.object(notification_service, 'send_payment_failure_email', new_callable=AsyncMock) as mock_email:
        await handle_stripe_webhook(webhook_payload)
        
        # Verify Email wurde gesendet
        mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_subscription_deleted():
    """Test Stripe Webhook: customer.subscription.deleted (Cancel)"""
    from app.api.v1.webhooks import handle_stripe_webhook
    from app.services.user_service import user_service
    
    webhook_payload = {
        'type': 'customer.subscription.deleted',
        'data': {
            'object': {
                'id': 'sub_cancelled',
                'customer': 'cus_test123',
                'status': 'canceled'
            }
        }
    }
    
    with patch.object(user_service, 'downgrade_to_community', new_callable=AsyncMock) as mock_downgrade:
        await handle_stripe_webhook(webhook_payload)
        
        # Verify User wurde zu Community downgraded
        mock_downgrade.assert_called_once()
        call_args = mock_downgrade.call_args
        assert call_args[0][0] == 'sub_cancelled'  # subscription_id


# ============================================================================
# TEST SUITE 4: Retry Logic
# ============================================================================

@pytest.mark.asyncio
async def test_payment_retry_on_temporary_failure(mock_stripe):
    """Test automatischer Retry bei temporären Fehlern"""
    from app.services.payment_service import payment_service
    
    # Mock: 1. Versuch failed, 2. Versuch succeeded
    mock_stripe['payment_intent'].retrieve.side_effect = [
        Mock(status='requires_payment_method'),  # 1. Versuch: fehlgeschlagen
        Mock(status='succeeded', metadata={'user_id': 'test-123', 'plan': 'pro'})  # 2. Versuch: Erfolg
    ]
    
    with patch.object(payment_service, 'retry_payment', new_callable=AsyncMock) as mock_retry:
        mock_retry.return_value = {'status': 'succeeded'}
        
        result = await payment_service.process_payment_with_retry(
            payment_intent_id='pi_retry',
            max_retries=3
        )
        
        assert result['status'] == 'succeeded'
        mock_retry.assert_called_once()


@pytest.mark.asyncio
async def test_payment_fails_after_max_retries(mock_stripe):
    """Test Downgrade nach 3 fehlgeschlagenen Versuchen"""
    from app.services.payment_service import payment_service
    from app.services.user_service import user_service
    
    # Alle 3 Versuche schlagen fehl
    mock_stripe['payment_intent'].retrieve.return_value = Mock(status='payment_failed')
    
    with patch.object(user_service, 'downgrade_to_community', new_callable=AsyncMock) as mock_downgrade:
        with pytest.raises(HTTPException) as exc_info:
            await payment_service.process_payment_with_retry(
                payment_intent_id='pi_fail_permanent',
                max_retries=3
            )
        
        assert exc_info.value.status_code == 402
        assert "max retries" in str(exc_info.value.detail).lower()
        
        # Nach 3 Fails → Downgrade
        mock_downgrade.assert_called_once()


# ============================================================================
# TEST SUITE 5: Price Calculations
# ============================================================================

def test_calculate_plan_price():
    """Test korrekte Plan-Preise"""
    from app.services.payment_service import payment_service
    
    # Monthly Prices
    assert payment_service.calculate_price(SubscriptionPlan.COMMUNITY, 'monthly') == 0
    assert payment_service.calculate_price(SubscriptionPlan.STARTER, 'monthly') == 1900  # $19
    assert payment_service.calculate_price(SubscriptionPlan.PRO, 'monthly') == 4900  # $49
    assert payment_service.calculate_price(SubscriptionPlan.BUSINESS, 'monthly') == 9900  # $99
    assert payment_service.calculate_price(SubscriptionPlan.PLUS, 'monthly') == 19900  # $199
    assert payment_service.calculate_price(SubscriptionPlan.ENTERPRISE, 'monthly') == 49900  # $499


def test_calculate_annual_discount():
    """Test Annual Discount (20%)"""
    from app.services.payment_service import payment_service
    
    # Pro: $49/mo * 12 = $588, mit 20% = $470.40
    annual_price = payment_service.calculate_price(SubscriptionPlan.PRO, 'annual')
    assert annual_price == 47040  # $470.40 in cents
    
    # Plus: $199/mo * 12 = $2388, mit 20% = $1910.40
    annual_price = payment_service.calculate_price(SubscriptionPlan.PLUS, 'annual')
    assert annual_price == 191040  # $1910.40 in cents


# ============================================================================
# TEST SUITE 6: Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_duplicate_payment_prevention(mock_stripe, test_user):
    """Test dass doppelte Payments verhindert werden"""
    from app.services.payment_service import payment_service
    
    # User hat bereits aktive Subscription
    test_user.subscription_id = 'sub_existing'
    test_user.subscription_status = SubscriptionStatus.ACTIVE
    test_user.plan = SubscriptionPlan.PRO
    
    # Versucht nochmal zu upgraden
    with pytest.raises(HTTPException) as exc_info:
        await payment_service.create_payment_intent(
            user=test_user,
            plan=SubscriptionPlan.PLUS,
            billing_cycle='monthly'
        )
    
    assert exc_info.value.status_code == 400
    assert "already has active subscription" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_invalid_plan_upgrade(mock_stripe, test_user):
    """Test dass Downgrade via Payment verhindert wird"""
    from app.services.payment_service import payment_service
    
    # User ist auf Plus Plan
    test_user.plan = SubscriptionPlan.PLUS
    
    # Versucht zu Pro zu "upgraden" (ist eigentlich Downgrade)
    with pytest.raises(HTTPException) as exc_info:
        await payment_service.create_payment_intent(
            user=test_user,
            plan=SubscriptionPlan.PRO,
            billing_cycle='monthly'
        )
    
    assert exc_info.value.status_code == 400
    assert "downgrade" in str(exc_info.value.detail).lower()


# ============================================================================
# SUMMARY
# ============================================================================
"""
Test Coverage:
✅ Payment Intent Creation (Pro, Plus, Annual)
✅ Payment Success → Plan Update
✅ Payment Failure → No Update
✅ Webhooks (invoice.paid, payment_failed, subscription.deleted)
✅ Retry Logic (3 Versuche, dann Downgrade)
✅ Price Calculations (Monthly, Annual mit 20% Discount)
✅ Edge Cases (Duplicate Payment, Invalid Upgrade)

Total: 15 Tests für Payment Integration
"""
