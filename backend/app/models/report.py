"""
Report Management Models
For generating and managing investigation reports
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List


class ReportType(str, Enum):
    """Report type enumeration"""
    INVESTIGATION = "investigation"
    COMPLIANCE = "compliance"
    RISK_ASSESSMENT = "risk_assessment"
    TRANSACTION_ANALYSIS = "transaction_analysis"
    ADDRESS_PROFILE = "address_profile"
    SANCTIONS_SCREENING = "sanctions_screening"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    """Report status enumeration"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ReportFormat(str, Enum):
    """Report format enumeration"""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class Report(BaseModel):
    """Report model for investigation reports"""
    id: str = Field(default_factory=lambda: f"report_{datetime.utcnow().timestamp()}")
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)

    # Report metadata
    report_type: ReportType = ReportType.INVESTIGATION
    status: ReportStatus = ReportStatus.DRAFT
    format: ReportFormat = ReportFormat.PDF

    # Content
    content: Dict[str, Any] = Field(default_factory=dict)  # Structured report content
    sections: List[Dict[str, Any]] = Field(default_factory=list)  # Report sections

    # File information (for generated reports)
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None

    # Ownership and access
    created_by: str  # User ID
    assigned_to: Optional[str] = None  # User ID for review/approval
    approved_by: Optional[str] = None  # User ID

    # Related entities
    related_cases: List[str] = Field(default_factory=list)  # Case IDs
    related_alerts: List[str] = Field(default_factory=list)  # Alert IDs
    related_addresses: List[str] = Field(default_factory=list)
    related_transactions: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    confidentiality_level: str = Field("internal", pattern="^(public|internal|confidential|restricted)$")
    version: int = 1

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class ReportTemplate(BaseModel):
    """Report template model"""
    id: str = Field(default_factory=lambda: f"template_{datetime.utcnow().timestamp()}")
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)

    # Template configuration
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF

    # Template content
    structure: Dict[str, Any] = Field(default_factory=dict)  # Template structure
    default_sections: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    created_by: str  # User ID
    is_public: bool = False  # Public templates can be used by all users
    usage_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class ReportQuery(BaseModel):
    """Query parameters for reports"""
    report_type: Optional[ReportType] = None
    status: Optional[ReportStatus] = None
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None
    related_case: Optional[str] = None
    tags: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


# In-Memory Storage (replace with PostgreSQL in production)
reports: Dict[str, Report] = {}
report_templates: Dict[str, ReportTemplate] = {}


def create_report(
    title: str,
    description: str,
    report_type: ReportType,
    created_by: str,
    content: Optional[Dict[str, Any]] = None,
    related_cases: Optional[List[str]] = None,
    related_alerts: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    template_id: Optional[str] = None
) -> Report:
    """Create a new report"""
    report = Report(
        title=title,
        description=description,
        report_type=report_type,
        created_by=created_by,
        content=content or {},
        related_cases=related_cases or [],
        related_alerts=related_alerts or [],
        tags=tags or []
    )

    reports[report.id] = report

    # Update template usage if template was used
    if template_id and template_id in report_templates:
        report_templates[template_id].usage_count += 1

    return report


def get_report(report_id: str) -> Optional[Report]:
    """Get report by ID"""
    return reports.get(report_id)


def update_report_status(
    report_id: str,
    new_status: ReportStatus,
    updated_by: str,
    note: Optional[str] = None
) -> Optional[Report]:
    """Update report status"""
    report = reports.get(report_id)
    if not report:
        return None

    old_status = report.status
    report.status = new_status
    report.updated_at = datetime.utcnow()

    # Set specific timestamps based on status
    if new_status == ReportStatus.APPROVED and old_status != ReportStatus.APPROVED:
        report.approved_at = datetime.utcnow()
        report.approved_by = updated_by

    elif new_status == ReportStatus.PUBLISHED and old_status != ReportStatus.PUBLISHED:
        report.published_at = datetime.utcnow()

    # Log status change (would be done in API layer)
    # log_report_activity(report_id, "status_updated", f"Status changed from {old_status.value} to {new_status.value}", updated_by)

    return report


def query_reports(query: ReportQuery) -> List[Report]:
    """Query reports with filters"""
    results = list(reports.values())

    if query.report_type:
        results = [r for r in results if r.report_type == query.report_type]

    if query.status:
        results = [r for r in results if r.status == query.status]

    if query.created_by:
        results = [r for r in results if r.created_by == query.created_by]

    if query.assigned_to:
        results = [r for r in results if r.assigned_to == query.assigned_to]

    if query.related_case:
        results = [r for r in results if query.related_case in r.related_cases]

    if query.tags:
        results = [r for r in results if any(tag in r.tags for tag in query.tags)]

    if query.start_date:
        results = [r for r in results if r.created_at >= query.start_date]

    if query.end_date:
        results = [r for r in results if r.created_at <= query.end_date]

    # Sort by creation date descending
    results.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    return results[query.offset : query.offset + query.limit]


def create_template(
    name: str,
    description: str,
    report_type: ReportType,
    created_by: str,
    structure: Optional[Dict[str, Any]] = None,
    default_sections: Optional[List[Dict[str, Any]]] = None,
    is_public: bool = False
) -> ReportTemplate:
    """Create a new report template"""
    template = ReportTemplate(
        name=name,
        description=description,
        report_type=report_type,
        created_by=created_by,
        structure=structure or {},
        default_sections=default_sections or [],
        is_public=is_public
    )

    report_templates[template.id] = template
    return template


def get_template(template_id: str) -> Optional[ReportTemplate]:
    """Get template by ID"""
    return report_templates.get(template_id)


def get_public_templates(report_type: Optional[ReportType] = None) -> List[ReportTemplate]:
    """Get all public templates"""
    templates = [t for t in report_templates.values() if t.is_public]

    if report_type:
        templates = [t for t in templates if t.report_type == report_type]

    return sorted(templates, key=lambda x: x.usage_count, reverse=True)


def generate_report_from_template(
    template_id: str,
    title: str,
    description: str,
    created_by: str,
    custom_content: Optional[Dict[str, Any]] = None
) -> Optional[Report]:
    """Generate a report from a template"""
    template = report_templates.get(template_id)
    if not template:
        return None

    # Merge template content with custom content
    content = template.structure.copy()
    if custom_content:
        content.update(custom_content)

    report = Report(
        title=title,
        description=description,
        report_type=template.report_type,
        created_by=created_by,
        content=content,
        sections=template.default_sections.copy()
    )

    reports[report.id] = report
    return report
