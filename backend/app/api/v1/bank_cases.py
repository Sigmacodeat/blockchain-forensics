"""
🏦 BANK CASE MANAGEMENT API
============================

Complete API for Bank Compliance Case Management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.case_management import (
    case_management_service,
    CaseType,
    CaseStatus,
    CasePriority,
    CaseDecision
)
from app.auth.dependencies import get_current_user, require_plan

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bank/cases", tags=["🏦 Bank Cases"])


# =========================================================================
# REQUEST/RESPONSE MODELS
# =========================================================================

class CaseCreateRequest(BaseModel):
    """Create Case Request"""
    case_type: str = Field(..., description="transaction_review, sar_investigation, etc.")
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    customer_id: str
    customer_name: str
    customer_tier: str
    priority: str = Field("medium", description="low, medium, high, critical")
    related_transactions: List[str] = Field(default_factory=list)
    related_addresses: List[str] = Field(default_factory=list)
    related_alerts: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class CaseAssignRequest(BaseModel):
    """Assign Case Request"""
    assigned_to: str = Field(..., description="User ID to assign to")
    assigned_to_name: str = Field(..., description="User display name")


class CaseStatusRequest(BaseModel):
    """Update Status Request"""
    new_status: str = Field(..., description="open, in_progress, closed, etc.")
    reason: Optional[str] = None


class CasePriorityRequest(BaseModel):
    """Update Priority Request"""
    new_priority: str = Field(..., description="low, medium, high, critical")


class CaseCommentRequest(BaseModel):
    """Add Comment Request"""
    comment: str = Field(..., max_length=2000)
    is_internal: bool = Field(True, description="Internal note or customer-visible")


class CaseCloseRequest(BaseModel):
    """Close Case Request"""
    decision: str = Field(..., description="cleared, false_positive, sar_filed, etc.")
    decision_reason: str = Field(..., max_length=2000)


class CaseResponse(BaseModel):
    """Case Response"""
    case_id: str
    case_type: str
    title: str
    description: str
    customer_id: str
    customer_name: str
    customer_tier: str
    status: str
    priority: str
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    created_at: str
    updated_at: str
    due_date: Optional[str]
    closed_at: Optional[str]
    decision: Optional[str]
    decision_reason: Optional[str]
    related_transactions: List[str]
    related_addresses: List[str]
    tags: List[str]


# =========================================================================
# CASE CRUD ENDPOINTS
# =========================================================================

@router.post("", response_model=Dict[str, Any])
async def create_case(
    request: CaseCreateRequest,
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    📋 Create new compliance case
    
    **Use Case:** Compliance Officer creates case for investigation
    
    **Example:**
    ```json
    {
      "case_type": "transaction_review",
      "title": "High-Risk Transaction Review",
      "description": "Customer sent €25k to known mixer",
      "customer_id": "CUST-12345",
      "customer_name": "John Doe",
      "customer_tier": "tier_2",
      "priority": "high",
      "related_transactions": ["0xabc..."],
      "tags": ["mixer", "high-value"]
    }
    ```
    
    **Plan:** Plus+
    """
    try:
        # Parse enums
        case_type = CaseType(request.case_type)
        priority = CasePriority(request.priority)
        
        # Create case
        case = case_management_service.create_case(
            case_type=case_type,
            title=request.title,
            description=request.description,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            customer_tier=request.customer_tier,
            created_by=str(current_user["user_id"]),
            created_by_name=current_user.get("email", ""),
            priority=priority,
            related_transactions=request.related_transactions,
            related_addresses=request.related_addresses,
            related_alerts=request.related_alerts,
            tags=request.tags
        )
        
        return {
            "success": True,
            "case_id": case.case_id,
            "due_date": case.due_date.isoformat() if case.due_date else None,
            "message": f"Case {case.case_id} created"
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create case: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create case")


@router.get("", response_model=Dict[str, Any])
async def list_cases(
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    case_type: Optional[str] = Query(None, description="Filter by type"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    📋 List cases with filters
    
    **Query Parameters:**
    - status: open, in_progress, closed, etc.
    - assigned_to: User ID
    - priority: low, medium, high, critical
    - case_type: transaction_review, sar_investigation, etc.
    - customer_id: Customer ID
    
    **Plan:** Plus+
    """
    try:
        # Parse filters
        status_filter = CaseStatus(status) if status else None
        priority_filter = CasePriority(priority) if priority else None
        type_filter = CaseType(case_type) if case_type else None
        
        # Get cases
        cases = case_management_service.list_cases(
            status=status_filter,
            assigned_to=assigned_to,
            priority=priority_filter,
            case_type=type_filter,
            customer_id=customer_id,
            limit=limit,
            offset=offset
        )
        
        # Serialize
        cases_data = []
        for case in cases:
            cases_data.append({
                "case_id": case.case_id,
                "case_type": case.case_type.value,
                "title": case.title,
                "description": case.description,
                "customer_id": case.customer_id,
                "customer_name": case.customer_name,
                "customer_tier": case.customer_tier,
                "status": case.status.value,
                "priority": case.priority.value,
                "assigned_to": case.assigned_to,
                "assigned_to_name": case.assigned_to_name,
                "created_at": case.created_at.isoformat(),
                "updated_at": case.updated_at.isoformat(),
                "due_date": case.due_date.isoformat() if case.due_date else None,
                "tags": case.tags
            })
        
        return {
            "cases": cases_data,
            "total": len(cases_data),
            "limit": limit,
            "offset": offset
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list cases")


@router.get("/{case_id}", response_model=Dict[str, Any])
async def get_case(
    case_id: str,
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    📋 Get case details with full timeline
    
    **Plan:** Plus+
    """
    case = case_management_service.get_case(case_id)
    
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    # Serialize timeline
    actions_data = [
        {
            "action_id": a.action_id,
            "action_type": a.action_type,
            "user_id": a.user_id,
            "user_name": a.user_name,
            "details": a.details,
            "timestamp": a.timestamp.isoformat()
        }
        for a in case.actions
    ]
    
    comments_data = [
        {
            "comment_id": c.comment_id,
            "user_id": c.user_id,
            "user_name": c.user_name,
            "comment": c.comment,
            "is_internal": c.is_internal,
            "timestamp": c.timestamp.isoformat()
        }
        for c in case.comments
    ]
    
    return {
        "case_id": case.case_id,
        "case_type": case.case_type.value,
        "title": case.title,
        "description": case.description,
        "customer_id": case.customer_id,
        "customer_name": case.customer_name,
        "customer_tier": case.customer_tier,
        "status": case.status.value,
        "priority": case.priority.value,
        "assigned_to": case.assigned_to,
        "assigned_to_name": case.assigned_to_name,
        "created_by": case.created_by,
        "created_by_name": case.created_by_name,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
        "due_date": case.due_date.isoformat() if case.due_date else None,
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        "decision": case.decision.value if case.decision else None,
        "decision_reason": case.decision_reason,
        "decision_by": case.decision_by,
        "decision_at": case.decision_at.isoformat() if case.decision_at else None,
        "related_transactions": case.related_transactions,
        "related_addresses": case.related_addresses,
        "related_alerts": case.related_alerts,
        "tags": case.tags,
        "actions": actions_data,
        "comments": comments_data,
        "metadata": case.metadata
    }


# =========================================================================
# CASE ACTIONS
# =========================================================================

@router.put("/{case_id}/assign", response_model=Dict[str, Any])
async def assign_case(
    case_id: str,
    request: CaseAssignRequest,
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    👤 Assign case to officer
    
    **Plan:** Plus+
    """
    try:
        case = case_management_service.assign_case(
            case_id=case_id,
            assigned_to=request.assigned_to,
            assigned_to_name=request.assigned_to_name,
            assigned_by=str(current_user["user_id"]),
            assigned_by_name=current_user.get("email", "")
        )
        
        return {
            "success": True,
            "case_id": case.case_id,
            "assigned_to": case.assigned_to_name,
            "status": case.status.value
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to assign case: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to assign case")


@router.put("/{case_id}/status", response_model=Dict[str, Any])
async def update_status(
    case_id: str,
    request: CaseStatusRequest,
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    📊 Update case status
    
    **Status Options:**
    - open
    - in_progress
    - awaiting_customer
    - awaiting_approval
    - resolved
    - closed
    - escalated
    
    **Plan:** Plus+
    """
    try:
        new_status = CaseStatus(request.new_status)
        
        case = case_management_service.update_status(
            case_id=case_id,
            new_status=new_status,
            user_id=str(current_user["user_id"]),
            user_name=current_user.get("email", ""),
            reason=request.reason
        )
        
        return {
            "success": True,
            "case_id": case.case_id,
            "status": case.status.value,
            "updated_at": case.updated_at.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update status")


@router.put("/{case_id}/priority", response_model=Dict[str, Any])
async def update_priority(
    case_id: str,
    request: CasePriorityRequest,
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    ⚠️ Update case priority
    
    **Priority Options:**
    - low (7 days SLA)
    - medium (3 days SLA)
    - high (24 hours SLA)
    - critical (4 hours SLA)
    
    **Plan:** Plus+
    """
    try:
        new_priority = CasePriority(request.new_priority)
        
        case = case_management_service.update_priority(
            case_id=case_id,
            new_priority=new_priority,
            user_id=str(current_user["user_id"]),
            user_name=current_user.get("email", "")
        )
        
        return {
            "success": True,
            "case_id": case.case_id,
            "priority": case.priority.value,
            "due_date": case.due_date.isoformat() if case.due_date else None
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update priority: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update priority")


@router.post("/{case_id}/comments", response_model=Dict[str, Any])
async def add_comment(
    case_id: str,
    request: CaseCommentRequest,
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    💬 Add comment to case
    
    **Plan:** Plus+
    """
    try:
        case = case_management_service.add_comment(
            case_id=case_id,
            user_id=str(current_user["user_id"]),
            user_name=current_user.get("email", ""),
            comment=request.comment,
            is_internal=request.is_internal
        )
        
        return {
            "success": True,
            "case_id": case.case_id,
            "comment_count": len(case.comments)
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add comment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add comment")


@router.put("/{case_id}/close", response_model=Dict[str, Any])
async def close_case(
    case_id: str,
    request: CaseCloseRequest,
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    ✅ Close case with decision
    
    **Decision Options:**
    - cleared
    - false_positive
    - sar_filed
    - account_closed
    - enhanced_monitoring
    - tier_upgrade
    
    **Plan:** Plus+
    """
    try:
        decision = CaseDecision(request.decision)
        
        case = case_management_service.close_case(
            case_id=case_id,
            decision=decision,
            decision_reason=request.decision_reason,
            user_id=str(current_user["user_id"]),
            user_name=current_user.get("email", "")
        )
        
        return {
            "success": True,
            "case_id": case.case_id,
            "status": case.status.value,
            "decision": case.decision.value,
            "closed_at": case.closed_at.isoformat() if case.closed_at else None
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to close case: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to close case")


# =========================================================================
# ANALYTICS
# =========================================================================

@router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_statistics(
    current_user: dict = Depends(require_plan('enterprise'))
):
    """
    📊 Get case statistics & analytics
    
    **Returns:**
    - Total cases
    - Status distribution
    - Priority distribution
    - Type distribution
    - Average resolution time
    - Overdue cases
    
    **Plan:** Plus+
    """
    try:
        stats = case_management_service.get_case_statistics()
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get statistics")
