"""
Advanced Analytics API
Funnel, Cohort, Retention (Admin Only)
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.advanced_analytics_service import advanced_analytics_service
from app.auth.dependencies import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class FunnelAnalysisRequest(BaseModel):
    """Funnel analysis request"""
    funnel_steps: List[str] = Field(..., min_length=2, description="Funnel steps in order")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    org_id: Optional[str] = None


@router.post("/funnel")
async def get_funnel_analysis(
    request: FunnelAnalysisRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Funnel Analysis (Admin only)
    
    **Requires:** Admin Role
    
    **Example:**
    ```json
    {
      "funnel_steps": ["signup", "first_login", "first_trace", "plan_upgrade"],
      "start_date": "2025-10-01T00:00:00Z",
      "end_date": "2025-10-31T23:59:59Z"
    }
    ```
    
    **Response:**
    ```json
    {
      "funnel_steps": [
        {
          "step": "signup",
          "step_number": 1,
          "count": 1000,
          "conversion_rate": 100.0,
          "drop_off": 0
        },
        {
          "step": "first_login",
          "step_number": 2,
          "count": 850,
          "conversion_rate": 85.0,
          "drop_off": 150
        },
        {
          "step": "first_trace",
          "step_number": 3,
          "count": 600,
          "conversion_rate": 60.0,
          "drop_off": 250
        },
        {
          "step": "plan_upgrade",
          "step_number": 4,
          "count": 120,
          "conversion_rate": 12.0,
          "drop_off": 480
        }
      ],
      "total_users": 1000,
      "overall_conversion_rate": 12.0
    }
    ```
    """
    try:
        result = await advanced_analytics_service.get_funnel_analysis(
            funnel_steps=request.funnel_steps,
            start_date=request.start_date,
            end_date=request.end_date,
            org_id=request.org_id
        )
        
        logger.info(f"Admin {current_user.get('email')} ran funnel analysis")
        return result
        
    except Exception as e:
        logger.error(f"Error in funnel analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cohort")
async def get_cohort_analysis(
    cohort_by: str = Query('month', pattern='^(day|week|month)$'),
    periods: int = Query(12, ge=1, le=24),
    org_id: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """
    Cohort Analysis (Admin only)
    
    **Requires:** Admin Role
    
    **Parameters:**
    - cohort_by: Group by 'day', 'week', or 'month'
    - periods: Number of periods to analyze (1-24)
    - org_id: Optional organization filter
    
    **Returns:**
    Retention matrix showing user retention over time by cohort
    
    **Example Response:**
    ```json
    {
      "cohorts": [
        {
          "cohort": "2025-01",
          "cohort_size": 150,
          "retention": [
            {"period": 0, "active_users": 150, "retention_rate": 100.0},
            {"period": 1, "active_users": 120, "retention_rate": 80.0},
            {"period": 2, "active_users": 95, "retention_rate": 63.3}
          ]
        }
      ],
      "cohort_by": "month",
      "periods": 12
    }
    ```
    """
    try:
        result = await advanced_analytics_service.get_cohort_analysis(
            cohort_by=cohort_by,
            periods=periods,
            org_id=org_id
        )
        
        logger.info(f"Admin {current_user.get('email')} ran cohort analysis")
        return result
        
    except Exception as e:
        logger.error(f"Error in cohort analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention")
async def get_retention_metrics(
    days: int = Query(30, ge=1, le=365),
    org_id: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """
    Retention Metrics (Admin only)
    
    **Requires:** Admin Role
    
    **Parameters:**
    - days: Analysis period (1-365)
    - org_id: Optional organization filter
    
    **Returns:**
    - Day 1, 7, 30 retention rates
    - Churn rate
    - Active user counts
    
    **Example Response:**
    ```json
    {
      "total_active_users": 5000,
      "retention": {
        "day_1_retention": {
          "retained_users": 3500,
          "retention_rate": 70.0
        },
        "day_7_retention": {
          "retained_users": 2000,
          "retention_rate": 40.0
        },
        "day_30_retention": {
          "retained_users": 1200,
          "retention_rate": 24.0
        }
      },
      "churn": {
        "churned_users": 800,
        "churn_rate": 16.0
      }
    }
    ```
    """
    try:
        result = await advanced_analytics_service.get_retention_metrics(
            days=days,
            org_id=org_id
        )
        
        logger.info(f"Admin {current_user.get('email')} viewed retention metrics")
        return result
        
    except Exception as e:
        logger.error(f"Error in retention metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engagement")
async def get_engagement_metrics(
    days: int = Query(30, ge=1, le=365),
    org_id: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """
    User Engagement Metrics (Admin only)
    
    **Requires:** Admin Role
    
    **Returns:**
    - DAU (Daily Active Users)
    - WAU (Weekly Active Users)
    - MAU (Monthly Active Users)
    - Stickiness (DAU/MAU ratio)
    
    **Example Response:**
    ```json
    {
      "dau": 450.5,
      "wau": 2800,
      "mau": 8500,
      "stickiness": 5.3,
      "period_days": 30
    }
    ```
    
    **Interpretation:**
    - Stickiness > 20%: Excellent (users visit daily)
    - Stickiness 10-20%: Good
    - Stickiness < 10%: Needs improvement
    """
    try:
        result = await advanced_analytics_service.get_user_engagement_metrics(
            days=days,
            org_id=org_id
        )
        
        logger.info(f"Admin {current_user.get('email')} viewed engagement metrics")
        return result
        
    except Exception as e:
        logger.error(f"Error in engagement metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365),
    org_id: Optional[str] = None,
    current_user: dict = Depends(require_admin)
):
    """
    Analytics Summary Dashboard (Admin only)
    
    **Requires:** Admin Role
    
    **Returns:**
    Combined view of all key metrics for quick overview
    """
    try:
        # Get all metrics in parallel
        import asyncio
        
        engagement, retention = await asyncio.gather(
            advanced_analytics_service.get_user_engagement_metrics(days, org_id),
            advanced_analytics_service.get_retention_metrics(days, org_id)
        )
        
        summary = {
            'engagement': engagement,
            'retention': retention,
            'period_days': days
        }
        
        logger.info(f"Admin {current_user.get('email')} viewed analytics summary")
        return summary
        
    except Exception as e:
        logger.error(f"Error in analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
