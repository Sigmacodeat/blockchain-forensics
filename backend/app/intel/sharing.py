"""
Intelligence Sharing Network
============================

Peer-to-peer intelligence sharing network inspired by TRM Labs Beacon.

Features:
- Real-time threat intelligence sharing
- Organization-to-organization communication
- Trust scoring and reputation management
- Selective sharing (bilateral, multilateral, broadcast)
- Intelligence verification and validation
- Rate limiting and abuse prevention
"""
from __future__ import annotations
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from .models import (
    IntelSharingMessage,
    ThreatLevel,
    IntelCategory,
    ThreatIntelItem,
    IntelSource,
    TLPLevel
)

logger = logging.getLogger(__name__)


class OrganizationProfile:
    """Organization profile in the intel sharing network"""
    
    def __init__(self, org_id: str, name: str, org_type: str = "private"):
        self.org_id = org_id
        self.name = name
        self.org_type = org_type  # "private", "law_enforcement", "exchange", "government"
        
        # Reputation
        base_trust = {
            "law_enforcement": 0.8,
            "government": 0.75,
            "exchange": 0.65,
        }.get(org_type, 0.5)
        self.trust_score: float = base_trust  # 0.0 to 1.0
        self.messages_sent: int = 0
        self.messages_received: int = 0
        self.verified_intel_count: int = 0
        self.false_positives: int = 0
        
        # Network
        self.trusted_orgs: Set[str] = set()
        self.blocked_orgs: Set[str] = set()
        
        # Limits
        self.max_messages_per_hour: int = 100
        self.max_broadcast_per_day: int = 10
        
        # Stats
        self.joined_at: datetime = datetime.utcnow()
        self.last_active: datetime = datetime.utcnow()
        self.trust_history: List[Dict[str, Any]] = []
    
    def adjust_trust(self, delta: float, reason: str):
        """Adjust trust score with bounded history."""
        previous = self.trust_score
        self.trust_score = max(0.0, min(1.0, self.trust_score + delta))
        self.trust_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "delta": round(delta, 4),
            "reason": reason,
            "previous": round(previous, 4),
            "current": round(self.trust_score, 4),
        })
        if len(self.trust_history) > 100:
            self.trust_history = self.trust_history[-100:]
        return self.trust_score

    def update_reputation(self, verified: bool, weight: float = 1.0):
        """Update trust score based on intel verification"""
        if verified:
            self.verified_intel_count += 1
            self.adjust_trust(0.02 * weight, "intel_verified")
        else:
            self.false_positives += 1
            penalty = 0.05 + (0.02 * weight)
            self.adjust_trust(-penalty, "intel_disputed")


