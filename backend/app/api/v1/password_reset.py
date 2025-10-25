"""
Password Reset Flow
Secure password reset with tokens
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, cast
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.auth.jwt import get_password_hash, verify_password
from app.api.v1.auth import users_db
from app.models.audit_log import log_audit_event, AuditAction
from app.services.email import email_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Password reset tokens (in production: use Redis with TTL)
reset_tokens: Dict[str, Dict] = {}


class PasswordResetRequest(BaseModel):
    """Request password reset"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token"""
    token: str
    new_password: str


class PasswordChange(BaseModel):
    """Change password (authenticated)"""
    current_password: str
    new_password: str


@router.post("/request")
async def request_password_reset(request: PasswordResetRequest):
    """
    Request password reset
    
    **Flow:**
    1. User provides email
    2. System generates secure token
    3. Email sent with reset link (mocked for now)
    4. Token valid for 1 hour
    
    **Note:** Always returns success to prevent email enumeration
    """
    # Find user
    user_dict = next(
        (u for u in users_db.values() if u["email"] == request.email),
        None
    )
    
    if user_dict:
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Store token with expiration
        reset_tokens[token] = {
            "user_id": user_dict["id"],
            "email": request.email,
            "expires_at": datetime.utcnow() + timedelta(hours=1),
        }
        
        # Log audit event
        log_audit_event(
            action=AuditAction.PASSWORD_RESET,
            user_id=cast(str, user_dict["id"]),
            user_email=str(request.email),
            metadata={"token_generated": True},
        )
        
        # Send email (dev-mode will log to console)
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        logger.info(f"Password reset requested for {request.email}")
        logger.info(f"Reset link (dev): {reset_link}")
        try:
            # username fallback to email prefix for dev
            username = request.email.split('@')[0]
            await email_service.send_password_reset_email(to=request.email, username=username, token=token)
        except Exception as e:
            # Do not leak errors to caller to avoid enumeration
            logger.warning(f"Password reset email dispatch failed: {e}")
    
    # Always return success to prevent email enumeration
    return {
        "message": "If the email exists, a reset link has been sent",
        "dev_note": "Check server logs for reset link (email not configured)"
    }


@router.post("/confirm")
async def confirm_password_reset(data: PasswordResetConfirm):
    """
    Confirm password reset with token
    
    **Flow:**
    1. User provides token and new password
    2. System validates token
    3. Password updated
    4. Token invalidated
    """
    # Validate token
    token_data = reset_tokens.get(data.token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check expiration
    if datetime.utcnow() > cast(datetime, token_data["expires_at"]):
        del reset_tokens[data.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Validate password
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Get user
    user_dict = users_db.get(cast(str, token_data["user_id"]))
    
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user_dict["hashed_password"] = get_password_hash(data.new_password)
    
    # Invalidate token
    del reset_tokens[data.token]
    
    # Log audit event
    log_audit_event(
        action=AuditAction.PASSWORD_RESET,
        user_id=cast(str, user_dict["id"]),
        user_email=cast(str, user_dict["email"]),
        metadata={"password_changed": True},
    )
    
    logger.info(f"Password reset successful for {user_dict['email']}")
    
    return {"message": "Password successfully reset"}


@router.post("/change")
async def change_password(
    data: PasswordChange,
    user_id: str,  # From auth dependency
):
    """
    Change password (authenticated user)
    
    **Requires:** Authentication
    """
    user_dict = users_db.get(user_id)
    
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(data.current_password, cast(str, user_dict["hashed_password"])):
        log_audit_event(
            action=AuditAction.PASSWORD_CHANGE,
            user_id=user_id,
            user_email=cast(str, user_dict["email"]),
            success=False,
            error_message="Invalid current password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )
    
    # Update password
    user_dict["hashed_password"] = get_password_hash(data.new_password)
    
    # Log audit event
    log_audit_event(
        action=AuditAction.PASSWORD_CHANGE,
        user_id=user_id,
        user_email=cast(str, user_dict["email"]),
        metadata={"self_initiated": True},
    )
    
    logger.info(f"Password changed for {user_dict['email']}")
    
    return {"message": "Password successfully changed"}
