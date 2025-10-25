"""
Universal Wallet Screening Service
===================================

TRM Labs-Style Universal Screening über alle 90+ unterstützten Chains.
Screent eine Wallet-Adresse gleichzeitig über alle Chains mit:
- Aggregate Risk Score
- Chain-spezifische Breakdowns
- Cross-Chain Exposure Detection
- Glass Box Attribution (transparente Confidence Scores)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)

# ML Risk Prediction (optional)
try:
    from app.ml.risk_predictor import get_risk_predictor, RiskFeatures
    HAS_ML_PREDICTOR = True
except ImportError:
    HAS_ML_PREDICTOR = False
    logger.info("ML Risk Predictor not available - using simple aggregation")


class RiskLevel(str, Enum):
    """Risk Level Classification"""
    CRITICAL = "critical"      # 90-100%
    HIGH = "high"              # 70-89%
    MEDIUM = "medium"          # 40-69%
    LOW = "low"                # 10-39%
    MINIMAL = "minimal"        # 0-9%


class AttributionSource(str, Enum):
    """Attribution Data Sources (Glass Box)"""
    SANCTIONS_LIST = "sanctions_list"
    EXCHANGE_LABEL = "exchange_label"
    THREAT_INTEL = "threat_intel"
    DARKWEB_MONITORING = "darkweb_monitoring"
    COMMUNITY_REPORT = "community_report"
    ML_CLUSTERING = "ml_clustering"
    CHAINALYSIS_REACTOR = "chainalysis_reactor"
    ELLIPTIC_DISCOVERY = "elliptic_discovery"
    TRM_LABS = "trm_labs"
    WALLET_FINGERPRINT = "wallet_fingerprint"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"


@dataclass
class AttributionEvidence:
    """Glass Box Attribution Evidence (TRM Labs-Style)"""
    source: AttributionSource
    confidence: float  # 0.0 - 1.0
    label: str
    evidence_type: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    verification_method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.value,
            "confidence": self.confidence,
            "label": self.label,
            "evidence_type": self.evidence_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "verification_method": self.verification_method,
        }


@dataclass
class ChainScreeningResult:
    """Screening-Ergebnis für eine Chain"""
    chain_id: str
    address: str
    risk_score: float  # 0.0 - 1.0
    risk_level: RiskLevel
    is_sanctioned: bool
    labels: List[str]
    attribution_evidence: List[AttributionEvidence]
    exposure_summary: Dict[str, Any]
    transaction_count: int
    first_seen: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    total_value_usd: float = 0.0
    counterparties: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "address": self.address,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "is_sanctioned": self.is_sanctioned,
            "labels": self.labels,
            "attribution_evidence": [e.to_dict() for e in self.attribution_evidence],
            "exposure_summary": self.exposure_summary,
            "transaction_count": self.transaction_count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "total_value_usd": self.total_value_usd,
            "counterparties": self.counterparties,
        }


@dataclass
class UniversalScreeningResult:
    """Aggregierte Universal Screening Results"""
    address: str
    screened_chains: List[str]
    total_chains_checked: int
    aggregate_risk_score: float
    aggregate_risk_level: RiskLevel
    highest_risk_chain: Optional[str]
    is_sanctioned_any_chain: bool
    cross_chain_activity: bool
    chain_results: Dict[str, ChainScreeningResult]
    screening_timestamp: datetime
    processing_time_ms: float
    
    # Aggregierte Metriken
    total_transactions: int = 0
    total_value_usd: float = 0.0
    unique_counterparties: int = 0
    all_labels: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "screened_chains": self.screened_chains,
            "total_chains_checked": self.total_chains_checked,
            "aggregate_risk_score": self.aggregate_risk_score,
            "aggregate_risk_level": self.aggregate_risk_level.value,
            "highest_risk_chain": self.highest_risk_chain,
            "is_sanctioned_any_chain": self.is_sanctioned_any_chain,
            "cross_chain_activity": self.cross_chain_activity,
            "chain_results": {
                chain: result.to_dict() 
                for chain, result in self.chain_results.items()
            },
            "screening_timestamp": self.screening_timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "summary": {
                "total_transactions": self.total_transactions,
                "total_value_usd": self.total_value_usd,
                "unique_counterparties": self.unique_counterparties,
                "all_labels": list(self.all_labels),
            }
        }


class UniversalScreeningService:
    """Universal Wallet Screening Service (TRM Labs-Style)"""
    
    def __init__(self):
        self.supported_chains: List[str] = []
        self._initialized = False
        
    async def initialize(self):
        """Initialisiere Service und lade unterstützte Chains"""
        if self._initialized:
            return
            
        try:
            # Importiere Multi-Chain Engine
            from app.services.multi_chain import multi_chain_engine
            
            # Lade alle unterstützten Chains
            chains = multi_chain_engine.adapter_factory.get_supported_chains()
            self.supported_chains = [chain.chain_id for chain in chains]
            
            logger.info(f"Universal Screening initialized with {len(self.supported_chains)} chains")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Universal Screening: {e}")
            # Fallback zu Standard-Chains
            self.supported_chains = ["ethereum", "bitcoin", "solana", "polygon", "arbitrum", "optimism"]
            self._initialized = True
    
    async def screen_address_universal(
        self,
        address: str,
        chains: Optional[List[str]] = None,
        max_concurrent: int = 10,
    ) -> UniversalScreeningResult:
        # Metrics imported lazily to avoid circular imports
        try:
            from app.monitoring.metrics import (
                universal_screening_requests,
                universal_screening_duration,
                universal_screening_chains_screened,
                universal_screening_risk_score
            )
            import time
            _start = time.time()
        except:
            _start = None
        """
        Screent eine Adresse über alle (oder spezifizierte) Chains gleichzeitig.
        
        Args:
            address: Wallet-Adresse zum Screenen
            chains: Optional Liste spezifischer Chains (None = alle)
            max_concurrent: Max parallele Chain-Requests
            
        Returns:
            UniversalScreeningResult mit aggregierten Daten
        """
        start_time = asyncio.get_event_loop().time()
        
        await self.initialize()
        
        # Bestimme zu screenende Chains
        target_chains = chains if chains else self.supported_chains
        
        # Parallel Screening über alle Chains
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def screen_single_chain(chain_id: str) -> Optional[ChainScreeningResult]:
            async with semaphore:
                try:
                    return await self._screen_chain(address, chain_id)
                except Exception as e:
                    logger.warning(f"Chain {chain_id} screening failed: {e}")
                    return None
        
        # Starte parallele Screening-Tasks
        tasks = [screen_single_chain(chain) for chain in target_chains]
        chain_results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtere erfolgreiche Results
        chain_results: Dict[str, ChainScreeningResult] = {}
        for chain_id, result in zip(target_chains, chain_results_list):
            if isinstance(result, ChainScreeningResult):
                chain_results[chain_id] = result
        
        # Aggregiere Results
        aggregate_result = self._aggregate_results(
            address=address,
            chain_results=chain_results,
            screened_chains=target_chains,
            start_time=start_time,
        )
        
        return aggregate_result
    
    async def _screen_chain(
        self,
        address: str,
        chain_id: str,
    ) -> ChainScreeningResult:
        """Screent eine Adresse auf einer spezifischen Chain"""
        
        # Importiere benötigte Services
        try:
            from app.services.compliance_service import service as compliance_service
            from app.analytics.exposure_service import exposure_service
            from app.services.multi_chain import multi_chain_engine
        except Exception as e:
            logger.error(f"Import error in _screen_chain: {e}")
            # Erstelle minimales Ergebnis
            return self._create_minimal_result(address, chain_id)
        
        # 1. Compliance Screening (Sanctions, Labels)
        compliance_result = None
        try:
            compliance_result = compliance_service.screen(chain_id, address)
        except Exception as e:
            logger.debug(f"Compliance screening failed for {chain_id}: {e}")
        
        # 2. Exposure Analysis (Direct + Indirect Risk)
        exposure_result = None
        try:
            exposure_result = await exposure_service.calculate(
                address=address,
                max_hops=3,
                context={"chain_id": chain_id}
            )
        except Exception as e:
            logger.debug(f"Exposure analysis failed for {chain_id}: {e}")
        
        # 3. Chain Activity Metadata
        activity_metadata = await self._get_chain_activity(chain_id, address)
        
        # 4. Attribution Evidence sammeln (Glass Box)
        attribution_evidence = self._collect_attribution_evidence(
            compliance_result=compliance_result,
            exposure_result=exposure_result,
            activity_metadata=activity_metadata,
        )
        
        # 5. Risk Score berechnen
        risk_score = self._calculate_risk_score(
            compliance_result=compliance_result,
            exposure_result=exposure_result,
            attribution_evidence=attribution_evidence,
        )
        
        risk_level = self._get_risk_level(risk_score)
        
        # 6. Labels sammeln
        labels = self._collect_labels(
            compliance_result=compliance_result,
            attribution_evidence=attribution_evidence,
        )
        
        # 7. Exposure Summary
        exposure_summary = self._create_exposure_summary(exposure_result)
        
        return ChainScreeningResult(
            chain_id=chain_id,
            address=address,
            risk_score=risk_score,
            risk_level=risk_level,
            is_sanctioned=bool(compliance_result and compliance_result.is_sanctioned),
            labels=labels,
            attribution_evidence=attribution_evidence,
            exposure_summary=exposure_summary,
            transaction_count=activity_metadata.get("tx_count", 0),
            first_seen=activity_metadata.get("first_seen"),
            last_activity=activity_metadata.get("last_activity"),
            total_value_usd=activity_metadata.get("total_value_usd", 0.0),
            counterparties=activity_metadata.get("counterparties", 0),
        )
    
    async def _get_chain_activity(
        self,
        chain_id: str,
        address: str,
    ) -> Dict[str, Any]:
        """Holt Chain-Activity-Metadaten"""
        try:
            from app.services.multi_chain import multi_chain_engine
            
            # Versuche Transaktionen zu holen (limitiert für Performance)
            txs = await multi_chain_engine.get_address_transactions_paged(
                chain_id=chain_id,
                address=address,
                limit=100,
            )
            
            if not txs:
                return {"tx_count": 0, "counterparties": 0, "total_value_usd": 0.0}
            
            # Extrahiere Metriken
            counterparties = set()
            total_value = 0.0
            
            for tx in txs:
                # Sammle Counterparties
                if tx.get("from"):
                    counterparties.add(tx["from"].lower())
                if tx.get("to"):
                    counterparties.add(tx["to"].lower())
                
                # Summiere Values (vereinfacht)
                if tx.get("value"):
                    try:
                        total_value += float(tx["value"])
                    except:
                        pass
            
            # Timestamps
            first_seen = None
            last_activity = None
            
            if txs:
                timestamps = []
                for tx in txs:
                    if tx.get("timestamp"):
                        try:
                            ts = datetime.fromisoformat(tx["timestamp"].replace("Z", "+00:00"))
                            timestamps.append(ts)
                        except:
                            pass
                
                if timestamps:
                    first_seen = min(timestamps)
                    last_activity = max(timestamps)
            
            return {
                "tx_count": len(txs),
                "counterparties": len(counterparties),
                "total_value_usd": total_value,  # Vereinfacht, sollte Preis-Conversion nutzen
                "first_seen": first_seen,
                "last_activity": last_activity,
            }
            
        except Exception as e:
            logger.debug(f"Failed to get chain activity for {chain_id}/{address}: {e}")
            return {"tx_count": 0, "counterparties": 0, "total_value_usd": 0.0}
    
    def _collect_attribution_evidence(
        self,
        compliance_result: Any,
        exposure_result: Any,
        activity_metadata: Dict[str, Any],
    ) -> List[AttributionEvidence]:
        """Sammelt Attribution Evidence (Glass Box)"""
        evidence_list = []
        
        # 1. Sanctions List Evidence
        if compliance_result and compliance_result.is_sanctioned:
            evidence_list.append(AttributionEvidence(
                source=AttributionSource.SANCTIONS_LIST,
                confidence=1.0,  # Sanctions sind 100% sicher
                label="Sanctioned Entity",
                evidence_type="ofac_sdn_list",
                timestamp=datetime.utcnow(),
                metadata={
                    "list_name": compliance_result.sanctions_list or "OFAC",
                    "program": getattr(compliance_result, "program", "Unknown"),
                },
                verification_method="direct_match",
            ))
        
        # 2. Labels als Evidence
        if compliance_result and hasattr(compliance_result, 'labels') and compliance_result.labels:
            for label in compliance_result.labels[:5]:  # Top 5
                evidence_list.append(AttributionEvidence(
                    source=AttributionSource.EXCHANGE_LABEL,
                    confidence=0.85,
                    label=label,
                    evidence_type="known_entity",
                    timestamp=datetime.utcnow(),
                    metadata={"source": "label_database"},
                    verification_method="label_repository",
                ))
        
        # 3. Behavioral Analysis Evidence
        tx_count = activity_metadata.get("tx_count", 0)
        if tx_count > 0:
            # Heuristik: Viele TXs = höhere Confidence
            confidence = min(0.7 + (tx_count / 1000) * 0.2, 0.95)
            evidence_list.append(AttributionEvidence(
                source=AttributionSource.BEHAVIORAL_ANALYSIS,
                confidence=confidence,
                label="Active Wallet",
                evidence_type="transaction_pattern",
                timestamp=datetime.utcnow(),
                metadata={
                    "tx_count": tx_count,
                    "counterparties": activity_metadata.get("counterparties", 0),
                },
                verification_method="transaction_history_analysis",
            ))
        
        # 4. Exposure-based Evidence
        if exposure_result:
            exposure_dict = exposure_result.to_dict() if hasattr(exposure_result, 'to_dict') else {}
            direct_exposure = exposure_dict.get("direct_exposure", {})
            
            if direct_exposure:
                # Hohe Direct Exposure = Evidence
                for category, score in direct_exposure.items():
                    if score > 0.5:
                        evidence_list.append(AttributionEvidence(
                            source=AttributionSource.THREAT_INTEL,
                            confidence=score,
                            label=f"Direct Exposure: {category}",
                            evidence_type="exposure_analysis",
                            timestamp=datetime.utcnow(),
                            metadata={"category": category, "score": score},
                            verification_method="graph_analysis",
                        ))
        
        return evidence_list
    
    def _calculate_risk_score(
        self,
        compliance_result: Any,
        exposure_result: Any,
        attribution_evidence: List[AttributionEvidence],
    ) -> float:
        """Berechnet aggregierten Risk Score (0.0 - 1.0)"""
        
        # Base Score
        risk_score = 0.0
        
        # 1. Sanctions = Sofort CRITICAL
        if compliance_result and compliance_result.is_sanctioned:
            return 1.0
        
        # 2. Compliance Risk Score
        if compliance_result and hasattr(compliance_result, 'risk_score'):
            risk_score = max(risk_score, float(compliance_result.risk_score))
        
        # 3. Exposure Risk
        if exposure_result:
            exposure_dict = exposure_result.to_dict() if hasattr(exposure_result, 'to_dict') else {}
            
            # Direct Exposure (höheres Gewicht)
            direct = exposure_dict.get("direct_exposure", {})
            if direct:
                max_direct = max(direct.values()) if direct else 0
                risk_score = max(risk_score, max_direct * 0.9)
            
            # Indirect Exposure (niedrigeres Gewicht)
            indirect = exposure_dict.get("indirect_exposure", {})
            if indirect:
                max_indirect = max(indirect.values()) if indirect else 0
                risk_score = max(risk_score, max_indirect * 0.6)
        
        # 4. Attribution Evidence Confidence
        if attribution_evidence:
            # Highest confidence evidence
            max_confidence = max(e.confidence for e in attribution_evidence)
            # Gewichte Evidence nur wenn High-Risk-Labels vorhanden
            high_risk_labels = ["sanctioned", "mixer", "darkweb", "ransomware", "scam"]
            has_high_risk = any(
                any(keyword in e.label.lower() for keyword in high_risk_labels)
                for e in attribution_evidence
            )
            if has_high_risk:
                risk_score = max(risk_score, max_confidence * 0.8)
        
        return min(risk_score, 1.0)
    
    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """Konvertiert Risk Score zu Risk Level"""
        if risk_score >= 0.9:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.7:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.1:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _collect_labels(
        self,
        compliance_result: Any,
        attribution_evidence: List[AttributionEvidence],
    ) -> List[str]:
        """Sammelt alle Labels"""
        labels = set()
        
        if compliance_result and hasattr(compliance_result, 'labels'):
            labels.update(compliance_result.labels or [])
        
        # Aus Attribution Evidence
        for evidence in attribution_evidence:
            if evidence.label:
                labels.add(evidence.label)
        
        return list(labels)
    
    def _create_exposure_summary(self, exposure_result: Any) -> Dict[str, Any]:
        """Erstellt Exposure Summary"""
        if not exposure_result:
            return {
                "direct_exposure": {},
                "indirect_exposure": {},
                "total_exposure_score": 0.0,
            }
        
        exposure_dict = exposure_result.to_dict() if hasattr(exposure_result, 'to_dict') else {}
        
        return {
            "direct_exposure": exposure_dict.get("direct_exposure", {}),
            "indirect_exposure": exposure_dict.get("indirect_exposure", {}),
            "total_exposure_score": exposure_dict.get("total_exposure_score", 0.0),
        }
    
    def _create_minimal_result(self, address: str, chain_id: str) -> ChainScreeningResult:
        """Erstellt minimales Result bei Fehlern"""
        return ChainScreeningResult(
            chain_id=chain_id,
            address=address,
            risk_score=0.0,
            risk_level=RiskLevel.MINIMAL,
            is_sanctioned=False,
            labels=[],
            attribution_evidence=[],
            exposure_summary={},
            transaction_count=0,
        )
    
    def _predict_ml_risk(
        self,
        chain_results: Dict[str, ChainScreeningResult],
        all_labels: Set[str],
    ) -> float:
        """
        ML-basierte Risk Prediction
        
        Extrahiert Features aus chain_results und nutzt ML-Model
        für intelligentere Risk-Aggregation.
        """
        # Feature Extraction
        total_tx = sum(r.transaction_count for r in chain_results.values())
        total_value = sum(r.total_value_usd for r in chain_results.values())
        avg_tx_value = total_value / total_tx if total_tx > 0 else 0
        max_tx_value = max((r.total_value_usd for r in chain_results.values()), default=0)
        unique_counterparties = sum(r.counterparties for r in chain_results.values())
        
        # Temporal Features (simplified - in production würden wir echte Timestamps nutzen)
        account_age_days = 365  # Default - würde aus first_seen berechnet
        transactions_last_24h = int(total_tx * 0.1)  # Schätzung
        transactions_last_7d = int(total_tx * 0.3)
        transactions_last_30d = int(total_tx * 0.7)
        
        # Network Features (würden aus Graph-DB kommen)
        clustering_coefficient = 0.15
        betweenness_centrality = 0.05
        degree_centrality = 0.10
        
        # Label-based Features
        has_mixer = any('mixer' in label.lower() or 'tornado' in label.lower() for label in all_labels)
        has_exchange = any('exchange' in label.lower() or 'binance' in label.lower() or 'coinbase' in label.lower() for label in all_labels)
        has_defi = any('defi' in label.lower() or 'uniswap' in label.lower() or 'aave' in label.lower() for label in all_labels)
        has_sanctions = any(r.is_sanctioned for r in chain_results.values())
        
        # Cross-Chain Features
        active_chains = len(chain_results)
        cross_chain_transfers = 0  # Würde aus Bridge-Detection kommen
        bridge_usage = 0.0
        
        # Behavioral Features (simplified)
        avg_gas_ratio = 1.0
        nonce_gaps = 0
        failed_tx_ratio = 0.05
        self_transfer_ratio = 0.1
        
        # Build Features Object
        features = RiskFeatures(
            total_transactions=total_tx,
            total_value_usd=total_value,
            avg_transaction_value=avg_tx_value,
            max_transaction_value=max_tx_value,
            unique_counterparties=unique_counterparties,
            account_age_days=account_age_days,
            transactions_last_24h=transactions_last_24h,
            transactions_last_7d=transactions_last_7d,
            transactions_last_30d=transactions_last_30d,
            clustering_coefficient=clustering_coefficient,
            betweenness_centrality=betweenness_centrality,
            degree_centrality=degree_centrality,
            has_mixer_labels=has_mixer,
            has_exchange_labels=has_exchange,
            has_defi_labels=has_defi,
            has_sanctions_labels=has_sanctions,
            total_labels_count=len(all_labels),
            active_chains_count=active_chains,
            cross_chain_transfers_count=cross_chain_transfers,
            bridge_usage_frequency=bridge_usage,
            avg_gas_price_ratio=avg_gas_ratio,
            nonce_gaps_count=nonce_gaps,
            failed_tx_ratio=failed_tx_ratio,
            self_transfer_ratio=self_transfer_ratio,
        )
        
        # Get ML Predictor
        predictor = get_risk_predictor()
        prediction = predictor.predict(features)
        
        logger.info(
            f"ML Risk Prediction: {prediction.risk_score:.3f} "
            f"(confidence: {prediction.confidence:.2f}, "
            f"level: {prediction.risk_level})"
        )
        
        return prediction.risk_score
    
    def _aggregate_results(
        self,
        address: str,
        chain_results: Dict[str, ChainScreeningResult],
        screened_chains: List[str],
        start_time: float,
    ) -> UniversalScreeningResult:
        """Aggregiert Chain-Results zu Universal Result"""
        
        # Berechne Processing Time
        end_time = asyncio.get_event_loop().time()
        processing_time_ms = (end_time - start_time) * 1000
        
        # Aggregierte Metriken
        total_transactions = sum(r.transaction_count for r in chain_results.values())
        total_value_usd = sum(r.total_value_usd for r in chain_results.values())
        unique_counterparties = sum(r.counterparties for r in chain_results.values())
        
        all_labels = set()
        for result in chain_results.values():
            all_labels.update(result.labels)
        
        # Aggregate Risk Score mit ML Enhancement
        aggregate_risk_score = 0.0
        highest_risk_chain = None
        
        if chain_results:
            max_risk_result = max(chain_results.values(), key=lambda r: r.risk_score)
            highest_risk_chain = max_risk_result.chain_id
            
            # Verwende ML-Prediction für intelligenteres Scoring
            if HAS_ML_PREDICTOR and len(chain_results) >= 2:
                try:
                    ml_score = self._predict_ml_risk(chain_results, all_labels)
                    # Kombiniere ML + Rule-based (Weighted Average)
                    aggregate_risk_score = 0.6 * ml_score + 0.4 * max_risk_result.risk_score
                except Exception as e:
                    logger.warning(f"ML prediction failed: {e} - using fallback")
                    aggregate_risk_score = max_risk_result.risk_score
            else:
                # Fallback: Simple Maximum
                aggregate_risk_score = max_risk_result.risk_score
        
        # Cross-Chain Activity Detection
        cross_chain_activity = len(chain_results) > 1
        
        # Sanctions Check (irgendeine Chain)
        is_sanctioned_any_chain = any(r.is_sanctioned for r in chain_results.values())
        
        # Risk Level
        aggregate_risk_level = self._get_risk_level(aggregate_risk_score)
        
        return UniversalScreeningResult(
            address=address,
            screened_chains=list(chain_results.keys()),
            total_chains_checked=len(screened_chains),
            aggregate_risk_score=aggregate_risk_score,
            aggregate_risk_level=aggregate_risk_level,
            highest_risk_chain=highest_risk_chain,
            is_sanctioned_any_chain=is_sanctioned_any_chain,
            cross_chain_activity=cross_chain_activity,
            chain_results=chain_results,
            screening_timestamp=datetime.utcnow(),
            processing_time_ms=processing_time_ms,
            total_transactions=total_transactions,
            total_value_usd=total_value_usd,
            unique_counterparties=unique_counterparties,
            all_labels=all_labels,
        )


# Global Service Instance
universal_screening_service = UniversalScreeningService()
