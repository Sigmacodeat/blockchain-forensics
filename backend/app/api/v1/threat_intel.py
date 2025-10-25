"""
Threat Intelligence API Endpoints
=================================

API endpoints for threat intelligence, dark web monitoring, and intel sharing.
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel

from app.intel.service import get_threat_intel_service
from app.intel.darkweb import get_darkweb_monitor, get_darkweb_store
from app.intel.sharing import get_intel_network
from app.intel.models import (
    ThreatIntelItem,
    CommunityIntelReport,
    IntelQuery,
    IntelStatistics,
    IntelEnrichmentResult,
    ThreatLevel,
    IntelCategory,
    IntelSource,
    IntelSharingMessage,
    TLPLevel,
    DarkWebIntel
)
from app.auth.dependencies import require_plan

router = APIRouter(prefix="/threat-intel", tags=["Threat Intelligence"])


# Request/Response Models
class EnrichAddressRequest(BaseModel):
    """Request to enrich an address"""
    chain: str
    address: str


class CommunityReportRequest(BaseModel):
    """Request to submit community intelligence"""
    chain: str
    address: str
    category: IntelCategory
    threat_level: ThreatLevel
    title: str
    description: str
    evidence: Optional[dict] = None


class ShareIntelRequest(BaseModel):
    """Request to share intelligence via network"""
    sender_org: str
    intel_item_id: Optional[str] = None  # Or provide full item
    threat_level: ThreatLevel
    category: IntelCategory
    tlp: TLPLevel = TLPLevel.AMBER
    title: str
    description: str
    indicators: dict
    recipient_orgs: Optional[List[str]] = None
    ttl_hours: int = 24


class UpdateFeedsResponse(BaseModel):
    """Response from feed update"""
    feeds_updated: int
    items_fetched: int
    items_stored: int
    timestamp: str


# Endpoints

@router.get("/statistics", response_model=IntelStatistics)
async def get_statistics(
    current_user: dict = Depends(require_plan("community"))
):
    """
    Get threat intelligence statistics.
    
    Available to: Community plan and above
    """
    service = get_threat_intel_service()
    stats = await service.get_statistics()
    return stats


@router.post("/enrich", response_model=IntelEnrichmentResult)
async def enrich_address(
    request: EnrichAddressRequest,
    current_user: dict = Depends(require_plan("pro"))
):
    """
    Enrich an address with threat intelligence.
    
    Available to: Pro plan and above
    
    Returns all threat intelligence associated with the address
    including threat scores, risk factors, and recommended actions.
    """
    service = get_threat_intel_service()
    result = await service.enrich_address(
        chain=request.chain,
        address=request.address
    )
    return result


@router.post("/query", response_model=List[ThreatIntelItem])
async def query_intelligence(
    query: IntelQuery,
    current_user: dict = Depends(require_plan("pro"))
):
    """
    Query threat intelligence with filters.
    
    Available to: Pro plan and above
    """
    service = get_threat_intel_service()
    results = await service.query_intelligence(query)
    return results


@router.post("/community/report", response_model=CommunityIntelReport)
async def submit_community_report(
    report: CommunityReportRequest,
    current_user: dict = Depends(require_plan("community"))
):
    """
    Submit community intelligence report (like Chainalysis Signals).
    
    Available to: Community plan and above
    
    Allows users to report suspicious addresses to the community.
    Reports are subject to verification before becoming active intelligence.
    """
    service = get_threat_intel_service()
    
    result = await service.submit_community_report(
        reporter_id=current_user.get("user_id", "unknown"),
        chain=report.chain,
        address=report.address,
        category=report.category,
        threat_level=report.threat_level,
        title=report.title,
        description=report.description,
        evidence=report.evidence
    )
    return result


@router.get("/community/reports", response_model=List[CommunityIntelReport])
async def get_community_reports(
    status: Optional[str] = Query(None),
    category: Optional[IntelCategory] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    current_user: dict = Depends(require_plan("pro"))
):
    """
    Get community intelligence reports.
    
    Available to: Pro plan and above
    """
    service = get_threat_intel_service()
    
    # Filter reports
    reports = service.community_reports
    
    if status:
        reports = [r for r in reports if r.status == status]
    
    if category:
        reports = [r for r in reports if r.category == category]
    
    # Pagination
    return reports[offset:offset + limit]


@router.post("/feeds/update", response_model=UpdateFeedsResponse)
async def update_feeds(
    current_user: dict = Depends(require_plan("business"))
):
    """
    Manually trigger update of all threat intelligence feeds.
    
    Available to: Business plan and above
    
    Updates:
    - Public threat feeds (CryptoScamDB, ChainAbuse, etc.)
    - Dark web monitoring
    - Community reports
    """
    service = get_threat_intel_service()
    result = await service.update_all_feeds()
    
    return UpdateFeedsResponse(
        feeds_updated=result["feeds_updated"],
        items_fetched=result["items_fetched"],
        items_stored=result["items_stored"],
        timestamp=result["timestamp"]
    )


# Dark Web Monitoring Endpoints

@router.get("/darkweb/scan", response_model=dict)
async def run_darkweb_scan(
    current_user: dict = Depends(require_plan("plus"))
):
    """
    Run a dark web monitoring scan.
    
    Available to: Plus plan and above
    
    Scans dark web marketplaces and forums for cryptocurrency threats.
    """
    monitor = get_darkweb_monitor()
    results = await monitor.run_full_scan()
    return results


@router.get("/darkweb/search", response_model=List[DarkWebIntel])
async def search_darkweb_intel(
    address: Optional[str] = Query(None),
    category: Optional[IntelCategory] = Query(None),
    marketplace: Optional[str] = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    current_user: dict = Depends(require_plan("plus"))
):
    """
    Search dark web intelligence.
    
    Available to: Plus plan and above
    """
    store = get_darkweb_store()
    results = await store.search(
        address=address,
        category=category,
        marketplace=marketplace,
        min_confidence=min_confidence
    )
    return results


@router.get("/darkweb/statistics", response_model=dict)
async def get_darkweb_statistics(
    current_user: dict = Depends(require_plan("plus"))
):
    """
    Get dark web monitoring statistics.
    
    Available to: Plus plan and above
    """
    store = get_darkweb_store()
    stats = await store.get_statistics()
    return stats


# Intel Sharing Network Endpoints

@router.post("/sharing/share", response_model=dict)
async def share_intelligence(
    request: ShareIntelRequest,
    current_user: dict = Depends(require_plan("enterprise"))
):
    """
    Share intelligence via intel sharing network (like TRM Beacon).
    
    Available to: Enterprise plan only
    
    Share threat intelligence with other organizations in the network.
    Can be broadcast to all or sent to specific recipients.
    """
    network = get_intel_network()
    
    message = await network.share_intelligence(
        sender_org=request.sender_org,
        threat_level=request.threat_level,
        category=request.category,
        tlp=request.tlp,
        title=request.title,
        description=request.description,
        indicators=request.indicators,
        recipient_orgs=request.recipient_orgs,
        ttl_hours=request.ttl_hours,
        metadata={}
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded or organization not registered"
        )
    
    return {
        "message_id": message.id,
        "status": "shared",
        "recipients": len(message.recipient_orgs) if message.recipient_orgs else "broadcast",
        "tlp": message.tlp.value,
        "trust_score": message.trust_score,
    }


@router.get("/sharing/messages", response_model=List[IntelSharingMessage])
async def get_shared_intelligence(
    org_id: str = Query(...),
    category: Optional[IntelCategory] = Query(None),
    threat_level: Optional[ThreatLevel] = Query(None),
    include_expired: bool = Query(False),
    current_user: dict = Depends(require_plan("enterprise"))
):
    """
    Get intelligence shared via network.
    
    Available to: Enterprise plan only
    
    Retrieves intelligence messages shared with your organization.
    """
    network = get_intel_network()
    
    messages = await network.get_messages_for_org(
        org_id=org_id,
        category=category,
        threat_level=threat_level,
        include_expired=include_expired
    )
    
    return messages


@router.post("/sharing/verify/{message_id}")
async def verify_shared_intelligence(
    message_id: str,
    is_verified: bool = Query(...),
    verifier_org: str = Query(...),
    notes: Optional[str] = Query(None),
    current_user: dict = Depends(require_plan("enterprise"))
):
    """
    Verify intelligence from another organization.
    
    Available to: Enterprise plan only
    
    Helps build reputation and trust scores in the network.
    """
    network = get_intel_network()
    
    success = await network.verify_intelligence(
        message_id=message_id,
        verifier_org=verifier_org,
        is_verified=is_verified,
        notes=notes
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return {
        "message_id": message_id,
        "verified": is_verified,
        "status": "success"
    }


@router.get("/sharing/network/statistics", response_model=dict)
async def get_network_statistics(
    current_user: dict = Depends(require_plan("enterprise"))
):
    """
    Get intel sharing network statistics.
    
    Available to: Enterprise plan only
    """
    network = get_intel_network()
    stats = network.get_network_statistics()
    return stats


@router.post("/sharing/organization/register")
async def register_organization(
    org_id: str = Query(...),
    name: str = Query(...),
    org_type: str = Query("private"),
    current_user: dict = Depends(require_plan("enterprise"))
):
    """
    Register organization in intel sharing network.
    
    Available to: Enterprise plan only
    """
    network = get_intel_network()
    org = network.register_organization(org_id, name, org_type)
    
    return {
        "org_id": org.org_id,
        "name": org.name,
        "type": org.org_type,
        "trust_score": org.trust_score,
        "status": "registered"
    }
