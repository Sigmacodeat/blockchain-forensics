"""
Threat Intelligence Service
===========================

Comprehensive threat intelligence service integrating:
- Multiple threat feeds (public and commercial)
- Dark web monitoring
- Intel sharing network (Beacon-style)
- Community intelligence (Signals-style)
- Automated enrichment

Inspired by Chainalysis, TRM Labs, Elliptic intelligence capabilities.
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

from .models import (
    ThreatIntelItem,
    CommunityIntelReport,
    IntelQuery,
    IntelStatistics,
    IntelEnrichmentResult,
    ThreatLevel,
    IntelCategory,
    IntelSource,
    IntelStatus,
    ThreatFeed
)
# Temporarily disabled due to missing bs4 dependency
# from .darkweb import get_darkweb_monitor, get_darkweb_store
from .sharing import get_intel_network
from .feeds import fetch_all_feeds

logger = logging.getLogger(__name__)


class ThreatIntelService:
    async def deconflict_intelligence(self, address: str, chain: str) -> Dict[str, Any]:
        """Deconflict conflicting intelligence from multiple sources with confidence fusion.
        
        Handles conflicts between sanctions vs threat intel, community vs commercial feeds.
        Returns fused intelligence with confidence score.
        """
        # Gather all intelligence for the address
        sanctions_data = await self.get_sanctions_intel(address, chain)
        threat_data = await self.get_threat_intel(address, chain)
        community_data = await self.get_community_intel(address, chain)
        
        # Deconflict logic
        return self._fuse_intelligence(address, chain, sanctions_data, threat_data, community_data)
    
    def _fuse_intelligence(self, address: str, chain: str, sanctions: Dict, threat: Dict, community: Dict) -> Dict[str, Any]:
        """Fuse intelligence from multiple sources with confidence weighting."""
        sources = [sanctions, threat, community]
        fused = {
            "address": address,
            "chain": chain,
            "is_high_risk": False,
            "confidence": 0.0,
            "categories": [],
            "sources": {
                "sanctions": bool(sanctions.get("hits")),
                "threat_feeds": bool(threat.get("hits")),
                "community": bool(community.get("reports"))
            },
            "conflicts_resolved": [],
            "fused_risk_level": "low"
        }
        
        # Confidence weights
        weights = {"sanctions": 0.8, "threat": 0.6, "community": 0.4}
        
        total_confidence = 0.0
        risk_indicators = 0
        
        for source_name, data, weight in [("sanctions", sanctions, weights["sanctions"]),
                                           ("threat", threat, weights["threat"]),
                                           ("community", community, weights["community"])]:
            if source_name == "sanctions" and data.get("hits"):
                fused["is_high_risk"] = True
                fused["confidence"] += weight
                fused["categories"].extend(["sanctions"] + data.get("categories", []))
                risk_indicators += 1
            elif source_name == "threat" and data.get("hits"):
                fused["is_high_risk"] = True
                fused["confidence"] += weight * 0.7  # Slightly lower for threat feeds
                fused["categories"].extend(data.get("categories", []))
                risk_indicators += 1
            elif source_name == "community" and data.get("reports"):
                # Community has lower weight, only if consistent with other sources
                if risk_indicators > 0:
                    fused["confidence"] += weight * 0.5
                    fused["categories"].extend(["community"] + [r.get("category") for r in data.get("reports", [])])
                    fused["conflicts_resolved"].append("community_consistent")
                else:
                    fused["conflicts_resolved"].append("community_ignored_low_confidence")
        
        # Normalize confidence
        fused["confidence"] = min(fused["confidence"], 1.0)
        
        # Determine fused risk level
        if fused["confidence"] >= 0.8:
            fused["fused_risk_level"] = "critical"
        elif fused["confidence"] >= 0.6:
            fused["fused_risk_level"] = "high"
        elif fused["confidence"] >= 0.4:
            fused["fused_risk_level"] = "medium"
        
        # De-duplicate categories
        fused["categories"] = list(set(fused["categories"]))
        
        return fused
    
    async def get_sanctions_intel(self, address: str, chain: str) -> Dict[str, Any]:
        """Get sanctions intelligence for address."""
        # Stub: integrate with sanctions service
        return {"hits": False, "categories": []}
    
    async def get_threat_intel(self, address: str, chain: str) -> Dict[str, Any]:
        """Get threat feed intelligence for address."""
        # Stub: integrate with feeds
        return {"hits": False, "categories": []}
    
    async def get_community_intel(self, address: str, chain: str) -> Dict[str, Any]:
        """Get community intelligence for address."""
        # Stub: integrate with sharing
        return {"reports": []}
    """
    Comprehensive threat intelligence service.
    
    Features:
    - Multi-source intelligence aggregation
    - Dark web monitoring integration
    - Intel sharing network (like TRM Beacon)
    - Community intelligence (like Chainalysis Signals)
    - Real-time enrichment
    - Automated feed updates
    """
    
    def __init__(self):
        # Storage (in-memory for demo, use database in production)
        self.intel_items: List[ThreatIntelItem] = []
        self.community_reports: List[CommunityIntelReport] = []
        self.threat_feeds: Dict[str, ThreatFeed] = {}
        
        # Indexes for fast lookup
        self.address_index: Dict[str, List[ThreatIntelItem]] = defaultdict(list)
        
        # External services
        # Temporarily disabled due to missing bs4 dependency
        # self.darkweb_monitor = get_darkweb_monitor()
        # self.darkweb_store = get_darkweb_store()
        self.intel_network = get_intel_network()
        
        # Stats
        self.last_update: Optional[datetime] = None
        self.total_feeds_processed: int = 0
    
    async def initialize(self):
        """Initialize service and load initial data"""
        logger.info("Initializing Threat Intelligence Service")
        
        # Register default threat feeds
        await self._register_default_feeds()
        
        # Initial data load
        await self.update_all_feeds()
        
        logger.info("Threat Intelligence Service initialized")
    
    async def _register_default_feeds(self):
        """Register default threat intelligence feeds"""
        default_feeds = [
            ThreatFeed(
                id="cryptoscamdb",
                name="CryptoScamDB",
                provider="CryptoScamDB",
                feed_type="api",
                url="https://api.cryptoscamdb.org/v1/scams",
                update_interval_minutes=60,
                default_confidence=0.9
            ),
            ThreatFeed(
                id="chainabuse",
                name="ChainAbuse",
                provider="ChainAbuse",
                feed_type="api",
                url="https://api.chainabuse.com/v0/reports",
                update_interval_minutes=30,
                default_confidence=0.8
            ),
            # Add more feeds as needed
        ]
        
        for feed in default_feeds:
            self.threat_feeds[feed.id] = feed
            logger.info(f"Registered threat feed: {feed.name}")
    
    async def update_all_feeds(self) -> Dict[str, Any]:
        """
        Update all threat intelligence feeds.
        
        Returns:
            Update statistics
        """
        logger.info("Updating all threat intelligence feeds")
        
        # Update public feeds
        feed_items = await fetch_all_feeds()
        
        # Update dark web monitoring
        darkweb_scan = await self.darkweb_monitor.run_full_scan()
        darkweb_items = darkweb_scan.get("items", [])
        
        # Store dark web intel
        await self.darkweb_store.store(darkweb_items)
        
        # Convert to ThreatIntelItems
        threat_items = []
        
        # From public feeds
        for item in feed_items:
            threat_item = ThreatIntelItem(
                chain=item.get("chain", "ethereum"),
                address=item.get("address", "").lower(),
                threat_level=ThreatLevel.MEDIUM,  # Default
                category=self._map_label_to_category(item.get("label", "suspicious")),
                source=IntelSource.OSINT,
                status=IntelStatus.ACTIVE,
                confidence=item.get("confidence", 0.7),
                title=f"{item.get('label', 'Suspicious')} address",
                description=item.get("metadata", {}).get("description", ""),
                metadata=item.get("metadata", {})
            )
            threat_items.append(threat_item)
        
        # From dark web
        for dwitem in darkweb_items:
            for address in dwitem.addresses:
                threat_item = ThreatIntelItem(
                    chain="ethereum",  # Assume ethereum for demo
                    address=address.lower(),
                    threat_level=ThreatLevel.HIGH,
                    category=dwitem.category,
                    source=IntelSource.DARK_WEB,
                    status=IntelStatus.ACTIVE,
                    confidence=dwitem.confidence,
                    title=dwitem.title,
                    description=dwitem.description,
                    metadata={
                        "marketplace": dwitem.marketplace,
                        "vendor": dwitem.vendor,
                        "discovered_at": dwitem.discovered_at.isoformat()
                    }
                )
                threat_items.append(threat_item)
        
        # Store items
        stored = await self._store_intel_items(threat_items)
        
        self.last_update = datetime.utcnow()
        self.total_feeds_processed += len(self.threat_feeds)
        
        return {
            "feeds_updated": len(self.threat_feeds),
            "items_fetched": len(feed_items) + len(darkweb_items),
            "items_stored": stored,
            "darkweb_scan": darkweb_scan,
            "timestamp": self.last_update.isoformat()
        }
    
    def _map_label_to_category(self, label: str) -> IntelCategory:
        """Map label to intelligence category"""
        label_lower = label.lower()
        
        mapping = {
            "scam": IntelCategory.SCAM,
            "phishing": IntelCategory.PHISHING,
            "ransomware": IntelCategory.RANSOMWARE,
            "mixer": IntelCategory.MIXER,
            "darknet": IntelCategory.DARKNET_MARKET,
            "hack": IntelCategory.HACK,
            "fraud": IntelCategory.FRAUD,
            "sanctions": IntelCategory.SANCTIONS,
        }
        
        for key, category in mapping.items():
            if key in label_lower:
                return category
        
        return IntelCategory.FRAUD  # Default
    
    async def _store_intel_items(self, items: List[ThreatIntelItem]) -> int:
        """Store intelligence items with deduplication"""
        stored = 0
        
        for item in items:
            # Simple deduplication by address
            key = f"{item.chain}:{item.address}"
            
            # Check if exists
            existing = [
                i for i in self.intel_items
                if i.chain == item.chain and i.address == item.address
                and i.category == item.category
            ]
            
            if not existing:
                self.intel_items.append(item)
                self.address_index[key].append(item)
                stored += 1
        
        return stored
    
    async def enrich_address(
        self,
        chain: str,
        address: str
    ) -> IntelEnrichmentResult:
        """
        Enrich an address with threat intelligence.
        
        Args:
            chain: Blockchain
            address: Address to enrich
            
        Returns:
            Enrichment result with all intelligence
        """
        address = address.lower()
        key = f"{chain}:{address}"
        
        # Find matches
        matches = self.address_index.get(key, [])
        
        # Also check dark web store
        darkweb_matches = await self.darkweb_store.search(address=address)
        
        # Aggregate
        if not matches and not darkweb_matches:
            return IntelEnrichmentResult(
                chain=chain,
                address=address,
                matches=[],
                threat_score=0.0,
                confidence=0.0,
                recommended_action="allow"
            )
        
        # Calculate scores
        threat_scores = []
        confidences = []
        categories = set()
        sources = set()
        threat_levels = []
        
        for match in matches:
            # Threat level to score
            level_scores = {
                ThreatLevel.CRITICAL: 1.0,
                ThreatLevel.HIGH: 0.8,
                ThreatLevel.MEDIUM: 0.5,
                ThreatLevel.LOW: 0.3,
                ThreatLevel.INFO: 0.1
            }
            
            threat_scores.append(level_scores.get(match.threat_level, 0.5) * match.confidence)
            confidences.append(match.confidence)
            categories.add(match.category)
            sources.add(match.source)
            threat_levels.append(match.threat_level)
        
        # Overall scores
        avg_threat = sum(threat_scores) / len(threat_scores) if threat_scores else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Highest threat level
        level_priority = {
            ThreatLevel.CRITICAL: 5,
            ThreatLevel.HIGH: 4,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.LOW: 2,
            ThreatLevel.INFO: 1
        }
        highest_threat = max(threat_levels, key=lambda x: level_priority.get(x, 0)) if threat_levels else None
        
        # Recommended action
        if avg_threat >= 0.8:
            action = "block"
        elif avg_threat >= 0.5:
            action = "alert"
        elif avg_threat >= 0.3:
            action = "monitor"
        else:
            action = "allow"
        
        # Risk factors
        risk_factors = []
        if IntelCategory.RANSOMWARE in categories:
            risk_factors.append("Associated with ransomware")
        if IntelCategory.SANCTIONS in categories:
            risk_factors.append("Sanctioned entity")
        if IntelSource.DARK_WEB in sources:
            risk_factors.append("Found on dark web")
        if IntelSource.LAW_ENFORCEMENT in sources:
            risk_factors.append("Law enforcement intelligence")
        
        return IntelEnrichmentResult(
            chain=chain,
            address=address,
            matches=matches,
            highest_threat_level=highest_threat,
            threat_score=avg_threat,
            confidence=avg_confidence,
            categories=list(categories),
            sources=list(sources),
            recommended_action=action,
            risk_factors=risk_factors
        )
    
    async def submit_community_report(
        self,
        reporter_id: str,
        chain: str,
        address: str,
        category: IntelCategory,
        threat_level: ThreatLevel,
        title: str,
        description: str,
        evidence: Optional[Dict[str, Any]] = None
    ) -> CommunityIntelReport:
        """
        Submit community intelligence report (like Chainalysis Signals).
        
        Args:
            reporter_id: User submitting report
            chain: Blockchain
            address: Address to report
            category: Threat category
            threat_level: Severity
            title: Report title
            description: Detailed description
            evidence: Supporting evidence
            
        Returns:
            Created report
        """
        report = CommunityIntelReport(
            reporter_id=reporter_id,
            chain=chain,
            address=address.lower(),
            category=category,
            threat_level=threat_level,
            title=title,
            description=description,
            evidence=evidence or {}
        )
        
        self.community_reports.append(report)
        
        logger.info(f"Community report submitted: {title} by {reporter_id}")
        
        return report
    
    async def query_intelligence(self, query: IntelQuery) -> List[ThreatIntelItem]:
        """
        Query threat intelligence.
        
        Args:
            query: Query parameters
            
        Returns:
            Matching intelligence items
        """
        results = self.intel_items
        
        # Filter by chains
        if query.chains:
            results = [item for item in results if item.chain in query.chains]
        
        # Filter by addresses
        if query.addresses:
            addr_set = set(a.lower() for a in query.addresses)
            results = [item for item in results if item.address in addr_set]
        
        # Filter by categories
        if query.categories:
            results = [item for item in results if item.category in query.categories]
        
        # Filter by sources
        if query.sources:
            results = [item for item in results if item.source in query.sources]
        
        # Filter by threat levels
        if query.threat_levels:
            results = [item for item in results if item.threat_level in query.threat_levels]
        
        # Filter by status
        if query.statuses:
            results = [item for item in results if item.status in query.statuses]
        
        # Filter by confidence
        if query.min_confidence:
            results = [item for item in results if item.confidence >= query.min_confidence]
        
        # Filter by dates
        if query.from_date:
            results = [item for item in results if item.first_seen >= query.from_date]
        if query.to_date:
            results = [item for item in results if item.first_seen <= query.to_date]
        
        # Search in title/description
        if query.search:
            search_lower = query.search.lower()
            results = [
                item for item in results
                if search_lower in item.title.lower()
                or (item.description and search_lower in item.description.lower())
            ]
        
        # Pagination
        total = len(results)
        results = results[query.offset:query.offset + query.limit]
        
        return results
    
    async def get_statistics(self) -> IntelStatistics:
        """Get threat intelligence statistics"""
        if not self.intel_items:
            return IntelStatistics(
                total_items=0,
                by_category={},
                by_source={},
                by_threat_level={},
                by_status={},
                avg_confidence=0.0,
                verified_percentage=0.0,
                active_feeds=len([f for f in self.threat_feeds.values() if f.enabled]),
                community_reports=len(self.community_reports),
                darkweb_alerts=0
            )
        
        # Aggregate stats
        by_category = defaultdict(int)
        by_source = defaultdict(int)
        by_threat_level = defaultdict(int)
        by_status = defaultdict(int)
        
        total_confidence = 0.0
        verified_count = 0
        
        for item in self.intel_items:
            by_category[item.category] += 1
            by_source[item.source] += 1
            by_threat_level[item.threat_level] += 1
            by_status[item.status] += 1
            
            total_confidence += item.confidence
            
            if item.status == IntelStatus.VERIFIED:
                verified_count += 1
        
        # Dark web stats
        dw_stats = await self.darkweb_store.get_statistics()
        
        return IntelStatistics(
            total_items=len(self.intel_items),
            by_category=dict(by_category),
            by_source=dict(by_source),
            by_threat_level=dict(by_threat_level),
            by_status=dict(by_status),
            avg_confidence=total_confidence / len(self.intel_items),
            verified_percentage=(verified_count / len(self.intel_items)) * 100,
            active_feeds=len([f for f in self.threat_feeds.values() if f.enabled]),
            community_reports=len(self.community_reports),
            darkweb_alerts=dw_stats.get("total_items", 0)
        )
    
    async def share_intel_via_network(
        self,
        sender_org: str,
        intel_item: ThreatIntelItem,
        recipient_orgs: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Share intelligence via intel sharing network.
        
        Args:
            sender_org: Sending organization
            intel_item: Intelligence to share
            recipient_orgs: Recipients (None = broadcast)
            
        Returns:
            Message ID if successful
        """
        # Prepare indicators
        indicators = {
            f"{intel_item.chain}_addresses": [intel_item.address]
        }
        
        # Add related addresses
        if intel_item.related_addresses:
            indicators[f"{intel_item.chain}_addresses"].extend(intel_item.related_addresses)
        
        # Share via network
        message = await self.intel_network.share_intelligence(
            sender_org=sender_org,
            threat_level=intel_item.threat_level,
            category=intel_item.category,
            title=intel_item.title,
            description=intel_item.description or "",
            indicators=indicators,
            recipient_orgs=recipient_orgs,
            metadata=intel_item.metadata
        )
        
        return message.id if message else None


# Global service instance
_threat_intel_service: Optional[ThreatIntelService] = None


def get_threat_intel_service() -> ThreatIntelService:
    """Get or create threat intelligence service instance"""
    global _threat_intel_service
    if _threat_intel_service is None:
        _threat_intel_service = ThreatIntelService()
    return _threat_intel_service


# Legacy compatibility
class IntelService:
    """Legacy stub for backward compatibility"""
    def __init__(self) -> None:
        self._service = get_threat_intel_service()
    
    def publish(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy publish method"""
        import time
        event.setdefault("id", f"evt_{int(time.time())}")
        event.setdefault("ts", int(time.time()))
        return event
    
    def policies(self) -> List[Dict[str, Any]]:
        """Legacy policies method"""
        return [
            {"id": "default", "name": "Default Policy", "rules": [], "approvers": [], "status": "active"}
        ]


intel_service = IntelService()
