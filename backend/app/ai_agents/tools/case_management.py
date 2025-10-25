"""
Case Management Tools for AI Agent.
Enables agent to create, manage, and export investigation cases.
"""

import logging
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

logger = logging.getLogger(__name__)


# Input Schemas
class CreateCaseInput(BaseModel):
    """Input for create_case tool"""
    title: str = Field(..., description="Case title")
    description: str = Field(..., description="Case description")
    addresses: List[str] = Field(..., description="Related blockchain addresses")
    priority: str = Field(default="medium", description="Priority: low, medium, high, critical")
    assigned_to: Optional[str] = Field(None, description="User ID to assign to")


class AddEvidenceInput(BaseModel):
    """Input for add_evidence tool"""
    case_id: str = Field(..., description="Case ID to add evidence to")
    evidence_type: str = Field(..., description="Type: transaction, address, document, screenshot")
    data: Dict[str, Any] = Field(..., description="Evidence data")
    notes: Optional[str] = Field(None, description="Additional notes")


class ListCasesInput(BaseModel):
    """Input for list_cases tool"""
    status: Optional[str] = Field(None, description="Filter by status: open, in_progress, review, closed")
    priority: Optional[str] = Field(None, description="Filter by priority: low, medium, high, critical")
    limit: int = Field(default=10, description="Maximum number of cases to return")


class UpdateCaseStatusInput(BaseModel):
    """Input for update_case_status tool"""
    case_id: str = Field(..., description="Case ID to update")
    status: str = Field(..., description="New status: open, in_progress, review, closed")
    notes: Optional[str] = Field(None, description="Status change notes")


class ExportCaseInput(BaseModel):
    """Input for export_case tool"""
    case_id: str = Field(..., description="Case ID to export")
    format: str = Field(default="pdf", description="Export format: pdf, excel, json")


# Tools Implementation
@tool("create_case", args_schema=CreateCaseInput)
async def create_case_tool(
    title: str,
    description: str,
    addresses: List[str],
    priority: str = "medium",
    assigned_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new investigation case.
    Use this when user wants to organize an investigation or track findings.
    
    Examples:
    - "Create a case for investigating address 0xABC..."
    - "Start a new case titled 'Mixer Investigation'"
    """
    try:
        from app.services.case_service import case_service
        
        case = await case_service.create_case(
            title=title,
            description=description,
            addresses=addresses,
            priority=priority,
            assigned_to=assigned_to
        )
        
        return {
            "success": True,
            "case_id": case.get("id"),
            "title": case.get("title"),
            "created_at": case.get("created_at"),
            "message": f"Case '{title}' created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating case: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create case"
        }


@tool("add_evidence", args_schema=AddEvidenceInput)
async def add_evidence_tool(
    case_id: str,
    evidence_type: str,
    data: Dict[str, Any],
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add evidence to an investigation case.
    Use this to document findings, transactions, or other relevant data.
    
    Evidence types:
    - transaction: Blockchain transaction details
    - address: Address analysis results
    - document: External documents or reports
    - screenshot: Screenshots or images
    """
    try:
        from app.services.case_service import case_service
        
        evidence = await case_service.add_evidence(
            case_id=case_id,
            evidence_type=evidence_type,
            data=data,
            notes=notes
        )
        
        return {
            "success": True,
            "evidence_id": evidence.get("id"),
            "case_id": case_id,
            "type": evidence_type,
            "message": f"Evidence added to case {case_id}"
        }
    except Exception as e:
        logger.error(f"Error adding evidence: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to add evidence"
        }


@tool("list_cases", args_schema=ListCasesInput)
async def list_cases_tool(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    List investigation cases with optional filters.
    Use this to see all ongoing investigations or find specific cases.
    
    Examples:
    - "Show me all open cases"
    - "List high priority cases"
    - "What cases are in progress?"
    """
    try:
        from app.services.case_service import case_service
        
        cases = await case_service.list_cases(
            status=status,
            priority=priority,
            limit=limit
        )
        
        return {
            "success": True,
            "total": len(cases),
            "cases": cases,
            "filters": {
                "status": status,
                "priority": priority
            }
        }
    except Exception as e:
        logger.error(f"Error listing cases: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list cases"
        }


@tool("update_case_status", args_schema=UpdateCaseStatusInput)
async def update_case_status_tool(
    case_id: str,
    status: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the status of an investigation case.
    
    Valid statuses:
    - open: Case is created but not started
    - in_progress: Investigation is ongoing
    - review: Investigation complete, under review
    - closed: Case is finished
    
    Examples:
    - "Mark case #123 as in progress"
    - "Close case #456"
    """
    try:
        from app.services.case_service import case_service
        
        case = await case_service.update_status(
            case_id=case_id,
            status=status,
            notes=notes
        )
        
        return {
            "success": True,
            "case_id": case_id,
            "old_status": case.get("previous_status"),
            "new_status": status,
            "message": f"Case status updated to {status}"
        }
    except Exception as e:
        logger.error(f"Error updating case status: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to update case status"
        }


@tool("export_case", args_schema=ExportCaseInput)
async def export_case_tool(
    case_id: str,
    format: str = "pdf"
) -> Dict[str, Any]:
    """
    Export a complete case with all evidence to file.
    Use this to generate court-admissible reports.
    
    Supported formats:
    - pdf: Professional PDF report
    - excel: Spreadsheet with all data
    - json: Machine-readable format
    
    Examples:
    - "Export case #123 as PDF"
    - "Generate report for case #456"
    """
    try:
        from app.services.case_service import case_service
        
        file_path = await case_service.export_case(case_id, format)
        
        return {
            "success": True,
            "case_id": case_id,
            "format": format,
            "file_path": file_path,
            "message": f"Case exported as {format}"
        }
    except Exception as e:
        logger.error(f"Error exporting case: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to export case"
        }


# Export all case management tools
CASE_TOOLS = [
    create_case_tool,
    add_evidence_tool,
    list_cases_tool,
    update_case_status_tool,
    export_case_tool,
]

logger.info(f"✅ Case Management Tools loaded: {len(CASE_TOOLS)} tools")
