from fastapi import APIRouter, Query, Body, HTTPException, Depends
from typing import Any, Dict, List
import os
from pydantic import BaseModel, field_validator, model_validator

from app.services.compliance_service import service
from app.observability.metrics import COMPLIANCE_REQUESTS, COMPLIANCE_LATENCY
from app.config import settings
from app.compliance.screening_engine import screening_engine
from app.compliance.sanctions_updater import sanctions_updater
from app.models.audit_log import log_audit_event, AuditAction
from app.compliance.sources.sanctions_indexer import sanctions_indexer
from app.compliance.travel_rule.adapters import travel_rule_manager, TravelRulePayload, TravelRuleResponse
from app.compliance.travel_rule.service import travel_rule_service
from app.compliance.vasp.service import vasp_service
from app.compliance.vasp_risk import vasp_risk_registry
from app.repos import vasp_risk_repo
from app.compliance.vasp.models import VaspType, VaspRiskLevel, ComplianceStatus
from app.auth.models import UserRole
from app.auth.dependencies import require_roles_if
from app.intel.exchange_liaison import (
    exchange_liaison_service,
    RequestType as ExchangeRequestType,
    RequestStatus as ExchangeRequestStatus,
)
from app.compliance.sar_str_generator import sar_generator
from app.compliance.sar_queue import sar_queue
from app.services.case_service import case_service
from app.services.evidence_service import evidence_service
from app.compliance.policy_engine import policy_engine
import time

router = APIRouter()


class WatchAdd(BaseModel):
    chain: str
    address: str
    reason: str = "manual"

    @field_validator('chain')
    @classmethod
    def validate_chain(cls, v: str) -> str:
        allowed = {"ethereum", "bitcoin", "solana"}
        vl = (v or "").lower()
        if vl not in allowed:
            raise ValueError(f"unsupported chain: {v}")
        return vl

    @field_validator('address')
    @classmethod
    def normalize_address(cls, v: str) -> str:
        return (v or "").strip().lower()

    @model_validator(mode="after")
    def validate_address_by_chain(self):
        import re
        c = (self.chain or "").lower()
        addr = (self.address or "").strip()
        ok = True
        if c == "ethereum":
            ok = bool(re.fullmatch(r"0x[0-9a-f]{40}", addr))
        elif c == "bitcoin":
            ok = bool(re.fullmatch(r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}", addr)) or bool(
                re.fullmatch(r"bc1[ac-hj-np-z02-9]{11,71}", addr)
            )
        elif c == "solana":
            ok = bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", addr))
        if not ok:
            raise ValueError(f"invalid {c} address format")
        return self


@router.get("/screen", summary="Screen an address for risk")
async def screen(chain: str = Query(...), address: str = Query(...)) -> Dict[str, Any]:
    op = "screen"
    start = time.time()
    try:
        res = service.screen(chain, address)
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"result": res.__dict__}
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sar/process/{report_id}")
async def process_sar_report(report_id: str, state: str = Query("submitted")) -> Dict[str, Any]:
    """Simulate processing a SAR/STR report to a new state (admin/testing).

    States: submitted, accepted, rejected, error, filed
    """
    try:
        status = await sar_queue.get_status(report_id)
        if not status:
            raise HTTPException(status_code=404, detail="report_not_found")
        await sar_queue.set_status(report_id, state)
        return {"report_id": report_id, "new_state": state}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== EVIDENCE & CHAIN-OF-CUSTODY ==========

class AddEvidenceRequest(BaseModel):
    case_id: str
    file_hash: str
    filename: str
    uploaded_by: str


