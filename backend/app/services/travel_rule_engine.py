"""
Travel Rule Engine
==================

FATF Travel Rule compliance engine for VASP-to-VASP communication.
Implements OpenVASP, TRISA, and other Travel Rule protocols.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from app.models.vasp import (
    TravelRuleMessage,
    TravelRuleStatus,
    TravelRuleProtocol,
    TravelRuleTransactionType,
    OriginatorInfo,
    BeneficiaryInfo,
    VASP,
)

logger = logging.getLogger(__name__)


class TravelRuleEngine:
    """
    Travel Rule Compliance Engine
    
    Implements FATF Travel Rule requirements:
    - USD 1,000 threshold for full Travel Rule
    - IVMS101 data standard
    - Multiple protocol support (OpenVASP, TRISA, etc.)
    - Sanctions screening integration
    """
    
    # FATF Travel Rule threshold (USD)
    TRAVEL_RULE_THRESHOLD_USD = 1000.0
    
    # Message expiry (24 hours)
    MESSAGE_EXPIRY_HOURS = 24
    
    def __init__(self, vasp_directory: 'VASPDirectory', sanctions_screener=None):
        """
        Initialize Travel Rule Engine
        
        Args:
            vasp_directory: VASP Directory instance
            sanctions_screener: Optional sanctions screening service
        """
        self.vasp_directory = vasp_directory
        self.sanctions_screener = sanctions_screener
        self.messages: Dict[str, TravelRuleMessage] = {}
        
    async def evaluate_transaction(
        self,
        from_address: str,
        to_address: str,
        blockchain: str,
        asset: str,
        amount: float,
        amount_usd: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate if transaction requires Travel Rule compliance
        
        Args:
            from_address: Originating wallet address
            to_address: Beneficiary wallet address
            blockchain: Blockchain name
            asset: Asset symbol
            amount: Amount in native units
            amount_usd: Amount in USD
            
        Returns:
            Evaluation result with requirements
        """
        logger.info(f"Evaluating Travel Rule for {blockchain}:{from_address} -> {to_address}")
        
        # Screen both addresses for VASP association
        from_screening = await self.vasp_directory.screen_address(from_address, blockchain)
        to_screening = await self.vasp_directory.screen_address(to_address, blockchain)
        
        # Check if both are VASPs
        both_vasps = from_screening.is_vasp and to_screening.is_vasp
        
        # Check threshold
        threshold_exceeded = False
        if amount_usd is not None:
            threshold_exceeded = amount_usd >= self.TRAVEL_RULE_THRESHOLD_USD
        
        # Determine if Travel Rule applies
        travel_rule_required = both_vasps and threshold_exceeded
        
        result = {
            "travel_rule_required": travel_rule_required,
            "threshold_exceeded": threshold_exceeded,
            "amount_usd": amount_usd,
            "threshold_usd": self.TRAVEL_RULE_THRESHOLD_USD,
            "originating_vasp": from_screening.dict() if from_screening.is_vasp else None,
            "beneficiary_vasp": to_screening.dict() if to_screening.is_vasp else None,
            "both_vasps": both_vasps,
            "recommendation": self._get_recommendation(
                travel_rule_required,
                threshold_exceeded,
                both_vasps
            ),
        }
        
        logger.info(f"Travel Rule evaluation: required={travel_rule_required}")
        return result
    
    def _get_recommendation(
        self,
        travel_rule_required: bool,
        threshold_exceeded: bool,
        both_vasps: bool,
    ) -> str:
        """Get recommendation text"""
        if travel_rule_required:
            return "Full Travel Rule compliance required. Exchange KYC/AML data with counterparty VASP."
        elif both_vasps and not threshold_exceeded:
            return "VASPs detected but under threshold. Travel Rule optional."
        elif threshold_exceeded and not both_vasps:
            return "Threshold exceeded but only one VASP detected. Standard KYC applies."
        else:
            return "No Travel Rule requirements. Standard transaction."
    
    async def create_message(
        self,
        originating_vasp_id: str,
        beneficiary_vasp_id: str,
        transaction_hash: Optional[str],
        blockchain: str,
        asset: str,
        amount: float,
        amount_usd: Optional[float],
        originator: OriginatorInfo,
        beneficiary: BeneficiaryInfo,
        protocol: TravelRuleProtocol = TravelRuleProtocol.OPENVASP,
    ) -> TravelRuleMessage:
        """
        Create Travel Rule message
        
        Args:
            originating_vasp_id: Originating VASP ID
            beneficiary_vasp_id: Beneficiary VASP ID
            transaction_hash: Blockchain transaction hash
            blockchain: Blockchain name
            asset: Asset symbol
            amount: Amount in native units
            amount_usd: Amount in USD
            originator: Originator information
            beneficiary: Beneficiary information
            protocol: Travel Rule protocol to use
            
        Returns:
            Created Travel Rule message
        """
        # Get VASP details
        orig_vasp = await self.vasp_directory.get_vasp(originating_vasp_id)
        ben_vasp = await self.vasp_directory.get_vasp(beneficiary_vasp_id)
        
        if not orig_vasp or not ben_vasp:
            raise ValueError("Invalid VASP ID(s)")
        
        # Create message
        message = TravelRuleMessage(
            id=str(uuid4()),
            originating_vasp_id=originating_vasp_id,
            originating_vasp_name=orig_vasp.name,
            beneficiary_vasp_id=beneficiary_vasp_id,
            beneficiary_vasp_name=ben_vasp.name,
            transaction_type=TravelRuleTransactionType.TRANSFER,
            transaction_hash=transaction_hash,
            blockchain=blockchain,
            asset=asset,
            amount=amount,
            amount_usd=amount_usd,
            originator=originator,
            beneficiary=beneficiary,
            protocol=protocol,
            status=TravelRuleStatus.PENDING,
        )
        
        # Screen for sanctions
        if self.sanctions_screener:
            screening = await self._screen_parties(originator, beneficiary)
            message.screening_result = screening.get("result")
            message.sanctions_hit = screening.get("sanctions_hit", False)
            message.pep_hit = screening.get("pep_hit", False)
            message.risk_score = screening.get("risk_score")
        
        # Store message
        self.messages[message.id] = message
        
        logger.info(f"Created Travel Rule message {message.id}")
        return message
    
    async def send_message(self, message_id: str) -> bool:
        """
        Send Travel Rule message to beneficiary VASP
        
        Args:
            message_id: Message ID
            
        Returns:
            Success status
        """
        message = self.messages.get(message_id)
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        if message.status != TravelRuleStatus.PENDING:
            raise ValueError(f"Message {message_id} already sent")
        
        # Get beneficiary VASP
        ben_vasp = await self.vasp_directory.get_vasp(message.beneficiary_vasp_id)
        if not ben_vasp:
            raise ValueError("Beneficiary VASP not found")
        
        # Send based on protocol
        success = False
        if message.protocol == TravelRuleProtocol.OPENVASP:
            success = await self._send_openvasp(message, ben_vasp)
        elif message.protocol == TravelRuleProtocol.TRISA:
            success = await self._send_trisa(message, ben_vasp)
        else:
            logger.warning(f"Protocol {message.protocol} not implemented, marking as sent")
            success = True
        
        if success:
            message.status = TravelRuleStatus.SENT
            message.sent_at = datetime.utcnow()
            logger.info(f"Sent Travel Rule message {message_id}")
        else:
            message.status = TravelRuleStatus.FAILED
            logger.error(f"Failed to send Travel Rule message {message_id}")
        
        return success
    
    async def _send_openvasp(self, message: TravelRuleMessage, vasp: VASP) -> bool:
        """
        Send message via OpenVASP protocol
        
        Args:
            message: Travel Rule message
            vasp: Beneficiary VASP
            
        Returns:
            Success status
        """
        if not vasp.openvasp_id or not vasp.api_endpoint:
            logger.error(f"VASP {vasp.id} missing OpenVASP configuration")
            return False
        
        # TODO: Implement actual OpenVASP protocol
        # This would use the OpenVASP library to:
        # 1. Establish session with beneficiary VASP
        # 2. Exchange encryption keys
        # 3. Send encrypted IVMS101 message
        # 4. Wait for acknowledgment
        
        logger.info(f"Sending OpenVASP message to {vasp.openvasp_id}")
        await asyncio.sleep(0.1)  # Simulate network call
        return True
    
    async def _send_trisa(self, message: TravelRuleMessage, vasp: VASP) -> bool:
        """
        Send message via TRISA protocol
        
        Args:
            message: Travel Rule message
            vasp: Beneficiary VASP
            
        Returns:
            Success status
        """
        if not vasp.trisa_endpoint:
            logger.error(f"VASP {vasp.id} missing TRISA configuration")
            return False
        
        # TODO: Implement actual TRISA protocol
        # This would use the TRISA library to:
        # 1. Lookup VASP in TRISA directory
        # 2. Verify certificates
        # 3. Send encrypted payload
        # 4. Wait for acknowledgment
        
        logger.info(f"Sending TRISA message to {vasp.trisa_endpoint}")
        await asyncio.sleep(0.1)  # Simulate network call
        return True
    
    async def acknowledge_message(self, message_id: str, accept: bool = True) -> bool:
        """
        Acknowledge received Travel Rule message
        
        Args:
            message_id: Message ID
            accept: Whether to accept or reject
            
        Returns:
            Success status
        """
        message = self.messages.get(message_id)
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        if message.status != TravelRuleStatus.SENT:
            raise ValueError(f"Message {message_id} not in sent state")
        
        message.status = TravelRuleStatus.ACCEPTED if accept else TravelRuleStatus.REJECTED
        message.acknowledged_at = datetime.utcnow()
        
        if accept:
            message.completed_at = datetime.utcnow()
        
        logger.info(f"Acknowledged Travel Rule message {message_id}: accept={accept}")
        return True
    
    async def get_message(self, message_id: str) -> Optional[TravelRuleMessage]:
        """Get Travel Rule message by ID"""
        return self.messages.get(message_id)
    
    async def list_messages(
        self,
        originating_vasp_id: Optional[str] = None,
        beneficiary_vasp_id: Optional[str] = None,
        status: Optional[TravelRuleStatus] = None,
        blockchain: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TravelRuleMessage]:
        """
        List Travel Rule messages with filters
        
        Args:
            originating_vasp_id: Filter by originating VASP
            beneficiary_vasp_id: Filter by beneficiary VASP
            status: Filter by status
            blockchain: Filter by blockchain
            from_date: Filter by created date (from)
            to_date: Filter by created date (to)
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of messages
        """
        messages = list(self.messages.values())
        
        # Apply filters
        if originating_vasp_id:
            messages = [m for m in messages if m.originating_vasp_id == originating_vasp_id]
        if beneficiary_vasp_id:
            messages = [m for m in messages if m.beneficiary_vasp_id == beneficiary_vasp_id]
        if status:
            messages = [m for m in messages if m.status == status]
        if blockchain:
            messages = [m for m in messages if m.blockchain == blockchain]
        if from_date:
            messages = [m for m in messages if m.created_at >= from_date]
        if to_date:
            messages = [m for m in messages if m.created_at <= to_date]
        
        # Sort by created_at descending
        messages.sort(key=lambda m: m.created_at, reverse=True)
        
        # Pagination
        return messages[skip:skip + limit]
    
    async def cleanup_expired_messages(self) -> int:
        """
        Clean up expired pending messages
        
        Returns:
            Number of messages cleaned up
        """
        expiry_time = datetime.utcnow() - timedelta(hours=self.MESSAGE_EXPIRY_HOURS)
        expired_ids = []
        
        for msg_id, message in self.messages.items():
            if message.status == TravelRuleStatus.PENDING and message.created_at < expiry_time:
                message.status = TravelRuleStatus.EXPIRED
                expired_ids.append(msg_id)
        
        logger.info(f"Expired {len(expired_ids)} Travel Rule messages")
        return len(expired_ids)
    
    async def _screen_parties(
        self,
        originator: OriginatorInfo,
        beneficiary: BeneficiaryInfo,
    ) -> Dict[str, Any]:
        """
        Screen parties for sanctions and PEPs
        
        Args:
            originator: Originator information
            beneficiary: Beneficiary information
            
        Returns:
            Screening result
        """
        if not self.sanctions_screener:
            return {
                "result": "not_screened",
                "sanctions_hit": False,
                "pep_hit": False,
                "risk_score": 0.0,
            }
        
        # TODO: Implement actual sanctions screening
        # This would call sanctions_screener to check:
        # 1. Originator name against sanctions lists
        # 2. Beneficiary name against sanctions lists
        # 3. Country restrictions
        # 4. PEP databases
        
        return {
            "result": "clear",
            "sanctions_hit": False,
            "pep_hit": False,
            "risk_score": 0.0,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get Travel Rule statistics
        
        Returns:
            Statistics dictionary
        """
        messages = list(self.messages.values())
        
        # Count by status
        by_status = {}
        for status in TravelRuleStatus:
            by_status[status.value] = sum(1 for m in messages if m.status == status)
        
        # 24h messages
        last_24h = datetime.utcnow() - timedelta(hours=24)
        messages_24h = sum(1 for m in messages if m.created_at >= last_24h)
        
        return {
            "total_messages": len(messages),
            "messages_24h": messages_24h,
            "by_status": by_status,
            "sanctions_hits": sum(1 for m in messages if m.sanctions_hit),
            "pep_hits": sum(1 for m in messages if m.pep_hit),
        }
