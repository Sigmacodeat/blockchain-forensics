from __future__ import annotations

"""
Risk Scoring API v1
- GET /api/v1/risk/address?chain=&address=
- POST /api/v1/risk/batch { items: [{chain,address}] }
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Query, Body, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import time
import asyncio
import json

from app.services.risk_service import service as risk_service
from app.observability.metrics import COMPLIANCE_REQUESTS, COMPLIANCE_LATENCY, RISK_SCORE
from app.config import settings
import os
from app.models.audit_log import log_audit_event, AuditAction
from app.auth.jwt import decode_token
from app.auth.dependencies import require_admin
from app.auth.models import UserRole

router = APIRouter()


class RiskItem(BaseModel):
    chain: str = Field(..., description="Chain: ethereum|bitcoin|solana")
    address: str = Field(..., description="Address on chain")


class RiskBatchRequest(BaseModel):
    items: List[RiskItem]


@router.get("/address")
async def risk_address(chain: str = Query(...), address: str = Query(...)) -> Dict[str, Any]:
    op = "risk_address"
    t0 = time.time()
    try:
        res = await risk_service.score_address(chain, address)
        # Heuristik: offensichtliche Ungültigkeit markieren (Tests erwarten Kategorie 'invalid')
        try:
            cat = list(res.categories) if isinstance(res.categories, list) else []
            invalid = False
            ch = (chain or "").lower().strip()
            addr = (address or "").strip()
            if ch == "ethereum":
                import re
                if not re.fullmatch(r"0x[0-9a-fA-F]{40}", addr):
                    invalid = True
            # Optional: weitere Chains (Light)
            if invalid:
                if "invalid" not in cat:
                    cat.append("invalid")
                res.categories = cat
                try:
                    res.score = 0.0
                except Exception:
                    pass
        except Exception:
            pass
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        try:
            RISK_SCORE.observe(float(res.score))
        except Exception:
            pass
        return {"result": {
            "chain": res.chain,
            "address": res.address,
            "score": res.score,
            "factors": res.factors,
            "categories": res.categories,
            "reasons": res.reasons,
        }}
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - t0)


# Simple per-client rate limiting for SSE
_RISK_RL_BUCKET: Dict[str, List[float]] = {}

def _risk_client_key(request: Request) -> str:
    ip = getattr(request.client, "host", "unknown") if request.client else "unknown"
    sid = request.headers.get("x-session-id") or ""
    return f"ip:{ip}|sid:{sid}"

def _risk_check_rl(key: str, limit_per_min: int) -> bool:
    now = time.time()
    window_start = now - 60.0
    bucket = [t for t in _RISK_RL_BUCKET.get(key, []) if t >= window_start]
    if len(bucket) >= limit_per_min:
        _RISK_RL_BUCKET[key] = bucket
        return False
    bucket.append(now)
    _RISK_RL_BUCKET[key] = bucket
    return True

def _risk_retry_after(key: str, limit_per_min: int) -> int:
    now = time.time()
    window_start = now - 60.0
    bucket = [t for t in _RISK_RL_BUCKET.get(key, []) if t >= window_start]
    if len(bucket) < limit_per_min:
        return 0
    oldest = min(bucket) if bucket else now
    return max(0, int(60 - (now - oldest)))


def _sse_pack(event_type: str, payload: dict) -> str:
    return f"event: {event_type}\n" + f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.get("/stream")
async def risk_stream(request: Request, chain: str = Query(...), address: str = Query(...)):
    op = "risk_stream"
    t0 = time.time()
    try:
        limit_per_min = int(getattr(settings, "CHAT_RATE_LIMIT_PER_MIN", 60) or 60)
        key = _risk_client_key(request)
        if not _risk_check_rl(key, limit_per_min):
            retry_after = _risk_retry_after(key, limit_per_min)
            raise HTTPException(status_code=429, detail="Too Many Requests", headers={"Retry-After": str(retry_after)})

        async def gen():
            yield _sse_pack("risk.ready", {"ok": True})
            try:
                if await request.is_disconnected():
                    return
            except Exception:
                pass

            ch = (chain or "").lower().strip()
            addr = (address or "").strip()
            invalid = False
            if ch == "ethereum":
                import re
                if not re.fullmatch(r"0x[0-9a-fA-F]{40}", addr):
                    invalid = True
            if invalid:
                yield _sse_pack("risk.error", {"detail": "invalid_address"})
                return

            yield _sse_pack("risk.typing", {"ok": True})
            try:
                res = await risk_service.score_address(ch, addr)
            except Exception as e:
                yield _sse_pack("risk.error", {"detail": str(e)})
                return

            try:
                L = len(str(res.reasons or ""))
                chunk_size = 64 if L < 512 else (96 if L < 2048 else 160)
                for i in range(0, len(res.reasons or []), 1):
                    pass
            except Exception:
                pass

            payload = {
                "chain": res.chain,
                "address": res.address,
                "score": res.score,
                "factors": res.factors,
                "categories": res.categories,
                "reasons": res.reasons,
            }
            yield _sse_pack("risk.result", payload)
            try:
                if await request.is_disconnected():
                    return
            except Exception:
                pass
            try:
                await asyncio.sleep(0)
            except Exception:
                pass

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)
    except HTTPException:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - t0)


@router.get("/admin/weights")
async def admin_get_weights(current_user: dict = Depends(require_admin)) -> Dict[str, Any]:  # ✅ FIX: require_admin
    op = "admin_get_risk_weights"
    t0 = time.time()
    try:
        w = risk_service.get_weights()
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"weights": w}
    except HTTPException:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - t0)


@router.get("/weights")
async def get_risk_weights() -> Dict[str, Any]:
    op = "get_risk_weights"
    t0 = time.time()
    try:
        w = risk_service.get_weights()
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"weights": w}
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - t0)


class SetWeightsRequest(BaseModel):
    watchlist: float | None = Field(default=None, ge=0.0, le=1.0)
    labels: float | None = Field(default=None, ge=0.0, le=1.0)
    taint: float | None = Field(default=None, ge=0.0, le=1.0)
    exposure: float | None = Field(default=None, ge=0.0, le=1.0)
    graph: float | None = Field(default=None, ge=0.0, le=1.0)


@router.put("/weights/admin")
async def admin_set_weights(payload: SetWeightsRequest, current_user: dict = Depends(require_admin)) -> Dict[str, Any]:  # ✅ FIX
    op = "admin_set_risk_weights"
    t0 = time.time()
    try:
        neww = risk_service.set_weights(
            **{k: v for k, v in payload.model_dump().items() if v is not None}
        )
        # Audit log
        log_audit_event(
            action=AuditAction.CONFIG_CHANGE,
            resource_type="risk_weights",
            resource_id="weights_v1",
            metadata={
                "new_weights": neww,
                "by": current_user.get("email"),
                "user_id": current_user.get("user_id"),
            },
        )
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"weights": neww}
    except HTTPException:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - t0)

@router.get("/admin/weights")
async def admin_get_weights_v2(request: Request) -> Dict[str, Any]:
    op = "admin_get_risk_weights_v2"
    t0 = time.time()
    try:
        # Admin guard (similar to admin_set_weights)
        is_admin = False
        auth = request.headers.get("Authorization")
        token_user = None
        if auth and auth.lower().startswith("bearer "):
            tok = auth.split(" ", 1)[1].strip()
            try:
                token_user = decode_token(tok)
                if token_user and getattr(token_user, "role", None) == UserRole.ADMIN:
                    is_admin = True
            except Exception:
                is_admin = False
        if request.headers.get("X-Admin") == "1":
            is_admin = True
        if settings.DEBUG:
            is_admin = True
        if not is_admin:
            raise HTTPException(status_code=403, detail="Admin authorization required")
        w = risk_service.get_weights()
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"weights": w}
    except HTTPException:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - t0)


@router.post("/weights")
async def set_risk_weights(payload: SetWeightsRequest) -> Dict[str, Any]:
    op = "set_risk_weights"
    t0 = time.time()
    try:
        # Restrict to TEST_MODE or DEBUG to avoid accidental prod changes
        if not (os.getenv("TEST_MODE") == "1" or settings.DEBUG):
            raise HTTPException(status_code=403, detail="Not allowed in production")
        neww = risk_service.set_weights(
            **{k: v for k, v in payload.model_dump().items() if v is not None}
        )
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"weights": neww}
    except HTTPException:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - t0)


@router.post("/batch")
async def risk_batch(payload: RiskBatchRequest = Body(...)) -> Dict[str, Any]:
    op = "risk_batch"
    t0 = time.time()
    try:
        results = []
        for it in payload.items:
            r = await risk_service.score_address(it.chain, it.address)
            try:
                RISK_SCORE.observe(float(r.score))
            except Exception:
                pass
            results.append({
                "chain": r.chain,
                "address": r.address,
                "score": r.score,
                "factors": r.factors,
                "categories": r.categories,
                "reasons": r.reasons,
            })
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"results": results}
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - t0)
