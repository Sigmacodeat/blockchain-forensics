"""
Link-Tracking API
Professional Attribution & Intelligence
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.db.session import get_db
from app.auth.dependencies import require_admin
from app.models.link_tracking import TrackedLink, LinkClick
from app.services.link_tracker import link_tracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/links", tags=["Link Tracking"])


class CreateLinkRequest(BaseModel):
    """Create Tracking-Link"""
    target_url: str
    source_platform: str  # twitter, linkedin, instagram, etc.
    source_username: Optional[str] = None
    campaign: Optional[str] = None
    custom_slug: Optional[str] = None


@router.post("/create")
async def create_tracking_link(
    request: CreateLinkRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Erstelle Tracking-Link für Social-Media
    
    **Use-Cases**:
    - Twitter-Profil-Link
    - LinkedIn-Post-Link
    - Instagram-Bio-Link
    - Reddit-Comment-Link
    
    **Returns**: Short-URL, QR-Code, Analytics-Dashboard
    
    **Example**:
    ```json
    {
      "target_url": "https://yoursite.com/pricing",
      "source_platform": "twitter",
      "source_username": "john_doe",
      "campaign": "summer_2025"
    }
    ```
    
    **Response**:
    ```json
    {
      "short_url": "https://yoursite.com/s/twitter-john_doe",
      "tracking_id": "trk_abc123",
      "qr_code": "data:image/png;base64,...",
      "analytics_dashboard": "https://yoursite.com/admin/links/trk_abc123"
    }
    ```
    """
    try:
        result = link_tracker.create_tracking_link(
            target_url=request.target_url,
            source_platform=request.source_platform,
            source_username=request.source_username,
            campaign=request.campaign,
            custom_slug=request.custom_slug
        )
        
        # Save to DB
        link = TrackedLink(
            tracking_id=result['tracking_id'],
            short_slug=result['short_url'].split('/')[-1],
            short_url=result['short_url'],
            target_url=request.target_url,
            source_platform=request.source_platform,
            source_username=request.source_username,
            campaign=request.campaign
        )
        db.add(link)
        db.commit()
        
        return result
    
    except Exception as e:
        logger.error(f"Link creation failed: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")


@router.get("/s/{slug}")
async def redirect_short_link(
    slug: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Short-Link Redirect with Intelligence-Tracking
    
    **Public Endpoint** (no auth required)
    
    This is where the magic happens! 🎯
    """
    # Get link
    link = db.query(TrackedLink).filter(TrackedLink.short_slug == slug).first()
    
    if not link:
        raise HTTPException(404, "Link not found")
    
    # Extract Intelligence
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")
    referrer = request.headers.get("Referer")
    
    # Track Click with Full Intelligence
    intelligence = link_tracker.track_click(
        tracking_id=link.tracking_id,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    
    # Save Click
    click = LinkClick(
        tracking_id=link.tracking_id,
        intelligence_data=intelligence
    )
    db.add(click)
    
    # Update Stats
    link.click_count += 1
    db.commit()
    
    logger.info(f"Redirect: {slug} → {link.target_url} | {intelligence['ip_intelligence']['city']}, {intelligence['ip_intelligence']['country']} | Platform: {intelligence['social_media']['platform']}")
    
    # Redirect
    return RedirectResponse(url=link.target_url, status_code=302)


@router.get("/{tracking_id}/analytics")
async def get_link_analytics(
    tracking_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Complete Analytics for Tracking-Link
    
    Returns:
    - Total Clicks
    - Unique Visitors
    - Geographic Distribution (Countries, Cities)
    - Social-Media-Platforms
    - Detected Usernames
    - Device-Types
    - Hourly/Daily-Distribution
    - Top-Referrers
    """
    link = db.query(TrackedLink).filter(TrackedLink.tracking_id == tracking_id).first()
    
    if not link:
        raise HTTPException(404, "Link not found")
    
    # Get all clicks
    clicks = db.query(LinkClick).filter(LinkClick.tracking_id == tracking_id).all()
    
    if not clicks:
        return {
            "link": {
                "short_url": link.short_url,
                "target_url": link.target_url,
                "source_platform": link.source_platform,
                "source_username": link.source_username
            },
            "total_clicks": 0,
            "message": "No clicks yet"
        }
    
    # Aggregate Data
    total_clicks = len(clicks)
    
    # Geographic Distribution
    countries = {}
    cities = {}
    for click in clicks:
        country = click.intelligence_data['ip_intelligence'].get('country', 'Unknown')
        city = click.intelligence_data['ip_intelligence'].get('city', 'Unknown')
        
        countries[country] = countries.get(country, 0) + 1
        city_key = f"{city}, {country}"
        cities[city_key] = cities.get(city_key, 0) + 1
    
    # Social-Media Distribution
    platforms = {}
    usernames_detected = set()
    for click in clicks:
        platform = click.intelligence_data['social_media'].get('platform', 'unknown')
        username = click.intelligence_data['social_media'].get('username')
        
        platforms[platform] = platforms.get(platform, 0) + 1
        if username:
            usernames_detected.add(username)
    
    # Device Distribution
    devices = {}
    for click in clicks:
        device_type = click.intelligence_data['device'].get('device_type', 'unknown')
        devices[device_type] = devices.get(device_type, 0) + 1
    
    # Hourly Distribution (last 24h)
    hourly = {}
    for click in clicks:
        hour = click.created_at.strftime('%Y-%m-%d %H:00')
        hourly[hour] = hourly.get(hour, 0) + 1
    
    return {
        "link": {
            "short_url": link.short_url,
            "target_url": link.target_url,
            "source_platform": link.source_platform,
            "source_username": link.source_username,
            "campaign": link.campaign,
            "created_at": link.created_at.isoformat()
        },
        "stats": {
            "total_clicks": total_clicks,
            "unique_countries": len(countries),
            "unique_cities": len(cities)
        },
        "geographic": {
            "countries": [{"name": k, "clicks": v} for k, v in sorted(countries.items(), key=lambda x: x[1], reverse=True)][:10],
            "cities": [{"name": k, "clicks": v} for k, v in sorted(cities.items(), key=lambda x: x[1], reverse=True)][:10]
        },
        "social_media": {
            "platforms": [{"name": k, "clicks": v} for k, v in sorted(platforms.items(), key=lambda x: x[1], reverse=True)],
            "usernames_detected": list(usernames_detected)
        },
        "devices": devices,
        "hourly_distribution": hourly
    }


@router.get("/{tracking_id}/clicks")
async def get_link_clicks_detail(
    tracking_id: str,
    limit: int = 50,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Detailed Click-List with Full Intelligence
    
    Returns: Complete Intelligence-Report for each click
    """
    clicks = db.query(LinkClick).filter(
        LinkClick.tracking_id == tracking_id
    ).order_by(desc(LinkClick.created_at)).limit(limit).all()
    
    return [
        {
            "timestamp": click.created_at.isoformat(),
            "intelligence": click.intelligence_data
        }
        for click in clicks
    ]


@router.get("/admin/all")
async def get_all_links(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all Tracking-Links
    """
    links = db.query(TrackedLink).order_by(desc(TrackedLink.created_at)).all()
    
    return [
        {
            "tracking_id": link.tracking_id,
            "short_url": link.short_url,
            "target_url": link.target_url,
            "source_platform": link.source_platform,
            "source_username": link.source_username,
            "campaign": link.campaign,
            "click_count": link.click_count,
            "created_at": link.created_at.isoformat()
        }
        for link in links
    ]
