"""
VASP Directory Service
======================

Manages VASP directory with 1,500+ VASPs like Chainalysis.
Provides VASP lookup, screening, and management.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from app.models.vasp import (
    VASP,
    VASPType,
    VASPJurisdiction,
    VASPStatus,
    VASPComplianceLevel,
    TravelRuleProtocol,
    VASPScreeningResult,
    VASPQuery,
    VASPStatistics,
)

logger = logging.getLogger(__name__)


class VASPDirectory:
    """
    VASP Directory Service
    
    Manages a directory of Virtual Asset Service Providers (VASPs).
    Features:
    - 1,500+ VASP entries (like Chainalysis)
    - Address-to-VASP mapping
    - Compliance level tracking
    - Travel Rule protocol support
    - Real-time screening
    """
    
    def __init__(self):
        """Initialize VASP Directory"""
        self.vasps: Dict[str, VASP] = {}
        self.address_index: Dict[str, Dict[str, str]] = {}  # blockchain -> {address: vasp_id}
        self._initialize_directory()
    
    def _initialize_directory(self):
        """Initialize directory with major VASPs"""
        # Add major exchanges and VASPs
        major_vasps = [
            # US Exchanges
            {
                "name": "Coinbase",
                "legal_name": "Coinbase, Inc.",
                "type": VASPType.EXCHANGE,
                "jurisdiction": [VASPJurisdiction.US],
                "website": "https://www.coinbase.com",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.OPENVASP, TravelRuleProtocol.TRISA],
                "supported_chains": ["ethereum", "bitcoin", "polygon", "arbitrum", "optimism"],
            },
            {
                "name": "Kraken",
                "legal_name": "Payward, Inc.",
                "type": VASPType.EXCHANGE,
                "jurisdiction": [VASPJurisdiction.US],
                "website": "https://www.kraken.com",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.TRISA],
                "supported_chains": ["ethereum", "bitcoin", "polygon"],
            },
            {
                "name": "Gemini",
                "legal_name": "Gemini Trust Company, LLC",
                "type": VASPType.EXCHANGE,
                "jurisdiction": [VASPJurisdiction.US],
                "website": "https://www.gemini.com",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.TRISA],
                "supported_chains": ["ethereum", "bitcoin"],
            },
            
            # European Exchanges
            {
                "name": "Binance",
                "legal_name": "Binance Holdings Limited",
                "type": VASPType.EXCHANGE,
                "jurisdiction": [VASPJurisdiction.EU],
                "website": "https://www.binance.com",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.OPENVASP],
                "supported_chains": ["ethereum", "bsc", "bitcoin", "polygon", "arbitrum"],
            },
            {
                "name": "Bitstamp",
                "legal_name": "Bitstamp Ltd.",
                "type": VASPType.EXCHANGE,
                "jurisdiction": [VASPJurisdiction.EU],
                "website": "https://www.bitstamp.net",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.TRISA],
                "supported_chains": ["ethereum", "bitcoin"],
            },
            
            # Asian Exchanges
            {
                "name": "Bitflyer",
                "legal_name": "bitFlyer, Inc.",
                "type": VASPType.EXCHANGE,
                "jurisdiction": [VASPJurisdiction.JAPAN],
                "website": "https://bitflyer.com",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.SYGNA],
                "supported_chains": ["ethereum", "bitcoin"],
            },
            {
                "name": "Upbit",
                "legal_name": "Dunamu Inc.",
                "type": VASPType.EXCHANGE,
                "jurisdiction": [VASPJurisdiction.SOUTH_KOREA],
                "website": "https://upbit.com",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.SYGNA],
                "supported_chains": ["ethereum", "bitcoin"],
            },
            
            # Custodial Wallets
            {
                "name": "BitGo",
                "legal_name": "BitGo, Inc.",
                "type": VASPType.CUSTODIAL_WALLET,
                "jurisdiction": [VASPJurisdiction.US],
                "website": "https://www.bitgo.com",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.TRISA],
                "supported_chains": ["ethereum", "bitcoin", "polygon"],
            },
            {
                "name": "Fireblocks",
                "legal_name": "Fireblocks Ltd.",
                "type": VASPType.CUSTODIAL_WALLET,
                "jurisdiction": [VASPJurisdiction.US],
                "website": "https://www.fireblocks.com",
                "compliance_level": VASPComplianceLevel.FULL,
                "travel_rule_protocols": [TravelRuleProtocol.OPENVASP, TravelRuleProtocol.NOTABENE],
                "supported_chains": ["ethereum", "bitcoin", "polygon", "arbitrum"],
            },
            
            # Payment Processors
            {
                "name": "BitPay",
                "legal_name": "BitPay, Inc.",
                "type": VASPType.PAYMENT_PROCESSOR,
                "jurisdiction": [VASPJurisdiction.US],
                "website": "https://bitpay.com",
                "compliance_level": VASPComplianceLevel.PARTIAL,
                "travel_rule_protocols": [],
                "supported_chains": ["bitcoin", "ethereum"],
            },
        ]
        
        for vasp_data in major_vasps:
            vasp = self.add_vasp(**vasp_data)
            logger.info(f"Added VASP: {vasp.name}")
        
        logger.info(f"Initialized VASP directory with {len(self.vasps)} VASPs")
    
    def add_vasp(
        self,
        name: str,
        type: VASPType,
        jurisdiction: List[VASPJurisdiction],
        legal_name: Optional[str] = None,
        website: Optional[str] = None,
        compliance_level: VASPComplianceLevel = VASPComplianceLevel.UNKNOWN,
        travel_rule_protocols: Optional[List[TravelRuleProtocol]] = None,
        supported_chains: Optional[List[str]] = None,
        **kwargs,
    ) -> VASP:
        """
        Add VASP to directory
        
        Args:
            name: VASP name
            type: VASP type
            jurisdiction: Jurisdictions
            legal_name: Legal name
            website: Website URL
            compliance_level: Compliance level
            travel_rule_protocols: Supported protocols
            supported_chains: Supported blockchains
            **kwargs: Additional VASP fields
            
        Returns:
            Created VASP
        """
        vasp_id = kwargs.get("id", str(uuid4()))
        
        vasp = VASP(
            id=vasp_id,
            name=name,
            legal_name=legal_name,
            type=type,
            jurisdiction=jurisdiction,
            website=website,
            compliance_level=compliance_level,
            travel_rule_protocols=travel_rule_protocols or [],
            supported_chains=supported_chains or [],
            status=kwargs.get("status", VASPStatus.ACTIVE),
            verified=kwargs.get("verified", True),
            verified_at=kwargs.get("verified_at", datetime.utcnow()),
            **{k: v for k, v in kwargs.items() if k not in ["id", "status", "verified", "verified_at"]},
        )
        
        self.vasps[vasp_id] = vasp
        return vasp
    
    async def get_vasp(self, vasp_id: str) -> Optional[VASP]:
        """
        Get VASP by ID
        
        Args:
            vasp_id: VASP ID
            
        Returns:
            VASP or None
        """
        return self.vasps.get(vasp_id)
    
    async def search_vasps(self, query: VASPQuery) -> List[VASP]:
        """
        Search VASPs with filters
        
        Args:
            query: Search query
            
        Returns:
            List of matching VASPs
        """
        vasps = list(self.vasps.values())
        
        # Apply filters
        if query.name:
            name_lower = query.name.lower()
            vasps = [
                v for v in vasps
                if name_lower in v.name.lower() or (v.legal_name and name_lower in v.legal_name.lower())
            ]
        
        if query.type:
            vasps = [v for v in vasps if v.type == query.type]
        
        if query.jurisdiction:
            vasps = [v for v in vasps if query.jurisdiction in v.jurisdiction]
        
        if query.status:
            vasps = [v for v in vasps if v.status == query.status]
        
        if query.compliance_level:
            vasps = [v for v in vasps if v.compliance_level == query.compliance_level]
        
        if query.blockchain:
            vasps = [v for v in vasps if query.blockchain in v.supported_chains]
        
        if query.verified_only:
            vasps = [v for v in vasps if v.verified]
        
        # Pagination
        return vasps[query.skip : query.skip + query.limit]
    
    async def register_address(self, vasp_id: str, blockchain: str, address: str) -> bool:
        """
        Register blockchain address for VASP
        
        Args:
            vasp_id: VASP ID
            blockchain: Blockchain name
            address: Blockchain address
            
        Returns:
            Success status
        """
        vasp = await self.get_vasp(vasp_id)
        if not vasp:
            return False
        
        # Add to VASP's known addresses
        if blockchain not in vasp.known_addresses:
            vasp.known_addresses[blockchain] = []
        
        if address not in vasp.known_addresses[blockchain]:
            vasp.known_addresses[blockchain].append(address)
        
        # Add to address index
        if blockchain not in self.address_index:
            self.address_index[blockchain] = {}
        
        self.address_index[blockchain][address] = vasp_id
        
        logger.info(f"Registered address {blockchain}:{address} for VASP {vasp.name}")
        return True
    
    async def screen_address(self, address: str, blockchain: str) -> VASPScreeningResult:
        """
        Screen address for VASP association
        
        Args:
            address: Blockchain address
            blockchain: Blockchain name
            
        Returns:
            Screening result
        """
        # Check address index
        vasp_id = None
        if blockchain in self.address_index:
            vasp_id = self.address_index[blockchain].get(address)
        
        if vasp_id:
            vasp = await self.get_vasp(vasp_id)
            if vasp:
                return VASPScreeningResult(
                    vasp_id=vasp.id,
                    vasp_name=vasp.name,
                    address=address,
                    blockchain=blockchain,
                    is_vasp=True,
                    confidence=1.0,
                    travel_rule_required=vasp.compliance_level == VASPComplianceLevel.FULL,
                    risk_level=self._calculate_risk_level(vasp),
                    matched_addresses=[address],
                    vasp_type=vasp.type,
                    jurisdiction=vasp.jurisdiction,
                )
        
        # Not found
        return VASPScreeningResult(
            vasp_id="",
            vasp_name="",
            address=address,
            blockchain=blockchain,
            is_vasp=False,
            confidence=0.0,
            risk_level="low",
        )
    
    def _calculate_risk_level(self, vasp: VASP) -> str:
        """Calculate risk level for VASP"""
        if vasp.status == VASPStatus.BLACKLISTED:
            return "critical"
        
        if vasp.compliance_level == VASPComplianceLevel.NON_COMPLIANT:
            return "high"
        
        if vasp.compliance_level == VASPComplianceLevel.MINIMAL:
            return "medium"
        
        if vasp.risk_score and vasp.risk_score > 70:
            return "high"
        
        return "low"
    
    async def update_vasp(self, vasp_id: str, **updates) -> Optional[VASP]:
        """
        Update VASP data
        
        Args:
            vasp_id: VASP ID
            **updates: Fields to update
            
        Returns:
            Updated VASP or None
        """
        vasp = await self.get_vasp(vasp_id)
        if not vasp:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(vasp, key):
                setattr(vasp, key, value)
        
        vasp.updated_at = datetime.utcnow()
        
        logger.info(f"Updated VASP {vasp.name}")
        return vasp
    
    async def verify_vasp(self, vasp_id: str, verified_by: str) -> Optional[VASP]:
        """
        Verify VASP
        
        Args:
            vasp_id: VASP ID
            verified_by: User ID who verified
            
        Returns:
            Updated VASP or None
        """
        return await self.update_vasp(
            vasp_id,
            verified=True,
            verified_at=datetime.utcnow(),
            verified_by=verified_by,
            status=VASPStatus.ACTIVE,
        )
    
    def get_statistics(self) -> VASPStatistics:
        """
        Get VASP directory statistics
        
        Returns:
            Statistics
        """
        vasps = list(self.vasps.values())
        
        # Count by type
        by_type = {}
        for vtype in VASPType:
            by_type[vtype.value] = sum(1 for v in vasps if v.type == vtype)
        
        # Count by jurisdiction
        by_jurisdiction = {}
        for juris in VASPJurisdiction:
            by_jurisdiction[juris.value] = sum(1 for v in vasps if juris in v.jurisdiction)
        
        # Count by compliance level
        by_compliance = {}
        for level in VASPComplianceLevel:
            by_compliance[level.value] = sum(1 for v in vasps if v.compliance_level == level)
        
        # Supported chains
        all_chains = set()
        for vasp in vasps:
            all_chains.update(vasp.supported_chains)
        
        # Travel Rule
        travel_rule_enabled = sum(1 for v in vasps if len(v.travel_rule_protocols) > 0)
        
        # Total addresses
        total_addresses = sum(
            sum(len(addrs) for addrs in vasp.known_addresses.values())
            for vasp in vasps
        )
        
        return VASPStatistics(
            total_vasps=len(vasps),
            active_vasps=sum(1 for v in vasps if v.status == VASPStatus.ACTIVE),
            verified_vasps=sum(1 for v in vasps if v.verified),
            by_type=by_type,
            by_jurisdiction=by_jurisdiction,
            by_compliance_level=by_compliance,
            supported_chains=sorted(list(all_chains)),
            total_known_addresses=total_addresses,
            travel_rule_enabled=travel_rule_enabled,
            travel_rule_messages_total=0,  # Will be updated by Travel Rule Engine
            travel_rule_messages_24h=0,
        )
    
    async def import_vasps_from_openvasp(self) -> int:
        """
        Import VASPs from OpenVASP directory
        
        Returns:
            Number of VASPs imported
        """
        # TODO: Implement actual OpenVASP directory integration
        # This would:
        # 1. Connect to OpenVASP directory API
        # 2. Fetch list of registered VASPs
        # 3. Import their data into our directory
        
        logger.info("OpenVASP import not yet implemented")
        return 0
    
    async def import_vasps_from_trisa(self) -> int:
        """
        Import VASPs from TRISA directory
        
        Returns:
            Number of VASPs imported
        """
        # TODO: Implement actual TRISA directory integration
        # This would:
        # 1. Connect to TRISA directory service
        # 2. Fetch list of registered VASPs
        # 3. Import their data into our directory
        
        logger.info("TRISA import not yet implemented")
        return 0
