"""
Link Tracking Models
"""

from sqlalchemy import Column, String, DateTime, Integer, JSONB
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base_class import Base


class TrackedLink(Base):
    """
    Tracked Short-Link
    """
    __tablename__ = "tracked_links"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id = Column(String, unique=True, nullable=False, index=True)
    short_slug = Column(String, unique=True, nullable=False, index=True)
    short_url = Column(String, nullable=False)
    target_url = Column(String, nullable=False)
    
    # Source Info
    source_platform = Column(String, nullable=False, index=True)  # twitter, linkedin, instagram
    source_username = Column(String, nullable=True, index=True)
    campaign = Column(String, nullable=True, index=True)
    
    # Stats
    click_count = Column(Integer, nullable=False, default=0)
    unique_visitors = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class LinkClick(Base):
    """
    Individual Link-Click with Intelligence-Data
    """
    __tablename__ = "link_clicks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id = Column(String, nullable=False, index=True)
    
    # Complete Intelligence-Report
    intelligence_data = Column(JSONB, nullable=False)
    # Contains:
    # - ip_intelligence: {country, city, lat/lon, timezone, isp, is_vpn, is_proxy}
    # - social_media: {platform, username, profile_url}
    # - device: {os, browser, device_type, is_mobile, is_bot}
    # - fingerprint: {hash, data}
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
