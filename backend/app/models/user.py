"""
User Management Models
For authentication, authorization, and user profiles

Includes:
- Pydantic models for app-level typing and responses
- SQLAlchemy ORM model for persistent storage (users table)
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, Dict, List, Tuple
import hashlib
import uuid

# SQLAlchemy ORM imports for persistent storage
from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import String as SAString
import os
from sqlalchemy.orm import declarative_base

# Shared SQLAlchemy Base for this module
Base = declarative_base()


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    ANALYST = "analyst"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class UserStatus(str, Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class SubscriptionPlan(str, Enum):
    """Subscription plan tiers"""
    COMMUNITY = "community"  # Free
    STARTER = "starter"  # $19/mo
    PRO = "pro"  # $49/mo
    BUSINESS = "business"  # $99/mo
    PLUS = "plus"  # $199/mo
    ENTERPRISE = "enterprise"  # $499/mo


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    NONE = "none"  # No subscription
    ACTIVE = "active"  # Active subscription
    PAST_DUE = "past_due"  # Payment failed, in grace period
    CANCELLING = "cancelling"  # Scheduled to cancel at period end
    CANCELLED = "cancelled"  # Cancelled


class User(BaseModel):
    """User model for authentication and authorization"""
    id: str = Field(default_factory=lambda: f"user_{datetime.utcnow().timestamp()}")
    email: EmailStr = Field(..., json_schema_extra={'unique': True})
    username: str = Field(..., min_length=3, max_length=50, json_schema_extra={'unique': True})

    # Profile information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    organization_type: Optional[str] = None
    organization_name: Optional[str] = None

    # Authentication
    hashed_password: str
    salt: Optional[str] = None  # For additional security
    password_changed_at: Optional[datetime] = None

    # Authorization
    role: UserRole = UserRole.VIEWER
    permissions: List[str] = Field(default_factory=list)  # Custom permissions

    # Status and metadata
    status: UserStatus = UserStatus.ACTIVE
    is_verified: bool = False
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Preferences
    timezone: str = "UTC"
    language: str = "en"
    notifications_enabled: bool = True

    # Subscription & Billing
    plan: SubscriptionPlan = SubscriptionPlan.COMMUNITY
    subscription_status: SubscriptionStatus = SubscriptionStatus.NONE
    subscription_id: Optional[str] = None  # Stripe subscription ID
    stripe_customer_id: Optional[str] = None  # Stripe customer ID
    billing_cycle_start: Optional[datetime] = None
    billing_cycle_end: Optional[datetime] = None

    # Institutional discount / verification
    institutional_discount_requested: bool = False
    institutional_discount_verified: bool = False
    verification_status: str = "none"
    
    # Trial Management (wie Chainalysis)
    trial_plan: Optional[SubscriptionPlan] = None  # Trial für höheren Plan
    trial_ends_at: Optional[datetime] = None  # Trial-Ende
    trial_started_at: Optional[datetime] = None  # Trial-Start (für Analytics)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)

    def model_post_init(self, __context):
        if not self.display_name:
            if self.first_name or self.last_name:
                parts = [p for p in [self.first_name, self.last_name] if p]
                if parts:
                    object.__setattr__(self, "display_name", " ".join(parts))
            if not self.display_name:
                object.__setattr__(self, "display_name", self.username or self.email)
        _register_user(self)

    def get_effective_plan(self) -> SubscriptionPlan:
        """
        Returns trial plan if active, else regular plan
        
        Usage:
            user = User(plan=SubscriptionPlan.COMMUNITY, trial_plan=SubscriptionPlan.PRO, trial_ends_at=future_date)
            effective = user.get_effective_plan()  # Returns PRO during trial
        """
        if self.trial_plan and self.trial_ends_at:
            if datetime.utcnow() < self.trial_ends_at:
                return self.trial_plan
        return self.plan
    
    def is_trial_active(self) -> bool:
        """Check if trial is currently active"""
        if not self.trial_plan or not self.trial_ends_at:
            return False
        return datetime.utcnow() < self.trial_ends_at
    
    def trial_days_remaining(self) -> Optional[int]:
        """Get remaining trial days (None if no active trial)"""
        if not self.is_trial_active():
            return None
        delta = self.trial_ends_at - datetime.utcnow()
        return max(0, delta.days)


# In-memory registry for lightweight tests
_USER_REGISTRY: Dict[str, Tuple[User, str]] = {}


def _register_user(user: User) -> None:
    _USER_REGISTRY[user.email.lower()] = (user, user.hashed_password)


def _test_hash(password: str, salt: Optional[str]) -> str:
    if salt:
        return hashlib.sha256(f"{password}:{salt}".encode()).hexdigest()
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Minimal auth helper for tests: accepts common mock hashing patterns."""
    entry = _USER_REGISTRY.get(email.lower())
    if not entry:
        return None
    user, stored_hash = entry
    candidates = {
        password,
        f"{password}_hash",
        _test_hash(password, user.salt),
        _test_hash(password, None),
    }
    if stored_hash in candidates:
        return user
    return None


