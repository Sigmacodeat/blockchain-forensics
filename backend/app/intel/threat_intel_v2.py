"""
Threat Intel v2 - Normalizer Plugins, TLP/Sharing, Advanced Deconfliction

Features:
- Normalizer Plugins für verschiedene Feed-Formate
- TLP (Traffic Light Protocol) für Sharing
- Deconfliction mit Sanctions/Intel Integration
- Scoring und Confidence-Fusion
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib

from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class TLPLevel(str, Enum):
    """Traffic Light Protocol Levels"""
    RED = "red"  # Do not share
    AMBER = "amber"  # Share within organization only
    GREEN = "green"  # Share with community
    WHITE = "white"  # Share publicly


class IntelConfidence(str, Enum):
    """Confidence Levels for Intelligence"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class NormalizedIntelItem:
    """Normalized Intelligence Item"""
    intel_id: str
    address: str
    chain: str
    category: str
    risk_score: float
    confidence: IntelConfidence
    tlp_level: TLPLevel
    source: str
    raw_data: Dict[str, Any]
    normalized_data: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    tags: Set[str] = field(default_factory=set)


@dataclass
class IntelNormalizerPlugin:
    """Plugin for normalizing different intelligence formats"""
    name: str
    source_type: str
    confidence_weight: float = 1.0

    def normalize(self, raw_data: Dict[str, Any]) -> Optional[NormalizedIntelItem]:
        """Normalize raw intelligence data"""
        raise NotImplementedError


class ChainalysisNormalizer(IntelNormalizerPlugin):
    """Normalizer for Chainalysis-style feeds"""

    def __init__(self):
        super().__init__("chainalysis", "chainalysis", 0.9)

    def normalize(self, raw_data: Dict[str, Any]) -> Optional[NormalizedIntelItem]:
        # Chainalysis format normalization
        if "address" not in raw_data:
            return None

        return NormalizedIntelItem(
            intel_id=f"chainalysis_{hashlib.sha256(str(raw_data).encode()).hexdigest()[:16]}",
            address=raw_data["address"],
            chain=raw_data.get("chain", "ethereum"),
            category=raw_data.get("category", "unknown"),
            risk_score=float(raw_data.get("risk_score", 0.5)),
            confidence=IntelConfidence.HIGH,
            tlp_level=TLPLevel.GREEN,
            source="chainalysis",
            raw_data=raw_data,
            normalized_data={
                "entity": raw_data.get("entity"),
                "risk_factors": raw_data.get("risk_factors", []),
                "exposure": raw_data.get("exposure", {}),
            },
            created_at=datetime.now(),
            tags=set(raw_data.get("tags", []))
        )


class TRMNormalizer(IntelNormalizerPlugin):
    """Normalizer for TRM Labs feeds"""

    def __init__(self):
        super().__init__("trm", "trm", 0.8)

    def normalize(self, raw_data: Dict[str, Any]) -> Optional[NormalizedIntelItem]:
        if "address" not in raw_data:
            return None

        # TRM specific mapping
        risk_mapping = {
            "Severe": 1.0,
            "High": 0.8,
            "Medium": 0.6,
            "Low": 0.3,
            "Unknown": 0.1
        }

        risk_level = raw_data.get("risk_level", "Unknown")
        risk_score = risk_mapping.get(risk_level, 0.1)

        return NormalizedIntelItem(
            intel_id=f"trm_{hashlib.sha256(str(raw_data).encode()).hexdigest()[:16]}",
            address=raw_data["address"],
            chain=raw_data.get("chain", "bitcoin"),
            category=raw_data.get("category", "unknown"),
            risk_score=risk_score,
            confidence=IntelConfidence.MEDIUM,
            tlp_level=TLPLevel.AMBER,
            source="trm",
            raw_data=raw_data,
            normalized_data={
                "entity_type": raw_data.get("entity_type"),
                "risk_level": risk_level,
                "indicators": raw_data.get("indicators", []),
            },
            created_at=datetime.now(),
            tags=set(raw_data.get("tags", []))
        )


class CommunityNormalizer(IntelNormalizerPlugin):
    """Normalizer for community intelligence"""

    def __init__(self):
        super().__init__("community", "community", 0.6)

    def normalize(self, raw_data: Dict[str, Any]) -> Optional[NormalizedIntelItem]:
        if "address" not in raw_data:
            return None

        return NormalizedIntelItem(
            intel_id=f"community_{hashlib.sha256(str(raw_data).encode()).hexdigest()[:16]}",
            address=raw_data["address"],
            chain=raw_data.get("chain", "ethereum"),
            category=raw_data.get("category", "community_report"),
            risk_score=float(raw_data.get("risk_score", 0.4)),
            confidence=IntelConfidence.LOW,
            tlp_level=TLPLevel.WHITE,
            source="community",
            raw_data=raw_data,
            normalized_data={
                "reporter": raw_data.get("reporter"),
                "description": raw_data.get("description"),
                "evidence": raw_data.get("evidence", []),
            },
            created_at=datetime.now(),
            tags=set(["community"])
        )


