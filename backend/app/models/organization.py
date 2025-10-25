"""
Organization Model - Multi-Tenancy für SaaS
PostgreSQL-basiert mit vollständiger Tenant-Isolation
"""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class OrgPlan(str, Enum):
    """Organization subscription plans"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OrgStatus(str, Enum):
    """Organization status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class Organization(Base):
    """
    Organization table - Multi-Tenant isolation
    All user data belongs to an organization
    """
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)  # External UUID
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-safe identifier
    
    # Owner & Contact
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_email = Column(String(255))
    
    # Subscription
    plan = Column(SAEnum(OrgPlan), default=OrgPlan.FREE, nullable=False)
    status = Column(SAEnum(OrgStatus), default=OrgStatus.ACTIVE, nullable=False)
    
    # Billing
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True)
    subscription_expires_at = Column(DateTime)
    
    # Limits (based on plan)
    max_users = Column(Integer, default=1)
    max_cases = Column(Integer, default=10)
    max_traces_per_month = Column(Integer, default=100)
    
    # Settings
    settings = Column(String)  # JSON string
    features_enabled = Column(String)  # JSON array of feature flags
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    trial_ends_at = Column(DateTime)
    deleted_at = Column(DateTime)  # Soft delete
    
    # Relationships
    # owner = relationship("User", back_populates="owned_organizations")
    # members = relationship("OrgMember", back_populates="organization")


class OrgMember(Base):
    """
    Organization members - Many-to-Many User <-> Organization
    """
    __tablename__ = "org_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Role within organization
    role = Column(String(50), default="member")  # owner, admin, member, viewer
    
    # Permissions
    permissions = Column(String)  # JSON array
    
    # Status
    status = Column(String(20), default="active")  # active, invited, suspended
    invited_by = Column(Integer, ForeignKey("users.id"))
    invited_at = Column(DateTime)
    joined_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # organization = relationship("Organization", back_populates="members")
    # user = relationship("User", foreign_keys=[user_id])


# Pydantic Models for API
class OrganizationCreate(BaseModel):
    """Create organization request"""
    name: str = Field(..., min_length=3, max_length=255)
    contact_email: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """Update organization request"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    contact_email: Optional[str] = None
    max_users: Optional[int] = None
    max_cases: Optional[int] = None


class OrganizationOut(BaseModel):
    """Organization response"""
    id: int
    uuid: str
    name: str
    slug: str
    owner_id: int
    plan: OrgPlan
    status: OrgStatus
    max_users: int
    max_cases: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrgMemberAdd(BaseModel):
    """Add member to organization"""
    user_id: int
    role: str = "member"


class OrgMemberOut(BaseModel):
    """Organization member response"""
    id: int
    organization_id: int
    user_id: int
    role: str
    status: str
    joined_at: Optional[datetime]
    
    class Config:
        from_attributes = True
