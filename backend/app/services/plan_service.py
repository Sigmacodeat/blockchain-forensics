"""
Plan & Pricing Service
Lädt `app/config/plans.json` und stellt Helper für Plan-Abfragen bereit.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_PLANS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "plans.json")
_PLANS_PATH = os.path.normpath(_PLANS_PATH)

@dataclass
class Plan:
    id: str
    name: str
    monthly_price_usd: Optional[float] = None
    yearly_price_usd: Optional[float] = None
    pricing: Optional[str] = None
    quotas: Dict[str, Any] = None
    features: Dict[str, Any] = None
    sla: Dict[str, Any] = None

@dataclass
class PricingConfig:
    currency: str
    annual_discount_percent: int
    overage: Dict[str, Any]
    addons: Dict[str, Any]
    plans: List[Plan]

class PlanService:
    def __init__(self) -> None:
        self._config: Optional[PricingConfig] = None
        self._plans_by_id: Dict[str, Plan] = {}
        self._load()

    def _load(self) -> None:
        with open(_PLANS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        plans: List[Plan] = [Plan(**p) for p in raw.get("plans", [])]
        self._config = PricingConfig(
            currency=raw.get("currency", "USD"),
            annual_discount_percent=raw.get("annual_discount_percent", 20),
            overage=raw.get("overage", {}),
            addons=raw.get("addons", {}),
            plans=plans,
        )
        self._plans_by_id = {p.id: p for p in plans}

    def reload(self) -> None:
        self._load()

    def get_config(self) -> PricingConfig:
        assert self._config is not None
        return self._config

    def list_plans(self) -> List[Plan]:
        return list(self._plans_by_id.values())

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        return self._plans_by_id.get(plan_id)

    def get_monthly_credits(self, plan_id: str) -> Optional[int]:
        p = self.get_plan(plan_id)
        if not p or not p.quotas:
            return None
        val = p.quotas.get("credits_monthly")
        return int(val) if isinstance(val, (int, float, str)) and str(val).isdigit() else None

plan_service = PlanService()
