"""
Exchange Liaison System
=======================

Direct communication channels with major exchanges for:
- Rapid intelligence sharing
- Account freezing requests
- Transaction holds
- Compliance data exchange
- Case collaboration

Inspired by Chainalysis's $12.6B+ asset recovery through exchange partnerships.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExchangeLiaisonStatus(str, Enum):
    """Status of exchange partnership"""
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class RequestType(str, Enum):
    """Type of exchange request"""
    FREEZE_ACCOUNT = "freeze_account"
    HOLD_TRANSACTION = "hold_transaction"
    INTEL_SHARING = "intel_sharing"
    KYC_REQUEST = "kyc_request"
    SUBPOENA = "subpoena"
    VOLUNTARY_DISCLOSURE = "voluntary_disclosure"


class RequestStatus(str, Enum):
    """Status of liaison request"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ExchangePartner:
    """Exchange partnership profile"""
    
    def __init__(
        self,
        exchange_id: str,
        name: str,
        liaison_email: str,
        api_endpoint: Optional[str] = None,
        supported_request_types: Optional[List[RequestType]] = None
    ):
        self.exchange_id = exchange_id
        self.name = name
        self.liaison_email = liaison_email
        self.api_endpoint = api_endpoint
        self.supported_request_types = supported_request_types or [
            RequestType.INTEL_SHARING,
            RequestType.FREEZE_ACCOUNT
        ]
        
        self.status = ExchangeLiaisonStatus.ACTIVE
        self.partnership_date = datetime.utcnow()
        self.total_requests = 0
        self.successful_requests = 0
        self.avg_response_time_hours = 24.0
        
        # Contact information
        self.emergency_contact: Optional[str] = None
        self.primary_jurisdiction: Optional[str] = None
        
        # Capabilities
        self.real_time_monitoring = False
        self.automatic_alerts = False
        self.kyc_sharing = False


