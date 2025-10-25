from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_strict
from app.services.multi_agent_orchestrator import multi_agent_orchestrator

router = APIRouter(prefix="/multi-agent", tags=["Multi-Agent"])


class WorkflowExecutionRequest(BaseModel):
    workflow_name: str = Field(..., description="Workflow: standard_investigation, privacy_focused, risk_assessment")
    query: str = Field(..., description="Untersuchungsanfrage")
    case_id: Optional[str] = Field(None, description="Optional Case-ID")


class CollaborativeInvestigationRequest(BaseModel):
    query: str = Field(..., description="KI-gesteuerte Anfrage")
    case_id: Optional[str] = Field(None, description="Optional Case-ID")


@router.post("/execute-workflow")
async def execute_workflow(
    payload: WorkflowExecutionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    """Führt einen vordefinierten Multi-Agent-Workflow aus"""
    try:
        result = await multi_agent_orchestrator.execute_workflow(
            workflow_name=payload.workflow_name,
            query=payload.query,
            initial_context={"user_id": current_user["user_id"], "case_id": payload.case_id}
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/collaborative-investigation")
async def collaborative_investigation(
    payload: CollaborativeInvestigationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_strict),
) -> Dict[str, Any]:
    """KI-gesteuerte kollaborative Untersuchung mit LangChain-Orchestrierung"""
    try:
        result = await multi_agent_orchestrator.collaborative_investigation(
            query=payload.query,
            case_id=payload.case_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collaborative investigation failed: {str(e)}")


@router.get("/workflows")
async def list_workflows(_user: Dict[str, Any] = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """Listet verfügbare Workflows"""
    workflows = {}
    for name, wf in multi_agent_orchestrator.workflows.items():
        workflows[name] = {
            "name": wf.name,
            "description": wf.description,
            "agents": wf.agents,
            "max_iterations": wf.max_iterations
        }

    return {
        "workflows": workflows,
        "langchain_available": multi_agent_orchestrator.langchain_available
    }
