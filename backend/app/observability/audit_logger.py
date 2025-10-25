"""
Enhanced Audit Logging System
Logs all security-relevant events für Compliance & Forensics
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

# Strukturiertes Audit-Log
audit_logger = logging.getLogger("audit")


class AuditEventType(str, Enum):
    """Audit Event Types"""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    
    # Authorization
    PLAN_CHECK_SUCCESS = "plan_check_success"
    PLAN_CHECK_FAILED = "plan_check_failed"
    ADMIN_ACCESS = "admin_access"
    ADMIN_ACCESS_DENIED = "admin_access_denied"
    
    # Resource Access
    RESOURCE_ACCESS = "resource_access"
    RESOURCE_ACCESS_DENIED = "resource_access_denied"
    ORG_VIOLATION = "org_violation"
    
    # Data Changes
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PLAN_CHANGED = "plan_changed"
    
    # Trial Management
    TRIAL_STARTED = "trial_started"
    TRIAL_ENDED = "trial_ended"
    TRIAL_EXPIRED = "trial_expired"
    
    # Rate Limiting
    RATE_LIMIT_HIT = "rate_limit_hit"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


def log_audit_event(
    event_type: AuditEventType,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    action: Optional[str] = None,
    result: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Log structured audit event
    
    Args:
        event_type: Type of event (from AuditEventType enum)
        user_id: User ID if applicable
        email: User email if applicable
        resource_type: Type of resource accessed (e.g., "case", "trace")
        resource_id: ID of resource
        action: Action performed (e.g., "read", "write", "delete")
        result: "success" or "failure"
        metadata: Additional context data
        ip_address: Client IP
        user_agent: Client User-Agent
    
    Example:
        log_audit_event(
            event_type=AuditEventType.PLAN_CHECK_FAILED,
            user_id="user_123",
            email="user@example.com",
            resource_type="graph_analytics",
            action="communities/detect",
            result="failure",
            metadata={"required_plan": "pro", "user_plan": "community"}
        )
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type.value,
        "user_id": user_id,
        "email": email,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
        "result": result,
        "metadata": metadata or {},
        "ip_address": ip_address,
        "user_agent": user_agent
    }
    
    # Strukturiertes JSON-Log
    audit_logger.info(
        f"AUDIT: {event_type.value}",
        extra={"audit_event": event}
    )


def log_plan_check(
    user_id: str,
    email: Optional[str],
    plan: str,
    required_plan: str,
    feature: str,
    allowed: bool,
    ip_address: Optional[str] = None
) -> None:
    """
    Log Plan-Check Event
    
    Usage:
        log_plan_check(
            user_id="user_123",
            email="user@example.com",
            plan="community",
            required_plan="pro",
            feature="graph_analytics",
            allowed=False
        )
    """
    event_type = AuditEventType.PLAN_CHECK_SUCCESS if allowed else AuditEventType.PLAN_CHECK_FAILED
    
    log_audit_event(
        event_type=event_type,
        user_id=user_id,
        email=email,
        resource_type="plan_check",
        action=feature,
        result="success" if allowed else "failure",
        metadata={
            "user_plan": plan,
            "required_plan": required_plan,
            "allowed": allowed
        },
        ip_address=ip_address
    )


def log_org_access_violation(
    user_id: str,
    email: Optional[str],
    user_org_id: Optional[str],
    resource_org_id: str,
    resource_type: str,
    resource_id: str,
    ip_address: Optional[str] = None
) -> None:
    """
    Log Cross-Tenant Access Violation
    
    Usage:
        log_org_access_violation(
            user_id="user_123",
            email="user@example.com",
            user_org_id="org_456",
            resource_org_id="org_789",
            resource_type="case",
            resource_id="CASE-000123"
        )
    """
    log_audit_event(
        event_type=AuditEventType.ORG_VIOLATION,
        user_id=user_id,
        email=email,
        resource_type=resource_type,
        resource_id=resource_id,
        action="access_denied",
        result="failure",
        metadata={
            "user_org_id": user_org_id,
            "resource_org_id": resource_org_id,
            "violation_type": "cross_tenant_access"
        },
        ip_address=ip_address
    )


def log_admin_access(
    user_id: str,
    email: str,
    action: str,
    allowed: bool,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log Admin Access Attempt
    
    Usage:
        log_admin_access(
            user_id="admin_1",
            email="admin@example.com",
            action="create_user",
            allowed=True
        )
    """
    event_type = AuditEventType.ADMIN_ACCESS if allowed else AuditEventType.ADMIN_ACCESS_DENIED
    
    log_audit_event(
        event_type=event_type,
        user_id=user_id,
        email=email,
        resource_type="admin",
        action=action,
        result="success" if allowed else "failure",
        metadata=metadata,
        ip_address=ip_address
    )


def log_trial_event(
    event_type: AuditEventType,
    user_id: str,
    email: str,
    trial_plan: str,
    trial_ends_at: Optional[datetime] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log Trial-Management Event
    
    Usage:
        log_trial_event(
            event_type=AuditEventType.TRIAL_STARTED,
            user_id="user_123",
            email="user@example.com",
            trial_plan="pro",
            trial_ends_at=datetime.utcnow() + timedelta(days=14)
        )
    """
    log_audit_event(
        event_type=event_type,
        user_id=user_id,
        email=email,
        resource_type="trial",
        action=trial_plan,
        result="success",
        metadata={
            "trial_plan": trial_plan,
            "trial_ends_at": trial_ends_at.isoformat() if trial_ends_at else None,
            **(metadata or {})
        }
    )


def log_rate_limit_event(
    user_id: str,
    plan: str,
    endpoint: str,
    limit: str,
    current_count: int,
    ip_address: Optional[str] = None
) -> None:
    """
    Log Rate-Limit Event
    
    Usage:
        log_rate_limit_event(
            user_id="user_123",
            plan="community",
            endpoint="/api/v1/trace",
            limit="10/minute",
            current_count=11
        )
    """
    log_audit_event(
        event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
        user_id=user_id,
        resource_type="rate_limit",
        action=endpoint,
        result="failure",
        metadata={
            "plan": plan,
            "limit": limit,
            "current_count": current_count
        },
        ip_address=ip_address
    )


# Configure audit logger (separate log file)
def configure_audit_logger():
    """Configure audit logger with separate file handler"""
    audit_logger.setLevel(logging.INFO)
    
    # JSON Formatter für strukturierte Logs
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage()
            }
            
            # Add audit_event if present
            if hasattr(record, 'audit_event'):
                log_obj.update(record.audit_event)
            
            return json.dumps(log_obj)
    
    # File Handler für Audit-Logs
    try:
        import os
        log_dir = os.getenv("LOG_DIR", "/var/log/blockchain-forensics")
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(f"{log_dir}/audit.log")
        file_handler.setFormatter(JSONFormatter())
        audit_logger.addHandler(file_handler)
    except Exception:
        # Fallback zu Console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(JSONFormatter())
        audit_logger.addHandler(console_handler)


# Initialize on import
configure_audit_logger()
