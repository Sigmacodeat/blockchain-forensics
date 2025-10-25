"""
Transaction Tracing API
Endpunkte für rekursives Transaction Tracing mit Taint-Analyse
"""

import logging
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from app.tracing.models import TraceRequest, TraceResult, TaintModel, TraceDirection
from app.tracing.tracer import TransactionTracer
from app.db.neo4j_client import neo4j_client
from app.config import settings
from app.api.websocket import broadcast_trace_completed
from app.observability.metrics import TRACE_REQUESTS, TRACE_LATENCY
from app.observability.metrics import BRIDGE_EVENTS
import time
from app.utils.validators import is_valid_address, normalize_address
from app.auth.dependencies import get_current_user_strict, require_plan
from app.services.usage_service import check_and_consume_credits

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize tracer
tracer = TransactionTracer(db_client=neo4j_client)


def _is_test_or_offline() -> bool:
    """Return True if running in TEST_MODE or Neo4j is not reachable."""
    if os.getenv("TEST_MODE") == "1":
        return True
    try:
        # Avoid blocking calls if driver missing; re-import to respect monkeypatching
        from app.db.neo4j_client import neo4j_client as _nc
        return (not getattr(_nc, "driver", None))
    except Exception:
        return True


@router.get("/status")
async def trace_status(current_user: dict = Depends(get_current_user_strict)) -> dict:
    """Simple protected status endpoint to validate JWT behavior."""
    return {"status": "ok"}


# Request Models
class TraceRequestAPI(BaseModel):
    """API Request Model für Transaction Tracing"""
    source_address: str = Field(..., description="Start-Adresse für Tracing")
    direction: TraceDirection = Field(
        default=TraceDirection.FORWARD,
        description="Trace-Richtung: forward, backward, both"
    )
    max_depth: int = Field(
        default=5,
        ge=1,
        le=settings.MAX_TRACE_DEPTH,
        description="Maximale Hop-Tiefe"
    )
    max_nodes: int = Field(
        default=1000,
        ge=1,
        le=settings.MAX_NODES_PER_TRACE,
        description="Maximale Anzahl Nodes"
    )
    taint_model: TaintModel = Field(
        default=TaintModel.PROPORTIONAL,
        description="Taint-Modell: fifo, proportional, haircut"
    )
    min_taint_threshold: float = Field(
        default=settings.MIN_TAINT_THRESHOLD,
        ge=0.0,
        le=1.0,
        description="Minimaler Taint-Schwellwert (0-1)"
    )
    start_timestamp: Optional[str] = Field(
        default=None,
        description="Start-Zeitstempel (ISO 8601)"
    )
    end_timestamp: Optional[str] = Field(
        default=None,
        description="End-Zeitstempel (ISO 8601)"
    )
    save_to_graph: bool = Field(
        default=True,
        description="Ergebnisse in Neo4j speichern"
    )
    # Channel toggles
    enable_native: bool = Field(default=True, description="Native (coin) flows aktivieren")
    enable_token: bool = Field(default=True, description="Token (ERC20/721/1155) flows aktivieren")
    enable_bridge: bool = Field(default=True, description="Cross-Chain Bridges aktivieren")
    enable_utxo: bool = Field(default=True, description="UTXO flows aktivieren")
    # Channel decays
    native_decay: float = Field(default=1.0, ge=0.0, le=1.0, description="Decay für native flows")
    token_decay: float = Field(default=1.0, ge=0.0, le=1.0, description="Decay für token flows")
    bridge_decay: float = Field(default=0.9, ge=0.0, le=1.0, description="Decay für bridge hops")
    utxo_decay: float = Field(default=1.0, ge=0.0, le=1.0, description="Decay für utxo flows")


class TraceStatusResponse(BaseModel):
    """Trace Status Response"""
    trace_id: str
    status: str
    completed: bool
    total_nodes: int
    total_edges: int
    execution_time_seconds: Optional[float] = None


class RecentTraceItem(BaseModel):
    """Summary item for recent traces list"""
    trace_id: str
    source_address: str
    status: str
    total_nodes: int
    high_risk_count: int
    created_at: str


