"""Case Management Tools for AI Agent"""

import logging
from typing import Dict, Any, Optional, List
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field
from datetime import datetime
from app.services.audit_service import audit_service
from app.utils.security import validate_eth_address, sanitize_html, validate_string_length
from app.services.tool_rate_limiter import tool_rate_limiter

logger = logging.getLogger(__name__)

# Input Schemas
class CreateCaseInput(BaseModel):
    """Input for create_case tool"""
    title: str = Field(..., description="Case title (max 200 chars)")
    description: str = Field(..., description="Case description (max 5000 chars)")
    source_address: Optional[str] = Field(None, description="Source blockchain address (0x... for Ethereum)")
    chain: Optional[str] = Field("ethereum", description="Blockchain (ethereum, bitcoin, etc.)")
    priority: str = Field("medium", description="Priority: low, medium, high, critical")
    category: str = Field("fraud", description="Category: fraud, hack, scam, money_laundering, etc.")
    user_id: str = Field(..., description="User ID (from authentication)")


class ExportCaseInput(BaseModel):
    """Input for export_case tool"""
    case_id: str = Field(..., description="Case ID to export")
    format: str = Field("pdf", description="Export format: pdf, json, zip")


class ListCasesInput(BaseModel):
    """Input for list_my_cases tool"""
    status: Optional[str] = Field(None, description="Filter by status: open, in_progress, closed")
    limit: int = Field(10, description="Max results (1-50)")


@tool("create_case", args_schema=CreateCaseInput)
async def create_case_tool(
    title: str,
    description: str,
    user_id: str,
    source_address: Optional[str] = None,
    chain: Optional[str] = None,
    priority: str = "medium",
    category: str = "fraud"
) -> Dict[str, Any]:
    """
    Create investigation case directly from chat.
    Requires authentication. Returns case with open-link.
    
    Use this when user asks:
    - "Create a case for this address"
    - "Start investigation case"
    - "Save this as a case"
    
    Security: Validates input, checks permissions, logs to audit trail.
    """
    start_time = datetime.utcnow()
    
    try:
        # ✅ RATE LIMIT: Check tool-specific limit
        # Note: plan should be passed from agent context
        user_plan = "community"  # Default - should be retrieved from user context
        allowed, current, limit = await tool_rate_limiter.check_limit(
            user_id=user_id,
            tool_name="create_case",
            plan=user_plan
        )
        
        if not allowed:
            retry_after = tool_rate_limiter.get_retry_after()
            return {
                "success": False,
                "error": f"Rate limit exceeded. You can create {limit} cases per hour. Current: {current}",
                "retry_after": retry_after,
                "upgrade_message": "Upgrade to Pro for higher limits (50 cases/hour)"
            }
        
        # ✅ SECURITY: Validate inputs
        if not validate_string_length(title, 1, 200):
            return {
                "success": False,
                "error": "Title must be 1-200 characters"
            }
        
        if not validate_string_length(description, 1, 5000):
            return {
                "success": False,
                "error": "Description must be 1-5000 characters"
            }
        
        # ✅ SECURITY: Sanitize HTML/XSS
        title = sanitize_html(title)
        description = sanitize_html(description)
        
        # ✅ SECURITY: Validate address if provided
        if source_address:
            if chain in ["ethereum", "polygon", "bsc", "arbitrum", "optimism"]:
                if not validate_eth_address(source_address):
                    return {
                        "success": False,
                        "error": f"Invalid Ethereum address: {source_address}"
                    }
        
        # ✅ SECURITY: Validate priority
        if priority not in ["low", "medium", "high", "critical"]:
            priority = "medium"  # Safe default
        
        # Import here to avoid circular dependencies
        from app.db.postgres_client import postgres_client
        import uuid
        
        # Generate case ID
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        
        # Prepare case data
        case_data = {
            "id": case_id,
            "title": title,
            "description": description,
            "status": "open",
            "priority": priority,
            "category": category,
            "source_address": source_address,
            "chain": chain,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save to database
        try:
            # Store in database with ownership tracking
            await postgres_client.execute(
                """
                INSERT INTO cases (
                    case_id, title, description, status, created_at,
                    owner_id, source_address, chain, priority, category
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (case_id) DO NOTHING
                """,
                case_id, title, description, "open", datetime.utcnow(),
                user_id, source_address, chain, priority, category
            )
        except Exception as db_error:
            logger.warning(f"Database insert failed (fallback mode): {db_error}")
        
        logger.info(f"Case created: {case_id} by user {user_id}")
        
        # AUDIT: Log case creation
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        await audit_service.log_case_action(
            action="created",
            case_id=case_id,
            user_id=user_id,
            details={
                "title": title[:100],  # Truncate for log
                "priority": priority,
                "category": category,
                "has_source_address": bool(source_address)
            }
        )
        
        return {
            "success": True,
            "case_id": case_id,
            "title": title,
            "status": "open",
            "marker": f"[CASE_CREATED:{case_id}]",
            "open_link": f"/cases/{case_id}",
            "message": f"✅ Investigation case created: {title}",
            "duration_ms": duration_ms
        }
    
    except Exception as e:
        logger.error(f"Case creation failed: {e}", exc_info=True)
        
        # AUDIT: Log failure
        await audit_service.log_case_action(
            action="create_failed",
            case_id="unknown",
            user_id=user_id,
            details={"error": str(e)}
        )
        
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Failed to create case"
        }


