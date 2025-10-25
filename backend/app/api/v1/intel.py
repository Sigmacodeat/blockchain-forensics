from fastapi import APIRouter, Body, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from app.intel import intel_service
from app.integrations.feeds import threat_intel_service
from app.services.intel_webhook_verifier import verify_signature
from app.metrics import INTEL_WEBHOOK_INGEST_TOTAL
# Redis client is optional in tests; import defensively
try:
    from app.db.redis_client import redis_client as _redis_client
except Exception:
    _redis_client = None
from app.intel.sharing import get_intel_network
from app.intel.models import ThreatLevel, IntelCategory
import os
import json
import time

router = APIRouter(tags=["Intel"]) 

class IntelEvent(BaseModel):
    type: str = Field(..., description="label|ioc|alert|sighting")
    payload: Dict[str, Any] = Field(default_factory=dict)
    tlp: str = Field(default="AMBER")
    publisher: Optional[str] = None
    signature: Optional[str] = None

class IntelPolicy(BaseModel):
    id: str
    name: str
    rules: List[Dict[str, Any]] = []
    approvers: List[str] = []
    status: str

@router.post("/publish")
async def publish(event: IntelEvent = Body(...)):
    """Stub: Publiziert ein Intel-Event (keine echte Föderation)."""
    return intel_service.publish(event.model_dump())

@router.get("/policies", response_model=List[IntelPolicy])
async def policies():
    """Stub: Gibt aktuelle Policies zurück."""
    return intel_service.policies()


@router.post("/webhooks/{source}")
async def ingest_webhook(source: str, request: Request):
    # Enforce reasonable body size (default 256KB)
    try:
        max_kb = int(os.getenv("MAX_INTEL_WEBHOOK_BODY_KB", "256"))
    except Exception:
        max_kb = 256
    raw_body = await request.body()
    if isinstance(raw_body, (bytes, bytearray)) and len(raw_body) > max_kb * 1024:
        raise HTTPException(status_code=413, detail="Payload too large")

    # Minimal content-type check when provided
    ctype = request.headers.get("content-type", "application/json").lower()
    if "json" not in ctype:
        raise HTTPException(status_code=415, detail="Unsupported Media Type (expected application/json)")
    try:
        body_json = raw_body.decode("utf-8") if isinstance(raw_body, (bytes, bytearray)) else str(raw_body)
        payload = json.loads(body_json) if body_json else {}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    secret = os.getenv(f"INTEL_WEBHOOK_SECRET_{source.upper()}") or os.getenv("INTEL_WEBHOOK_SECRET")
    if not secret:
        if INTEL_WEBHOOK_INGEST_TOTAL:
            INTEL_WEBHOOK_INGEST_TOTAL.labels(source, "no_secret").inc()
        raise HTTPException(status_code=401, detail="Missing webhook secret")

    if not verify_signature(secret, request.headers, body_json):
        if INTEL_WEBHOOK_INGEST_TOTAL:
            INTEL_WEBHOOK_INGEST_TOTAL.labels(source, "invalid_sig").inc()
        raise HTTPException(status_code=401, detail="Invalid signature")

    idem = request.headers.get("Idempotency-Key") or payload.get("delivery_id")
    if idem and _redis_client is not None:
        try:
            prev = await _redis_client.check_idempotency(f"intel:{source}:{idem}", ttl=86400)
        except Exception:
            prev = None
        if prev:
            if INTEL_WEBHOOK_INGEST_TOTAL:
                INTEL_WEBHOOK_INGEST_TOTAL.labels(source, "idempotent_hit").inc()
            return prev

    ingested = threat_intel_service.ingest_inbound_event(source, payload)
    result = {"status": "ok", "source": source, "received_at": ingested["received_at"], "size": len(body_json)}
    if INTEL_WEBHOOK_INGEST_TOTAL is not None:
        INTEL_WEBHOOK_INGEST_TOTAL.labels(source, "ok").inc()

    # Audit hook entfernt (kein audit_trail_service im Einsatz)

    if idem and _redis_client is not None:
        try:
            await _redis_client.store_idempotency_result(f"intel:{source}:{idem}", result, ttl=86400)
        except Exception:
            pass
    return result


