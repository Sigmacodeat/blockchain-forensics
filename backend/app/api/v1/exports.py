from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import require_plan
from app.exports.bigquery_exporter import bigquery_exporter

router = APIRouter(prefix="/exports", tags=["Exports"]) 


class TransactionsExportRequest(BaseModel):
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Rows to export to BigQuery")
    table: Optional[str] = Field(None, description="Override table name (default: transactions)")


class TraceGraphExportRequest(BaseModel):
    trace: Dict[str, Any] = Field(default_factory=dict, description="Trace data with nodes/edges or graph field")


@router.get("/bigquery/status")
async def bigquery_status(_user: dict = Depends(require_plan("pro"))) -> Dict[str, Any]:
    """Status & Konfiguration für BigQuery-Export (Feature-Flag)."""
    try:
        return {
            "enabled": bool(bigquery_exporter.enabled),
            "project": getattr(bigquery_exporter, "project", None),
            "dataset": getattr(bigquery_exporter, "dataset", None),
            "location": getattr(bigquery_exporter, "location", None),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read BigQuery status: {str(e)}")


@router.post("/bigquery/transactions")
async def export_transactions(
    payload: TransactionsExportRequest,
    _user: dict = Depends(require_plan("business")),
) -> Dict[str, Any]:
    """Exportiert Transaktionszeilen nach BigQuery (optional, Feature-Flag)."""
    try:
        if not payload.rows:
            raise HTTPException(status_code=400, detail="rows must not be empty")
        res = bigquery_exporter.export_transactions(payload.rows, table_override=payload.table)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export transactions: {str(e)}")


@router.post("/bigquery/trace-graph")
async def export_trace_graph(
    payload: TraceGraphExportRequest,
    _user: dict = Depends(require_plan("business")),
) -> Dict[str, Any]:
    """Exportiert Trace-Graph (nodes/edges) nach BigQuery (optional, Feature-Flag)."""
    try:
        if not payload.trace:
            raise HTTPException(status_code=400, detail="trace must not be empty")
        res = bigquery_exporter.export_trace_graph(payload.trace)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export trace graph: {str(e)}")
