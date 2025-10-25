"""
Entity Profiler API Endpoints

Comprehensive entity profiling with OSINT integration.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.entity_profiler_service import entity_profiler_service, EntityType, AttributionConfidence
from app.auth.dependencies import get_current_user_strict, require_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entity-profiler", tags=["Entity Profiler"])


# Request/Response Models

class EntityProfileRequest(BaseModel):
    address: str = Field(..., description="Blockchain address")
    chain: str = Field("ethereum", description="Blockchain")
    include_osint: bool = Field(True, description="Include OSINT data")
    include_relationships: bool = Field(True, description="Include relationship graph")
    depth: int = Field(1, ge=1, le=3, description="Relationship depth")


class BulkProfileRequest(BaseModel):
    addresses: List[dict] = Field(..., max_length=100, description="List of {address, chain}")
    include_osint: bool = Field(False, description="Include OSINT (slower)")


# Endpoints

@router.post("/profile")
async def profile_entity(
    request: EntityProfileRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Create comprehensive entity profile with OSINT.
    
    **Requires:** Pro+ plan
    
    **Features:**
    - Multi-source data aggregation
    - OSINT integration (Twitter, GitHub, websites, etc.)
    - Entity type detection
    - Behavioral analysis
    - Relationship mapping
    - Attribution scoring
    
    **OSINT Sources:**
    - Social media (Twitter, LinkedIn, Reddit)
    - Developer platforms (GitHub)
    - Company registries
    - Domain/WHOIS data
    - News mentions
    - Blockchain explorers
    
    **Returns:**
    - Comprehensive entity profile
    """
    await require_plan(current_user, "pro")
    
    try:
        profile = await entity_profiler_service.profile_entity(
            address=request.address,
            chain=request.chain,
            include_osint=request.include_osint,
            include_relationships=request.include_relationships,
            depth=request.depth
        )
        
        return profile
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Entity profiling failed: {e}")
        raise HTTPException(status_code=500, detail="Entity profiling failed")


@router.post("/profile/bulk")
async def bulk_profile_entities(
    request: BulkProfileRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Bulk profile multiple entities.
    
    **Requires:** Plus+ plan
    
    **Limits:**
    - Max 100 addresses per request
    - OSINT disabled by default (enable for slower but richer data)
    
    **Returns:**
    - List of entity profiles
    """
    await require_plan(current_user, "plus")
    
    if len(request.addresses) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 addresses per bulk request"
        )
    
    try:
        profiles = await entity_profiler_service.bulk_profile(
            addresses=request.addresses,
            include_osint=request.include_osint
        )
        
        return {
            "total": len(request.addresses),
            "successful": len(profiles),
            "failed": len(request.addresses) - len(profiles),
            "profiles": profiles
        }
        
    except Exception as e:
        logger.error(f"Bulk profiling failed: {e}")
        raise HTTPException(status_code=500, detail="Bulk profiling failed")


@router.get("/entity-types")
async def get_entity_types(
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Get list of supported entity types.
    
    **Requires:** Community+ plan
    
    **Returns:**
    - List of entity types with descriptions
    """
    await require_plan(current_user, "community")
    
    entity_types = [
        {
            "type": EntityType.EXCHANGE.value,
            "description": "Cryptocurrency exchange",
            "risk_level": "varies"
        },
        {
            "type": EntityType.MIXER.value,
            "description": "Privacy mixer / tumbler",
            "risk_level": "high"
        },
        {
            "type": EntityType.DEFI_PROTOCOL.value,
            "description": "DeFi protocol smart contract",
            "risk_level": "low"
        },
        {
            "type": EntityType.RANSOMWARE.value,
            "description": "Ransomware operator",
            "risk_level": "critical"
        },
        {
            "type": EntityType.SCAM.value,
            "description": "Scam operation",
            "risk_level": "high"
        },
        {
            "type": EntityType.INDIVIDUAL.value,
            "description": "Individual user wallet",
            "risk_level": "low"
        }
    ]
    
    return {
        "entity_types": entity_types,
        "total": len(entity_types)
    }
