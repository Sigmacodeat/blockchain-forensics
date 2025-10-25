"""
Intelligence Network API Endpoints

TRM Beacon-style intelligence sharing network for coordinated threat response.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from app.services.intelligence_sharing_service import (
    intelligence_sharing_service,
    FlagReason,
    InvestigatorTier,
    FlagStatus,
    AlertAction
)
from app.auth.dependencies import get_current_user_strict, require_plan
from app.models.audit_log import log_audit_event, AuditAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence-network", tags=["Intelligence Network"])


# Request/Response Models

class InvestigatorRegistration(BaseModel):
    org_name: str = Field(..., description="Organization name")
    tier: InvestigatorTier = Field(..., description="Trust tier")
    verification_docs: Optional[dict] = Field(None, description="Verification documents")
    contact_info: Optional[dict] = Field(None, description="Contact information")


class AddressFlagRequest(BaseModel):
    address: str = Field(..., description="Blockchain address to flag")
    chain: str = Field(..., description="Chain ID (ethereum, bitcoin, etc.)")
    reason: FlagReason = Field(..., description="Reason for flagging")
    incident_id: Optional[str] = Field(None, description="Related incident/case ID")
    amount_usd: Optional[float] = Field(None, ge=0, description="Estimated amount in USD")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed description")
    evidence: Optional[List[dict]] = Field(default_factory=list, description="Supporting evidence")
    related_addresses: Optional[List[str]] = Field(default_factory=list, description="Related addresses")
    auto_trace: bool = Field(True, description="Automatically trace funds")


class FlagConfirmation(BaseModel):
    additional_evidence: Optional[List[dict]] = Field(default_factory=list, description="Additional evidence")


class NetworkMemberRegistration(BaseModel):
    org_name: str = Field(..., description="Organization name")
    member_type: str = Field(..., description="exchange, defi, stablecoin_issuer, custodian")
    alert_webhook: Optional[str] = Field(None, description="Webhook URL for alerts")
    auto_freeze_enabled: bool = Field(False, description="Enable automatic freezing")


class AddressCheckRequest(BaseModel):
    address: str = Field(..., description="Address to check")
    chain: str = Field(..., description="Chain ID")
    check_related: bool = Field(True, description="Also check related addresses")


# Endpoints

@router.post("/investigators/register")
async def register_investigator(
    request: InvestigatorRegistration,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Register as a verified investigator in the intelligence network.
    
    **Requires:** Plus+ plan
    
    **Trust Tiers:**
    - `verified_law_enforcement`: Highest trust (government agencies)
    - `verified_exchange`: Trusted exchanges
    - `verified_security_firm`: Security firms & forensics companies
    - `verified_analyst`: Individual verified analysts
    - `community_trusted`: Community members (requires validation)
    
    **Returns:**
    - Investigator profile with trust score
    """
    await require_plan(current_user, "plus")
    
    try:
        investigator_id = f"inv-{current_user['user_id']}"
        
        investigator = await intelligence_sharing_service.register_investigator(
            investigator_id=investigator_id,
            org_name=request.org_name,
            tier=request.tier,
            verification_docs=request.verification_docs,
            contact_info=request.contact_info
        )
        
        await log_audit_event(
            user_id=current_user["user_id"],
            action=AuditAction.CREATE,
            resource_type="investigator",
            resource_id=investigator_id,
            details={"org_name": request.org_name, "tier": request.tier.value}
        )
        
        return investigator
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to register investigator: {e}")
        raise HTTPException(status_code=500, detail="Failed to register investigator")


