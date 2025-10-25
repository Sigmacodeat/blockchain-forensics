"""
Typology DSL API
- List/Reload rules
- Simulate rule evaluation against an event
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Query, Depends, HTTPException
from pydantic import BaseModel

from app.services.typology_engine import typology_engine
from app.auth.dependencies import require_admin

router = APIRouter(prefix="/typologies", tags=["Typologies"])


class SimulateRequest(BaseModel):
    event: Dict[str, Any]
    variant: Optional[str] = None


@router.get("/rules", summary="List loaded typology rules")
async def list_rules(variant: Optional[str] = Query(None)) -> Dict[str, Any]:
    try:
        rules = typology_engine.list_rules(variant=variant)
        return {"count": len(rules), "rules": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", summary="Reload typology rules from YAML files")
async def reload_rules(current_user: dict = Depends(require_admin)) -> Dict[str, Any]:
    try:
        count = typology_engine.load_rules()
        return {"reloaded": True, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate", summary="Simulate a single event against typology rules")
async def simulate_typologies(payload: SimulateRequest = Body(...)) -> Dict[str, Any]:
    try:
        matches = typology_engine.evaluate(payload.event, variant=payload.variant)
        return {"matches": matches, "match_count": len(matches)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
