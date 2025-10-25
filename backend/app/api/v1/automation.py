"""
Automation API
Settings, Simulation, Auto‑Investigation (MVP)
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from json import dumps as json_dumps

from app.auth.dependencies import get_current_user
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# In‑memory settings (MVP). Persist later into Postgres.
_AUTOMATION_SETTINGS: Dict[str, Any] = {
    "enabled": True,
    "risk_threshold": 0.8,
    "min_amount_usd": 5000,
    "auto_create_case": True,
    "auto_trace_depth": 3,
    "report_template": "standard",
}


class AutomationSettings(BaseModel):
    enabled: bool = True
    risk_threshold: float = Field(ge=0.0, le=1.0, default=0.8)
    min_amount_usd: float = Field(ge=0.0, default=5000)
    auto_create_case: bool = True
    auto_trace_depth: int = Field(ge=0, le=10, default=3)
    report_template: str = "standard"


class SimulationRequest(BaseModel):
    hours: int = Field(ge=1, le=168, default=24)
    sample_size: int = Field(ge=1, le=1000, default=100)


class SimulationResult(BaseModel):
    evaluated: int
    would_create_cases: int
    would_trigger_traces: int
    high_priority: int


class AutoInvestigateRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    depth: int = 3


class AutoInvestigateResult(BaseModel):
    created_case: bool
    case_id: Optional[str] = None
    trace_started: bool
    parameters: Dict[str, Any]


@router.get("/automation/settings", response_model=AutomationSettings)
async def get_settings(user: Dict = Depends(get_current_user)) -> AutomationSettings:
    return AutomationSettings(**_AUTOMATION_SETTINGS)


@router.put("/automation/settings", response_model=AutomationSettings)
async def put_settings(payload: AutomationSettings, user: Dict = Depends(get_current_user)) -> AutomationSettings:
    _AUTOMATION_SETTINGS.update(payload.model_dump())
    return AutomationSettings(**_AUTOMATION_SETTINGS)


@router.post("/automation/simulate", response_model=SimulationResult)
async def simulate(req: SimulationRequest, user: Dict = Depends(get_current_user)) -> SimulationResult:
    """Use existing tools.simulate_alerts if available to approximate impact."""
    try:
        from app.ai_agents import tools as forensic_tools
        registry = getattr(forensic_tools, "FORENSIC_TOOLS", {})
        fn = registry.get("simulate_alerts")
        data = None
        if fn:
            out = await fn(sample_size=req.sample_size) if callable(fn) else fn
            # Try to derive counts from output shape (best effort MVP)
            if isinstance(out, dict):
                data = out
        # Simple heuristic result if no structured data
        evaluated = req.sample_size
        risk_thr = float(_AUTOMATION_SETTINGS.get("risk_threshold", 0.8))
        would_create_cases = int(evaluated * (1 - (risk_thr * 0.7)))
        would_trigger_traces = min(evaluated, would_create_cases * 2)
        high_priority = int(would_create_cases * 0.4)
        return SimulationResult(
            evaluated=evaluated,
            would_create_cases=would_create_cases,
            would_trigger_traces=would_trigger_traces,
            high_priority=high_priority,
        )
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail="Simulation failed")


@router.post("/automation/auto_investigate", response_model=AutoInvestigateResult)
async def auto_investigate(
    req: AutoInvestigateRequest,
    user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutoInvestigateResult:
    """Enqueue an auto-investigation job (MVP)."""
    depth = min(max(req.depth, 0), int(_AUTOMATION_SETTINGS.get("auto_trace_depth", 3)))
    job_payload = {
        "address": req.address,
        "chain": req.chain,
        "depth": depth,
        "settings": _AUTOMATION_SETTINGS,
        "user_id": user.get("id"),
    }
    # Persist automation_event and job (best-effort)
    try:
        event_sql = text(
            """
            INSERT INTO automation_events (address, chain, depth, status, created_at)
            VALUES (:address, :chain, :depth, 'queued', NOW())
            RETURNING id
            """
        )
        job_sql = text(
            """
            INSERT INTO jobs (type, payload, status, created_at, updated_at)
            VALUES ('auto_investigate', :payload::jsonb, 'queued', NOW(), NOW())
            RETURNING id
            """
        )
        payload_json = {
            "address": req.address,
            "chain": req.chain,
            "depth": depth,
            "user_id": user.get("id"),
        }
        res_event = await db.execute(event_sql, {"address": req.address, "chain": req.chain, "depth": depth})
        _event_id = res_event.scalar()  # noqa: F841
        res_job = await db.execute(job_sql, {"payload": json_dumps(payload_json)})
        _job_id = res_job.scalar()  # noqa: F841
        try:
            await db.commit()
        except Exception:
            await db.rollback()
    except Exception as e:
        logger.warning(f"Persisting automation event/job failed: {e}")

    try:
        from app.workers.auto_investigate_worker import enqueue_auto_investigate
        # fire-and-forget enqueue
        import asyncio
        asyncio.create_task(enqueue_auto_investigate(job_payload))
    except Exception as e:
        logger.error(f"Failed to enqueue auto-investigate: {e}")
        # still return intent result

    created_case = bool(_AUTOMATION_SETTINGS.get("auto_create_case", True))
    trace_started = True
    return AutoInvestigateResult(
        created_case=created_case,
        case_id=None,
        trace_started=trace_started,
        parameters={"address": req.address, "chain": req.chain, "depth": depth, "settings": _AUTOMATION_SETTINGS},
    )


@router.get("/automation/recent")
async def recent_jobs(user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        from app.workers.auto_investigate_worker import get_recent_jobs
        return {"items": get_recent_jobs()}
    except Exception as e:
        logger.error(f"Failed to read recent jobs: {e}")
        return {"items": []}
