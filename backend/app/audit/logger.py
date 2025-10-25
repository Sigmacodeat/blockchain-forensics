"""
Audit Logging System
===================

Comprehensive audit logging for compliance and security monitoring.
Logs all critical operations with structured data for forensic analysis.

Features:
- Structured JSON logging
- Event classification (create, read, update, delete, auth, etc.)
- User and system activity tracking
- Compliance reporting integration
- Immutable audit trails
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import hashlib
import os
from app.config import settings

# Import database for audit storage if available
try:
    from app.db.postgres import postgres_client
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Import metrics for audit event counting
try:
    from app.observability.metrics import AUDIT_EVENTS_TOTAL
except ImportError:
    class MockCounter:
        def inc(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
    AUDIT_EVENTS_TOTAL = MockCounter()

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    AUTHENTICATE = "authenticate"
    AUTHORIZE = "authorize"
    EXECUTE = "execute"  # For background jobs and API calls
    EXPORT = "export"
    COMPLIANCE = "compliance"  # Sanctions checks, risk assessments
    SECURITY = "security"  # Failed logins, suspicious activities


class AuditSeverity(Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLogger:
    """
    Centralized audit logging service
    """

    def __init__(self):
        self.enabled = True
        self.log_to_db = DB_AVAILABLE
        # Disable file logging in tests/collection environments to avoid permission errors
        in_tests = os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST")
        # If LOG_FILE is explicitly configured, honor it; otherwise default to project-local logs path
        configured_log_file = getattr(settings, "LOG_FILE", None)
        default_local_path = os.path.abspath(os.path.join(os.getcwd(), "logs", "audit.log"))
        self.audit_log_path = configured_log_file or default_local_path
        self.log_to_file = (configured_log_file is not None) and (not in_tests)

        # Ensure log directory exists when file logging is enabled
        if self.log_to_file:
            try:
                os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Cannot create log directory, disabling file logs: {e}")
                self.log_to_file = False

        # Setup file logger for audit events when enabled
        self.file_logger = logging.getLogger("audit")
        if self.log_to_file and not self.file_logger.handlers:
            try:
                handler = logging.FileHandler(self.audit_log_path)
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
                self.file_logger.addHandler(handler)
                self.file_logger.setLevel(logging.INFO)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Cannot open audit log file, disabling file logs: {e}")
                self.log_to_file = False

    async def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> str:
        """
        Log an audit event

        Args:
            event_type: Type of audit event
            severity: Severity level
            user_id: User performing the action
            resource: Resource being accessed/modified
            action: Specific action performed
            details: Additional structured data
            ip_address: Client IP address
            user_agent: Client user agent
            session_id: User session ID
            request_id: HTTP request ID
            success: Whether the operation succeeded
            error_message: Error message if operation failed

        Returns:
            Audit event ID (hash of event data)
        """
        if not self.enabled:
            return ""

        # Build audit event
        event_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "session_id": session_id,
            "request_id": request_id,
            "success": success,
            "error_message": error_message,
        }

        # Generate unique event ID
        event_id = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()[:16]
        event_data["event_id"] = event_id

        # Log to file (synchronous)
        try:
            if self.log_to_file:
                self.file_logger.info(json.dumps(event_data))
        except Exception as e:
            logger.error(f"Failed to write audit log to file: {e}")

        # Log to database (asynchronous)
        if self.log_to_db:
            asyncio.create_task(self._log_to_db(event_data))

        # Update metrics
        try:
            AUDIT_EVENTS_TOTAL.labels(
                event_type=event_type.value,
                severity=severity.value
            ).inc()
        except Exception:
            pass

        return event_id

    async def _log_to_db(self, event_data: Dict[str, Any]):
        """Log audit event to database"""
        try:
            async with postgres_client.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_events (
                        event_id, timestamp, event_type, severity, user_id,
                        resource, action, details, ip_address, user_agent,
                        session_id, request_id, success, error_message
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    """,
                    event_data["event_id"],
                    event_data["timestamp"],
                    event_data["event_type"],
                    event_data["severity"],
                    event_data["user_id"],
                    event_data["resource"],
                    event_data["action"],
                    json.dumps(event_data["details"]),
                    event_data["ip_address"],
                    event_data["user_agent"],
                    event_data["session_id"],
                    event_data["request_id"],
                    event_data["success"],
                    event_data["error_message"],
                )
        except Exception as e:
            logger.error(f"Failed to write audit event to database: {e}")

    async def query_audit_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query audit events with filters

        Returns:
            List of audit events matching criteria
        """
        if not self.log_to_db:
            return []

        try:
            query = """
                SELECT event_id, timestamp, event_type, severity, user_id,
                       resource, action, details, ip_address, user_agent,
                       session_id, request_id, success, error_message
                FROM audit_events
                WHERE 1=1
            """
            params = []

            if start_time:
                query += " AND timestamp >= $1"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= $2"
                params.append(end_time)

            if event_type:
                query += " AND event_type = $3"
                params.append(event_type.value)

            if user_id:
                query += " AND user_id = $4"
                params.append(user_id)

            if resource:
                query += " AND resource = $5"
                params.append(resource)

            query += " ORDER BY timestamp DESC LIMIT $6"
            params.append(limit)

            async with postgres_client.acquire() as conn:
                rows = await conn.fetch(query, *params)

            events = []
            for row in rows:
                event = dict(row)
                event["details"] = json.loads(event["details"] or "{}")
                events.append(event)

            return events

        except Exception as e:
            logger.error(f"Failed to query audit events: {e}")
            return []

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Generate compliance report from audit logs

        Args:
            start_date: Report start date
            end_date: Report end date
            report_type: Type of report ("summary", "detailed", "security")

        Returns:
            Compliance report data
        """
        if not self.log_to_db:
            return {"error": "Database not available for compliance reports"}

        try:
            # Get events for the period
            events = await self.query_audit_events(
                start_time=start_date,
                end_time=end_date,
                limit=10000  # Large limit for reports
            )

            if report_type == "summary":
                return {
                    "report_type": "summary",
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "total_events": len(events),
                    "events_by_type": self._group_events_by_type(events),
                    "events_by_severity": self._group_events_by_severity(events),
                    "high_risk_events": len([e for e in events if e["severity"] in ["high", "critical"]]),
                    "failed_operations": len([e for e in events if not e["success"]]),
                    "unique_users": len(set(e["user_id"] for e in events if e["user_id"])),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }

            elif report_type == "security":
                security_events = [e for e in events if e["event_type"] in ["security", "authenticate", "authorize"]]
                return {
                    "report_type": "security",
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "security_events": len(security_events),
                    "failed_logins": len([e for e in security_events if e["event_type"] == "authenticate" and not e["success"]]),
                    "suspicious_activities": len([e for e in security_events if e["severity"] in ["high", "critical"]]),
                    "events": security_events[:100],  # Limit for readability
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }

            else:  # detailed
                return {
                    "report_type": "detailed",
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "events": events,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {"error": str(e)}

    def _group_events_by_type(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group events by type"""
        groups = {}
        for event in events:
            event_type = event["event_type"]
            groups[event_type] = groups.get(event_type, 0) + 1
        return groups

    def _group_events_by_severity(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group events by severity"""
        groups = {}
        for event in events:
            severity = event["severity"]
            groups[severity] = groups.get(severity, 0) + 1
        return groups


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions for common audit events
async def log_api_access(
    user_id: Optional[str],
    method: str,
    endpoint: str,
    status_code: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    response_time: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
) -> str:
    """Log API access event"""
    severity = AuditSeverity.LOW
    if status_code >= 400:
        severity = AuditSeverity.MEDIUM
    if status_code >= 500:
        severity = AuditSeverity.HIGH

    return await audit_logger.log_event(
        event_type=AuditEventType.EXECUTE,
        severity=severity,
        user_id=user_id,
        resource=endpoint,
        action=f"{method} {endpoint}",
        details={
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
            **(details or {})
        },
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        success=status_code < 400,
        error_message=None if status_code < 400 else "API Error",
    )


async def log_authentication(
    user_id: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> str:
    """Log authentication event"""
    return await audit_logger.log_event(
        event_type=AuditEventType.AUTHENTICATE,
        severity=AuditSeverity.HIGH,
        user_id=user_id,
        action="login" if success else "login_failed",
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id,
        success=success,
        error_message="Authentication failed" if not success else None,
    )


async def log_data_access(
    user_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> str:
    """Log data access event (read/create/update/delete)"""
    severity = AuditSeverity.MEDIUM
    if action in ["create", "update", "delete"]:
        severity = AuditSeverity.HIGH

    return await audit_logger.log_event(
        event_type=AuditEventType.READ if action == "read" else AuditEventType.CREATE if action == "create" else AuditEventType.UPDATE if action == "update" else AuditEventType.DELETE,
        severity=severity,
        user_id=user_id,
        resource=f"{resource_type}:{resource_id}",
        action=action,
        details=details or {},
        ip_address=ip_address,
        success=True,
    )


async def log_security_event(
    event_type: str,
    severity: AuditSeverity,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> str:
    """Log security-related event"""
    return await audit_logger.log_event(
        event_type=AuditEventType.SECURITY,
        severity=severity,
        user_id=user_id,
        action=event_type,
        details=details or {},
        ip_address=ip_address,
        success=False,
        error_message=f"Security event: {event_type}",
    )
