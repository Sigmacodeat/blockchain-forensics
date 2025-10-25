"""
Crypto Payment Models
SQLAlchemy models for cryptocurrency payment tracking
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class PaymentStatus(enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    WAITING = "waiting"  # Waiting for crypto deposit
    CONFIRMING = "confirming"  # Transaction seen, waiting for confirmations
    CONFIRMED = "confirmed"  # Payment confirmed
    SENDING = "sending"  # Sending crypto to our wallet
    FINISHED = "finished"  # Payment completed
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class CryptoPayment(Base):
    """
    Crypto payment record
    Tracks cryptocurrency payments via NOWPayments
    """
    __tablename__ = "crypto_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # NOWPayments IDs
    payment_id = Column(Integer, unique=True, nullable=False, index=True)  # NOWPayments payment ID
    order_id = Column(String(255), unique=True, nullable=False, index=True)  # Our internal order ID
    
    # User & Subscription
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_name = Column(String(50), nullable=False)  # community, pro, business, plus, enterprise
    
    # Payment Details
    price_amount = Column(Float, nullable=False)  # Amount in USD
    price_currency = Column(String(10), default="usd")
    pay_amount = Column(Float, nullable=False)  # Amount in crypto
    pay_currency = Column(String(10), nullable=False)  # btc, eth, usdt, etc.
    
    # Transaction Info
    pay_address = Column(String(255))  # Deposit address
    payin_extra_id = Column(String(255))  # Extra ID for some currencies (XRP, XLM)
    pay_in_hash = Column(String(255), index=True)  # Blockchain transaction hash
    
    # Status
    payment_status = Column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Exchange Rate
    actual_pay_amount = Column(Float)  # Actual amount received
    outcome_amount = Column(Float)  # Amount we receive after fees
    outcome_currency = Column(String(10), default="usd")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)  # Payment expiration
    
    # Purchase Info
    purchase_id = Column(String(255))  # NOWPayments purchase_id
    invoice_url = Column(String(512))  # Payment page URL
    
    # Webhooks
    last_webhook_at = Column(DateTime)
    webhook_count = Column(Integer, default=0)
    
    # Notes
    notes = Column(Text)  # Admin notes or error messages
    
    # Relationships
    user = relationship("User", back_populates="crypto_payments")
    
    def __repr__(self):
        return f"<CryptoPayment {self.order_id} - {self.payment_status.value} - {self.pay_currency.upper()}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "plan_name": self.plan_name,
            "price_amount": self.price_amount,
            "price_currency": self.price_currency,
            "pay_amount": self.pay_amount,
            "pay_currency": self.pay_currency,
            "pay_address": self.pay_address,
            "payin_extra_id": self.payin_extra_id,
            "pay_in_hash": self.pay_in_hash,
            "payment_status": self.payment_status.value,
            "actual_pay_amount": self.actual_pay_amount,
            "outcome_amount": self.outcome_amount,
            "outcome_currency": self.outcome_currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "purchase_id": self.purchase_id,
            "invoice_url": self.invoice_url,
            "last_webhook_at": self.last_webhook_at.isoformat() if self.last_webhook_at else None,
            "webhook_count": self.webhook_count,
            "notes": self.notes
        }


class CryptoSubscription(Base):
    """
    Crypto subscription for recurring payments
    Since NOWPayments doesn't support native recurring,
    we track and trigger new payments each billing cycle
    """
    __tablename__ = "crypto_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User & Plan
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_name = Column(String(50), nullable=False)
    
    # Payment Details
    currency = Column(String(10), nullable=False)  # btc, eth, etc.
    amount_usd = Column(Float, nullable=False)
    
    # Billing
    interval = Column(String(20), nullable=False)  # monthly, yearly
    next_billing_date = Column(DateTime, nullable=False, index=True)
    last_payment_date = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime)
    
    # Payment History
    successful_payments = Column(Integer, default=0)
    failed_payments = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="crypto_subscriptions")
    
    def __repr__(self):
        return f"<CryptoSubscription {self.user_id} - {self.plan_name} - {self.currency.upper()}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_name": self.plan_name,
            "currency": self.currency,
            "amount_usd": self.amount_usd,
            "interval": self.interval,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None,
            "last_payment_date": self.last_payment_date.isoformat() if self.last_payment_date else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "successful_payments": self.successful_payments,
            "failed_payments": self.failed_payments
        }
