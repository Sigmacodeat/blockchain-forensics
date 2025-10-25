"""
Analytics Data Models
Für Ultimate Analytics System
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, JSONB, Float
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base_class import Base


class AnalyticsEvent(Base):
    """
    Complete Analytics Event
    Speichert ALLE erfassten Daten
    """
    __tablename__ = "analytics_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    
    # Network & Device
    ip_address = Column(String, nullable=True)
    fingerprint = Column(JSONB, nullable=False)  # Complete fingerprint data
    
    # Behavior
    behavior = Column(JSONB, nullable=False)  # Mouse, clicks, scroll, interactions
    
    # Performance
    performance = Column(JSONB, nullable=False)  # Page load, API latencies, resources
    
    # Network Info
    network = Column(JSONB, nullable=True)  # Connection type, speed
    
    # Errors
    errors = Column(JSONB, nullable=False, default=list)  # Frontend errors
    
    # Page Context
    page_url = Column(String, nullable=False, index=True)
    page_title = Column(String, nullable=True)
    referrer = Column(String, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False)  # Client timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class AIInsight(Base):
    """
    AI-Generated Insights
    """
    __tablename__ = "ai_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    
    # Predictions
    conversion_probability = Column(Float, nullable=True)  # 0-1
    churn_risk = Column(Float, nullable=True)  # 0-1
    engagement_score = Column(Float, nullable=True)  # 0-1
    
    # Insights
    insights = Column(JSONB, nullable=False)  # AI-generated insights
    recommendations = Column(JSONB, nullable=False)  # Recommended actions
    
    # Patterns
    behavior_patterns = Column(JSONB, nullable=True)
    performance_issues = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class AutoOptimization(Base):
    """
    AI-Generated Optimizations
    """
    __tablename__ = "auto_optimizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Optimization Type
    optimization_type = Column(String, nullable=False)  # 'ab_test', 'performance', 'ui_ux', 'error_fix'
    
    # Target
    target_page = Column(String, nullable=True)
    target_element = Column(String, nullable=True)
    
    # Details
    description = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)  # Why AI suggests this
    expected_impact = Column(String, nullable=True)  # '+20% conversion'
    
    # Implementation
    implementation_code = Column(Text, nullable=True)  # Auto-generated code
    ab_test_variants = Column(JSONB, nullable=True)  # A/B test variants
    
    # Status
    status = Column(String, nullable=False, default='pending')  # pending, approved, implemented, rejected
    
    # Metadata
    priority = Column(Integer, nullable=False, default=5)  # 1-10
    confidence = Column(Float, nullable=False)  # 0-1
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
