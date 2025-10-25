from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class VaspType(str, Enum):
    """VASP business types"""
    EXCHANGE = "exchange"
    CUSTODIAL_WALLET = "custodial_wallet"
    PAYMENT_PROCESSOR = "payment_processor"
    ATM_OPERATOR = "atm_operator"
    DEFI_PROTOCOL = "defi_protocol"
    NFT_MARKETPLACE = "nft_marketplace"
    OTC_DESK = "otc_desk"
    BROKER_DEALER = "broker_dealer"
    OTHER = "other"


class VaspRiskLevel(str, Enum):
    """VASP risk classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComplianceStatus(str, Enum):
    """Regulatory compliance status"""
    COMPLIANT = "compliant"
    PENDING_REVIEW = "pending_review"
    NON_COMPLIANT = "non_compliant"
    SANCTIONED = "sanctioned"
    UNKNOWN = "unknown"


class Vasp(BaseModel):
    """Virtual Asset Service Provider profile"""
    id: str
    legal_name: str
    dba_name: Optional[str] = None  # Doing Business As
    vasp_type: VaspType = VaspType.OTHER
    
    # Jurisdictional information
    jurisdiction: Optional[str] = None
    registration_number: Optional[str] = None
    licenses: List[str] = []
    regulatory_authorities: List[str] = []
    
    # Contact information
    website: Optional[HttpUrl] = None
    contact_email: Optional[str] = None
    headquarters_address: Optional[str] = None
    
    # Compliance
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    travel_rule_capable: bool = False
    supported_protocols: List[str] = []  # e.g., ["TRISA", "TRP"]
    
    # Risk assessment
    risk_level: VaspRiskLevel = VaspRiskLevel.UNKNOWN
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # Operational info
    supported_chains: List[str] = []
    daily_volume_usd: Optional[float] = None
    user_count: Optional[int] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    verified: bool = False
    verification_date: Optional[datetime] = None
    
    # Additional data
    metadata: Dict[str, Any] = {}


class VaspProfile(BaseModel):
    """Extended VASP profile with screening results"""
    vasp_id: str
    vasp: Optional[Vasp] = None
    
    # Rating
    rating: Optional[Literal["A+", "A", "B", "C", "D", "F"]] = None
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # Screening results
    sanctions_match: bool = False
    pep_match: bool = False
    adverse_media: bool = False
    
    # Historical data
    last_reviewed_at: Optional[datetime] = None
    last_transaction_at: Optional[datetime] = None
    total_transactions: int = 0
    
    # Red flags
    red_flags: List[str] = []
    warnings: List[str] = []
    
    # Compliance notes
    notes: str = ""


class VaspScreeningResult(BaseModel):
    """VASP screening result"""
    vasp_id: str
    vasp_name: str
    
    # Match results
    sanctions_hit: bool = False
    sanctions_lists: List[str] = []
    
    pep_hit: bool = False
    
    adverse_media_hit: bool = False
    adverse_media_count: int = 0
    
    # Risk assessment
    overall_risk: VaspRiskLevel = VaspRiskLevel.UNKNOWN
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_factors: List[str] = []
    
    # Compliance
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    compliance_issues: List[str] = []
    
    # Recommendations
    recommended_action: Literal["approve", "review", "reject", "monitor"] = "review"
    
    # Metadata
    screened_at: datetime = Field(default_factory=datetime.utcnow)
    screened_by: str = "system"
    
    metadata: Dict[str, Any] = {}
