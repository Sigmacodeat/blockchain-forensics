"""
Alert Annotation Service
========================
Persistiert Dispositionen und Eventzeiten für Alerts, um KPIs
(FPR/MTTD) stabil und auditierbar zu machen.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional, Any
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.models.alert_annotation import AlertAnnotation
from app.models.case import Base  # noqa: F401 (ensures metadata is loaded)
try:
    from app.db.session import SessionLocal  # type: ignore
except Exception:
    SessionLocal = None  # type: ignore

logger = logging.getLogger(__name__)


class AlertAnnotationService:
    def __init__(self, db_session: Optional[Session] = None) -> None:
        self.db_session = db_session

    def _get_db(self) -> Session:
        if self.db_session is not None:
            return self.db_session
        if SessionLocal is None:
            raise RuntimeError("SessionLocal is unavailable (no DB in test mode)")
        return SessionLocal()

    def ensure_table(self) -> None:
        # Falls kein Migrationssystem: create-if-not-exists
        try:
            if SessionLocal is None:
                return
            from sqlalchemy import inspect
            db = self._get_db()
            insp = inspect(db.bind)
            if not insp.has_table(AlertAnnotation.__tablename__):
                AlertAnnotation.__table__.create(bind=db.bind, checkfirst=True)
        except Exception as e:
            logger.warning(f"ensure_table failed: {e}")

    def set_disposition(self, alert_id: str, disposition: str) -> None:
        db = self._get_db()
        try:
            now = datetime.utcnow()
            ann = db.execute(
                select(AlertAnnotation).where(AlertAnnotation.alert_id == alert_id)
            ).scalar_one_or_none()
            if ann is None:
                ann = AlertAnnotation(alert_id=alert_id, disposition=disposition, created_at=now, updated_at=now)
                db.add(ann)
            else:
                db.execute(
                    update(AlertAnnotation)
                    .where(AlertAnnotation.id == ann.id)
                    .values(disposition=disposition, updated_at=now)
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            if self.db_session is None:
                db.close()

    def set_event_time(self, alert_id: str, event_time: datetime) -> None:
        db = self._get_db()
        try:
            now = datetime.utcnow()
            ann = db.execute(
                select(AlertAnnotation).where(AlertAnnotation.alert_id == alert_id)
            ).scalar_one_or_none()
            if ann is None:
                ann = AlertAnnotation(alert_id=alert_id, event_time=event_time, created_at=now, updated_at=now)
                db.add(ann)
            else:
                db.execute(
                    update(AlertAnnotation)
                    .where(AlertAnnotation.id == ann.id)
                    .values(event_time=event_time, updated_at=now)
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            if self.db_session is None:
                db.close()

    def get_annotations_map(self, alert_ids: Iterable[str]) -> Dict[str, AlertAnnotation]:
        ids = list(set(alert_ids))
        if not ids:
            return {}
        db = self._get_db()
        try:
            rows: List[AlertAnnotation] = list(
                db.execute(select(AlertAnnotation).where(AlertAnnotation.alert_id.in_(ids))).scalars()
            )
            return {r.alert_id: r for r in rows}
        finally:
            if self.db_session is None:
                db.close()

    def get_disposition_stats(self, since: Optional[datetime] = None, until: Optional[datetime] = None) -> Dict[str, Any]:
        db = self._get_db()
        try:
            stmt = select(AlertAnnotation)
            if since is not None:
                stmt = stmt.where(AlertAnnotation.created_at >= since)
            if until is not None:
                stmt = stmt.where(AlertAnnotation.created_at <= until)
            rows: List[AlertAnnotation] = list(db.execute(stmt).scalars())
            counts: Dict[str, int] = {}
            reviewed = 0
            for r in rows:
                d = (r.disposition or "").strip().lower() if r.disposition else None
                if d:
                    counts[d] = counts.get(d, 0) + 1
                    reviewed += 1
            fp = counts.get("false_positive", 0)
            denom = reviewed if reviewed > 0 else 1
            rate = fp / denom
            return {
                "counts": counts,
                "reviewed": reviewed,
                "false_positive_rate": rate,
                "window": {
                    "since": since.isoformat() if since else None,
                    "until": until.isoformat() if until else None,
                },
            }
        finally:
            if self.db_session is None:
                db.close()

    def get_mttd_seconds(self, since: Optional[datetime] = None, until: Optional[datetime] = None) -> Dict[str, Any]:
        db = self._get_db()
        try:
            stmt = select(AlertAnnotation)
            if since is not None:
                stmt = stmt.where(AlertAnnotation.created_at >= since)
            if until is not None:
                stmt = stmt.where(AlertAnnotation.created_at <= until)
            rows: List[AlertAnnotation] = list(db.execute(stmt).scalars())
            samples: List[float] = []
            for r in rows:
                if r.event_time and r.created_at and r.created_at >= r.event_time:
                    delta = (r.created_at - r.event_time).total_seconds()
                    samples.append(float(delta))
            avg = (sum(samples) / len(samples)) if samples else 0.0
            return {
                "count": len(samples),
                "average_seconds": avg,
                "window": {
                    "since": since.isoformat() if since else None,
                    "until": until.isoformat() if until else None,
                },
            }
        finally:
            if self.db_session is None:
                db.close()

    def get_kpi_summary(self, since: Optional[datetime] = None, until: Optional[datetime] = None) -> Dict[str, Any]:
        disp = self.get_disposition_stats(since=since, until=until)
        mttd = self.get_mttd_seconds(since=since, until=until)
        return {
            "dispositions": disp,
            "mttd": mttd,
        }


# Global instance
alert_annotation_service = AlertAnnotationService()
try:
    alert_annotation_service.ensure_table()
except Exception:
    # In Test/ohne DB still allow import
    pass
