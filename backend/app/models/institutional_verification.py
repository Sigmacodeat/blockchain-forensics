"""
Institutional Verification Models
=================================

SQLAlchemy ORM models for institutional verification workflow.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class InstitutionalVerificationStatus(str):
    """Verification status values"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class InstitutionalVerification(Base):  # type: ignore[misc]
    """Institutional verification request"""

    __tablename__ = "institutional_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    organization_type = Column(String(50), nullable=False)
    organization_name = Column(String(255), nullable=True)

    status = Column(String(50), default=InstitutionalVerificationStatus.PENDING, index=True)
    admin_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    reviewed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    document_type = Column(String(50), nullable=True)
    document_url = Column(Text, nullable=True)
    document_filename = Column(String(255), nullable=True)
    document_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserORM", foreign_keys=[user_id])
    reviewer = relationship("UserORM", foreign_keys=[reviewed_by])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_type": self.organization_type,
            "organization_name": self.organization_name,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "rejection_reason": self.rejection_reason,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "document": {
                "type": self.document_type,
                "url": self.document_url,
                "filename": self.document_filename,
                "metadata": self.document_metadata,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
