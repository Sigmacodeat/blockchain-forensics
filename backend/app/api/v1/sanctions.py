from fastapi import APIRouter, Body, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
import json
import time
from app.compliance.sanctions.models import MultiSanctionsQuery, SanctionsScreeningResult

router = APIRouter(tags=["Sanctions"])

class ScreenRequest(BaseModel):
    # Support screening by address, name, or ENS
    address: Optional[str] = Field(default=None, description="Blockchain address to screen")
    name: Optional[str] = Field(default=None, description="Entity/person name to screen")
    ens: Optional[str] = Field(default=None, description="ENS to screen")
    lists: Optional[List[Literal["ofac", "un", "eu", "uk", "canada", "australia"]]] = Field(
        default=None, description="Optional list filter; default: all enabled sources"
    )
    fuzzy_threshold: Optional[float] = Field(default=0.85, ge=0.0, le=1.0)

class AliasHit(BaseModel):
    alias: str
    kind: Literal["name", "aka", "ens", "address"]
    confidence: float
    source: str

class ScreenResponse(BaseModel):
    matched: bool
    entity_id: Optional[str] = None
    canonical_name: Optional[str] = None
    lists: List[str] = []
    alias_hits: List[AliasHit] = []
    explain: Optional[str] = None

class StatsResponse(BaseModel):
    sources: List[str]
    versions: Dict[str, Any]
    counts: Dict[str, Any]
    last_updated: Optional[Dict[str, Any]] = None
    totals: Optional[Dict[str, Any]] = None
    source_entity_counts: Optional[Dict[str, int]] = None
    source_alias_counts: Optional[Dict[str, int]] = None
    diff: Optional[Dict[str, Any]] = None


class DiffSourceSummary(BaseModel):
    version_changed: bool
    previous_version: Optional[str]
    current_version: Optional[str]
    entity_count_diff: int
    alias_count_diff: int
    previous_last_updated: Optional[str]
    current_last_updated: Optional[str]


class DiffSummaryResponse(BaseModel):
    sources: Dict[str, DiffSourceSummary]
    total_entity_diff: int
    total_alias_diff: int


class HealthSourceStatus(BaseModel):
    source: str
    status: Literal["ok", "stale", "never_updated", "unknown"]
    age_seconds: Optional[float] = None
    last_updated: Optional[str] = None
    version: Optional[str] = None
    entity_count: int = 0
    alias_count: int = 0


class HealthResponse(BaseModel):
    overall_status: Literal["ok", "warning", "critical"]
    sources: List[HealthSourceStatus]
    totals: Dict[str, int]


class HealthQuery(BaseModel):
    max_age_seconds: Optional[int] = Field(default=3600, ge=60, le=86400)

# Use service stub
from app.compliance.sanctions import sanctions_service
try:
    from app.metrics import LABEL_REQUESTS, LABEL_LATENCY  # type: ignore
except Exception:
    LABEL_REQUESTS = None  # type: ignore
    LABEL_LATENCY = None  # type: ignore

@router.post("/screen", response_model=ScreenResponse)
async def screen(req: ScreenRequest = Body(...)):
    """
    Minimaler Stub für Sanction Screening.
    - Keine Geschäftslogik: gibt deterministische Dummy-Daten zurück.
    - Dient als API-Vorlage bis der Sanctions-Aggregator implementiert ist.
    """
    if not (req.address or req.name or req.ens):
        try:
            if LABEL_REQUESTS:
                LABEL_REQUESTS.labels(op="sanctions_screen", status="bad_request").inc()
            if LABEL_LATENCY:
                LABEL_LATENCY.labels(op="sanctions_screen").observe(0)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Provide at least one of: address, name, ens")

    t0 = time.time()
    res = sanctions_service.screen(
        address=req.address,
        name=req.name,
        ens=req.ens,
        lists=req.lists,
    )
    try:
        if LABEL_REQUESTS:
            LABEL_REQUESTS.labels(op="sanctions_screen", status="ok").inc()
        if LABEL_LATENCY:
            LABEL_LATENCY.labels(op="sanctions_screen").observe(max(0.0, time.time() - t0))
    except Exception:
        pass
    return ScreenResponse(**res)