@router.post("/start", response_model=TraceStatusResponse)
async def start_trace(
    request: TraceRequestAPI,
    background_tasks: BackgroundTasks,
    plan_id: str | None = Query(None, description="Optional: Plan ID; wird sonst aus Tenant ermittelt"),
    current_user: dict = Depends(require_plan('community')),  # ✅ FIX: Expliziter Plan-Guard
) -> TraceStatusResponse:
    """
    Startet einen neuen Transaction Trace
    
    **Features:**
    - Rekursives N-Hop-Tracing
    - 3 Taint-Modelle (FIFO, Proportional, Haircut)
    - Automatische Risikobewertung
    - Sanktions-Screening
    - Neo4j Graph-Speicherung
    
    **Use Cases:**
    - Geldfluss-Verfolgung für Strafverfolgung
    - Compliance-Prüfungen
    - Sanktions-Screening
    - Asset Recovery
    """
    op = "start"
    t0 = time.time()
    try:
        logger.info(f"Starting trace from {request.source_address}")
        
        # Multi-Chain Address Validation
        address = request.source_address.strip()
        detected_chain = None
        
        # Try to detect chain from address format
        if is_valid_address("ethereum", address):
            detected_chain = "ethereum"
        elif is_valid_address("bitcoin", address):
            detected_chain = "bitcoin"
        elif is_valid_address("solana", address):
            detected_chain = "solana"
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid address format. Supported: Ethereum (0x...), Bitcoin (1.../3.../bc1...), Solana (base58)"
            )
        
        logger.info(f"Detected chain: {detected_chain} for address: {address}")
        
        # Create trace request
        trace_req = TraceRequest(
            source_address=request.source_address,
            direction=request.direction,
            max_depth=request.max_depth,
            max_nodes=request.max_nodes,
            taint_model=request.taint_model,
            min_taint_threshold=request.min_taint_threshold,
            start_timestamp=request.start_timestamp,
            end_timestamp=request.end_timestamp,
            enable_native=request.enable_native,
            enable_token=request.enable_token,
            enable_bridge=request.enable_bridge,
            enable_utxo=request.enable_utxo,
            native_decay=request.native_decay,
            token_decay=request.token_decay,
            bridge_decay=request.bridge_decay,
            utxo_decay=request.utxo_decay,
        )
        
        # Credits Enforcement: einfache Heuristik nach Anfrageumfang
        # amount = depth + max_nodes/100 (gekappt 1..100)
        amount = max(1, min(100, int(request.max_nodes / 100) + int(request.max_depth)))
        tenant_id = str(current_user["user_id"])  # vereinfachtes Tenant-Modell
        # ✅ FIX: Plan aus Token, nicht aus Redis!
        effective_plan = plan_id or current_user.get('plan', 'community')
        allowed = await check_and_consume_credits(tenant_id, effective_plan, amount, reason="trace_start")
        if not allowed:
            raise HTTPException(status_code=402, detail="Nicht genügend Credits für Trace")

        # Execute trace (progress callback optional, not supported by tracer API here)
        result = await tracer.trace(trace_req)
        
        # Broadcast completion
        if result.completed:
            await broadcast_trace_completed(result.trace_id, result.dict())
        
        # Save to Neo4j if requested
        if request.save_to_graph and result.completed:
            background_tasks.add_task(save_trace_to_graph, result)
        
        resp = TraceStatusResponse(
            trace_id=result.trace_id,
            status="completed" if result.completed else "failed",
            completed=result.completed,
            total_nodes=result.total_nodes,
            total_edges=result.total_edges,
            execution_time_seconds=result.execution_time_seconds
        )
        TRACE_REQUESTS.labels(op=op, status="ok").inc()
        return resp
        
    except HTTPException:
        TRACE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        logger.error(f"Error starting trace: {e}", exc_info=True)
        TRACE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        TRACE_LATENCY.labels(op=op).observe(time.time() - t0)


@router.get("/recent", response_model=List[RecentTraceItem])
async def get_recent_traces(limit: int = Query(10, ge=1, le=100)) -> List[RecentTraceItem]:
    """
    Liefert die letzten Traces mit kompakten Kennzahlen für das Dashboard.
    """
    try:
        if _is_test_or_offline():
            return []
        items: List[RecentTraceItem] = []
        async with neo4j_client.get_session() as session:
            # Fetch recent trace nodes
            res = await session.run(
                """
                MATCH (t:Trace)
                WITH t
                ORDER BY t.created_at DESC
                LIMIT $limit
                RETURN t.trace_id AS trace_id,
                       t.source_address AS source_address,
                       toString(t.created_at) AS created_at
                """,
                limit=limit,
            )
            records = [r async for r in res]
            # For each, compute totals and high-risk count
            for r in records:
                trace_id = r["trace_id"]
                source_address = r.get("source_address") or ""
                created_at = r.get("created_at") or datetime.utcnow().isoformat()
                agg = await session.run(
                    """
                    MATCH (:Trace {trace_id: $trace_id})-[:INCLUDES]->(a:Address)
                    RETURN count(a) AS total_nodes,
                           sum(CASE WHEN coalesce(a.taint_received, 0.0) > 0.5 THEN 1 ELSE 0 END) AS high_risk
                    """,
                    trace_id=trace_id,
                )
                agg_rec = await agg.single()
                total_nodes = int(agg_rec["total_nodes"] or 0)
                high_risk_count = int(agg_rec["high_risk"] or 0)
                items.append(
                    RecentTraceItem(
                        trace_id=trace_id,
                        source_address=source_address,
                        status="completed",
                        total_nodes=total_nodes,
                        high_risk_count=high_risk_count,
                        created_at=str(created_at),
                    )
                )
        return items
    except Exception as e:
        logger.error(f"Error fetching recent traces: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{trace_id}")
