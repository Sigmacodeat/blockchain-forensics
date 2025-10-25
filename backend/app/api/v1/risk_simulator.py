from __future__ import annotations

from fastapi import APIRouter, Body, Depends

from app.api.v1.schemas.risk_simulator import (
    RiskSimulationScenario,
    RiskSimulationResult,
)
from app.auth.dependencies import require_plan
from app.services.risk_simulator import risk_simulator

router = APIRouter(prefix="/risk-simulator", tags=["Risk Simulator"])


@router.post("/simulate", response_model=RiskSimulationResult)
async def simulate_risk(
    scenario: RiskSimulationScenario = Body(...),
    current_user: dict = Depends(require_plan("business")),
) -> RiskSimulationResult:
    """Run predictive risk simulation for a scenario."""
    return await risk_simulator.simulate(scenario)


@router.post("/simulate/batch", response_model=RiskSimulationResult)
async def simulate_batch(
    scenario: RiskSimulationScenario = Body(...),
    current_user: dict = Depends(require_plan("enterprise")),
) -> RiskSimulationResult:
    """Alias for simulate endpoint (reserved for multi-scenario support)."""
    return await risk_simulator.simulate(scenario)
