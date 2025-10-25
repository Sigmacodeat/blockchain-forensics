"""
Contract History Tracker
========================
Tracks contract upgrades, proxy changes, and risk evolution over time.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class HistoricalSnapshot:
    """Snapshot of contract analysis at a specific time"""
    timestamp: datetime
    address: str
    chain: str
    analysis: Dict
    proxy_implementation: Optional[str] = None
    risk_score: float = 0.0
    vulnerability_count: int = 0


class ContractHistoryTracker:
    """
    Tracks contract analysis history for:
    - Proxy upgrade detection
    - Risk score trends
    - Vulnerability evolution
    """
    
    def __init__(self):
        # In-memory storage (would be Redis/PostgreSQL in production)
        self._history: Dict[str, List[HistoricalSnapshot]] = {}
    
    def add_snapshot(
        self,
        address: str,
        chain: str,
        analysis: Dict
    ) -> HistoricalSnapshot:
        """Add new analysis snapshot to history"""
        snapshot = HistoricalSnapshot(
            timestamp=datetime.utcnow(),
            address=address.lower(),
            chain=chain.lower(),
            analysis=analysis,
            proxy_implementation=analysis.get("proxy", {}).get("implementation"),
            risk_score=analysis.get("score", 0.0),
            vulnerability_count=analysis.get("vulnerabilities", {}).get("total", 0),
        )
        
        key = f"{chain}:{address}".lower()
        if key not in self._history:
            self._history[key] = []
        
        self._history[key].append(snapshot)
        
        # Keep only last 100 snapshots per contract
        if len(self._history[key]) > 100:
            self._history[key] = self._history[key][-100:]
        
        return snapshot
    
    def get_history(
        self,
        address: str,
        chain: str,
        days: int = 30
    ) -> List[HistoricalSnapshot]:
        """Get analysis history for contract"""
        key = f"{chain}:{address}".lower()
        if key not in self._history:
            return []
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [
            snap for snap in self._history[key]
            if snap.timestamp >= cutoff
        ]
    
    def detect_upgrades(
        self,
        address: str,
        chain: str
    ) -> List[Dict]:
        """Detect proxy implementation upgrades"""
        history = self.get_history(address, chain, days=365)
        if not history:
            return []
        
        upgrades = []
        prev_impl = None
        
        for snapshot in history:
            current_impl = snapshot.proxy_implementation
            if current_impl and current_impl != prev_impl and prev_impl is not None:
                upgrades.append({
                    "timestamp": snapshot.timestamp.isoformat(),
                    "from_implementation": prev_impl,
                    "to_implementation": current_impl,
                    "risk_score_before": history[history.index(snapshot) - 1].risk_score if history.index(snapshot) > 0 else None,
                    "risk_score_after": snapshot.risk_score,
                })
            prev_impl = current_impl
        
        return upgrades
    
    def get_risk_trend(
        self,
        address: str,
        chain: str,
        days: int = 30
    ) -> Dict:
        """Get risk score trend analysis"""
        history = self.get_history(address, chain, days)
        if not history:
            return {
                "trend": "unknown",
                "current_score": 0.0,
                "average_score": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "datapoints": [],
            }
        
        scores = [snap.risk_score for snap in history]
        datapoints = [
            {
                "timestamp": snap.timestamp.isoformat(),
                "score": snap.risk_score,
                "vulnerabilities": snap.vulnerability_count,
            }
            for snap in history
        ]
        
        # Calculate trend
        if len(scores) >= 2:
            recent_avg = sum(scores[-5:]) / min(5, len(scores))
            older_avg = sum(scores[:5]) / min(5, len(scores))
            if recent_avg > older_avg + 0.1:
                trend = "increasing"
            elif recent_avg < older_avg - 0.1:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "trend": trend,
            "current_score": scores[-1] if scores else 0.0,
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "datapoints": datapoints,
        }
    
    def get_timeline_summary(
        self,
        address: str,
        chain: str,
        days: int = 90
    ) -> Dict:
        """Get comprehensive timeline summary"""
        history = self.get_history(address, chain, days)
        upgrades = self.detect_upgrades(address, chain)
        risk_trend = self.get_risk_trend(address, chain, days)
        
        # Significant events
        events = []
        
        # Add upgrades as events
        for upgrade in upgrades:
            events.append({
                "type": "proxy_upgrade",
                "timestamp": upgrade["timestamp"],
                "description": f"Proxy upgraded to {upgrade['to_implementation'][:10]}...",
                "severity": "high" if abs((upgrade.get("risk_score_after", 0) or 0) - (upgrade.get("risk_score_before", 0) or 0)) > 0.2 else "medium",
            })
        
        # Add risk spikes
        for i, snap in enumerate(history[1:], 1):
            prev_snap = history[i-1]
            if snap.risk_score > prev_snap.risk_score + 0.3:
                events.append({
                    "type": "risk_spike",
                    "timestamp": snap.timestamp.isoformat(),
                    "description": f"Risk score increased from {prev_snap.risk_score:.2f} to {snap.risk_score:.2f}",
                    "severity": "critical" if snap.risk_score > 0.7 else "high",
                })
        
        # Sort events by timestamp
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "address": address,
            "chain": chain,
            "period_days": days,
            "total_snapshots": len(history),
            "total_upgrades": len(upgrades),
            "upgrades": upgrades,
            "risk_trend": risk_trend,
            "events": events[:20],  # Last 20 events
            "first_seen": history[0].timestamp.isoformat() if history else None,
            "last_analyzed": history[-1].timestamp.isoformat() if history else None,
        }


# Singleton
history_tracker = ContractHistoryTracker()
