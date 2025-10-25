from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from app.intel.threat_intel_v2 import (
    threat_intel_v2,
    NormalizedIntelItem,
    IntelNormalizerPlugin,
    TLPLevel,
    IntelConfidence
)

router = APIRouter()


class NormalizeIntelRequest(BaseModel):
    raw_data: Dict[str, Any] = Field(..., description="Raw intelligence data")
    source_type: str = Field(..., description="Source type (chainalysis, trm, community, etc.)")


class ShareIntelRequest(BaseModel):
    intel_id: str = Field(..., description="Intelligence item ID")
    target_org: str = Field(..., description="Target organization ID")


from app.auth.dependencies import require_plan


@router.post("/normalize", tags=["Threat Intel v2"])
async def normalize_intelligence(req: NormalizeIntelRequest, current_user: dict = Depends(require_plan("pro"))):
    """Normalize intelligence data using appropriate plugin"""
    try:
        normalized = await threat_intel_v2.normalize_intel(req.raw_data, req.source_type)
        if not normalized:
            raise HTTPException(status_code=400, detail="Normalization failed")

        return {
            "normalized_item": {
                "intel_id": normalized.intel_id,
                "address": normalized.address,
                "chain": normalized.chain,
                "category": normalized.category,
                "risk_score": normalized.risk_score,
                "confidence": normalized.confidence.value,
                "tlp_level": normalized.tlp_level.value,
                "source": normalized.source,
                "normalized_data": normalized.normalized_data,
                "created_at": normalized.created_at.isoformat(),
                "expires_at": normalized.expires_at.isoformat() if normalized.expires_at else None,
                "tags": list(normalized.tags)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Normalization failed: {str(e)}")


@router.get("/item/{address}/{chain}", tags=["Threat Intel v2"])
async def get_intel_item(address: str, chain: str, current_user: dict = Depends(require_plan("pro"))):
    """Retrieve intelligence for an address"""
    try:
        item = await threat_intel_v2.get_intel_item(address, chain)
        if not item:
            raise HTTPException(status_code=404, detail="Intelligence item not found")

        return {
            "item": {
                "intel_id": item.intel_id,
                "address": item.address,
                "chain": item.chain,
                "category": item.category,
                "risk_score": item.risk_score,
                "confidence": item.confidence.value,
                "tlp_level": item.tlp_level.value,
                "source": item.source,
                "normalized_data": item.normalized_data,
                "created_at": item.created_at.isoformat(),
                "expires_at": item.expires_at.isoformat() if item.expires_at else None,
                "tags": list(item.tags)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.post("/deconflict/{address}/{chain}", tags=["Threat Intel v2"])
async def deconflict_intelligence(
    address: str,
    chain: str,
    intel_items: List[Dict[str, Any]] = None
    ,
    current_user: dict = Depends(require_plan("business"))
):
    """Deconflict intelligence with sanctions and cross-source validation"""
    try:
        # For demo, create sample intel items if none provided
        if not intel_items:
            intel_items = [
                {
                    "intel_id": "sample_1",
                    "address": address,
                    "chain": chain,
                    "category": "mixer",
                    "risk_score": 0.8,
                    "confidence": "high",
                    "tlp_level": "green",
                    "source": "chainalysis",
                    "raw_data": {},
                    "normalized_data": {"entity": "Tornado Cash"},
                    "created_at": "2025-01-01T00:00:00",
                    "tags": ["mixer", "privacy"]
                }
            ]

        # Convert to NormalizedIntelItem objects
        normalized_items = []
        for item_data in intel_items:
            item = NormalizedIntelItem(
                intel_id=item_data["intel_id"],
                address=item_data["address"],
                chain=item_data["chain"],
                category=item_data["category"],
                risk_score=item_data["risk_score"],
                confidence=IntelConfidence(item_data["confidence"]),
                tlp_level=TLPLevel(item_data["tlp_level"]),
                source=item_data["source"],
                raw_data=item_data.get("raw_data", {}),
                normalized_data=item_data.get("normalized_data", {}),
                created_at=datetime.fromisoformat(item_data["created_at"]) if isinstance(item_data["created_at"], str) else item_data["created_at"],
                tags=set(item_data.get("tags", []))
            )
            normalized_items.append(item)

        result = await threat_intel_v2.deconflict_with_sanctions(address, chain, normalized_items)
        return {"deconflicted_intelligence": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deconfliction failed: {str(e)}")


@router.post("/share", tags=["Threat Intel v2"])
async def share_intelligence(req: ShareIntelRequest, current_user: dict = Depends(require_plan("enterprise"))):
    """Share intelligence with another organization (TLP compliant)"""
    try:
        # Get the intel item first
        # For demo, create a sample item
        sample_item = NormalizedIntelItem(
            intel_id=req.intel_id,
            address="0x123...",
            chain="ethereum",
            category="sample",
            risk_score=0.5,
            confidence=IntelConfidence.MEDIUM,
            tlp_level=TLPLevel.GREEN,
            source="demo",
            raw_data={},
            normalized_data={},
            created_at=datetime.now(),
            tags=set()
        )

        success = await threat_intel_v2.share_intelligence(sample_item, req.target_org)
        return {"shared": success, "intel_id": req.intel_id, "target_org": req.target_org}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sharing failed: {str(e)}")


@router.get("/normalizers", tags=["Threat Intel v2"])
async def list_normalizers(current_user: dict = Depends(require_plan("community"))):
    """List all registered normalizer plugins"""
    try:
        normalizers = threat_intel_v2.list_normalizers()
        return {"normalizers": normalizers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Listing failed: {str(e)}")


@router.post("/cleanup", tags=["Threat Intel v2"])
async def cleanup_expired_intel(current_user: dict = Depends(require_plan("enterprise"))):
    """Clean up expired intelligence items"""
    try:
        await threat_intel_v2.cleanup_expired_intel()
        return {"status": "Cleanup completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/stats", tags=["Threat Intel v2"])
async def get_threat_intel_stats(current_user: dict = Depends(require_plan("pro"))):
    """Get Threat Intel v2 statistics"""
    try:
        stats = {
            "normalizers_registered": len(threat_intel_v2.normalizers),
            "tlp_levels_supported": [level.value for level in TLPLevel],
            "confidence_levels_supported": [level.value for level in IntelConfidence],
            "cache_enabled": True,
            "sharing_enabled": True,
            "deconfliction_enabled": True
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.post("/test-normalizer", tags=["Threat Intel v2"])
async def test_normalizer(
    source_type: str = Query(..., description="Normalizer to test"),
    test_data: Dict[str, Any] = None
    ,
    current_user: dict = Depends(require_plan("pro"))
):
    """Test a normalizer plugin with sample data"""
    try:
        if not test_data:
            # Provide sample data based on source type
            if source_type == "chainalysis":
                test_data = {
                    "address": "0x1234567890123456789012345678901234567890",
                    "chain": "ethereum",
                    "category": "mixer",
                    "risk_score": 0.9,
                    "entity": "Tornado Cash",
                    "tags": ["privacy", "mixer"]
                }
            elif source_type == "trm":
                test_data = {
                    "address": "bc1q1234567890123456789012345678901234567890",
                    "chain": "bitcoin",
                    "category": "ransomware",
                    "risk_level": "High"
                }
            elif source_type == "community":
                test_data = {
                    "address": "0x9876543210987654321098765432109876543210",
                    "category": "scam",
                    "reporter": "community_user",
                    "description": "Reported scam address"
                }
            else:
                raise HTTPException(status_code=400, detail="Unknown source type")

        normalized = await threat_intel_v2.normalize_intel(test_data, source_type)
        if not normalized:
            return {"test_result": "normalization_failed", "test_data": test_data}

        return {
            "test_result": "success",
            "normalized_item": {
                "intel_id": normalized.intel_id,
                "address": normalized.address,
                "chain": normalized.chain,
                "category": normalized.category,
                "risk_score": normalized.risk_score,
                "confidence": normalized.confidence.value,
                "tlp_level": normalized.tlp_level.value,
                "source": normalized.source,
                "normalized_data": normalized.normalized_data,
                "tags": list(normalized.tags)
            },
            "test_data": test_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
