from __future__ import annotations
from typing import Any, Dict, Optional
import asyncio
import json
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.soar_engine import soar_engine
from app.auth.dependencies import require_admin

router = APIRouter(prefix="/soar", tags=["SOAR"])


class RunRequest(BaseModel):
    event: Dict[str, Any]


class TogglePlaybookRequest(BaseModel):
    enabled: bool


def _sse_pack(event_type: str, payload: dict) -> str:
    return f"event: {event_type}\n" + f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/playbooks", summary="List loaded playbooks")
async def list_playbooks() -> Dict[str, Any]:
    try:
        pbs = soar_engine.list_playbooks()
        return {"count": len(pbs), "playbooks": pbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playbooks/{playbook_id}", summary="Get playbook details")
async def get_playbook(playbook_id: str) -> Dict[str, Any]:
    try:
        pb = soar_engine.get_playbook(playbook_id)
        if not pb:
            raise HTTPException(status_code=404, detail="Playbook not found")
        # Serialize minimal details without leaking unsafe expressions
        return {
            "id": pb.id,
            "name": pb.name,
            "enabled": pb.enabled,
            "tags": getattr(pb, "tags", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/playbooks/{playbook_id}/enabled", summary="Enable/disable a playbook")
async def toggle_playbook(
    playbook_id: str,
    payload: TogglePlaybookRequest,
    current_user: dict = Depends(require_admin)
) -> Dict[str, Any]:
    try:
        ok = soar_engine.set_enabled(playbook_id, bool(payload.enabled))
        if not ok:
            raise HTTPException(status_code=404, detail="Playbook not found")
        return {"id": playbook_id, "enabled": bool(payload.enabled)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", summary="Reload playbooks from YAML files")
async def reload_playbooks(current_user: dict = Depends(require_admin)) -> Dict[str, Any]:
    try:
        cnt = soar_engine.load_playbooks()
        return {"reloaded": True, "count": cnt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", summary="Run SOAR engine for a single event")
async def run_playbooks(payload: RunRequest = Body(...)) -> Dict[str, Any]:
    try:
        res = soar_engine.run(payload.event)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", summary="Evaluate SOAR playbooks without executing actions")
async def evaluate_playbooks(payload: RunRequest = Body(...)) -> Dict[str, Any]:
    try:
        res = soar_engine.evaluate_only(payload.event)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playbooks/run-stream", summary="Run playbooks with SSE streaming")
async def run_playbooks_stream(
    payload: RunRequest = Body(...),
    evaluate_only: bool = Query(False, description="Only evaluate matches without executing actions")
):
    async def event_stream():
        yield _sse_pack("playbook.ready", {"ok": True})
        await asyncio.sleep(0)
        try:
            result = soar_engine.evaluate_only(payload.event) if evaluate_only else soar_engine.run(payload.event)
            matches = result.get("matches", []) if isinstance(result, dict) else []
            for idx, match in enumerate(matches):
                await asyncio.sleep(0)
                yield _sse_pack(
                    "playbook.match",
                    {
                        "index": idx,
                        "playbook_id": match.get("playbook_id"),
                        "name": match.get("name"),
                        "tags": match.get("tags"),
                        "actions": match.get("actions") if not evaluate_only else None,
                    },
                )
            await asyncio.sleep(0)
            yield _sse_pack("playbook.result", result if isinstance(result, dict) else {"result": result})
        except Exception as exc:  # pragma: no cover - streaming error path
            yield _sse_pack("playbook.error", {"detail": str(exc)})

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)
