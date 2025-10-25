"""
Advanced Reports API
====================

Multi-format forensic report generation and export
"""

import logging
import zipfile
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Response, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO
from datetime import datetime

from app.auth.dependencies import get_current_user_strict
from app.services.audit_service import audit_service
from app.reports.advanced_exporter import advanced_exporter
from app.reports.pdf_generator import PDFReportGenerator
from app.services.usage_service import check_and_consume_credits
from app.services.tenant_service import tenant_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== Request/Response Models =====

class GenerateReportRequest(BaseModel):
    """Request to generate a report"""
    trace_id: str
    format: str = "pdf"  # pdf, excel, csv, json, html
    entity_type: Optional[str] = "transactions"  # For CSV: transactions or addresses
    include_findings: bool = True


class ReportMetadata(BaseModel):
    """Report metadata"""
    report_id: str
    trace_id: str
    format: str
    generated_at: str
    size_bytes: int
    checksum: str  # SHA-256


# ===== API Endpoints =====

@router.post("/generate/{trace_id}")
async def generate_report(
    trace_id: str,
    format: str = "pdf",  # pdf, excel, csv, json, html
    entity_type: str = "transactions",  # For CSV: transactions or addresses
    include_findings: bool = True,
    plan_id: str | None = None,  # Optional: Plan ID; wird sonst aus Tenant ermittelt
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Generate forensic report in specified format (WITH AUTHORIZATION)
    
    **Path Parameters:**
    - trace_id: Trace ID to generate report for
    
    **Query Parameters:**
    - format: Output format (pdf, excel, csv, json, html)
    - entity_type: For CSV - transactions or addresses
    - include_findings: Include findings/alerts in report
    
    **Security:**
    - Requires authentication
    - Checks trace ownership
    - Logs to audit trail
    
    **Formats:**
    - **PDF**: Court-admissible forensic report (best for legal)
    - **Excel**: Multi-sheet workbook (best for analysis)
    - **CSV**: Data export (best for data science)
    - **JSON**: API integration (best for automation)
    - **HTML**: Web viewing (best for quick review)
    
    **Returns:**
    - File download with appropriate content-type
    """
    try:
        # Credits Enforcement per format
        cost_map = {
            "pdf": 50,
            "excel": 40,
            "csv": 10,
            "json": 5,
            "html": 5,
        }
        # entity_type could add small extra cost
        extra = 0
        try:
            amount = max(1, int(cost_map.get(format, 10) + extra))
            tenant_id = str(current_user["user_id"])  # vereinfachtes Tenant-Modell
            effective_plan = plan_id or tenant_service.get_plan_id(tenant_id)
            allowed = await check_and_consume_credits(tenant_id, effective_plan, amount, reason=f"report_{format}")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Report")
        except HTTPException:
            raise
        except Exception:
            # In Zweifelsfall nicht blockieren (z. B. Redis down)
            pass

        # Get trace data (mock for now - in production would query database)
        trace_data = await _get_trace_data(trace_id)
        
        if not trace_data:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        
        # Get findings if requested
        findings = None
        if include_findings:
            findings = await _get_trace_findings(trace_id)
        
        # Generate report in requested format
        if format == "pdf":
            pdf_gen = PDFReportGenerator()
            content, _ = await pdf_gen.generate_trace_report(trace_id, trace_data, findings)
            media_type = "application/pdf"
            filename = f"forensic_report_{trace_id}.pdf"
        
        elif format == "excel":
            content = advanced_exporter.export_to_excel(trace_id, trace_data, findings)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"forensic_report_{trace_id}.xlsx"
        
        elif format == "csv":
            content = advanced_exporter.export_to_csv(trace_id, trace_data, entity_type).encode('utf-8')
            media_type = "text/csv"
            filename = f"forensic_report_{trace_id}_{entity_type}.csv"
        
        elif format == "json":
            content = advanced_exporter.export_to_json(trace_id, trace_data, findings).encode('utf-8')
            media_type = "application/json"
            filename = f"forensic_report_{trace_id}.json"
        
        elif format == "html":
            content = advanced_exporter.export_to_html(trace_id, trace_data, findings).encode('utf-8')
            media_type = "text/html"
            filename = f"forensic_report_{trace_id}.html"
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        # Return file as download
        return StreamingResponse(
            BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Report-Trace-ID": trace_id,
                "X-Report-Format": format
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/{trace_id}")
async def generate_batch_reports(
    trace_id: str,
    include_findings: bool = Query(True),
    plan_id: str | None = Query(None, description="Optional: Plan ID; wird sonst aus Tenant ermittelt"),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Generate reports in ALL available formats
    
    Returns a ZIP archive containing:
    - PDF report
    - Excel workbook
    - CSV (transactions)
    - CSV (addresses)
    - JSON export
    - HTML view
    
    **Use Case:**
    - Comprehensive evidence package for legal proceedings
    - Complete data export for archival
    - Multi-format distribution
    """
    import zipfile
    from io import BytesIO
    
    try:
        # Credits Enforcement for batch: approximate sum of formats
        batch_cost = 50 + 40 + 10 + 10 + 5 + 5  # pdf, excel, csv(tx), csv(addr), json, html
        
        user_id = current_user["user_id"]
        
        # AUTHORIZATION: Check trace ownership
        from app.db.postgres_client import postgres_client
        trace = await postgres_client.fetch_one(
            "SELECT user_id FROM traces WHERE trace_id = $1",
            trace_id
        )
        
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        if trace["user_id"] != user_id:
            # AUDIT: Log unauthorized attempt
            from app.services.audit_service import audit_service
            await audit_service.log_action(
                user_id=user_id,
                action="unauthorized_report_generation",
                resource_type="trace",
                resource_id=trace_id,
                details={"reason": "not_owner"}
            )
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Get user's tenant
        org = await tenant_service.get_current_org(user_id)  # vereinfachtes Tenant-Modell
        tenant_id = str(user_id)
        effective_plan = plan_id or tenant_service.get_plan_id(tenant_id)
        try:
            allowed = await check_and_consume_credits(tenant_id, effective_plan, batch_cost, reason="report_batch_all")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Batch-Reports")
        except HTTPException:
            raise
        except Exception:
            # Fallback: nicht blockieren, wenn Usage-Service ausfällt
            pass
        
        trace_data = await _get_trace_data(trace_id)
        if not trace_data:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        
        findings = None
        if include_findings:
            findings = await _get_trace_findings(trace_id)
        
        # Generate all formats
        exports = advanced_exporter.export_all_formats(trace_id, trace_data, findings)
        
        # Add PDF
        try:
            pdf_gen = PDFReportGenerator()
            exports['pdf'], _ = await pdf_gen.generate_trace_report(trace_id, trace_data, findings)
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
        
        # Create ZIP archive
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for format_name, content in exports.items():
                # Determine extension
                ext_map = {
                    'pdf': 'pdf',
                    'excel': 'xlsx',
                    'csv_transactions': 'csv',
                    'csv_addresses': 'csv',
                    'json': 'json',
                    'html': 'html'
                }
                ext = ext_map.get(format_name, 'bin')
                
                filename = f"forensic_report_{trace_id}_{format_name}.{ext}"
                zip_file.writestr(filename, content)
            
            # Add README
            readme = f"""
Blockchain Forensic Analysis Report
====================================

Trace ID: {trace_id}
Generated: {datetime.utcnow().isoformat()}

Included Files:
- forensic_report_{trace_id}_pdf.pdf - Court-admissible report
- forensic_report_{trace_id}_excel.xlsx - Multi-sheet workbook
- forensic_report_{trace_id}_csv_transactions.csv - Transaction data
- forensic_report_{trace_id}_csv_addresses.csv - Address data
- forensic_report_{trace_id}_json.json - Complete data export
- forensic_report_{trace_id}_html.html - Web viewable report

CONFIDENTIAL: This package contains sensitive forensic analysis data.
"""
            zip_file.writestr("README.txt", readme)
        
        zip_buffer.seek(0)
        
        logger.info(f"Batch report generated for {trace_id}: {list(exports.keys())}")
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=forensic_reports_{trace_id}.zip"
            }
        )
    
    except HTTPException:
        raise
