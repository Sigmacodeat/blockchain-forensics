from __future__ import annotations
import os
import logging
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from app.compliance.vasp.service import vasp_service
from app.compliance.vasp.models import VaspRiskLevel, ComplianceStatus
from app.repos import vasp_risk_repo


logger = logging.getLogger(__name__)

try:  # Optional metrics, tolerate absence during certain test runs
    from app.metrics import (
        VASP_RISK_SCORED_TOTAL,
        VASP_RISK_SCORE_DISTRIBUTION,
        VASP_RISK_LAST_SCORE,
    )
except Exception:  # pragma: no cover - metrics should not break functionality
    VASP_RISK_SCORED_TOTAL = None
    VASP_RISK_SCORE_DISTRIBUTION = None
    VASP_RISK_LAST_SCORE = None


class VaspRiskRecord(BaseModel):
    vasp_id: str
    vasp_name: str
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    overall_risk: VaspRiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    compliance_status: ComplianceStatus
    sanctions_hit: bool = False
    pep_hit: bool = False
    adverse_media_hit: bool = False
    adverse_media_count: int = 0
    recommended_action: Literal["approve", "review", "reject", "monitor"] = "review"
    risk_factors: List[str] = Field(default_factory=list)
    compliance_issues: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VaspRiskRegistry:
    def __init__(self, enable_persistence: Optional[bool] = None) -> None:
        self._records_by_vasp: Dict[str, List[VaspRiskRecord]] = {}
        if enable_persistence is None:
            self._persist = os.getenv("ENABLE_VASP_RISK_PERSISTENCE", "1") == "1"
        else:
            self._persist = enable_persistence

    def _cache_record(self, rec: VaspRiskRecord) -> None:
        arr = self._records_by_vasp.setdefault(rec.vasp_id, [])
        arr.append(rec)
        if len(arr) > 50:
            self._records_by_vasp[rec.vasp_id] = arr[-50:]

    def _persist_record(self, rec: VaspRiskRecord) -> None:
        if not self._persist:
            return
        try:
            vasp_risk_repo.insert_record({
                "vasp_id": rec.vasp_id,
                "vasp_name": rec.vasp_name,
                "scored_at": rec.scored_at,
                "overall_risk": rec.overall_risk.value,
                "risk_score": rec.risk_score,
                "compliance_status": rec.compliance_status.value,
                "sanctions_hit": rec.sanctions_hit,
                "pep_hit": rec.pep_hit,
                "adverse_media_hit": rec.adverse_media_hit,
                "adverse_media_count": rec.adverse_media_count,
                "recommended_action": rec.recommended_action,
                "risk_factors": rec.risk_factors,
                "compliance_issues": rec.compliance_issues,
                "metadata": rec.metadata,
            })
        except Exception as exc:  # pragma: no cover - persistence failures shouldn't break scoring
            logger.warning("Failed to persist VASP risk record for %s: %s", rec.vasp_id, exc)

    def _dict_to_record(self, data: Dict[str, Any]) -> VaspRiskRecord:
        try:
            risk_level = VaspRiskLevel(data.get("overall_risk", "unknown"))
        except Exception:
            risk_level = VaspRiskLevel.UNKNOWN
        try:
            compliance_status = ComplianceStatus(data.get("compliance_status", "unknown"))
        except Exception:
            compliance_status = ComplianceStatus.UNKNOWN
        return VaspRiskRecord(
            vasp_id=str(data.get("vasp_id")),
            vasp_name=str(data.get("vasp_name", "")),
            scored_at=data.get("scored_at") or datetime.utcnow(),
            overall_risk=risk_level,
            risk_score=float(data.get("risk_score") or 0.0),
            compliance_status=compliance_status,
            sanctions_hit=bool(data.get("sanctions_hit", False)),
            pep_hit=bool(data.get("pep_hit", False)),
            adverse_media_hit=bool(data.get("adverse_media_hit", False)),
            adverse_media_count=int(data.get("adverse_media_count", 0)),
            recommended_action=str(data.get("recommended_action", "review")),
            risk_factors=list(data.get("risk_factors", []) or []),
            compliance_issues=list(data.get("compliance_issues", []) or []),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    def add_record(self, rec: VaspRiskRecord) -> None:
        self._cache_record(rec)
        if VASP_RISK_SCORED_TOTAL:
            try:
                VASP_RISK_SCORED_TOTAL.labels(rec.vasp_id, rec.overall_risk.value, rec.compliance_status.value).inc()
                VASP_RISK_LAST_SCORE.labels(rec.vasp_id).set(rec.risk_score)
                VASP_RISK_SCORE_DISTRIBUTION.observe(rec.risk_score)
            except Exception:  # pragma: no cover - metrics failures should not break flow
                pass
        self._persist_record(rec)

    def last(self, vasp_id: str) -> Optional[VaspRiskRecord]:
        arr = self._records_by_vasp.get(vasp_id) or []
        if arr:
            return arr[-1]
        if self._persist:
            data = vasp_risk_repo.fetch_last_record(vasp_id)
            if data:
                rec = self._dict_to_record(data)
                self._cache_record(rec)
                return rec
        return None

    def list(self, vasp_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[VaspRiskRecord]:
        if self._persist:
            if vasp_id:
                rows = vasp_risk_repo.fetch_latest_for_vasp(vasp_id, limit, offset)
            else:
                rows = vasp_risk_repo.fetch_latest_global(limit, offset)
            records = [self._dict_to_record(row) for row in rows]
            for rec in records:
                self._cache_record(rec)
            return records
        if vasp_id:
            arr = self._records_by_vasp.get(vasp_id) or []
            return arr[max(0, offset): max(0, offset) + max(0, limit)]
        out: List[VaspRiskRecord] = []
        for arr in self._records_by_vasp.values():
            out.extend(arr)
        out.sort(key=lambda r: r.scored_at, reverse=True)
        return out[max(0, offset): max(0, offset) + max(0, limit)]

    async def score_vasp(self, vasp_id: str) -> Optional[VaspRiskRecord]:
        res = await vasp_service.screen_vasp(vasp_id)
        if not res:
            return None
        rec = VaspRiskRecord(
            vasp_id=res.vasp_id,
            vasp_name=res.vasp_name,
            overall_risk=res.overall_risk,
            risk_score=res.risk_score,
            compliance_status=res.compliance_status,
            sanctions_hit=res.sanctions_hit,
            pep_hit=res.pep_hit,
            adverse_media_hit=res.adverse_media_hit,
            adverse_media_count=res.adverse_media_count,
            recommended_action=res.recommended_action,
            risk_factors=res.risk_factors,
            compliance_issues=res.compliance_issues,
            metadata=res.metadata,
        )
        self.add_record(rec)
        return rec

    async def score_many(self, vasp_ids: List[str]) -> List[VaspRiskRecord]:
        out: List[VaspRiskRecord] = []
        for vid in vasp_ids:
            try:
                r = await self.score_vasp(vid)
                if r:
                    out.append(r)
            except Exception:
                continue
        return out

    def summary(self) -> Dict[str, Any]:
        """Aggregate summary over last records per VASP."""
        if self._persist:
            summary = vasp_risk_repo.fetch_summary()
            if summary:
                return summary
        by_level: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        scores: List[float] = []
        total = 0
        for vid, arr in self._records_by_vasp.items():
            if not arr:
                continue
            last = arr[-1]
            total += 1
            by_level[last.overall_risk.value] = by_level.get(last.overall_risk.value, 0) + 1
            by_status[last.compliance_status.value] = by_status.get(last.compliance_status.value, 0) + 1
            try:
                scores.append(float(last.risk_score))
            except Exception:
                pass
        avg = (sum(scores) / len(scores)) if scores else 0.0
        return {
            "total_vasps_scored": total,
            "by_risk_level": by_level,
            "by_compliance_status": by_status,
            "avg_risk_score": round(avg, 4),
        }


vasp_risk_registry = VaspRiskRegistry()