class ExchangeLiaisonRequest:
    """Request to exchange partner"""
    
    def __init__(
        self,
        exchange_id: str,
        request_type: RequestType,
        case_id: str,
        description: str,
        target_addresses: Optional[List[str]] = None,
        target_accounts: Optional[List[str]] = None,
        urgency: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = f"req_{exchange_id}_{int(datetime.utcnow().timestamp())}"
        self.exchange_id = exchange_id
        self.request_type = request_type
        self.case_id = case_id
        self.description = description
        self.target_addresses = target_addresses or []
        self.target_accounts = target_accounts or []
        self.urgency = urgency  # low, normal, high, critical
        self.metadata = metadata or {}
        
        self.status = RequestStatus.PENDING
        self.submitted_at: Optional[datetime] = None
        self.reviewed_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        self.response: Optional[Dict[str, Any]] = None
        self.notes: List[str] = []


class ExchangeLiaisonService:
    """
    Manages relationships and communications with exchange partners.
    
    Features:
    - Direct communication channels
    - Automated request submission
    - Response tracking
    - Intelligence sharing
    - Emergency freeze capabilities
    """
    
    def __init__(self):
        self.partners: Dict[str, ExchangePartner] = {}
        self.requests: Dict[str, ExchangeLiaisonRequest] = {}
        
        # Initialize major exchange partnerships
        self._initialize_partnerships()
    
    def _initialize_partnerships(self):
        """Initialize partnerships with major exchanges"""
        major_exchanges = [
            ExchangePartner(
                exchange_id="binance",
                name="Binance",
                liaison_email="compliance@binance.com",
                api_endpoint="https://api.binance.com/v1/compliance",
                supported_request_types=[
                    RequestType.FREEZE_ACCOUNT,
                    RequestType.INTEL_SHARING,
                    RequestType.KYC_REQUEST,
                    RequestType.SUBPOENA
                ]
            ),
            ExchangePartner(
                exchange_id="coinbase",
                name="Coinbase",
                liaison_email="legal@coinbase.com",
                api_endpoint="https://api.coinbase.com/v2/compliance",
                supported_request_types=[
                    RequestType.FREEZE_ACCOUNT,
                    RequestType.INTEL_SHARING,
                    RequestType.SUBPOENA,
                    RequestType.VOLUNTARY_DISCLOSURE
                ]
            ),
            ExchangePartner(
                exchange_id="kraken",
                name="Kraken",
                liaison_email="compliance@kraken.com",
                supported_request_types=[
                    RequestType.FREEZE_ACCOUNT,
                    RequestType.INTEL_SHARING,
                    RequestType.KYC_REQUEST
                ]
            ),
            ExchangePartner(
                exchange_id="gemini",
                name="Gemini",
                liaison_email="compliance@gemini.com",
                supported_request_types=[
                    RequestType.FREEZE_ACCOUNT,
                    RequestType.INTEL_SHARING,
                    RequestType.SUBPOENA
                ]
            ),
            ExchangePartner(
                exchange_id="bitfinex",
                name="Bitfinex",
                liaison_email="compliance@bitfinex.com",
                supported_request_types=[
                    RequestType.INTEL_SHARING,
                    RequestType.FREEZE_ACCOUNT
                ]
            ),
        ]
        
        for partner in major_exchanges:
            # Set enhanced capabilities for tier-1 exchanges
            if partner.exchange_id in ["coinbase", "kraken", "gemini"]:
                partner.real_time_monitoring = True
                partner.automatic_alerts = True
                partner.kyc_sharing = True
                partner.avg_response_time_hours = 6.0
            
            self.partners[partner.exchange_id] = partner
    
    def register_partner(self, partner: ExchangePartner) -> ExchangePartner:
        """Register new exchange partner"""
        self.partners[partner.exchange_id] = partner
        logger.info(f"Registered exchange partner: {partner.name}")
        return partner
    
    async def submit_request(
        self,
        exchange_id: str,
        request_type: RequestType,
        case_id: str,
        description: str,
        target_addresses: Optional[List[str]] = None,
        target_accounts: Optional[List[str]] = None,
        urgency: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExchangeLiaisonRequest:
        """
        Submit request to exchange partner.
        
        Args:
            exchange_id: Exchange identifier
            request_type: Type of request
            case_id: Associated case ID
            description: Request description
            target_addresses: Blockchain addresses of interest
            target_accounts: Account IDs (if known)
            urgency: Request urgency level
            metadata: Additional data
            
        Returns:
            Liaison request with tracking ID
        """
        partner = self.partners.get(exchange_id)
        if not partner:
            raise ValueError(f"Unknown exchange partner: {exchange_id}")
        
        if partner.status != ExchangeLiaisonStatus.ACTIVE:
            raise ValueError(f"Exchange partner {exchange_id} is not active")
        
        if request_type not in partner.supported_request_types:
            raise ValueError(
                f"Request type {request_type} not supported by {partner.name}"
            )
        
        # Create request
        request = ExchangeLiaisonRequest(
            exchange_id=exchange_id,
            request_type=request_type,
            case_id=case_id,
            description=description,
            target_addresses=target_addresses,
            target_accounts=target_accounts,
            urgency=urgency,
            metadata=metadata
        )
        
        # Submit (in production, would send via API/email)
        request.submitted_at = datetime.utcnow()
        request.status = RequestStatus.SUBMITTED
        
        # Store request
        self.requests[request.id] = request
        
        # Update partner stats
        partner.total_requests += 1
        
        logger.info(
            f"Submitted {request_type} request to {partner.name} "
            f"for case {case_id} (ID: {request.id})"
        )
        
        # Simulate immediate response for high-urgency freeze requests
        if urgency == "critical" and request_type == RequestType.FREEZE_ACCOUNT:
            await self._simulate_freeze_response(request, partner)
        
        return request
    
    async def _simulate_freeze_response(
        self,
        request: ExchangeLiaisonRequest,
        partner: ExchangePartner
    ):
        """Simulate rapid freeze response (for demo)"""
        request.status = RequestStatus.APPROVED
        request.reviewed_at = datetime.utcnow()
        request.response = {
            "action": "account_frozen",
            "frozen_accounts": request.target_accounts or [],
            "frozen_at": datetime.utcnow().isoformat(),
            "estimated_holdings_usd": 0,  # Would be real data
            "next_steps": "Awaiting legal documentation"
        }
        request.notes.append(
            f"Emergency freeze approved by {partner.name} compliance team"
        )
        
        partner.successful_requests += 1
    
    async def get_request_status(self, request_id: str) -> Optional[ExchangeLiaisonRequest]:
        """Get status of liaison request"""
        return self.requests.get(request_id)
    
    async def update_request(
        self,
        request_id: str,
        status: RequestStatus,
        response: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> ExchangeLiaisonRequest:
        """Update request status (typically called by exchange via webhook)"""
        request = self.requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        request.status = status
        
        if status in [RequestStatus.APPROVED, RequestStatus.REJECTED]:
            request.reviewed_at = datetime.utcnow()
        
        if status == RequestStatus.COMPLETED:
            request.completed_at = datetime.utcnow()
            
            # Update partner success rate
            partner = self.partners.get(request.exchange_id)
            if partner and status == RequestStatus.COMPLETED:
                partner.successful_requests += 1
        
        if response:
            request.response = response
        
        if notes:
            request.notes.append(f"{datetime.utcnow().isoformat()}: {notes}")
        
        return request
    
    def get_partner_statistics(self, exchange_id: str) -> Optional[Dict[str, Any]]:
        """Get partnership statistics"""
        partner = self.partners.get(exchange_id)
        if not partner:
            return None
        
        success_rate = (
            (partner.successful_requests / partner.total_requests * 100)
            if partner.total_requests > 0
            else 0
        )
        
        return {
            "exchange_id": partner.exchange_id,
            "name": partner.name,
            "status": partner.status.value,
            "total_requests": partner.total_requests,
            "successful_requests": partner.successful_requests,
            "success_rate": success_rate,
            "avg_response_time_hours": partner.avg_response_time_hours,
            "capabilities": {
                "real_time_monitoring": partner.real_time_monitoring,
                "automatic_alerts": partner.automatic_alerts,
                "kyc_sharing": partner.kyc_sharing
            },
            "supported_request_types": [rt.value for rt in partner.supported_request_types]
        }
    
    def get_all_partners(self) -> List[Dict[str, Any]]:
        """Get all exchange partners"""
        return [
            {
                "exchange_id": p.exchange_id,
                "name": p.name,
                "status": p.status.value,
                "total_requests": p.total_requests,
                "success_rate": (
                    (p.successful_requests / p.total_requests * 100)
                    if p.total_requests > 0
                    else 0
                )
            }
            for p in self.partners.values()
        ]
    
    def get_case_requests(self, case_id: str) -> List[ExchangeLiaisonRequest]:
        """Get all requests for a case"""
        return [
            req for req in self.requests.values()
            if req.case_id == case_id
        ]
    
    def get_pending_requests(self) -> List[ExchangeLiaisonRequest]:
        """Get all pending requests"""
        return [
            req for req in self.requests.values()
            if req.status in [RequestStatus.PENDING, RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW]
        ]


# Global service instance
exchange_liaison_service = ExchangeLiaisonService()