class ThreatIntelV2Service:
    """Enhanced Threat Intelligence Service"""

    def __init__(self):
        self.normalizers: Dict[str, IntelNormalizerPlugin] = {}
        self.intel_cache: Dict[str, NormalizedIntelItem] = {}
        self.tlp_policies: Dict[TLPLevel, Dict[str, Any]] = self._init_tlp_policies()

        # Register default normalizers
        self.register_normalizer(ChainalysisNormalizer())
        self.register_normalizer(TRMNormalizer())
        self.register_normalizer(CommunityNormalizer())

    def _init_tlp_policies(self) -> Dict[TLPLevel, Dict[str, Any]]:
        """Initialize TLP sharing policies"""
        return {
            TLPLevel.RED: {
                "can_share": False,
                "share_with_org": False,
                "share_with_community": False,
                "retention_days": 365,
                "auto_expire": True
            },
            TLPLevel.AMBER: {
                "can_share": True,
                "share_with_org": True,
                "share_with_community": False,
                "retention_days": 180,
                "auto_expire": True
            },
            TLPLevel.GREEN: {
                "can_share": True,
                "share_with_org": True,
                "share_with_community": True,
                "retention_days": 90,
                "auto_expire": True
            },
            TLPLevel.WHITE: {
                "can_share": True,
                "share_with_org": True,
                "share_with_community": True,
                "share_publicly": True,
                "retention_days": 30,
                "auto_expire": False
            }
        }

    def register_normalizer(self, normalizer: IntelNormalizerPlugin):
        """Register a new normalizer plugin"""
        self.normalizers[normalizer.name] = normalizer
        logger.info(f"Registered normalizer: {normalizer.name} for {normalizer.source_type}")

    def unregister_normalizer(self, name: str):
        """Unregister a normalizer plugin"""
        if name in self.normalizers:
            del self.normalizers[name]
            logger.info(f"Unregistered normalizer: {name}")

    async def normalize_intel(self, raw_data: Dict[str, Any], source_type: str) -> Optional[NormalizedIntelItem]:
        """Normalize intelligence using appropriate plugin"""
        normalizer = self.normalizers.get(source_type)
        if not normalizer:
            logger.warning(f"No normalizer found for source type: {source_type}")
            return None

        try:
            normalized = normalizer.normalize(raw_data)
            if normalized:
                # Apply TLP policies
                self._apply_tlp_policy(normalized)

                # Cache normalized item
                cache_key = f"intel:{normalized.address}:{normalized.chain}"
                await self._cache_intel_item(cache_key, normalized)

            return normalized
        except Exception as e:
            logger.error(f"Normalization failed for {source_type}: {e}")
            return None

    def _apply_tlp_policy(self, item: NormalizedIntelItem):
        """Apply TLP policy to normalized item"""
        policy = self.tlp_policies.get(item.tlp_level, self.tlp_policies[TLPLevel.WHITE])

        if policy.get("auto_expire", False):
            retention_days = policy.get("retention_days", 30)
            item.expires_at = datetime.now() + timedelta(days=retention_days)

    async def _cache_intel_item(self, key: str, item: NormalizedIntelItem, ttl: int = 3600):
        """Cache normalized intel item"""
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client:
                data = {
                    "intel_id": item.intel_id,
                    "address": item.address,
                    "chain": item.chain,
                    "category": item.category,
                    "risk_score": item.risk_score,
                    "confidence": item.confidence.value,
                    "tlp_level": item.tlp_level.value,
                    "source": item.source,
                    "normalized_data": item.normalized_data,
                    "created_at": item.created_at.isoformat(),
                    "expires_at": item.expires_at.isoformat() if item.expires_at else None,
                    "tags": list(item.tags)
                }
                await client.setex(key, ttl, json.dumps(data))
        except Exception:
            pass

    async def get_intel_item(self, address: str, chain: str) -> Optional[NormalizedIntelItem]:
        """Retrieve cached intel item"""
        cache_key = f"intel:{address}:{chain}"

        # Try cache first
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client:
                data = await client.get(cache_key)
                if data:
                    parsed = json.loads(data)
                    return NormalizedIntelItem(
                        intel_id=parsed["intel_id"],
                        address=parsed["address"],
                        chain=parsed["chain"],
                        category=parsed["category"],
                        risk_score=parsed["risk_score"],
                        confidence=IntelConfidence(parsed["confidence"]),
                        tlp_level=TLPLevel(parsed["tlp_level"]),
                        source=parsed["source"],
                        raw_data={},  # Not cached
                        normalized_data=parsed["normalized_data"],
                        created_at=datetime.fromisoformat(parsed["created_at"]),
                        expires_at=datetime.fromisoformat(parsed["expires_at"]) if parsed["expires_at"] else None,
                        tags=set(parsed["tags"])
                    )
        except Exception:
            pass

        return None

    async def deconflict_with_sanctions(self, address: str, chain: str, intel_items: List[NormalizedIntelItem]) -> Dict[str, Any]:
        """Advanced deconfliction with sanctions data"""
        # Get sanctions data (placeholder - integrate with actual sanctions service)
        sanctions_data = await self._get_sanctions_data(address, chain)

        fused_result = {
            "address": address,
            "chain": chain,
            "is_high_risk": False,
            "overall_risk_score": 0.0,
            "confidence_level": IntelConfidence.VERY_LOW,
            "categories": set(),
            "sources": set(),
            "deconfliction_notes": [],
            "recommendations": []
        }

        # Weight sources
        source_weights = {
            "sanctions": 1.0,
            "chainalysis": 0.9,
            "trm": 0.8,
            "elliptic": 0.8,
            "community": 0.4
        }

        total_weight = 0.0
        weighted_risk = 0.0
        confidence_scores = []

        # Process sanctions first (highest priority)
        if sanctions_data.get("is_sanctioned"):
            fused_result["is_high_risk"] = True
            fused_result["overall_risk_score"] = 1.0
            fused_result["confidence_level"] = IntelConfidence.VERY_HIGH
            fused_result["categories"].add("sanctions")
            fused_result["sources"].add("sanctions")
            fused_result["deconfliction_notes"].append("Sanctions override all other intelligence")
            return fused_result

        # Process intel items
        for item in intel_items:
            weight = source_weights.get(item.source, 0.5)
            total_weight += weight
            weighted_risk += item.risk_score * weight

            confidence_scores.append(self._confidence_to_numeric(item.confidence))
            fused_result["categories"].add(item.category)
            fused_result["sources"].add(item.source)

        if total_weight > 0:
            fused_result["overall_risk_score"] = weighted_risk / total_weight
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            fused_result["confidence_level"] = self._numeric_to_confidence(avg_confidence)

        # Risk threshold
        fused_result["is_high_risk"] = fused_result["overall_risk_score"] > 0.7

        # Generate recommendations
        if fused_result["is_high_risk"]:
            fused_result["recommendations"].extend([
                "Enhanced due diligence required",
                "Transaction monitoring recommended",
                "Consider blocking or flagging"
            ])
        elif fused_result["overall_risk_score"] > 0.3:
            fused_result["recommendations"].append("Standard due diligence recommended")

        # Convert sets to lists for JSON serialization
        fused_result["categories"] = list(fused_result["categories"])
        fused_result["sources"] = list(fused_result["sources"])

        return fused_result

    async def _get_sanctions_data(self, address: str, chain: str) -> Dict[str, Any]:
        """Get sanctions data for address (placeholder)"""
        # TODO: Integrate with actual sanctions service
        return {"is_sanctioned": False, "lists": []}

    def _confidence_to_numeric(self, confidence: IntelConfidence) -> float:
        """Convert confidence enum to numeric value"""
        mapping = {
            IntelConfidence.VERY_LOW: 0.1,
            IntelConfidence.LOW: 0.3,
            IntelConfidence.MEDIUM: 0.5,
            IntelConfidence.HIGH: 0.8,
            IntelConfidence.VERY_HIGH: 0.95
        }
        return mapping.get(confidence, 0.5)

    def _numeric_to_confidence(self, value: float) -> IntelConfidence:
        """Convert numeric value to confidence enum"""
        if value >= 0.9:
            return IntelConfidence.VERY_HIGH
        elif value >= 0.7:
            return IntelConfidence.HIGH
        elif value >= 0.5:
            return IntelConfidence.MEDIUM
        elif value >= 0.3:
            return IntelConfidence.LOW
        else:
            return IntelConfidence.VERY_LOW

    async def share_intelligence(self, item: NormalizedIntelItem, target_org: str) -> bool:
        """Share intelligence with another organization respecting TLP"""
        policy = self.tlp_policies.get(item.tlp_level)

        if not policy or not policy.get("can_share", False):
            logger.warning(f"Cannot share intelligence with TLP {item.tlp_level}")
            return False

        # Check if sharing with community/organization is allowed
        if not policy.get("share_with_org", False):
            logger.warning(f"TLP {item.tlp_level} does not allow sharing with organizations")
            return False

        # TODO: Implement actual sharing mechanism (API call, message queue, etc.)
        logger.info(f"Sharing intelligence {item.intel_id} with organization {target_org}")
        return True

    async def cleanup_expired_intel(self):
        """Clean up expired intelligence items"""
        # TODO: Implement cleanup logic for Redis/PostgreSQL
        logger.info("Cleaning up expired intelligence items")

    def list_normalizers(self) -> List[Dict[str, Any]]:
        """List all registered normalizers"""
        return [
            {
                "name": norm.name,
                "source_type": norm.source_type,
                "confidence_weight": norm.confidence_weight
            }
            for norm in self.normalizers.values()
        ]


# Singleton
threat_intel_v2 = ThreatIntelV2Service()
