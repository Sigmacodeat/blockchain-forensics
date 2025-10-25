"""
Authentication Models & Schemas
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class UserRole(str, Enum):
    """User Roles für RBAC"""
    ADMIN = "admin"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    VIEWER = "viewer"
    PARTNER = "partner"


class UserBase(BaseModel):
    """Base User Schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    organization: Optional[str] = None


class UserCreate(UserBase):
    """User Creation Schema"""
    password: str = Field(..., min_length=8)
    organization_type: Optional[str] = Field(None, description="Type of organization: police, detective, lawyer, government, exchange, other")
    organization_name: Optional[str] = Field(None, description="Name of organization (e.g., LKA Berlin)")
    wants_institutional_discount: Optional[bool] = Field(False, description="User requests 10% institutional discount")
    referral_code: Optional[str] = None


class UserLogin(BaseModel):
    """Login Schema"""
    email: EmailStr
    password: str


class User(UserBase):
    """User Response Schema"""
    id: str
    role: UserRole
    is_active: bool
    created_at: datetime
    plan: str = Field(description="User subscription plan")
    organization_type: Optional[str] = None
    organization_name: Optional[str] = None
    institutional_discount_requested: bool = False
    institutional_discount_verified: bool = False
    verification_status: Optional[str] = "none"

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT Token Response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token Payload Data"""
    user_id: str
    email: str
    role: UserRole
    # SaaS plan embedded into token (always present, defaults to 'community')
    plan: str = 'community'
    # Organization ID for multi-tenancy (None for single-user accounts)
    org_id: Optional[str] = None
    features: Optional[list[str]] = []


class AuthResponse(BaseModel):
    """Combined Auth Response"""
    user: User
    tokens: Token
