"""
Minimal Case Management Models (in-memory friendly)
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Case(BaseModel):
    case_id: str = Field(...)
    title: str = Field(..., min_length=1)
    description: str = Field("")
    lead_investigator: str = Field(..., min_length=1)
    status: str = Field("active")  # active|closed|archived
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Entity(BaseModel):
    address: str = Field(..., min_length=1)
    chain: str = Field(..., min_length=1)
    labels: Dict[str, Any] = Field(default_factory=dict)


class EvidenceLink(BaseModel):
    case_id: str
    resource_id: str
    resource_type: str
    record_hash: Optional[str] = None
    notes: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
