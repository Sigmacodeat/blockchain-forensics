"""
Advanced Risk Analysis API
===========================

TRM Labs-Style Advanced Indirect Risk Detection API.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from app.analytics.advanced_indirect_risk import advanced_indirect_risk_service
from app.auth.dependencies import get_current_user_optional, require_plan

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyzeIndirectRiskRequest(BaseModel):
    """Request für Indirect Risk Analysis"""
    target_address: str = Field(..., min_length=1)
    max_hops: int = Field(default=3, ge=1, le=10)
    chains: Optional[List[str]] = None
    max_paths: int = Field(default=1000, ge=10, le=10000)


@router.post(
    "/indirect-risk",
    summary="Analyze Indirect Risk",
    description="""
    Analysiere Indirect Risk für Adresse mit Advanced Multi-Hop Detection.
    
    Features:
    - Path-Agnostic Tracing (findet alle Pfade)
    - Cross-Chain Risk Propagation
    - Nuanced Risk Scoring mit Decay
    - Unterstützt alle 90+ Chains
    
    TRM Labs-Style Implementation.
    """,
    dependencies=[Depends(require_plan("plus"))],
)
async def analyze_indirect_risk(
    request: AnalyzeIndirectRiskRequest,
    current_user = Depends(get_current_user_optional),
):
    """Analysiere Indirect Risk"""
    try:
        result = await advanced_indirect_risk_service.analyze_indirect_risk(
            target_address=request.target_address,
            max_hops=request.max_hops,
            chains=request.chains,
            max_paths=request.max_paths,
        )
        
        return {
            "success": True,
            "data": result.to_dict(),
            "message": f"Analyzed {result.paths_analyzed} paths across {len(result.chains_analyzed)} chains",
        }
        
    except Exception as e:
        logger.error(f"Indirect risk analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/indirect-risk/{address}",
    summary="Get Indirect Risk (Simple)",
    description="Hole Indirect Risk für Adresse (GET-Variante)",
    dependencies=[Depends(require_plan("plus"))],
)
async def get_indirect_risk(
    address: str,
    max_hops: int = Query(default=3, ge=1, le=10),
    chains: Optional[str] = Query(default=None, description="Comma-separated chains"),
    current_user = Depends(get_current_user_optional),
):
    """Hole Indirect Risk (GET)"""
    try:
        # Parse Chains
        chain_list = None
        if chains:
            chain_list = [c.strip() for c in chains.split(",") if c.strip()]
        
        result = await advanced_indirect_risk_service.analyze_indirect_risk(
            target_address=address,
            max_hops=max_hops,
            chains=chain_list,
        )
        
        return {
            "success": True,
            "data": result.to_dict(),
        }
        
    except Exception as e:
        logger.error(f"Indirect risk analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
