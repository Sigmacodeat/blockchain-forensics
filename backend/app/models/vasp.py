"""
VASP (Virtual Asset Service Provider) Models
=============================================

Models for Travel Rule compliance and VASP directory management.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VASPType(str, Enum):
    """VASP Type Classification"""
    EXCHANGE = "exchange"
    CUSTODIAL_WALLET = "custodial_wallet"
    PAYMENT_PROCESSOR = "payment_processor"
    DEFI_PLATFORM = "defi_platform"
    ATM_OPERATOR = "atm_operator"
    OTC_DESK = "otc_desk"
    BROKER = "broker"
    OTHER = "other"


class VASPJurisdiction(str, Enum):
    """Regulatory Jurisdictions"""
    US = "US"
    EU = "EU"
    UK = "UK"
    SINGAPORE = "SG"
    SWITZERLAND = "CH"
    JAPAN = "JP"
    SOUTH_KOREA = "KR"
    CANADA = "CA"
    AUSTRALIA = "AU"
    HONG_KONG = "HK"
    UAE = "AE"
    OTHER = "OTHER"


class VASPStatus(str, Enum):
    """VASP Status in Directory"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    BLACKLISTED = "blacklisted"


class VASPComplianceLevel(str, Enum):
    """Compliance Rating"""
    FULL = "full"  # Full Travel Rule compliance
    PARTIAL = "partial"  # Partial compliance
    MINIMAL = "minimal"  # Minimal compliance
    UNKNOWN = "unknown"  # Unknown status
    NON_COMPLIANT = "non_compliant"  # Non-compliant


class TravelRuleProtocol(str, Enum):
    """Travel Rule Protocol Standards"""
    OPENVASP = "openvasp"
    TRISA = "trisa"
    TRUST = "trust"
    SYGNA = "sygna"
    NOTABENE = "notabene"
    SHYFT = "shyft"
    PROPRIETARY = "proprietary"


class VASP(BaseModel):
    """
    VASP Directory Entry
    
    Represents a Virtual Asset Service Provider in our directory.
    Based on Chainalysis' 1,500+ VASP directory.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    legal_name: Optional[str] = None
    type: VASPType
    jurisdiction: List[VASPJurisdiction]
    
    # Identification
    lei: Optional[str] = None  # Legal Entity Identifier
    registration_number: Optional[str] = None
    license_number: Optional[str] = None
    
    # Contact & Technical
    website: Optional[str] = None
    email: Optional[str] = None
    api_endpoint: Optional[str] = None
    
    # Travel Rule
    travel_rule_protocols: List[TravelRuleProtocol] = Field(default_factory=list)
    vasp_code: Optional[str] = None  # IVMS101 VASP Code
    openvasp_id: Optional[str] = None
    trisa_endpoint: Optional[str] = None
    
    # Compliance
    status: VASPStatus = VASPStatus.PENDING_VERIFICATION
    compliance_level: VASPComplianceLevel = VASPComplianceLevel.UNKNOWN
    kyc_required: bool = True
    aml_program: bool = False
    sanctions_screening: bool = False
    
    # Supported Chains & Assets
    supported_chains: List[str] = Field(default_factory=list)
    supported_assets: List[str] = Field(default_factory=list)
    
    # Known Addresses
    known_addresses: Dict[str, List[str]] = Field(default_factory=dict)  # chain -> addresses
    
    # Risk Assessment
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_factors: List[str] = Field(default_factory=list)
    
    # Metadata
    verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional Data
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TravelRuleTransactionType(str, Enum):
    """Travel Rule Transaction Types"""
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"


class TravelRuleStatus(str, Enum):
    """Travel Rule Message Status"""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"
    EXPIRED = "expired"


class OriginatorInfo(BaseModel):
    """
    Originator Information (IVMS101)
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Natural Person
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Legal Person
    legal_name: Optional[str] = None
    
    # Common
    address: Optional[str] = None
    city: Optional[str] = None
    country: str
    postal_code: Optional[str] = None
    
    # Identification
    id_type: Optional[str] = None  # passport, national_id, etc.
    id_number: Optional[str] = None
    id_country: Optional[str] = None
    
    # Account
    account_number: Optional[str] = None
    
    # Blockchain
    wallet_address: str


