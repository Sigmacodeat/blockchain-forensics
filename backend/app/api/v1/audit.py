"""
Audit Log API Endpoints
Admin-only access to audit logs for compliance
"""

import logging
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query
from datetime import datetime

from app.models.audit_log import (
    AuditLogEntry,
    AuditLogQuery,
    AuditAction,
    query_audit_logs,
)
from app.auth.dependencies import require_admin_strict as require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[AuditLogEntry])
async def get_audit_logs(
    user_id: Optional[str] = Query(None),
    action: Optional[AuditAction] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    success: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin),
):
    """
    Get audit logs (Admin only)
    
    **Requires:** Admin Role
    
    **Filters:**
    - user_id: Filter by user
    - action: Filter by action type
    - resource_type: Filter by resource (trace, user, etc.)
    - start_date/end_date: Date range
    - success: Filter by success/failure
    """
    query = AuditLogQuery(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        success=success,
        limit=limit,
        offset=offset,
    )
    
    logs = query_audit_logs(query)
    
    logger.info(f"Admin {current_user['email']} queried audit logs: {len(logs)} results")
    
    return logs


@router.get("/logs", response_model=List[AuditLogEntry])
async def get_audit_logs_alias(
    user_id: Optional[str] = Query(None),
    action: Optional[AuditAction] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    success: Optional[bool] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_admin),
):
    """
    Alias: /api/v1/audit/logs -> same as root listing
    """
    return await get_audit_logs(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        success=success,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get("/stats")
async def get_audit_stats(
    current_user: dict = Depends(require_admin),
):
    """
    Get audit log statistics (Admin only)
    
    **Requires:** Admin Role
    """
    from app.models.audit_log import audit_logs
    
    # Calculate stats
    total_logs = len(audit_logs)
    failed_actions = len([log for log in audit_logs if not log.success])
    
    # Actions by type
    actions_by_type: Dict[str, int] = {}
    for log in audit_logs:
        action_str = str(log.action)
        actions_by_type[action_str] = actions_by_type.get(action_str, 0) + 1
    
    # Recent activity (last 24h)
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_logs = [log for log in audit_logs if log.timestamp >= cutoff]
    
    return {
        "total_logs": total_logs,
        "failed_actions": failed_actions,
        "success_rate": (total_logs - failed_actions) / total_logs if total_logs > 0 else 1.0,
        "actions_by_type": actions_by_type,
        "last_24h_count": len(recent_logs),
    }


@router.get("/user/{user_id}", response_model=List[AuditLogEntry])
async def get_user_audit_logs(
    user_id: str,
    limit: int = Query(100, le=1000),
    current_user: dict = Depends(require_admin),
):
    """
    Get audit logs for specific user (Admin only)
    
    **Requires:** Admin Role
    """
    query = AuditLogQuery(user_id=user_id, limit=limit)
    logs = query_audit_logs(query)
    
    logger.info(f"Admin {current_user['email']} viewed audit logs for user {user_id}")
    
    return logs
