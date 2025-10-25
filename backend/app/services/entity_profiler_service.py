"""
Entity Profiler Service with OSINT Integration

Comprehensive entity profiling combining blockchain data with OSINT.
Similar to Chainalysis Reactor's Entity Profiler.

Features:
- Multi-source data aggregation
- OSINT integration (social media, websites, registries)
- Entity relationship mapping
- Behavior pattern analysis
- Attribution scoring
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of blockchain entities"""
    EXCHANGE = "exchange"
    MIXER = "mixer"
    GAMBLING = "gambling"
    MARKETPLACE = "marketplace"
    SCAM = "scam"
    RANSOMWARE = "ransomware"
    DARKNET_SERVICE = "darknet_service"
    DEFI_PROTOCOL = "defi_protocol"
    BRIDGE = "bridge"
    PAYMENT_PROCESSOR = "payment_processor"
    MERCHANT = "merchant"
    INDIVIDUAL = "individual"
    CUSTODIAN = "custodian"
    MINING_POOL = "mining_pool"
    UNKNOWN = "unknown"


class AttributionConfidence(str, Enum):
    """Confidence level for entity attribution"""
    CONFIRMED = "confirmed"  # 95-100%
    HIGH = "high"  # 80-94%
    MEDIUM = "medium"  # 60-79%
    LOW = "low"  # 40-59%
    SPECULATIVE = "speculative"  # <40%


class OSINTSource(str, Enum):
    """OSINT data sources"""
    TWITTER = "twitter"
    GITHUB = "github"
    LINKEDIN = "linkedin"
    COMPANY_REGISTRY = "company_registry"
    WHOIS = "whois"
    DNS = "dns"
    WEBSITE = "website"
    REDDIT = "reddit"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    BLOCKCHAIN_EXPLORER = "blockchain_explorer"
    NEWS = "news"


