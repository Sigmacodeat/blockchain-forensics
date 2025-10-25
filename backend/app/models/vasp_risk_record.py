from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, DateTime, Float, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.case import Base as CaseBase, _IS_TEST as CASE_IS_TEST

Base = CaseBase
_IS_TEST = CASE_IS_TEST
_ID_TYPE: Any = String(36) if _IS_TEST else PGUUID(as_uuid=True)


class VaspRiskRecordORM(Base):  # type: ignore[misc]
    __tablename__ = "vasp_risk_records"

    id = Column(_ID_TYPE, primary_key=True, index=True, default=lambda: str(uuid.uuid4()) if _IS_TEST else uuid.uuid4())
    vasp_id = Column(String(255), nullable=False, index=True)
    vasp_name = Column(String(512), nullable=False)
    scored_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    overall_risk = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    compliance_status = Column(String(50), nullable=False)
    sanctions_hit = Column(Boolean, nullable=False, default=False)
    pep_hit = Column(Boolean, nullable=False, default=False)
    adverse_media_hit = Column(Boolean, nullable=False, default=False)
    adverse_media_count = Column(Integer, nullable=False, default=0)
    recommended_action = Column(String(50), nullable=False)
    risk_factors = Column(JSON, nullable=False, default=list)
    compliance_issues = Column(JSON, nullable=False, default=list)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<VaspRiskRecordORM vasp_id={self.vasp_id} risk={self.overall_risk} score={self.risk_score}>"
