"""
SAR/STR Compliance API
======================

Endpoints zur Generierung und zum Export von SAR/STR-Reports basierend auf Fällen.
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from app.auth.dependencies import get_current_user_strict

# Optionaler Import des Case-Services (in TEST_MODE nicht zwingend vorhanden)
try:
    from app.services.case_service import case_service  # type: ignore
except Exception:
    case_service = None  # type: ignore

# SAR/STR Generator
from app.compliance.sar_str_generator import sar_generator, SARReport

router = APIRouter(tags=["SAR/STR"]) 


class GenerateSARRequest(BaseModel):
    case_id: str = Field(..., description="Case-ID für die Report-Generierung")
    format: str = Field("fincen", pattern="^(fincen|eu|uk|canada|singapore|australia|json)$")


class GenerateSARResponse(BaseModel):
    success: bool
    report_id: Optional[str] = None
    report_preview: Optional[Dict[str, Any]] = None
    exported: Optional[str] = None


async def _load_case(case_id: str) -> Dict[str, Any]:
    """Lädt Falldaten für die Report-Generierung."""
    if case_service is None:
        # Minimaler Mock für TEST_MODE
        return {
            "case_id": case_id,
            "subject_name": "Unknown",
            "addresses": [],
            "risk_score": 0.0,
            "total_amount_usd": 0.0,
            "risk_factors": [],
            "attachments": [],
        }
    data = case_service.get_case(case_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    # CaseService liefert serialisierte Struktur bereits passend
    return data


@router.post("/sar/from-case/{case_id}", response_model=GenerateSARResponse)
async def generate_sar_from_case(
    case_id: str,
    format: str = Query("fincen", pattern="^(fincen|eu|uk|canada|singapore|australia|json)$"),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Generiert einen SAR/STR-Report aus einem bestehenden Fall und exportiert ihn im gewünschten Format.

    Formate:
    - fincen: FinCEN SAR XML (als JSON-String zurückgegeben)
    - eu: EU STR (JSON-Struktur)
    - json: Rohdaten des Reports
    """
    # Falldaten laden
    case_data = await _load_case(case_id)

    # Narrativ und Report erzeugen
    report: SARReport = await sar_generator.generate_from_case(case_id, case_data)

    # Export in gewünschtes Format
    exported = await sar_generator.export_report(report, format=format)

    # Für Preview zusätzlich die JSON-Struktur zurückgeben (nicht bei sehr großen Reports)
    preview = {
        "report_id": report.report_id,
        "jurisdiction": report.jurisdiction,
        "report_type": report.report_type,
        "subject_name": report.subject_name,
        "amount_usd": report.amount_usd,
        "transaction_date": report.transaction_date,
        "risk_score": report.risk_score,
    }

    return GenerateSARResponse(
        success=True,
        report_id=report.report_id,
        report_preview=preview,
        exported=exported,
    )


class SubmitSARRequest(BaseModel):
    case_id: str
    format: str = Field("fincen", pattern="^(fincen|eu|uk|canada|singapore|australia|json)$")
    destination: str = Field("regulator", description="Zielsystem: regulator|internal|file")


@router.post("/sar/submit", response_model=Dict[str, Any])
async def submit_sar(
    payload: SubmitSARRequest,
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Simuliert das Einreichen eines SAR/STR-Reports (E-Filing Stub).
    In Produktion würde hier eine sichere Übertragung (API/SFTP) erfolgen.
    """
    case_data = await _load_case(payload.case_id)
    report = await sar_generator.generate_from_case(payload.case_id, case_data)
    exported = await sar_generator.export_report(report, format=payload.format)

    # Stub: Audit-Log/Tracking könnte hier geschrieben werden
    submission_id = f"SUB-{report.report_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    return {
        "success": True,
        "submission_id": submission_id,
        "report_id": report.report_id,
        "destination": payload.destination,
        "format": payload.format,
        "bytes": len(exported.encode("utf-8")),
    }