class EntityProfilerService:
    """
    Entity Profiler with OSINT integration.
    
    Architecture:
    - Multi-source data aggregation
    - Pattern-based entity recognition
    - Relationship graph building
    - Confidence scoring
    """
    
    def __init__(self):
        self.entity_cache: Dict[str, Dict[str, Any]] = {}
        
    async def profile_entity(
        self,
        address: str,
        chain: str = "ethereum",
        include_osint: bool = True,
        include_relationships: bool = True,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Create comprehensive entity profile.
        
        Args:
            address: Blockchain address
            chain: Chain ID
            include_osint: Include OSINT data
            include_relationships: Include relationship graph
            depth: Relationship graph depth
            
        Returns:
            Comprehensive entity profile
        """
        cache_key = f"{chain}:{address.lower()}"
        
        # Check cache
        if cache_key in self.entity_cache:
            cached = self.entity_cache[cache_key]
            age = (datetime.utcnow() - datetime.fromisoformat(cached["profiled_at"])).seconds
            if age < 3600:  # 1 hour cache
                logger.info(f"Returning cached profile: {cache_key}")
                return cached
        
        # Gather blockchain data
        blockchain_data = await self._gather_blockchain_data(address, chain)
        
        # Detect entity type
        entity_type = self._detect_entity_type(blockchain_data)
        
        # OSINT enrichment
        osint_data = {}
        if include_osint:
            osint_data = await self._gather_osint(address, chain, entity_type)
        
        # Behavioral analysis
        behavior = await self._analyze_behavior(blockchain_data)
        
        # Relationships
        relationships = {}
        if include_relationships:
            relationships = await self._build_relationship_graph(
                address, chain, depth
            )
        
        # Attribution
        attribution = self._determine_attribution(
            blockchain_data,
            osint_data,
            behavior
        )
        
        # Risk assessment
        risk = await self._assess_entity_risk(
            entity_type,
            blockchain_data,
            osint_data,
            behavior
        )
        
        profile = {
            "address": address.lower(),
            "chain": chain,
            "entity_type": entity_type.value,
            "attribution": attribution,
            "blockchain_data": blockchain_data,
            "osint_data": osint_data,
            "behavior_analysis": behavior,
            "relationships": relationships,
            "risk_assessment": risk,
            "profiled_at": datetime.utcnow().isoformat(),
            "profile_id": self._generate_profile_id(address, chain)
        }
        
        # Cache profile
        self.entity_cache[cache_key] = profile
        
        logger.info(f"Entity profiled: {address} - Type: {entity_type.value}")
        
        return profile
    
    async def _gather_blockchain_data(
        self,
        address: str,
        chain: str
    ) -> Dict[str, Any]:
        """Gather blockchain activity data."""
        # TODO: Integrate with existing services
        # - Transaction history
        # - Balance & holdings
        # - Counterparty analysis
        # - Labels from enrichment service
        
        return {
            "first_seen": "2020-01-01T00:00:00Z",
            "last_seen": datetime.utcnow().isoformat(),
            "total_transactions": 1250,
            "total_volume_usd": 5000000,
            "unique_counterparties": 324,
            "balance_usd": 50000,
            "top_tokens": ["ETH", "USDT", "USDC"],
            "labels": [],
            "is_contract": False
        }
    
    async def _gather_osint(
        self,
        address: str,
        chain: str,
        entity_type: EntityType
    ) -> Dict[str, Any]:
        """Gather OSINT data from multiple sources."""
        osint = {
            "sources_checked": [],
            "findings": []
        }
        
        # Check common OSINT sources
        sources_to_check = [
            OSINTSource.TWITTER,
            OSINTSource.GITHUB,
            OSINTSource.WEBSITE,
            OSINTSource.BLOCKCHAIN_EXPLORER,
            OSINTSource.NEWS
        ]
        
        for source in sources_to_check:
            finding = await self._check_osint_source(address, chain, source)
            if finding:
                osint["findings"].append(finding)
            osint["sources_checked"].append(source.value)
        
        # Extract key information
        osint["identified_names"] = self._extract_names(osint["findings"])
        osint["social_profiles"] = self._extract_social_profiles(osint["findings"])
        osint["websites"] = self._extract_websites(osint["findings"])
        osint["news_mentions"] = self._extract_news_mentions(osint["findings"])
        
        return osint
    
    async def _check_osint_source(
        self,
        address: str,
        chain: str,
        source: OSINTSource
    ) -> Optional[Dict[str, Any]]:
        """Check a specific OSINT source."""
        # Mock implementation - in production, integrate with real APIs
        
        if source == OSINTSource.TWITTER:
            # Search Twitter for address mentions
            return {
                "source": source.value,
                "data_type": "social_profile",
                "confidence": AttributionConfidence.MEDIUM.value,
                "data": {
                    "platform": "twitter",
                    "mentions": 5,
                    "last_mention": datetime.utcnow().isoformat()
                }
            }
        
        elif source == OSINTSource.BLOCKCHAIN_EXPLORER:
            # Check blockchain explorers for tags
            return {
                "source": source.value,
                "data_type": "explorer_tag",
                "confidence": AttributionConfidence.HIGH.value,
                "data": {
                    "platform": "etherscan",
                    "tags": []
                }
            }
        
        return None
    
    def _detect_entity_type(self, blockchain_data: Dict[str, Any]) -> EntityType:
        """Detect entity type from blockchain patterns."""
        # Pattern-based detection
        tx_count = blockchain_data.get("total_transactions", 0)
        volume = blockchain_data.get("total_volume_usd", 0)
        counterparties = blockchain_data.get("unique_counterparties", 0)
        labels = blockchain_data.get("labels", [])
        
        # Check labels first
        for label in labels:
            label_lower = str(label).lower()
            if "exchange" in label_lower:
                return EntityType.EXCHANGE
            elif "mixer" in label_lower:
                return EntityType.MIXER
            elif "defi" in label_lower:
                return EntityType.DEFI_PROTOCOL
            elif "bridge" in label_lower:
                return EntityType.BRIDGE
        
        # Pattern-based detection
        if tx_count > 10000 and counterparties > 1000:
            # High activity, many counterparties = likely exchange/service
            if volume > 10_000_000:
                return EntityType.EXCHANGE
            else:
                return EntityType.PAYMENT_PROCESSOR
        
        elif blockchain_data.get("is_contract"):
            # Smart contract
            if volume > 1_000_000:
                return EntityType.DEFI_PROTOCOL
            else:
                return EntityType.UNKNOWN
        
        elif tx_count < 100:
            # Low activity = likely individual
            return EntityType.INDIVIDUAL
        
        return EntityType.UNKNOWN
    
    async def _analyze_behavior(
        self,
        blockchain_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze behavioral patterns."""
        return {
            "activity_pattern": "regular",  # regular, sporadic, burst
            "time_pattern": "24/7",  # 24/7, business_hours, specific_times
            "transaction_patterns": {
                "avg_value_usd": blockchain_data.get("total_volume_usd", 0) / max(blockchain_data.get("total_transactions", 1), 1),
                "value_distribution": "varied",  # consistent, varied, outliers
                "frequency": "high"  # low, medium, high
            },
            "counterparty_patterns": {
                "repeat_ratio": 0.3,  # % of repeat counterparties
                "clustering": "dispersed"  # clustered, dispersed
            },
            "gas_behavior": {
                "avg_gas_price": "medium",
                "priority_usage": "occasional"
            }
        }
    
    async def _build_relationship_graph(
        self,
        address: str,
        chain: str,
        depth: int
    ) -> Dict[str, Any]:
        """Build relationship graph."""
        # TODO: Integrate with graph service
        
        return {
            "depth": depth,
            "total_nodes": 0,
            "direct_connections": [],
            "indirect_connections": [],
            "clusters": []
        }
    
    def _determine_attribution(
        self,
        blockchain_data: Dict[str, Any],
        osint_data: Dict[str, Any],
        behavior: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine entity attribution with confidence scoring."""
        # Collect attribution signals
        signals = []
        
        # From labels
        labels = blockchain_data.get("labels", [])
        if labels:
            signals.append({
                "type": "label",
                "value": labels[0],
                "confidence": AttributionConfidence.HIGH.value,
                "source": "blockchain_labels"
            })
        
        # From OSINT
        names = osint_data.get("identified_names", [])
        if names:
            signals.append({
                "type": "name",
                "value": names[0],
                "confidence": AttributionConfidence.MEDIUM.value,
                "source": "osint"
            })
        
        # Calculate overall confidence
        if len(signals) >= 3:
            overall_confidence = AttributionConfidence.HIGH
        elif len(signals) >= 2:
            overall_confidence = AttributionConfidence.MEDIUM
        elif len(signals) == 1:
            overall_confidence = AttributionConfidence.LOW
        else:
            overall_confidence = AttributionConfidence.SPECULATIVE
        
        return {
            "confidence": overall_confidence.value,
            "signals": signals,
            "attributed_name": names[0] if names else None,
            "attributed_entity_type": None,
            "attribution_methods": [s["source"] for s in signals]
        }
    
    async def _assess_entity_risk(
        self,
        entity_type: EntityType,
        blockchain_data: Dict[str, Any],
        osint_data: Dict[str, Any],
        behavior: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess entity risk level."""
        risk_score = 0.0
        risk_factors = []
        
        # High-risk entity types
        if entity_type in [EntityType.MIXER, EntityType.SCAM, EntityType.RANSOMWARE, EntityType.DARKNET_SERVICE]:
            risk_score += 0.8
            risk_factors.append(f"High-risk entity type: {entity_type.value}")
        
        # High volume
        volume = blockchain_data.get("total_volume_usd", 0)
        if volume > 10_000_000:
            risk_score += 0.2
            risk_factors.append(f"High transaction volume: ${volume:,.0f}")
        
        # Suspicious behavior
        if behavior["activity_pattern"] == "burst":
            risk_score += 0.3
            risk_factors.append("Burst activity pattern")
        
        # Lack of attribution
        if not osint_data.get("identified_names"):
            risk_score += 0.2
            risk_factors.append("No OSINT attribution found")
        
        risk_score = min(risk_score, 1.0)
        
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommended_actions": self._generate_risk_actions(risk_level)
        }
    
    def _generate_risk_actions(self, risk_level: str) -> List[str]:
        """Generate recommended actions based on risk."""
        if risk_level == "high":
            return [
                "⚠️ Enhanced due diligence required",
                "Flag for AML review",
                "Consider transaction monitoring"
            ]
        elif risk_level == "medium":
            return [
                "Additional verification recommended",
                "Review transaction patterns"
            ]
        else:
            return ["Standard monitoring sufficient"]
    
    def _extract_names(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Extract identified names from OSINT findings."""
        names = []
        for finding in findings:
            if finding.get("data_type") == "name":
                names.append(finding["data"].get("name"))
        return [n for n in names if n]
    
    def _extract_social_profiles(self, findings: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract social media profiles."""
        profiles = []
        for finding in findings:
            if finding.get("data_type") == "social_profile":
                profiles.append({
                    "platform": finding["data"].get("platform"),
                    "handle": finding["data"].get("handle"),
                    "url": finding["data"].get("url")
                })
        return profiles
    
    def _extract_websites(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Extract associated websites."""
        websites = []
        for finding in findings:
            if finding.get("data_type") == "website":
                websites.append(finding["data"].get("url"))
        return [w for w in websites if w]
    
    def _extract_news_mentions(self, findings: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract news mentions."""
        mentions = []
        for finding in findings:
            if finding.get("data_type") == "news":
                mentions.append({
                    "title": finding["data"].get("title"),
                    "url": finding["data"].get("url"),
                    "date": finding["data"].get("date")
                })
        return mentions
    
    def _generate_profile_id(self, address: str, chain: str) -> str:
        """Generate unique profile ID."""
        data = f"{chain}:{address.lower()}:{datetime.utcnow().date()}"
        return f"profile-{hashlib.sha256(data.encode()).hexdigest()[:16]}"
    
    async def bulk_profile(
        self,
        addresses: List[Dict[str, str]],
        include_osint: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Bulk profile multiple entities.
        
        Args:
            addresses: List of {address, chain} dicts
            include_osint: Include OSINT (slower)
            
        Returns:
            List of profiles
        """
        import asyncio
        
        tasks = [
            self.profile_entity(
                address=addr["address"],
                chain=addr.get("chain", "ethereum"),
                include_osint=include_osint,
                include_relationships=False
            )
            for addr in addresses
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        logger.info(f"Bulk profiling completed: {len(valid_results)}/{len(addresses)} successful")
        
        return valid_results


# Global service instance
entity_profiler_service = EntityProfilerService()