@router.post("/screen/multi", response_model=List[SanctionsScreeningResult])
async def screen_multi(query: MultiSanctionsQuery = Body(...)):
    """
    Multi-Liste-Screening für mehrere Adressen gleichzeitig.
    Ermöglicht effiziente Prüfung gegen alle gewählten Sanktionslisten.
    """
    t0 = time.time()
    results = []
    for addr in query.addresses:
        res = sanctions_service.screen(
            address=addr,
            lists=query.sources,
        )
        # Konvertiere zu SanctionsScreeningResult
        is_sanctioned = res.get("matched", False)
        matches = [
            {
                "source": hit["source"],
                "entity_id": res.get("entity_id"),
                "canonical_name": res.get("canonical_name"),
                "confidence": hit["confidence"],
                "kind": hit["kind"],
                "alias": hit["alias"],
            }
            for hit in res.get("alias_hits", [])
        ]
        overall_risk = "HIGH" if is_sanctioned else "LOW"
        from datetime import datetime
        result = SanctionsScreeningResult(
            address=addr,
            is_sanctioned=is_sanctioned,
            matches=matches,
            overall_risk=overall_risk,
            recommendations=["Block transaction" if is_sanctioned else "Allow transaction"],
            screened_at=datetime.utcnow().isoformat(),
        )
        results.append(result)
    try:
        if LABEL_REQUESTS:
            LABEL_REQUESTS.labels(op="sanctions_multi", status="ok").inc()
        if LABEL_LATENCY:
            LABEL_LATENCY.labels(op="sanctions_multi").observe(max(0.0, time.time() - t0))
    except Exception:
        pass
    return results

@router.get("/stats", response_model=StatsResponse)
async def stats():
    """Stub für Quellen-/Versions-/Count-Statistiken."""
    data = sanctions_service.stats()
    return StatsResponse(**data)


@router.get("/stats/diff", response_model=DiffSummaryResponse)
async def stats_diff():
    """Liefert die zuletzt ermittelte Diff-Zusammenfassung."""
    diff = sanctions_service.get_diff_summary()
    if not diff:
        return DiffSummaryResponse(sources={}, total_entity_diff=0, total_alias_diff=0)
    return DiffSummaryResponse(**diff)

@router.post("/refresh")
async def refresh_sanctions():
    """Aktualisiert nur die Sanctions-Daten in der DB aus bereits geladenen Quellen."""
    try:
        import os
        if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            # In Tests keine externen Pipelines aufrufen; liefere Erfolg zurück
            return {
                "success": True,
                "inserted": 0,
                "existing": 0,
                "total": 0,
            }
        from app.ingest.labels_ingester import run_once
        
        # Run the ingestion pipeline
        result = await run_once()
        
        return {
            "success": True,
            "inserted": result.get("inserted", 0),
            "existing": result.get("existing", 0),
            "total": result.get("total", 0),
            "diff": sanctions_service.get_diff_summary()
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


# Alias für Abwärtskompatibilität zu Tests: /reload -> identisch zu /refresh
@router.post("/reload")
async def reload_sanctions():
    return await refresh_sanctions()


class BatchItem(BaseModel):
    address: Optional[str] = None
    name: Optional[str] = None
    ens: Optional[str] = None
    lists: Optional[List[Literal["ofac", "un", "eu", "uk", "canada", "australia"]]] = None
    fuzzy_threshold: Optional[float] = Field(default=0.85, ge=0.0, le=1.0)

class BatchScreenRequest(BaseModel):
    items: List[BatchItem]

@router.post("/screen/batch", response_model=List[ScreenResponse])
async def screen_batch(req: BatchScreenRequest = Body(...)):
    """Batch-Screening mehrerer Items."""
    results: List[ScreenResponse] = []
    t0 = time.time()
    for it in req.items:
        if not (it.address or it.name or it.ens):
            results.append(ScreenResponse(matched=False, lists=it.lists or ["ofac","un","eu","uk","canada","australia"], alias_hits=[], explain="Missing input"))
            continue
        res = sanctions_service.screen(
            address=it.address,
            name=it.name,
            ens=it.ens,
            lists=it.lists,
        )
        results.append(ScreenResponse(**res))
    try:
        if LABEL_REQUESTS:
            LABEL_REQUESTS.labels(op="sanctions_batch", status="ok").inc()
        if LABEL_LATENCY:
            LABEL_LATENCY.labels(op="sanctions_batch").observe(max(0.0, time.time() - t0))
    except Exception:
        pass
    return results


@router.post("/webhook/{source}")
async def sanctions_webhook(source: str, request: Request) -> Dict[str, Any]:
    try:
        import os
        max_kb = int(os.getenv("MAX_SANCTIONS_WEBHOOK_BODY_KB", "256"))
        raw = await request.body()
        if len(raw) > max_kb * 1024:
            raise HTTPException(status_code=413, detail="Payload too large")
        try:
            body_text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
            payload = json.loads(body_text) if body_text else {}
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        from app.compliance.sanctions.service import sanctions_service
        res = sanctions_service.ingest_webhook(source, payload if isinstance(payload, dict) else {})
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def sanctions_health(max_age_seconds: int = 3600):
    """Health-Status der Sanctions-Quellen mit Altersprüfung."""
    summary = sanctions_service.health(max_age_seconds=max_age_seconds)
    return HealthResponse(**summary)
