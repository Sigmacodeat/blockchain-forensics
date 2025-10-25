"""
Reporting Tools for AI Agent.
Generate forensic reports, executive summaries, and compliance documents.
"""

import logging
from typing import List, Optional, Dict, Any
from langchain.tools import tool
from pydantic.v1 import BaseModel, Field

logger = logging.getLogger(__name__)


# Input Schemas
class GenerateReportInput(BaseModel):
    """Input for generate_forensic_report tool"""
    trace_id: Optional[str] = Field(None, description="Trace ID to include in report")
    case_id: Optional[str] = Field(None, description="Case ID to generate report for")
    addresses: Optional[List[str]] = Field(None, description="Specific addresses to analyze")
    format: str = Field(default="pdf", description="Report format: pdf, markdown, json")
    include_sections: List[str] = Field(
        default=["summary", "methodology", "findings", "recommendations"],
        description="Sections to include in report"
    )


class ExecutiveSummaryInput(BaseModel):
    """Input for generate_executive_summary tool"""
    case_id: str = Field(..., description="Case ID to summarize")
    max_length: int = Field(default=500, description="Maximum length in words")


class ScheduleReportInput(BaseModel):
    """Input for schedule_report tool"""
    report_type: str = Field(..., description="Report type: daily, weekly, monthly")
    recipients: List[str] = Field(..., description="Email addresses to send report to")
    filters: Optional[Dict] = Field(None, description="Filters to apply to report data")


class EmailReportInput(BaseModel):
    """Input for email_report tool"""
    report_id: str = Field(..., description="Report ID to email")
    recipients: List[str] = Field(..., description="Email addresses")
    subject: Optional[str] = Field(None, description="Email subject line")
    message: Optional[str] = Field(None, description="Email body message")


# Tools Implementation
@tool("generate_forensic_report", args_schema=GenerateReportInput)
async def generate_forensic_report_tool(
    trace_id: Optional[str] = None,
    case_id: Optional[str] = None,
    addresses: Optional[List[str]] = None,
    format: str = "pdf",
    include_sections: List[str] = ["summary", "methodology", "findings", "recommendations"]
) -> Dict[str, Any]:
    """
    Generate a comprehensive forensic report for court proceedings.
    Includes chain of custody, evidence trail, and risk assessment.
    
    Report sections:
    - summary: Executive summary of findings
    - methodology: Investigation methods used
    - findings: Detailed analysis results
    - recommendations: Actionable next steps
    - evidence: Supporting evidence and data
    - timeline: Chronological event timeline
    
    Examples:
    - "Generate a forensic report for case #123"
    - "Create a PDF report for trace #abc456"
    """
    try:
        # Import service (will be created if doesn't exist)
        try:
            from app.services.forensic_report_service import report_service
        except ImportError:
            logger.warning("forensic_report_service not found, using fallback")
            return {
                "success": False,
                "error": "Report service not yet implemented",
                "message": "Feature coming soon - forensic_report_service.py needed"
            }
        
        report = await report_service.generate_report(
            trace_id=trace_id,
            case_id=case_id,
            addresses=addresses,
            format=format,
            include_sections=include_sections
        )
        
        return {
            "success": True,
            "report_id": report.get("id"),
            "format": format,
            "file_url": report.get("file_url"),
            "pages": report.get("pages", 0),
            "sections": include_sections,
            "message": f"Forensic report generated successfully ({format})"
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate forensic report"
        }


@tool("generate_executive_summary", args_schema=ExecutiveSummaryInput)
async def generate_executive_summary_tool(
    case_id: str,
    max_length: int = 500
) -> Dict[str, Any]:
    """
    Generate a concise executive summary for management.
    Non-technical language, focuses on key findings and risks.
    
    Examples:
    - "Create an executive summary for case #123"
    - "Summarize case #456 for management"
    """
    try:
        try:
            from app.services.forensic_report_service import report_service
        except ImportError:
            # Fallback: Simple summary
            return {
                "success": True,
                "case_id": case_id,
                "summary": f"Executive summary for case {case_id} (service not yet implemented)",
                "message": "Feature coming soon"
            }
        
        summary = await report_service.generate_executive_summary(
            case_id=case_id,
            max_length=max_length
        )
        
        return {
            "success": True,
            "case_id": case_id,
            "summary": summary,
            "word_count": len(summary.split()),
            "message": "Executive summary generated"
        }
    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate executive summary"
        }


