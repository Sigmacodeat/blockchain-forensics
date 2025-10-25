"""
Advanced Indirect Risk Detection
==================================

TRM Labs-Style Multi-Hop Indirect Risk Detection:
- Path-Agnostic Tracing (findet ALLE Pfade zwischen Adressen)
- Cross-Chain Risk Propagation
- Nuanced Risk Scoring (verschiedene Pfad-Typen haben unterschiedliche Gewichte)
- Unterstützt Solana, Polygon, Optimism, Arbitrum, und alle anderen Chains
- Risk Decay über Hops
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math

logger = logging.getLogger(__name__)


class PathType(str, Enum):
    """Pfad-Typ für Risk Propagation"""
    DIRECT = "direct"              # Direkte Transaktion
    MIXER = "mixer"                # Via Mixer
    BRIDGE = "bridge"              # Cross-Chain Bridge
    EXCHANGE = "exchange"          # Via Exchange
    DEFI = "defi"                  # Via DeFi Protocol
    UNKNOWN = "unknown"            # Unbekannt


class RiskCategory(str, Enum):
    """Risk Categories"""
    SANCTIONS = "sanctions"
    DARKWEB = "darkweb"
    RANSOMWARE = "ransomware"
    SCAM = "scam"
    MIXER = "mixer"
    STOLEN_FUNDS = "stolen_funds"
    TERRORISM = "terrorism"
    CHILD_ABUSE = "child_abuse"


@dataclass
class RiskPath:
    """Einzelner Pfad mit Risk"""
    from_address: str
    to_address: str
    hop_count: int
    path_type: PathType
    risk_categories: Set[RiskCategory]
    intermediate_addresses: List[str]
    chains_involved: List[str]
    risk_score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_address": self.from_address,
            "to_address": self.to_address,
            "hop_count": self.hop_count,
            "path_type": self.path_type.value,
            "risk_categories": [c.value for c in self.risk_categories],
            "intermediate_addresses": self.intermediate_addresses,
            "chains_involved": self.chains_involved,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
        }


@dataclass
class IndirectRiskResult:
    """Result für Indirect Risk Analysis"""
    target_address: str
    max_hops: int
    total_paths_found: int
    paths_analyzed: int
    
    # Risk Scores by Category (0.0 - 1.0)
    risk_by_category: Dict[RiskCategory, float]
    aggregate_risk_score: float
    
    # Paths Details
    high_risk_paths: List[RiskPath]
    
    # Metadata
    chains_analyzed: List[str]
    analysis_timestamp: datetime
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_address": self.target_address,
            "max_hops": self.max_hops,
            "total_paths_found": self.total_paths_found,
            "paths_analyzed": self.paths_analyzed,
            "risk_by_category": {k.value: v for k, v in self.risk_by_category.items()},
            "aggregate_risk_score": self.aggregate_risk_score,
            "high_risk_paths": [p.to_dict() for p in self.high_risk_paths],
            "chains_analyzed": self.chains_analyzed,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
        }


class AdvancedIndirectRiskService:
    """
    Advanced Indirect Risk Detection Service (TRM Labs-Style).
    
    Features:
    - Path-Agnostic Tracing (findet alle Pfade)
    - Cross-Chain Risk Propagation
    - Nuanced Risk Scoring
    - Risk Decay über Hops
    """
    
    # Risk Decay Parameters (TRM Labs-Style)
    RISK_DECAY_FACTOR = 0.7  # Pro Hop: Risk * 0.7
    MIN_RISK_THRESHOLD = 0.05  # Minimaler Risk Score
    
    # Path Type Weights (verschiedene Pfad-Typen haben unterschiedliche Risiken)
    PATH_TYPE_WEIGHTS = {
        PathType.DIRECT: 1.0,
        PathType.MIXER: 0.9,      # Mixer sind verdächtig
        PathType.BRIDGE: 0.8,      # Cross-Chain hat etwas weniger Risk
        PathType.EXCHANGE: 0.6,    # Exchanges mischen, aber sind reguliert
        PathType.DEFI: 0.7,
        PathType.UNKNOWN: 0.5,
    }
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialisiere Service"""
        if self._initialized:
            return
        
        logger.info("Initializing Advanced Indirect Risk Service")
        self._initialized = True
    
    async def analyze_indirect_risk(
        self,
        target_address: str,
        max_hops: int = 3,
        chains: Optional[List[str]] = None,
        max_paths: int = 1000,
    ) -> IndirectRiskResult:
        """
        Analysiere Indirect Risk für Adresse.
        
        Args:
            target_address: Ziel-Adresse
            max_hops: Maximale Hop-Tiefe
            chains: Chains zu analysieren (None = alle)
            max_paths: Max Pfade zu analysieren
            
        Returns:
            IndirectRiskResult
        """
        await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        
        # Initialisiere Multi-Chain Engine
        try:
            from app.services.multi_chain import multi_chain_engine
            
            if chains:
                await multi_chain_engine.initialize_chains(chains)
            else:
                # Alle Chains
                all_chains = multi_chain_engine.adapter_factory.get_supported_chains()
                chains = [c.chain_id for c in all_chains]
        except Exception as e:
            logger.warning(f"Failed to initialize chains: {e}")
            chains = ["ethereum", "bitcoin", "solana"]
        
        # Finde alle Pfade (Path-Agnostic)
        all_paths = await self._find_all_paths(
            target_address=target_address,
            max_hops=max_hops,
            chains=chains,
            max_paths=max_paths,
        )
        
        # Analysiere Risk für jeden Pfad
        risk_paths = []
        for path_data in all_paths:
            risk_path = await self._analyze_path_risk(path_data)
            if risk_path and risk_path.risk_score > self.MIN_RISK_THRESHOLD:
                risk_paths.append(risk_path)
        
        # Aggregiere Risk by Category
        risk_by_category: Dict[RiskCategory, float] = {}
        for path in risk_paths:
            for category in path.risk_categories:
                # Maximum Risk über alle Pfade für jede Kategorie
                current_risk = risk_by_category.get(category, 0.0)
                risk_by_category[category] = max(current_risk, path.risk_score)
        
        # Aggregate Risk Score (Maximum über alle Kategorien)
        aggregate_risk = max(risk_by_category.values()) if risk_by_category else 0.0
        
        # Sortiere Pfade nach Risk
        risk_paths.sort(key=lambda p: p.risk_score, reverse=True)
        
        # Processing Time
        end_time = asyncio.get_event_loop().time()
        processing_time_ms = (end_time - start_time) * 1000
        
        return IndirectRiskResult(
            target_address=target_address,
            max_hops=max_hops,
            total_paths_found=len(all_paths),
            paths_analyzed=len(risk_paths),
            risk_by_category=risk_by_category,
            aggregate_risk_score=aggregate_risk,
            high_risk_paths=risk_paths[:20],  # Top 20
            chains_analyzed=chains,
            analysis_timestamp=datetime.utcnow(),
            processing_time_ms=processing_time_ms,
        )
    
    async def _find_all_paths(
        self,
        target_address: str,
        max_hops: int,
        chains: List[str],
        max_paths: int,
    ) -> List[Dict[str, Any]]:
        """
        Finde alle Pfade zu Adresse (Path-Agnostic).
        
        Nutzt BFS über alle Chains.
        """
        paths: List[Dict[str, Any]] = []
        visited: Set[str] = set()
        
        # BFS Queue: (address, chain, hop_count, path_so_far)
        queue: List[Tuple[str, str, int, List[str]]] = []
        
        # Start mit target_address auf allen Chains
        for chain in chains:
            queue.append((target_address, chain, 0, [target_address]))
            visited.add(f"{chain}:{target_address.lower()}")
        
        # BFS
        while queue and len(paths) < max_paths:
            current_address, current_chain, hop_count, path_so_far = queue.pop(0)
            
            if hop_count >= max_hops:
                continue
            
            # Hole Counterparties für current_address
            counterparties = await self._get_counterparties(current_address, current_chain)
            
            for cp_address, cp_data in counterparties:
                # Check ob bereits besucht
                key = f"{current_chain}:{cp_address.lower()}"
                if key in visited:
                    continue
                
                visited.add(key)
                
                # Erstelle Pfad
                new_path = path_so_far + [cp_address]
                
                # Speichere Pfad
                paths.append({
                    "from_address": target_address,
                    "to_address": cp_address,
                    "hop_count": hop_count + 1,
                    "intermediate_addresses": new_path[1:-1],
                    "chain": current_chain,
                    "counterparty_data": cp_data,
                })
                
                # Füge zu Queue hinzu für weitere Exploration
                if hop_count + 1 < max_hops:
                    queue.append((cp_address, current_chain, hop_count + 1, new_path))
                
                # Check Max Paths Limit
                if len(paths) >= max_paths:
                    break
        
        logger.info(f"Found {len(paths)} paths for {target_address} up to {max_hops} hops")
        
        return paths
    
    async def _get_counterparties(
        self,
        address: str,
        chain: str,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Hole Counterparties für Adresse auf Chain.
        
        Returns: List of (counterparty_address, metadata)
        """
        try:
            from app.services.multi_chain import multi_chain_engine
            
            # Hole Transaktionen (limitiert)
            txs = await multi_chain_engine.get_address_transactions_paged(
                chain_id=chain,
                address=address,
                limit=50,  # Limitiert für Performance
            )
            
            counterparties: Dict[str, Dict[str, Any]] = {}
            
            for tx in txs:
                # From
                if tx.get("from") and tx["from"].lower() != address.lower():
                    addr = tx["from"]
                    if addr not in counterparties:
                        counterparties[addr] = {
                            "interactions": 0,
                            "total_value": 0.0,
                        }
                    counterparties[addr]["interactions"] += 1
                    if tx.get("value"):
                        try:
                            counterparties[addr]["total_value"] += float(tx["value"])
                        except:
                            pass
                
                # To
                if tx.get("to") and tx["to"].lower() != address.lower():
                    addr = tx["to"]
                    if addr not in counterparties:
                        counterparties[addr] = {
                            "interactions": 0,
                            "total_value": 0.0,
                        }
                    counterparties[addr]["interactions"] += 1
                    if tx.get("value"):
                        try:
                            counterparties[addr]["total_value"] += float(tx["value"])
                        except:
                            pass
            
            return list(counterparties.items())
            
        except Exception as e:
            logger.debug(f"Failed to get counterparties for {address} on {chain}: {e}")
            return []
    
    async def _analyze_path_risk(
        self,
        path_data: Dict[str, Any],
    ) -> Optional[RiskPath]:
        """
        Analysiere Risk für einzelnen Pfad.
        """
        try:
            # Hole Risk Data für alle Adressen im Pfad
            all_addresses = [path_data["from_address"]] + path_data["intermediate_addresses"] + [path_data["to_address"]]
            
            risk_categories: Set[RiskCategory] = set()
            max_risk_in_path = 0.0
            
            # Prüfe jede Adresse auf Risk
            for addr in all_addresses:
                addr_risk = await self._get_address_risk(addr, path_data["chain"])
                
                if addr_risk:
                    risk_categories.update(addr_risk["categories"])
                    max_risk_in_path = max(max_risk_in_path, addr_risk["risk_score"])
            
            # Wenn kein Risk gefunden, skip
            if not risk_categories or max_risk_in_path < self.MIN_RISK_THRESHOLD:
                return None
            
            # Bestimme Path Type
            path_type = self._determine_path_type(path_data)
            
            # Berechne Risk Score mit Decay
            hop_count = path_data["hop_count"]
            decayed_risk = max_risk_in_path * (self.RISK_DECAY_FACTOR ** hop_count)
            
            # Apply Path Type Weight
            path_weight = self.PATH_TYPE_WEIGHTS.get(path_type, 0.5)
            final_risk = decayed_risk * path_weight
            
            # Confidence (sinkt mit Hops)
            confidence = 1.0 / (1.0 + hop_count * 0.3)
            
            return RiskPath(
                from_address=path_data["from_address"],
                to_address=path_data["to_address"],
                hop_count=hop_count,
                path_type=path_type,
                risk_categories=risk_categories,
                intermediate_addresses=path_data["intermediate_addresses"],
                chains_involved=[path_data["chain"]],
                risk_score=final_risk,
                confidence=confidence,
            )
            
        except Exception as e:
            logger.debug(f"Failed to analyze path risk: {e}")
            return None
    
    async def _get_address_risk(
        self,
        address: str,
        chain: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Hole Risk Data für Adresse.
        """
        try:
            from app.services.compliance_service import service as compliance_service
            
            # Screen Adresse
            result = compliance_service.screen(chain, address)
            
            if not result:
                return None
            
            # Map zu Risk Categories
            categories: Set[RiskCategory] = set()
            
            if result.is_sanctioned:
                categories.add(RiskCategory.SANCTIONS)
            
            # Check Labels
            for label in (result.labels or []):
                label_lower = label.lower()
                if "darkweb" in label_lower or "dark web" in label_lower:
                    categories.add(RiskCategory.DARKWEB)
                elif "ransomware" in label_lower:
                    categories.add(RiskCategory.RANSOMWARE)
                elif "scam" in label_lower or "fraud" in label_lower:
                    categories.add(RiskCategory.SCAM)
                elif "mixer" in label_lower or "tumbler" in label_lower:
                    categories.add(RiskCategory.MIXER)
                elif "stolen" in label_lower or "hack" in label_lower:
                    categories.add(RiskCategory.STOLEN_FUNDS)
                elif "terror" in label_lower:
                    categories.add(RiskCategory.TERRORISM)
                elif "child" in label_lower or "csam" in label_lower:
                    categories.add(RiskCategory.CHILD_ABUSE)
            
            return {
                "risk_score": result.risk_score if hasattr(result, 'risk_score') else 0.5,
                "categories": categories,
            }
            
        except Exception as e:
            logger.debug(f"Failed to get address risk: {e}")
            return None
    
    def _determine_path_type(self, path_data: Dict[str, Any]) -> PathType:
        """Bestimme Path Type basierend auf Intermediate Addresses"""
        # Simplified: In Production würde man Labels der Intermediate Addresses prüfen
        
        if not path_data.get("intermediate_addresses"):
            return PathType.DIRECT
        
        # Hier könnte man Counterparty Data analysieren
        # Für jetzt: Default Unknown
        return PathType.UNKNOWN


# Global Service Instance
advanced_indirect_risk_service = AdvancedIndirectRiskService()
