"""
Threat Intelligence Models
==========================

Data models for threat intelligence feeds, intel sharing, and dark web monitoring.
Inspired by Chainalysis Signals Network, TRM Labs Beacon, and Elliptic Intelligence.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ThreatLevel(str, Enum):
    """Threat severity level"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # High priority
    MEDIUM = "medium"      # Monitor closely
    LOW = "low"            # Informational
    INFO = "info"          # General intelligence


class IntelSource(str, Enum):
    """Intelligence source type"""
    COMMUNITY = "community"           # Community-reported intel
    EXCHANGE = "exchange"             # Exchange partnerships
    LAW_ENFORCEMENT = "law_enforcement"  # LEA feeds
    DARK_WEB = "dark_web"            # Dark web monitoring
    OSINT = "osint"                  # Open source intelligence
    COMMERCIAL = "commercial"         # Commercial threat feeds
    INTERNAL = "internal"            # Internal investigation
    AUTOMATED = "automated"          # Automated detection


class IntelCategory(str, Enum):
    """Intelligence category"""
    RANSOMWARE = "ransomware"
    SCAM = "scam"
    PHISHING = "phishing"
    DARKNET_MARKET = "darknet_market"
    MIXER = "mixer"
    STOLEN_FUNDS = "stolen_funds"
    TERRORIST_FINANCING = "terrorist_financing"
    SANCTIONS = "sanctions"
    CHILD_ABUSE = "child_abuse"
    FRAUD = "fraud"
    MONEY_LAUNDERING = "money_laundering"
    HACK = "hack"
    EXCHANGE_FRAUD = "exchange_fraud"
    PYRAMID_SCHEME = "pyramid_scheme"


class IntelStatus(str, Enum):
    """Intelligence item status"""
    PENDING = "pending"      # Awaiting review
    VERIFIED = "verified"    # Verified by analyst
    DISPUTED = "disputed"    # Under dispute
    EXPIRED = "expired"      # No longer relevant
    ACTIVE = "active"        # Active threat


class TLPLevel(str, Enum):
    """Traffic Light Protocol classification"""
    RED = "red"        # Restricted to specific recipients
    AMBER = "amber"    # Limited distribution (trusted partners)
    GREEN = "green"    # Community wide within orgs
    WHITE = "white"    # Publicly shareable


class ThreatIntelItem(BaseModel):
    """Individual threat intelligence item"""
    id: Optional[str] = None
    
    # Identity
    chain: str
    address: str
    
    # Classification
    threat_level: ThreatLevel
    category: IntelCategory
    source: IntelSource
    status: IntelStatus = IntelStatus.PENDING
    
    # Metadata
    confidence: float = Field(..., ge=0.0, le=1.0)
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    
    # Details
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Attribution
    reporter_id: Optional[str] = None  # Who reported this
    verified_by: Optional[str] = None  # Analyst who verified
    
    # Evidence
    evidence: Dict[str, Any] = Field(default_factory=dict)
    related_addresses: List[str] = Field(default_factory=list)
    related_transactions: List[str] = Field(default_factory=list)
    
    # Impact
    affected_amount_usd: Optional[float] = None
    victim_count: Optional[int] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class CommunityIntelReport(BaseModel):
    """Community-submitted intelligence report (like Chainalysis Signals)"""
    id: Optional[str] = None
    
    # Reporter info
    reporter_id: str
    reporter_reputation: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Report content
    chain: str
    address: str
    category: IntelCategory
    threat_level: ThreatLevel
    
    title: str
    description: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    
    # Verification
    status: IntelStatus = IntelStatus.PENDING
    verified_by: Optional[str] = None
    verification_notes: Optional[str] = None
    
    # Community feedback
    upvotes: int = 0
    downvotes: int = 0
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DarkWebIntel(BaseModel):
    """Dark web monitoring intelligence"""
    id: Optional[str] = None
    
    # Source
    marketplace: str  # e.g., "alphabay", "hydra"
    listing_id: Optional[str] = None
    vendor: Optional[str] = None
    
    # Content
    title: str
    description: str
    category: IntelCategory
    
    # Extracted IOCs
    addresses: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    emails: List[str] = Field(default_factory=list)
    
    # Context
    price_usd: Optional[float] = None
    currency: Optional[str] = None
    
    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class IntelSharingMessage(BaseModel):
    """Intel sharing network message (like TRM Beacon)"""
    id: Optional[str] = None
    
    # Network
    network: str = "beacon"  # Network name
    sender_org: str
    recipient_orgs: List[str] = Field(default_factory=list)  # Empty = broadcast
    
    # Content
    threat_level: ThreatLevel
    category: IntelCategory
    tlp: TLPLevel = TLPLevel.AMBER
    
    title: str
    description: str
    
    # IOCs
    indicators: Dict[str, List[str]] = Field(default_factory=dict)  # type -> list of IOCs
    
    # Metadata
    ttl_hours: int = 24  # Time to live
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Verification
    verified: bool = False
    trust_score: float = Field(default=0.5, ge=0.0, le=1.0)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('expires_at', mode='before')
    @classmethod
    def set_expires_at(cls, v, info):
        if v is None and 'shared_at' in info.data:
            from datetime import timedelta
            return info.data['shared_at'] + timedelta(hours=info.data.get('ttl_hours', 24))
        return v
    
    model_config = ConfigDict(from_attributes=True)


class ThreatFeed(BaseModel):
    """External threat feed configuration"""
    id: Optional[str] = None
    
    name: str
    provider: str
    feed_type: str  # "api", "rss", "csv", "json"
    url: str
    
    # Authentication
    auth_type: Optional[str] = None  # "api_key", "oauth", "basic"
    credentials: Dict[str, str] = Field(default_factory=dict)
    
    # Configuration
    update_interval_minutes: int = 60
    enabled: bool = True
    
    # Mapping
    field_mappings: Dict[str, str] = Field(default_factory=dict)
    default_confidence: float = 0.7
    
    # Stats
    last_update: Optional[datetime] = None
    items_fetched: int = 0
    items_stored: int = 0
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class IntelQuery(BaseModel):
    """Query parameters for threat intelligence"""
    chains: Optional[List[str]] = None
    addresses: Optional[List[str]] = None
    
    categories: Optional[List[IntelCategory]] = None
    sources: Optional[List[IntelSource]] = None
    threat_levels: Optional[List[ThreatLevel]] = None
    statuses: Optional[List[IntelStatus]] = None
    
    min_confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    
    limit: int = Field(default=100, le=1000)
    offset: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class IntelStatistics(BaseModel):
    """Threat intelligence statistics"""
    total_items: int
    by_category: Dict[str, int]
    by_source: Dict[str, int]
    by_threat_level: Dict[str, int]
    by_status: Dict[str, int]
    
    avg_confidence: float
    verified_percentage: float
    
    active_feeds: int
    community_reports: int
    darkweb_alerts: int
    
    last_update: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)


class IntelEnrichmentResult(BaseModel):
    """Result of enriching an address with threat intelligence"""
    chain: str
    address: str
    
    # Matches
    matches: List[ThreatIntelItem]
    highest_threat_level: Optional[ThreatLevel] = None
    
    # Aggregated scores
    threat_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Categories found
    categories: List[IntelCategory] = Field(default_factory=list)
    sources: List[IntelSource] = Field(default_factory=list)
    
    # Recommendations
    recommended_action: str  # "block", "alert", "monitor", "allow"
    risk_factors: List[str] = Field(default_factory=list)
    
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(from_attributes=True)
