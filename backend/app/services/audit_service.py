"""
Audit Logging Service
=====================

Comprehensive audit trail for all forensic operations.
Compliant with GDPR, SOC2, ISO27001.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json
from app.db.postgres import postgres_client

logger = logging.getLogger(__name__)


class AuditService:
    """Centralized audit logging for compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self._table_initialized = False
    
    async def _ensure_table(self):
        """Ensure audit_logs table exists"""
        try:
            await postgres_client.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    user_id VARCHAR(255),
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(50),
                    resource_id VARCHAR(255),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    details JSONB,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    duration_ms INTEGER,
                    INDEX idx_user_id (user_id),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_action (action),
                    INDEX idx_resource (resource_type, resource_id)
                )
            """)
        except Exception as e:
            logger.warning(f"Audit table creation failed (may already exist): {e}")
    
    async def log_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """Log an audit event"""
        # Lazy table initialization
        if not self._table_initialized:
            await self._ensure_table()
            self._table_initialized = True
        
        try:
            await postgres_client.execute("""
                INSERT INTO audit_logs (
                    timestamp, user_id, action, resource_type, resource_id,
                    ip_address, user_agent, details, success, error_message, duration_ms
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                datetime.utcnow(),
                user_id,
                action,
                resource_type,
                resource_id,
                ip_address,
                user_agent,
                json.dumps(details) if details else None,
                success,
                error_message,
                duration_ms
            )
            
            # Also log to structured logger
            self.logger.info(
                f"AUDIT: {action}",
                extra={
                    "user_id": user_id,
                    "resource": f"{resource_type}:{resource_id}" if resource_type else None,
                    "success": success,
                    "duration_ms": duration_ms
                }
            )
        except Exception as e:
            # Never fail the main operation due to audit logging
            logger.error(f"Audit logging failed: {e}", exc_info=True)
    
    async def log_tool_call(
        self,
        tool_name: str,
        user_id: str,
        args: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """Log AI tool execution"""
        await self.log_action(
            action=f"tool_call:{tool_name}",
            user_id=user_id,
            resource_type="ai_tool",
            resource_id=tool_name,
            details={
                "args": self._sanitize_args(args),
                "result_summary": self._summarize_result(result) if result else None
            },
            success=success,
            error_message=error,
            duration_ms=duration_ms
        )
    
    async def log_download(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        format: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log file download"""
        await self.log_action(
            action="download",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"format": format},
            ip_address=ip_address
        )
    
    async def log_case_action(
        self,
        action: str,
        case_id: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log case-related action"""
        await self.log_action(
            action=f"case_{action}",
            user_id=user_id,
            resource_type="case",
            resource_id=case_id,
            details=details
        )
    
    async def get_user_audit_trail(
        self,
        user_id: str,
        limit: int = 100,
        action_filter: Optional[str] = None
    ) -> list:
        """Get audit trail for user (GDPR compliance)"""
        query = """
            SELECT timestamp, action, resource_type, resource_id, 
                   details, success, duration_ms
            FROM audit_logs
            WHERE user_id = $1
        """
        params = [user_id]
        
        if action_filter:
            query += " AND action = $2"
            params.append(action_filter)
        
        query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        rows = await postgres_client.fetch(query, *params)
        return [dict(row) for row in rows]
    
    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from logged arguments"""
        sanitized = args.copy()
        
        # Remove sensitive fields
        sensitive_keys = [
            'password', 'token', 'api_key', 'secret',
            'private_key', 'seed_phrase', 'mnemonic'
        ]
        
        for key in list(sanitized.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
        
        return sanitized
    
    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of result (avoid logging large data)"""
        if not result:
            return {}
        
        summary = {
            "success": result.get("success", True),
            "keys": list(result.keys())[:10]  # First 10 keys
        }
        
        # Add size indicators
        for key, value in result.items():
            if isinstance(value, (list, dict)):
                summary[f"{key}_size"] = len(value)
        
        return summary


# Global singleton
audit_service = AuditService()
