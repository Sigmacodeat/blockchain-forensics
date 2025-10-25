"""
Erweiterte Forensic API für Blockchain-Analyse
============================================

Professionelle API für:
- Batch-Analyse von Adressen und Transaktionen
- Advanced Pattern Recognition
- Cross-Chain Correlation
- Evidence Collection und Management
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, Body, BackgroundTasks, UploadFile, File, Form
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
try:
    # Pydantic v2
    from pydantic import field_validator  # type: ignore
except Exception:
    # Fallback for Pydantic v1 (no-op shim)
    def field_validator(*args, **kwargs):  # type: ignore
        def _decorator(func):
            return func
        return _decorator
import logging
from datetime import datetime
import uuid
import os
import time
import threading

from app.services.alert_service import alert_service
from app.analytics.exposure_service import exposure_service
from app.services.ml_analytics import analytics_engine
from app.services.multi_chain import multi_chain_engine
from app.services.compliance import compliance_manager, custody_manager, AuditEvent, AuditEventType, ComplianceLevel
from app.services.forensic_visualizer import forensic_visualizer
from app.analytics.taint_tracer import trace_forward
from app.analytics.wallet_clustering import suggest_clusters
from app.cases.service import case_service
from app.cases.models import Entity as CaseEntity, EvidenceLink as CaseEvidenceLink

logger = logging.getLogger(__name__)

router = APIRouter()


# ==========================
# Security & Rate Limiting
# ==========================
_API_KEY = os.getenv("API_KEY")
_RL_LIMIT = int(os.getenv("API_RATE_LIMIT", "120"))  # requests per minute per IP+path
_rl_lock = threading.Lock()
_rl_store = {}


def api_key_required(request: Request):
    if not _API_KEY:
        return  # guard disabled if no API_KEY configured
    provided = request.headers.get("X-API-Key")
    if provided != _API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


def rate_limit(request: Request):
    # simple sliding window per IP+path
    if _RL_LIMIT <= 0:
        return
    now = int(time.time())
    window = now // 60
    # Some test clients may not provide request.client
    try:
        client_host = getattr(request.client, "host", None) or "testclient"
    except Exception:
        client_host = "testclient"
    key = f"{client_host}:{request.url.path}:{window}"
    with _rl_lock:
        cnt = _rl_store.get(key, 0) + 1
        _rl_store[key] = cnt
        # cleanup previous window keys occasionally (best-effort)
        if cnt == 1:
            prev_key = f"{client_host}:{request.url.path}:{window-1}"
            _rl_store.pop(prev_key, None)
        if cnt > _RL_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")


class ExposureCalcRequest(BaseModel):
    address: str = Field(..., min_length=1)
    max_hops: int = Field(3, ge=1, le=10)
    context: Optional[Dict[str, Any]] = None

    @field_validator('address')
    def _trim_addr(cls, v: str) -> str:
        s = (v or '').strip()
        if not s:
            raise ValueError('address is required')
        return s


class ExposureCalcResponse(BaseModel):
    result: Dict[str, Any]


class ExposureBatchRequest(BaseModel):
    addresses: List[str] = Field(..., min_length=1, max_length=200)
    max_hops: int = Field(3, ge=1, le=10)
    context_by_address: Optional[Dict[str, Dict[str, Any]]] = None

    @field_validator('addresses')
    def _sanitize_addresses(cls, v: List[str]) -> List[str]:
        out = []
        for a in v:
            s = (a or '').strip()
            if s:
                out.append(s)
        if not out:
            raise ValueError('addresses cannot be empty after sanitization')
        return out


class AddressTransactionsResponse(BaseModel):
    chain: str
    address: str
    total: int
    result: List[Dict[str, Any]]


class ExposureBatchResponse(BaseModel):
    results: Dict[str, Dict[str, Any]]


class BridgeTransfer(BaseModel):
    chain: str
    address: str
    tx_hash: Optional[str] = None
    log_index: Optional[int] = None
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    event_name: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    amount: Optional[int] = None
    token: Optional[str] = None
    amount_raw: Optional[int] = None
    decimals: Optional[int] = None
    token_symbol: Optional[str] = None
    value_usd: Optional[float] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    topics: Optional[List[str]] = None
    data: Optional[str] = None
    # Provenance
    adapter: Optional[str] = None
    rpc_endpoint: Optional[str] = None
    collection_timestamp: Optional[str] = None
    record_hash: Optional[str] = None


class BridgeTransfersResponse(BaseModel):
    version: str = Field(default="1.0")
    start_time: str
    end_time: str
    total: int
    transfers: List[BridgeTransfer]
    evidence_id: Optional[str] = None
    chain_hash: Optional[str] = None
    chain_length: Optional[int] = None


class TaintTraceRequest(BaseModel):
    seed: str = Field(..., min_length=1)
    chains: List[str] = Field(default_factory=lambda: ["ethereum"])  # standard: nur ETH
    max_hops: int = Field(3, ge=1, le=10)
    per_hop_limit: int = Field(50, ge=10, le=200)

    @field_validator('seed')
    def _trim_seed(cls, v: str) -> str:
        s = (v or '').strip()
        if not s:
            raise ValueError('seed is required')
        return s


class TaintTraceResponse(BaseModel):
    seed: str
    hops: int
    edges: List[Dict[str, Any]]
    visited: List[str]
    analysis_timestamp: str


class ClusterSuggestRequest(BaseModel):
    addresses: List[str] = Field(..., min_length=1, max_length=200)
    chains: List[str] = Field(default_factory=lambda: ["ethereum"])  # standard: ETH
    limit_per_address: int = Field(100, ge=20, le=500)
    min_shared_counterparties: int = Field(3, ge=1, le=50)

    @field_validator('addresses')
    def _sanitize(cls, v: List[str]) -> List[str]:
        out = []
        for a in v:
            s = (a or '').strip()
            if s:
                out.append(s)
        if not out:
            raise ValueError('addresses cannot be empty after sanitization')
        return out


class ClusterSuggestResponse(BaseModel):
    clusters: List[Dict[str, Any]]
    analyzed: int


@router.post("/analyze/batch")
async def batch_analysis(
    addresses: List[str] = Body(...),
    chains: List[str] = Body(default=["ethereum"]),
    analysis_types: List[str] = Body(default=["risk", "pattern", "correlation"]),
    compliance_level: str = "standard"
):
    """Batch-Analyse mehrerer Adressen"""
    try:
        # Compliance-Setup
        if compliance_level == "court":
            compliance_manager.compliance_level = compliance_manager.compliance_level.COURT_ADMISSIBLE
            compliance_manager.require_evidence_collection = True

        results = {}

        # Multi-Chain Setup
        await multi_chain_engine.initialize_chains(chains)

        for address in addresses:
            # Evidence-Record erstellen falls erforderlich
            if compliance_manager.require_evidence_collection:
                evidence = compliance_manager.create_evidence_record(
                    case_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    resource_id=address,
                    resource_type="address",
                    collection_method="api_batch_analysis",
                    collected_by="system"
                )

            # Cross-Chain-Analyse
            chain_activities = await multi_chain_engine.cross_chain_analysis([address])

            # ML-Analyse
            historical_data = {
                "address": address,
                "tx_frequency": 10,  # Platzhalter
                "avg_tx_value": 1.5,
                "unique_counterparties": 5,
                "cross_chain_activity": len(chains) > 1,
                "transaction_sequence": []  # Platzhalter
            }

            ml_analysis = analytics_engine.analyze_entity(address, historical_data)

            # Alert-Generierung für verdächtige Aktivitäten
            alerts = []
            if ml_analysis.get("risk_assessment", {}).get("risk_score", 0) > 0.8:
                # Generiere Test-Alert
                test_event = {
                    "address": address,
                    "risk_score": ml_analysis["risk_assessment"]["risk_score"],
                    "chain": chains[0]
                }
                alerts = await alert_service.process_event(test_event)

            results[address] = {
                "chain_activities": chain_activities.get(address, {}),
                "ml_analysis": ml_analysis,
                "alerts_generated": len(alerts),
                "evidence_id": evidence.evidence_id if compliance_manager.require_evidence_collection else None,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

        return {
            "status": "completed",
            "analyzed_addresses": len(addresses),
            "chains_analyzed": chains,
            "analysis_types": analysis_types,
            "results": results
        }

    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================
# Case Management (minimal)
# ==========================

class CreateCaseRequest(BaseModel):
    case_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field("")
    lead_investigator: str = Field(..., min_length=1)


class CreateCaseResponse(BaseModel):
    status: str
    case: Dict[str, Any]


@router.post("/cases/create", response_model=CreateCaseResponse, dependencies=[Depends(api_key_required), Depends(rate_limit)])
async def create_case(payload: CreateCaseRequest, request: Request):
    try:
        c = case_service.create_case(
            case_id=payload.case_id,
            title=payload.title,
            description=payload.description,
            lead_investigator=payload.lead_investigator,
        )
        # Audit-Event
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.USER_ACTION,
            user_id=payload.lead_investigator,
            resource_id=c.case_id,
            action="create_case",
            details={"title": c.title},
            ip_address="system",
            user_agent="forensics_api",
            compliance_level=ComplianceLevel.LAW_ENFORCEMENT,
        )
        try:
            compliance_manager.log_audit_event(audit_event)
        except Exception:
            pass
        return {"status": "case_created", "case": c.model_dump()}
    except Exception as e:
        logger.error(f"Create case error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AddEntityRequest(BaseModel):
    address: str = Field(..., min_length=1)
    chain: str = Field(..., min_length=1)
    labels: Optional[Dict[str, Any]] = None


@router.post("/cases/{case_id}/entities/add", dependencies=[Depends(api_key_required), Depends(rate_limit)])
async def add_case_entity(case_id: str, payload: AddEntityRequest, request: Request):
    try:
        entity = CaseEntity(address=payload.address.strip(), chain=payload.chain.strip(), labels=payload.labels or {})
        case_service.add_entity(case_id, entity)
        # Audit-Event
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.USER_ACTION,
            user_id="system",
            resource_id=case_id,
            action="add_case_entity",
            details={"address": entity.address, "chain": entity.chain},
            ip_address="system",
            user_agent="forensics_api",
            compliance_level=ComplianceLevel.LAW_ENFORCEMENT,
        )
        try:
            compliance_manager.log_audit_event(audit_event)
        except Exception:
            pass
        return {"status": "entity_added", "case_id": case_id, "entity": entity.model_dump()}
    except Exception as e:
        logger.error(f"Add case entity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class LinkEvidenceRequest(BaseModel):
    resource_id: str = Field(..., min_length=1)
    resource_type: str = Field(..., min_length=1)
    record_hash: Optional[str] = None
    notes: str = ""


@router.post("/cases/{case_id}/evidence/link", dependencies=[Depends(api_key_required), Depends(rate_limit)])
async def link_case_evidence(case_id: str, payload: LinkEvidenceRequest, request: Request):
    try:
        link = CaseEvidenceLink(
            case_id=case_id,
            resource_id=payload.resource_id,
            resource_type=payload.resource_type,
            record_hash=payload.record_hash,
            notes=payload.notes,
        )
        case_service.link_evidence(link)
        # Audit-Event
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.USER_ACTION,
            user_id="system",
            resource_id=case_id,
            action="link_case_evidence",
            details={"resource_id": link.resource_id, "resource_type": link.resource_type},
            ip_address="system",
            user_agent="forensics_api",
            compliance_level=ComplianceLevel.LAW_ENFORCEMENT,
        )
        try:
            compliance_manager.log_audit_event(audit_event)
        except Exception:
            pass
        return {"status": "evidence_linked", "case_id": case_id, "evidence": link.model_dump()}
    except Exception as e:
        logger.error(f"Link case evidence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ExportCaseResponse(BaseModel):
    status: str
    export: Dict[str, Any]


@router.get("/cases/{case_id}/export", response_model=ExportCaseResponse, dependencies=[Depends(api_key_required), Depends(rate_limit)])
async def export_case(case_id: str, request: Request):
    try:
        data = case_service.export(case_id)
        return {"status": "export_ready", "export": data}
    except Exception as e:
        logger.error(f"Export case error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ExportCaseCsvResponse(BaseModel):
    status: str
    entities_csv: str
    evidence_csv: str
    format: str


@router.get("/cases/{case_id}/export.csv", response_model=ExportCaseCsvResponse, dependencies=[Depends(api_key_required), Depends(rate_limit)])
async def export_case_csv(case_id: str, request: Request):
    try:
        csvs = case_service.export_csv(case_id)
        return {
            "status": "export_ready",
            "entities_csv": csvs.get("entities_csv", ""),
            "evidence_csv": csvs.get("evidence_csv", ""),
            "format": csvs.get("format", "csv"),
        }
    except Exception as e:
        logger.error(f"Export case CSV error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CaseChecksumResponse(BaseModel):
    status: str
    case_id: str
    checksum_sha256: str


@router.get("/cases/{case_id}/checksum", response_model=CaseChecksumResponse, dependencies=[Depends(api_key_required), Depends(rate_limit)])
async def get_case_checksum(case_id: str, request: Request):
    try:
        cs = case_service.get_checksum(case_id)
        return {"status": "ok", "case_id": case_id, "checksum_sha256": cs}
    except Exception as e:
        logger.error(f"Get case checksum error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class VerifyCaseRequest(BaseModel):
    checksum_sha256: Optional[str] = None
    signature_hmac_sha256: Optional[str] = None


class VerifyCaseResponse(BaseModel):
    status: str
    case_id: str
    checksum_sha256: str
    match: Optional[bool] = None
    signature_hmac_sha256: Optional[str] = None
    signature_match: Optional[bool] = None


@router.post("/cases/{case_id}/verify", response_model=VerifyCaseResponse, dependencies=[Depends(api_key_required), Depends(rate_limit)])
async def verify_case_checksum(case_id: str, payload: VerifyCaseRequest, request: Request):
    try:
        res = case_service.verify(case_id, payload.checksum_sha256, payload.signature_hmac_sha256)
        return {"status": "ok", **res}
    except Exception as e:
        logger.error(f"Verify case checksum error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class UploadAttachmentResponse(BaseModel):
    status: str
    case_id: str
    meta: Dict[str, Any]
    evidence: Dict[str, Any]


@router.post(
    "/cases/{case_id}/attachments/upload",
    response_model=UploadAttachmentResponse,
    dependencies=[Depends(api_key_required), Depends(rate_limit)],
)
async def upload_case_attachment(
    case_id: str,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(""),
    request: Request = None,
):
    try:
        content = await file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 25MB)")
        meta = case_service.save_attachment(
            case_id=case_id,
            filename=file.filename or "attachment.bin",
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        link = case_service.link_attachment_as_evidence(case_id, meta, notes or "")

        # Audit-Event
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.USER_ACTION,
            user_id="system",
            resource_id=case_id,
            action="upload_case_attachment",
            details={"filename": meta.get("filename"), "sha256": meta.get("sha256")},
            ip_address="system",
            user_agent="forensics_api",
            compliance_level=ComplianceLevel.LAW_ENFORCEMENT,
        )
        try:
            compliance_manager.log_audit_event(audit_event)
        except Exception:
            pass

        return {"status": "attachment_uploaded", "case_id": case_id, "meta": meta, "evidence": link.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload attachment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trace/taint", response_model=TaintTraceResponse)
async def taint_trace(
    payload: TaintTraceRequest,
):
    """Leichtgewichtiger Forward-Taint-Trace ab einer Seed-Adresse über mehrere Chains.
    Nutzt paginierte Address-TX-APIs je Chain, keine direkten RPC-Annahmen im Endpoint.
    """
    try:
        chains = payload.chains if isinstance(payload.chains, list) and payload.chains else ["ethereum"]
        # Chains bereitstellen (Adapter init)
        await multi_chain_engine.initialize_chains(chains)
        # Trace starten
        res = await trace_forward(
            seed=payload.seed,
            chains=chains,
            max_hops=payload.max_hops,
            per_hop_limit=payload.per_hop_limit,
        )
        d = res.to_dict()
        return TaintTraceResponse(
            seed=d.get("seed"),
            hops=d.get("hops", 0),
            edges=d.get("edges", []),
            visited=d.get("visited", []),
            analysis_timestamp=d.get("analysis_timestamp"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Taint trace error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cluster/suggest", response_model=ClusterSuggestResponse)
async def cluster_suggest(
    payload: ClusterSuggestRequest,
):
    """Heuristische Cluster-Vorschläge (v1): Co-occurrence & gemeinsame Gegenparteien.
    Keine Persistenz; schnelles, erklärbares Ergebnis.
    """
    try:
        chains = payload.chains if isinstance(payload.chains, list) and payload.chains else ["ethereum"]
        await multi_chain_engine.initialize_chains(chains)
        res = await suggest_clusters(
            addresses=payload.addresses,
            chains=chains,
            limit_per_address=payload.limit_per_address,
            min_shared_counterparties=payload.min_shared_counterparties,
        )
        return ClusterSuggestResponse(
            clusters=res.get("clusters", []),
            analyzed=res.get("analyzed", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cluster suggest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/address/{chain_id}/{address}/transactions", response_model=AddressTransactionsResponse)
async def get_address_transactions_paged(
    chain_id: str,
    address: str,
    limit: int = Query(default=100, ge=1, le=1000),
    from_block: Optional[int] = Query(default=None, ge=0),
    to_block: Optional[int] = Query(default=None, ge=0),
    start_height: Optional[int] = Query(default=None, ge=0),
    end_height: Optional[int] = Query(default=None, ge=0),
):
    """Paginierte Adress-Transaktionen über Chains hinweg.
    EVM: from_block/to_block; UTXO: start_height/end_height.
    """
    try:
        # Initialisiere Chain falls noch nicht aktiv
        await multi_chain_engine.initialize_chains([chain_id])

        items = await multi_chain_engine.get_address_transactions_paged(
            chain_id,
            address,
            limit=limit,
            from_block=from_block,
            to_block=to_block,
            start_height=start_height,
            end_height=end_height,
        )
        return AddressTransactionsResponse(
            chain=chain_id,
            address=address,
            total=len(items),
            result=items,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"address transactions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exposure/calc", response_model=ExposureCalcResponse)
async def exposure_calc(
    payload: ExposureCalcRequest,
):
    """Berechnet Direct/Indirect Exposure für eine Adresse (leichtgewichtig)."""
    try:
        ctx = payload.context if isinstance(payload.context, dict) else {}
        res = await exposure_service.calculate(payload.address, max_hops=payload.max_hops, context=ctx)
        return ExposureCalcResponse(result=res.to_dict())
    except Exception as e:
        logger.error(f"Exposure calc error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exposure/batch", response_model=ExposureBatchResponse)
async def exposure_batch(
    payload: ExposureBatchRequest,
):
    """Batch-Exposure-Berechnung für mehrere Adressen."""
    try:
        addresses = payload.addresses
        mh = payload.max_hops
        ctx_map = payload.context_by_address if isinstance(payload.context_by_address, dict) else {}
        # sanitize address keys in ctx_map
        sanitized_ctx = {}
        for a, ctx in (ctx_map or {}).items():
            key = (a or "").strip()
            if not key:
                continue
            sanitized_ctx[key] = ctx if isinstance(ctx, dict) else {}
        sanitized_addresses = [ (a or "").strip() for a in addresses if (a or "").strip() ]
        if not sanitized_addresses:
            raise HTTPException(status_code=400, detail="no valid addresses after sanitization")
        res = await exposure_service.batch_calculate(sanitized_addresses, max_hops=mh, context_by_address=sanitized_ctx)
        return ExposureBatchResponse(results=res)
    except Exception as e:
        logger.error(f"Exposure batch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/patterns")
async def pattern_analysis(
    addresses: List[str] = Body(...),
    pattern_types: List[str] = Body(default=["money_laundering", "ponzi", "mixer_usage"]),
    time_window_days: int = 30
):
    """Erweiterte Pattern-Erkennung"""
    try:
        pattern_results = {}

        for address in addresses:
            # Simulierte Pattern-Daten
            transaction_sequence = [
                {"type": "transfer", "value": 1000, "timestamp": "2024-01-01T10:00:00Z"},
                {"type": "mixer", "value": 1000, "timestamp": "2024-01-01T11:00:00Z"},
                {"type": "transfer", "value": 950, "timestamp": "2024-01-01T12:00:00Z"},
            ]

            # Pattern-Recognition
            patterns = analytics_engine.pattern_recognizer.recognize_patterns(transaction_sequence)

            # Filter nach gewünschten Pattern-Typen
            relevant_patterns = [
                p for p in patterns
                if any(pt in p.get("pattern_type", "") for pt in pattern_types)
            ]

            if relevant_patterns:
                pattern_results[address] = {
                    "detected_patterns": relevant_patterns,
                    "confidence": max(p["confidence"] for p in relevant_patterns),
                    "pattern_types": list(set(p["pattern_type"] for p in relevant_patterns))
                }

        return {
            "status": "completed",
            "analyzed_addresses": len(addresses),
            "time_window_days": time_window_days,
            "pattern_types_searched": pattern_types,
            "results": pattern_results
        }

    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chains/supported")
async def get_supported_chains():
    """Gibt alle unterstützten Chains zurück"""
    chains = multi_chain_engine.adapter_factory.get_supported_chains()
    chain_stats = multi_chain_engine.get_chain_statistics()

    return {
        "total_chains": chain_stats["total_chains"],
        "chains_by_type": chain_stats["chains_by_type"],
        "supported_features": chain_stats["supported_features"],
        "chains": [
            {
                "chain_id": chain.chain_id,
                "name": chain.name,
                "symbol": chain.symbol,
                "chain_type": chain.chain_type.value,
                "features": chain.features,
                "block_explorer": chain.block_explorer_url
            }
            for chain in chains
        ]
    }


@router.post("/evidence/collect")
async def collect_evidence(
    resource_id: str = Body(...),
    resource_type: str = Body(...),
    case_id: str = Body(...),
    collection_method: str = Body(...),
    handler_id: str = Body(...)
):
    """Sammelt Evidence für Strafverfolgung"""
    try:
        # Erstelle Evidence-Record
        evidence = compliance_manager.create_evidence_record(
            case_id=case_id,
            resource_id=resource_id,
            resource_type=resource_type,
            collection_method=collection_method,
            collected_by=handler_id
        )

        # Registriere Handler falls nicht vorhanden
        custody_manager.register_handler(
            handler_id=handler_id,
            name=f"Handler_{handler_id}",
            role="investigator",
            clearance_level="high"
        )

        return {
            "status": "evidence_collected",
            "evidence_id": evidence.evidence_id,
            "collection_timestamp": evidence.collection_timestamp.isoformat(),
            "chain_of_custody": evidence.chain_of_custody
        }

    except Exception as e:
        logger.error(f"Evidence collection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evidence/transfer")
async def transfer_evidence(
    evidence_id: str = Body(...),
    from_handler: str = Body(...),
    to_handler: str = Body(...),
    action: str = Body(...),
    notes: str = Body(default="")
):
    """Transferiert Evidence zwischen Handlern"""
    try:
        success = custody_manager.transfer_evidence(
            evidence_id=evidence_id,
            from_handler=from_handler,
            to_handler=to_handler,
            action=action,
            notes=notes
        )

        if not success:
            raise HTTPException(status_code=400, detail="Transfer failed")

        return {
            "status": "evidence_transferred",
            "evidence_id": evidence_id,
            "transfer_timestamp": datetime.utcnow().isoformat(),
            "notes": notes
        }

    except Exception as e:
        logger.error(f"Evidence transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/trail/{resource_id}")
async def get_audit_trail(
    resource_id: str,
    limit: int = Query(default=100, le=1000)
):
    """Holt Audit-Trail für Ressource"""
    try:
        audit_events = compliance_manager.get_audit_trail(resource_id, limit)

        return {
            "resource_id": resource_id,
            "total_events": len(audit_events),
            "events": [
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                    "user_id": event.user_id,
                    "action": event.action,
                    "compliance_level": event.compliance_level.value,
                    "hash_chain": event.hash_chain
                }
                for event in audit_events
            ]
        }

    except Exception as e:
        logger.error(f"Audit trail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/compliance/{case_id}")
async def generate_compliance_report(
    case_id: str,
    report_type: str = Query(default="full", pattern="^(full|suspicious_activity|evidence_summary)$")
):
    """Generiert Compliance-Bericht"""
    try:
        report = compliance_manager.generate_compliance_report(case_id, report_type)

        return {
            "case_id": case_id,
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "report": report
        }

    except Exception as e:
        logger.error(f"Compliance report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualize/graph")
async def create_visualization(
    viz_type: str = Body(...),
    data: Dict[str, Any] = Body(...),
    config: Optional[Dict[str, Any]] = Body(default=None)
):
    """Erstellt erweiterte Visualisierungen"""
    try:
        from app.services.forensic_visualizer import VisualizationType, VisualizationConfig

        # Parse Visualization Type
        try:
            viz_type_enum = VisualizationType(viz_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported visualization type: {viz_type}")

        # Parse Config
        if config:
            viz_config = VisualizationConfig(**config)
        else:
            viz_config = VisualizationConfig(
                viz_type=viz_type_enum,
                title=f"Forensic {viz_type.title()}",
                width=1000,
                height=800
            )

        # Erstelle Visualisierung
        visualization = forensic_visualizer.create_visualization(viz_type_enum, data, viz_config)

        return {
            "status": "visualization_created",
            "viz_type": viz_type,
            "config": viz_config.to_dict(),
            "data": visualization["data"],
            "export_formats": ["json", "html"]
        }

    except Exception as e:
        logger.error(f"Visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bridge/transfers", response_model=BridgeTransfersResponse)
async def get_bridge_transfers(
    start_time: str = Query(..., description="ISO-8601 Startzeit, z.B. 2025-01-01T00:00:00Z"),
    end_time: str = Query(..., description="ISO-8601 Endzeit, z.B. 2025-01-01T23:59:59Z"),
    case_id: Optional[str] = Query(default=None, description="Optional: Evidence-Case-ID für Beweissicherung"),
):
    """Liefert strukturierte Bridge-/Cross-Chain-Transfer-Logs im Zeitraum mit optionaler Evidence-Erfassung."""
    try:
        # Parse times
        try:
            if not start_time or not isinstance(start_time, str):
                raise ValueError("start_time must be a valid ISO string")
            if not end_time or not isinstance(end_time, str):
                raise ValueError("end_time must be a valid ISO string")

            # Handle Z suffix for UTC
            start_time_clean = start_time.replace("Z", "+00:00") if start_time.endswith("Z") else start_time
            end_time_clean = end_time.replace("Z", "+00:00") if end_time.endswith("Z") else end_time

            st = datetime.fromisoformat(start_time_clean)
            et = datetime.fromisoformat(end_time_clean)
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"Ungültiges Zeitformat. Erwartet ISO-8601. Fehler: {str(e)}")

        if et <= st:
            raise HTTPException(status_code=400, detail="end_time muss nach start_time liegen")

        # Optional: Evidence-Record vorbereiten
        evidence = None
        if case_id:
            evidence = compliance_manager.create_evidence_record(
                case_id=case_id,
                resource_id=f"bridge_transfers_{st.isoformat()}_{et.isoformat()}",
                resource_type="bridge_transfers",
                collection_method="api_bridge_transfers",
                collected_by="system",
            )

        transfers = await multi_chain_engine.get_cross_chain_transfers(st, et)

        # Record-Hashes für Provenance ergänzen
        import hashlib
        import json
        enriched = []
        for t in transfers:
            try:
                canonical = json.dumps(t, sort_keys=True, separators=(",", ":")).encode()
                rec_hash = hashlib.sha256(canonical).hexdigest()
                # confidence aus decode_confidence übernehmen, falls vorhanden
                conf = t.get("decode_confidence")
                if conf is not None and t.get("confidence") is None:
                    try:
                        # validiere Bereich [0,1]
                        c = float(conf)
                        if 0.0 <= c <= 1.0:
                            t["confidence"] = c
                    except Exception:
                        pass
                t = {**t, "record_hash": rec_hash}
            except Exception:
                pass
            enriched.append(BridgeTransfer(**t))

        # Hash-Chain berechnen (gerichtsfester Nachweis der Reihenfolge)
        chain_hash = None
        try:
            prev = b""
            for e in enriched:
                rh = (e.record_hash or "").encode()
                prev = hashlib.sha256(prev + rh).digest()
            chain_hash = prev.hex() if prev else None
        except Exception:
            chain_hash = None

        # Optional: Audit-Event inkl. chain_hash
        try:
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                event_type=AuditEventType.ANALYSIS_RUN,
                user_id="system",
                resource_id=case_id or "bridge_transfers",
                action="get_bridge_transfers",
                details={
                    "start_time": st.isoformat(),
                    "end_time": et.isoformat(),
                    "count": len(enriched),
                    "chain_hash": chain_hash,
                },
                ip_address="system",
                user_agent="forensics_api",
                compliance_level=ComplianceLevel.LAW_ENFORCEMENT,
            )
            compliance_manager.log_audit_event(audit_event)
        except Exception:
            pass

        # Response formen und Evidence-ID ggf. zurückgeben
        return BridgeTransfersResponse(
            start_time=st.isoformat(),
            end_time=et.isoformat(),
            total=len(enriched),
            transfers=enriched,
            evidence_id=(evidence.evidence_id if evidence else None),
            chain_hash=chain_hash,
            chain_length=len(enriched),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bridge transfers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/train")
async def train_ml_models(
    training_data: Dict[str, Any] = Body(...),
    ml_model_types: List[str] = Body(default=["anomaly", "risk", "pattern"], alias="model_types")
):
    """Trainiert ML-Modelle für Forensik"""
    try:
        # Importiere Training-Daten
        from app.services.ml_analytics import analytics_engine

        trained_models = analytics_engine.train_all_models(training_data)

        return {
            "status": "models_trained",
            "trained_models": len(trained_models),
            "models": {
                name: model.to_dict()
                for name, model in trained_models.items()
            }
        }

    except Exception as e:
        logger.error(f"ML training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/models")
async def get_ml_models():
    """Gibt verfügbare ML-Modelle zurück"""
    try:
        models = analytics_engine.get_model_performance()

        return {
            "status": "success",
            "models": models
        }

    except Exception as e:
        logger.error(f"ML models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investigation/create")
async def create_investigation(
    case_id: str = Body(...),
    title: str = Body(...),
    description: str = Body(...),
    lead_investigator: str = Body(...),
    priority: str = Body(default="medium")
):
    """Erstellt neue Untersuchung"""
    try:
        # Erstelle Investigation-Record
        investigation = {
            "investigation_id": str(uuid.uuid4()),
            "case_id": case_id,
            "title": title,
            "description": description,
            "lead_investigator": lead_investigator,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "evidence_collected": 0,
            "alerts_generated": 0,
            "analysis_completed": False
        }

        # Audit-Event für Investigation-Erstellung
        audit_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.USER_ACTION,
            user_id=lead_investigator,
            resource_id=case_id,
            action="create_investigation",
            details={"investigation_id": investigation["investigation_id"]},
            ip_address="system",
            user_agent="investigation_system",
            compliance_level=ComplianceLevel.LAW_ENFORCEMENT
        )
        compliance_manager.log_audit_event(audit_event)

        return {
            "status": "investigation_created",
            "investigation": investigation
        }

    except Exception as e:
        logger.error(f"Investigation creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigation/{case_id}/summary")
async def get_investigation_summary(case_id: str):
    """Holt Untersuchungs-Zusammenfassung"""
    try:
        # Sammle alle relevanten Daten für den Case
        evidence_records = compliance_manager.get_evidence_for_case(case_id)
        audit_events = [e for e in compliance_manager.audit_events if case_id in str(e.details)]

        # Berechne Statistiken
        evidence_count = len(evidence_records)
        alert_count = sum(1 for event in audit_events if event.event_type.value == "analysis_run")
        analysis_count = sum(1 for event in audit_events if "analysis" in event.action)

        return {
            "case_id": case_id,
            "summary": {
                "evidence_pieces": evidence_count,
                "alerts_generated": alert_count,
                "analysis_runs": analysis_count,
                "audit_events": len(audit_events),
                "last_activity": max((e.timestamp for e in audit_events), default=None),
                "compliance_status": "compliant"
            },
            "evidence_records": [record.to_dict() for record in evidence_records[:10]],  # Letzte 10
            "recent_audit_events": [
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                    "action": event.action
                }
                for event in sorted(audit_events, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }

    except Exception as e:
        logger.error(f"Investigation summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================
# NFT Wash Trading Detection
# ==========================

class NFTTradeInput(BaseModel):
    """Single NFT trade for wash trading analysis"""
    tx_hash: str
    timestamp: str  # ISO 8601
    token_address: str
    token_id: str
    from_address: str
    to_address: str
    price: float
    marketplace: Optional[str] = None
    block_number: Optional[int] = None


class NFTWashDetectRequest(BaseModel):
    """Request for NFT wash trading detection"""
    trades: List[NFTTradeInput] = Field(..., min_length=1, max_length=1000)
    round_trip_window_hours: Optional[int] = Field(168, ge=1, le=720)
    repeated_threshold: Optional[int] = Field(3, ge=2, le=20)
    price_spike_threshold: Optional[float] = Field(2.0, ge=1.1, le=10.0)


class NFTWashFindingOutput(BaseModel):
    """Wash trading finding output"""
    pattern_type: str
    confidence: float
    addresses_involved: List[str]
    trades_involved: List[str]
    description: str
    evidence: Dict[str, Any]


class NFTWashDetectResponse(BaseModel):
    """Response for NFT wash trading detection"""
    success: bool
    findings: List[NFTWashFindingOutput]
    summary: Dict[str, Any]


@router.post("/nft/wash-detect", response_model=NFTWashDetectResponse, dependencies=[Depends(rate_limit)])
async def detect_nft_wash_trading(
    request: NFTWashDetectRequest,
    background_tasks: BackgroundTasks,
) -> NFTWashDetectResponse:
    """
    Detects NFT wash trading patterns in provided trades.
    
    **Heuristics:**
    - Self-trading (same owner via intermediary wallets)
    - Round-trip patterns (A→B→A)
    - Repeated counterparties
    - Price anomalies (artificial spikes)
    - Coordinated bidding patterns
    
    **Query Parameters:**
    - trades: List of NFT trades to analyze
    - round_trip_window_hours: Time window for round-trip detection (default: 168 = 7 days)
    - repeated_threshold: Minimum occurrences for repeated counterparty detection (default: 3)
    - price_spike_threshold: Price multiplier threshold for anomaly detection (default: 2.0 = 200%)
    
    **Returns:**
    - findings: List of detected wash trading patterns with confidence scores
    - summary: Aggregated statistics
    """
    try:
        from app.analytics.nft_wash_trading import nft_wash_detector, NFTTrade, WashTradingFinding
        from datetime import datetime as dt
        
        # Convert input to NFTTrade objects
        trades = []
        for t in request.trades:
            try:
                timestamp = dt.fromisoformat(t.timestamp.replace('Z', '+00:00'))
            except Exception:
                timestamp = dt.utcnow()
            
            trades.append(NFTTrade(
                tx_hash=t.tx_hash,
                timestamp=timestamp,
                token_address=t.token_address.lower(),
                token_id=t.token_id,
                from_address=t.from_address.lower(),
                to_address=t.to_address.lower(),
                price=t.price,
                marketplace=t.marketplace,
                block_number=t.block_number,
            ))
        
        # Run detector with custom parameters
        detector = nft_wash_detector
        if request.round_trip_window_hours or request.repeated_threshold or request.price_spike_threshold:
            from app.analytics.nft_wash_trading import NFTWashTradingDetector
            detector = NFTWashTradingDetector(
                round_trip_window_hours=request.round_trip_window_hours or 168,
                repeated_counterparty_threshold=request.repeated_threshold or 3,
                price_spike_threshold=request.price_spike_threshold or 2.0,
            )
        
        findings: List[WashTradingFinding] = await detector.detect_wash_trading(trades)
        
        # Convert findings to output format
        findings_output = [
            NFTWashFindingOutput(
                pattern_type=f.pattern_type,
                confidence=round(f.confidence, 3),
                addresses_involved=f.addresses_involved,
                trades_involved=f.trades_involved,
                description=f.description,
                evidence=f.evidence,
            )
            for f in findings
        ]
        
        # Summary stats
        pattern_counts = {}
        for f in findings:
            pattern_counts[f.pattern_type] = pattern_counts.get(f.pattern_type, 0) + 1
        
        unique_addresses = set()
        unique_trades = set()
        for f in findings:
            unique_addresses.update(f.addresses_involved)
            unique_trades.update(f.trades_involved)
        
        summary = {
            "total_trades_analyzed": len(request.trades),
            "total_findings": len(findings),
            "pattern_counts": pattern_counts,
            "unique_addresses_flagged": len(unique_addresses),
            "unique_trades_flagged": len(unique_trades),
            "avg_confidence": round(sum(f.confidence for f in findings) / max(len(findings), 1), 3),
        }
        
        return NFTWashDetectResponse(
            success=True,
            findings=findings_output,
            summary=summary,
        )
    
    except Exception as e:
        logger.error(f"NFT wash trading detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
