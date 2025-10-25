"""
Know Your Transaction (KYT) Engine - Real-Time Transaction Monitoring
Chainalysis Reactor competitor: Real-time risk scoring, sanctions screening, alerts
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.enrichment.labels_service import labels_service
from app.ml.risk_scorer import risk_scorer
from app.services.alert_service import alert_service, Alert, AlertType, AlertSeverity

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"

@dataclass
class Transaction:
    """Transaction data model."""
    tx_hash: str
    chain: str
    from_address: str
    to_address: str
    value_eth: float
    value_usd: float
    timestamp: datetime
    block_number: int
    gas_price: Optional[float] = None
    input_data: Optional[str] = None

@dataclass
class KYTResult:
    """KYT analysis result."""
    tx_hash: str
    risk_level: RiskLevel
    risk_score: float
    alerts: List[Dict[str, Any]]
    from_labels: List[str]
    to_labels: List[str]
    from_risk: float
    to_risk: float
    sanctions_hit: bool
    high_risk_hit: bool
    mixer_hit: bool
    analysis_time_ms: float

class KYTEngine:
    """Real-time transaction monitoring engine."""
    
    def __init__(self):
        self.subscribers: Dict[str, Set[asyncio.Queue]] = {}  # user_id -> queues
        self._running = False
        
    async def start(self):
        """Start the KYT engine."""
        self._running = True
        logger.info("KYT Engine started")
        
    async def stop(self):
        """Stop the KYT engine."""
        self._running = False
        logger.info("KYT Engine stopped")
        
    def subscribe(self, user_id: str) -> asyncio.Queue:
        """Subscribe to KYT alerts for a user."""
        queue = asyncio.Queue(maxsize=100)
        if user_id not in self.subscribers:
            self.subscribers[user_id] = set()
        self.subscribers[user_id].add(queue)
        logger.info(f"User {user_id} subscribed to KYT alerts")
        return queue
        
    def unsubscribe(self, user_id: str, queue: asyncio.Queue):
        """Unsubscribe from KYT alerts."""
        if user_id in self.subscribers:
            self.subscribers[user_id].discard(queue)
            if not self.subscribers[user_id]:
                del self.subscribers[user_id]
        logger.info(f"User {user_id} unsubscribed from KYT alerts")
    
    async def _broadcast_result(self, result: KYTResult):
        """Broadcast KYT result to all subscribers."""
        for user_id, queues in list(self.subscribers.items()):
            for queue in list(queues):
                try:
                    await asyncio.wait_for(
                        queue.put({
                            "type": "kyt.result",
                            "data": {
                                "tx_hash": result.tx_hash,
                                "risk_level": result.risk_level.value,
                                "risk_score": result.risk_score,
                                "alerts": result.alerts,
                                "from_labels": result.from_labels,
                                "to_labels": result.to_labels,
                                "analysis_time_ms": result.analysis_time_ms
                            }
                        }),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Queue full for user {user_id}, skipping broadcast")
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_id}: {e}")
        
    async def analyze_transaction(self, tx: Transaction) -> KYTResult:
        """Analyze a transaction in real-time.
        
        Args:
            tx: Transaction to analyze
            
        Returns:
            KYTResult with risk assessment and alerts
        """
        start = datetime.now()
        
        # Fetch labels for from/to addresses
        from_labels = await labels_service.get_labels(tx.from_address) or []
        to_labels = await labels_service.get_labels(tx.to_address) or []
        
        # Risk scoring
        from_risk_result = await risk_scorer.calculate_risk_score(tx.from_address)
        to_risk_result = await risk_scorer.calculate_risk_score(tx.to_address)
        from_risk = from_risk_result.get("risk_score", 0.0)
        to_risk = to_risk_result.get("risk_score", 0.0)
        
        # Combined risk score (weighted)
        tx_risk_score = (from_risk * 0.4 + to_risk * 0.4 + (tx.value_usd / 100000) * 0.2)
        tx_risk_score = min(1.0, tx_risk_score)
        
        # Determine base risk level
        if tx_risk_score >= 0.9:
            risk_level = RiskLevel.CRITICAL
        elif tx_risk_score >= 0.7:
            risk_level = RiskLevel.HIGH
        elif tx_risk_score >= 0.4:
            risk_level = RiskLevel.MEDIUM
        elif tx_risk_score >= 0.2:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.SAFE
            
        # Check for specific risk factors (allow tests to patch helpers)
        s_res = check_sanctions([tx.from_address, tx.to_address])
        sanctions_hit = await s_res if asyncio.iscoroutine(s_res) else bool(s_res)
        m_res = check_mixer([tx.from_address, tx.to_address])
        mixer_hit = await m_res if asyncio.iscoroutine(m_res) else bool(m_res)
        # Escalate based on critical hits
        if sanctions_hit:
            risk_level = RiskLevel.CRITICAL
        elif mixer_hit and risk_level.value in {RiskLevel.SAFE.value, RiskLevel.LOW.value, RiskLevel.MEDIUM.value}:
            risk_level = RiskLevel.HIGH
        high_risk_hit = from_risk > 0.7 or to_risk > 0.7
        
        # Generate alerts
        alerts = []
        
        if sanctions_hit:
            alert = {
                "type": "SANCTIONED",
                "severity": "CRITICAL",
                "title": "Sanctioned Address Detected",
                "description": f"Transaction involves sanctioned address",
                "tx_hash": tx.tx_hash,
                "from_address": tx.from_address,
                "to_address": tx.to_address
            }
            alerts.append(alert)
            # Dispatch to alert service
            try:
                await alert_service.dispatch_manual_alert(Alert(
                    alert_type=AlertType.SANCTIONED_ADDRESS,
                    severity=AlertSeverity.CRITICAL,
                    title=alert["title"],
                    description=alert["description"],
                    metadata=alert,
                    address=tx.from_address if "sanctioned" in from_labels else tx.to_address,
                    tx_hash=tx.tx_hash
                ))
            except Exception as e:
                logger.error(f"Failed to dispatch sanctioned alert: {e}")
                
        if mixer_hit:
            alert = {
                "type": "MIXER",
                "severity": "HIGH",
                "title": "Mixer/Tumbler Detected",
                "description": f"Transaction involves privacy mixer",
                "tx_hash": tx.tx_hash,
                "from_address": tx.from_address,
                "to_address": tx.to_address
            }
            alerts.append(alert)
            
        if tx.value_usd >= 100000:
            alert = {
                "type": "LARGE_TRANSFER",
                "severity": "MEDIUM",
                "title": "Large Transaction",
                "description": f"Transaction value: ${tx.value_usd:,.2f}",
                "tx_hash": tx.tx_hash,
                "value_usd": tx.value_usd
            }
            alerts.append(alert)
            
        if high_risk_hit and not sanctions_hit:
            alert = {
                "type": "HIGH_RISK",
                "severity": "HIGH",
                "title": "High-Risk Address",
                "description": f"Transaction involves high-risk address (score: {max(from_risk, to_risk):.2f})",
                "tx_hash": tx.tx_hash,
                "from_risk": from_risk,
                "to_risk": to_risk
            }
            alerts.append(alert)
        
        analysis_time = (datetime.now() - start).total_seconds() * 1000
        
        result = KYTResult(
            tx_hash=tx.tx_hash,
            risk_level=risk_level,
            risk_score=tx_risk_score,
            alerts=alerts,
            from_labels=from_labels,
            to_labels=to_labels,
            from_risk=from_risk,
            to_risk=to_risk,
            sanctions_hit=sanctions_hit,
            high_risk_hit=high_risk_hit,
            mixer_hit=mixer_hit,
            analysis_time_ms=analysis_time
        )
        # SOAR automation (best-effort)
        try:
            import os as _os
            if _os.getenv("ENABLE_SOAR_AUTOMATION", "1") == "1":
                from app.services.soar_engine import soar_engine as _soar_engine
                event = {
                    "address": tx.to_address,
                    "value_usd": tx.value_usd,
                    "labels": list(set(from_labels + to_labels)),
                    "metadata": {
                        "from_address": tx.from_address,
                        "to_address": tx.to_address,
                        "from_risk": from_risk,
                        "to_risk": to_risk,
                        "counterparty_risk": max(from_risk, to_risk),
                        "chain": tx.chain,
                        "tx_hash": tx.tx_hash,
                    },
                }
                _soar_engine.run(event)
        except Exception as _soar_err:
            logger.debug(f"SOAR automation skipped: {_soar_err}")

        # Broadcast to subscribers
        await self._broadcast_result(result)
        
        return result


async def check_sanctions(addresses: List[str]) -> bool:
    """Return True if any of the addresses is sanctioned.

    Uses labels_service, which integrates the multi-sanctions aggregator. Separated
    into its own function so tests can patch it easily.
    """
    try:
        addrs = [a for a in addresses if isinstance(a, str) and a]
        if not addrs:
            return False
        bulk = await labels_service.bulk_get_labels(addrs)
        for addr in addrs:
            labs = (bulk.get(addr.lower()) or [])
            if any(l in {"sanctioned", "ofac", "sdn", "uk", "eu", "un", "canada", "australia"} for l in labs):
                return True
        return False
    except Exception as e:
        logger.debug(f"check_sanctions fallback: {e}")
        # Fallback: quick per-address check
        for a in addresses:
            try:
                labs = await labels_service.get_labels(a)
                if any(l in {"sanctioned", "ofac", "sdn"} for l in (labs or [])):
                    return True
            except Exception:
                continue
        return False


async def check_mixer(addresses: List[str]) -> bool:
    """Return True if any of the addresses is a known mixer/obfuscation service."""
    try:
        addrs = [a for a in addresses if isinstance(a, str) and a]
        if not addrs:
            return False
        bulk = await labels_service.bulk_get_labels(addrs)
        for addr in addrs:
            labs = (bulk.get(addr.lower()) or [])
            if any(l in {"mixer", "tornado", "blender", "privacy", "obfuscation"} for l in labs):
                return True
        return False
    except Exception as e:
        logger.debug(f"check_mixer fallback: {e}")
        for a in addresses:
            try:
                labs = await labels_service.get_labels(a)
                if any(l in {"mixer", "tornado", "blender"} for l in (labs or [])):
                    return True
            except Exception:
                continue
        return False

# Global KYT engine instance
kyt_engine = KYTEngine()
