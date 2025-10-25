"""
Universal Wallet Screening API
===============================

TRM Labs-Style API für Universal Screening über alle 90+ Chains.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from app.services.universal_screening import (
    universal_screening_service,
    UniversalScreeningResult,
)
from app.auth.dependencies import get_current_user_optional, require_plan

logger = logging.getLogger(__name__)

router = APIRouter()


class UniversalScreenRequest(BaseModel):
    """Request für Universal Screening"""
    address: str = Field(..., min_length=1, description="Wallet-Adresse zum Screenen")
    chains: Optional[List[str]] = Field(
        default=None,
        description="Spezifische Chains (None = alle 90+ Chains)",
    )
    max_concurrent: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max parallele Chain-Requests",
    )


class UniversalScreenResponse(BaseModel):
    """Response für Universal Screening"""
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None


class ChainListResponse(BaseModel):
    """Response für Chain-Liste"""
    success: bool
    total_chains: int
    chains: List[str]


@router.post(
    "/screen",
    response_model=UniversalScreenResponse,
    summary="Universal Wallet Screening über alle Chains",
    description="""
    Screent eine Wallet-Adresse gleichzeitig über alle 90+ unterstützten Chains.
    
    Features:
    - Parallel Screening über alle Chains
    - Aggregate Risk Score
    - Chain-spezifische Breakdowns
    - Glass Box Attribution (transparente Confidence Scores)
    - Cross-Chain Exposure Detection
    
    TRM Labs-Style Implementation.
    """,
    dependencies=[Depends(require_plan("pro"))],
)
async def screen_address_universal(
    request: UniversalScreenRequest,
    current_user = Depends(get_current_user_optional),
):
    """
    Universal Wallet Screening über alle Chains.
    
    Screent eine Adresse gleichzeitig über:
    - Alle 90+ unterstützte Chains (oder spezifizierte Chains)
    - Sanctions Lists (OFAC, UN, EU, UK)
    - Threat Intelligence Feeds
    - Exchange Labels
    - Behavioral Analysis
    - Cross-Chain Exposure
    
    Returns aggregate Risk Score + Chain-specific Breakdowns.
    """
    try:
        # Validiere Adresse
        address = request.address.strip()
        if not address:
            raise HTTPException(status_code=400, detail="Address cannot be empty")
        
        # Universal Screening durchführen
        result = await universal_screening_service.screen_address_universal(
            address=address,
            chains=request.chains,
            max_concurrent=request.max_concurrent,
        )
        
        # Log für Analytics
        logger.info(
            f"Universal Screening: {address} | "
            f"Chains: {result.total_chains_checked} | "
            f"Risk: {result.aggregate_risk_score:.2f} | "
            f"Time: {result.processing_time_ms:.0f}ms"
        )
        
        return UniversalScreenResponse(
            success=True,
            data=result.to_dict(),
            message=f"Screened across {result.total_chains_checked} chains in {result.processing_time_ms:.0f}ms",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Universal screening error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Screening failed: {str(e)}")


@router.get(
    "/screen/{address}",
    response_model=UniversalScreenResponse,
    summary="Universal Screening (GET)",
    description="Screent eine Adresse über alle Chains (GET-Variante für einfache Abfragen)",
    dependencies=[Depends(require_plan("pro"))],
)
async def screen_address_universal_get(
    address: str,
    chains: Optional[str] = Query(
        default=None,
        description="Comma-separated Chain-IDs (z.B. 'ethereum,bitcoin,solana')",
    ),
    max_concurrent: int = Query(default=10, ge=1, le=50),
    current_user = Depends(get_current_user_optional),
):
    """
    Universal Screening via GET (einfachere Variante).
    """
    try:
        # Parse Chains
        chain_list = None
        if chains:
            chain_list = [c.strip() for c in chains.split(",") if c.strip()]
        
        # Universal Screening durchführen
        result = await universal_screening_service.screen_address_universal(
            address=address,
            chains=chain_list,
            max_concurrent=max_concurrent,
        )
        
        return UniversalScreenResponse(
            success=True,
            data=result.to_dict(),
            message=f"Screened across {result.total_chains_checked} chains in {result.processing_time_ms:.0f}ms",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Universal screening error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Screening failed: {str(e)}")


@router.get(
    "/chains",
    response_model=ChainListResponse,
    summary="Unterstützte Chains für Universal Screening",
    description="Gibt alle 90+ unterstützten Chains zurück",
)
async def get_supported_chains():
    """
    Gibt alle für Universal Screening unterstützten Chains zurück.
    """
    try:
        await universal_screening_service.initialize()
        
        chains = universal_screening_service.supported_chains
        
        return ChainListResponse(
            success=True,
            total_chains=len(chains),
            chains=chains,
        )
        
    except Exception as e:
        logger.error(f"Failed to get supported chains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/batch",
    summary="Batch Universal Screening",
    description="Screent mehrere Adressen gleichzeitig über alle Chains",
    dependencies=[Depends(require_plan("plus"))],
)
async def batch_universal_screening(
    addresses: List[str] = Field(..., min_length=1, max_length=50),
    chains: Optional[List[str]] = None,
    max_concurrent_per_address: int = 10,
    current_user = Depends(get_current_user_optional),
):
    """
    Batch Universal Screening für mehrere Adressen.
    
    Screent bis zu 50 Adressen parallel über alle Chains.
    """
    try:
        import asyncio
        
        # Validiere
        if len(addresses) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 addresses per batch request",
            )
        
        # Erstelle Tasks für alle Adressen
        async def screen_one(addr: str):
            try:
                return await universal_screening_service.screen_address_universal(
                    address=addr,
                    chains=chains,
                    max_concurrent=max_concurrent_per_address,
                )
            except Exception as e:
                logger.warning(f"Failed to screen {addr}: {e}")
                return None
        
        # Parallel screenen
        results = await asyncio.gather(*[screen_one(addr) for addr in addresses])
        
        # Filtere erfolgreiche Results
        successful_results = {}
        for addr, result in zip(addresses, results):
            if result:
                successful_results[addr] = result.to_dict()
        
        return {
            "success": True,
            "total_requested": len(addresses),
            "total_screened": len(successful_results),
            "results": successful_results,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch screening error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
