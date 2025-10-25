"""
Exposure Service
=================

Berechnung von Direct/Indirect Exposure zu Hochrisiko-/Sanktions-Entitäten.
Ziel: leichte, schnelle Heuristiken als Grundbaustein (später erweiterbar).
"""
from __future__ import annotations

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExposureResult:
    address: str
    direct_exposure: bool
    max_hops: int
    indirect_hops: Optional[int]
    exposure_share: float
    labels_seen: List[str]
    paths_examined: int
    computed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "direct_exposure": self.direct_exposure,
            "max_hops": self.max_hops,
            "indirect_hops": self.indirect_hops,
            "exposure_share": self.exposure_share,
            "labels_seen": self.labels_seen,
            "paths_examined": self.paths_examined,
            "computed_at": self.computed_at,
        }


class ExposureService:
    """
    Minimaler Exposure-Calculator (Heuristik):
    - Prüft Labels (sanctioned/high_risk) für direkte Exposition
    - Nutzt leichtgewichtige Heuristik für indirekte Exposition (via bereitgestellten Events/Graph-Summary)
    - exposure_share: Platzhalter (0..1), später durch Taint/Flow ersetzt
    """

    def __init__(self):
        # spätere Injektion von Graph/Tracing-Backend
        self.max_hops_default = 3

    async def calculate(
        self,
        address: str,
        max_hops: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExposureResult:
        # sanitize address
        address = (address or "").strip()
        # sanitize hops
        try:
            mh = int(max_hops) if max_hops is not None else self.max_hops_default
        except Exception:
            mh = self.max_hops_default
        max_hops = mh if mh > 0 else self.max_hops_default

        # context normalization
        ctx = context if isinstance(context, dict) else {}
        raw_labels = ctx.get("labels", []) or []
        if not isinstance(raw_labels, list):
            raw_labels = [str(raw_labels)]
        labels = []
        for l in raw_labels:
            try:
                ls = str(l).strip()
                if ls:
                    labels.append(ls)
            except Exception:
                continue

        # Direkte Exposition, wenn bereits sanktioniert/high_risk
        direct = any(l in {"sanctioned", "ofac", "high_risk"} for l in labels)

        # Indirekte Exposition (heuristisch):
        # Erwartet optional ctx["graph_summary"] mit z.B. {"sanctioned_hops": int, "exposure_share": float}
        graph_summary = ctx.get("graph_summary", {}) if isinstance(ctx.get("graph_summary", {}), dict) else {}
        sanctioned_hops = graph_summary.get("sanctioned_hops")
        try:
            exposure_share = float(graph_summary.get("exposure_share", 0.0))
        except Exception:
            exposure_share = 0.0
        try:
            paths_examined = int(graph_summary.get("paths_examined", 0))
        except Exception:
            paths_examined = 0

        # Wenn keine Graph-Daten: fallback auf einfache Heuristik
        if sanctioned_hops is None:
            # Heuristik: wenn Labels auf Gegenparteien hindeuten (ctx["counterparty_labels"]) -> 2 Hops annehmen
            cps = ctx.get("counterparty_labels", []) or []
            has_risky_cp = any("sanction" in str(c).lower() or "mixer" in str(c).lower() for c in cps)
            sanctioned_hops = 2 if has_risky_cp else None
            exposure_share = 0.2 if has_risky_cp else 0.0
            paths_examined = paths_examined or (10 if has_risky_cp else 0)

        # Begrenze Hops auf max_hops
        if isinstance(sanctioned_hops, (int, float)) and sanctioned_hops is not None and sanctioned_hops > max_hops:
            sanctioned_hops = None  # außerhalb Fenster
            exposure_share = 0.0

        # clamp share to [0,1]
        try:
            if exposure_share < 0.0:
                exposure_share = 0.0
            if exposure_share > 1.0:
                exposure_share = 1.0
        except Exception:
            exposure_share = 0.0

        return ExposureResult(
            address=address,
            direct_exposure=direct,
            max_hops=max_hops,
            indirect_hops=sanctioned_hops,
            exposure_share=exposure_share,
            labels_seen=labels,
            paths_examined=paths_examined,
            computed_at=datetime.utcnow().isoformat(),
        )

    async def batch_calculate(
        self,
        addresses: List[str],
        max_hops: Optional[int] = None,
        context_by_address: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        res: Dict[str, Dict[str, Any]] = {}
        for a in addresses:
            r = await self.calculate(a, max_hops=max_hops, context=(context_by_address or {}).get(a))
            res[a] = r.to_dict()
        return res


# Singleton
exposure_service = ExposureService()
