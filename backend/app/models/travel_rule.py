"""
Travel Rule Models
==================

SQLAlchemy models for Travel Rule Protocol (TRP) compliance.
Implements IVMS101 message format for originator and beneficiary information.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()


class TravelRuleStatus(enum.Enum):
    """Status of a Travel Rule message"""
    PREPARED = "prepared"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TravelRuleMessage(Base):
    """Main Travel Rule message table"""

    __tablename__ = "travel_rule_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, index=True)  # Unique message ID
    status = Column(Enum(TravelRuleStatus), default=TravelRuleStatus.PREPARED)

    # IVMS101 Payload (JSON)
    ivms101_payload = Column(JSON, nullable=False)

    # Originator and Beneficiary (extracted for quick access)
    originator_vasp_id = Column(String(255))
    beneficiary_vasp_id = Column(String(255))
    originator_address = Column(String(255))
    beneficiary_address = Column(String(255))
    transaction_amount = Column(String(255))  # Amount as string to preserve precision
    transaction_currency = Column(String(10))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    # Relationships
    status_history = relationship("TravelRuleStatusHistory", back_populates="message")

    def __repr__(self):
        return f"<TravelRuleMessage(id={self.id}, message_id={self.message_id}, status={self.status})>"


class TravelRuleStatusHistory(Base):
    """Status history for audit trail"""

    __tablename__ = "travel_rule_status_history"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("travel_rule_messages.id"), nullable=False)

    old_status = Column(Enum(TravelRuleStatus), nullable=True)
    new_status = Column(Enum(TravelRuleStatus), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String(255))  # User/system identifier
    notes = Column(Text, nullable=True)

    # Relationship
    message = relationship("TravelRuleMessage", back_populates="status_history")

    def __repr__(self):
        return f"<TravelRuleStatusHistory(message_id={self.message_id}, new_status={self.new_status})>"


class TravelRuleParty(Base):
    """Party information for originator/beneficiary"""

    __tablename__ = "travel_rule_parties"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("travel_rule_messages.id"), nullable=False)

    # Party type
    party_type = Column(String(50))  # "originator" or "beneficiary"

    # Basic info
    name = Column(String(255))
    address = Column(JSON)  # Structured address

    # Identification
    customer_id = Column(String(255))
    national_id = Column(JSON)  # Type, number, country

    # Geographic info
    country_of_residence = Column(String(2))  # ISO 3166-1 alpha-2

    # Relationships
    message = relationship("TravelRuleMessage")

    def __repr__(self):
        return f"<TravelRuleParty(message_id={self.message_id}, party_type={self.party_type})>"
