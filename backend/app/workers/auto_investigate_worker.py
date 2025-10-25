"""
Auto-Investigate Worker
- Nimmt Jobs aus einer In-Memory Queue entgegen
- Persistiert Case/Entity/Evidence (Datei-Snapshots via CaseService)
- Enqueued Trace-Request (Kafka falls aktiviert)
- Heartbeats & Prometheus-Metriken
"""
import asyncio
import logging
import time
import json
import uuid
import hashlib
from typing import Any, Dict, Optional, List, Tuple
from collections import deque
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.cases.service import case_service
from app.cases.models import Entity, EvidenceLink
from app.streaming.event_publisher import event_publisher
from app.ml.risk_scorer import risk_scorer
from app.bridge.registry import bridge_registry
from app.services.alert_service import alert_service
from app.config import settings
from app.observability.metrics import (
    WORKER_STATUS,
    WORKER_PROCESSED_TOTAL,
    WORKER_ERRORS_TOTAL,
    WORKER_LAST_HEARTBEAT,
)

logger = logging.getLogger(__name__)

_queue: Optional[asyncio.Queue] = None
_task: Optional[asyncio.Task] = None
_running = False
_recent: deque = deque(maxlen=50)
_WORKER_NAME = "auto_investigate"
_recent_keys: deque = deque(maxlen=200)


def _job_key(job: Dict[str, Any]) -> str:
    addr = (job.get("address") or "").lower().strip()
    chain = (job.get("chain") or "ethereum").lower().strip()
    depth = int(job.get("depth") or 0)
    settings = job.get("settings") or {}
    payload = f"{addr}|{chain}|{depth}|{hashlib.sha256(str(sorted(settings.items())).encode('utf-8')).hexdigest()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def _persist_case_and_links(job: Dict[str, Any]) -> Tuple[str, Optional[EvidenceLink]]:
    """Create a minimal case (if needed) and attach entity/evidence.
    Returns (case_id, evidence_link_or_none)
    """
    addr = job.get("address")
    chain = job.get("chain") or "ethereum"
    depth = int(job.get("depth") or 0)
    # Generate deterministic-ish case_id for same addr/chain within a short window if not provided
    case_id = job.get("case_id") or f"CASE-AUTO-{addr[:6]}-{int(time.time())}"

    # Create case if not exists (CaseService keeps in-memory map; idempotent for same id)
    if case_id not in case_service._cases:  # type: ignore[attr-defined]
        title = f"Auto Investigation for {addr}"
        desc = f"Automated investigation initiated for {addr} on {chain} (depth={depth})."
        case_service.create_case(case_id=case_id, title=title, description=desc, lead_investigator="auto")

    # Ensure entity is linked
    try:
        entity = Entity(address=addr, chain=chain, labels={"source": "auto_investigate"})
        case_service.add_entity(case_id, entity)
    except Exception:
        # best-effort; do not fail the workflow on entity errors
        pass

    # Link a synthetic evidence record describing the automation event
    try:
        ev_hash = hashlib.sha256(f"{addr}|{chain}|{depth}|{time.time()}".encode("utf-8")).hexdigest()
        link = EvidenceLink(
            case_id=case_id,
            resource_id=f"auto_investigate:{addr}",
            resource_type="automation_event",
            record_hash=ev_hash,
            notes=f"AutoInvestigation queued (depth={depth})",
        )
        case_service.link_evidence(link)
        return case_id, link
    except Exception:
        return case_id, None


async def _enqueue_trace(job: Dict[str, Any], case_id: str) -> Tuple[bool, Optional[str]]:
    """Publish a trace request via EventPublisher if Kafka enabled.
    Returns (published, request_id)
    """
    try:
        direction = (job.get("direction") or "forward").lower()
        max_depth = int(job.get("depth") or job.get("max_depth") or 3)
        chain = job.get("chain") or "ethereum"
        addr = job.get("address")
        request_id = str(uuid.uuid4())
        meta = {"case_id": case_id, "request_id": request_id, "source": "auto_investigate"}
        ok = await event_publisher.publish_trace_request(
            address=addr,
            direction=direction,
            max_depth=max_depth,
            chain=chain,
            metadata=meta,
        )
        return ok, request_id
    except Exception:
        return False, None


