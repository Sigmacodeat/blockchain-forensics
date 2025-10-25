"""
Institutional Verification Service
===================================

Business logic for institutional verification workflow.
Handles document uploads, status management, and admin reviews.
"""

import logging
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.institutional_verification import (
    InstitutionalVerification,
    InstitutionalVerificationStatus
)
from app.db.session import get_db_session
from app.services.report_storage_service import report_storage

logger = logging.getLogger(__name__)

# Accepted organization types for institutional verification. Keep in sync with API validation.
ALLOWED_ORGANIZATION_TYPES = {
    "police",
    "detective",
    "lawyer",
    "government",
    "exchange",
    "other",
}

# Allowed document extensions and size limits for uploads.
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024


class InstitutionalVerificationService:
    """Business logic for managing institutional verification lifecycle."""

    VALID_STATUSES = {
        InstitutionalVerificationStatus.PENDING,
        InstitutionalVerificationStatus.APPROVED,
        InstitutionalVerificationStatus.REJECTED,
        InstitutionalVerificationStatus.CANCELLED,
    }

    def __init__(self) -> None:
        self.storage_service = report_storage

    @staticmethod
    def _error(message: str, *, code: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"success": False, "error": message}
        if code:
            payload["code"] = code
        return payload

    @staticmethod
    def _sanitize_optional_text(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @staticmethod
    def _normalize_organization_type(value: str) -> Optional[str]:
        normalized = value.strip().lower()
        return normalized if normalized in ALLOWED_ORGANIZATION_TYPES else None

    @contextmanager
    def _session_scope(self, db: Optional[Session] = None):
        session = db or get_db_session()
        try:
            yield session
        finally:
            if db is None:
                session.close()

    async def create_verification_request(
        self,
        user_id: str,
        organization_type: str,
        organization_name: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        org_type = self._normalize_organization_type(organization_type)
        if org_type is None:
            return self._error("Invalid organization type", code="invalid_organization_type")

        org_name = self._sanitize_optional_text(organization_name)

        with self._session_scope(db) as session:
            try:
                existing = session.query(InstitutionalVerification).filter(
                    InstitutionalVerification.user_id == user_id,
                    InstitutionalVerification.status == InstitutionalVerificationStatus.PENDING,
                ).first()

                if existing:
                    return self._error(
                        "User already has a pending verification request",
                        code="duplicate_request",
                    )

                verification = InstitutionalVerification(
                    user_id=user_id,
                    organization_type=org_type,
                    organization_name=org_name,
                    status=InstitutionalVerificationStatus.PENDING,
                )

                session.add(verification)
                session.commit()
                session.refresh(verification)

                logger.info("Created verification request %s for user %s", verification.id, user_id)

                return {"success": True, "verification": verification.to_dict()}

            except IntegrityError as exc:
                session.rollback()
                logger.exception("Integrity error creating verification request: %s", exc)
                return self._error("Database integrity error", code="integrity_error")
            except Exception as exc:
                session.rollback()
                logger.exception("Unexpected error creating verification request: %s", exc)
                return self._error("Failed to create verification request", code="creation_failed")

    async def upload_verification_document(
        self,
        verification_id: int,
        file_data: bytes,
        filename: str,
        document_type: str,
        user_id: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        document_type_sanitized = self._sanitize_optional_text(document_type)
        if not document_type_sanitized:
            return self._error("Document type is required", code="missing_document_type")

        if not file_data:
            return self._error("File payload is empty", code="empty_file")

        file_extension = Path(filename or "").suffix.lower()
        if not file_extension or file_extension not in ALLOWED_DOCUMENT_EXTENSIONS:
            return self._error("Unsupported document file type", code="invalid_document_type")

        if len(file_data) > MAX_DOCUMENT_SIZE_BYTES:
            return self._error("Document exceeds maximum size (10MB)", code="file_too_large")

        storage_format = file_extension.lstrip(".") or "bin"
        uploaded_at = datetime.utcnow()
        unique_filename = f"institutional_verification_{verification_id}_{uuid.uuid4().hex}{file_extension}"

        with self._session_scope(db) as session:
            try:
                verification = session.query(InstitutionalVerification).filter(
                    InstitutionalVerification.id == verification_id,
                    InstitutionalVerification.user_id == user_id,
                ).with_for_update(nowait=False).first()

                if not verification:
                    return self._error("Verification request not found", code="not_found")

                if verification.status != InstitutionalVerificationStatus.PENDING:
                    return self._error("Cannot upload document for non-pending verification", code="invalid_status")

                document_url = await self.storage_service.store_report(
                    report_id=f"verification_{verification_id}",
                    content=file_data,
                    format=storage_format,
                    user_id=user_id,
                )

                verification.document_type = document_type_sanitized.lower()
                verification.document_url = document_url
                verification.document_filename = unique_filename
                verification.document_metadata = {
                    "original_filename": filename,
                    "file_size": len(file_data),
                    "uploaded_at": uploaded_at.isoformat(),
                    "file_extension": file_extension,
                }
                verification.updated_at = uploaded_at

                session.commit()

                logger.info("Uploaded verification document for request %s", verification_id)

                return {
                    "success": True,
                    "document_url": document_url,
                    "filename": unique_filename,
                }

            except Exception as exc:
                session.rollback()
                logger.exception("Error uploading verification document: %s", exc)
                return self._error("Failed to upload verification document", code="upload_failed")

    async def get_verification_status(
        self,
        user_id: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        with self._session_scope(db) as session:
            try:
                verification = session.query(InstitutionalVerification).filter(
                    InstitutionalVerification.user_id == user_id
                ).order_by(InstitutionalVerification.created_at.desc()).first()

                if not verification:
                    return {
                        "success": True,
                        "has_verification": False,
                        "status": "none",
                        "can_request": True,
                    }

                status = verification.status
                return {
                    "success": True,
                    "has_verification": True,
                    "status": status,
                    "verification": verification.to_dict(),
                    "can_request": status in (
                        InstitutionalVerificationStatus.REJECTED,
                        InstitutionalVerificationStatus.CANCELLED,
                    ),
                }

            except Exception as exc:
                logger.exception("Error retrieving verification status: %s", exc)
                return self._error("Failed to retrieve verification status", code="status_error")

    async def get_verification_request(
        self,
        verification_id: int,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        with self._session_scope(db) as session:
            try:
                query = session.query(InstitutionalVerification).filter(
                    InstitutionalVerification.id == verification_id
                )

                if user_id:
                    query = query.filter(InstitutionalVerification.user_id == user_id)

                verification = query.first()

                if not verification:
                    return self._error("Verification request not found", code="not_found")

                return {"success": True, "verification": verification.to_dict()}

            except Exception as exc:
                logger.exception("Error retrieving verification request: %s", exc)
                return self._error("Failed to retrieve verification request", code="retrieval_failed")

    async def list_verification_requests(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        normalized_status = status.strip().lower() if status else None
        if normalized_status and normalized_status not in self.VALID_STATUSES:
            return self._error("Invalid status filter", code="invalid_status_filter")

        page_size = max(1, min(limit, 100))
        page_offset = max(0, offset)

        with self._session_scope(db) as session:
            try:
                query = session.query(InstitutionalVerification)

                if normalized_status:
                    query = query.filter(InstitutionalVerification.status == normalized_status)

                total = query.count()
                verifications = (
                    query.order_by(InstitutionalVerification.created_at.desc())
                    .offset(page_offset)
                    .limit(page_size)
                    .all()
                )

                return {
                    "success": True,
                    "verifications": [v.to_dict() for v in verifications],
                    "total": total,
                    "limit": page_size,
                    "offset": page_offset,
                }

            except Exception as exc:
                logger.exception("Error listing verification requests: %s", exc)
                return self._error("Failed to list verification requests", code="list_failed")

    async def review_verification_request(
        self,
        verification_id: int,
        admin_user_id: str,
        action: str,
        admin_notes: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        normalized_action = action.strip().lower()
        if normalized_action not in {"approve", "reject"}:
            return self._error("Action must be 'approve' or 'reject'", code="invalid_action")

        admin_notes_clean = self._sanitize_optional_text(admin_notes)
        rejection_reason_clean = self._sanitize_optional_text(rejection_reason)

        with self._session_scope(db) as session:
            try:
                verification = session.query(InstitutionalVerification).filter(
                    InstitutionalVerification.id == verification_id
                ).with_for_update(nowait=False).first()

                if not verification:
                    return self._error("Verification request not found", code="not_found")

                if verification.status != InstitutionalVerificationStatus.PENDING:
                    return self._error(
                        "Only pending verifications can be reviewed",
                        code="invalid_status",
                    )

                decision_timestamp = datetime.utcnow()

                if normalized_action == "approve":
                    verification.status = InstitutionalVerificationStatus.APPROVED
                    verification.rejection_reason = None
                else:
                    verification.status = InstitutionalVerificationStatus.REJECTED
                    verification.rejection_reason = rejection_reason_clean

                verification.reviewed_by = admin_user_id
                verification.reviewed_at = decision_timestamp
                verification.admin_notes = admin_notes_clean
                verification.updated_at = decision_timestamp

                session.commit()

                logger.info("Verification %s %sd by admin %s", verification_id, normalized_action, admin_user_id)

                return {
                    "success": True,
                    "action": normalized_action,
                    "verification": verification.to_dict(),
                }

            except Exception as exc:
                session.rollback()
                logger.exception("Error reviewing verification request: %s", exc)
                return self._error("Failed to review verification request", code="review_failed")


# Singleton instance
institutional_verification_service = InstitutionalVerificationService()