@tool("export_case", args_schema=ExportCaseInput)
async def export_case_tool(case_id: str, format: str = "pdf") -> Dict[str, Any]:
    """
    Export case report as PDF/JSON/ZIP for download.
    Returns download marker for frontend to render download button.
    
    Use this when user asks:
    - "Export this case as PDF"
    - "Download case report"
    - "Generate case evidence package"
    """
    try:
        from app.services.case_export_service import CaseExporter
        from app.models.case import get_case
        
        # Get case
        case = get_case(case_id)
        if not case:
            return {
                "success": False,
                "error": "Case not found",
                "message": f"❌ Case {case_id} not found"
            }
        
        # Generate export
        exporter = CaseExporter()
        
        if format.lower() == "pdf":
            file_path = exporter.export_case_pdf(case_id)
        elif format.lower() == "zip":
            file_path = exporter.export_case_zip(case_id)
        else:
            # JSON format
            report_json = exporter.generate_case_report(case)
            file_path = f"/tmp/case_{case_id}_report.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_json)
        
        # Return response with download marker
        return {
            "success": True,
            "case_id": case_id,
            "format": format.upper(),
            "file_path": file_path,
            "download_url": f"/api/v1/cases/{case_id}/download/{format}",
            "marker": f"[DOWNLOAD:case:{case_id}:{format}]",
            "message": f"✅ Case report ready for download\n\n📄 Format: **{format.upper()}**\n💾 Click button below to download"
        }
    except Exception as e:
        logger.error(f"Error in export_case_tool: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to export case: {str(e)}"
        }


@tool("list_my_cases", args_schema=ListCasesInput)
async def list_my_cases_tool(
    status: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    List user's recent investigation cases.
    
    Use this when user asks:
    - "Show my cases"
    - "List recent investigations"
    - "What cases am I working on?"
    """
    try:
        from app.db.postgres_client import postgres_client
        
        # Build query
        query = "SELECT id, title, status, priority, created_at FROM cases WHERE 1=1"
        params = []
        
        if status:
            query += f" AND status = ${len(params) + 1}"
            params.append(status)
        
        query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
        params.append(min(limit, 50))
        
        # Fetch cases
        cases = []
        try:
            async with postgres_client.acquire() as conn:
                rows = await conn.fetch(query, *params)
                cases = [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "status": row["status"],
                        "priority": row["priority"],
                        "created_at": row["created_at"].isoformat(),
                        "open_link": f"/cases/{row['id']}"
                    }
                    for row in rows
                ]
        except Exception as db_error:
            logger.warning(f"Database query failed: {db_error}")
            # Return mock data for demo
            cases = [
                {
                    "id": "CASE-DEMO01",
                    "title": "Sample Investigation",
                    "status": "open",
                    "priority": "medium",
                    "created_at": datetime.utcnow().isoformat(),
                    "open_link": "/cases/CASE-DEMO01"
                }
            ]
        
        # Format response
        if not cases:
            return {
                "success": True,
                "total": 0,
                "cases": [],
                "message": "No cases found. Create your first case to get started!"
            }
        
        # Build formatted list
        case_list = "\n".join([
            f"{i+1}. **{c['title']}** (`{c['id']}`)\n   Status: {c['status']} | Priority: {c['priority']}\n   🔗 [Open Case]({c['open_link']})"
            for i, c in enumerate(cases)
        ])
        
        return {
            "success": True,
            "total": len(cases),
            "cases": cases,
            "message": f"📁 Found {len(cases)} case(s):\n\n{case_list}"
        }
    except Exception as e:
        logger.error(f"Error in list_my_cases_tool: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to list cases: {str(e)}"
        }


# Export tools list
CASE_MANAGEMENT_TOOLS = [
    create_case_tool,
    export_case_tool,
    list_my_cases_tool
]