@router.post("/flags")
async def flag_address(
    request: AddressFlagRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Flag an address as illicit in the intelligence network.
    
    **Requires:** Plus+ plan
    
    **Features:**
    - Auto-tracing of flagged funds
    - Real-time alerts to network members
    - Multi-source validation
    - Evidence attachment
    
    **Returns:**
    - Flag record with confidence score
    """
    await require_plan(current_user, "plus")
    
    try:
        investigator_id = f"inv-{current_user['user_id']}"
        
        flag = await intelligence_sharing_service.flag_address(
            address=request.address,
            chain=request.chain,
            reason=request.reason,
            investigator_id=investigator_id,
            incident_id=request.incident_id,
            amount_usd=request.amount_usd,
            description=request.description,
            evidence=request.evidence,
            related_addresses=request.related_addresses,
            auto_trace=request.auto_trace
        )
        
        await log_audit_event(
            user_id=current_user["user_id"],
            action=AuditAction.CREATE,
            resource_type="intelligence_flag",
            resource_id=flag["flag_id"],
            details={
                "address": request.address,
                "chain": request.chain,
                "reason": request.reason.value
            }
        )
        
        return flag
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to flag address: {e}")
        raise HTTPException(status_code=500, detail="Failed to flag address")


@router.post("/flags/{flag_id}/confirm")
async def confirm_flag(
    flag_id: str,
    request: FlagConfirmation,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Confirm an existing flag (multi-source validation).
    
    **Requires:** Plus+ plan
    
    **Features:**
    - Increases confidence score
    - Auto-confirms with 3+ sources
    - Updates network-wide risk assessment
    
    **Returns:**
    - Updated flag with new confidence score
    """
    await require_plan(current_user, "plus")
    
    try:
        investigator_id = f"inv-{current_user['user_id']}"
        
        flag = await intelligence_sharing_service.confirm_flag(
            flag_id=flag_id,
            investigator_id=investigator_id,
            additional_evidence=request.additional_evidence
        )
        
        await log_audit_event(
            user_id=current_user["user_id"],
            action=AuditAction.UPDATE,
            resource_type="intelligence_flag",
            resource_id=flag_id,
            details={"action": "confirm"}
        )
        
        return flag
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to confirm flag: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm flag")


@router.post("/check")
async def check_address(
    request: AddressCheckRequest,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Check if address is flagged in the intelligence network.
    
    **Requires:** Pro+ plan
    
    **Features:**
    - Checks direct flags
    - Checks related address flags
    - Calculates aggregate risk score
    - Recommends action (freeze/review/monitor/allow)
    
    **Returns:**
    - Risk assessment with recommended action
    """
    await require_plan(current_user, "pro")
    
    try:
        result = await intelligence_sharing_service.check_address_against_network(
            address=request.address,
            chain=request.chain,
            check_related=request.check_related
        )
        
        # Log high-risk checks
        if result["risk_score"] >= 0.7:
            await log_audit_event(
                user_id=current_user["user_id"],
                action=AuditAction.READ,
                resource_type="intelligence_check",
                resource_id=request.address,
                details={
                    "risk_score": result["risk_score"],
                    "is_flagged": result["is_flagged"]
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to check address: {e}")
        raise HTTPException(status_code=500, detail="Failed to check address")


@router.post("/members/register")
async def register_network_member(
    request: NetworkMemberRegistration,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Register as a network member (exchange, DeFi, stablecoin issuer).
    
    **Requires:** Enterprise plan
    
    **Features:**
    - Receive real-time alerts
    - Auto-freeze flagged funds (optional)
    - Participate in fund recovery
    
    **Returns:**
    - Member profile
    """
    await require_plan(current_user, "enterprise")
    
    try:
        member_id = f"member-{current_user['user_id']}"
        
        member = await intelligence_sharing_service.register_network_member(
            member_id=member_id,
            org_name=request.org_name,
            member_type=request.member_type,
            alert_webhook=request.alert_webhook,
            auto_freeze_enabled=request.auto_freeze_enabled
        )
        
        await log_audit_event(
            user_id=current_user["user_id"],
            action=AuditAction.CREATE,
            resource_type="network_member",
            resource_id=member_id,
            details={"org_name": request.org_name, "type": request.member_type}
        )
        
        return member
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to register member: {e}")
        raise HTTPException(status_code=500, detail="Failed to register member")


@router.get("/flags")
async def list_flags(
    status: Optional[FlagStatus] = Query(None, description="Filter by status"),
    reason: Optional[FlagReason] = Query(None, description="Filter by reason"),
    chain: Optional[str] = Query(None, description="Filter by chain"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user_strict)
):
    """
    List flags in the intelligence network.
    
    **Requires:** Pro+ plan
    
    **Returns:**
    - List of flags matching filters
    """
    await require_plan(current_user, "pro")
    
    try:
        # Filter flags
        flags = list(intelligence_sharing_service.flags_db.values())
        
        if status:
            flags = [f for f in flags if f["status"] == status.value]
        
        if reason:
            flags = [f for f in flags if f["reason"] == reason.value]
        
        if chain:
            flags = [f for f in flags if f["chain"] == chain]
        
        # Sort by timestamp (newest first)
        flags.sort(key=lambda x: x["flagged_at"], reverse=True)
        
        # Paginate
        total = len(flags)
        flags = flags[offset:offset + limit]
        
        return {
            "flags": flags,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list flags: {e}")
        raise HTTPException(status_code=500, detail="Failed to list flags")


@router.get("/flags/{flag_id}")
async def get_flag(
    flag_id: str,
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Get flag details.
    
    **Requires:** Pro+ plan
    
    **Returns:**
    - Flag record with all details
    """
    await require_plan(current_user, "pro")
    
    try:
        if flag_id not in intelligence_sharing_service.flags_db:
            raise HTTPException(status_code=404, detail="Flag not found")
        
        return intelligence_sharing_service.flags_db[flag_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get flag: {e}")
        raise HTTPException(status_code=500, detail="Failed to get flag")


@router.get("/stats")
async def get_network_stats(
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Get intelligence network statistics.
    
    **Requires:** Pro+ plan
    
    **Returns:**
    - Network statistics including:
      - Total investigators & members
      - Flag counts by status/reason
      - Total amount flagged
      - Network effectiveness score
    """
    await require_plan(current_user, "pro")
    
    try:
        stats = await intelligence_sharing_service.get_network_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get network stats")


@router.get("/my-profile")
async def get_my_investigator_profile(
    current_user: dict = Depends(get_current_user_strict)
):
    """
    Get my investigator profile.
    
    **Requires:** Plus+ plan
    
    **Returns:**
    - Investigator profile with stats
    """
    await require_plan(current_user, "plus")
    
    try:
        investigator_id = f"inv-{current_user['user_id']}"
        
        if investigator_id not in intelligence_sharing_service.investigators:
            raise HTTPException(status_code=404, detail="Not registered as investigator")
        
        return intelligence_sharing_service.investigators[investigator_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get investigator profile")
