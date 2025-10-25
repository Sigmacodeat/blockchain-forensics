"""
OFAC Sanctions API Endpoints
"""

import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.services.ofac_sanctions import ofac_service
from app.api.v1.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class SanctionCheckRequest(BaseModel):
    """Request to check addresses against sanctions list"""
    addresses: List[str]


class SanctionCheckResponse(BaseModel):
    """Response with sanction check results"""
    address: str
    is_sanctioned: bool
    entity_info: Dict | None = None


class UpdateStatsResponse(BaseModel):
    """OFAC update statistics"""
    total_addresses: int
    last_update: str | None
    by_program: List[Dict]
    in_memory: int


@router.post("/check", response_model=List[SanctionCheckResponse])
async def check_sanctions(
    request: SanctionCheckRequest,
    current_user = Depends(get_current_user)
):
    """
    Check multiple addresses against OFAC sanctions list
    
    **Permissions**: Requires authentication
    **Rate Limit**: 100 checks per minute
    """
    results = []
    
    for address in request.addresses:
        try:
            is_sanctioned = await ofac_service.is_sanctioned(address)
            entity_info = None
            
            if is_sanctioned:
                entity_info = await ofac_service.get_entity_info(address)
            
            results.append(SanctionCheckResponse(
                address=address,
                is_sanctioned=is_sanctioned,
                entity_info=entity_info
            ))
            
        except Exception as e:
            logger.error(f"Sanction check error for {address}: {e}")
            results.append(SanctionCheckResponse(
                address=address,
                is_sanctioned=False,
                entity_info={"error": str(e)}
            ))
    
    return results


@router.get("/check/{address}", response_model=SanctionCheckResponse)
async def check_single_address(
    address: str,
    current_user = Depends(get_current_user)
):
    """
    Check single address against OFAC sanctions list
    
    **Example**: `/api/v1/ofac/check/0x1234...`
    """
    try:
        is_sanctioned = await ofac_service.is_sanctioned(address)
        entity_info = None
        
        if is_sanctioned:
            entity_info = await ofac_service.get_entity_info(address)
        
        return SanctionCheckResponse(
            address=address,
            is_sanctioned=is_sanctioned,
            entity_info=entity_info
        )
        
    except Exception as e:
        logger.error(f"Sanction check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=UpdateStatsResponse)
async def get_statistics(
    current_user = Depends(get_current_user)
):
    """
    Get OFAC sanctions list statistics
    
    Returns:
    - Total addresses
    - Last update timestamp
    - Breakdown by program
    """
    try:
        stats = await ofac_service.get_statistics()
        return UpdateStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
async def trigger_update(
    force: bool = Query(False, description="Force update even if recent"),
    current_user = Depends(get_current_user),
):
    """
    Trigger manual OFAC list update
    
    **Permissions**: Admin only
    **Note**: Automatic updates run daily
    """
    try:
        # Enforce ADMIN role for manual updates
        role = str(getattr(current_user, "role", getattr(current_user, "get", lambda k, d=None: None)("role")))
        role_upper = role.upper() if isinstance(role, str) else str(role).upper()
        if role_upper != "ADMIN":
            raise HTTPException(status_code=403, detail="Admin only")

        stats = await ofac_service.update_sanctions_list()
        return {
            "message": "Update completed" if stats["success"] else "Update failed",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Update trigger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
