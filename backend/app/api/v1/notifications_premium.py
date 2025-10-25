from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.notification_service_premium import PremiumNotificationService
from app.db.session import get_db
from app.auth.dependencies import get_current_user
from sqlalchemy.orm import Session

router = APIRouter()

# Models
class CreateNotificationRequest(BaseModel):
    title: str
    message: str
    type: str
    priority: str = "normal"
    action_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None

class UpdatePreferencesRequest(BaseModel):
    email_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    discord_enabled: Optional[bool] = None
    notification_types: Optional[Dict[str, Dict[str, bool]]] = None
    digests: Optional[Dict[str, bool]] = None

# Endpoints
@router.get("/notifications")
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PremiumNotificationService(db)
    return await service.get_user_notifications(current_user.id, unread_only, limit)

@router.get("/notifications/unread-count")
async def get_unread_count(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PremiumNotificationService(db)
    count = await service.get_unread_count(current_user.id)
    return {"count": count}

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PremiumNotificationService(db)
    success = await service.mark_as_read(notification_id, current_user.id)
    return {"success": success}

@router.post("/notifications/mark-all-read")
async def mark_all_read(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PremiumNotificationService(db)
    count = await service.mark_all_as_read(current_user.id)
    return {"count": count}

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PremiumNotificationService(db)
    success = await service.delete_notification(notification_id, current_user.id)
    return {"success": success}

@router.get("/notifications/preferences")
async def get_preferences(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PremiumNotificationService(db)
    return await service.get_user_preferences(current_user.id)

@router.put("/notifications/preferences")
async def update_preferences(
    request: UpdatePreferencesRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PremiumNotificationService(db)
    return await service.update_user_preferences(current_user.id, request.dict(exclude_none=True))

@router.post("/notifications/send")
async def send_notification(
    request: CreateNotificationRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PremiumNotificationService(db)
    return await service.send_notification(
        user_id=current_user.id,
        title=request.title,
        message=request.message,
        type=request.type,
        priority=request.priority,
        action_url=request.action_url,
        metadata=request.metadata,
        channels=request.channels
    )
