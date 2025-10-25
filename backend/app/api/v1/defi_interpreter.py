"""
DeFi Transaction Interpreter API Endpoints

Human-readable interpretation of complex DeFi transactions.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.defi_interpreter_service import defi_interpreter_service
from app.auth.dependencies import get_current_user_strict, require_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/defi-interpreter", tags=["DeFi Interpreter"])


# Request/Response Models

class TransactionInterpretRequest(BaseModel):
    tx_hash: str = Field(..., description="Transaction hash")
    chain: str = Field("ethereum", description="Blockchain")
    include_risk: bool = Field(True, description="Include risk assessment")


class BatchInterpretRequest(BaseModel):
    tx_hashes: List[str] = Field(..., max_length=50, description="Transaction hashes (max 50)")
    chain: str = Field("ethereum", description="Blockchain")


# Endpoints

@router.post("/interpret")
async def interpret_transaction(
    request: TransactionInterpretRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Interpret a DeFi transaction into human-readable format.
    
    **Requires:** Pro+ plan
    
    **Features:**
    - Automatic protocol detection
    - Function decoding
    - Human-readable descriptions
    - Complexity analysis
    - Risk assessment
    
    **Supported Protocols:**
    - Uniswap, SushiSwap, Curve
    - Aave, Compound, MakerDAO
    - Lido, Balancer, Yearn
    - And more...
    
    **Returns:**
    - Human-readable transaction interpretation
    """
    await require_plan(current_user, "pro")
    
    try:
        result = await defi_interpreter_service.interpret_transaction(
            tx_hash=request.tx_hash,
            chain=request.chain,
            include_risk=request.include_risk
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Transaction interpretation failed: {e}")
        raise HTTPException(status_code=500, detail="Transaction interpretation failed")


@router.post("/interpret/batch")
async def batch_interpret(
    request: BatchInterpretRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Batch interpret multiple DeFi transactions.
    
    **Requires:** Pro+ plan
    
    **Limits:**
    - Max 50 transactions per request
    
    **Returns:**
    - List of interpretations
    """
    await require_plan(current_user, "pro")
    
    try:
        results = await defi_interpreter_service.batch_interpret(
            tx_hashes=request.tx_hashes,
            chain=request.chain
        )
        
        return {
            "total": len(request.tx_hashes),
            "successful": len(results),
            "failed": len(request.tx_hashes) - len(results),
            "interpretations": results
        }
        
    except Exception as e:
        logger.error(f"Batch interpretation failed: {e}")
        raise HTTPException(status_code=500, detail="Batch interpretation failed")


@router.get("/protocols")
async def get_supported_protocols(
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Get list of supported DeFi protocols.
    
    **Requires:** Community+ plan
    
    **Returns:**
    - Protocol statistics and supported transaction types
    """
    await require_plan(current_user, "community")
    
    try:
        stats = await defi_interpreter_service.get_protocol_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get protocol stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get protocol stats")
