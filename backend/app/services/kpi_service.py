from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from app.services.alert_service import alert_service
from app.services.alert_annotation_service import alert_annotation_service
try:
    from app.services.case_service import case_service
except Exception:
    case_service = None  # type: ignore
from app.repos.sanctions_repository import sanctions_repository
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


@dataclass
class KpiResult:
    fpr: float
    mttr: float
    mttd: float
    sla_breach_rate: float
    sanctions_hits: int


class KpiService:
    def _cache_key(self, *, days: int, sla_hours: int) -> str:
        return f"kpis:{days}:{sla_hours}"

    async def get_kpis(self, *, days: int, sla_hours: int) -> KpiResult:
        # Try cache first
        try:
            cached = await redis_client.cache_get(self._cache_key(days=days, sla_hours=sla_hours))
            if cached and isinstance(cached, dict):
                return KpiResult(
                    fpr=float(cached.get("fpr", 0.0)),
                    mttr=float(cached.get("mttr", 0.0)),
                    mttd=float(cached.get("mttd", 0.0)),
                    sla_breach_rate=float(cached.get("sla_breach_rate", 0.0)),
                    sanctions_hits=int(cached.get("sanctions_hits", 0)),
                )
        except Exception:
            pass
        cutoff = datetime.utcnow() - timedelta(days=days)
        # Pull recent alerts via facade and filter by cutoff locally
        try:
            recent_alerts = alert_service.get_recent_alerts(limit=10000)
        except Exception:
            recent_alerts = []
        alerts = [a for a in recent_alerts if getattr(a, "timestamp", cutoff) >= cutoff]
        alerts_by_id = {getattr(a, "alert_id", None): a for a in alerts}

        # Sanctions hits
        addresses: List[str] = []
        for aid, a in alerts_by_id.items():
            addr = getattr(a, "address", None)
            if isinstance(addr, str) and addr:
                addresses.append(addr)
        sanctions_hits = 0
        try:
            sanctions_hits = await sanctions_repository.count_distinct_hits(addresses)
        except Exception:
            sanctions_hits = 0

        # False Positive Rate via annotations/dispositions
        total_alerts = len(alerts)
        alert_ids = [a.alert_id for a in alerts]
        annotations = {}
        try:
            annotations = alert_annotation_service.get_annotations_map(alert_ids)
        except Exception as e:
            logger.warning(f"Failed loading alert annotations: {e}")

        def _get_disposition(aid: str) -> Optional[str]:
            ann = annotations.get(aid)
            return getattr(ann, "disposition", None)

        fp_ids = {aid for aid in alert_ids if _get_disposition(aid) == "false_positive"}
        tp_ids = {aid for aid in alert_ids if _get_disposition(aid) == "true_positive"}
        labeled = len(fp_ids) + len(tp_ids)
        if total_alerts > 0 and labeled > 0:
            fpr = len(fp_ids) / max(1, labeled)
        else:
            # Fallback: suppression total as proxy for noise
            try:
                supp_stats = alert_service.get_suppression_statistics()
                false_positives = int(supp_stats.get("total_suppressions", 0))
            except Exception:
                false_positives = 0
            fpr = (false_positives / total_alerts) if total_alerts > 0 else 0.0

        # MTTR / SLA from cases
        mttr_hours = 0.0
        sla_breach_rate = 0.0
        try:
            cases = []
            if case_service is not None:
                result = case_service.query_cases(limit=1000, offset=0)
                cases = result.get("cases", [])
            closed_durations: List[float] = []
            breaches = 0
            total_closed = 0
            for c in cases:
                created_at = c.get("created_at")
                closed_at = c.get("closed_at")
                if not created_at or not closed_at:
                    continue
                try:
                    ca = datetime.fromisoformat(created_at)
                    clo = datetime.fromisoformat(closed_at)
                except Exception:
                    continue
                if clo < cutoff:
                    continue
                dur_hours = max(0.0, (clo - ca).total_seconds() / 3600.0)
                closed_durations.append(dur_hours)
                total_closed += 1
                if dur_hours > float(sla_hours):
                    breaches += 1

            if closed_durations:
                closed_durations.sort()
                n = len(closed_durations)
                if n % 2 == 1:
                    mttr_hours = closed_durations[n // 2]
                else:
                    mttr_hours = (closed_durations[n // 2 - 1] + closed_durations[n // 2]) / 2.0
                sla_breach_rate = (breaches / total_closed) if total_closed > 0 else 0.0
        except Exception as ce:
            logger.warning(f"MTTR/SLA computation failed: {ce}")

        # MTTD using annotation.event_time vs alert first seen
        total_detection_time = 0.0
        detection_count = 0
        for aid, ann in annotations.items():
            if getattr(ann, "event_time", None) and aid in alerts_by_id:
                try:
                    first_seen = getattr(alerts_by_id[aid], "timestamp", None)
                    if first_seen:
                        det = (first_seen - ann.event_time).total_seconds() / 3600.0
                        if det >= 0:
                            total_detection_time += det
                            detection_count += 1
                except Exception:
                    pass
        mttd = (total_detection_time / detection_count) if detection_count > 0 else 0.0

        result = KpiResult(
            fpr=float(fpr),
            mttr=float(mttr_hours),
            mttd=float(mttd),
            sla_breach_rate=float(sla_breach_rate),
            sanctions_hits=int(sanctions_hits),
        )
        # Store in cache (5 minutes)
        try:
            await redis_client.cache_set(
                self._cache_key(days=days, sla_hours=sla_hours),
                {
                    "fpr": result.fpr,
                    "mttr": result.mttr,
                    "mttd": result.mttd,
                    "sla_breach_rate": result.sla_breach_rate,
                    "sanctions_hits": result.sanctions_hits,
                },
                ttl=300,
            )
        except Exception:
            pass

        return result


kpi_service = KpiService()