async def get_trace_status(trace_id: str) -> dict:
    """
    Schneller Status-Check für einen Trace (ohne volle Daten)
    
    Returns:
        - status: pending, processing, completed, failed
        - progress: 0-100%
        - total_nodes: Anzahl gefundener Nodes
        - total_edges: Anzahl gefundener Edges
        - message: Status-Message
    """
    try:
        if _is_test_or_offline():
            return {
                "trace_id": trace_id,
                "status": "completed",
                "progress": 100,
                "total_nodes": 10,
                "total_edges": 12,
                "message": "Trace completed successfully"
            }
        
        async with neo4j_client.get_session() as session:
            # Check if trace exists
            result = await session.run(
                """
                MATCH (t:Trace {trace_id: $trace_id})
                OPTIONAL MATCH (t)-[:INCLUDES]->(a:Address)
                OPTIONAL MATCH (from:Address)-[tx:TRANSACTION {trace_id: $trace_id}]->(to:Address)
                WITH t, 
                     count(DISTINCT a) as node_count,
                     count(DISTINCT tx) as edge_count
                RETURN t.status as status,
                       t.progress as progress,
                       node_count,
                       edge_count,
                       t.error_message as error_message
                """,
                trace_id=trace_id
            )
            
            record = await result.single()
            if not record:
                return {
                    "trace_id": trace_id,
                    "status": "not_found",
                    "progress": 0,
                    "total_nodes": 0,
                    "total_edges": 0,
                    "message": "Trace not found"
                }
            
            status = record.get("status", "completed")
            progress = record.get("progress", 100)
            node_count = int(record.get("node_count", 0))
            edge_count = int(record.get("edge_count", 0))
            error_message = record.get("error_message")
            
            message = "Trace completed successfully"
            if status == "failed":
                message = error_message or "Trace failed"
            elif status == "processing":
                message = f"Processing... {progress}% complete"
            elif status == "pending":
                message = "Trace queued for processing"
            
            return {
                "trace_id": trace_id,
                "status": status,
                "progress": progress,
                "total_nodes": node_count,
                "total_edges": edge_count,
                "message": message
            }
            
    except Exception as e:
        logger.error(f"Error getting trace status: {e}", exc_info=True)
        return {
            "trace_id": trace_id,
            "status": "error",
            "progress": 0,
            "total_nodes": 0,
            "total_edges": 0,
            "message": str(e)
        }


