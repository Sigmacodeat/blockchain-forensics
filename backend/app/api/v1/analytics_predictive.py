from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_strict
from app.services.predictive_model import predictive_model

router = APIRouter(prefix="/analytics/predict", tags=["Analytics Predictive"])


class UserActivityPredictionRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="User to predict (default: current user)")
    days_ahead: int = Field(7, ge=1, le=30, description="Prediction horizon")
    metric: str = Field("tokens_used", description="Metric: tokens_used, alerts_triggered, traces_run")


class SystemRiskPredictionRequest(BaseModel):
    days_ahead: int = Field(7, ge=1, le=14, description="Prediction horizon")


@router.post("/user-activity")
async def predict_user_activity(
    payload: UserActivityPredictionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    """Prognostiziert Nutzer-Aktivität (Zeitreihen-Modell)"""
    user_id = payload.user_id or current_user["user_id"]
    try:
        result = await predictive_model.predict_user_activity(
            user_id=user_id,
            days_ahead=payload.days_ahead,
            metric=payload.metric
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/system-risk")
async def predict_system_risk(
    payload: SystemRiskPredictionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    """Prognostiziert systemweite Risiko-Trends"""
    try:
        result = await predictive_model.predict_system_risk_trends(
            days_ahead=payload.days_ahead
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System prediction failed: {str(e)}")
