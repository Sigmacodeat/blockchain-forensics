"""
Case Management Service
=======================

Business logic for blockchain forensics case management.
Handles case creation, updates, notes, attachments, and timeline events.
"""

import logging
import uuid
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.case import (
    Case,
    CaseNote,
    CaseAttachment,
    CaseEvent,
    CaseStatus,
    CasePriority,
    Base
)
from app.db.session import SessionLocal
from app.messaging.kafka_client import KafkaTopics

logger = logging.getLogger(__name__)


class CaseManagementService:
    """Service for case management operations"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def create_case(
        self,
        title: str,
        description: str,
        priority: CasePriority = CasePriority.MEDIUM,
        assignee_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Create a new case.

        Args:
            title: Case title
            description: Case description
            priority: Case priority level
            assignee_id: User ID of assignee
            tags: List of tags
            category: Case category
            created_by: User ID who created the case

        Returns:
            Dict with success status and case details
        """
        db = self.db_session or SessionLocal()

        try:
            # Generate unique case ID
            case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"

            # Create case record
            case = Case(
                case_id=case_id,
                title=title,
                description=description,
                priority=priority,
                assignee_id=assignee_id,
                tags=tags or [],
                category=category,
                created_by=created_by
            )

            db.add(case)
            db.flush()  # Get case.id

            # Add creation event
            self._add_case_event(
                db,
                case.id,
                "case_created",
                f"Case '{title}' created",
                created_by,
                "system"
            )

            db.commit()

            # Trigger audit event
            self._trigger_audit_event(case_id, "case_created", {
                "title": title,
                "priority": priority.value,
                "category": category,
                "assignee": assignee_id
            })

            logger.info(f"Case {case_id} created successfully")

            return {
                "success": True,
                "case_id": case_id,
                "case": self._serialize_case(case)
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating case: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if not self.db_session:
                db.close()

    def add_timeline_event(
        self,
        case_id: str,
        event_type: str,
        description: str,
        triggered_by: str,
        triggered_by_name: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        db = self.db_session or SessionLocal()

        try:
            case = db.query(Case).filter(Case.case_id == case_id).first()

            if not case:
                return {
                    "success": False,
                    "error": f"Case {case_id} not found"
                }

            event = self._add_case_event(
                db,
                case.id,
                event_type,
                description,
                triggered_by,
                triggered_by_name or triggered_by,
                payload
            )

            db.flush()
            serialized = self._serialize_event(event)

            db.commit()

            return {
                "success": True,
                "event": serialized
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error adding timeline event to case {case_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if not self.db_session:
                db.close()

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get case details by ID.

        Args:
            case_id: Case ID

        Returns:
            Dict with case details or None if not found
        """
        db = self.db_session or SessionLocal()

        try:
            case = db.query(Case).filter(Case.case_id == case_id).first()

            if not case:
                return None

            return self._serialize_case(case)

        except Exception as e:
            logger.error(f"Error getting case {case_id}: {e}")
            return None
        finally:
            if not self.db_session:
                db.close()

    def update_case(
        self,
        case_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[CaseStatus] = None,
        priority: Optional[CasePriority] = None,
        assignee_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        updated_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Update case details.

        Args:
            case_id: Case ID
            title: New title
            description: New description
            status: New status
            priority: New priority
            assignee_id: New assignee
            tags: New tags
            category: New category
            updated_by: User making the update

        Returns:
            Dict with success status and updated case
        """
        db = self.db_session or SessionLocal()

        try:
            case = db.query(Case).filter(Case.case_id == case_id).first()

            if not case:
                return {
                    "success": False,
                    "error": f"Case {case_id} not found"
                }

            # Track changes for events
            changes = []

            if title and title != case.title:
                changes.append(f"Title changed to '{title}'")
                case.title = title

            if description and description != case.description:
                changes.append("Description updated")
                case.description = description

            if status and status != case.status:
                old_status = case.status.value
                case.status = status
                changes.append(f"Status changed from {old_status} to {status.value}")

                if status == CaseStatus.CLOSED:
                    case.closed_at = datetime.utcnow()

            if priority and priority != case.priority:
                old_priority = case.priority.value
                case.priority = priority
                changes.append(f"Priority changed from {old_priority} to {priority.value}")

            if assignee_id != case.assignee_id:
                old_assignee = case.assignee_id or "Unassigned"
                case.assignee_id = assignee_id
                case.assigned_at = datetime.utcnow() if assignee_id else None
                changes.append(f"Assignee changed to {assignee_id or 'Unassigned'}")

            if tags is not None and tags != case.tags:
                changes.append("Tags updated")
                case.tags = tags

            if category and category != case.category:
                changes.append(f"Category changed to {category}")
                case.category = category

            case.updated_at = datetime.utcnow()

            # Add update event if there were changes
            if changes:
                self._add_case_event(
                    db,
                    case.id,
                    "case_updated",
                    "; ".join(changes),
                    updated_by,
                    "system"
                )

            db.commit()

            # Trigger audit event
            self._trigger_audit_event(case_id, "case_updated", {
                "changes": changes,
                "updated_by": updated_by
            })

            logger.info(f"Case {case_id} updated successfully")

            return {
                "success": True,
                "case_id": case_id,
                "case": self._serialize_case(case)
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating case {case_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if not self.db_session:
                db.close()

    def add_note(
        self,
        case_id: str,
        note_text: str,
        author_id: str,
        author_name: str,
        is_internal: bool = False
    ) -> Dict[str, Any]:
        """
        Add a note to a case.

        Args:
            case_id: Case ID
            note_text: Note content
            author_id: User ID of author
            author_name: Display name of author
            is_internal: Whether note is internal only

        Returns:
            Dict with success status and note details
        """
        db = self.db_session or SessionLocal()

        try:
            case = db.query(Case).filter(Case.case_id == case_id).first()

            if not case:
                return {
                    "success": False,
                    "error": f"Case {case_id} not found"
                }

            note = CaseNote(
                case_id=case.id,
                author_id=author_id,
                author_name=author_name,
                note_text=note_text,
                is_internal=1 if is_internal else 0
            )

            db.add(note)

            # Add note event
            self._add_case_event(
                db,
                case.id,
                "note_added",
                f"Note added by {author_name}",
                author_id,
                "system"
            )

            db.commit()

            logger.info(f"Note added to case {case_id}")

            return {
                "success": True,
                "note_id": note.id,
                "note": self._serialize_note(note)
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error adding note to case {case_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if not self.db_session:
                db.close()

    def add_attachment(
        self,
        case_id: str,
        filename: str,
        file_type: str,
        file_size: int,
        file_uri: str,
        file_hash: str,
        uploaded_by: str,
        description: Optional[str] = None,
        is_evidence: bool = True
    ) -> Dict[str, Any]:
        """
        Add an attachment to a case.

        Args:
            case_id: Case ID
            filename: Original filename
            file_type: MIME type
            file_size: File size in bytes
            file_uri: Storage URI
            file_hash: SHA-256 hash
            uploaded_by: User ID who uploaded
            description: Optional description
            is_evidence: Whether this is evidence

        Returns:
            Dict with success status and attachment details
        """
        db = self.db_session or SessionLocal()

        try:
            case = db.query(Case).filter(Case.case_id == case_id).first()

            if not case:
                return {
                    "success": False,
                    "error": f"Case {case_id} not found"
                }

            attachment = CaseAttachment(
                case_id=case.id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                file_uri=file_uri,
                file_hash=file_hash,
                uploaded_by=uploaded_by,
                description=description,
                is_evidence=1 if is_evidence else 0
            )

            db.add(attachment)

            # Add attachment event
            self._add_case_event(
                db,
                case.id,
                "attachment_uploaded",
                f"File '{filename}' uploaded",
                uploaded_by,
                "system"
            )

            db.commit()

            logger.info(f"Attachment '{filename}' added to case {case_id}")

            return {
                "success": True,
                "attachment_id": attachment.id,
                "attachment": self._serialize_attachment(attachment)
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error adding attachment to case {case_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if not self.db_session:
                db.close()

    def get_case_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        """
        Get timeline events for a case.

        Args:
            case_id: Case ID

        Returns:
            List of timeline events
        """
        db = self.db_session or SessionLocal()

        try:
            case = db.query(Case).filter(Case.case_id == case_id).first()

            if not case:
                return []

            events = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(
                CaseEvent.created_at.desc()
            ).all()

            return [self._serialize_event(event) for event in events]

        except Exception as e:
            logger.error(f"Error getting timeline for case {case_id}: {e}")
            return []
        finally:
            if not self.db_session:
                db.close()

    def query_cases(
        self,
        status: Optional[CaseStatus] = None,
        priority: Optional[CasePriority] = None,
        assignee_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query cases with filters.

        Args:
            status: Filter by status
            priority: Filter by priority
            assignee_id: Filter by assignee
            category: Filter by category
            tags: Filter by tags (any match)
            limit: Max results
            offset: Pagination offset

        Returns:
            Dict with cases list and metadata
        """
        db = self.db_session or SessionLocal()

        try:
            query = db.query(Case)

            if status:
                query = query.filter(Case.status == status)

            if priority:
                query = query.filter(Case.priority == priority)

            if assignee_id:
                query = query.filter(Case.assignee_id == assignee_id)

            if category:
                query = query.filter(Case.category == category)

            if tags:
                # Filter cases that have any of the specified tags
                tag_conditions = [Case.tags.contains([tag]) for tag in tags]
                query = query.filter(db.or_(*tag_conditions))

            # Get total count
            total = query.count()

            # Apply pagination and get results
            cases = query.order_by(Case.created_at.desc()).offset(offset).limit(limit).all()

            return {
                "cases": [self._serialize_case(case) for case in cases],
                "total": total,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error querying cases: {e}")
            return {
                "cases": [],
                "total": 0,
                "error": str(e)
            }
        finally:
            if not self.db_session:
                db.close()

    def _add_case_event(
        self,
        db: Session,
        case_id: int,
        event_type: str,
        description: str,
        triggered_by: str,
        triggered_by_name: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> CaseEvent:
        """Add a timeline event to a case"""
        event = CaseEvent(
            case_id=case_id,
            event_type=event_type,
            event_description=description,
            event_payload=payload,
            triggered_by=triggered_by,
            triggered_by_name=triggered_by_name
        )

        db.add(event)
        return event

    def _serialize_case(self, case: Case) -> Dict[str, Any]:
        """Serialize case for API response"""
        return {
            "id": case.id,
            "case_id": case.case_id,
            "title": case.title,
            "description": case.description,
            "status": case.status.value,
            "priority": case.priority.value,
            "assignee_id": case.assignee_id,
            "assignee_name": None,  # Would need user lookup
            "created_by": case.created_by,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
            "closed_at": case.closed_at.isoformat() if case.closed_at else None,
            "tags": case.tags,
            "category": case.category,
            "notes_count": len(case.notes),
            "attachments_count": len(case.attachments),
            "events_count": len(case.events)
        }

    def _serialize_note(self, note: CaseNote) -> Dict[str, Any]:
        """Serialize note for API response"""
        return {
            "id": note.id,
            "case_id": note.case_id,
            "author_id": note.author_id,
            "author_name": note.author_name,
            "note_text": note.note_text,
            "is_internal": bool(note.is_internal),
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat()
        }

    def _serialize_attachment(self, attachment: CaseAttachment) -> Dict[str, Any]:
        """Serialize attachment for API response"""
        return {
            "id": attachment.id,
            "case_id": attachment.case_id,
            "filename": attachment.filename,
            "file_type": attachment.file_type,
            "file_size": attachment.file_size,
            "file_uri": attachment.file_uri,
            "file_hash": attachment.file_hash,
            "uploaded_by": attachment.uploaded_by,
            "description": attachment.description,
            "is_evidence": bool(attachment.is_evidence),
            "created_at": attachment.created_at.isoformat()
        }

    def _serialize_event(self, event: CaseEvent) -> Dict[str, Any]:
        """Serialize event for API response"""
        return {
            "id": event.id,
            "case_id": event.case_id,
            "event_type": event.event_type,
            "event_description": event.event_description,
            "event_payload": event.event_payload,
            "triggered_by": event.triggered_by,
            "triggered_by_name": event.triggered_by_name,
            "created_at": event.created_at.isoformat()
        }

    def _trigger_audit_event(self, case_id: str, event_type: str, data: Dict[str, Any]):
        """Trigger audit event for Kafka"""
        try:
            from app.messaging.kafka_client import KafkaProducerClient

            producer = KafkaProducerClient()
            audit_event = {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "case_id": case_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }

            producer.produce_event(
                topic=KafkaTopics.AUDIT_LOG,
                event=audit_event
            )

        except Exception as e:
            logger.error(f"Failed to trigger audit event: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Compute basic case statistics: totals and breakdowns.
        Returns:
            {
                "total_cases": int,
                "by_status": {status: count},
                "by_priority": {priority: count}
            }
        """
        db = self.db_session or SessionLocal()
        try:
            # Total
            total = db.query(Case).count()

            # By status
            by_status: Dict[str, int] = {}
            for s in CaseStatus:
                by_status[s.value] = db.query(Case).filter(Case.status == s).count()

            # By priority
            by_priority: Dict[str, int] = {}
            for p in CasePriority:
                by_priority[p.value] = db.query(Case).filter(Case.priority == p).count()

            return {
                "total_cases": total,
                "by_status": by_status,
                "by_priority": by_priority,
            }
        except Exception as e:
            logger.error(f"Error computing case statistics: {e}")
            return {"total_cases": 0, "by_status": {}, "by_priority": {}, "error": str(e)}
        finally:
            if not self.db_session:
                db.close()
    
    async def count_user_cases(self, user_id: str) -> int:
        """Count total cases for a user"""
        db = self.db_session or SessionLocal()
        try:
            count = db.query(Case).filter(Case.created_by == user_id).count()
            return count
        except Exception as e:
            logger.error(f"Error counting user cases: {e}")
            return 0
        finally:
            if not self.db_session:
                db.close()
    
    async def create_case_with_user(
        self,
        user: Any,
        title: str,
        description: str,
        priority: CasePriority = CasePriority.MEDIUM
    ) -> Dict[str, Any]:
        """Create case with user context and plan-based limits"""
        from app.models.user import SubscriptionPlan
        
        # Plan-based limits
        CASE_LIMITS = {
            SubscriptionPlan.COMMUNITY: 10,
            SubscriptionPlan.STARTER: 50,
            SubscriptionPlan.PRO: 100,
            SubscriptionPlan.BUSINESS: 500,
            SubscriptionPlan.PLUS: 1000,
            SubscriptionPlan.ENTERPRISE: 999999  # Unlimited
        }
        
        # Check user's case count
        user_case_count = await self.count_user_cases(user.id)
        limit = CASE_LIMITS.get(user.plan, 10)
        
        if user_case_count >= limit:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail=f"Case limit reached ({limit} cases for {user.plan.value} plan). Upgrade to create more cases."
            )
        
        # Create case
        result = self.create_case(
            title=title,
            description=description,
            priority=priority,
            created_by=user.id
        )
        
        result['plan_tier'] = user.plan.value
        return result


# Global service instance
case_service = CaseManagementService()