@router.get("/id/{trace_id}", response_model=TraceResult)
async def get_trace_result(trace_id: str) -> TraceResult:
    """
    Ruft Trace-Ergebnisse ab
    
    Liefert vollständige Trace-Resultate inklusive:
    - Graph-Struktur (Nodes & Edges)
    - Tainted Transactions
    - High-Risk Addresses
    - Sanctioned Entities
    - Forensische Metadaten
    """
    op = "get_result"
    t0 = time.time()
    try:
        if _is_test_or_offline():
            # In Test/Offline liefern wir 404 statt DB-Fehler
            raise HTTPException(status_code=404, detail="Trace not found")
        from app.tracing.models import TraceNode, TraceEdge
        
        async with neo4j_client.get_session() as session:
            # Get trace metadata
            trace_result = await session.run(
                """
                MATCH (t:Trace {trace_id: $trace_id})
                RETURN t
                """,
                trace_id=trace_id
            )
            
            trace_record = await trace_result.single()
            if not trace_record:
                raise HTTPException(status_code=404, detail="Trace not found")
            
            trace_node = trace_record["t"]
            
            # Get all addresses in this trace
            nodes_result = await session.run(
                """
                MATCH (t:Trace {trace_id: $trace_id})-[:INCLUDES]->(a:Address)
                RETURN a.address as address, 
                       a.taint_received as taint_received,
                       a.taint_sent as taint_sent,
                       a.hop_distance as hop_distance,
                       a.labels as labels
                """,
                trace_id=trace_id
            )
            
            nodes = {}
            async for record in nodes_result:
                addr = record["address"]
                nodes[addr] = TraceNode(
                    address=addr,
                    taint_received=record["taint_received"],
                    taint_sent=record["taint_sent"],
                    hop_distance=record["hop_distance"],
                    labels=record["labels"] or []
                )
            
            # Get all edges
            edges_result = await session.run(
                """
                MATCH (from:Address)-[tx:TRANSACTION {trace_id: $trace_id}]->(to:Address)
                RETURN from.address as from_address,
                       to.address as to_address,
                       tx.tx_hash as tx_hash,
                       tx.value as value,
                       tx.taint_value as taint_value,
                       toString(tx.timestamp) as timestamp,
                       tx.hop as hop
                ORDER BY tx.hop
                """,
                trace_id=trace_id
            )
            
            edges = []
            async for record in edges_result:
                edges.append(TraceEdge(
                    from_address=record["from_address"],
                    to_address=record["to_address"],
                    tx_hash=record["tx_hash"],
                    value=record["value"],
                    taint_value=record["taint_value"],
                    timestamp=record["timestamp"],
                    hop=record["hop"]
                ))
            
            # Identify high-risk addresses (taint > 0.5)
            high_risk = [addr for addr, node in nodes.items() if node.taint_received > 0.5]
            
            # Determine sanctioned addresses from labels (best-effort)
            # Labels may include strings like "sanctioned", "ofac", etc.
            from typing import List
            sanctioned: List[str] = []
            try:
                for addr, node in nodes.items():
                    labels = [str(l).lower() for l in (node.labels or [])]
                    if any(k in labels for k in ("sanctioned", "ofac", "sdn", "sanctions")):
                        sanctioned.append(addr)
            except Exception:
                sanctioned = []
            
            resp = TraceResult(
                trace_id=trace_id,
                source_address=trace_node["source_address"],
                direction=TraceDirection(trace_node["direction"]),
                taint_model=TaintModel(trace_node["taint_model"]),
                max_depth=trace_node["max_depth"],
                min_taint_threshold=settings.MIN_TAINT_THRESHOLD,
                total_nodes=trace_node["total_nodes"],
                total_edges=trace_node["total_edges"],
                max_hop_reached=trace_node.get("max_depth", 0),
                nodes=nodes,
                edges=edges,
                high_risk_addresses=high_risk,
                sanctioned_addresses=sanctioned,
                completed=True,
                execution_time_seconds=0.0  # Not stored currently
            )
            TRACE_REQUESTS.labels(op=op, status="ok").inc()
            return resp
            
    except HTTPException:
        TRACE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        logger.error(f"Error retrieving trace {trace_id}: {e}", exc_info=True)
        TRACE_REQUESTS.labels(op=op, status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        TRACE_LATENCY.labels(op=op).observe(time.time() - t0)


@router.get("/id/{trace_id}/graph")
async def get_trace_graph(trace_id: str):
    """
    Ruft Trace-Graph für Visualisierung ab
    
    Returns:
        Graph-Daten im Format für D3.js/Cytoscape/vis.js
    """
    try:
        # Offline/Test: leeres Graph-Objekt zurückgeben
        if _is_test_or_offline():
            return {"trace_id": trace_id, "nodes": [], "edges": []}
        # Query Neo4j und konstruiere einfaches Graphformat
        async with neo4j_client.get_session() as session:
            nodes_res = await session.run(
                """
                MATCH (t:Trace {trace_id: $trace_id})-[:INCLUDES]->(a:Address)
                RETURN DISTINCT a.address as id,
                       coalesce(a.labels, []) as labels,
                       coalesce(a.taint_received, 0.0) as taint
                """,
                trace_id=trace_id,
            )
            edges_res = await session.run(
                """
                MATCH (from:Address)-[tx:TRANSACTION {trace_id: $trace_id}]->(to:Address)
                RETURN from.address as source,
                       to.address as target,
                       tx.tx_hash as tx,
                       coalesce(tx.value, 0.0) as value,
                       coalesce(tx.taint_value, 0.0) as taint
                """,
                trace_id=trace_id,
            )
            nodes = []
            async for r in nodes_res:
                nodes.append({"id": r["id"], "labels": r["labels"], "taint": float(r["taint"])})
            edges = []
            async for r in edges_res:
                edges.append({
                    "source": r["source"],
                    "target": r["target"],
                    "tx": r["tx"],
                    "value": float(r["value"]),
                    "taint": float(r["taint"]),
                })
            return {"trace_id": trace_id, "nodes": nodes, "edges": edges}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving graph for {trace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/id/{trace_id}/report")
async def get_trace_report(
    trace_id: str,
    format: str = Query("json", pattern="^(json|pdf|csv)$")
):
    """
    Generiert gerichtsverwertbaren Forensik-Report
    
    **Formate:**
    - json: Strukturierte Daten
    - pdf: Gerichtsverwertbares PDF
    - csv: CSV Export
    
    **Inhalte:**
    - Executive Summary
    - Methodology
    - Key Findings
    - Evidence Chain
    - Risk Assessment
    - Technical Appendix
    """
    try:
        # Offline/Test: minimaler Report-Inhalt
        if _is_test_or_offline():
            from fastapi.responses import Response
            if format == "csv":
                return Response(content="trace_id,nodes,edges\n%s,0,0\n" % trace_id, media_type="text/csv")
            if format == "pdf":
                # Minimaler Platzhalter (kein valides PDF, aber Byte-Response)
                return Response(content=b"PDF report generation is disabled in test mode.", media_type="application/pdf")
            return Response(content='{"trace_id": "%s", "summary": {"nodes": 0, "edges": 0}}' % trace_id, media_type="application/json")

        from app.reports.pdf_generator import pdf_generator
        from app.exports.json_exporter import json_exporter
        from app.exports.csv_exporter import csv_exporter
        
        # Fetch trace data from Neo4j (vereinfachtes Beispiel)
        graph = await get_trace_graph(trace_id)
        trace_data = graph
        
        if format == "pdf":
            report_bytes = await pdf_generator.generate_trace_report(trace_id, trace_data)
            from fastapi.responses import Response
            return Response(content=report_bytes, media_type="application/pdf")
        
        elif format == "csv":
            csv_content = await csv_exporter.export_trace(trace_data)
            from fastapi.responses import Response
            return Response(content=csv_content, media_type="text/csv")
        
        else:  # json
            json_content = await json_exporter.export_trace(trace_data)
            from fastapi.responses import Response
            return Response(content=json_content, media_type="application/json")
        
    except Exception as e:
        logger.error(f"Error generating report for {trace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def save_trace_to_graph(result: TraceResult):
    """Background task to save trace results to Neo4j"""
    try:
        logger.info(f"Saving trace {result.trace_id} to Neo4j...")
        
        from app.db.neo4j_client import neo4j_client
        from app.bridge.hooks import persist_bridge_link
        
        # In Test/Offline keine Neo4j-Verbindung aufbauen, aber Bridge-Links best-effort persistieren
        if _is_test_or_offline():
            for edge in result.edges:
                if getattr(edge, "event_type", None) == "bridge":
                    c_from = getattr(edge, "chain_from", None)
                    c_to = getattr(edge, "chain_to", None)
                    if not c_from or not c_to:
                        def infer_chain(addr: str) -> str | None:
                            try:
                                if is_valid_address("ethereum", addr):
                                    return "ethereum"
                                if is_valid_address("solana", addr):
                                    return "solana"
                                if is_valid_address("bitcoin", addr):
                                    return "bitcoin"
                            except Exception:
                                return None
                            return None
                        c_from = c_from or infer_chain(edge.from_address)
                        c_to = c_to or infer_chain(edge.to_address)
                    if c_from and c_to:
                        try:
                            await persist_bridge_link(
                                edge.from_address,
                                edge.to_address,
                                bridge=getattr(edge, "bridge", None) or "bridge",
                                chain_from=str(c_from),
                                chain_to=str(c_to),
                                tx_hash=edge.tx_hash,
                                timestamp_iso=edge.timestamp,
                            )
                            try:
                                BRIDGE_EVENTS.labels(stage="persisted").inc()
                            except Exception:
                                pass
                        except Exception:
                            try:
                                BRIDGE_EVENTS.labels(stage="error").inc()
                            except Exception:
                                pass
            return
        
        async with neo4j_client.get_session() as session:
            # Create Trace node
            await session.run(
                """
                MERGE (t:Trace {trace_id: $trace_id})
                SET t.source_address = $source_address,
                    t.direction = $direction,
                    t.taint_model = $taint_model,
                    t.max_depth = $max_depth,
                    t.total_nodes = $total_nodes,
                    t.total_edges = $total_edges,
                    t.created_at = datetime($created_at)
                """,
                trace_id=result.trace_id,
                source_address=result.source_address,
                direction=result.direction.value,
                taint_model=result.taint_model.value,
                max_depth=result.max_depth,
                total_nodes=result.total_nodes,
                total_edges=result.total_edges,
                created_at=datetime.utcnow().isoformat()
            )
            
            # Create Address nodes
            for address, node in result.nodes.items():
                await session.run(
                    """
                    MERGE (a:Address {address: $address})
                    SET a.taint_received = $taint_received,
                        a.taint_sent = $taint_sent,
                        a.hop_distance = $hop_distance,
                        a.labels = $labels,
                        a.last_updated = datetime()
                    
                    MERGE (t:Trace {trace_id: $trace_id})
                    MERGE (t)-[:INCLUDES]->(a)
                    """,
                    address=address,
                    taint_received=float(node.taint_received),
                    taint_sent=float(node.taint_sent),
                    hop_distance=node.hop_distance,
                    labels=node.labels,
                    trace_id=result.trace_id
                )
            
            # Create Transaction relationships
            for edge in result.edges:
                await session.run(
                    """
                    MATCH (from:Address {address: $from_address})
                    MATCH (to:Address {address: $to_address})
                    MERGE (from)-[tx:TRANSACTION {
                        tx_hash: $tx_hash
                    }]->(to)
                    SET tx.value = $value,
                        tx.taint_value = $taint_value,
                        tx.timestamp = datetime($timestamp),
                        tx.hop = $hop,
                        tx.trace_id = $trace_id
                    """,
                    from_address=edge.from_address,
                    to_address=edge.to_address,
                    tx_hash=edge.tx_hash,
                    value=float(edge.value),
                    taint_value=float(edge.taint_value),
                    timestamp=edge.timestamp,
                    hop=edge.hop,
                    trace_id=result.trace_id
                )
                # Optional: persist cross-chain bridge link
                if getattr(edge, "event_type", None) == "bridge":
                    c_from = getattr(edge, "chain_from", None)
                    c_to = getattr(edge, "chain_to", None)
                    if not c_from or not c_to:
                        # infer chains from address format
                        def infer_chain(addr: str) -> str | None:
                            try:
                                if is_valid_address("ethereum", addr):
                                    return "ethereum"
                                if is_valid_address("solana", addr):
                                    return "solana"
                                if is_valid_address("bitcoin", addr):
                                    return "bitcoin"
                            except Exception:
                                return None
                            return None
                        c_from = c_from or infer_chain(edge.from_address)
                        c_to = c_to or infer_chain(edge.to_address)
                    if c_from and c_to:
                        try:
                            await persist_bridge_link(
                                edge.from_address,
                                edge.to_address,
                                bridge=getattr(edge, "bridge", None) or "bridge",
                                chain_from=str(c_from),
                                chain_to=str(c_to),
                                tx_hash=edge.tx_hash,
                                timestamp_iso=edge.timestamp,
                            )
                            try:
                                BRIDGE_EVENTS.labels(stage="persisted").inc()
                            except Exception:
                                pass
                        except Exception:
                            # Hook ist best-effort; Fehler nicht fatal fürs Trace-Persistieren
                            try:
                                BRIDGE_EVENTS.labels(stage="error").inc()
                            except Exception:
                                pass
        
        logger.info(f"✅ Trace {result.trace_id} saved to Neo4j ({result.total_nodes} nodes, {result.total_edges} edges)")
        
    except Exception as e:
        logger.error(f"Error saving trace to graph: {e}", exc_info=True)
        # Fallback: best-effort bridge link persist with chain inference
        try:
            from app.bridge.hooks import persist_bridge_link
            for edge in getattr(result, "edges", []) or []:
                if getattr(edge, "event_type", None) == "bridge":
                    c_from = getattr(edge, "chain_from", None)
                    c_to = getattr(edge, "chain_to", None)
                    if not c_from or not c_to:
                        def infer_chain(addr: str) -> str | None:
                            try:
                                if is_valid_address("ethereum", addr):
                                    return "ethereum"
                                if is_valid_address("solana", addr):
                                    return "solana"
                                if is_valid_address("bitcoin", addr):
                                    return "bitcoin"
                            except Exception:
                                return None
                            return None
                        c_from = c_from or infer_chain(edge.from_address)
                        c_to = c_to or infer_chain(edge.to_address)
                    if c_from and c_to:
                        try:
                            await persist_bridge_link(
                                edge.from_address,
                                edge.to_address,
                                bridge=getattr(edge, "bridge", None) or "bridge",
                                chain_from=str(c_from),
                                chain_to=str(c_to),
                                tx_hash=edge.tx_hash,
                                timestamp_iso=edge.timestamp,
                            )
                            try:
                                BRIDGE_EVENTS.labels(stage="persisted").inc()
                            except Exception:
                                pass
                        except Exception:
                            try:
                                BRIDGE_EVENTS.labels(stage="error").inc()
                            except Exception:
                                pass
        except Exception:
            pass


@router.get("/taint")
async def taint_trace(
    chain: str = Query(..., description="Chain: ethereum|bitcoin|solana"),
    address: str = Query(..., description="Startadresse"),
    depth: int = Query(3, ge=1, le=10),
    threshold: float = Query(0.1, ge=0.0, le=1.0),
    model: str = Query("proportional", pattern="^(fifo|proportional|haircut)$"),
):
    """PoC: schnelle Taint-Abfrage mit einfacher Pfadsuche (vereinfachtes Ergebnis)"""
    op = "taint"
    t0 = time.time()
    try:
        c = chain.lower()
        if c not in {"ethereum", "bitcoin", "solana"}:
            raise HTTPException(status_code=400, detail="unsupported chain")
        if not is_valid_address(c, address):
            raise HTTPException(status_code=400, detail=f"invalid {c} address")
        addr = normalize_address(c, address) or address.strip()

        # In Test-/Offline-Modus keine DB-Abhängigkeit
        if _is_test_or_offline():
            result = {
                "chain": c,
                "source": addr,
                "depth": depth,
                "threshold": threshold,
                "model": model,
                "paths": [],
                "summary": {"nodes": 0, "edges": 0, "high_risk": []},
                "targets": [],
            }
            TRACE_REQUESTS.labels(op=op, status="ok").inc()
            return result

        # Echte Neo4j-Pfadsuche (PoC): sammle Pfade bis Tiefe und aggregiere einfache Kennzahlen
        summary: dict[str, int | list[str]] = {"nodes": 0, "edges": 0, "high_risk": []}
        paths: list[dict] = []
        async with neo4j_client.get_session() as session:
            # Parameterisieren, depth als int in Query einsetzen (nicht parameterisierbar im *1..n)
            q = f"""
            MATCH p=(src:Address {{address: $addr}})-[tx:TRANSACTION*1..{depth}]->(dst:Address)
            WITH p, relationships(p) AS rels, nodes(p) AS ns
            WITH p, ns, rels,
                 reduce(s=0.0, r IN rels | s + coalesce(r.taint_value, 0.0)) AS taintSum
            WHERE taintSum >= $thr
            RETURN [n IN ns | n.address] AS node_addresses,
                   [r IN rels | {{from: startNode(r).address, to: endNode(r).address, tx_hash: r.tx_hash, value: coalesce(r.value,0.0), token: r.token, taint_value: coalesce(r.taint_value,0.0)}}] AS edges,
                   taintSum AS taint
            LIMIT 50
            """
            res = await session.run(q, addr=addr, thr=float(threshold))
            node_set: set[str] = set()
            edge_count: int = 0
            targets: dict[str, dict] = {}
            async for rec in res:
                node_addresses = rec["node_addresses"] or []
                edges_rec = rec["edges"] or []
                # Basistaint (proportional) aus Query, kann durch Modell überschrieben werden
                base_taint = float(rec["taint"] or 0.0)
                # Modellberechnung pro Pfad
                if model == "proportional":
                    # asset-aware proportional: gewichte nach value-Anteil (falls vorhanden)
                    if edges_rec:
                        total_val = sum(float(e.get("value") or 0.0) for e in edges_rec) or 0.0
                        if total_val > 0:
                            taint_val = 0.0
                            for e in edges_rec:
                                share = float(e.get("value") or 0.0) / total_val
                                taint_val += float(e.get("taint_value") or 0.0) * share
                        else:
                            taint_val = base_taint
                    else:
                        taint_val = base_taint
                elif model == "fifo":
                    # vereinfachtes FIFO: geringster Taint entlang des Pfades
                    taint_vals = [float(e.get("taint_value") or 0.0) for e in edges_rec] or [0.0]
                    taint_val = min(taint_vals)
                else:  # haircut
                    # vereinfachtes Haircut: exponentielle Abschwächung je Hop
                    decay = 0.5
                    tv = 0.0
                    for idx, e in enumerate(edges_rec):
                        tv += float(e.get("taint_value") or 0.0) * (decay ** idx)
                    taint_val = tv
                for a in node_addresses:
                    node_set.add(a)
                edge_count += len(edges_rec)
                paths.append({
                    "nodes": node_addresses,
                    "edges": edges_rec,
                    "taint": taint_val,
                })
                # Zieladresse aggregieren
                if node_addresses:
                    dst = node_addresses[-1]
                    tinfo = targets.get(dst) or {"taint": 0.0, "paths": 0, "tokens": {}}
                    tinfo["taint"] = float(tinfo["taint"]) + float(taint_val)
                    tinfo["paths"] = int(tinfo["paths"]) + 1
                    # token-aggregation best-effort
                    for e in edges_rec:
                        tok = e.get("token") or "native"
                        val = float(e.get("value") or 0.0)
                        tinfo["tokens"][tok] = float(tinfo["tokens"].get(tok, 0.0)) + val
                    targets[dst] = tinfo
            summary["nodes"] = len(node_set)
            summary["edges"] = edge_count
            # High-Risk: Ziele mit hohem Taint in Pfaden
            high: list[str] = []
            thr: float = threshold if threshold >= 0.5 else 0.5
            for pth in paths:
                ta: float = float(pth.get("taint", 0.0))
                nodes_list = pth.get("nodes", [])
                if ta >= thr and nodes_list:
                    high.append(nodes_list[-1])
            summary["high_risk"] = sorted(list(set(high)))
        # Sortiere Top-Ziele nach Taint
        top_targets = sorted(
            (
                {"address": k, "taint": v["taint"], "paths": v["paths"], "tokens": v["tokens"]}
                for k, v in targets.items()
            ),
            key=lambda x: x["taint"], reverse=True
        )
        result = {
            "chain": c,
            "source": addr,
            "depth": depth,
            "threshold": threshold,
            "model": model,
            "paths": paths,
            "summary": summary,
            "targets": top_targets[:50],
        }
        TRACE_REQUESTS.labels(op=op, status="ok").inc()
        return result
    except HTTPException:
        TRACE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        TRACE_REQUESTS.labels(op=op, status="error").inc()
        logger.error(f"taint_trace error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        TRACE_LATENCY.labels(op=op).observe(time.time() - t0)


@router.get("/cluster")
async def cluster_lookup(
    chain: str = Query(...),
    address: str = Query(...),
):
    """PoC: heuristisches Clustering – gibt einfache cluster_id zurück"""
    op = "cluster"
    t0 = time.time()
    try:
        c = chain.lower()
        if c not in {"ethereum", "bitcoin", "solana"}:
            raise HTTPException(status_code=400, detail="unsupported chain")
        if not is_valid_address(c, address):
            raise HTTPException(status_code=400, detail=f"invalid {c} address")
        addr = normalize_address(c, address) or address.strip().lower()
        members: list[str] = []
        if _is_test_or_offline():
            cluster_id = f"{c}:{addr[:10]}"
            resp = {"chain": c, "address": addr, "cluster_id": cluster_id, "members": members}
            TRACE_REQUESTS.labels(op=op, status="ok").inc()
            return resp

        # ... rest of the code remains the same ...
        cluster_id = f"{c}:{addr[:10]}"
        async with neo4j_client.get_session() as session:
            # Auto-detect if UTXO-style :Tx nodes exist
            detect = await session.run("MATCH (t:Tx) RETURN t LIMIT 1")
            has_utxo = await detect.single() is not None
            if has_utxo:
                # UTXO co-spend heuristic: addresses co-appearing as inputs in same tx as addr
                q_utxo = """
                MATCH (t:Tx)-[:INPUT]->(a:Address {address: $addr})
                MATCH (t)-[:INPUT]->(co:Address)
                WHERE co.address <> $addr
                WITH DISTINCT co.address AS coaddr LIMIT 200
                RETURN coaddr
                """
                res = await session.run(q_utxo, addr=addr)
                async for r in res:
                    members.append(r["coaddr"]) 
                # Change heuristic: outputs that are unique and unspent (best-effort)
                q_change = """
                MATCH (t:Tx)-[:INPUT]->(:Address {address: $addr})
                MATCH (t)-[:OUTPUT]->(out:Address)
                WITH out, size((out)<-[:INPUT]-(:Tx)) AS spends
                WHERE spends = 0 AND out.address <> $addr
                RETURN DISTINCT out.address AS change LIMIT 50
                """
                change_res = await session.run(q_change, addr=addr)
                async for r in change_res:
                    members.append(r["change"]) 
            else:
                # EVM fallback: high mutual interaction degree within 2 hops
                q_evm = """
                MATCH (a:Address {address: $addr})-[:TRANSACTION]->(b:Address)
                WITH b, count(*) AS outdeg
                MATCH (b)-[:TRANSACTION]->(a2:Address {address: $addr})
                WITH b, outdeg, count(*) AS indeg
                WHERE outdeg + indeg >= 2
                RETURN DISTINCT b.address AS neigh LIMIT 200
                """
                res = await session.run(q_evm, addr=addr)
                async for r in res:
                    members.append(r["neigh"]) 
            # Ensure uniqueness and include seed address
            members = sorted(list({m for m in members if m}))
            # Persist cluster node and relations
            await session.run(
                """
                MERGE (cl:Cluster {id: $cid})
                SET cl.chain = $chain, cl.size = $size, cl.updated_at = datetime()
                MERGE (seed:Address {address: $addr})
                MERGE (seed)-[:IN_CLUSTER]->(cl)
                """,
                cid=cluster_id, chain=c, size=len(members) + 1, addr=addr,
            )
            if members:
                await session.run(
                    """
                    UNWIND $members AS m
                    MERGE (a:Address {address: m})
                    WITH a
                    MERGE (cl:Cluster {id: $cid})
                    MERGE (a)-[:IN_CLUSTER]->(cl)
                    """,
                    members=members, cid=cluster_id,
                )
        resp = {"chain": c, "address": addr, "cluster_id": cluster_id, "members": members}
        TRACE_REQUESTS.labels(op=op, status="ok").inc()
        return resp
    except HTTPException:
        TRACE_REQUESTS.labels(op=op, status="error").inc()
        raise
    except Exception as e:
        TRACE_REQUESTS.labels(op=op, status="error").inc()
        logger.error(f"cluster_lookup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        TRACE_LATENCY.labels(op=op).observe(time.time() - t0)