class BeneficiaryInfo(BaseModel):
    """
    Beneficiary Information (IVMS101)
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Natural Person
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Legal Person
    legal_name: Optional[str] = None
    
    # Common
    address: Optional[str] = None
    city: Optional[str] = None
    country: str
    postal_code: Optional[str] = None
    
    # Account
    account_number: Optional[str] = None
    
    # Blockchain
    wallet_address: str


class TravelRuleMessage(BaseModel):
    """
    Travel Rule Message
    
    FATF Travel Rule compliant message for VASP-to-VASP communication.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    
    # VASPs
    originating_vasp_id: str
    originating_vasp_name: str
    beneficiary_vasp_id: str
    beneficiary_vasp_name: str
    
    # Transaction
    transaction_type: TravelRuleTransactionType
    transaction_hash: Optional[str] = None
    blockchain: str
    asset: str
    amount: float
    amount_usd: Optional[float] = None
    
    # Parties
    originator: OriginatorInfo
    beneficiary: BeneficiaryInfo
    
    # Protocol
    protocol: TravelRuleProtocol
    protocol_version: str = "1.0"
    
    # Status
    status: TravelRuleStatus = TravelRuleStatus.PENDING
    
    # Compliance
    screening_result: Optional[str] = None
    sanctions_hit: bool = False
    pep_hit: bool = False
    risk_score: Optional[float] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Additional Data
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VASPScreeningResult(BaseModel):
    """
    Result of VASP Screening
    """
    model_config = ConfigDict(from_attributes=True)
    
    vasp_id: str
    vasp_name: str
    address: str
    blockchain: str
    
    # Screening Results
    is_vasp: bool
    confidence: float = Field(ge=0, le=1)
    
    # Compliance
    travel_rule_required: bool = False
    threshold_exceeded: bool = False  # USD threshold for Travel Rule
    
    # Risk
    risk_level: str  # low, medium, high, critical
    risk_factors: List[str] = Field(default_factory=list)
    
    # Matched Data
    matched_addresses: List[str] = Field(default_factory=list)
    vasp_type: Optional[VASPType] = None
    jurisdiction: List[VASPJurisdiction] = Field(default_factory=list)
    
    # Timestamp
    screened_at: datetime = Field(default_factory=datetime.utcnow)


class VASPQuery(BaseModel):
    """
    Query Parameters for VASP Search
    """
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = None
    type: Optional[VASPType] = None
    jurisdiction: Optional[VASPJurisdiction] = None
    status: Optional[VASPStatus] = None
    compliance_level: Optional[VASPComplianceLevel] = None
    blockchain: Optional[str] = None
    verified_only: bool = False
    
    # Pagination
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class TravelRuleQuery(BaseModel):
    """
    Query Parameters for Travel Rule Messages
    """
    model_config = ConfigDict(from_attributes=True)
    
    originating_vasp_id: Optional[str] = None
    beneficiary_vasp_id: Optional[str] = None
    status: Optional[TravelRuleStatus] = None
    blockchain: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    
    # Pagination
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class VASPStatistics(BaseModel):
    """
    VASP Directory Statistics
    """
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    total_vasps: int
    active_vasps: int
    vasps_by_type: Dict[VASPType, int]
    vasps_by_jurisdiction: Dict[str, int]
    vasps_by_compliance_level: Dict[VASPComplianceLevel, int]
    
    # Travel Rule Stats
    travel_rule_enabled_vasps: int
    travel_rule_enabled: int
    travel_rule_messages_total: int
    travel_rule_messages_24h: int
