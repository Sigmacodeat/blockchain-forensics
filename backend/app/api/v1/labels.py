"""
Labels API backed by Postgres repository
"""
from fastapi import APIRouter, Query, Body, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel, field_validator, model_validator

from app.repos.labels_repo import add_label as repo_add_label, get_labels as repo_get_labels
from app.observability.metrics import LABEL_REQUESTS, LABEL_LATENCY
import time
from app.enrichment.labels_service import labels_service
from app.auth.jwt import decode_token
from app.auth.models import UserRole
from app.auth.dependencies import require_admin
from app.ingest.label_feeds_aggregator import aggregate_label_feeds

router = APIRouter()

class LabelCreate(BaseModel):
    chain: str
    address: str
    label: str
    category: str = "generic"

    @field_validator('chain')
    @classmethod
    def validate_chain(cls, v: str) -> str:
        allowed = {"ethereum", "bitcoin", "solana"}
        vl = (v or "").lower()
        if vl not in allowed:
            raise ValueError(f"unsupported chain: {v}")
        return vl

    @field_validator('address')
    @classmethod
    def normalize_address(cls, v: str) -> str:
        return (v or "").strip().lower()

    @model_validator(mode="after")
    def validate_address_by_chain(self):
        import re
        c = (self.chain or "").lower()
        addr = (self.address or "").strip()
        ok = True
        if c == "ethereum":
            # 0x + 40 hex chars
            ok = bool(re.fullmatch(r"0x[0-9a-f]{40}", addr))
        elif c == "bitcoin":
            # Legacy/Base58 (25-34) or bech32 bc1 (11-71 payload)
            ok = bool(re.fullmatch(r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}", addr)) or bool(
                re.fullmatch(r"bc1[ac-hj-np-z02-9]{11,71}", addr)
            )
        elif c == "solana":
            # Base58-like (exclude 0,O,I,l) length 32-44
            ok = bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", addr))
        if not ok:
            raise ValueError(f"invalid {c} address format")
        return self

@router.get("/", summary="Lookup labels by chain/address")
async def get_labels(chain: str = Query(...), address: str = Query(...)) -> Dict[str, Any]:
    op = "get"
    start = time.time()
    try:
        # Basic validation to prevent reflected XSS and invalid inputs
        c = (chain or "").lower().strip()
        a = (address or "").strip()
        allowed = {"ethereum", "bitcoin", "solana"}
        if c not in allowed:
            raise HTTPException(status_code=400, detail="unsupported chain")
        import re
        ok = True
        if c == "ethereum":
            ok = bool(re.fullmatch(r"0x[0-9a-fA-F]{40}", a))
        elif c == "bitcoin":
            ok = bool(re.fullmatch(r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}", a)) or bool(
                re.fullmatch(r"bc1[ac-hj-np-z02-9]{11,71}", a)
            )
        elif c == "solana":
            ok = bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", a))
        if not ok:
            raise HTTPException(status_code=400, detail="invalid address format")
        # Normalized values
        labels = await repo_get_labels(c, a.lower())
        LABEL_REQUESTS.labels(op=op, status="ok").inc()
        # Echo back normalized, not raw inputs (avoid reflecting scripts)
        return {"chain": c, "address": a.lower(), "labels": labels}
    except Exception as e:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        LABEL_LATENCY.labels(op=op).observe(time.time() - start)


@router.post("/admin/aggregate-feeds", summary="Aggregate external label feeds (admin)")
async def aggregate_external_label_feeds(sources: List[str] | None = Body(default=None), current_user: dict = Depends(require_admin)) -> Dict[str, Any]:
    op = "feeds_aggregate"
    start = time.time()
    try:
        res = await aggregate_label_feeds(sources)
        LABEL_REQUESTS.labels(op=op, status="ok").inc()
        return res
    except HTTPException:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        LABEL_LATENCY.labels(op=op).observe(time.time() - start)


def _is_admin(request_headers: Dict[str, str]) -> bool:
    auth = request_headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        tok = auth.split(" ", 1)[1].strip()
        user = decode_token(tok)
        if user and getattr(user, "role", None) == UserRole.ADMIN:
            return True
    if request_headers.get("X-Admin") == "1":
        return True
    return False


@router.post("/admin/sanctions/refresh", summary="Refresh OFAC sanctions list (admin)")
async def refresh_sanctions(force: bool = Query(False), current_user: dict = Depends(require_admin)) -> Dict[str, Any]:  # ✅ FIX
    op = "sanctions_refresh"
    start = time.time()
    try:
        await labels_service.update_sanctions_list(force=bool(force))
        LABEL_REQUESTS.labels(op=op, status="ok").inc()
        return {"refreshed": True, "forced": bool(force)}
    except HTTPException:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        LABEL_LATENCY.labels(op=op).observe(time.time() - start)


class InvalidateRequest(BaseModel):
    address: str


@router.post("/admin/cache/invalidate", summary="Invalidate labels cache for an address (admin)")
async def invalidate_cache(payload: InvalidateRequest, current_user: dict = Depends(require_admin)) -> Dict[str, Any]:  # ✅ FIX
    op = "cache_invalidate"
    start = time.time()
    try:
        await labels_service.invalidate_cache(payload.address)
        LABEL_REQUESTS.labels(op=op, status="ok").inc()
        return {"invalidated": payload.address.lower()}
    except HTTPException:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        LABEL_LATENCY.labels(op=op).observe(time.time() - start)


@router.get("/detailed", summary="Get detailed labels (with source/confidence)")
async def get_labels_detailed(
    chain: str = Query(...),
    address: str = Query(...),
) -> Dict[str, Any]:
    op = "get_detailed"
    start = time.time()
    try:
        # chain currently not used by service; kept for API symmetry/validation
        det = await labels_service.get_labels_detailed(address)
        LABEL_REQUESTS.labels(op=op, status="ok").inc()
        return {"chain": chain, "address": address, "labels": det}
    except Exception as e:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        LABEL_LATENCY.labels(op=op).observe(time.time() - start)


class BulkRequest(BaseModel):
    addresses: List[str]


@router.post("/bulk", summary="Bulk label lookup")
async def bulk_labels(
    chain: str = Query(...),
    payload: BulkRequest = Body(...),
) -> Dict[str, Any]:
    op = "bulk"
    start = time.time()
    try:
        res = await labels_service.bulk_get_labels(payload.addresses)
        LABEL_REQUESTS.labels(op=op, status="ok").inc()
        return {"chain": chain, "results": res}
    except Exception as e:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        LABEL_LATENCY.labels(op=op).observe(time.time() - start)


@router.post("/", summary="Add a label entry")
async def add_label(
    payload: LabelCreate = Body(...)
) -> Dict[str, Any]:
    op = "add"
    start = time.time()
    try:
        entry = await repo_add_label(
            payload.chain,
            payload.address,
            payload.label,
            payload.category,
        )
        LABEL_REQUESTS.labels(op=op, status="ok").inc()
        return {"created": entry}
    except Exception as e:
        LABEL_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        LABEL_LATENCY.labels(op=op).observe(time.time() - start)
