"""
Audit Log Models
Tracks all user actions for compliance and security
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any


class AuditAction(str, Enum):
    """Types of auditable actions"""
    # Auth Actions
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGE = "password_change"
    
    # User Management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"
    ROLE_CHANGE = "role_change"
    
    # Trace Actions
    TRACE_CREATE = "trace_create"
    TRACE_VIEW = "trace_view"
    TRACE_EXPORT = "trace_export"
    TRACE_DELETE = "trace_delete"
    
    # Report Actions
    REPORT_GENERATE = "report_generate"
    REPORT_DOWNLOAD = "report_download"
    REPORT_SHARE = "report_share"
    
    # Data Actions
    DATA_INGEST = "data_ingest"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    
    # System Actions
    CONFIG_CHANGE = "config_change"
    SYSTEM_ACCESS = "system_access"


class AuditLogEntry(BaseModel):
    """Audit Log Entry Model"""
    id: str = Field(default_factory=lambda: f"audit_{datetime.utcnow().timestamp()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Who
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # What
    action: AuditAction
    resource_type: Optional[str] = None  # e.g., "trace", "user", "report"
    resource_id: Optional[str] = None
    
    # Details
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Context
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class AuditLogQuery(BaseModel):
    """Query parameters for audit logs"""
    user_id: Optional[str] = None
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success: Optional[bool] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


# In-Memory Storage (replace with TimescaleDB in production)
audit_logs: list[AuditLogEntry] = []


def log_audit_event(
    action: AuditAction,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    user_role: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLogEntry:
    """Log an audit event"""
    entry = AuditLogEntry(
        action=action,
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
        error_message=error_message,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    audit_logs.append(entry)
    return entry


def query_audit_logs(query: AuditLogQuery) -> list[AuditLogEntry]:
    """Query audit logs with filters"""
    results = audit_logs.copy()
    
    if query.user_id:
        results = [log for log in results if log.user_id == query.user_id]
    
    if query.action:
        results = [log for log in results if log.action == query.action]
    
    if query.resource_type:
        results = [log for log in results if log.resource_type == query.resource_type]
    
    if query.start_date:
        results = [log for log in results if log.timestamp >= query.start_date]
    
    if query.end_date:
        results = [log for log in results if log.timestamp <= query.end_date]
    
    if query.success is not None:
        results = [log for log in results if log.success == query.success]
    
    # Sort by timestamp descending
    results.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply pagination
    return results[query.offset : query.offset + query.limit]
