"""
User Management API Endpoints
Admin-only endpoints for managing users
"""

import logging
from typing import List, cast
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from app.auth.models import User, UserRole
from app.auth.dependencies import (
    get_current_user_strict,
    require_admin_strict,
)
from app.api.v1.auth import users_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me", response_model=User)
async def me(current_user: dict = Depends(get_current_user_strict)):
    """Return current user details; JWT enforced."""
    user_dict = users_db.get(cast(str, current_user["user_id"]))
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User nicht gefunden"
        )
    return User(
        id=cast(str, user_dict["id"]),
        email=cast(str, user_dict["email"]),
        username=cast(str, user_dict["username"]),
        organization=user_dict.get("organization"),
        role=UserRole(cast(str, user_dict["role"])),
        is_active=bool(user_dict["is_active"]),
        created_at=cast(datetime, user_dict["created_at"])
    )


@router.get("/", response_model=List[User])
async def list_users(current_user: dict = Depends(require_admin_strict)):
    """
    List all users (Admin only)
    
    **Requires:** Admin Role
    """
    users_list = [
        User(
            id=cast(str, u["id"]),
            email=cast(str, u["email"]),
            username=cast(str, u["username"]),
            organization=u.get("organization"),
            role=UserRole(cast(str, u["role"])),
            is_active=bool(u["is_active"]),
            created_at=cast(datetime, u["created_at"])
        )
        for u in users_db.values()
    ]
    
    return users_list


from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    """Request model for creating a user"""
    email: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
    role: str = "investigator"
    status: str = "active"


@router.post("/", response_model=User, status_code=201)
async def create_user(
    request: UserCreateRequest,
    current_user: dict = Depends(require_admin_strict)
):
    """
    Create a new user (Admin only)
    
    **Requires:** Admin Role
    """
    import uuid
    
    # Check if email already exists
    for u in users_db.values():
        if u["email"] == request.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    user_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    user_dict = {
        "id": user_id,
        "email": request.email,
        "username": request.username,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "role": request.role,
        "is_active": request.status == "active",
        "created_at": now,
        "organization": None
    }
    
    users_db[user_id] = user_dict
    
    logger.info(f"Admin {current_user['email']} created user {request.email}")
    
    return User(
        id=user_id,
        email=request.email,
        username=request.username,
        organization=None,
        role=UserRole(request.role),
        is_active=request.status == "active",
        created_at=now
    )


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: dict = Depends(require_admin_strict)):
    """
    Get user by ID (Admin only)
    
    **Requires:** Admin Role
    """
    user_dict = users_db.get(user_id)
    
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User nicht gefunden"
        )
    
    return User(
        id=cast(str, user_dict["id"]),
        email=cast(str, user_dict["email"]),
        username=cast(str, user_dict["username"]),
        organization=user_dict.get("organization"),
        role=UserRole(cast(str, user_dict["role"])),
        is_active=bool(user_dict["is_active"]),
        created_at=cast(datetime, user_dict["created_at"]) 
    )


@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: dict = Depends(require_admin_strict)
):
    """
    Update user role (Admin only)
    
    **Requires:** Admin Role
    """
    user_dict = users_db.get(user_id)
    
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User nicht gefunden"
        )
    
    # Update role
    user_dict["role"] = role.value
    
    logger.info(f"Admin {current_user['email']} updated user {user_dict['email']} role to {role}")
    
    return {"message": f"Role updated to {role}", "user_id": user_id}


@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_user: dict = Depends(require_admin_strict)
):
    """
    Activate/Deactivate user (Admin only)
    
    **Requires:** Admin Role
    """
    user_dict = users_db.get(user_id)
    
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User nicht gefunden"
        )
    
    # Prevent self-deactivation
    if user_id == current_user["user_id"] and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kann eigenen Account nicht deaktivieren"
        )
    
    # Update status
    user_dict["is_active"] = bool(is_active)
    
    status_text = "aktiviert" if is_active else "deaktiviert"
    logger.info(f"Admin {current_user['email']} {status_text} user {user_dict['email']}")
    
    return {"message": f"User {status_text}", "user_id": user_id}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin_strict)
):
    """
    Delete user (Admin only)
    
    **Requires:** Admin Role
    **Warning:** This permanently deletes the user
    """
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User nicht gefunden"
        )
    
    # Prevent self-deletion
    if user_id == current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kann eigenen Account nicht löschen"
        )
    
    user_email = users_db[user_id]["email"]
    del users_db[user_id]
    
    logger.warning(f"Admin {current_user['email']} deleted user {user_email}")
    
    return {"message": "User erfolgreich gelöscht", "user_id": user_id}