async def _ai_assess_and_alert(job: Dict[str, Any], case_id: str) -> None:
    """Run AI/ML assessments and alerts for the given job and attach evidence.
    Best-effort: never raise to caller.
    """
    addr = (job.get("address") or "").strip()
    chain = (job.get("chain") or "ethereum").strip()
    tx_hash = (job.get("tx_hash") or job.get("tx") or None) or None
    method_selector = (job.get("method_selector") or job.get("selector") or None) or None
    value_usd = None
    try:
        if job.get("value_usd") is not None:
            value_usd = float(job.get("value_usd"))
    except Exception:
        value_usd = None
    if not addr:
        return
    try:
        # 1) Risk Score
        risk: Dict[str, Any] = await risk_scorer.calculate_risk_score(addr)
        try:
            risk_json = json.dumps({"address": addr, **risk}, ensure_ascii=False, indent=2).encode("utf-8")
            meta = case_service.save_attachment(
                case_id,
                filename=f"risk_{addr[:8]}_{int(time.time())}.json",
                content=risk_json,
                content_type="application/json",
            )
            case_service.link_attachment_as_evidence(
                case_id,
                meta,
                notes=f"Risk assessment for {addr} (score={risk.get('risk_score')}, level={risk.get('risk_level')})",
            )
        except Exception:
            pass

        # 2) Bridge Lookup (contract-level)
        try:
            is_bridge = bridge_registry.is_bridge_contract(addr, chain)
            info: Dict[str, Any] = {"address": addr, "chain": chain, "is_bridge_contract": bool(is_bridge)}
            if is_bridge:
                contract = bridge_registry.get_contract(addr, chain)
                if contract:
                    info["contract"] = {
                        "address": contract.address,
                        "chain": contract.chain,
                        "name": contract.name,
                        "bridge_type": contract.bridge_type,
                        "counterpart_chains": contract.counterpart_chains,
                        "method_selectors": contract.method_selectors,
                        "added_at": contract.added_at.isoformat(),
                    }
            # Optional: method selector check if provided by job
            if method_selector:
                try:
                    info["method_selector"] = method_selector
                    info["is_bridge_method"] = bridge_registry.is_bridge_method(method_selector)
                except Exception:
                    info["is_bridge_method_error"] = True

            bridge_bytes = json.dumps(info, ensure_ascii=False, indent=2).encode("utf-8")
            meta_b = case_service.save_attachment(
                case_id,
                filename=f"bridge_{addr[:8]}_{int(time.time())}.json",
                content=bridge_bytes,
                content_type="application/json",
            )
            case_service.link_attachment_as_evidence(
                case_id,
                meta_b,
                notes=f"Bridge registry check for {addr} on {chain}",
            )
        except Exception:
            pass

        # 3) Trigger alert if high risk
        try:
            score = float(risk.get("risk_score") or 0.0)
            threshold = getattr(settings, "AUTO_INVESTIGATE_HIGH_RISK_THRESHOLD", 0.7)
            if score >= float(threshold):
                event = {
                    "address": addr,
                    "risk_score": score,
                    "labels": risk.get("factors") or [],
                }
                if tx_hash:
                    event["tx_hash"] = tx_hash
                if value_usd is not None:
                    event["value_usd"] = value_usd
                if chain:
                    event["chain"] = chain
                alerts = await alert_service.process_event(event)
                out = {
                    "submitted_event": event,
                    "alerts_triggered": [a.to_dict() for a in alerts],
                    "count": len(alerts),
                }
                out_bytes = json.dumps(out, ensure_ascii=False, indent=2).encode("utf-8")
                meta_a = case_service.save_attachment(
                    case_id,
                    filename=f"alerts_{addr[:8]}_{int(time.time())}.json",
                    content=out_bytes,
                    content_type="application/json",
                )
                case_service.link_attachment_as_evidence(
                    case_id,
                    meta_a,
                    notes=f"Triggered alerts for high risk address {addr} (score={score})",
                )
        except Exception as e:
            logger.warning(f"[AutoInvestigate] Alert processing failed: {e}")
    except Exception as e:
        logger.warning(f"[AutoInvestigate] AI assessment failed: {e}")


