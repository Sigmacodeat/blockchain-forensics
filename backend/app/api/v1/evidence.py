from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.services.evidence_vault import evidence_vault

router = APIRouter()


class EvidenceAppendRequest(BaseModel):
    event_type: str = Field(..., min_length=1)
    payload: Any
    meta: Optional[Dict[str, Any]] = None


@router.post("/append", status_code=status.HTTP_201_CREATED, tags=["Evidence"])
async def evidence_append(req: EvidenceAppendRequest):
    try:
        rec = await evidence_vault.append(req.event_type, req.payload, req.meta or {})
        return {"success": True, "record": rec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/head", tags=["Evidence"])
async def evidence_head():
    try:
        rec = await evidence_vault.head()
        return {"head": rec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify-integrity", tags=["Evidence"])
async def evidence_verify_integrity():
    """Verify the entire evidence chain integrity and signatures"""
    try:
        result = await evidence_vault.verify_chain_integrity()
        return {"verification": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integrity verification failed: {str(e)}")


@router.get("/chain-of-custody", tags=["Evidence"])
async def evidence_chain_of_custody(
    start_seq: Optional[int] = Query(None, description="Start sequence number"),
    end_seq: Optional[int] = Query(None, description="End sequence number")
):
    """Generate Chain-of-Custody Report for court admissibility"""
    try:
        report = await evidence_vault.generate_chain_of_custody_report(start_seq, end_seq)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain-of-Custody report generation failed: {str(e)}")


@router.get("/export/{format}", tags=["Evidence"])
async def evidence_export(
    format: str,
    start_seq: Optional[int] = Query(None, description="Start sequence number"),
    end_seq: Optional[int] = Query(None, description="End sequence number")
):
    """Export evidence chain in specified format"""
    if format not in ["json", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'pdf'")
    try:
        if format == "json":
            report = await evidence_vault.generate_chain_of_custody_report(start_seq, end_seq)
            return {"export": report}
        elif format == "pdf":
            # For PDF export, we'd need a PDF generation library like reportlab
            # For now, return JSON with note about PDF implementation
            report = await evidence_vault.generate_chain_of_custody_report(start_seq, end_seq)
            report["note"] = "PDF export requires additional PDF generation library (e.g., reportlab)"
            return {"export": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/record/by-seq/{seq}", tags=["Evidence"])
async def evidence_verify_record_by_seq(seq: int):
    try:
        result = await evidence_vault.verify_record_by_seq(seq)
        return {"verification": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Record verification failed: {str(e)}")


@router.get("/record/by-id/{record_id}", tags=["Evidence"])
async def evidence_verify_record_by_id(record_id: str):
    try:
        result = await evidence_vault.verify_record_by_id(record_id)
        return {"verification": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Record verification failed: {str(e)}")


@router.get("/anchor/{tx}/status", tags=["Evidence"])
async def evidence_anchor_status(tx: str):
    try:
        info = await evidence_vault.verify_anchor_status(tx)
        return {"anchor": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anchor status check failed: {str(e)}")


@router.post("/anchor/retry/{seq}", tags=["Evidence"])
async def evidence_retry_anchor(seq: int):
    try:
        info = await evidence_vault.retry_anchor_by_seq(seq)
        return {"result": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anchor retry failed: {str(e)}")
