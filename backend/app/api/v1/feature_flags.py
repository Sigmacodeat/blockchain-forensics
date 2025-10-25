"""
Feature Flags API
Admin-only endpoints for feature management
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from app.services.feature_flag_service import (
    feature_flag_service,
    FeatureFlagStatus
)
from app.auth.dependencies import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class FeatureFlagCreate(BaseModel):
    """Create feature flag request"""
    key: str = Field(..., min_length=3, max_length=64, description="Unique flag key")
    name: str = Field(..., min_length=3, max_length=128, description="Display name")
    description: str = Field(..., description="Flag description")
    status: FeatureFlagStatus = Field(default=FeatureFlagStatus.DISABLED)


class FeatureFlagUpdate(BaseModel):
    """Update feature flag request"""
    status: Optional[FeatureFlagStatus] = None
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)
    rollout_user_ids: Optional[List[str]] = None


class FeatureFlagResponse(BaseModel):
    """Feature flag response"""
    key: str
    name: str
    description: str
    status: str
    rollout_percentage: int
    rollout_user_ids: List[str]
    environment: str
    created_at: str
    updated_at: str


class FeatureFlagCheckRequest(BaseModel):
    """Check feature flag request"""
    user_id: Optional[str] = None


class FeatureFlagCheckResponse(BaseModel):
    """Check feature flag response"""
    enabled: bool
    variant: Optional[str] = None


@router.post("/", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    request: FeatureFlagCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new feature flag (Admin only)
    
    **Requires:** Admin Role
    
    **Example:**
    ```json
    {
      "key": "new_dashboard_ui",
      "name": "New Dashboard UI",
      "description": "Enable new dashboard design",
      "status": "disabled"
    }
    ```
    """
    try:
        flag = await feature_flag_service.create_flag(
            key=request.key,
            name=request.name,
            description=request.description,
            status=request.status
        )
        
        logger.info(f"Admin {current_user.get('email')} created feature flag: {request.key}")
        
        return FeatureFlagResponse(**flag.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating feature flag: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=List[FeatureFlagResponse])
async def list_feature_flags(current_user: dict = Depends(require_admin)):
    """
    List all feature flags (Admin only)
    
    **Requires:** Admin Role
    """
    try:
        flags = await feature_flag_service.list_flags()
        return [FeatureFlagResponse(**flag.to_dict()) for flag in flags]
        
    except Exception as e:
        logger.error(f"Error listing feature flags: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{key}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    key: str,
    current_user: dict = Depends(require_admin)
):
    """
    Get feature flag by key (Admin only)
    
    **Requires:** Admin Role
    """
    try:
        flag = await feature_flag_service.get_flag(key)
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag '{key}' not found"
            )
        
        return FeatureFlagResponse(**flag.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature flag {key}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{key}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    key: str,
    request: FeatureFlagUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Update feature flag (Admin only)
    
    **Requires:** Admin Role
    
    **Example:**
    ```json
    {
      "status": "rollout",
      "rollout_percentage": 25
    }
    ```
    """
    try:
        flag = await feature_flag_service.update_flag(
            key=key,
            status=request.status,
            rollout_percentage=request.rollout_percentage,
            rollout_user_ids=request.rollout_user_ids
        )
        
        logger.info(f"Admin {current_user.get('email')} updated feature flag: {key}")
        
        return FeatureFlagResponse(**flag.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating feature flag {key}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_flag(
    key: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete feature flag (Admin only)
    
    **Requires:** Admin Role
    **Warning:** This will immediately disable the feature for all users
    """
    try:
        deleted = await feature_flag_service.delete_flag(key)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag '{key}' not found"
            )
        
        logger.warning(f"Admin {current_user.get('email')} deleted feature flag: {key}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feature flag {key}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{key}/check", response_model=FeatureFlagCheckResponse)
async def check_feature_flag(
    key: str,
    request: FeatureFlagCheckRequest
):
    """
    Check if feature is enabled for user
    
    **Public endpoint** - No auth required
    
    **Example:**
    ```json
    {
      "user_id": "user_123"
    }
    ```
    
    **Response:**
    ```json
    {
      "enabled": true,
      "variant": "A"
    }
    ```
    """
    try:
        enabled = await feature_flag_service.is_enabled(key, request.user_id)
        variant = None
        
        # Get variant if A/B test
        if enabled and request.user_id:
            variant = await feature_flag_service.get_variant(key, request.user_id)
        
        return FeatureFlagCheckResponse(enabled=enabled, variant=variant)
        
    except Exception as e:
        logger.error(f"Error checking feature flag {key}: {e}")
        # Fail gracefully - return disabled
        return FeatureFlagCheckResponse(enabled=False, variant=None)


@router.post("/{key}/enable", response_model=FeatureFlagResponse)
async def enable_feature_flag(
    key: str,
    current_user: dict = Depends(require_admin)
):
    """
    Enable feature flag for all users (Admin only)
    
    **Requires:** Admin Role
    **Shortcut** for updating status to ENABLED
    """
    try:
        flag = await feature_flag_service.update_flag(key, status=FeatureFlagStatus.ENABLED)
        logger.info(f"Admin {current_user.get('email')} enabled feature flag: {key}")
        return FeatureFlagResponse(**flag.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error enabling feature flag {key}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{key}/disable", response_model=FeatureFlagResponse)
async def disable_feature_flag(
    key: str,
    current_user: dict = Depends(require_admin)
):
    """
    Disable feature flag for all users (Admin only)
    
    **Requires:** Admin Role
    **Shortcut** for updating status to DISABLED
    """
    try:
        flag = await feature_flag_service.update_flag(key, status=FeatureFlagStatus.DISABLED)
        logger.info(f"Admin {current_user.get('email')} disabled feature flag: {key}")
        return FeatureFlagResponse(**flag.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error disabling feature flag {key}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