async def _process_job(job: Dict[str, Any]):
    try:
        addr = job.get("address")
        chain = job.get("chain")
        depth = job.get("depth")
        settings = job.get("settings", {})
        logger.info(f"[AutoInvestigate] Start job: address={addr} chain={chain} depth={depth} settings={settings}")
        # Metrics heartbeat (best-effort)
        try:
            WORKER_STATUS.labels(worker="auto_investigate").set(1)
            WORKER_LAST_HEARTBEAT.labels(worker="auto_investigate").set(time.time())
        except Exception:
            pass

        # Persist Case (file-based via case_service)
        case_id = f"AUTO-{(chain or 'ethereum')}-{(addr or 'unknown')}-{int(time.time())}"
        title = f"Auto Investigate {addr}"
        description = f"Chain={chain} Depth={depth} Settings={settings}"
        try:
            case_service.create_case(case_id=case_id, title=title, description=description, lead_investigator="auto")
            case_service.add_entity(case_id, Entity(address=addr or "", chain=(chain or "ethereum"), labels=[]))
        except Exception as e:
            logger.warning(f"[AutoInvestigate] Case persistence failed: {e}")

        # Enqueue trace job (Kafka if enabled, otherwise no-op False)
        published, request_id = await _enqueue_trace(job, case_id)

        # Optional: generate and attach initial report snapshot
        try:
            export = case_service.export(case_id)
            # Save JSON snapshot as attachment and link as evidence
            json_bytes = (json.dumps(export, ensure_ascii=False, indent=2)).encode("utf-8")
            meta = case_service.save_attachment(case_id, filename=f"report_{case_id}.json", content=json_bytes, content_type="application/json")
            case_service.link_attachment_as_evidence(case_id, meta, notes="Initial auto-investigation snapshot (JSON)")
            # CSV export (entities/evidence)
            csvs = case_service.export_csv(case_id)
            ent_bytes = csvs.get("entities_csv", "").encode("utf-8")
            ev_bytes = csvs.get("evidence_csv", "").encode("utf-8")
            meta_ent = case_service.save_attachment(case_id, filename=f"entities_{case_id}.csv", content=ent_bytes, content_type="text/csv")
            case_service.link_attachment_as_evidence(case_id, meta_ent, notes="Entities CSV snapshot")
            meta_ev = case_service.save_attachment(case_id, filename=f"evidence_{case_id}.csv", content=ev_bytes, content_type="text/csv")
            case_service.link_attachment_as_evidence(case_id, meta_ev, notes="Evidence CSV snapshot")
        except Exception as e:
            logger.warning(f"[AutoInvestigate] Report export failed: {e}")

        # AI/ML assessments, bridge check and alerting (best-effort)
        try:
            await _ai_assess_and_alert(job, case_id)
        except Exception as e:
            logger.warning(f"[AutoInvestigate] AI/Alert phase failed: {e}")

        logger.info(f"[AutoInvestigate] Done job for {addr} (case_id={case_id}, trace_published={published})")
        _recent.appendleft({
            "address": addr,
            "chain": chain,
            "depth": depth,
            "status": "done",
            "case_id": case_id,
            "trace_request_id": request_id,
        })

        # Metrics: processed + heartbeat
        try:
            WORKER_PROCESSED_TOTAL.labels(worker=_WORKER_NAME).inc()
            WORKER_LAST_HEARTBEAT.labels(worker=_WORKER_NAME).set(time.time())
        except Exception:
            pass
        # Best-effort DB status update
        db = await _get_db_session()
        if db is not None:
            try:
                # Update latest matching automation_event to done
                await db.execute(
                    text(
                        """
                        UPDATE automation_events SET status='done'
                        WHERE id IN (
                          SELECT id FROM automation_events
                          WHERE address=:address AND chain=:chain AND depth=:depth
                          ORDER BY created_at DESC LIMIT 1
                        )
                        """
                    ),
                    {"address": addr, "chain": chain or "ethereum", "depth": int(depth or 0)},
                )
                # Update latest matching job to done
                await db.execute(
                    text(
                        """
                        UPDATE jobs SET status='done', updated_at=NOW()
                        WHERE id IN (
                          SELECT id FROM jobs
                          WHERE type='auto_investigate' AND payload->>'address' = :address
                          ORDER BY created_at DESC LIMIT 1
                        )
                        """
                    ),
                    {"address": addr},
                )
                await db.commit()
            except Exception as e:
                try:
                    await db.rollback()
                except Exception:
                    pass
                logger.warning(f"[AutoInvestigate] DB status update failed: {e}")
            finally:
                await _close_db_session(db)
    except Exception as e:
        logger.error(f"[AutoInvestigate] Job failed: {e}")
        _recent.appendleft({
            "address": job.get("address"),
            "chain": job.get("chain"),
            "depth": job.get("depth"),
            "status": "error",
            "error": str(e),
        })
        try:
            WORKER_ERRORS_TOTAL.labels(worker=_WORKER_NAME).inc()
            WORKER_LAST_HEARTBEAT.labels(worker=_WORKER_NAME).set(time.time())
        except Exception:
            pass
        # Best-effort DB status update to error
        try:
            db = await _get_db_session()
            if db is not None:
                try:
                    await db.execute(
                        text(
                            """
                            UPDATE automation_events SET status='error', error=:error
                            WHERE id IN (
                              SELECT id FROM automation_events
                              WHERE address=:address AND chain=:chain AND depth=:depth
                              ORDER BY created_at DESC LIMIT 1
                            )
                            """
                        ),
                        {
                            "address": job.get("address"),
                            "chain": job.get("chain") or "ethereum",
                            "depth": int(job.get("depth") or 0),
                            "error": str(e),
                        },
                    )
                    await db.execute(
                        text(
                            """
                            UPDATE jobs SET status='error', updated_at=NOW()
                            WHERE id IN (
                              SELECT id FROM jobs
                              WHERE type='auto_investigate' AND payload->>'address' = :address
                              ORDER BY created_at DESC LIMIT 1
                            )
                            """
                        ),
                        {"address": job.get("address")},
                    )
                    await db.commit()
                finally:
                    await _close_db_session(db)
        except Exception:
            pass