@tool("schedule_report", args_schema=ScheduleReportInput)
async def schedule_report_tool(
    report_type: str,
    recipients: List[str],
    filters: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Schedule automated report generation and delivery.
    
    Report types:
    - daily: Generated every day at 9 AM
    - weekly: Generated every Monday
    - monthly: Generated on 1st of each month
    
    Examples:
    - "Schedule a weekly report to admin@company.com"
    - "Set up daily risk reports"
    """
    try:
        try:
            from app.services.forensic_report_service import report_service
        except ImportError:
            return {
                "success": False,
                "error": "Report service not yet implemented",
                "message": "Feature coming soon"
            }
        
        schedule = await report_service.schedule_report(
            report_type=report_type,
            recipients=recipients,
            filters=filters
        )
        
        return {
            "success": True,
            "schedule_id": schedule.get("id"),
            "report_type": report_type,
            "recipients": recipients,
            "next_run": schedule.get("next_run"),
            "message": f"{report_type.capitalize()} report scheduled successfully"
        }
    except Exception as e:
        logger.error(f"Error scheduling report: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to schedule report"
        }


@tool("email_report", args_schema=EmailReportInput)
async def email_report_tool(
    report_id: str,
    recipients: List[str],
    subject: Optional[str] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Email a generated report to recipients.
    
    Examples:
    - "Email report #abc123 to admin@company.com"
    - "Send the latest report to the team"
    """
    try:
        try:
            from app.services.forensic_report_service import report_service
        except ImportError:
            return {
                "success": False,
                "error": "Report service not yet implemented",
                "message": "Feature coming soon"
            }
        
        await report_service.email_report(
            report_id=report_id,
            recipients=recipients,
            subject=subject,
            message=message
        )
        
        return {
            "success": True,
            "report_id": report_id,
            "recipients": recipients,
            "message": f"Report emailed to {len(recipients)} recipient(s)"
        }
    except Exception as e:
        logger.error(f"Error emailing report: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to email report"
        }


@tool("generate_compliance_report")
async def generate_compliance_report_tool(
    start_date: str,
    end_date: str,
    regulations: List[str] = ["OFAC", "EU", "FATF"]
) -> Dict[str, Any]:
    """
    Generate compliance report for regulatory submission.
    Includes all sanctions screenings, alerts, and actions taken.
    
    Supported regulations:
    - OFAC: US Office of Foreign Assets Control
    - EU: European Union sanctions
    - FATF: Financial Action Task Force
    - UK: UK Treasury sanctions
    
    Examples:
    - "Generate OFAC compliance report for last month"
    - "Create regulatory report from Jan 1 to Dec 31"
    """
    try:
        try:
            from app.services.forensic_report_service import report_service
        except ImportError:
            return {
                "success": False,
                "error": "Report service not yet implemented",
                "message": "Feature coming soon"
            }
        
        report = await report_service.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            regulations=regulations
        )
        
        return {
            "success": True,
            "report_id": report.get("id"),
            "period": f"{start_date} to {end_date}",
            "regulations": regulations,
            "total_screenings": report.get("total_screenings"),
            "hits": report.get("hits"),
            "message": "Compliance report generated successfully"
        }
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate compliance report"
        }


# Export all reporting tools
REPORTING_TOOLS = [
    generate_forensic_report_tool,
    generate_executive_summary_tool,
    schedule_report_tool,
    email_report_tool,
    generate_compliance_report_tool,
]

logger.info(f"✅ Reporting Tools loaded: {len(REPORTING_TOOLS)} tools")
