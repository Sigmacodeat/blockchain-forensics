from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Query

from app.ingest.label_feeds_aggregator import fetch_sources, normalize_and_dedupe

router = APIRouter(prefix="/intel-beacon", tags=["Intel Beacon"]) 


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _indicator_for_item(it: Dict[str, Any]) -> Dict[str, Any]:
    chain = (it.get("chain") or "").lower()
    address = (it.get("address") or "").lower()
    label = it.get("label") or ""
    cat = it.get("category") or "generic"
    iid = f"indicator--{uuid.uuid4()}"
    pattern = f"[x-crypto-addr:value = '{chain}:{address}']"
    created = _now_iso()
    return {
        "type": "indicator",
        "spec_version": "2.1",
        "id": iid,
        "created": created,
        "modified": created,
        "name": f"{chain}:{address}",
        "description": label or cat,
        "pattern": pattern,
        "pattern_type": "stix",
        "valid_from": created,
        "labels": [label] if label else [cat],
    }


def _bundle(indicators: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "spec_version": "2.1",
        "objects": indicators,
    }


@router.get("/taxii2")
async def taxii_discovery() -> Dict[str, Any]:
    return {
        "title": "Intel Beacon",
        "description": "STIX/TAXII service",
        "contact": "",
        "default": "/api/v1/intel-beacon/taxii2/root",
        "api_roots": ["/api/v1/intel-beacon/taxii2/root"],
    }


@router.get("/taxii2/root")
async def taxii_root() -> Dict[str, Any]:
    return {
        "title": "Intel Beacon Root",
        "versions": ["2.1"],
        "max_content_length": 10_000_000,
    }


@router.get("/taxii2/root/collections")
async def taxii_collections() -> Dict[str, Any]:
    return {
        "collections": [
            {
                "id": "labels-indicators",
                "title": "Labels as STIX Indicators",
                "can_read": True,
                "can_write": False,
            }
        ]
    }


@router.get("/taxii2/root/collections/{collection_id}/objects")
async def taxii_objects(collection_id: str, limit: int = Query(100, ge=1, le=2000)) -> Dict[str, Any]:
    items = await fetch_sources(["rekt", "slowmist", "chainabuse", "etherscan", "defillama"]) 
    deduped, _stats = normalize_and_dedupe(items)
    inds: List[Dict[str, Any]] = []
    for it in deduped[: limit]:
        inds.append(_indicator_for_item(it))
    return _bundle(inds)
