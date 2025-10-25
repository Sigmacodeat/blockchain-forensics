"""
Demo System API Endpoints
==========================

Two-Tier Demo System:
1. GET /demo/sandbox - Get sandbox demo data (no auth)
2. POST /demo/live - Create 30-min live demo user (no auth)
3. GET /demo/stats - Admin stats (auth required)
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from app.services.demo_service import demo_service
from app.auth.dependencies import get_current_user_optional, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/sandbox")
async def get_sandbox_demo() -> Dict[str, Any]:
    """
    Get Sandbox Demo Data (Tier 1 - No Signup)
    
    Returns static mock data that simulates the platform.
    Perfect for first-time visitors who want instant preview.
    
    - **No authentication required**
    - **Read-only data**
    - **Zero friction**
    """
    
    try:
        data = await demo_service.get_sandbox_demo_data()
        return data
    except Exception as e:
        logger.error(f"Error getting sandbox demo: {e}")
        raise HTTPException(status_code=500, detail="Failed to load sandbox demo")


@router.post("/live")
async def create_live_demo(request: Request) -> Dict[str, Any]:
    """
    Create Live Demo User (Tier 2 - 30 Minutes)
    
    Creates a temporary user account with:
    - Full Pro plan access
    - 30-minute session
    - Real feature testing
    - Auto-cleanup after expiration
    
    Rate Limit: 3 per IP per day (abuse prevention)
    
    - **No authentication required**
    - **Returns JWT token for automatic login**
    """
    
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Create live demo user
        result = await demo_service.create_live_demo_user(
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return result
        
    except ValueError as e:
        # Rate limit exceeded
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating live demo: {e}")
        raise HTTPException(status_code=500, detail="Failed to create live demo")


@router.get("/stats")
async def get_demo_stats(
    current_user: Dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get Demo System Statistics (Admin Only)
    
    Returns:
    - Active live demos
    - Today's demo count
    - System health
    
    Requires: Admin role
    """
    
    try:
        stats = await demo_service.get_demo_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting demo stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get demo stats")


@router.post("/cleanup")
async def cleanup_expired_demos(
    current_user: Dict = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Manually Trigger Demo Cleanup (Admin Only)
    
    Deletes all expired live demo accounts.
    Normally runs automatically via CRON.
    
    Requires: Admin role
    """
    
    try:
        count = await demo_service.cleanup_expired_demos()
        return {
            "success": True,
            "cleaned_up": count,
            "message": f"Cleaned up {count} expired demo accounts"
        }
    except Exception as e:
        logger.error(f"Error cleaning up demos: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup demos")
