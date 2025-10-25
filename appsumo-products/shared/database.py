"""
Shared Database Models für alle AppSumo Produkte
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model for all products"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Optional for AppSumo users
    
    # AppSumo Integration
    license_key = Column(String, unique=True, nullable=True, index=True)
    plan_tier = Column(Integer, default=1)
    plan_name = Column(String, default="tier_1")
    product_id = Column(String, nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Plan features & limits
    features = Column(JSON, default={})
    limits = Column(JSON, default={})
    
    # Usage tracking
    api_calls_today = Column(Integer, default=0)
    api_calls_reset_at = Column(DateTime, nullable=True)

class APIKey(Base):
    """API Keys for programmatic access"""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

class UsageMetric(Base):
    """Track usage for billing/limits"""
    __tablename__ = "usage_metrics"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, nullable=False)
    
    # Metrics
    metric_type = Column(String, nullable=False)  # api_call, feature_use, etc.
    metric_value = Column(Integer, default=1)
    
    # Metadata
    timestamp = Column(DateTime, server_default=func.now())
    metadata = Column(JSON, default={})

class SavedItem(Base):
    """Generic saved items (cases, reports, traces, etc.)"""
    __tablename__ = "saved_items"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, nullable=False)
    
    # Content
    item_type = Column(String, nullable=False)  # case, report, trace, etc.
    title = Column(String, nullable=False)
    data = Column(JSON, default={})
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_public = Column(Boolean, default=False)
    tags = Column(JSON, default=[])

class UserSettings(Base):
    """User preferences and settings"""
    __tablename__ = "user_settings"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    product_id = Column(String, nullable=False)
    
    # Settings
    preferences = Column(JSON, default={})
    notifications = Column(JSON, default={})
    theme = Column(String, default="light")
    language = Column(String, default="en")
    
    # Metadata
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Database Helper Functions
def create_tables(engine):
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_user_by_email(session, email: str):
    """Get user by email"""
    return session.query(User).filter(User.email == email).first()

def get_user_by_license(session, license_key: str):
    """Get user by license key"""
    return session.query(User).filter(User.license_key == license_key).first()

def increment_api_calls(session, user_id: str):
    """Increment API call counter"""
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        # Reset counter if new day
        if user.api_calls_reset_at and user.api_calls_reset_at.date() < datetime.utcnow().date():
            user.api_calls_today = 0
            user.api_calls_reset_at = datetime.utcnow()
        
        user.api_calls_today += 1
        session.commit()
        return user.api_calls_today
    return 0

def check_rate_limit(session, user_id: str, plan_tier: int) -> bool:
    """Check if user is within rate limits"""
    from .appsumo import PLAN_LIMITS
    
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    limits = PLAN_LIMITS.get(plan_tier)
    if not limits:
        return False
    
    daily_limit = limits.limits.get("api_calls_per_day", 100)
    
    # -1 means unlimited
    if daily_limit == -1:
        return True
    
    # Reset if new day
    if user.api_calls_reset_at and user.api_calls_reset_at.date() < datetime.utcnow().date():
        user.api_calls_today = 0
        user.api_calls_reset_at = datetime.utcnow()
        session.commit()
    
    return user.api_calls_today < daily_limit
