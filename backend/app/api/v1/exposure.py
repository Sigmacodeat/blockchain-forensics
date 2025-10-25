"""
Exposure API
============
Endpoints zur schnellen Berechnung von Direct/Indirect Exposure
gegenüber Hochrisiko-/Sanktions-Entitäten.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Depends

from app.analytics.exposure_service import exposure_service
from app.auth.dependencies import get_current_user_strict

router = APIRouter()


@router.get("/calculate")
async def calculate_exposure(
    address: str = Query(..., description="Adresse (Account/Contract)"),
    max_hops: Optional[int] = Query(None, ge=1, le=10),
    # optionale Kontextfelder (Labels, Graph-Summary, Gegenparteien), Base64/JSON nicht nötig – wir erlauben JSON im Query nicht, daher Body-Variante unten
    current_user: dict = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    try:
        result = await exposure_service.calculate(address=address, max_hops=max_hops)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate")
async def calculate_exposure_with_context(
    payload: Dict[str, Any] = Body(..., description="{ address, max_hops?, context? }"),
    current_user: dict = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    try:
        address = payload.get("address")
        if not address:
            raise HTTPException(status_code=400, detail="address fehlt")
        max_hops = payload.get("max_hops")
        context = payload.get("context")
        result = await exposure_service.calculate(address=address, max_hops=max_hops, context=context)
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_calculate_exposure(
    payload: Dict[str, Any] = Body(..., description="{ addresses: string[], max_hops?, context_by_address? }"),
    current_user: dict = Depends(get_current_user_strict),
) -> Dict[str, Dict[str, Any]]:
    try:
        addresses = payload.get("addresses") or []
        if not isinstance(addresses, list) or not all(isinstance(a, str) for a in addresses):
            raise HTTPException(status_code=400, detail="addresses muss string[] sein")
        max_hops = payload.get("max_hops")
        context_by_address = payload.get("context_by_address")
        result = await exposure_service.batch_calculate(addresses=addresses, max_hops=max_hops, context_by_address=context_by_address)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
