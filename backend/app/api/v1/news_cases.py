"""
NewsCases API (REST)
- Create/List/Get/Update/Delete slug-basierte NewsCases
- Snapshot-Endpunkt für aktuellen Status
"""
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
import json
import hashlib
import time
from pydantic import BaseModel, Field

from app.services.news_case_service import news_case_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news-cases", tags=["NewsCases"])  # mounted unter /api/v1


class AddressInput(BaseModel):
    chain: str = Field(..., description="Chain ID, z.B. ethereum, bitcoin, solana")
    address: str = Field(..., description="Address string")


class CreateNewsCaseRequest(BaseModel):
    slug: str = Field(..., description="Öffentlicher Slug, z.B. 'binance-hack-2025'")
    name: str = Field(..., description="Anzeigename")
    description: Optional[str] = Field(None, description="Beschreibung")
    addresses: List[AddressInput] = Field(default_factory=list)
    auto_trace: bool = Field(default=False, description="Bei neuen Transaktionen automatisch Trace anstoßen (Best-Effort)")


class UpdateNewsCaseRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    addresses: Optional[List[AddressInput]] = None
    auto_trace: Optional[bool] = Field(default=None, description="Auto-Trace schalten")


_RATE_LIMIT_BUCKET: Dict[str, list[float]] = {}
_RATE_LIMIT_MAX = 10
_RATE_LIMIT_WINDOW = 60.0


def _rate_limit_key(request: Request) -> str:
    client = request.client.host if request.client else "anonymous"
    return f"news_cases:create:{client}"


def _check_rate_limit(key: str, limit: int, window_seconds: float) -> tuple[bool, int, float]:
    now = time.time()
    bucket = _RATE_LIMIT_BUCKET.get(key, [])
    bucket = [ts for ts in bucket if ts > now - window_seconds]
    bucket.append(now)
    _RATE_LIMIT_BUCKET[key] = bucket
    count = len(bucket)
    allowed = count <= limit
    retry_after = max(0.0, window_seconds - (now - bucket[0])) if bucket else window_seconds
    return allowed, count, retry_after


@router.post("", status_code=201)
async def create_news_case(request: Request, payload: CreateNewsCaseRequest) -> Dict[str, Any]:
    key = _rate_limit_key(request)
    allowed, count, retry_after = _check_rate_limit(key, _RATE_LIMIT_MAX, _RATE_LIMIT_WINDOW)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={
                "Retry-After": f"{int(retry_after)}",
                "X-RateLimit-Limit": str(_RATE_LIMIT_MAX),
                "X-RateLimit-Remaining": "0",
            },
        )
    try:
        case = await news_case_service.create(
            slug=payload.slug.strip().lower(),
            name=payload.name,
            addresses=[(a.model_dump() if hasattr(a, 'model_dump') else a.dict()) for a in payload.addresses],
            description=payload.description,
            auto_trace=bool(payload.auto_trace),
        )
        return {"status": "created", "case": case.to_dict()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("create_news_case failed: %s", e)
        raise HTTPException(status_code=500, detail="internal error")


@router.get("")
async def list_news_cases() -> Dict[str, Any]:
    cases = await news_case_service.list()
    return {"cases": [c.to_dict() for c in cases]}


@router.get("/{slug}")
async def get_news_case(slug: str) -> Dict[str, Any]:
    case = await news_case_service.get(slug)
    if not case:
        raise HTTPException(status_code=404, detail="not found")
    return case.to_dict()


@router.put("/{slug}")
async def update_news_case(slug: str, payload: UpdateNewsCaseRequest) -> Dict[str, Any]:
    try:
        case = await news_case_service.update(
            slug,
            name=payload.name,
            description=payload.description,
            addresses=[(a.model_dump() if hasattr(a, 'model_dump') else a.dict()) for a in (payload.addresses or [])] if payload.addresses is not None else None,
            auto_trace=payload.auto_trace,
        )
        return {"status": "updated", "case": case.to_dict()}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error("update_news_case failed: %s", e)
        raise HTTPException(status_code=500, detail="internal error")


@router.delete("/{slug}", status_code=204)
async def delete_news_case(slug: str):
    await news_case_service.delete(slug)
    return {"status": "deleted"}


@router.get("/{slug}/snapshot")
async def get_snapshot(slug: str) -> Dict[str, Any]:
    try:
        snap = await news_case_service.snapshot(slug)
        return snap
    except ValueError:
        raise HTTPException(status_code=404, detail="not found")
    except Exception as e:
        logger.error("snapshot failed: %s", e)
        raise HTTPException(status_code=500, detail="internal error")


@router.get("/{slug}/public")
async def get_public_snapshot(slug: str):
    """Öffentlicher Snapshot-Endpunkt (nur lesen) für Public-Dashboards.
    Liefert Caching-Header (ETag, Cache-Control) für schnelle Public-Views.
    """
    try:
        snap = await news_case_service.snapshot(slug)
        body = json.dumps(snap, separators=(",", ":"))
        etag = 'W/"' + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16] + '"'
        resp = Response(content=body, media_type="application/json")
        resp.headers["ETag"] = etag
        # kurz cachebar, sofort revalidierbar
        resp.headers["Cache-Control"] = "public, max-age=5, must-revalidate"
        return resp
    except ValueError:
        raise HTTPException(status_code=404, detail="not found")
    except Exception as e:
        logger.error("public snapshot failed: %s", e)
        raise HTTPException(status_code=500, detail="internal error")