class IntelSharingNetwork:
    """
    Intelligence sharing network (like TRM Beacon).
    
    Enables organizations to share threat intelligence in real-time
    with trust scoring and selective sharing.
    """
    
    def __init__(self, network_name: str = "beacon"):
        self.network_name = network_name
        
        # Organizations
        self.organizations: Dict[str, OrganizationProfile] = {}
        
        # Messages
        self.messages: List[IntelSharingMessage] = []
        self.message_index: Dict[str, IntelSharingMessage] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, List[datetime]] = defaultdict(list)
        
        # Statistics
        self.total_messages: int = 0
        self.total_verifications: int = 0
    
    def register_organization(
        self,
        org_id: str,
        name: str,
        org_type: str = "private"
    ) -> OrganizationProfile:
        """
        Register an organization in the network.
        
        Args:
            org_id: Unique organization ID
            name: Organization name
            org_type: Type of organization
            
        Returns:
            Organization profile
        """
        if org_id in self.organizations:
            logger.warning(f"Organization {org_id} already registered")
            return self.organizations[org_id]
        
        org = OrganizationProfile(org_id, name, org_type)
        self.organizations[org_id] = org
        
        logger.info(f"Registered organization: {name} ({org_id})")
        return org
    
    def _check_rate_limit(self, org_id: str, limit_type: str = "hourly") -> bool:
        """Check if organization is within rate limits"""
        org = self.organizations.get(org_id)
        if not org:
            return False
        
        now = datetime.utcnow()
        
        if limit_type == "hourly":
            # Remove timestamps older than 1 hour
            cutoff = now - timedelta(hours=1)
            self.rate_limits[org_id] = [
                ts for ts in self.rate_limits[org_id] if ts > cutoff
            ]
            
            # Check limit
            if len(self.rate_limits[org_id]) >= org.max_messages_per_hour:
                return False
        
        return True
    
    async def share_intelligence(
        self,
        sender_org: str,
        threat_level: ThreatLevel,
        category: IntelCategory,
        title: str,
        description: str,
        indicators: Dict[str, List[str]],
        recipient_orgs: Optional[List[str]] = None,
        ttl_hours: int = 24,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[IntelSharingMessage]:
        """
        Share intelligence with network.
        
        Args:
            sender_org: Sending organization ID
            threat_level: Threat severity
            category: Intelligence category
            title: Intel title
            description: Intel description
            indicators: IOCs (e.g., {"addresses": ["0x..."], "domains": ["evil.com"]})
            recipient_orgs: Specific recipients (None = broadcast)
            ttl_hours: Time to live in hours
            metadata: Additional metadata
            
        Returns:
            Sharing message if successful
        """
        # Validate sender
        org = self.organizations.get(sender_org)
        if not org:
            logger.error(f"Unknown organization: {sender_org}")
            return None
        
        # Check rate limits
        if not self._check_rate_limit(sender_org):
            logger.warning(f"Rate limit exceeded for {sender_org}")
            return None
        
        # Check broadcast limit
        if not recipient_orgs:  # Broadcast
            broadcast_count = len([
                msg for msg in self.messages
                if msg.sender_org == sender_org
                and not msg.recipient_orgs
                and msg.shared_at > datetime.utcnow() - timedelta(days=1)
            ])
            
            if broadcast_count >= org.max_broadcast_per_day:
                logger.warning(f"Broadcast limit exceeded for {sender_org}")
                return None
        
        # Create message
        message = IntelSharingMessage(
            id=self._generate_message_id(sender_org),
            network=self.network_name,
            sender_org=sender_org,
            recipient_orgs=recipient_orgs or [],
            threat_level=threat_level,
            category=category,
            tlp=metadata.get("tlp") if metadata and metadata.get("tlp") else TLPLevel.AMBER,
            title=title,
            description=description,
            indicators=indicators,
            ttl_hours=ttl_hours,
            trust_score=org.trust_score,
            metadata=metadata or {}
        )
        
        # Store message
        self.messages.append(message)
        self.message_index[message.id] = message
        self.total_messages += 1
        
        # Update sender stats and trust (reward for sharing with higher trust recipients)
        org.messages_sent += 1
        org.last_active = datetime.utcnow()
        recipient_trust = [self.organizations[r].trust_score for r in message.recipient_orgs if r in self.organizations]
        if recipient_trust:
            avg_recipient_trust = sum(recipient_trust) / len(recipient_trust)
            reward = 0.01 * (avg_recipient_trust - org.trust_score)
            if reward:
                org.adjust_trust(reward, "share_to_trusted_recipients")
        
        # Record for rate limiting
        self.rate_limits[sender_org].append(datetime.utcnow())
        
        # Notify recipients
        await self._notify_recipients(message)
        
        logger.info(
            f"Intel shared by {sender_org}: {title} "
            f"({'broadcast' if not recipient_orgs else f'{len(recipient_orgs)} orgs'})"
        )
        
        return message
    
    def _generate_message_id(self, sender_org: str) -> str:
        """Generate unique message ID"""
        data = f"{sender_org}:{datetime.utcnow().isoformat()}:{self.total_messages}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def _notify_recipients(self, message: IntelSharingMessage):
        """Notify recipients of new intelligence"""
        # In production, this would:
        # 1. Send webhooks to recipients
        # 2. Update recipient dashboards
        # 3. Trigger alerts if high priority
        
        recipients = message.recipient_orgs or list(self.organizations.keys())
        
        for org_id in recipients:
            if org_id == message.sender_org:
                continue  # Don't notify sender
            
            org = self.organizations.get(org_id)
            if org:
                org.messages_received += 1
                
                # In production: send webhook, email, etc.
                logger.debug(f"Notified {org_id} of new intel: {message.title}")
    
    async def get_messages_for_org(
        self,
        org_id: str,
        category: Optional[IntelCategory] = None,
        threat_level: Optional[ThreatLevel] = None,
        include_expired: bool = False
    ) -> List[IntelSharingMessage]:
        """
        Get messages for an organization.
        
        Args:
            org_id: Organization ID
            category: Filter by category
            threat_level: Filter by threat level
            include_expired: Include expired messages
            
        Returns:
            List of messages
        """
        now = datetime.utcnow()
        messages = []
        
        for msg in self.messages:
            # Check if message is for this org
            is_broadcast = not msg.recipient_orgs
            is_recipient = org_id in msg.recipient_orgs
            
            if not (is_broadcast or is_recipient):
                continue
            
            # Check expiration
            if not include_expired and msg.expires_at and msg.expires_at < now:
                continue
            
            # Filter by category
            if category and msg.category != category:
                continue
            
            # Filter by threat level
            if threat_level and msg.threat_level != threat_level:
                continue
            
            messages.append(msg)
        
        # Sort by shared_at descending
        messages.sort(key=lambda m: m.shared_at, reverse=True)
        
        return messages
    
    async def verify_intelligence(
        self,
        message_id: str,
        verifier_org: str,
        is_verified: bool,
        notes: Optional[str] = None
    ) -> bool:
        """
        Verify intelligence from another organization.
        
        Args:
            message_id: Message ID
            verifier_org: Verifying organization ID
            is_verified: Whether intel is verified
            notes: Verification notes
            
        Returns:
            True if verification recorded
        """
        message = self.message_index.get(message_id)
        if not message:
            return False
        
        # Update sender reputation
        sender = self.organizations.get(message.sender_org)
        if sender:
            sender.update_reputation(is_verified)
        
        # Mark message as verified
        message.verified = is_verified
        
        self.total_verifications += 1
        
        logger.info(
            f"Intel {message_id} {'verified' if is_verified else 'disputed'} "
            f"by {verifier_org}"
        )
        
        return True
    
    async def convert_to_threat_intel(
        self,
        message: IntelSharingMessage
    ) -> List[ThreatIntelItem]:
        """
        Convert sharing message to threat intel items.
        
        Args:
            message: Sharing message
            
        Returns:
            List of threat intel items
        """
        items = []
        
        # Extract addresses
        for chain, addresses in message.indicators.items():
            if "address" not in chain.lower():
                continue
            
            chain_name = chain.replace("_addresses", "").replace("addresses", "ethereum")
            
            for address in addresses:
                item = ThreatIntelItem(
                    chain=chain_name,
                    address=address.lower(),
                    threat_level=message.threat_level,
                    category=message.category,
                    source=IntelSource.COMMUNITY,
                    title=message.title,
                    description=message.description,
                    confidence=message.trust_score,
                    metadata={
                        "shared_via": self.network_name,
                        "sender_org": message.sender_org,
                        "message_id": message.id,
                        **message.metadata
                    }
                )
                items.append(item)
        
        return items
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """Get network statistics"""
        active_orgs = sum(
            1 for org in self.organizations.values()
            if org.last_active > datetime.utcnow() - timedelta(days=7)
        )
        
        # Message stats by category
        by_category = defaultdict(int)
        by_threat_level = defaultdict(int)
        for msg in self.messages:
            by_category[msg.category] += 1
            by_threat_level[msg.threat_level] += 1
        
        return {
            "network_name": self.network_name,
            "total_organizations": len(self.organizations),
            "active_organizations": active_orgs,
            "total_messages": self.total_messages,
            "total_verifications": self.total_verifications,
            "messages_by_category": dict(by_category),
            "messages_by_threat_level": dict(by_threat_level),
            "avg_trust_score": sum(
                org.trust_score for org in self.organizations.values()
            ) / max(len(self.organizations), 1)
        }
    
    def trust_organization(self, org_id: str, trusted_org_id: str):
        """Add organization to trusted list"""
        org = self.organizations.get(org_id)
        if org:
            org.trusted_orgs.add(trusted_org_id)
    
    def block_organization(self, org_id: str, blocked_org_id: str):
        """Block organization"""
        org = self.organizations.get(org_id)
        if org:
            org.blocked_orgs.add(blocked_org_id)
            org.trusted_orgs.discard(blocked_org_id)


# Global network instance
_intel_network: Optional[IntelSharingNetwork] = None


def get_intel_network(network_name: str = "beacon") -> IntelSharingNetwork:
    """Get or create intel sharing network instance"""
    global _intel_network
    if _intel_network is None:
        _intel_network = IntelSharingNetwork(network_name)
        
        # Register demo organizations
        _intel_network.register_organization(
            "org_internal",
            "Internal Security Team",
            "private"
        )
        _intel_network.register_organization(
            "org_exchange_a",
            "Exchange A Security",
            "exchange"
        )
        _intel_network.register_organization(
            "org_law_enforcement",
            "Cybercrime Unit",
            "law_enforcement"
        )
    
    return _intel_network


def reset_intel_network():
    """Reset the global intel sharing network instance (for test isolation)."""
    global _intel_network
    _intel_network = None
