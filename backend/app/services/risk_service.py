"""
Risk Scoring v1
- Kombiniert einfache Faktoren: Compliance-Screening, Labels, Taint, Exposure.
- TEST/OFFLINE-sicher, optionale Neo4j-basierte Exposure-Einbindung.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import os

from app.integrations.feeds import threat_intel_service
from app.config import settings
from app.db.neo4j_client import neo4j_client
# labels_store kann in Minimal-/Test-Umgebungen fehlen -> resilienter Import
try:
    from app.enrichment import labels_store  # type: ignore
except Exception:
    class _DummyLabelsStore:
        def get(self, chain: str, address: str):
            return []
    labels_store = _DummyLabelsStore()  # type: ignore
# Address-Utils können in Minimal-/Test-Setups fehlen -> resilienter Import
try:
    from app.services.address_utils import is_valid_address, normalize_address  # type: ignore
except Exception:
    def is_valid_address(chain: str, address: str) -> bool:  # type: ignore
        try:
            return isinstance(address, str) and len(address) > 0
        except Exception:
            return False

    def normalize_address(chain: str, address: str) -> str:  # type: ignore
        try:
            return address.lower() if isinstance(address, str) else address
        except Exception:
            return address
# Compliance-Service kann in Minimal-/Test-Setups fehlen -> resilienter Import
try:
    from app.services.compliance import compliance_service  # type: ignore
except Exception:
    class _ScreenResult:
        def __init__(self):
            self.watchlisted = False
            self.reasons = []
            self.categories = []

    class _DummyComplianceService:
        def screen(self, chain: str, address: str) -> _ScreenResult:  # type: ignore
            return _ScreenResult()

    compliance_service = _DummyComplianceService()  # type: ignore


@dataclass
class RiskScoreResult:
    chain: str
    address: str
    score: int               # 0..100
    factors: Dict[str, float]
    categories: List[str]
    reasons: List[str]
    explanations: Dict[str, float] | None = None


class RiskService:
    """Berechnet einfache Risikoscores für Adressen (0..100)."""

    def __init__(self):
        # Gewichtungen (konfigurierbar via Settings/ENV)
        self.w_watchlist = float(getattr(settings, "RISK_W_WATCHLIST", 0.6))
        self.w_labels = float(getattr(settings, "RISK_W_LABELS", 0.25))
        self.w_taint = float(getattr(settings, "RISK_W_TAINT", 0.05))
        self.w_exposure = float(getattr(settings, "RISK_W_EXPOSURE", 0.10))
        self.w_graph = float(getattr(settings, "RISK_W_GRAPH", 0.0))
        self.w_threat_intel = float(getattr(settings, "RISK_W_THREAT_INTEL", 0.8))

    def _score_threat_intel(self, chain: str, address: str) -> tuple[float, List[str]]:
        """Score based on threat intelligence feeds"""
        intel = threat_intel_service.get_address_intel(address)
        max_risk = threat_intel_service.get_risk_score_boost(address)

        categories = []
        if intel:
            for entry in intel:
                categories.append(entry["type"])

        return max_risk, categories

    def _score_labels(self, chain: str, address: str) -> tuple[float, List[str]]:
        labels = labels_store.get(chain, address)
        cats = list({l.get("category", "generic") for l in labels})
        score = 0.0
        if any(c in {"mixer", "scam", "ransomware"} for c in cats):
            score = 0.9
        elif any(c in {"exchange", "dex", "cex"} for c in cats):
            score = 0.4
        elif labels:
            score = 0.2
        return score, cats

    def _score_taint(self, chain: str, address: str) -> float:
        """Ermittelt einen Taint-Score (0..1) aus Graph-Signalen.
        Bevorzugte Quelle kann über Settings gewählt werden:
        - RISK_TAINT_SOURCE: 'exposure' | 'graph_signal' | 'auto'
        In TEST/OFFLINE -> 0.0
        """
        if os.getenv("TEST_MODE") == "1" or os.getenv("OFFLINE_MODE") == "1":
            return 0.0
        source = str(getattr(settings, "RISK_TAINT_SOURCE", "auto")).lower()
        try:
            from app.db.neo4j_client import neo4j_client
            addr = address
            # Auto: probiere graph_signals, fallback auf exposure
            if source == "graph_signal" or source == "auto":
                try:
                    sig = neo4j_client.get_address_graph_signals  # type: ignore[attr-defined]
                except Exception:
                    sig = None
                if sig is not None:
                    g = neo4j_client  # call async in sync context is not possible here -> use best-effort 0.0
                    # Hinweis: Diese Methode ist async; synchroner Aufruf hier nicht möglich.
                    # Der echte Taint-Score wird in score_address() bereits über async-Pfad in graph_component berechnet.
                    # Daher hier 0.0 lassen, um doppelte Abfragen und Async-in-Sync zu vermeiden.
                    return 0.0
            if source == "exposure" or source == "auto":
                try:
                    get_exp = neo4j_client.get_address_exposure  # type: ignore[attr-defined]
                except Exception:
                    get_exp = None
                if get_exp is not None:
                    # Gleiches Problem (async). score_address() ermittelt exposure bereits asynchron.
                    return 0.0
        except Exception:
            return 0.0
        return 0.0

    async def score_address(self, chain: str, address: str) -> RiskScoreResult:
        """Berechnet Score und liefert Faktoren/Kategorien/Gründe zurück."""
        if not is_valid_address(chain, address):
            # Ungültige Adressen bekommen "niedrig" mit Grund
            return RiskScoreResult(
                chain=chain,
                address=address,
                score=0,
                factors={"watchlist": 0.0, "labels": 0.0, "taint": 0.0},
                categories=["invalid"],
                reasons=[f"invalid {chain} address"],
            )
        addr = normalize_address(chain, address) or address

        # Compliance Screen (Watchlist etc.)
        scr = compliance_service.screen(chain, addr)
        watch_component = 1.0 if scr.watchlisted else 0.0

        # Threat Intelligence
        threat_component, threat_cats = self._score_threat_intel(chain, addr)

        # Labels
        label_component, cats = self._score_labels(chain, addr)

        # Taint/Exposure (async Teil unten)
        taint_component = self._score_taint(chain, addr)
        exposure = 0.0
        graph_component = 0.0
        if os.getenv("TEST_MODE") != "1" and os.getenv("OFFLINE_MODE") != "1":
            try:
                exposure = await neo4j_client.get_address_exposure(addr)
            except Exception:
                exposure = 0.0
            # Optional: Graph-Signale aggregieren (Flag)
            if bool(getattr(settings, "RISK_USE_GRAPH_SIGNALS", False)):
                try:
                    sig = await neo4j_client.get_address_graph_signals(addr)
                    # einfacher Durchschnitt der drei Signale
                    vals = [
                        float(sig.get("avg_neighbor_taint", 0.0)),
                        float(sig.get("high_risk_neighbor_ratio", 0.0)),
                        float(sig.get("max_path_taint3", 0.0)),
                    ]
                    graph_component = max(0.0, min(1.0, sum(vals) / 3.0))
                except Exception:
                    graph_component = 0.0

        # Optional: Quelle für taint_component aus async-Werten ableiten
        try:
            src = str(getattr(settings, "RISK_TAINT_SOURCE", "auto")).lower()
            if src == "exposure":
                taint_component = float(exposure)
            elif src == "graph_signal":
                taint_component = float(graph_component)
            elif src == "auto":
                # Bevorzuge konkrete Graph-Signale, sonst Exposure
                taint_component = float(graph_component) if graph_component > 0 else float(exposure)
            taint_component = max(0.0, min(1.0, float(taint_component)))
        except Exception:
            pass

        # Aggregation (einfach linear, 0..1 -> 0..100)
        components = {
            "watchlist": self.w_watchlist * watch_component,
            "labels": self.w_labels * label_component,
            "taint": self.w_taint * taint_component,
            "exposure": self.w_exposure * exposure,
            "graph": self.w_graph * graph_component,
            "threat_intel": self.w_threat_intel * threat_component,
        }
        agg = sum(components.values())
        agg = max(0.0, min(1.0, agg))
        score = int(round(agg * 100))

        # SHAP-ähnliche Erklärungen: Beiträge pro Faktor (in Score-Punkten)
        explanations = {k: round(v * 100.0, 2) for k, v in components.items() if abs(v) > 1e-6}

        reasons = list(scr.reasons)
        if label_component >= 0.9:
            reasons.append("High-risk labels present")
        elif label_component >= 0.4:
            reasons.append("Exchange/DEX-related labels")
        elif label_component > 0.0:
            reasons.append("Generic labels present")

        if threat_component >= 0.8:
            reasons.append("Critical threat intelligence match")
        elif threat_component >= 0.5:
            reasons.append("High threat intelligence indicators")

        categories = sorted(list(set(scr.categories + cats + threat_cats)))
        # Optional: persist score to graph
        try:
            if (
                os.getenv("TEST_MODE") != "1"
                and os.getenv("OFFLINE_MODE") != "1"
                and bool(getattr(settings, "RISK_PERSIST_TO_GRAPH", False))
            ):
                await neo4j_client.set_address_risk_score(addr, float(score))
        except Exception:
            pass

        return RiskScoreResult(
            chain=chain,
            address=addr,
            score=score,
            factors={
                "watchlist": watch_component,
                "labels": label_component,
                "taint": taint_component,
                "exposure": exposure,
                "graph": graph_component,
                "threat_intel": threat_component,
            },
            categories=categories,
            reasons=reasons,
            explanations=explanations,
        )

    def get_weights(self) -> Dict[str, float]:
        """Aktuelle Gewichtungen zurückgeben."""
        return {
            "watchlist": self.w_watchlist,
            "labels": self.w_labels,
            "taint": self.w_taint,
            "exposure": self.w_exposure,
            "graph": self.w_graph,
            "threat_intel": self.w_threat_intel,
        }

    def set_weights(self, **weights: float) -> Dict[str, float]:
        """Gewichte setzen (einzeln oder mehrere). Werte werden auf [0,1] geklammert."""
        for key, val in weights.items():
            if key not in {"watchlist", "labels", "taint", "exposure", "graph", "threat_intel"}:
                continue
            try:
                v = float(val)
            except Exception:
                continue
            v = max(0.0, min(1.0, v))
            if key == "watchlist":
                self.w_watchlist = v
            elif key == "labels":
                self.w_labels = v
            elif key == "taint":
                self.w_taint = v
            elif key == "exposure":
                self.w_exposure = v
            elif key == "graph":
                self.w_graph = v
            elif key == "threat_intel":
                self.w_threat_intel = v
        return self.get_weights()


service = RiskService()
