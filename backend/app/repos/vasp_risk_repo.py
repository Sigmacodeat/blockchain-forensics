from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.vasp_risk_record import VaspRiskRecordORM


def _create_session() -> Optional[Session]:
    try:
        return SessionLocal()
    except Exception:
        return None


def insert_record(data: Dict[str, Any]) -> None:
    session = _create_session()
    if session is None:
        return
    try:
        obj = VaspRiskRecordORM(
            vasp_id=data["vasp_id"],
            vasp_name=data["vasp_name"],
            scored_at=data["scored_at"],
            overall_risk=str(data["overall_risk"]),
            risk_score=float(data["risk_score"]),
            compliance_status=str(data["compliance_status"]),
            sanctions_hit=bool(data.get("sanctions_hit", False)),
            pep_hit=bool(data.get("pep_hit", False)),
            adverse_media_hit=bool(data.get("adverse_media_hit", False)),
            adverse_media_count=int(data.get("adverse_media_count", 0)),
            recommended_action=str(data.get("recommended_action", "review")),
            risk_factors=list(data.get("risk_factors", [])),
            compliance_issues=list(data.get("compliance_issues", [])),
            metadata=dict(data.get("metadata", {})),
        )
        session.add(obj)
        session.commit()
    except (SQLAlchemyError, OperationalError):
        session.rollback()
        raise
    finally:
        session.close()


def _orm_to_dict(obj: VaspRiskRecordORM) -> Dict[str, Any]:
    return {
        "vasp_id": obj.vasp_id,
        "vasp_name": obj.vasp_name,
        "scored_at": obj.scored_at,
        "overall_risk": obj.overall_risk,
        "risk_score": obj.risk_score,
        "compliance_status": obj.compliance_status,
        "sanctions_hit": obj.sanctions_hit,
        "pep_hit": obj.pep_hit,
        "adverse_media_hit": obj.adverse_media_hit,
        "adverse_media_count": obj.adverse_media_count,
        "recommended_action": obj.recommended_action,
        "risk_factors": obj.risk_factors or [],
        "compliance_issues": obj.compliance_issues or [],
        "metadata": obj.metadata or {},
    }


def fetch_latest_for_vasp(vasp_id: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    session = _create_session()
    if session is None:
        return []
    try:
        stmt = (
            select(VaspRiskRecordORM)
            .where(VaspRiskRecordORM.vasp_id == vasp_id)
            .order_by(desc(VaspRiskRecordORM.scored_at))
            .offset(max(0, offset))
            .limit(max(0, limit))
        )
        rows = session.execute(stmt).scalars().all()
        return [_orm_to_dict(obj) for obj in rows]
    finally:
        session.close()


def fetch_latest_global(limit: int, offset: int) -> List[Dict[str, Any]]:
    session = _create_session()
    if session is None:
        return []
    try:
        stmt = (
            select(VaspRiskRecordORM)
            .order_by(desc(VaspRiskRecordORM.scored_at))
            .offset(max(0, offset))
            .limit(max(0, limit))
        )
        rows = session.execute(stmt).scalars().all()
        return [_orm_to_dict(obj) for obj in rows]
    finally:
        session.close()


def fetch_last_record(vasp_id: str) -> Optional[Dict[str, Any]]:
    rows = fetch_latest_for_vasp(vasp_id, limit=1, offset=0)
    return rows[0] if rows else None


def fetch_summary() -> Optional[Dict[str, Any]]:
    session = _create_session()
    if session is None:
        return None
    try:
        row_number = func.row_number().over(
            partition_by=VaspRiskRecordORM.vasp_id,
            order_by=VaspRiskRecordORM.scored_at.desc(),
        )
        subquery = (
            select(
                VaspRiskRecordORM.vasp_id.label("vasp_id"),
                VaspRiskRecordORM.vasp_name.label("vasp_name"),
                VaspRiskRecordORM.overall_risk.label("overall_risk"),
                VaspRiskRecordORM.compliance_status.label("compliance_status"),
                VaspRiskRecordORM.risk_score.label("risk_score"),
                row_number.label("rn"),
            )
        ).subquery()

        stmt = select(subquery).where(subquery.c.rn == 1)
        rows = session.execute(stmt).all()
        if not rows:
            return None

        total = len(rows)
        by_level: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        scores: List[float] = []

        for r in rows:
            data = r._mapping
            risk_level = data["overall_risk"]
            status = data["compliance_status"]
            score = float(data["risk_score"] or 0.0)
            by_level[risk_level] = by_level.get(risk_level, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            scores.append(score)

        avg = sum(scores) / len(scores) if scores else 0.0
        return {
            "total_vasps_scored": total,
            "by_risk_level": by_level,
            "by_compliance_status": by_status,
            "avg_risk_score": round(avg, 4),
        }
    finally:
        session.close()


def update_last_record_review(
    vasp_id: str,
    review_status: str,
    reviewed_by: str,
    notes: Optional[str] = None,
    recommended_action: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update review metadata on the latest record for a VASP and return the updated row.

    Stores fields under metadata.review: { status, reviewed_by, reviewed_at, notes } and optionally updates
    recommended_action column if provided.
    """
    session = _create_session()
    if session is None:
        return None
    try:
        stmt = (
            select(VaspRiskRecordORM)
            .where(VaspRiskRecordORM.vasp_id == vasp_id)
            .order_by(desc(VaspRiskRecordORM.scored_at))
            .limit(1)
        )
        obj = session.execute(stmt).scalars().first()
        if not obj:
            return None

        # Merge review into metadata
        meta = dict(obj.metadata or {})
        review_block = dict(meta.get("review", {}))
        review_block.update(
            {
                "status": review_status,
                "reviewed_by": reviewed_by,
                "reviewed_at": (obj.scored_at or None) and obj.scored_at.isoformat(),
            }
        )
        if notes is not None:
            review_block["notes"] = notes
        meta["review"] = review_block
        obj.metadata = meta

        if recommended_action:
            obj.recommended_action = str(recommended_action)

        session.add(obj)
        session.commit()
        session.refresh(obj)
        return _orm_to_dict(obj)
    except (SQLAlchemyError, OperationalError):
        session.rollback()
        raise
    finally:
        session.close()
