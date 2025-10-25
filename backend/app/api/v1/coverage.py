"""
Coverage API
Provides current chain/bridge/mixer coverage and adapter status
"""

from fastapi import APIRouter
from typing import Dict, Any

from app.services.coverage_service import aggregate_coverage, get_adapter_health
from app.normalizer.bridge_patterns import list_bridge_patterns
from app.tracing.mixer_rules import list_mixer_rules

router = APIRouter()


@router.get("/", summary="Get coverage overview")
async def get_coverage() -> Dict[str, Any]:
    """Return current coverage aggregated from adapters and heuristics."""
    return await aggregate_coverage()


@router.get("/health", summary="Get adapter health status")
async def get_health() -> Dict[str, Any]:
    """Return health status for configured adapters."""
    return await get_adapter_health()


@router.get("/bridges", summary="List known bridge patterns")
async def get_bridges() -> Dict[str, Any]:
    return {"bridges": list_bridge_patterns()}


@router.get("/mixers", summary="List known mixer rules")
async def get_mixers() -> Dict[str, Any]:
    return {"mixers": list_mixer_rules()}
