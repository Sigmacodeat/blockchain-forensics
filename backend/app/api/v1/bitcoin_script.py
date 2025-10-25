from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user_strict
from app.services.bitcoin_script_analyzer import bitcoin_script_analyzer

router = APIRouter(prefix="/bitcoin-script", tags=["Bitcoin Script"])


@router.get("/analyze/{txid}")
async def analyze_bitcoin_script(
    txid: str,
    _user: Dict[str, Any] = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    """Liefert eine Script-Level-Analyse für eine Bitcoin-Transaktion (leichtgewichtig)."""
    try:
        res = await bitcoin_script_analyzer.analyze_tx(txid)
        if not res.get("success"):
            # Liefere 404 bei nicht gefundener TX oder fehlender RPC
            msg = res.get("message") or "analysis failed"
            code = 404 if "not found" in msg.lower() else 503 if "rpc" in msg.lower() else 400
            raise HTTPException(status_code=code, detail=msg)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze tx: {str(e)}")
