"""
Chat Session Models
Extended mit User-Identity-Resolution & Analytics
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class ChatSession(Base):
    """
    Chat Session Model - Extended
    
    Tracks:
    - Session metadata (IP, User-Agent, Fingerprint)
    - User-Identity (user_id, anonymous_id)
    - UTM-Parameters (for attribution)
    - Referrer (for traffic-source)
    """
    __tablename__ = "chat_sessions"
    
    # Identity
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)  # Authenticated user
    anonymous_id = Column(String, nullable=True, index=True)  # Anonymous tracking ID
    
    # Metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    fingerprint = Column(String, nullable=True)  # Browser fingerprint
    
    # Attribution
    utm_source = Column(String, nullable=True)  # e.g., "google", "twitter"
    utm_medium = Column(String, nullable=True)  # e.g., "cpc", "organic"
    utm_campaign = Column(String, nullable=True)  # e.g., "summer_2025"
    utm_term = Column(String, nullable=True)  # e.g., "blockchain forensics"
    utm_content = Column(String, nullable=True)  # e.g., "banner_ad_1"
    referrer = Column(String, nullable=True)  # Full referrer URL
    
    # Language & Locale
    language = Column(String, nullable=True, default="en")  # User's language
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    events = relationship("ConversationEvent", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    Individual Chat Message
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True)  # Tool calls, errors, intents, sentiment, etc.
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class ConversationEvent(Base):
    """
    Conversion-Events für Funnel-Tracking
    
    Event-Types:
    - page_view: Landing
    - chat_started: First message
    - demo_viewed: Demo opened
    - trial_started: Trial activated
    - payment_initiated: Payment started
    - payment_completed: Payment successful
    - signup_completed: Account registered
    """
    __tablename__ = "conversation_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Identity
    user_id = Column(String, nullable=True, index=True)
    anonymous_id = Column(String, nullable=True, index=True)
    
    # Event
    event_type = Column(String, nullable=False, index=True)
    event_data = Column(JSONB, nullable=True)  # Additional metadata
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="events")
