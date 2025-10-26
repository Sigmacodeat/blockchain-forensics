
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import json

router = APIRouter()

class AnalyticsEvent:
    def __init__(self, event_name, data, ip, user_agent):
        self.event_name = event_name
        self.data = data
        self.ip = ip
        self.user_agent = user_agent
        self.timestamp = datetime.utcnow()

@router.post("/api/analytics/track")
async def track_event(request: Request, db: Session = Depends(get_db)):
    """Server-side event tracking for reliability"""
    data = await request.json()
    event_name = data.get("event")

    # Create event record
    db_event = AnalyticsEvent(
        event_name=event_name,
        data=json.dumps(data),
        ip=request.client.host,
        user_agent=data.get("userAgent", "")
    )

    # Store in database
    db.add(db_event)
    db.commit()

    # Could forward to external services here
    # e.g., send to GA4 Measurement Protocol

    return {"status": "tracked", "event_id": db_event.id}

@router.get("/api/analytics/events")
async def get_events(db: Session = Depends(get_db)):
    """Get analytics events for dashboard"""
    events = db.query(AnalyticsEvent).order_by(AnalyticsEvent.timestamp.desc()).limit(100).all()
    return {
        "events": [
            {
                "event_name": e.event_name,
                "data": json.loads(e.data),
                "timestamp": e.timestamp.isoformat(),
                "ip": e.ip
            } for e in events
        ]
    }