async def _worker_loop():
    global _running
    assert _queue is not None
    _running = True
    logger.info("[AutoInvestigate] Worker started")
    try:
        WORKER_STATUS.labels(worker=_WORKER_NAME).set(1)
        WORKER_LAST_HEARTBEAT.labels(worker=_WORKER_NAME).set(time.time())
    except Exception:
        pass
    while _running:
        try:
            job = await _queue.get()
            await _process_job(job)
            _queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[AutoInvestigate] Loop error: {e}")
            await asyncio.sleep(0.1)
    logger.info("[AutoInvestigate] Worker stopped")
    try:
        WORKER_STATUS.labels(worker=_WORKER_NAME).set(0)
        WORKER_LAST_HEARTBEAT.labels(worker=_WORKER_NAME).set(time.time())
    except Exception:
        pass


def start_auto_investigate_worker() -> asyncio.Task:
    global _queue, _task
    if _queue is None:
        _queue = asyncio.Queue()
    if _task is None or _task.done():
        _task = asyncio.create_task(_worker_loop())
    return _task


def stop_auto_investigate_worker():
    global _running, _task
    _running = False
    if _task and not _task.done():
        _task.cancel()


async def enqueue_auto_investigate(job: Dict[str, Any]):
    if _queue is None:
        raise RuntimeError("AutoInvestigate worker not started")
    key = _job_key(job)
    # Simple idempotency: skip if recently seen
    if key in _recent_keys:
        _recent.appendleft({
            "address": job.get("address"),
            "chain": job.get("chain"),
            "depth": job.get("depth"),
            "status": "duplicate_skipped",
        })
        return
    _recent_keys.appendleft(key)
    _recent.appendleft({
        "address": job.get("address"),
        "chain": job.get("chain"),
        "depth": job.get("depth"),
        "status": "queued",
    })
    await _queue.put(job)


def get_recent_jobs() -> List[Dict[str, Any]]:
    return list(_recent)


async def _get_db_session() -> Optional[AsyncSession]:
    """Return AsyncSession if available, else None. Safe in TEST_MODE."""
    try:
        from app.db.postgres_client import postgres_client  # lazy import
        AsyncSessionLocal = getattr(postgres_client, "AsyncSessionLocal", None)
        if AsyncSessionLocal is None:
            return None
        # Create a new session instance
        return AsyncSessionLocal()
    except Exception:
        return None


async def _close_db_session(db: Optional[AsyncSession]) -> None:
    try:
        if db is not None:
            await db.close()
    except Exception:
        pass
