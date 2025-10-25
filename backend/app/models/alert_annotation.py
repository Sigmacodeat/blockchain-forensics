from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Index

# Reuse Base from existing models to share metadata
from app.models.case import Base  # type: ignore


class AlertAnnotation(Base):
    __tablename__ = "alert_annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(128), nullable=False, index=True)
    disposition = Column(String(32), nullable=True)  # false_positive|true_positive|benign|unknown
    event_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_alert_annotations_alert_id", "alert_id"),
        Index("ix_alert_annotations_updated_at", "updated_at"),
        {"extend_existing": True},
    )
