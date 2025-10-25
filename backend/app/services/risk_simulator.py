from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.risk_service import service as risk_service
from app.intel.models import ThreatLevel


class ScenarioWeights(BaseModel):
    watchlist: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    labels: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    taint: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    exposure: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    graph: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    threat_intel: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AddressScenario(BaseModel):
    chain: str = Field(..., description="Blockchain name, e.g. 'ethereum'")
    address: str = Field(..., description="Blockchain address to simulate")
    assume_watchlist_hit: bool = Field(default=False, description="Treat address as watchlist hit")
    assume_labels_high_risk: bool = Field(
        default=False, description="Assume labels imply high-risk categorisation"
    )
    assume_threat_level: Optional[ThreatLevel] = Field(
        default=None, description="Override threat intel level for simulation"
    )
    assume_exposure: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Override exposure factor"
    )
    assume_graph_signal: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Override graph signal factor"
    )
    assume_taint: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Override taint factor"
    )
    notes: Optional[str] = Field(default=None, description="Optional analyst notes")


class RiskSimulationScenario(BaseModel):
    name: str = Field(..., description="Scenario name")
    alert_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Threshold (0-100) marking high-risk in scenario results",
    )
    weights: Optional[ScenarioWeights] = Field(
        default=None, description="Optional weight overrides for simulation"
    )
    addresses: List[AddressScenario] = Field(
        default_factory=list, description="Addresses to simulate"
    )
    notes: Optional[str] = Field(default=None, description="Scenario level notes")


class AddressSimulationResult(BaseModel):
    chain: str
    address: str
    baseline_score: int
    scenario_score: int
    delta: int
    baseline: Dict[str, Any]
    scenario_factors: Dict[str, float]
    contributions: Dict[str, float]
    assumptions: Dict[str, Any]
    notes: Optional[str] = None


class RiskSimulationSummary(BaseModel):
    addresses: int
    average_score: float
    average_delta: float
    max_score: int
    min_score: int
    addresses_above_threshold: int


class RiskSimulationResult(BaseModel):
    scenario: str
    notes: Optional[str]
    generated_at: datetime
    alert_threshold: int
    baseline_weights: Dict[str, float]
    scenario_weights: Dict[str, float]
    results: List[AddressSimulationResult]
    summary: RiskSimulationSummary


class RiskSimulatorService:
    """Predictive risk simulation based on configurable scenarios."""

    _threat_level_factors: Dict[ThreatLevel, float] = {
        ThreatLevel.CRITICAL: 1.0,
        ThreatLevel.HIGH: 0.85,
        ThreatLevel.MEDIUM: 0.6,
        ThreatLevel.LOW: 0.35,
        ThreatLevel.INFO: 0.15,
    }

    async def simulate(self, scenario: RiskSimulationScenario) -> RiskSimulationResult:
        if not scenario.addresses:
            return RiskSimulationResult(
                scenario=scenario.name,
                notes=scenario.notes,
                generated_at=datetime.utcnow(),
                alert_threshold=scenario.alert_threshold,
                baseline_weights=risk_service.get_weights(),
                scenario_weights=risk_service.get_weights(),
                results=[],
                summary=RiskSimulationSummary(
                    addresses=0,
                    average_score=0.0,
                    average_delta=0.0,
                    max_score=0,
                    min_score=0,
                    addresses_above_threshold=0,
                ),
            )

        baseline_weights = risk_service.get_weights()
        scenario_weights = baseline_weights.copy()
        if scenario.weights:
            scenario_weights.update(
                scenario.weights.model_dump(exclude_none=True)
            )

        results: List[AddressSimulationResult] = []
        scenario_scores: List[int] = []
        deltas: List[int] = []
        addresses_above_threshold = 0

        for addr in scenario.addresses:
            baseline_result = await risk_service.score_address(addr.chain, addr.address)
            baseline_data = asdict(baseline_result)

            scenario_factors: Dict[str, float] = dict(
                baseline_data.get("factors", {})
            )
            assumptions: Dict[str, Any] = {}

            if addr.assume_watchlist_hit:
                scenario_factors["watchlist"] = 1.0
                assumptions["assume_watchlist_hit"] = True

            if addr.assume_labels_high_risk:
                scenario_factors["labels"] = max(
                    0.9, scenario_factors.get("labels", 0.0)
                )
                assumptions["assume_labels_high_risk"] = True

            if addr.assume_threat_level:
                scenario_factors["threat_intel"] = self._threat_level_factors.get(
                    addr.assume_threat_level,
                    scenario_factors.get("threat_intel", 0.0),
                )
                assumptions["assume_threat_level"] = addr.assume_threat_level.value

            if addr.assume_exposure is not None:
                scenario_factors["exposure"] = addr.assume_exposure
                assumptions["assume_exposure"] = addr.assume_exposure

            if addr.assume_graph_signal is not None:
                scenario_factors["graph"] = addr.assume_graph_signal
                assumptions["assume_graph_signal"] = addr.assume_graph_signal

            if addr.assume_taint is not None:
                scenario_factors["taint"] = addr.assume_taint
                assumptions["assume_taint"] = addr.assume_taint

            for key in scenario_weights.keys():
                scenario_factors.setdefault(key, 0.0)
                scenario_factors[key] = float(
                    max(0.0, min(1.0, scenario_factors[key]))
                )

            scenario_raw = sum(
                scenario_weights.get(key, 0.0)
                * scenario_factors.get(key, 0.0)
                for key in scenario_weights.keys()
            )
            scenario_raw = max(0.0, min(1.0, scenario_raw))
            scenario_score = int(round(scenario_raw * 100))
            baseline_score = int(baseline_result.score)
            delta = scenario_score - baseline_score

            scenario_scores.append(scenario_score)
            deltas.append(delta)
            if scenario_score >= scenario.alert_threshold:
                addresses_above_threshold += 1

            contributions = {
                key: round(
                    scenario_weights.get(key, 0.0)
                    * scenario_factors.get(key, 0.0)
                    * 100,
                    2,
                )
                for key in scenario_weights.keys()
            }

            results.append(
                AddressSimulationResult(
                    chain=addr.chain,
                    address=addr.address.lower(),
                    baseline_score=baseline_score,
                    scenario_score=scenario_score,
                    delta=delta,
                    baseline=baseline_data,
                    scenario_factors={
                        key: round(value, 3)
                        for key, value in scenario_factors.items()
                    },
                    contributions=contributions,
                    assumptions=assumptions,
                    notes=addr.notes,
                )
            )

        avg_score = round(mean(scenario_scores), 2) if scenario_scores else 0.0
        avg_delta = round(mean(deltas), 2) if deltas else 0.0
        max_score = max(scenario_scores) if scenario_scores else 0
        min_score = min(scenario_scores) if scenario_scores else 0

        summary = RiskSimulationSummary(
            addresses=len(results),
            average_score=avg_score,
            average_delta=avg_delta,
            max_score=max_score,
            min_score=min_score,
            addresses_above_threshold=addresses_above_threshold,
        )

        return RiskSimulationResult(
            scenario=scenario.name,
            notes=scenario.notes,
            generated_at=datetime.utcnow(),
            alert_threshold=scenario.alert_threshold,
            baseline_weights=baseline_weights,
            scenario_weights=scenario_weights,
            results=results,
            summary=summary,
        )


risk_simulator = RiskSimulatorService()


__all__ = [
    "ScenarioWeights",
    "AddressScenario",
    "RiskSimulationScenario",
    "AddressSimulationResult",
    "RiskSimulationSummary",
    "RiskSimulationResult",
    "RiskSimulatorService",
    "risk_simulator",
]
