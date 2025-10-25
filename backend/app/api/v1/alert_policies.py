"""
Alert Policies API
==================

CRUD + Versioning + Simulation for alert policies.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, Field

from app.services.alert_policy_service import alert_policy_service
from app.auth.dependencies import get_current_user_strict
from app.services.usage_service import check_and_consume_credits
from app.services.tenant_service import tenant_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== Models =====
class PolicyCreateRequest(BaseModel):
    policy_id: str = Field(..., description="Unique policy ID")
    name: str = Field(..., description="Display name")
    rules: Dict[str, Any] = Field(..., description="Policy rules payload (JSON)")
    notes: Optional[str] = None


class PolicyUpdateRequest(BaseModel):
    rules: Dict[str, Any] = Field(..., description="Policy rules payload (JSON)")
    notes: Optional[str] = None
    status: str = Field("draft", pattern="^(draft|active|archived)$")


class PolicyStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(draft|active|archived)$")


class SimulationRequest(BaseModel):
    policy_rules: Optional[Dict[str, Any]] = Field(None, description="Rules to simulate (optional if policy_id provided)")
    policy_id: Optional[str] = Field(None, description="Existing policy to use for simulation")
    events: List[Dict[str, Any]] = Field(default_factory=list)


# ===== Endpoints =====
@router.get("", summary="List policies")
async def list_policies() -> Dict[str, Any]:
    try:
        items = alert_policy_service.list_policies()
        return {"policies": items, "total": len(items)}
    except Exception as e:
        logger.error(f"list_policies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}", summary="Get policy by ID")
async def get_policy(policy_id: str) -> Dict[str, Any]:
    try:
        item = alert_policy_service.get_policy(policy_id)
        if not item:
            raise HTTPException(status_code=404, detail="policy not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_policy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", summary="Create a policy")
async def create_policy(payload: PolicyCreateRequest) -> Dict[str, Any]:
    try:
        item = alert_policy_service.create_policy(
            policy_id=payload.policy_id,
            name=payload.name,
            rules=payload.rules,
            created_by="api",
            notes=payload.notes,
        )
        return item
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"create_policy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{policy_id}/versions", summary="Create new policy version")
async def update_policy(policy_id: str, payload: PolicyUpdateRequest) -> Dict[str, Any]:
    try:
        item = alert_policy_service.update_policy(
            policy_id=policy_id,
            rules=payload.rules,
            created_by="api",
            notes=payload.notes,
            status=payload.status,
        )
        return item
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"update_policy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{policy_id}/versions/{version}/status", summary="Set policy version status")
async def set_policy_status(policy_id: str, version: int, payload: PolicyStatusRequest) -> Dict[str, Any]:
    try:
        item = alert_policy_service.set_status(policy_id, version, payload.status)
        # Auto-reload active policies via service facade after status change
        try:
            from app.services.alert_service import alert_service
            _summary = alert_service.reload_policies()
            logger.info("Policies reloaded: %s active rules", _summary.get("total_rules"))
        except Exception as re:
            # Do not fail the status update if reload fails; log warning
            logger.warning(f"policy reload after status change failed: {re}")
        return item
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"set_policy_status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate", summary="Simulate policy rules against events")
async def simulate(
    payload: SimulationRequest,
    plan_id: str | None = None,
    current_user: dict = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    try:
        if not payload.policy_rules and not payload.policy_id:
            raise HTTPException(status_code=400, detail="policy_rules or policy_id required")

        rules: Dict[str, Any]
        if payload.policy_rules:
            rules = payload.policy_rules
        else:
            pol = alert_policy_service.get_policy(payload.policy_id or "")
            if not pol:
                raise HTTPException(status_code=404, detail="policy not found")
            # Use latest version rules
            latest = max(pol["versions"], key=lambda v: v["version"]) if pol["versions"] else None
            rules = latest["rules"] if latest else {"rules": []}

        # Credits-Konsum: 1 Credit je Event (konfigurierbar)
        amount = max(len(payload.events), 1)
        tenant_id = str(current_user["user_id"])  # vereinfachtes Tenant-Modell
        effective_plan = plan_id or tenant_service.get_plan_id(tenant_id)
        allowed = await check_and_consume_credits(tenant_id, effective_plan, amount, reason="policy_simulation")
        if not allowed:
            raise HTTPException(status_code=402, detail="Nicht genügend Credits für Simulation")

        result = alert_policy_service.simulate(rules, payload.events)
        return {
            "policy_id": payload.policy_id,
            "summary": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"simulate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", summary="Reload active policies")
async def reload_policies() -> Dict[str, Any]:
    """Reload active policy rules into the running alert engine."""
    try:
        from app.services.alert_service import alert_service
        summary = alert_service.reload_policies()
        return {"status": "reloaded", "active_rules_count": summary.get("total_rules", 0)}
    except Exception as e:
        logger.error(f"reload_policies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class EvaluateRequest(BaseModel):
    policy_rules: Optional[Dict[str, Any]] = Field(None, description="Rules to evaluate (optional if policy_id provided)")
    policy_id: Optional[str] = Field(None, description="Existing policy to use for evaluation")
    event: Dict[str, Any] = Field(default_factory=dict)


@router.post("/evaluate", summary="Evaluate a single event against policy rules")
async def evaluate_event(payload: EvaluateRequest) -> Dict[str, Any]:
    try:
        if not payload.policy_rules and not payload.policy_id:
            raise HTTPException(status_code=400, detail="policy_rules or policy_id required")

        rules: Dict[str, Any]
        if payload.policy_rules:
            rules = payload.policy_rules
        else:
            pol = alert_policy_service.get_policy(payload.policy_id or "")
            if not pol:
                raise HTTPException(status_code=404, detail="policy not found")
            latest = max(pol["versions"], key=lambda v: v["version"]) if pol["versions"] else None
            rules = latest["rules"] if latest else {"rules": []}

        # reuse simulate logic with a single event
        result = alert_policy_service.simulate(rules, [payload.event])
        return {"summary": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"evaluate_event error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
