"""
🏦 CASE MANAGEMENT SYSTEM für Banken
======================================

Vollständiges Case-Management für Compliance-Teams:
- Case Creation & Assignment
- Workflow Management
- Comments & Timeline
- Status Tracking
- Approval Workflows
- SAR Integration
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CaseStatus(str, Enum):
    """Case Status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AWAITING_CUSTOMER = "awaiting_customer"
    AWAITING_APPROVAL = "awaiting_approval"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class CasePriority(str, Enum):
    """Case Priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseType(str, Enum):
    """Case Types"""
    TRANSACTION_REVIEW = "transaction_review"
    CUSTOMER_DUE_DILIGENCE = "customer_due_diligence"
    SAR_INVESTIGATION = "sar_investigation"
    ANOMALY_DETECTION = "anomaly_detection"
    PEP_SCREENING = "pep_screening"
    SANCTIONS_HIT = "sanctions_hit"
    MIXER_CONTACT = "mixer_contact"
    HIGH_RISK_JURISDICTION = "high_risk_jurisdiction"


class CaseDecision(str, Enum):
    """Final Decisions"""
    CLEARED = "cleared"
    FALSE_POSITIVE = "false_positive"
    SAR_FILED = "sar_filed"
    ACCOUNT_CLOSED = "account_closed"
    ENHANCED_MONITORING = "enhanced_monitoring"
    TIER_UPGRADE = "tier_upgrade"


@dataclass
class CaseComment:
    """Comment in Case Timeline"""
    comment_id: str
    case_id: str
    user_id: str
    user_name: str
    comment: str
    timestamp: datetime
    is_internal: bool = True  # Nur für Compliance-Team


@dataclass
class CaseAction:
    """Action in Case Timeline"""
    action_id: str
    case_id: str
    action_type: str  # assigned, status_changed, approved, etc.
    user_id: str
    user_name: str
    details: Dict[str, Any]
    timestamp: datetime


@dataclass
class Case:
    """Compliance Case"""
    case_id: str
    case_type: CaseType
    title: str
    description: str
    
    # Customer
    customer_id: str
    customer_name: str
    customer_tier: str
    
    # Assignment
    assigned_to: Optional[str] = None  # User ID
    assigned_to_name: Optional[str] = None
    created_by: str = ""
    created_by_name: str = ""
    
    # Status
    status: CaseStatus = CaseStatus.OPEN
    priority: CasePriority = CasePriority.MEDIUM
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Related Data
    related_transactions: List[str] = field(default_factory=list)
    related_addresses: List[str] = field(default_factory=list)
    related_alerts: List[str] = field(default_factory=list)
    
    # Timeline
    comments: List[CaseComment] = field(default_factory=list)
    actions: List[CaseAction] = field(default_factory=list)
    
    # Decision
    decision: Optional[CaseDecision] = None
    decision_reason: Optional[str] = None
    decision_by: Optional[str] = None
    decision_at: Optional[datetime] = None
    
    # SAR
    sar_id: Optional[str] = None
    sar_filed_at: Optional[datetime] = None
    
    # Tags & Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CaseManagementService:
    """Case Management Service für Banken"""
    
    def __init__(self):
        self.cases: Dict[str, Case] = {}
        logger.info("🏦 Case Management Service initialized")
    
    # =========================================================================
    # CASE CRUD
    # =========================================================================
    
    def create_case(
        self,
        case_type: CaseType,
        title: str,
        description: str,
        customer_id: str,
        customer_name: str,
        customer_tier: str,
        created_by: str,
        created_by_name: str,
        priority: CasePriority = CasePriority.MEDIUM,
        related_transactions: List[str] = None,
        related_addresses: List[str] = None,
        related_alerts: List[str] = None,
        tags: List[str] = None
    ) -> Case:
        """Create new case"""
        case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{len(self.cases) + 1:04d}"
        
        # Calculate due date based on priority
        due_date = self._calculate_due_date(priority)
        
        case = Case(
            case_id=case_id,
            case_type=case_type,
            title=title,
            description=description,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_tier=customer_tier,
            created_by=created_by,
            created_by_name=created_by_name,
            priority=priority,
            due_date=due_date,
            related_transactions=related_transactions or [],
            related_addresses=related_addresses or [],
            related_alerts=related_alerts or [],
            tags=tags or []
        )
        
        # Log creation action
        self._add_action(
            case,
            "case_created",
            created_by,
            created_by_name,
            {"priority": priority.value}
        )
        
        self.cases[case_id] = case
        logger.info(f"📋 Case created: {case_id} - {title}")
        
        return case
    
    def get_case(self, case_id: str) -> Optional[Case]:
        """Get case by ID"""
        return self.cases.get(case_id)
    
    def list_cases(
        self,
        status: Optional[CaseStatus] = None,
        assigned_to: Optional[str] = None,
        priority: Optional[CasePriority] = None,
        case_type: Optional[CaseType] = None,
        customer_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Case]:
        """List cases with filters"""
        filtered = []
        
        for case in self.cases.values():
            # Apply filters
            if status and case.status != status:
                continue
            if assigned_to and case.assigned_to != assigned_to:
                continue
            if priority and case.priority != priority:
                continue
            if case_type and case.case_type != case_type:
                continue
            if customer_id and case.customer_id != customer_id:
                continue
            
            filtered.append(case)
        
        # Sort by priority (critical first) and created_at (newest first)
        priority_order = {
            CasePriority.CRITICAL: 0,
            CasePriority.HIGH: 1,
            CasePriority.MEDIUM: 2,
            CasePriority.LOW: 3
        }
        filtered.sort(
            key=lambda c: (priority_order[c.priority], -c.created_at.timestamp())
        )
        
        return filtered[offset:offset+limit]
    
    # =========================================================================
    # CASE UPDATES
    # =========================================================================
    
    def assign_case(
        self,
        case_id: str,
        assigned_to: str,
        assigned_to_name: str,
        assigned_by: str,
        assigned_by_name: str
    ) -> Case:
        """Assign case to officer"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        case.assigned_to = assigned_to
        case.assigned_to_name = assigned_to_name
        case.updated_at = datetime.now()
        
        if case.status == CaseStatus.OPEN:
            case.status = CaseStatus.IN_PROGRESS
        
        self._add_action(
            case,
            "assigned",
            assigned_by,
            assigned_by_name,
            {"assigned_to": assigned_to_name}
        )
        
        logger.info(f"👤 Case {case_id} assigned to {assigned_to_name}")
        return case
    
    def update_status(
        self,
        case_id: str,
        new_status: CaseStatus,
        user_id: str,
        user_name: str,
        reason: Optional[str] = None
    ) -> Case:
        """Update case status"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        old_status = case.status
        case.status = new_status
        case.updated_at = datetime.now()
        
        if new_status == CaseStatus.CLOSED:
            case.closed_at = datetime.now()
        
        self._add_action(
            case,
            "status_changed",
            user_id,
            user_name,
            {
                "old_status": old_status.value,
                "new_status": new_status.value,
                "reason": reason
            }
        )
        
        logger.info(f"📊 Case {case_id} status: {old_status.value} → {new_status.value}")
        return case
    
    def update_priority(
        self,
        case_id: str,
        new_priority: CasePriority,
        user_id: str,
        user_name: str
    ) -> Case:
        """Update case priority"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        old_priority = case.priority
        case.priority = new_priority
        case.updated_at = datetime.now()
        
        # Recalculate due date
        case.due_date = self._calculate_due_date(new_priority, case.created_at)
        
        self._add_action(
            case,
            "priority_changed",
            user_id,
            user_name,
            {
                "old_priority": old_priority.value,
                "new_priority": new_priority.value
            }
        )
        
        logger.info(f"⚠️ Case {case_id} priority: {old_priority.value} → {new_priority.value}")
        return case
    
    def add_comment(
        self,
        case_id: str,
        user_id: str,
        user_name: str,
        comment: str,
        is_internal: bool = True
    ) -> Case:
        """Add comment to case"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        comment_obj = CaseComment(
            comment_id=f"{case_id}-C{len(case.comments) + 1}",
            case_id=case_id,
            user_id=user_id,
            user_name=user_name,
            comment=comment,
            timestamp=datetime.now(),
            is_internal=is_internal
        )
        
        case.comments.append(comment_obj)
        case.updated_at = datetime.now()
        
        logger.info(f"💬 Comment added to case {case_id}")
        return case
    
    def close_case(
        self,
        case_id: str,
        decision: CaseDecision,
        decision_reason: str,
        user_id: str,
        user_name: str
    ) -> Case:
        """Close case with decision"""
        case = self.cases.get(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        case.status = CaseStatus.CLOSED
        case.decision = decision
        case.decision_reason = decision_reason
        case.decision_by = user_id
        case.decision_at = datetime.now()
        case.closed_at = datetime.now()
        case.updated_at = datetime.now()
        
        self._add_action(
            case,
            "case_closed",
            user_id,
            user_name,
            {
                "decision": decision.value,
                "reason": decision_reason
            }
        )
        
        logger.info(f"✅ Case {case_id} closed with decision: {decision.value}")
        return case
    
    # =========================================================================
    # ANALYTICS
    # =========================================================================
    
    def get_case_statistics(self) -> Dict[str, Any]:
        """Get case statistics"""
        total_cases = len(self.cases)
        
        # Status distribution
        status_dist = {}
        for status in CaseStatus:
            status_dist[status.value] = len([c for c in self.cases.values() if c.status == status])
        
        # Priority distribution
        priority_dist = {}
        for priority in CasePriority:
            priority_dist[priority.value] = len([c for c in self.cases.values() if c.priority == priority])
        
        # Type distribution
        type_dist = {}
        for case_type in CaseType:
            type_dist[case_type.value] = len([c for c in self.cases.values() if c.case_type == case_type])
        
        # Average resolution time
        closed_cases = [c for c in self.cases.values() if c.status == CaseStatus.CLOSED and c.closed_at]
        if closed_cases:
            avg_resolution_hours = sum(
                (c.closed_at - c.created_at).total_seconds() / 3600
                for c in closed_cases
            ) / len(closed_cases)
        else:
            avg_resolution_hours = 0.0
        
        # Overdue cases
        overdue = len([
            c for c in self.cases.values()
            if c.due_date and c.status not in [CaseStatus.CLOSED, CaseStatus.RESOLVED]
            and datetime.now() > c.due_date
        ])
        
        return {
            "total_cases": total_cases,
            "status_distribution": status_dist,
            "priority_distribution": priority_dist,
            "type_distribution": type_dist,
            "avg_resolution_hours": round(avg_resolution_hours, 1),
            "overdue_cases": overdue
        }
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _calculate_due_date(
        self,
        priority: CasePriority,
        from_date: Optional[datetime] = None
    ) -> datetime:
        """Calculate due date based on priority"""
        base_date = from_date or datetime.now()
        
        sla_hours = {
            CasePriority.CRITICAL: 4,    # 4 hours
            CasePriority.HIGH: 24,        # 1 day
            CasePriority.MEDIUM: 72,      # 3 days
            CasePriority.LOW: 168         # 7 days
        }
        
        return base_date + timedelta(hours=sla_hours[priority])
    
    def _add_action(
        self,
        case: Case,
        action_type: str,
        user_id: str,
        user_name: str,
        details: Dict[str, Any]
    ):
        """Add action to case timeline"""
        action = CaseAction(
            action_id=f"{case.case_id}-A{len(case.actions) + 1}",
            case_id=case.case_id,
            action_type=action_type,
            user_id=user_id,
            user_name=user_name,
            details=details,
            timestamp=datetime.now()
        )
        case.actions.append(action)


# Global instance
case_management_service = CaseManagementService()
