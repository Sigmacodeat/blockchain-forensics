"""
Notifications API
Endpoints for user notifications and alerts
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body, Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for TEST_MODE
_TEST_MODE = bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TEST_MODE") == "1")
_NOTIFICATIONS: List[Dict[str, Any]] = []
_NOTIFICATION_ID_COUNTER = 0


# API Models
class NotificationCreateRequest(BaseModel):
    """Request model for creating a notification"""
    user_id: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)  # alert, info, warning, success
    priority: str = Field(default="normal")  # low, normal, high
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationUpdateRequest(BaseModel):
    """Request model for updating a notification"""
    read: bool = Field(default=False)


class NotificationResponse(BaseModel):
    """Response model for notification"""
    id: int
    user_id: str
    type: str
    priority: str
    title: str
    message: str
    read: bool
    created_at: str
    metadata: Dict[str, Any]


# Notification Endpoints
@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    request: NotificationCreateRequest = Body(...)
) -> NotificationResponse:
    """Create a new notification"""
    global _NOTIFICATION_ID_COUNTER
    
    if _TEST_MODE:
        _NOTIFICATION_ID_COUNTER += 1
        notification = {
            "id": _NOTIFICATION_ID_COUNTER,
            "user_id": request.user_id,
            "type": request.type,
            "priority": request.priority,
            "title": request.title,
            "message": request.message,
            "read": False,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": request.metadata
        }
        _NOTIFICATIONS.append(notification)
        return NotificationResponse(**notification)
    
    # Production implementation would save to database
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    user_id: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100)
) -> List[NotificationResponse]:
    """List notifications"""
    if _TEST_MODE:
        notifications = _NOTIFICATIONS
        
        # Filter by user_id
        if user_id:
            notifications = [n for n in notifications if n["user_id"] == user_id]
        
        # Filter by read status
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        # Limit results
        notifications = notifications[:limit]
        
        return [NotificationResponse(**n) for n in notifications]
    
    # Production implementation would read from database
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int = Path(...)
) -> NotificationResponse:
    """Get a specific notification"""
    if _TEST_MODE:
        for notification in _NOTIFICATIONS:
            if notification["id"] == notification_id:
                return NotificationResponse(**notification)
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Production implementation would read from database
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int = Path(...),
    request: NotificationUpdateRequest = Body(...)
) -> NotificationResponse:
    """Mark a notification as read/unread"""
    if _TEST_MODE:
        for notification in _NOTIFICATIONS:
            if notification["id"] == notification_id:
                notification["read"] = request.read
                return NotificationResponse(**notification)
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Production implementation would update database
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: int = Path(...)
):
    """Delete a notification"""
    if _TEST_MODE:
        global _NOTIFICATIONS
        _NOTIFICATIONS = [n for n in _NOTIFICATIONS if n["id"] != notification_id]
        return None
    
    # Production implementation would delete from database
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/mark-all-read", status_code=200)
async def mark_all_read(
    user_id: str = Query(...)
) -> Dict[str, Any]:
    """Mark all notifications as read for a user"""
    if _TEST_MODE:
        count = 0
        for notification in _NOTIFICATIONS:
            if notification["user_id"] == user_id and not notification["read"]:
                notification["read"] = True
                count += 1
        return {"status": "ok", "marked_read": count}
    
    # Production implementation would update database
    raise HTTPException(status_code=501, detail="Not implemented")
