"""
Trial Management API
14-Tage Trials für höhere Pläne (wie Chainalysis)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.models.user import SubscriptionPlan
from app.db.session import get_db
from app.models.user import UserORM
from app.observability.audit_logger import log_trial_event, AuditEventType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trials", tags=["Trials"])


class TrialStartRequest(BaseModel):
    """Request to start a trial"""
    plan: SubscriptionPlan = Field(..., description="Plan to trial (pro, business, plus, enterprise)")


class TrialResponse(BaseModel):
    """Trial response"""
    success: bool
    trial_plan: str
    trial_ends_at: str
    days_remaining: int
    message: str


@router.post("/start", response_model=TrialResponse)
async def start_trial(
    request: TrialStartRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TrialResponse:
    """
    Start 14-day trial for higher plan
    
    **Restrictions:**
    - Only community users can start trials
    - One trial per user (lifetime)
    - Trial plan must be higher than current plan
    
    **Usage:**
    ```json
    POST /api/v1/trials/start
    {
        "plan": "pro"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "trial_plan": "pro",
        "trial_ends_at": "2025-11-02T12:00:00Z",
        "days_remaining": 14,
        "message": "Trial started! Explore Pro features for 14 days."
    }
    ```
    """
    user_id = current_user['user_id']
    
    # Get user from DB
    db_user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not db_user:
        raise HTTPException(404, "User not found")
    
    current_plan = db_user.plan or 'community'
    
    # ✅ Check: Nur Community Users können Trials starten
    if current_plan != 'community':
        raise HTTPException(
            400, 
            f"Trials nur für community users. Aktueller Plan: {current_plan}"
        )
    
    # ✅ Check: Trial-Plan muss höher sein
    plan_hierarchy = ['community', 'starter', 'pro', 'business', 'plus', 'enterprise']
    current_idx = plan_hierarchy.index(current_plan)
    trial_idx = plan_hierarchy.index(request.plan.value)
    
    if trial_idx <= current_idx:
        raise HTTPException(
            400,
            f"Trial-Plan muss höher sein als {current_plan}"
        )
    
    # ✅ Check: Kein aktiver Trial
    if db_user.trial_plan and db_user.trial_ends_at:
        if datetime.utcnow() < db_user.trial_ends_at:
            days_left = (db_user.trial_ends_at - datetime.utcnow()).days
            raise HTTPException(
                400,
                f"Bereits aktiver Trial für {db_user.trial_plan}. Noch {days_left} Tage verbleibend."
            )
    
    # ✅ Check: Nur ein Trial pro User (lifetime)
    if db_user.trial_started_at:
        raise HTTPException(
            400,
            "Sie haben bereits einen Trial genutzt. Upgrade zu einem bezahlten Plan für vollen Zugriff."
        )
    
    # ✅ Start Trial (14 Tage)
    trial_ends_at = datetime.utcnow() + timedelta(days=14)
    trial_started_at = datetime.utcnow()
    
    db_user.trial_plan = request.plan.value
    db_user.trial_ends_at = trial_ends_at
    db_user.trial_started_at = trial_started_at
    
    db.commit()
    
    # Audit-Log
    log_trial_event(
        event_type=AuditEventType.TRIAL_STARTED,
        user_id=user_id,
        email=current_user.get('email', ''),
        trial_plan=request.plan.value,
        trial_ends_at=trial_ends_at
    )
    
    logger.info(f"Trial started: user={user_id}, plan={request.plan.value}, ends={trial_ends_at}")
    
    return TrialResponse(
        success=True,
        trial_plan=request.plan.value,
        trial_ends_at=trial_ends_at.isoformat(),
        days_remaining=14,
        message=f"Trial started! Explore {request.plan.value.upper()} features for 14 days."
    )


@router.get("/status")
async def get_trial_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current trial status
    
    **Returns:**
    ```json
    {
        "has_trial": true,
        "trial_plan": "pro",
        "trial_active": true,
        "trial_ends_at": "2025-11-02T12:00:00Z",
        "days_remaining": 12,
        "ever_had_trial": true
    }
    ```
    """
    user_id = current_user['user_id']
    
    db_user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not db_user:
        raise HTTPException(404, "User not found")
    
    has_trial = bool(db_user.trial_plan and db_user.trial_ends_at)
    trial_active = False
    days_remaining = 0
    
    if has_trial:
        trial_active = datetime.utcnow() < db_user.trial_ends_at
        if trial_active:
            days_remaining = (db_user.trial_ends_at - datetime.utcnow()).days
    
    return {
        "has_trial": has_trial,
        "trial_plan": db_user.trial_plan,
        "trial_active": trial_active,
        "trial_ends_at": db_user.trial_ends_at.isoformat() if db_user.trial_ends_at else None,
        "days_remaining": days_remaining,
        "ever_had_trial": bool(db_user.trial_started_at)
    }


@router.post("/cancel")
async def cancel_trial(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel active trial (user reverts to community plan)
    
    **Note:** Trial-Start bleibt gespeichert (trial_started_at), sodass User nicht nochmal Trial starten kann.
    """
    user_id = current_user['user_id']
    
    db_user = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not db_user:
        raise HTTPException(404, "User not found")
    
    if not (db_user.trial_plan and db_user.trial_ends_at):
        raise HTTPException(400, "Kein aktiver Trial")
    
    if datetime.utcnow() >= db_user.trial_ends_at:
        raise HTTPException(400, "Trial bereits abgelaufen")
    
    # Cancel Trial
    trial_plan = db_user.trial_plan
    db_user.trial_plan = None
    db_user.trial_ends_at = None
    # trial_started_at bleibt! (für lifetime-check)
    
    db.commit()
    
    # Audit-Log
    log_trial_event(
        event_type=AuditEventType.TRIAL_ENDED,
        user_id=user_id,
        email=current_user.get('email', ''),
        trial_plan=trial_plan,
        metadata={"reason": "user_cancelled"}
    )
    
    logger.info(f"Trial cancelled: user={user_id}, plan={trial_plan}")
    
    return {
        "success": True,
        "message": "Trial cancelled. Sie nutzen jetzt wieder den Community Plan."
    }
