from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_strict
from app.services.bitcoin_script_batch_analyzer import analyze_batch_scripts

router = APIRouter(prefix="/bitcoin-script", tags=["Bitcoin Script"])


class BatchScriptRequest(BaseModel):
    txids: List[str] = Field(..., min_length=1, max_length=100, description="Bitcoin TXIDs to analyze")


@router.post("/analyze-batch")
async def analyze_batch_bitcoin_scripts(
    payload: BatchScriptRequest,
    _user: Dict[str, Any] = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    """Analysiert mehrere Bitcoin-TXIDs in Batch mit aggregierten Statistiken."""
    try:
        res = await analyze_batch_scripts(payload.txids)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("message", "Batch analysis failed"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze batch: {str(e)}")