@router.post("/evidence/add")
async def add_evidence_item(payload: AddEvidenceRequest) -> Dict[str, Any]:
    """Add evidence to case chain-of-custody."""
    try:
        item = evidence_service.add_evidence(
            case_id=payload.case_id,
            file_hash=payload.file_hash,
            filename=payload.filename,
            uploaded_by=payload.uploaded_by
        )
        return {
            "success": True,
            "case_id": payload.case_id,
            "position": item.chain_position,
            "file_hash": item.file_hash,
            "signature": item.signature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evidence/chain/{case_id}")
async def get_evidence_chain(case_id: str) -> Dict[str, Any]:
    """Get complete chain-of-custody for case."""
    try:
        chain = evidence_service.get_chain(case_id)
        if not chain:
            raise HTTPException(status_code=404, detail="chain_not_found")
        return {
            "case_id": chain.case_id,
            "chain_hash": chain.chain_hash,
            "is_valid": chain.is_valid,
            "items": [
                {
                    "position": item.chain_position,
                    "filename": item.filename,
                    "hash": item.file_hash,
                    "uploaded_at": item.uploaded_at,
                    "uploaded_by": item.uploaded_by,
                    "signature": item.signature
                }
                for item in chain.items
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evidence/export/{case_id}")
async def export_evidence_package(case_id: str) -> Dict[str, Any]:
    """Export court-ready evidence package."""
    try:
        package = evidence_service.export_package(case_id)
        if not package:
            raise HTTPException(status_code=404, detail="no_evidence")
        return package
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== POLICY ENGINE ==========

class PolicyEvaluateRequest(BaseModel):
    transaction: Dict[str, Any]
    jurisdiction: str = "GLOBAL"


@router.post("/policy/evaluate")
async def evaluate_policy(payload: PolicyEvaluateRequest) -> Dict[str, Any]:
    """Evaluate transaction against compliance policies."""
    try:
        decision = policy_engine.evaluate(payload.transaction, payload.jurisdiction)
        return {
            "allowed": decision.allowed,
            "action": decision.action,
            "matched_rules": decision.matched_rules,
            "reasons": decision.reasons,
            "risk_level": decision.risk_level,
            "requires_review": decision.requires_review
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy/list")
async def list_policies(
    jurisdiction: str | None = Query(None),
    rule_type: str | None = Query(None)
) -> Dict[str, Any]:
    """List compliance policies."""
    try:
        policies = policy_engine.list_policies(jurisdiction, rule_type)
        return {
            "policies": [
                {
                    "rule_id": p.rule_id,
                    "name": p.name,
                    "jurisdiction": p.jurisdiction,
                    "rule_type": p.rule_type,
                    "action": p.action,
                    "priority": p.priority,
                    "enabled": p.enabled
                }
                for p in policies
            ],
            "count": len(policies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/travel-rule/pending")
async def get_travel_rule_pending() -> Dict[str, Any]:
    """List all pending Travel Rule transfers (in-memory)."""
    try:
        items = travel_rule_service.get_pending_transfers()
        return {"pending": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Inbound webhook for Travel Rule notifications
class TravelRuleInboundRequest(BaseModel):
    protocol: str = "TRISA"
    reference_id: str
    status: str | None = None
    payload: Dict[str, Any] | None = None


@router.post("/travel-rule/inbound")
async def travel_rule_inbound(payload: TravelRuleInboundRequest) -> Dict[str, Any]:
    """Receive inbound Travel Rule notification from counterparty VASP.

    Updates pending state and returns normalized status. This endpoint should be
    protected by shared secret or mutual TLS in production.
    """
    try:
        res = await travel_rule_service.receive_inbound(
            protocol=payload.protocol,
            reference_id=payload.reference_id,
            status=payload.status,
            payload=payload.payload,
        )
        # Audit log (best-effort)
        try:
            log_audit_event(
                action=AuditAction.SYSTEM_ACCESS,
                resource_type="travel_rule_inbound",
                resource_id=payload.reference_id,
                metadata={"protocol": payload.protocol, "status": res.get("status")},
            )
        except Exception:
            pass
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== SANCTIONS WORKER CONTROL (Admin) ==========

@router.post("/sanctions/worker/run-once")
async def sanctions_worker_run_once() -> Dict[str, Any]:
    """Manually trigger a single sanctions worker update cycle (admin)."""
    op = "sanctions_worker_run_once"
    start = time.time()
    try:
        try:
            from app.workers.sanctions_worker import run_sanctions_update_once  # type: ignore
        except Exception as imp_err:
            raise HTTPException(status_code=500, detail=f"Sanctions worker not available: {imp_err}")

        result = await run_sanctions_update_once()
        try:
            COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        except Exception:
            pass
        return {"status": result.get("status", "unknown"), "result": result}
    except HTTPException:
        try:
            COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        except Exception:
            pass
        raise
    except Exception as e:
        try:
            COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - start)
        except Exception:
            pass


# ========== SAR/STR REPORTING ==========

class SARGenerateRequest(BaseModel):
    case_id: str
    format: str | None = "fincen"  # fincen | eu | uk | canada | singapore | australia | raw


@router.post("/sar/generate")
async def generate_sar_report(payload: SARGenerateRequest) -> Dict[str, Any]:
    """Generate SAR/STR report from a case using templates in `sar_str_generator.py`."""
    try:
        # Load case data
        case = case_service.get_case(payload.case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case {payload.case_id} not found")

        # Minimal case_data mapping expected by generator
        case_data: Dict[str, Any] = {
            "addresses": [],
            "risk_score": 0.0,
            "subject_name": case.get("title") or "Unknown",
            "total_amount_usd": 0.0,
            "attachments": [],
            "risk_factors": [case.get("category")] if case.get("category") else [],
            "sanctions_hit": False,
            "mixer_usage": False,
        }

        # Try to enrich from events/attachments if available (best-effort)
        try:
            # attachments_count exists; full attachment details not returned by get_case()
            # This keeps endpoint fast and side-effect free.
            pass
        except Exception:
            pass

        # Generate and export
        report = await sar_generator.generate_from_case(payload.case_id, case_data)
        export_fmt = (payload.format or "fincen").lower()
        content = await sar_generator.export_report(report, format=export_fmt)

        # Attempt to parse JSON output for convenience
        parsed: Dict[str, Any] | None = None
        try:
            import json as _json
            parsed = _json.loads(content)
        except Exception:
            parsed = None

        # Audit log
        try:
            log_audit_event(
                action=AuditAction.DATA_EXPORT,
                resource_type="sar_report",
                resource_id=payload.case_id,
                metadata={"format": export_fmt},
            )
        except Exception:
            pass

        return {
            "success": True,
            "case_id": payload.case_id,
            "format": export_fmt,
            "report_id": getattr(report, "report_id", None),
            "report": parsed if parsed is not None else content,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SARSubmitRequest(BaseModel):
    report_id: str
    case_id: str
    format: str = "fincen"
    content: Dict[str, Any] | str
    async_submit: bool = True


@router.post("/sar/submit")
async def submit_sar_report(payload: SARSubmitRequest) -> Dict[str, Any]:
    """Submit SAR/STR to regulator (stub). Queues request for background processing.

    In Produktion wird hier an die jeweilige Behörde (z.B. FinCEN BSA E-Filing) übermittelt
    und der Status asynchron verfolgt.
    """
    try:
        # Best-effort Audit Log
        try:
            log_audit_event(
                action=AuditAction.DATA_EXPORT,
                resource_type="sar_submit",
                resource_id=payload.report_id,
                metadata={"case_id": payload.case_id, "format": payload.format},
            )
        except Exception:
            pass

        # Simuliertes Queueing (real: enqueue to worker)
        await sar_queue.enqueue(payload.report_id, payload.case_id, payload.format)
        return {"accepted": True, "queued": True, "report_id": payload.report_id, "case_id": payload.case_id, "format": payload.format, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sar/status/{report_id}")
async def get_sar_status(report_id: str) -> Dict[str, Any]:
    """Get submission status for a SAR/STR report."""
    try:
        st = await sar_queue.get_status(report_id)
        if not st:
            raise HTTPException(status_code=404, detail="report_not_found")
        return {"report_id": report_id, "status": st}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sar/queue")
async def list_sar_queue() -> Dict[str, Any]:
    """List queued SAR/STR submissions (in-memory)."""
    try:
        allq = await sar_queue.all()
        return {"items": allq, "count": len(allq)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== TRAVEL RULE / VASP (Now with real adapters) ==========

class TravelRulePrepareIn(BaseModel):
    sender_vasp: str
    receiver_vasp: str
    tx_hash: str | None = None
    amount_usd: float | None = None
    originator: Dict[str, Any] | None = None
    beneficiary: Dict[str, Any] | None = None


@router.post("/travel-rule/prepare")
async def travel_rule_prepare(payload: TravelRulePrepareIn) -> Dict[str, Any]:
    """Prepare Travel Rule payload using registered adapters."""
    try:
        # Use default TRISA adapter for now - can be configured
        protocol = "TRISA"
        tr_payload = TravelRulePayload(
            sender_vasp=payload.sender_vasp,
            receiver_vasp=payload.receiver_vasp,
            tx_hash=payload.tx_hash,
            amount=payload.amount_usd,
            originator=payload.originator,
            beneficiary=payload.beneficiary
        )

        response = await travel_rule_manager.prepare_and_send(protocol, tr_payload)

        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)

        # Audit log
        log_audit_event(
            action=AuditAction.DATA_EXPORT,
            resource_type="travel_rule",
            resource_id=payload.tx_hash or "n/a",
            metadata={
                "sender_vasp": payload.sender_vasp,
                "receiver_vasp": payload.receiver_vasp,
                "amount_usd": payload.amount_usd,
                "protocol": protocol,
                "reference_id": response.reference_id
            },
        )
        return {
            "status": "prepared",
            "reference_id": response.reference_id,
            "protocol": protocol
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/travel-rule/submit")
async def travel_rule_submit(ref_id: str = Query(...)) -> Dict[str, Any]:
    """Submit previously prepared Travel Rule payload."""
    try:
        # Check status using the reference ID
        # For now, return mock status
        status_response = TravelRuleResponse(
            success=True,
            message="Travel Rule submitted",
            reference_id=ref_id,
            delivery_status="submitted"
        )

        log_audit_event(
            action=AuditAction.DATA_EXPORT,
            resource_type="travel_rule",
            resource_id=ref_id,
            metadata={"delivery_status": status_response.delivery_status},
        )
        return {"status": status_response.delivery_status, "reference": ref_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/vasp/lookup")
async def vasp_lookup(legal_name: str = Query(...)) -> Dict[str, Any]:
    """Lookup VASP directory (skeleton; returns mock matches)."""
    try:
        matches = [
            {"legal_name": legal_name, "jurisdiction": "US", "endpoint": "https://vasp.example/api"},
            {"legal_name": f"{legal_name} Ltd.", "jurisdiction": "EU", "endpoint": "https://vasp-eu.example/api"},
        ]
        result = {"query": legal_name, "matches": matches, "count": len(matches)}
        log_audit_event(
            action=AuditAction.SYSTEM_ACCESS,
            resource_type="vasp_lookup",
            resource_id=legal_name,
            metadata={"match_count": len(matches)},
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/watchlist", summary="List watchlist entries")
async def list_watch(
    chain: str | None = Query(default=None),
    address: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int | None = Query(default=None, ge=0),
) -> Dict[str, Any]:
    op = "list"
    start = time.time()
    try:
        if limit is not None or offset is not None:
            page = await service.list_watch_page(chain, address, limit or 10, offset or 0)
            COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
            return page
        elif chain or address:
            items = await service.list_watch_filtered(chain, address)
        else:
            items = await service.list_watch()
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"items": items}
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - start)


@router.get("/name-screen")
async def name_screen(
    name: str = Query(...),
    threshold: float | None = Query(None, ge=0.0, le=1.0),
    limit: int | None = Query(None, ge=1, le=50),
) -> Dict[str, Any]:
    """GET variant for fuzzy sanctions name screening with configurable defaults.
    Response shape: { query, matches: [...], match_count }
    """
    op = "name_screen"
    start = time.time()
    try:
        # Defaults from settings if not provided
        th = float(threshold if threshold is not None else getattr(settings, "FUZZY_NAME_THRESHOLD", 0.85))
        lim_default = int(getattr(settings, "FUZZY_MAX_MATCHES", 10))
        lim = int(limit if limit is not None else lim_default)

        matches = await screening_engine.screen_name(name, th, max_results=lim)

        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {
            "query": name,
            "threshold": th,
            "matches": matches,
            "match_count": len(matches),
        }
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - start)


@router.post("/watchlist", summary="Add an address to watchlist")
async def add_watch(payload: WatchAdd = Body(...)) -> Dict[str, Any]:
    op = "add"
    start = time.time()
    try:
        entry = await service.add_watch(payload.chain, payload.address, payload.reason)
        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {"created": entry}
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - start)


# ========== SANCTIONS SCREENING ENDPOINTS (Now with multi-source) ==========

@router.post("/sanctions/screen-address")
async def screen_sanctions_address(chain: str, address: str) -> Dict[str, Any]:
    """Screen cryptocurrency address against multiple sanctions lists"""
    try:
        # Use the new multi-source indexer
        sanctions_data = await sanctions_indexer.get_normalized_data()

        # Check if address is in sanctions
        matching_sanctions = []
        for item in sanctions_data:
            if item['chain'] == chain.lower() and item['address'] == address.lower():
                matching_sanctions.append(item)

        return {
            "address": address,
            "chain": chain,
            "is_sanctioned": len(matching_sanctions) > 0,
            "sanctions": matching_sanctions,
            "total_matches": len(matching_sanctions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sanctions/screen-name")
async def screen_sanctions_name(
    name: str,
    threshold: float = Query(0.85, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    """Screen entity name with fuzzy matching (configurable threshold and limit)."""
    op = "sanctions_screen_name"
    start = time.time()
    try:
        # Normalize threshold into [0.0, 1.0]
        norm_threshold = max(0.0, min(1.0, float(threshold)))

        # Delegate to screening engine (handles normalization and ranking)
        matches = await screening_engine.screen_name(name, norm_threshold, max_results=limit)
        if isinstance(limit, int) and limit > 0:
            matches = matches[:limit]

        COMPLIANCE_REQUESTS.labels(op=op, status="ok").inc()
        return {
            "query": name,
            "threshold": norm_threshold,
            "matches": matches,
            "match_count": len(matches),
        }
    except Exception as e:
        COMPLIANCE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        COMPLIANCE_LATENCY.labels(op=op).observe(time.time() - start)


@router.get("/sanctions/statistics")
async def get_sanctions_statistics() -> Dict[str, Any]:
    """Get sanctions database statistics"""
    try:
        data = await sanctions_indexer.get_normalized_data()
        stats = {
            "total_entries": len(data),
            "sources": {},
            "chains": {},
            "categories": {}
        }

        for item in data:
            source = item.get('source', 'unknown')
            chain = item.get('chain', 'unknown')
            category = item.get('category', 'unknown')

            stats["sources"][source] = stats["sources"].get(source, 0) + 1
            stats["chains"][chain] = stats["chains"].get(chain, 0) + 1
            stats["categories"][category] = stats["categories"].get(category, 0) + 1

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sanctions/update")
async def trigger_sanctions_update() -> Dict[str, Any]:
    """Manually trigger multi-source sanctions list update"""
    try:
        result = await sanctions_indexer.fetch_all()
        total = sum(len(items) for items in result.values())

        return {
            "status": "completed",
            "sources_updated": list(result.keys()),
            "total_entries": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== VASP SCREENING ENDPOINTS ==========

@router.get("/vasp/search")
async def search_vasps(
    query: str = Query(..., min_length=1),
    vasp_type: str | None = Query(None),
    jurisdiction: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """Search VASP database"""
    try:
        # Convert type string to enum
        type_filter = None
        if vasp_type:
            try:
                type_filter = VaspType(vasp_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid VASP type: {vasp_type}")
        
        results = vasp_service.search(
            query=query,
            vasp_type=type_filter,
            jurisdiction=jurisdiction,
            limit=limit
        )
        
        return {
            "query": query,
            "results": [v.dict() for v in results],
            "count": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vasp/{vasp_id}")
async def get_vasp(vasp_id: str) -> Dict[str, Any]:
    """Get VASP details by ID"""
    try:
        vasp = vasp_service.get(vasp_id)
        if not vasp:
            raise HTTPException(status_code=404, detail=f"VASP {vasp_id} not found")
        
        return vasp.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vasp/{vasp_id}/screen")
async def screen_vasp(
    vasp_id: str,
    check_sanctions: bool = Query(True),
    check_pep: bool = Query(True),
    check_adverse_media: bool = Query(True)
) -> Dict[str, Any]:
    """Screen VASP for compliance risks"""
    try:
        result = await vasp_service.screen_vasp(
            vasp_id=vasp_id,
            check_sanctions=check_sanctions,
            check_pep=check_pep,
            check_adverse_media=check_adverse_media
        )
        
        log_audit_event(
            action=AuditAction.SYSTEM_ACCESS,
            resource_type="vasp_screening",
            resource_id=vasp_id,
            metadata={
                "sanctions_hit": result.sanctions_hit,
                "pep_hit": result.pep_hit,
                "risk_level": result.overall_risk.value,
                "recommended_action": result.recommended_action
            }
        )
        
        return result.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vasp/{vasp_id}/risk/score")
async def vasp_risk_score(vasp_id: str) -> Dict[str, Any]:
    """Führt ein KYB/VASP Risk Scoring durch und speichert das Ergebnis im In-Memory-Registry."""
    try:
        rec = await vasp_risk_registry.score_vasp(vasp_id)
        if not rec:
            raise HTTPException(status_code=404, detail=f"VASP {vasp_id} not found")
        return {"record": rec.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vasp/{vasp_id}/risk/last")
async def vasp_risk_last(vasp_id: str, auto_score_if_missing: bool = Query(True)) -> Dict[str, Any]:
    """Liefert den letzten Risk-Record; optional wird gescored wenn kein Record existiert."""
    try:
        rec = vasp_risk_registry.last(vasp_id)
        if not rec and auto_score_if_missing:
            rec = await vasp_risk_registry.score_vasp(vasp_id)
        if not rec:
            raise HTTPException(status_code=404, detail="no_record")
        return {"record": rec.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vasp/risk/history")
async def vasp_risk_history(vasp_id: str | None = Query(None), limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)) -> Dict[str, Any]:
    """Listet Risk-Records (optional gefiltert nach VASP-ID)."""
    try:
        items = vasp_risk_registry.list(vasp_id=vasp_id, limit=limit, offset=offset)
        return {"items": [it.model_dump() for it in items], "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ScoreManyRequest(BaseModel):
    vasp_ids: List[str]


@router.post("/vasp/risk/score-many")
async def vasp_risk_score_many(payload: ScoreManyRequest) -> Dict[str, Any]:
    """Batch-Scoring für mehrere VASPs."""
    try:
        recs = await vasp_risk_registry.score_many(payload.vasp_ids or [])
        return {"records": [r.model_dump() for r in recs], "count": len(recs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vasp/risk/summary")
async def vasp_risk_summary() -> Dict[str, Any]:
    """Aggregierte Zusammenfassung der letzten Risk-Records pro VASP."""
    try:
        return vasp_risk_registry.summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vasp/risk/run-once")
async def vasp_risk_run_once(
    _: dict = Depends(require_roles_if(os.getenv("TEST_MODE") != "1" and not os.getenv("PYTEST_CURRENT_TEST"), [UserRole.ADMIN]))
) -> Dict[str, Any]:
    """Trigger a single VASP risk update cycle (admin/testing)."""
    try:
        try:
            from app.workers.vasp_risk_worker import run_vasp_risk_update_once  # type: ignore
        except Exception as imp_err:
            raise HTTPException(status_code=500, detail=f"VASP risk worker not available: {imp_err}")
        result = await run_vasp_risk_update_once()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== VASP RISK REVIEW ==========
class VaspRiskReviewRequest(BaseModel):
    status: str
    reviewed_by: str
    notes: Dict[str, Any] | str | None = None
    recommended_action: str | None = None


@router.put("/vasp/{vasp_id}/risk/review")
async def vasp_risk_review_update(vasp_id: str, payload: VaspRiskReviewRequest) -> Dict[str, Any]:
    """Aktualisiert Review-Metadaten am letzten Risk-Record eines VASPs."""
    try:
        updated = vasp_risk_repo.update_last_record_review(
            vasp_id=vasp_id,
            review_status=payload.status,
            reviewed_by=payload.reviewed_by,
            notes=payload.notes if isinstance(payload.notes, str) else payload.notes,
            recommended_action=payload.recommended_action,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="no_record")
        return {"record": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vasp/statistics")
async def get_vasp_statistics() -> Dict[str, Any]:
    """Get VASP database statistics"""
    try:
        stats = vasp_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== TRAVEL RULE SERVICE ENDPOINTS ==========

class TravelRuleInitiateRequest(BaseModel):
    protocol: str = "TRISA"
    sender_vasp: str
    receiver_vasp: str
    tx_hash: str | None = None
    chain: str
    amount: float
    currency: str = "USD"
    originator: Dict[str, Any]
    beneficiary: Dict[str, Any]
    urgency: str = "normal"
    metadata: Dict[str, Any] | None = None


@router.post("/travel-rule/initiate")
async def initiate_travel_rule_transfer(payload: TravelRuleInitiateRequest) -> Dict[str, Any]:
    """Initiate Travel Rule compliant transfer"""
    try:
        response = await travel_rule_service.initiate_transfer(
            protocol=payload.protocol,
            sender_vasp=payload.sender_vasp,
            receiver_vasp=payload.receiver_vasp,
            tx_hash=payload.tx_hash,
            chain=payload.chain,
            amount=payload.amount,
            currency=payload.currency,
            originator=payload.originator,
            beneficiary=payload.beneficiary,
            metadata=payload.metadata
        )
        
        log_audit_event(
            action=AuditAction.DATA_EXPORT,
            resource_type="travel_rule",
            resource_id=payload.tx_hash or "n/a",
            metadata={
                "protocol": payload.protocol,
                "sender_vasp": payload.sender_vasp,
                "receiver_vasp": payload.receiver_vasp,
                "reference_id": response.reference_id
            }
        )
        
        return {
            "success": response.success,
            "message": response.message,
            "reference_id": response.reference_id,
            "delivery_status": response.delivery_status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/travel-rule/status/{reference_id}")
async def check_travel_rule_status(
    reference_id: str,
    protocol: str = Query("TRISA")
) -> Dict[str, Any]:
    """Check Travel Rule transfer status"""
    try:
        response = await travel_rule_service.check_transfer_status(
            protocol=protocol,
            reference_id=reference_id
        )
        
        return {
            "reference_id": reference_id,
            "success": response.success,
            "delivery_status": response.delivery_status,
            "message": response.message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/travel-rule/history")
async def get_travel_rule_history(
    vasp: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500)
) -> Dict[str, Any]:
    """Get Travel Rule transaction history"""
    try:
        history = travel_rule_service.get_transaction_history(
            vasp=vasp,
            limit=limit
        )
        
        return {
            "transactions": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/travel-rule/statistics")
async def get_travel_rule_statistics() -> Dict[str, Any]:
    """Get Travel Rule compliance statistics"""
    try:
        stats = travel_rule_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== EXCHANGE LIAISON ENDPOINTS ==========

@router.get("/exchange-liaison/partners")
async def get_exchange_partners() -> Dict[str, Any]:
    """Get all exchange partners"""
    try:
        partners = exchange_liaison_service.get_all_partners()
        return {
            "partners": partners,
            "count": len(partners)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-liaison/partners/{exchange_id}")
async def get_exchange_partner_stats(exchange_id: str) -> Dict[str, Any]:
    """Get exchange partner statistics"""
    try:
        stats = exchange_liaison_service.get_partner_statistics(exchange_id)
        if not stats:
            raise HTTPException(status_code=404, detail=f"Exchange {exchange_id} not found")
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ExchangeLiaisonSubmitRequest(BaseModel):
    exchange_id: str
    request_type: str  # freeze_account, intel_sharing, etc.
    case_id: str
    description: str
    target_addresses: list[str] | None = None
    target_accounts: list[str] | None = None
    urgency: str = "normal"
    metadata: Dict[str, Any] | None = None


class ExchangeLiaisonStatusUpdateRequest(BaseModel):
    status: str
    response: Dict[str, Any] | None = None
    notes: str | None = None


@router.post("/exchange-liaison/submit")
async def submit_exchange_request(payload: ExchangeLiaisonSubmitRequest) -> Dict[str, Any]:
    """Submit request to exchange partner"""
    try:
        # Convert string to enum
        try:
            request_type = ExchangeRequestType(payload.request_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request type: {payload.request_type}"
            )
        
        request = await exchange_liaison_service.submit_request(
            exchange_id=payload.exchange_id,
            request_type=request_type,
            case_id=payload.case_id,
            description=payload.description,
            target_addresses=payload.target_addresses,
            target_accounts=payload.target_accounts,
            urgency=payload.urgency,
            metadata=payload.metadata
        )
        
        log_audit_event(
            action=AuditAction.DATA_EXPORT,
            resource_type="exchange_liaison",
            resource_id=request.id,
            metadata={
                "exchange_id": payload.exchange_id,
                "request_type": payload.request_type,
                "case_id": payload.case_id,
                "urgency": payload.urgency
            }
        )

        try:
            case_service.add_timeline_event(
                case_id=payload.case_id,
                event_type="exchange_request_submitted",
                description=(
                    f"Exchange request {request.id} submitted to {payload.exchange_id} "
                    f"({payload.request_type})"
                ),
                triggered_by="system",
                triggered_by_name="Exchange Liaison",
                payload={
                    "request_id": request.id,
                    "exchange_id": payload.exchange_id,
                    "request_type": payload.request_type,
                    "urgency": payload.urgency,
                    "target_accounts": payload.target_accounts or [],
                    "target_addresses": payload.target_addresses or [],
                },
            )
        except Exception:
            pass

        return {
            "request_id": request.id,
            "status": request.status.value,
            "exchange_id": request.exchange_id,
            "submitted_at": request.submitted_at.isoformat() if request.submitted_at else None
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-liaison/requests/{request_id}")
async def get_exchange_request_status(request_id: str) -> Dict[str, Any]:
    """Get exchange liaison request status"""
    try:
        request = await exchange_liaison_service.get_request_status(request_id)
        if not request:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
        
        return {
            "request_id": request.id,
            "exchange_id": request.exchange_id,
            "request_type": request.request_type.value,
            "case_id": request.case_id,
            "status": request.status.value,
            "submitted_at": request.submitted_at.isoformat() if request.submitted_at else None,
            "reviewed_at": request.reviewed_at.isoformat() if request.reviewed_at else None,
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "response": request.response,
            "notes": request.notes
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exchange-liaison/requests/{request_id}/status")
async def update_exchange_request_status(
    request_id: str,
    payload: ExchangeLiaisonStatusUpdateRequest,
) -> Dict[str, Any]:
    try:
        try:
            status = ExchangeRequestStatus(payload.status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")

        request = await exchange_liaison_service.update_request(
            request_id=request_id,
            status=status,
            response=payload.response,
            notes=payload.notes,
        )

        log_audit_event(
            action=AuditAction.DATA_ACCESS,
            resource_type="exchange_liaison",
            resource_id=request.id,
            metadata={
                "exchange_id": request.exchange_id,
                "case_id": request.case_id,
                "status": status.value,
            },
        )

        try:
            case_service.add_timeline_event(
                case_id=request.case_id,
                event_type="exchange_request_updated",
                description=(
                    f"Exchange request {request.id} status updated to {status.value}"
                ),
                triggered_by="system",
                triggered_by_name="Exchange Liaison",
                payload={
                    "request_id": request.id,
                    "exchange_id": request.exchange_id,
                    "status": status.value,
                    "response": payload.response,
                    "notes": payload.notes,
                },
            )
        except Exception:
            pass

        return {
            "request_id": request.id,
            "status": request.status.value,
            "exchange_id": request.exchange_id,
            "case_id": request.case_id,
            "reviewed_at": request.reviewed_at.isoformat() if request.reviewed_at else None,
            "completed_at": request.completed_at.isoformat() if request.completed_at else None,
            "response": request.response,
            "notes": request.notes,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-liaison/case/{case_id}")
async def get_case_exchange_requests(case_id: str) -> Dict[str, Any]:
    """Get all exchange requests for a case"""
    try:
        requests = exchange_liaison_service.get_case_requests(case_id)
        
        return {
            "case_id": case_id,
            "requests": [
                {
                    "request_id": req.id,
                    "exchange_id": req.exchange_id,
                    "request_type": req.request_type.value,
                    "status": req.status.value,
                    "submitted_at": req.submitted_at.isoformat() if req.submitted_at else None
                }
                for req in requests
            ],
            "count": len(requests)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-liaison/pending")
async def get_pending_exchange_requests() -> Dict[str, Any]:
    """Get all pending exchange requests"""
    try:
        requests = exchange_liaison_service.get_pending_requests()
        
        return {
            "requests": [
                {
                    "request_id": req.id,
                    "exchange_id": req.exchange_id,
                    "request_type": req.request_type.value,
                    "case_id": req.case_id,
                    "status": req.status.value,
                    "urgency": req.urgency,
                    "submitted_at": req.submitted_at.isoformat() if req.submitted_at else None
                }
                for req in requests
            ],
            "count": len(requests)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
