"""
VASP & Travel Rule API
======================

API endpoints for VASP directory and Travel Rule compliance.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models.vasp import (
    VASP,
    VASPType,
    VASPJurisdiction,
    VASPStatus,
    VASPComplianceLevel,
    TravelRuleProtocol,
    TravelRuleMessage,
    TravelRuleStatus,
    OriginatorInfo,
    BeneficiaryInfo,
    VASPScreeningResult,
    VASPQuery,
    VASPStatistics,
)
from app.services.vasp_directory import VASPDirectory
from app.services.travel_rule_engine import TravelRuleEngine
from app.auth.dependencies import require_plan

router = APIRouter(prefix="/vasp", tags=["VASP & Travel Rule"])

# Initialize services (in production, use dependency injection)
vasp_directory = VASPDirectory()
travel_rule_engine = TravelRuleEngine(vasp_directory)


# ============================================================================
# VASP Directory Endpoints
# ============================================================================

@router.get("/directory", response_model=List[VASP])
async def list_vasps(
    name: Optional[str] = None,
    type: Optional[VASPType] = None,
    jurisdiction: Optional[VASPJurisdiction] = None,
    status: Optional[VASPStatus] = None,
    compliance_level: Optional[VASPComplianceLevel] = None,
    blockchain: Optional[str] = None,
    verified_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    _=Depends(require_plan("pro")),
):
    """
    List VASPs in directory with filters
    
    **Plan Required:** Pro+
    
    Returns list of VASPs matching criteria.
    """
    query = VASPQuery(
        name=name,
        type=type,
        jurisdiction=jurisdiction,
        status=status,
        compliance_level=compliance_level,
        blockchain=blockchain,
        verified_only=verified_only,
        skip=skip,
        limit=limit,
    )
    
    return await vasp_directory.search_vasps(query)


@router.get("/directory/{vasp_id}", response_model=VASP)
async def get_vasp(
    vasp_id: str,
    _=Depends(require_plan("pro")),
):
    """
    Get VASP by ID
    
    **Plan Required:** Pro+
    """
    vasp = await vasp_directory.get_vasp(vasp_id)
    if not vasp:
        raise HTTPException(status_code=404, detail="VASP not found")
    return vasp


class AddVASPRequest(BaseModel):
    """Request to add VASP to directory"""
    name: str
    legal_name: Optional[str] = None
    type: VASPType
    jurisdiction: List[VASPJurisdiction]
    website: Optional[str] = None
    email: Optional[str] = None
    lei: Optional[str] = None
    registration_number: Optional[str] = None
    compliance_level: VASPComplianceLevel = VASPComplianceLevel.UNKNOWN
    travel_rule_protocols: List[TravelRuleProtocol] = Field(default_factory=list)
    supported_chains: List[str] = Field(default_factory=list)


@router.post("/directory", response_model=VASP)
async def add_vasp(
    request: AddVASPRequest,
    _=Depends(require_plan("business")),
):
    """
    Add VASP to directory
    
    **Plan Required:** Business+
    """
    vasp = vasp_directory.add_vasp(**request.dict())
    return vasp


class UpdateVASPRequest(BaseModel):
    """Request to update VASP"""
    legal_name: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    status: Optional[VASPStatus] = None
    compliance_level: Optional[VASPComplianceLevel] = None
    travel_rule_protocols: Optional[List[TravelRuleProtocol]] = None
    supported_chains: Optional[List[str]] = None


@router.patch("/directory/{vasp_id}", response_model=VASP)
async def update_vasp(
    vasp_id: str,
    request: UpdateVASPRequest,
    _=Depends(require_plan("business")),
):
    """
    Update VASP data
    
    **Plan Required:** Business+
    """
    updates = {k: v for k, v in request.dict().items() if v is not None}
    vasp = await vasp_directory.update_vasp(vasp_id, **updates)
    
    if not vasp:
        raise HTTPException(status_code=404, detail="VASP not found")
    
    return vasp


class RegisterAddressRequest(BaseModel):
    """Request to register address for VASP"""
    blockchain: str
    address: str


@router.post("/directory/{vasp_id}/addresses")
async def register_address(
    vasp_id: str,
    request: RegisterAddressRequest,
    _=Depends(require_plan("business")),
):
    """
    Register blockchain address for VASP
    
    **Plan Required:** Business+
    """
    success = await vasp_directory.register_address(
        vasp_id,
        request.blockchain,
        request.address,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="VASP not found")
    
    return {"success": True, "message": "Address registered"}


@router.post("/directory/{vasp_id}/verify")
async def verify_vasp(
    vasp_id: str,
    verified_by: str = Query(...),
    _=Depends(require_plan("enterprise")),
):
    """
    Verify VASP
    
    **Plan Required:** Enterprise
    """
    vasp = await vasp_directory.verify_vasp(vasp_id, verified_by)
    
    if not vasp:
        raise HTTPException(status_code=404, detail="VASP not found")
    
    return vasp


@router.get("/statistics", response_model=VASPStatistics)
async def get_vasp_statistics(
    _=Depends(require_plan("pro")),
):
    """
    Get VASP directory statistics
    
    **Plan Required:** Pro+
    """
    stats = vasp_directory.get_statistics()
    
    # Add Travel Rule stats
    tr_stats = travel_rule_engine.get_statistics()
    stats.travel_rule_messages_total = tr_stats["total_messages"]
    stats.travel_rule_messages_24h = tr_stats["messages_24h"]
    
    return stats


# ============================================================================
# VASP Screening Endpoints
# ============================================================================

class ScreenAddressRequest(BaseModel):
    """Request to screen address"""
    address: str
    blockchain: str


@router.post("/screen", response_model=VASPScreeningResult)
async def screen_address(
    request: ScreenAddressRequest,
    _=Depends(require_plan("pro")),
):
    """
    Screen address for VASP association
    
    **Plan Required:** Pro+
    
    Returns whether the address belongs to a known VASP.
    """
    result = await vasp_directory.screen_address(
        request.address,
        request.blockchain,
    )
    return result


# ============================================================================
# Travel Rule Endpoints
# ============================================================================

class EvaluateTransactionRequest(BaseModel):
    """Request to evaluate Travel Rule requirements"""
    from_address: str
    to_address: str
    blockchain: str
    asset: str
    amount: float
    amount_usd: Optional[float] = None


@router.post("/travel-rule/evaluate")
async def evaluate_travel_rule(
    request: EvaluateTransactionRequest,
    _=Depends(require_plan("business")),
):
    """
    Evaluate if transaction requires Travel Rule compliance
    
    **Plan Required:** Business+
    
    Checks:
    - If both parties are VASPs
    - If transaction exceeds USD 1,000 threshold
    - Travel Rule requirements
    """
    result = await travel_rule_engine.evaluate_transaction(
        from_address=request.from_address,
        to_address=request.to_address,
        blockchain=request.blockchain,
        asset=request.asset,
        amount=request.amount,
        amount_usd=request.amount_usd,
    )
    return result


class CreateTravelRuleMessageRequest(BaseModel):
    """Request to create Travel Rule message"""
    originating_vasp_id: str
    beneficiary_vasp_id: str
    transaction_hash: Optional[str] = None
    blockchain: str
    asset: str
    amount: float
    amount_usd: Optional[float] = None
    originator: OriginatorInfo
    beneficiary: BeneficiaryInfo
    protocol: TravelRuleProtocol = TravelRuleProtocol.OPENVASP


@router.post("/travel-rule/messages", response_model=TravelRuleMessage)
async def create_travel_rule_message(
    request: CreateTravelRuleMessageRequest,
    _=Depends(require_plan("business")),
):
    """
    Create Travel Rule message
    
    **Plan Required:** Business+
    
    Creates a FATF Travel Rule compliant message for VASP-to-VASP communication.
    """
    message = await travel_rule_engine.create_message(
        originating_vasp_id=request.originating_vasp_id,
        beneficiary_vasp_id=request.beneficiary_vasp_id,
        transaction_hash=request.transaction_hash,
        blockchain=request.blockchain,
        asset=request.asset,
        amount=request.amount,
        amount_usd=request.amount_usd,
        originator=request.originator,
        beneficiary=request.beneficiary,
        protocol=request.protocol,
    )
    return message


@router.post("/travel-rule/messages/{message_id}/send")
async def send_travel_rule_message(
    message_id: str,
    _=Depends(require_plan("business")),
):
    """
    Send Travel Rule message to beneficiary VASP
    
    **Plan Required:** Business+
    """
    try:
        success = await travel_rule_engine.send_message(message_id)
        return {
            "success": success,
            "message_id": message_id,
            "status": "sent" if success else "failed",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class AcknowledgeMessageRequest(BaseModel):
    """Request to acknowledge message"""
    accept: bool = True


@router.post("/travel-rule/messages/{message_id}/acknowledge")
async def acknowledge_travel_rule_message(
    message_id: str,
    request: AcknowledgeMessageRequest,
    _=Depends(require_plan("business")),
):
    """
    Acknowledge received Travel Rule message
    
    **Plan Required:** Business+
    """
    try:
        success = await travel_rule_engine.acknowledge_message(
            message_id,
            request.accept,
        )
        return {
            "success": success,
            "message_id": message_id,
            "status": "accepted" if request.accept else "rejected",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/travel-rule/messages/{message_id}", response_model=TravelRuleMessage)
async def get_travel_rule_message(
    message_id: str,
    _=Depends(require_plan("business")),
):
    """
    Get Travel Rule message by ID
    
    **Plan Required:** Business+
    """
    message = await travel_rule_engine.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.get("/travel-rule/messages", response_model=List[TravelRuleMessage])
async def list_travel_rule_messages(
    originating_vasp_id: Optional[str] = None,
    beneficiary_vasp_id: Optional[str] = None,
    status: Optional[TravelRuleStatus] = None,
    blockchain: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    _=Depends(require_plan("business")),
):
    """
    List Travel Rule messages with filters
    
    **Plan Required:** Business+
    """
    messages = await travel_rule_engine.list_messages(
        originating_vasp_id=originating_vasp_id,
        beneficiary_vasp_id=beneficiary_vasp_id,
        status=status,
        blockchain=blockchain,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )
    return messages


@router.get("/travel-rule/statistics")
async def get_travel_rule_statistics(
    _=Depends(require_plan("business")),
):
    """
    Get Travel Rule statistics
    
    **Plan Required:** Business+
    """
    return travel_rule_engine.get_statistics()


# ============================================================================
# Import Endpoints
# ============================================================================

@router.post("/import/openvasp")
async def import_from_openvasp(
    _=Depends(require_plan("enterprise")),
):
    """
    Import VASPs from OpenVASP directory
    
    **Plan Required:** Enterprise
    """
    count = await vasp_directory.import_vasps_from_openvasp()
    return {
        "success": True,
        "imported": count,
        "source": "openvasp",
    }


@router.post("/import/trisa")
async def import_from_trisa(
    _=Depends(require_plan("enterprise")),
):
    """
    Import VASPs from TRISA directory
    
    **Plan Required:** Enterprise
    """
    count = await vasp_directory.import_vasps_from_trisa()
    return {
        "success": True,
        "imported": count,
        "source": "trisa",
    }