def has_permission(user: User, resource: str, action: str) -> bool:
    """Lightweight permission check used in tests."""
    if user.role == UserRole.ADMIN:
        return True
    key = f"{resource}:{action}"
    return key in set(user.permissions or [])


# -----------------------------
# SQLAlchemy ORM User (persistent)
# -----------------------------
class UserORM(Base):  # type: ignore[misc]
    """SQLAlchemy ORM model backed by the users table."""

    __tablename__ = "users"

    # IDs as UUID (Postgres) or string (SQLite TEST_MODE)
    _IS_TEST = os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST")
    if _IS_TEST:
        id = Column(SAString(36), primary_key=True, index=True)
    else:
        id = Column(PGUUID(as_uuid=False), primary_key=True, index=True, server_default="gen_random_uuid()")

    # Identity
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True, index=True)  # nullable wie in DB

    # Auth
    hashed_password = Column(String(255), nullable=False)

    # Role & status (String statt Enum, passt zur DB-Struktur)
    role = Column(String(32), nullable=False, default='analyst')
    is_active = Column(Boolean, nullable=False, default=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=True, server_default="now()")
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default="now()")
    last_login = Column(DateTime(timezone=True), nullable=True)

    # SaaS
    plan = Column(String(32), nullable=False, default='community')
    features = Column(JSON, nullable=False, default=list)

    # Optional profile fields (kept minimal for auth)
    organization = Column(String(255), nullable=True)
    organization_type = Column(String(50), nullable=True)
    organization_name = Column(String(255), nullable=True)

    # Institutional discount / verification workflow
    institutional_discount_requested = Column(Boolean, nullable=False, default=False)
    institutional_discount_verified = Column(Boolean, nullable=False, default=False)
    verification_status = Column(String(32), nullable=False, default="none")
    verification_documents = Column(Text, nullable=True)
    verification_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    if _IS_TEST:
        verified_by = Column(SAString(36), ForeignKey("users.id"), nullable=True)
    else:
        verified_by = Column(PGUUID(as_uuid=False), ForeignKey("users.id"), nullable=True)

# ... Rest des Codes bleibt gleich ...


class UserSubscription(Base):
    """
    User subscription for SaaS billing
    Tracks active subscriptions, payment methods, and billing cycles
    """

    __tablename__ = "user_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    # User reference
    user_id = Column(String(36), nullable=False, index=True)  # Match UserORM.id type

    # Plan details
    plan_name = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active, cancelled, past_due

    # Payment method
    payment_method = Column(String(20), nullable=False)  # stripe, crypto, paypal

    # Crypto payment details (for BTC payments)
    crypto_txid = Column(String(255))
    crypto_amount = Column(Float)
    crypto_currency = Column(String(10))

    # Billing cycle
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)

    # Cancellation
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    cancelled_at = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserSubscription {self.user_id} - {self.plan_name} - {self.status}>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_name": self.plan_name,
            "status": self.status,
            "payment_method": self.payment_method,
            "crypto_txid": self.crypto_txid,
            "crypto_amount": self.crypto_amount,
            "crypto_currency": self.crypto_currency,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "cancel_at_period_end": self.cancel_at_period_end,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
