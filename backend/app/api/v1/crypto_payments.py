"""
Crypto Payment API Endpoints
Handles cryptocurrency payments via NOWPayments
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

# Auth dependencies (fallback in TEST_MODE)
try:
    from app.auth.middleware import require_auth, get_current_user  # type: ignore
except Exception:  # pragma: no cover
    def require_auth():  # type: ignore
        def _dep():
            return {"user_id": "test-user", "email": "test@example.com"}
        return _dep
    def get_current_user():  # type: ignore
        def _dep():
            return {"user_id": "test-user", "email": "test@example.com"}
        return _dep
from app.services.crypto_payments import crypto_payment_service
from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crypto-payments", tags=["crypto-payments"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CurrencyInfo(BaseModel):
    """Cryptocurrency information"""
    code: str
    name: str
    symbol: str
    logo: str
    network: str


class AvailableCurrenciesResponse(BaseModel):
    """Available cryptocurrencies response"""
    currencies: List[CurrencyInfo]


class PaymentEstimateRequest(BaseModel):
    """Payment estimate request"""
    plan: str = Field(..., description="Subscription plan name")
    currency: str = Field(..., description="Crypto currency code")


class PaymentEstimateResponse(BaseModel):
    """Payment estimate response"""
    plan: str
    price_usd: float
    currency: str
    estimated_amount: float
    minimum_amount: float
    exchange_rate: float


class CreatePaymentRequest(BaseModel):
    """Create crypto payment request"""
    plan: str = Field(..., description="Subscription plan (community, starter, pro, business, plus, enterprise)")
    currency: str = Field(..., description="Crypto currency code (btc, eth, usdt, etc.)")
    interval: Optional[str] = Field("monthly", description="Billing interval (monthly, yearly)")
    recurring: bool = Field(False, description="Create recurring subscription")


class CreatePaymentResponse(BaseModel):
    """Create payment response"""
    payment_id: int
    order_id: str
    pay_address: str
    pay_amount: float
    pay_currency: str
    price_amount: float
    price_currency: str
    payment_status: str
    invoice_url: str
    expires_at: Optional[str]


class PaymentStatusResponse(BaseModel):
    """Payment status response"""
    payment_id: int
    order_id: str
    payment_status: str
    pay_address: Optional[str]
    pay_amount: float
    pay_currency: str
    actual_pay_amount: Optional[float]
    pay_in_hash: Optional[str]
    created_at: str
    updated_at: Optional[str]
    invoice_url: Optional[str]


class PaymentHistoryResponse(BaseModel):
    """Payment history response"""
    payments: List[Dict[str, Any]]
    total: int


class SubscriptionResponse(BaseModel):
    """Crypto subscription response"""
    id: str
    plan: str
    currency: str
    amount_usd: float
    interval: str
    is_active: bool
    next_billing_date: str
    successful_payments: int
    failed_payments: int


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/currencies", response_model=AvailableCurrenciesResponse)
async def get_available_currencies():
    """
    Get list of available cryptocurrencies
    
    **Returns 30 most popular cryptocurrencies:**
    - Bitcoin (BTC)
    - Ethereum (ETH)
    - USDT, USDC (Stablecoins)
    - BNB, Solana, Polygon, Avalanche
    - And 22 more...
    """
    try:
        available = await crypto_payment_service.get_available_currencies()
        
        currencies = [
            CurrencyInfo(
                code=code,
                **crypto_payment_service.get_currency_info(code)
            )
            for code in available
        ]
        
        return AvailableCurrenciesResponse(currencies=currencies)
    except Exception as e:
        logger.error(f"Error fetching currencies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch currencies")


@router.post("/estimate", response_model=PaymentEstimateResponse)
async def estimate_payment(request: PaymentEstimateRequest):
    """
    Get payment estimate for plan and currency
    
    **Returns:**
    - USD price for plan
    - Estimated crypto amount
    - Current exchange rate
    - Minimum payment amount
    """
    try:
        # Get plan price
        price_usd = crypto_payment_service.PLAN_PRICES.get(request.plan.lower())
        if price_usd is None:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {request.plan}")
        
        # Get estimate
        estimate = await crypto_payment_service.get_estimate(
            amount_usd=price_usd,
            currency_from="usd",
            currency_to=request.currency.lower()
        )
        
        if not estimate:
            raise HTTPException(status_code=400, detail="Failed to get estimate")
        
        # Get minimum amount
        min_amount = await crypto_payment_service.get_minimum_payment_amount(
            request.currency.lower()
        )
        
        return PaymentEstimateResponse(
            plan=request.plan,
            price_usd=price_usd,
            currency=request.currency.lower(),
            estimated_amount=float(estimate.get("estimated_amount", 0)),
            minimum_amount=float(min_amount or 0),
            exchange_rate=float(estimate.get("estimated_amount", 0)) / price_usd if price_usd > 0 else 0
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to estimate payment")


@router.post("/create", response_model=CreatePaymentResponse, dependencies=[Depends(require_auth)])
async def create_payment(
    request: CreatePaymentRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create crypto payment for subscription
    
    **Creates:**
    - Payment order in NOWPayments
    - Payment record in database
    - Optional recurring subscription
    
    **Returns payment details with deposit address**
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Generate unique order ID
        order_id = f"order_{uuid.uuid4().hex[:16]}"
        
        # Create payment
        payment_data = await crypto_payment_service.create_payment(
            plan_name=request.plan,
            currency=request.currency.lower(),
            user_id=user_id,
            order_id=order_id
        )
        
        if not payment_data:
            raise HTTPException(status_code=400, detail="Failed to create payment")
        
        # Save to database
        try:
            query = """
                INSERT INTO crypto_payments (
                    payment_id, order_id, user_id, plan_name,
                    price_amount, price_currency, pay_amount, pay_currency,
                    pay_address, payin_extra_id, payment_status,
                    invoice_url, expires_at, purchase_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """
            await postgres_client.execute(
                query,
                payment_data["payment_id"],
                order_id,
                user_id,
                request.plan,
                float(payment_data["price_amount"]),
                payment_data["price_currency"],
                float(payment_data["pay_amount"]),
                payment_data["pay_currency"],
                payment_data.get("pay_address"),
                payment_data.get("payin_extra_id"),
                payment_data["payment_status"],
                crypto_payment_service.get_payment_url(payment_data["payment_id"]),
                datetime.fromisoformat(payment_data["expiration_estimate_date"]) if payment_data.get("expiration_estimate_date") else None,
                payment_data.get("purchase_id")
            )
        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            # Continue even if DB save fails - payment still created in NOWPayments
        
        # Create recurring subscription if requested
        if request.recurring:
            try:
                subscription_data = await crypto_payment_service.create_recurring_payment(
                    plan_name=request.plan,
                    currency=request.currency.lower(),
                    user_id=user_id,
                    interval=request.interval
                )
                
                if subscription_data:
                    await postgres_client.execute(
                        """
                        INSERT INTO crypto_subscriptions (
                            user_id, plan_name, currency, amount_usd,
                            interval, next_billing_date
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        user_id,
                        request.plan,
                        request.currency.lower(),
                        subscription_data["amount_usd"],
                        subscription_data["interval"],
                        datetime.fromisoformat(subscription_data["next_billing_date"])
                    )
            except Exception as sub_error:
                logger.error(f"Subscription creation error: {sub_error}")
                # Continue - one-time payment still works
        
        return CreatePaymentResponse(
            payment_id=payment_data["payment_id"],
            order_id=order_id,
            pay_address=payment_data["pay_address"],
            pay_amount=float(payment_data["pay_amount"]),
            pay_currency=payment_data["pay_currency"],
            price_amount=float(payment_data["price_amount"]),
            price_currency=payment_data["price_currency"],
            payment_status=payment_data["payment_status"],
            invoice_url=crypto_payment_service.get_payment_url(payment_data["payment_id"]),
            expires_at=payment_data.get("expiration_estimate_date")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment")


@router.get("/status/{payment_id}", response_model=PaymentStatusResponse, dependencies=[Depends(require_auth)])
async def get_payment_status(
    payment_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get payment status by ID
    
    **Returns:**
    - Current payment status
    - Transaction hash (if confirmed)
    - Deposit address
    - Amount details
    """
    try:
        user_id = current_user.get("id")
        
        # Check payment belongs to user
        payment = await postgres_client.fetchrow(
            "SELECT * FROM crypto_payments WHERE payment_id = $1 AND user_id = $2",
            payment_id,
            user_id
        )
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Get updated status from NOWPayments
        status_data = await crypto_payment_service.get_payment_status(payment_id)
        
        if status_data:
            # Update database
            await postgres_client.execute(
                """
                UPDATE crypto_payments
                SET payment_status = $1,
                    actual_pay_amount = $2,
                    pay_in_hash = $3,
                    updated_at = NOW()
                WHERE payment_id = $4
                """,
                status_data["payment_status"],
                float(status_data.get("actually_paid", 0)) if status_data.get("actually_paid") else None,
                status_data.get("payin_hash"),
                payment_id
            )
            
            return PaymentStatusResponse(
                payment_id=payment_id,
                order_id=payment["order_id"],
                payment_status=status_data["payment_status"],
                pay_address=payment["pay_address"],
                pay_amount=float(payment["pay_amount"]),
                pay_currency=payment["pay_currency"],
                actual_pay_amount=float(status_data.get("actually_paid", 0)) if status_data.get("actually_paid") else None,
                pay_in_hash=status_data.get("payin_hash"),
                created_at=payment["created_at"].isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                invoice_url=payment["invoice_url"]
            )
        else:
            # Return database data
            return PaymentStatusResponse(
                payment_id=payment_id,
                order_id=payment["order_id"],
                payment_status=payment["payment_status"],
                pay_address=payment["pay_address"],
                pay_amount=float(payment["pay_amount"]),
                pay_currency=payment["pay_currency"],
                actual_pay_amount=float(payment["actual_pay_amount"]) if payment.get("actual_pay_amount") else None,
                pay_in_hash=payment.get("pay_in_hash"),
                created_at=payment["created_at"].isoformat(),
                updated_at=payment["updated_at"].isoformat() if payment.get("updated_at") else None,
                invoice_url=payment["invoice_url"]
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment status")


@router.get("/history", response_model=PaymentHistoryResponse, dependencies=[Depends(require_auth)])
async def get_payment_history(
    current_user: Dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    Get payment history for current user
    
    **Returns list of all crypto payments**
    """
    try:
        user_id = current_user.get("id")
        
        # Get payments
        payments = await postgres_client.fetch(
            """
            SELECT * FROM crypto_payments
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_id,
            limit,
            offset
        )
        
        # Get total count
        total = await postgres_client.fetchval(
            "SELECT COUNT(*) FROM crypto_payments WHERE user_id = $1",
            user_id
        )
        
        return PaymentHistoryResponse(
            payments=[dict(p) for p in payments],
            total=total or 0
        )
    except Exception as e:
        logger.error(f"Error getting payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment history")


@router.get("/subscriptions", response_model=List[SubscriptionResponse], dependencies=[Depends(require_auth)])
async def get_subscriptions(current_user: Dict = Depends(get_current_user)):
    """
    Get active crypto subscriptions
    
    **Returns list of recurring subscriptions**
    """
    try:
        user_id = current_user.get("id")
        
        subscriptions = await postgres_client.fetch(
            """
            SELECT * FROM crypto_subscriptions
            WHERE user_id = $1 AND is_active = TRUE
            ORDER BY created_at DESC
            """,
            user_id
        )
        
        return [
            SubscriptionResponse(
                id=str(sub["id"]),
                plan=sub["plan_name"],
                currency=sub["currency"],
                amount_usd=float(sub["amount_usd"]),
                interval=sub["interval"],
                is_active=sub["is_active"],
                next_billing_date=sub["next_billing_date"].isoformat(),
                successful_payments=sub["successful_payments"],
                failed_payments=sub["failed_payments"]
            )
            for sub in subscriptions
        ]
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscriptions")


@router.post("/subscriptions/{subscription_id}/cancel", dependencies=[Depends(require_auth)])
async def cancel_subscription(
    subscription_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Cancel crypto subscription
    
    **Stops recurring billing**
    """
    try:
        user_id = current_user.get("id")
        
        # Check subscription belongs to user
        subscription = await postgres_client.fetchrow(
            "SELECT * FROM crypto_subscriptions WHERE id = $1 AND user_id = $2",
            uuid.UUID(subscription_id),
            user_id
        )
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Cancel subscription
        await postgres_client.execute(
            """
            UPDATE crypto_subscriptions
            SET is_active = FALSE, cancelled_at = NOW(), updated_at = NOW()
            WHERE id = $1
            """,
            uuid.UUID(subscription_id)
        )
        
        return {"message": "Subscription cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


class ExtendPaymentRequest(BaseModel):
    """Extend payment client expiry window"""
    minutes: int = Field(10, ge=1, le=60, description="Number of minutes to extend (1-60)")


@router.post("/extend/{payment_id}", dependencies=[Depends(require_auth)])
async def extend_payment_expiry(
    payment_id: int,
    body: ExtendPaymentRequest = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Extend the local client expiry window for a pending payment by N minutes.
    Note: NOWPayments does not support server-side expiry extension; this endpoint
    adjusts our client expiry (DB: expires_at) to improve UX during on-chain delays.
    """
    try:
        user_id = current_user.get("id")
        # Load payment and verify ownership
        payment = await postgres_client.fetchrow(
            "SELECT * FROM crypto_payments WHERE payment_id = $1 AND user_id = $2",
            payment_id,
            user_id
        )
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment["payment_status"] != "pending":
            raise HTTPException(status_code=400, detail="Only pending payments can be extended")

        base = payment["expires_at"] if payment.get("expires_at") else datetime.utcnow()
        if isinstance(base, str):
            # Safety: in case DB returns string
            base = datetime.fromisoformat(base)
        # If already expired, start from now
        if base < datetime.utcnow():
            base = datetime.utcnow()

        new_expiry = base + timedelta(minutes=body.minutes)

        await postgres_client.execute(
            """
            UPDATE crypto_payments
            SET expires_at = $1, updated_at = NOW()
            WHERE payment_id = $2 AND user_id = $3
            """,
            new_expiry,
            payment_id,
            user_id,
        )

        return {
            "payment_id": payment_id,
            "payment_status": payment["payment_status"],
            "client_expiry": new_expiry.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending payment expiry: {e}")
        raise HTTPException(status_code=500, detail="Failed to extend payment expiry")


@router.get("/qr-code/{payment_id}", dependencies=[Depends(require_auth)])
async def get_payment_qr_code(
    payment_id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate QR code for payment address
    
    **Returns base64-encoded PNG image**
    """
    try:
        user_id = current_user.get("id")
        
        # Get payment
        payment = await postgres_client.fetchrow(
            "SELECT * FROM crypto_payments WHERE payment_id = $1 AND user_id = $2",
            payment_id,
            user_id
        )
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Generate QR code
        qr_code = crypto_payment_service.generate_qr_code(
            address=payment["pay_address"],
            amount=float(payment["pay_amount"]),
            currency=payment["pay_currency"]
        )
        
        if not qr_code:
            raise HTTPException(status_code=500, detail="Failed to generate QR code")
        
        return {
            "qr_code": qr_code,
            "address": payment["pay_address"],
            "amount": float(payment["pay_amount"]),
            "currency": payment["pay_currency"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate QR code")

# ============================================================================
# Internal BTC Wallet Management (Admin Only)
# ============================================================================

from app.services.btc_wallet_service import btc_wallet_service
from app.auth.dependencies import require_admin
from app.models.crypto_payment import CryptoWallet
from app.db.postgres import get_db
from sqlalchemy.orm import Session


class CreateWalletRequest(BaseModel):
    """Request to create a new BTC wallet"""
    pass  # No params needed


class WalletResponse(BaseModel):
    """BTC wallet response"""
    address: str
    balance: float
    created_at: datetime


class WalletTransaction(BaseModel):
    """BTC transaction info"""
    hash: str
    value: float
    confirmations: int
    time: int


@router.post("/admin/wallet/create", response_model=WalletResponse)
async def create_btc_wallet(
    request: CreateWalletRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new BTC wallet for the platform."""
    try:
        # Check if wallet already exists
        existing = btc_wallet_service.get_wallet(db, "platform")
        if existing:
            raise HTTPException(status_code=400, detail="Platform BTC wallet already exists")

        # Generate new address
        wallet_data = btc_wallet_service.generate_address()
        
        # Store in database
        wallet = btc_wallet_service.store_wallet(
            db=db,
            user_id="platform",
            address=wallet_data['address'],
            private_key_encrypted=wallet_data['private_key_encrypted']
        )

        # Update balance
        btc_wallet_service.update_balance(db, wallet)

        return WalletResponse(
            address=wallet.address,
            balance=wallet.balance,
            created_at=wallet.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating BTC wallet: {e}")
        raise HTTPException(status_code=500, detail="Failed to create wallet")


@router.get("/admin/wallet", response_model=WalletResponse)
async def get_btc_wallet(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get platform BTC wallet info."""
    try:
        wallet = btc_wallet_service.get_wallet(db, "platform")
        if not wallet:
            raise HTTPException(status_code=404, detail="BTC wallet not found")

        # Update balance
        btc_wallet_service.update_balance(db, wallet)

        return WalletResponse(
            address=wallet.address,
            balance=wallet.balance,
            created_at=wallet.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting BTC wallet: {e}")
        raise HTTPException(status_code=500, detail="Failed to get wallet")


@router.get("/admin/wallet/transactions", response_model=List[WalletTransaction])
async def get_btc_transactions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get recent BTC transactions."""
    try:
        wallet = btc_wallet_service.get_wallet(db, "platform")
        if not wallet:
            raise HTTPException(status_code=404, detail="BTC wallet not found")

        transactions = btc_wallet_service.get_transactions(wallet.address)
        
        return [
            WalletTransaction(
                hash=tx['hash'],
                value=tx['result'] / 100000000 if 'result' in tx else 0,  # Convert satoshis to BTC
                confirmations=tx.get('confirmations', 0),
                time=tx.get('time', 0)
            )
            for tx in transactions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting BTC transactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get transactions")


@router.post("/admin/wallet/refresh-balance")
async def refresh_wallet_balance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Refresh wallet balance."""
    try:
        wallet = btc_wallet_service.get_wallet(db, "platform")
        if not wallet:
            raise HTTPException(status_code=404, detail="BTC wallet not found")

        btc_wallet_service.update_balance(db, wallet)
        return {"balance": wallet.balance}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing balance: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh balance")
