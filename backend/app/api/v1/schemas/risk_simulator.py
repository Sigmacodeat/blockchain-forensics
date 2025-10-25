from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid circular imports at runtime while providing type hints
    from app.services.risk_simulator import (
        ScenarioWeights,
        AddressScenario,
        RiskSimulationScenario,
        AddressSimulationResult,
        RiskSimulationSummary,
        RiskSimulationResult,
    )

# Re-export models from service layer for API schema usage.
from app.services.risk_simulator import (  # noqa: F401
    ScenarioWeights,
    AddressScenario,
    RiskSimulationScenario,
    AddressSimulationResult,
    RiskSimulationSummary,
    RiskSimulationResult,
)

__all__ = [
    "ScenarioWeights",
    "AddressScenario",
    "RiskSimulationScenario",
    "AddressSimulationResult",
    "RiskSimulationSummary",
    "RiskSimulationResult",
]