@router.get("/webhooks/recent")
async def recent_inbound(limit: int = 100):
    return threat_intel_service.recent_inbound_events(limit=limit)


@router.post("/webhooks/{source}/verify")
async def verify_webhook_signature(source: str, request: Request):
    try:
        max_kb = int(os.getenv("MAX_INTEL_WEBHOOK_BODY_KB", "256"))
    except Exception:
        max_kb = 256
    raw_body = await request.body()
    if isinstance(raw_body, (bytes, bytearray)) and len(raw_body) > max_kb * 1024:
        raise HTTPException(status_code=413, detail="Payload too large")

    ctype = request.headers.get("content-type", "application/json").lower()
    if "json" not in ctype:
        raise HTTPException(status_code=415, detail="Unsupported Media Type (expected application/json)")

    try:
        body_json = raw_body.decode("utf-8") if isinstance(raw_body, (bytes, bytearray)) else str(raw_body)
        _ = json.loads(body_json) if body_json else {}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    secret = os.getenv(f"INTEL_WEBHOOK_SECRET_{source.upper()}") or os.getenv("INTEL_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=401, detail="Missing webhook secret")

    ok = verify_signature(secret, request.headers, body_json)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid signature")

    # No ingest, only verification result
    return {"status": "verified", "source": source}

# ========== ADMIN TRIGGERS ==========

@router.post("/feeds/run-once")
async def run_feeds_once() -> Dict[str, Any]:
    """Manually trigger a single run of public intelligence feeds ingestion."""
    try:
        from app.intel.feeds import run_once as feeds_run_once  # lazy import
    except Exception as imp_err:
        raise HTTPException(status_code=500, detail=f"Feeds module not available: {imp_err}")
    t0 = time.time()
    try:
        res = await feeds_run_once()
        return {"status": "ok", "took": time.time() - t0, "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/labels/run-once")
async def run_labels_ingester_once() -> Dict[str, Any]:
    """Manually trigger a single run of labels ingester (sanctions + exchange seeds)."""
    try:
        from app.ingest.labels_ingester import run_once as labels_run_once  # lazy import
    except Exception as imp_err:
        raise HTTPException(status_code=500, detail=f"Labels ingester not available: {imp_err}")
    t0 = time.time()
    try:
        res = await labels_run_once()
        return {"status": "ok", "took": time.time() - t0, "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== INTELLIGENCE SHARING NETWORK (Beacon-Style) ==========

class IntelSharingShareRequest(BaseModel):
    sender_org: str
    threat_level: str  # low, medium, high, critical
    category: str  # malware, phishing, scam, hack, ransomware, etc.
    title: str
    description: str
    indicators: Dict[str, List[str]]  # e.g., {"addresses": ["0x..."], "domains": ["evil.com"]}
    recipient_orgs: List[str] | None = None  # None = broadcast
    ttl_hours: int = 24
    metadata: Dict[str, Any] | None = None


@router.post("/sharing/share")
async def share_intelligence(payload: IntelSharingShareRequest) -> Dict[str, Any]:
    """Share intelligence with network (Beacon-style)"""
    try:
        network = get_intel_network()
        
        # Convert string to enum (support both names and values)
        try:
            try:
                threat_level = ThreatLevel[payload.threat_level.upper()]
            except KeyError:
                threat_level = ThreatLevel(payload.threat_level.lower())
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid threat level: {payload.threat_level}")

        try:
            try:
                category = IntelCategory[payload.category.upper()]
            except KeyError:
                category = IntelCategory(payload.category.lower())
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid category: {payload.category}")
        
        message = await network.share_intelligence(
            sender_org=payload.sender_org,
            threat_level=threat_level,
            category=category,
            title=payload.title,
            description=payload.description,
            indicators=payload.indicators,
            recipient_orgs=payload.recipient_orgs,
            ttl_hours=payload.ttl_hours,
            metadata=payload.metadata
        )
        
        if not message:
            raise HTTPException(status_code=400, detail="Failed to share intelligence")
        
        return {
            "message_id": message.id,
            "sender_org": message.sender_org,
            "shared_at": message.shared_at.isoformat(),
            "recipients": message.recipient_orgs or "broadcast",
            "trust_score": message.trust_score
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sharing/messages/{org_id}")
async def get_org_messages(
    org_id: str,
    category: str | None = None,
    threat_level: str | None = None,
    include_expired: bool = False
) -> Dict[str, Any]:
    """Get intelligence messages for organization"""
    try:
        network = get_intel_network()
        
        # Convert filters
        category_filter = None
        if category:
            try:
                category_filter = IntelCategory(category.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        threat_filter = None
        if threat_level:
            try:
                threat_filter = ThreatLevel(threat_level.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid threat level: {threat_level}")
        
        messages = await network.get_messages_for_org(
            org_id=org_id,
            category=category_filter,
            threat_level=threat_filter,
            include_expired=include_expired
        )
        
        return {
            "org_id": org_id,
            "messages": [
                {
                    "message_id": msg.id,
                    "sender_org": msg.sender_org,
                    "threat_level": (msg.threat_level if isinstance(msg.threat_level, str) else msg.threat_level.value),
                    "category": (msg.category if isinstance(msg.category, str) else msg.category.value),
                    "title": msg.title,
                    "description": msg.description,
                    "indicators": msg.indicators,
                    "shared_at": msg.shared_at.isoformat(),
                    "expires_at": msg.expires_at.isoformat() if msg.expires_at else None,
                    "trust_score": msg.trust_score,
                    "verified": msg.verified
                }
                for msg in messages
            ],
            "count": len(messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sharing/verify/{message_id}")
async def verify_intelligence(
    message_id: str,
    verifier_org: str,
    is_verified: bool,
    notes: str | None = None
) -> Dict[str, Any]:
    """Verify intelligence from another organization"""
    try:
        network = get_intel_network()
        
        success = await network.verify_intelligence(
            message_id=message_id,
            verifier_org=verifier_org,
            is_verified=is_verified,
            notes=notes
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        
        return {
            "message_id": message_id,
            "verifier_org": verifier_org,
            "is_verified": is_verified,
            "status": "recorded"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sharing/network/statistics")
async def get_network_statistics() -> Dict[str, Any]:
    """Get intelligence sharing network statistics"""
    try:
        network = get_intel_network()
        stats = network.get_network_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sharing/organizations/register")
async def register_organization(
    org_id: str,
    name: str,
    org_type: str = "private"
) -> Dict[str, Any]:
    """Register organization in intelligence network"""
    try:
        network = get_intel_network()
        org = network.register_organization(org_id, name, org_type)
        
        return {
            "org_id": org.org_id,
            "name": org.name,
            "org_type": org.org_type,
            "trust_score": org.trust_score,
            "joined_at": org.joined_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== THREAT INTELLIGENCE STATISTICS ==========

@router.get("/feeds/statistics")
async def get_threat_intel_statistics() -> Dict[str, Any]:
    """Get comprehensive threat intelligence statistics"""
    try:
        from app.intel.feeds import fetch_all_feeds
        
        # Fetch latest feed data
        items = await fetch_all_feeds()
        
        stats = {
            "total_items": len(items),
            "by_source": {},
            "by_chain": {},
            "by_category": {},
            "sources_count": 0
        }
        
        sources = set()
        for item in items:
            source = item.get('source', 'unknown')
            chain = item.get('chain', 'unknown')
            category = item.get('label', 'unknown')
            
            sources.add(source)
            
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            stats["by_chain"][chain] = stats["by_chain"].get(chain, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        stats["sources_count"] = len(sources)
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
