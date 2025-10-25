"""
Intelligence Sharing Network Service (TRM Beacon-Style)

Real-time intelligence sharing between organizations for coordinated threat response.
Similar to TRM Labs' Beacon Network.

Features:
- Flagging of illicit addresses by verified investigators
- Real-time auto-tracing of flagged funds
- Instant alerts when flagged funds reach monitored exchanges
- Trust-based network with verification
- Multi-institutional collaboration
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class FlagReason(str, Enum):
    """Reason for flagging an address"""
    HACK = "hack"
    FRAUD = "fraud"
    SANCTIONS = "sanctions"
    TERRORISM_FINANCING = "terrorism_financing"
    MONEY_LAUNDERING = "money_laundering"
    RANSOMWARE = "ransomware"
    SCAM = "scam"
    MIXER_ABUSE = "mixer_abuse"
    CHILD_EXPLOITATION = "child_exploitation"
    OTHER_ILLICIT = "other_illicit"


class InvestigatorTier(str, Enum):
    """Trust tier for investigators"""
    VERIFIED_LAW_ENFORCEMENT = "verified_law_enforcement"  # Highest trust
    VERIFIED_EXCHANGE = "verified_exchange"
    VERIFIED_SECURITY_FIRM = "verified_security_firm"
    VERIFIED_ANALYST = "verified_analyst"
    COMMUNITY_TRUSTED = "community_trusted"  # Lower trust, requires validation


class FlagStatus(str, Enum):
    """Status of a flag"""
    ACTIVE = "active"
    CONFIRMED = "confirmed"  # Confirmed by multiple sources
    DISPUTED = "disputed"
    RESOLVED = "resolved"  # Funds recovered or case closed
    EXPIRED = "expired"


class AlertAction(str, Enum):
    """Recommended action for alerts"""
    FREEZE = "freeze"  # Freeze funds immediately
    REVIEW = "review"  # Manual review required
    MONITOR = "monitor"  # Continue monitoring
    ALLOW = "allow"  # Allow with logging


class IntelligenceSharingService:
    """
    Intelligence Sharing Network for coordinated threat response.
    
    Architecture:
    - Decentralized trust network
    - Real-time event streaming (Kafka)
    - Automatic fund tracing on flag
    - Alert broadcasting to network members
    """
    
    def __init__(self):
        self.flags_db: Dict[str, Dict[str, Any]] = {}  # In-memory for now, move to DB
        self.investigators: Dict[str, Dict[str, Any]] = {}
        self.network_members: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: List[callable] = []
        
    async def register_investigator(
        self,
        investigator_id: str,
        org_name: str,
        tier: InvestigatorTier,
        verification_docs: Optional[Dict[str, Any]] = None,
        contact_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Register a verified investigator in the network.
        
        Args:
            investigator_id: Unique investigator ID
            org_name: Organization name
            tier: Trust tier
            verification_docs: Verification documents
            contact_info: Contact information
            
        Returns:
            Investigator profile
        """
        investigator = {
            "investigator_id": investigator_id,
            "org_name": org_name,
            "tier": tier.value,
            "trust_score": self._get_initial_trust_score(tier),
            "flags_submitted": 0,
            "flags_confirmed": 0,
            "joined_at": datetime.utcnow().isoformat(),
            "verification_docs": verification_docs or {},
            "contact_info": contact_info or {},
            "is_active": True
        }
        
        self.investigators[investigator_id] = investigator
        logger.info(f"Registered investigator: {org_name} ({tier.value})")
        
        return investigator
    
    async def flag_address(
        self,
        address: str,
        chain: str,
        reason: FlagReason,
        investigator_id: str,
        incident_id: Optional[str] = None,
        amount_usd: Optional[float] = None,
        description: Optional[str] = None,
        evidence: Optional[List[Dict[str, Any]]] = None,
        related_addresses: Optional[List[str]] = None,
        auto_trace: bool = True
    ) -> Dict[str, Any]:
        """
        Flag an address as illicit.
        
        Args:
            address: Blockchain address to flag
            chain: Chain ID (ethereum, bitcoin, etc.)
            reason: Reason for flagging
            investigator_id: ID of investigator submitting flag
            incident_id: Related incident/case ID
            amount_usd: Estimated amount involved
            description: Detailed description
            evidence: Supporting evidence
            related_addresses: Related addresses
            auto_trace: Automatically trace funds
            
        Returns:
            Flag record
        """
        if investigator_id not in self.investigators:
            raise ValueError(f"Investigator {investigator_id} not registered")
        
        investigator = self.investigators[investigator_id]
        if not investigator["is_active"]:
            raise ValueError(f"Investigator {investigator_id} is not active")
        
        flag_id = self._generate_flag_id(address, chain, investigator_id)
        
        flag = {
            "flag_id": flag_id,
            "address": address.lower(),
            "chain": chain,
            "reason": reason.value,
            "investigator_id": investigator_id,
            "org_name": investigator["org_name"],
            "tier": investigator["tier"],
            "incident_id": incident_id,
            "amount_usd": amount_usd,
            "description": description,
            "evidence": evidence or [],
            "related_addresses": [addr.lower() for addr in (related_addresses or [])],
            "status": FlagStatus.ACTIVE.value,
            "confidence_score": self._calculate_confidence_score(investigator["tier"], evidence),
            "confirmations": 1,
            "confirming_investigators": [investigator_id],
            "flagged_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "auto_trace_enabled": auto_trace,
            "trace_initiated": False
        }
        
        self.flags_db[flag_id] = flag
        
        # Update investigator stats
        investigator["flags_submitted"] += 1
        
        logger.info(f"Address flagged: {address} ({chain}) by {investigator['org_name']} - Reason: {reason.value}")
        
        # Auto-trace if enabled
        if auto_trace:
            await self._initiate_auto_trace(flag)
        
        # Broadcast alert to network
        await self._broadcast_flag_alert(flag)
        
        return flag
    
    async def confirm_flag(
        self,
        flag_id: str,
        investigator_id: str,
        additional_evidence: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Confirm an existing flag (multi-source validation).
        
        Args:
            flag_id: Flag ID to confirm
            investigator_id: ID of confirming investigator
            additional_evidence: Additional supporting evidence
            
        Returns:
            Updated flag
        """
        if flag_id not in self.flags_db:
            raise ValueError(f"Flag {flag_id} not found")
        
        if investigator_id not in self.investigators:
            raise ValueError(f"Investigator {investigator_id} not registered")
        
        flag = self.flags_db[flag_id]
        
        # Don't allow double confirmation by same investigator
        if investigator_id in flag["confirming_investigators"]:
            return flag
        
        flag["confirmations"] += 1
        flag["confirming_investigators"].append(investigator_id)
        flag["last_updated"] = datetime.utcnow().isoformat()
        
        if additional_evidence:
            flag["evidence"].extend(additional_evidence)
        
        # Update confidence score
        flag["confidence_score"] = self._recalculate_confidence(flag)
        
        # Auto-confirm if multiple trusted sources
        if flag["confirmations"] >= 3 and flag["status"] == FlagStatus.ACTIVE.value:
            flag["status"] = FlagStatus.CONFIRMED.value
            logger.info(f"Flag {flag_id} auto-confirmed (3+ sources)")
        
        # Update confirming investigator stats
        investigator = self.investigators[investigator_id]
        investigator["flags_confirmed"] += 1
        
        return flag
    
    async def check_address_against_network(
        self,
        address: str,
        chain: str,
        check_related: bool = True
    ) -> Dict[str, Any]:
        """
        Check if address is flagged in the intelligence network.
        
        Args:
            address: Address to check
            chain: Chain ID
            check_related: Also check related addresses
            
        Returns:
            Risk assessment with flags and recommended action
        """
        address = address.lower()
        
        # Direct flags
        direct_flags = [
            flag for flag in self.flags_db.values()
            if flag["address"] == address 
            and flag["chain"] == chain
            and flag["status"] in [FlagStatus.ACTIVE.value, FlagStatus.CONFIRMED.value]
        ]
        
        # Related address flags
        related_flags = []
        if check_related:
            related_flags = [
                flag for flag in self.flags_db.values()
                if address in flag.get("related_addresses", [])
                and flag["status"] in [FlagStatus.ACTIVE.value, FlagStatus.CONFIRMED.value]
            ]
        
        # Calculate aggregate risk
        risk_score = self._calculate_aggregate_risk(direct_flags, related_flags)
        
        # Determine recommended action
        action = self._determine_action(risk_score, direct_flags, related_flags)
        
        result = {
            "address": address,
            "chain": chain,
            "is_flagged": len(direct_flags) > 0,
            "direct_flags": len(direct_flags),
            "related_flags": len(related_flags),
            "risk_score": risk_score,
            "recommended_action": action.value,
            "flags": direct_flags + related_flags,
            "checked_at": datetime.utcnow().isoformat()
        }
        
        # Log high-risk checks
        if risk_score >= 0.7:
            logger.warning(f"High-risk address checked: {address} ({chain}) - Score: {risk_score}")
        
        return result
    
    async def register_network_member(
        self,
        member_id: str,
        org_name: str,
        member_type: str,  # exchange, defi, stablecoin_issuer, custodian
        alert_webhook: Optional[str] = None,
        auto_freeze_enabled: bool = False
    ) -> Dict[str, Any]:
        """
        Register an organization as a network member (exchange, DeFi, etc.).
        
        Args:
            member_id: Unique member ID
            org_name: Organization name
            member_type: Type of member
            alert_webhook: Webhook URL for alerts
            auto_freeze_enabled: Enable automatic freezing
            
        Returns:
            Member profile
        """
        member = {
            "member_id": member_id,
            "org_name": org_name,
            "member_type": member_type,
            "alert_webhook": alert_webhook,
            "auto_freeze_enabled": auto_freeze_enabled,
            "joined_at": datetime.utcnow().isoformat(),
            "alerts_received": 0,
            "funds_frozen": 0,
            "funds_recovered_usd": 0.0,
            "is_active": True
        }
        
        self.network_members[member_id] = member
        logger.info(f"Network member registered: {org_name} ({member_type})")
        
        return member
    
    async def _initiate_auto_trace(self, flag: Dict[str, Any]) -> None:
        """Initiate automatic tracing of flagged funds."""
        try:
            # TODO: Integrate with existing trace service
            # from app.services.trace_service import trace_service
            # trace_id = await trace_service.start_trace(
            #     source=flag["address"],
            #     chain=flag["chain"],
            #     max_depth=5,
            #     auto_follow=True
            # )
            
            flag["trace_initiated"] = True
            flag["trace_id"] = f"auto-trace-{flag['flag_id']}"
            
            logger.info(f"Auto-trace initiated for flag {flag['flag_id']}")
        except Exception as e:
            logger.error(f"Auto-trace failed for flag {flag['flag_id']}: {e}")
    
    async def _broadcast_flag_alert(self, flag: Dict[str, Any]) -> None:
        """Broadcast flag alert to all network members."""
        alert = {
            "alert_type": "flag_created",
            "flag_id": flag["flag_id"],
            "address": flag["address"],
            "chain": flag["chain"],
            "reason": flag["reason"],
            "confidence_score": flag["confidence_score"],
            "amount_usd": flag.get("amount_usd"),
            "flagged_by": flag["org_name"],
            "timestamp": flag["flagged_at"]
        }
        
        # Broadcast to all active members
        for member in self.network_members.values():
            if member["is_active"]:
                await self._send_alert_to_member(member, alert)
    
    async def _send_alert_to_member(
        self,
        member: Dict[str, Any],
        alert: Dict[str, Any]
    ) -> None:
        """Send alert to a specific network member."""
        try:
            # TODO: Implement webhook delivery
            # if member["alert_webhook"]:
            #     async with httpx.AsyncClient() as client:
            #         await client.post(member["alert_webhook"], json=alert)
            
            member["alerts_received"] += 1
            logger.debug(f"Alert sent to {member['org_name']}: {alert['alert_type']}")
        except Exception as e:
            logger.error(f"Failed to send alert to {member['org_name']}: {e}")
    
    def _get_initial_trust_score(self, tier: InvestigatorTier) -> float:
        """Get initial trust score based on tier."""
        scores = {
            InvestigatorTier.VERIFIED_LAW_ENFORCEMENT: 1.0,
            InvestigatorTier.VERIFIED_EXCHANGE: 0.9,
            InvestigatorTier.VERIFIED_SECURITY_FIRM: 0.85,
            InvestigatorTier.VERIFIED_ANALYST: 0.75,
            InvestigatorTier.COMMUNITY_TRUSTED: 0.6
        }
        return scores.get(tier, 0.5)
    
    def _calculate_confidence_score(
        self,
        tier: str,
        evidence: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Calculate confidence score for a flag."""
        base_scores = {
            "verified_law_enforcement": 0.95,
            "verified_exchange": 0.85,
            "verified_security_firm": 0.80,
            "verified_analyst": 0.70,
            "community_trusted": 0.55
        }
        
        base = base_scores.get(tier, 0.5)
        
        # Boost confidence if evidence provided
        if evidence and len(evidence) > 0:
            evidence_boost = min(0.05 * len(evidence), 0.15)
            base = min(base + evidence_boost, 1.0)
        
        return round(base, 2)
    
    def _recalculate_confidence(self, flag: Dict[str, Any]) -> float:
        """Recalculate confidence score based on confirmations."""
        base = flag["confidence_score"]
        confirmations = flag["confirmations"]
        
        # Each additional confirmation boosts confidence
        boost = min(0.05 * (confirmations - 1), 0.2)
        
        return round(min(base + boost, 1.0), 2)
    
    def _calculate_aggregate_risk(
        self,
        direct_flags: List[Dict[str, Any]],
        related_flags: List[Dict[str, Any]]
    ) -> float:
        """Calculate aggregate risk score."""
        if not direct_flags and not related_flags:
            return 0.0
        
        # Direct flags have full weight
        direct_score = sum(flag["confidence_score"] for flag in direct_flags)
        
        # Related flags have reduced weight
        related_score = sum(flag["confidence_score"] * 0.3 for flag in related_flags)
        
        # Cap at 1.0
        total = min(direct_score + related_score, 1.0)
        
        return round(total, 2)
    
    def _determine_action(
        self,
        risk_score: float,
        direct_flags: List[Dict[str, Any]],
        related_flags: List[Dict[str, Any]]
    ) -> AlertAction:
        """Determine recommended action based on risk."""
        # Freeze if directly flagged with high confidence
        if direct_flags:
            max_confidence = max(flag["confidence_score"] for flag in direct_flags)
            if max_confidence >= 0.9:
                return AlertAction.FREEZE
            elif max_confidence >= 0.7:
                return AlertAction.REVIEW
        
        # Review if related to flagged addresses
        if related_flags and risk_score >= 0.5:
            return AlertAction.REVIEW
        
        # Monitor if low risk
        if risk_score >= 0.3:
            return AlertAction.MONITOR
        
        return AlertAction.ALLOW
    
    def _generate_flag_id(self, address: str, chain: str, investigator_id: str) -> str:
        """Generate unique flag ID."""
        data = f"{address.lower()}-{chain}-{investigator_id}-{datetime.utcnow().isoformat()}"
        return f"flag-{hashlib.sha256(data.encode()).hexdigest()[:16]}"
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """Get intelligence network statistics."""
        active_flags = [f for f in self.flags_db.values() if f["status"] == FlagStatus.ACTIVE.value]
        confirmed_flags = [f for f in self.flags_db.values() if f["status"] == FlagStatus.CONFIRMED.value]
        
        total_amount_flagged = sum(
            flag.get("amount_usd", 0) or 0
            for flag in active_flags + confirmed_flags
        )
        
        return {
            "total_investigators": len(self.investigators),
            "active_investigators": len([i for i in self.investigators.values() if i["is_active"]]),
            "total_network_members": len(self.network_members),
            "active_members": len([m for m in self.network_members.values() if m["is_active"]]),
            "total_flags": len(self.flags_db),
            "active_flags": len(active_flags),
            "confirmed_flags": len(confirmed_flags),
            "total_amount_flagged_usd": total_amount_flagged,
            "flags_by_reason": self._count_flags_by_reason(),
            "network_effectiveness": self._calculate_network_effectiveness()
        }
    
    def _count_flags_by_reason(self) -> Dict[str, int]:
        """Count flags by reason."""
        counts: Dict[str, int] = {}
        for flag in self.flags_db.values():
            reason = flag["reason"]
            counts[reason] = counts.get(reason, 0) + 1
        return counts
    
    def _calculate_network_effectiveness(self) -> float:
        """Calculate network effectiveness score."""
        if not self.flags_db:
            return 0.0
        
        confirmed = len([f for f in self.flags_db.values() if f["status"] == FlagStatus.CONFIRMED.value])
        total = len(self.flags_db)
        
        return round(confirmed / total, 2)


# Global service instance
intelligence_sharing_service = IntelligenceSharingService()
