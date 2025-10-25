"""
AppSumo Models
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Boolean, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class AppSumoCode(Base):
    """AppSumo Redemption Code"""
    __tablename__ = "appsumo_codes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    product = Column(String(100), nullable=False, index=True)
    tier = Column(Integer, nullable=False)
    status = Column(String(20), default='active', index=True)
    
    # Redemption
    redeemed_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    redeemed_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    created_by_admin_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # AppSumo Integration
    appsumo_invoice_id = Column(String(100), nullable=True)
    appsumo_purchase_date = Column(DateTime, nullable=True)
    
    # Analytics
    redemption_ip = Column(INET, nullable=True)
    redemption_user_agent = Column(String, nullable=True)


class AppSumoActivation(Base):
    """User Product Activation"""
    __tablename__ = "appsumo_activations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    code_id = Column(UUID(as_uuid=True), ForeignKey('appsumo_codes.id'), nullable=False)
    product = Column(String(100), nullable=False, index=True)
    tier = Column(Integer, nullable=False)
    
    # Activation Details
    activated_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(20), default='active', index=True)
    
    # Features granted
    features = Column(JSON, default={})
    limits = Column(JSON, default={})
    
    # Analytics
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)


class AppSumoRevenue(Base):
    """Revenue Tracking"""
    __tablename__ = "appsumo_revenue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_id = Column(UUID(as_uuid=True), ForeignKey('appsumo_codes.id'), nullable=False)
    product = Column(String(100), nullable=False, index=True)
    tier = Column(Integer, nullable=False)
    
    # Revenue
    amount_usd = Column(DECIMAL(10, 2), nullable=False)
    appsumo_fee_usd = Column(DECIMAL(10, 2), nullable=True)
    net_revenue_usd = Column(DECIMAL(10, 2), nullable=True)
    
    # Dates
    sale_date = Column(DateTime, nullable=False, index=True)
    recorded_at = Column(DateTime, default=func.now())
    
    # Conversion Tracking
    converted_to_saas = Column(Boolean, default=False)
    conversion_date = Column(DateTime, nullable=True)
    monthly_recurring_revenue = Column(DECIMAL(10, 2), nullable=True)
