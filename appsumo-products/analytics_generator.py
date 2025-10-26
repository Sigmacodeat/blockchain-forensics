#!/usr/bin/env python3
"""
Analytics Setup Generator
Creates GA4 configuration, event tracking, and server-side endpoints
"""

import json
import os

def generate_ga4_config():
    """Generate GA4 configuration with custom events"""
    ga4_config = {
        "gtag_id": "GA_MEASUREMENT_ID",
        "custom_dimensions": {
            "dimension1": "user_tier",
            "dimension2": "product_slug",
            "dimension3": "license_key",
            "dimension4": "referrer_source"
        },
        "custom_metrics": {
            "metric1": "feature_usage_count",
            "metric2": "api_calls_count"
        },
        "conversion_events": [
            "license_activated",
            "tier_upgrade",
            "feature_used",
            "support_contacted"
        ]
    }
    return ga4_config

def generate_event_tracking():
    """Generate client-side event tracking code"""
    events = {
        "license_activated": """
        gtag('event', 'license_activated', {
          'event_category': 'conversion',
          'event_label': 'appsumo',
          'value': tier_price,
          'custom_parameter_1': product_slug,
          'custom_parameter_2': tier
        });
        """,
        "feature_used": """
        gtag('event', 'feature_used', {
          'event_category': 'engagement',
          'event_label': feature_name,
          'custom_parameter_1': product_slug,
          'custom_parameter_2': user_tier
        });
        """,
        "tier_upgrade": """
        gtag('event', 'tier_upgrade', {
          'event_category': 'conversion',
          'event_label': 'upsell',
          'value': upgrade_price,
          'custom_parameter_1': product_slug,
          'custom_parameter_2': old_tier + '_to_' + new_tier
        });
        """
    }
    return events

def generate_utm_builder():
    """Generate UTM parameter builder for AppSumo links"""
    utm_config = {
        "base_params": {
            "utm_source": "appsumo",
            "utm_medium": "cpc",
            "utm_campaign": "lifetime-deals"
        },
        "product_mapping": {
            "wallet-guardian": "wg",
            "transaction-inspector": "ti",
            "analytics-pro": "ap",
            "nft-manager": "nm",
            "complete-security": "cs",
            "defi-tracker": "dt"
        }
    }
    return utm_config

def generate_server_tracking():
    """Generate server-side tracking endpoint"""
    server_code = '''
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
'''
    return server_code

def main():
    # Create output directory
    os.makedirs("analytics_output", exist_ok=True)

    # Generate configurations
    ga4_config = generate_ga4_config()
    event_tracking = generate_event_tracking()
    utm_config = generate_utm_builder()
    server_tracking = generate_server_tracking()

    # Save to files
    with open("analytics_output/ga4-config.json", "w") as f:
        json.dump(ga4_config, f, indent=2)

    with open("analytics_output/event-tracking.js", "w") as f:
        f.write("// Client-side event tracking\n")
        for event_name, code in event_tracking.items():
            f.write(f"\n// {event_name}\n{code.strip()}\n")

    with open("analytics_output/utm-config.json", "w") as f:
        json.dump(utm_config, f, indent=2)

    with open("analytics_output/server-tracking.py", "w") as f:
        f.write(server_tracking)

    print("✅ Analytics assets generated:")
    print("   - GA4 configuration (ga4-config.json)")
    print("   - Event tracking code (event-tracking.js)")
    print("   - UTM configuration (utm-config.json)")
    print("   - Server-side tracking (server-tracking.py)")
    print("\n📁 Output in analytics_output/ directory")

if __name__ == "__main__":
    main()