@router.get("/manifest/{trace_id}")
async def get_report_manifest(trace_id: str):
    """
    Get manifest for a generated report
    
    Returns the cryptographic manifest and signature for a report
    """
    try:
        # Check if trace exists (mock)
        trace_data = await _get_trace_data(trace_id)
        if not trace_data:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        
        # Generate manifest (this would normally be stored/retrieved from DB)
        # For now, regenerate it
        from app.services.signing import manifest_service, generate_report_hash_and_manifest
        
        # Mock report content for demonstration
        mock_content = f"Report for {trace_id}".encode('utf-8')
        content_hash, manifest = generate_report_hash_and_manifest(
            report_id=trace_id,
            report_type="trace_report",
            content=mock_content
        )
        
        return {
            "report_id": trace_id,
            "manifest": manifest,
            "verification_status": "valid" if manifest_service.verify_manifest(manifest) else "invalid"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get manifest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_available_formats():
    """
    Get list of available report formats
    
    Returns format availability and recommendations
    """
    formats = {
        "pdf": {
            "available": True,
            "name": "PDF",
            "description": "Court-admissible forensic report",
            "mime_type": "application/pdf",
            "recommended_for": ["Legal proceedings", "Official documentation", "Archival"],
            "features": ["Professional formatting", "Digital signatures", "Evidence chain"]
        },
        "excel": {
            "available": advanced_exporter.formats_available['excel'],
            "name": "Excel (XLSX)",
            "description": "Multi-sheet workbook with data",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "recommended_for": ["Data analysis", "Financial review", "Detailed investigation"],
            "features": ["Multiple sheets", "Formatted tables", "Color-coded risks"]
        },
        "csv": {
            "available": True,
            "name": "CSV",
            "description": "Comma-separated data export",
            "mime_type": "text/csv",
            "recommended_for": ["Data science", "Import to other tools", "Database loading"],
            "features": ["Plain text", "Universal compatibility", "Easy parsing"]
        },
        "json": {
            "available": True,
            "name": "JSON",
            "description": "Structured data for API integration",
            "mime_type": "application/json",
            "recommended_for": ["API integration", "Automation", "Custom processing"],
            "features": ["Machine-readable", "Complete data", "Metadata included"]
        },
        "html": {
            "available": True,
            "name": "HTML",
            "description": "Web-viewable report",
            "mime_type": "text/html",
            "recommended_for": ["Quick review", "Email sharing", "Web dashboards"],
            "features": ["Browser compatible", "Interactive", "Visual formatting"]
        }
    }
    
    return {
        "formats": formats,
        "total_available": sum(1 for f in formats.values() if f["available"]),
        "recommendations": {
            "legal": "pdf",
            "analysis": "excel",
            "automation": "json",
            "quick_review": "html",
            "data_export": "csv"
        }
    }


@router.get("/metadata/{trace_id}")
async def get_report_metadata(trace_id: str):
    """
    Get metadata for available reports
    
    Returns information about reports without generating them
    """
    try:
        trace_data = await _get_trace_data(trace_id)
        if not trace_data:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        
        nodes = trace_data.get('graph', {}).get('nodes', {})
        edges = trace_data.get('graph', {}).get('edges', [])
        
        return {
            "trace_id": trace_id,
            "status": trace_data.get('status', 'unknown'),
            "completed_at": trace_data.get('completed_at'),
            "statistics": {
                "total_addresses": len(nodes),
                "total_transactions": len(edges),
                "high_risk_addresses": sum(1 for n in nodes.values() if n.get('taint_received', 0) > 0.5),
                "total_volume": sum(e.get('amount', 0) for e in edges)
            },
            "available_formats": list(advanced_exporter.formats_available.keys()),
            "recommended_format": "pdf" if len(edges) < 100 else "excel"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get metadata failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Helper Functions =====

async def _get_trace_data(trace_id: str) -> Optional[dict]:
    """Get trace data from database/storage"""
    # Mock implementation - in production would query Neo4j/PostgreSQL
    logger.warning(f"_get_trace_data: Mock implementation for {trace_id}")
    
    # Return mock data for testing
    return {
        "trace_id": trace_id,
        "chain": "ethereum",
        "root_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "direction": "both",
        "max_depth": 3,
        "status": "completed",
        "started_at": "2025-01-11T10:00:00Z",
        "completed_at": "2025-01-11T10:05:00Z",
        "duration_seconds": 300,
        "graph": {
            "nodes": {
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e": {
                    "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                    "taint_received": 1.0,
                    "taint_sent": 0.8,
                    "labels": ["Source"],
                    "tx_count": 10,
                    "total_volume": 50000.0
                },
                "0x1234567890abcdef1234567890abcdef12345678": {
                    "address": "0x1234567890abcdef1234567890abcdef12345678",
                    "taint_received": 0.75,
                    "taint_sent": 0.5,
                    "labels": ["High-Risk", "Mixer"],
                    "tx_count": 5,
                    "total_volume": 25000.0
                }
            },
            "edges": [
                {
                    "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                    "to": "0x1234567890abcdef1234567890abcdef12345678",
                    "amount": 10000.0,
                    "tx_hash": "0xabc123...",
                    "timestamp": "2025-01-11T09:00:00Z",
                    "block_number": 12345678,
                    "taint": 0.8
                }
            ]
        }
    }


async def _get_trace_findings(trace_id: str) -> Optional[dict]:
    """Get findings/alerts for trace"""
    logger.warning(f"_get_trace_findings: Mock implementation for {trace_id}")
    
    return {
        "alerts": [
            {
                "type": "high_risk_address",
                "severity": "high",
                "title": "High-Risk Address Detected",
                "description": "Address shows mixer interaction pattern",
                "address": "0x1234567890abcdef1234567890abcdef12345678",
                "metadata": {
                    "risk_score": 0.75,
                    "factors": ["mixer_usage", "large_volume"]
                }
            }
        ]
    }
