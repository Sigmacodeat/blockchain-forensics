from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
import os, logging
from uuid import uuid4
from datetime import datetime, timezone
from app.db.postgres import postgres_client
from app.auth.dependencies import require_role
import aiohttp
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


class UltimateAnalyticsPage(BaseModel):
    url: str = Field(..., max_length=1024)
    title: Optional[str] = Field(None, max_length=512)
    referrer: Optional[str] = Field(None, max_length=1024)


class UltimateAnalyticsPayload(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    user_id: Optional[str] = Field(None, max_length=128)
    fingerprint: Optional[Dict[str, Any]] = None
    behavior: Dict[str, Any] = Field(default_factory=dict)
    performance: Dict[str, Any] = Field(default_factory=dict)
    network: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime
    page: UltimateAnalyticsPage
    consent_version: Optional[str] = Field(None, max_length=64)
    events_count: Optional[int] = Field(None, ge=0)


@router.post("/analytics/track")
async def ingest_ultimate_analytics(req: Request, payload: UltimateAnalyticsPayload):
    if req.headers.get("DNT") == "1":
        return {"status": "ignored", "reason": "dnt"}
    if not payload.consent_version:
        return {"status": "ignored", "reason": "missing_consent"}
    if not payload.session_id.strip():
        raise HTTPException(status_code=400, detail="invalid session_id")
    if os.getenv("TEST_MODE") == "1" or not getattr(postgres_client, "pool", None):
        return {"status": "accepted", "persisted": False}

    fingerprint = dict(payload.fingerprint or {})
    behavior = dict(payload.behavior or {})
    if payload.events_count is not None:
        meta = behavior.setdefault("_meta", {})
        if isinstance(meta, dict):
            try:
                meta["events_count"] = int(payload.events_count)
            except (TypeError, ValueError):
                meta.pop("events_count", None)
    performance = dict(payload.performance or {})
    network = payload.network or None
    errors = payload.errors or []

    page_url = payload.page.url[:1024]
    page_title = payload.page.title[:512] if payload.page.title else None
    referrer = payload.page.referrer[:1024] if payload.page.referrer else None

    timestamp = payload.timestamp
    if timestamp.tzinfo is not None:
        timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)

    ip_address = None
    forwarded = req.headers.get("x-forwarded-for")
    if forwarded:
        ip_address = forwarded.split(",")[0].strip()
    elif req.client:
        ip_address = req.client.host

    try:
        async with postgres_client.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO analytics_events (
                    id,
                    session_id,
                    user_id,
                    ip_address,
                    fingerprint,
                    behavior,
                    performance,
                    network,
                    errors,
                    page_url,
                    page_title,
                    referrer,
                    timestamp
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb, $8::jsonb, $9::jsonb, $10, $11, $12, $13)
                """,
                uuid4(),
                payload.session_id.strip(),
                payload.user_id.strip() if payload.user_id else None,
                ip_address,
                fingerprint,
                behavior,
                performance,
                network,
                errors,
                page_url,
                page_title,
                referrer,
                timestamp,
            )
    except Exception as exc:
        logger.warning("Ultimate analytics insert failed: %s", exc)
        return {"status": "accepted", "persisted": False}

    return {"status": "ok", "persisted": True}

class AnalyticsEvent(BaseModel):
    event: str = Field(..., min_length=1, max_length=128)
    ts: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = Field(None, max_length=128)
    path: Optional[str] = Field(None, max_length=512)
    referrer: Optional[str] = Field(None, max_length=512)
    properties: Dict[str, Any] = Field(default_factory=dict)
    org_id: Optional[str] = Field(None, max_length=64)


class WebVitalMetric(BaseModel):
    name: str = Field(..., max_length=32)
    id: str = Field(..., max_length=128)
    value: float
    rating: Optional[str] = Field(None, max_length=16)
    navigationType: Optional[str] = Field(None, max_length=32)
    ts: Optional[int] = None
    org_id: Optional[str] = Field(None, max_length=64)

@router.post("/analytics/events")
async def ingest_event(req: Request, payload: AnalyticsEvent):
    dnt = req.headers.get("DNT") == "1"
    if dnt:
        return {"status": "ignored"}
    if not payload.event:
        raise HTTPException(status_code=400, detail="Missing event name")
    ua = req.headers.get("user-agent", "")[:256]
    ip_hash = ""  # hashed in middleware; optional here
    # Resolve org id from header or payload
    org_id = req.headers.get("X-Org-Id") or payload.org_id
    # Ensure properties also carries org_id for downstream tools
    if org_id:
        payload.properties = {**(payload.properties or {}), "org_id": org_id}
    if os.getenv("TEST_MODE") != "1" and getattr(postgres_client, "pool", None):
        try:
            async with postgres_client.acquire() as conn:
                # Try insert with org_id if the column exists; fallback to legacy insert if it fails
                try:
                    await conn.execute(
                        """
                        INSERT INTO web_events (ts, user_id, session_id, event, properties, path, referrer, ua, ip_hash, method, status, duration, org_id)
                        VALUES (COALESCE(TO_TIMESTAMP($1), NOW()), $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11, $12, $13)
                        """,
                        payload.ts,
                        payload.user_id,
                        payload.session_id,
                        payload.event,
                        payload.properties or {},
                        payload.path,
                        payload.referrer,
                        ua,
                        ip_hash,
                        req.method,
                        200,
                        0.0,
                        org_id,
                    )
                except Exception:
                    await conn.execute(
                        """
                        INSERT INTO web_events (ts, user_id, session_id, event, properties, path, referrer, ua, ip_hash, method, status, duration)
                        VALUES (COALESCE(TO_TIMESTAMP($1), NOW()), $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11, $12)
                        """,
                        payload.ts,
                        payload.user_id,
                        payload.session_id,
                        payload.event,
                        payload.properties or {},
                        payload.path,
                        payload.referrer,
                        ua,
                        ip_hash,
                        req.method,
                        200,
                        0.0,
                    )
        except Exception as e:
            # Swallow DB errors to not break UX
            return {"status": "accepted", "persisted": False}
    # Optional: forward to PostHog if configured
    ph_host = os.getenv("POSTHOG_HOST")
    ph_key = os.getenv("POSTHOG_PROJECT_KEY")
    if ph_host and ph_key:
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{ph_host.rstrip('/')}/capture/",
                    json={
                        "api_key": ph_key,
                        "event": payload.event,
                        "properties": {
                            **(payload.properties or {}),
                            "path": payload.path,
                            "referrer": payload.referrer,
                            "$ip": None,  # do not forward IP
                            "$set": {},
                        },
                        "distinct_id": payload.user_id or payload.session_id or "anon",
                        "timestamp": payload.ts,
                    },
                    timeout=3,
                )
        except Exception:
            pass
    return {"status": "ok", "persisted": True}


@router.post("/metrics/webvitals")
async def ingest_web_vitals(req: Request, metric: WebVitalMetric):
    """
    Ingest Web Vitals from frontend. Accepts payload from web-vitals library.

    Persists to Postgres if available (table `web_vitals`), otherwise no-ops.
    Never blocks UX due to DB errors.
    """
    ua = req.headers.get("user-agent", "")[:256]
    org_id = req.headers.get("X-Org-Id") or metric.org_id
    path = req.headers.get("x-path", None)
    if os.getenv("TEST_MODE") != "1" and getattr(postgres_client, "pool", None):
        try:
            async with postgres_client.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS web_vitals (
                        id BIGSERIAL PRIMARY KEY,
                        ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        metric_id VARCHAR(128),
                        name VARCHAR(32) NOT NULL,
                        value DOUBLE PRECISION NOT NULL,
                        rating VARCHAR(16),
                        navigation_type VARCHAR(32),
                        ua VARCHAR(256),
                        path VARCHAR(512),
                        org_id VARCHAR(64)
                    );
                    """
                )
                try:
                    await conn.execute(
                        """
                        INSERT INTO web_vitals (ts, metric_id, name, value, rating, navigation_type, ua, path, org_id)
                        VALUES (COALESCE(TO_TIMESTAMP($1/1000.0), NOW()), $2, $3, $4, $5, $6, $7, $8, $9)
                        """,
                        metric.ts,
                        metric.id,
                        metric.name,
                        metric.value,
                        metric.rating,
                        metric.navigationType,
                        ua,
                        path,
                        org_id,
                    )
                except Exception:
                    await conn.execute(
                        """
                        INSERT INTO web_vitals (ts, metric_id, name, value, rating, navigation_type, ua, path)
                        VALUES (COALESCE(TO_TIMESTAMP($1/1000.0), NOW()), $2, $3, $4, $5, $6, $7, $8)
                        """,
                        metric.ts,
                        metric.id,
                        metric.name,
                        metric.value,
                        metric.rating,
                        metric.navigationType,
                        ua,
                        path,
                    )
        except Exception:
            # swallow DB errors
            pass
    return {"status": "ok"}


@router.get("/analytics/kpis")
async def analytics_kpis(range: str = "day", org_id: Optional[str] = None, request: Request = None):
    """
    Returns basic KPIs over the selected time range:
    - total_events
    - unique_users (by user_id if present else session_id)
    - pageviews (event == 'page_view')
    """
    if range not in {"day", "week", "month"}:
        range = "day"
    if not getattr(postgres_client, "pool", None):
        return {"total_events": 0, "unique_users": 0, "pageviews": 0}
    window = {
        "day": "NOW() - INTERVAL '1 day'",
        "week": "NOW() - INTERVAL '7 day'",
        "month": "NOW() - INTERVAL '30 day'",
    }[range]
    # Prefer explicit query param, fallback to header
    if not org_id and request is not None:
        org_id = request.headers.get("X-Org-Id")
    async with postgres_client.acquire() as conn:
        if org_id:
            total_events = await conn.fetchval(
                f"SELECT COUNT(*) FROM web_events WHERE ts >= {window} AND org_id = $1",
                org_id,
            )
            unique_users = await conn.fetchval(
                f"SELECT COUNT(DISTINCT COALESCE(NULLIF(user_id,''), session_id)) FROM web_events WHERE ts >= {window} AND org_id = $1",
                org_id,
            )
            pageviews = await conn.fetchval(
                f"SELECT COUNT(*) FROM web_events WHERE ts >= {window} AND event = 'page_view' AND org_id = $1",
                org_id,
            )
        else:
            total_events = await conn.fetchval(
                f"SELECT COUNT(*) FROM web_events WHERE ts >= {window}"
            )
            unique_users = await conn.fetchval(
                f"SELECT COUNT(DISTINCT COALESCE(NULLIF(user_id,''), session_id)) FROM web_events WHERE ts >= {window}"
            )
            pageviews = await conn.fetchval(
                f"SELECT COUNT(*) FROM web_events WHERE ts >= {window} AND event = 'page_view'"
            )
    return {"total_events": int(total_events or 0), "unique_users": int(unique_users or 0), "pageviews": int(pageviews or 0)}


@router.get("/analytics/top-paths")
async def analytics_top_paths(limit: int = 20, org_id: Optional[str] = None, request: Request = None):
    if limit < 1 or limit > 100:
        limit = 20
    if not getattr(postgres_client, "pool", None):
        return {"paths": []}
    if not org_id and request is not None:
        org_id = request.headers.get("X-Org-Id")
    async with postgres_client.acquire() as conn:
        if org_id:
            rows = await conn.fetch(
                """
                SELECT path, COUNT(*) AS c
                FROM web_events
                WHERE path IS NOT NULL AND org_id = $1
                GROUP BY path
                ORDER BY c DESC
                LIMIT $2
                """,
                org_id,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT path, COUNT(*) AS c
                FROM web_events
                WHERE path IS NOT NULL
                GROUP BY path
                ORDER BY c DESC
                LIMIT $1
                """,
                limit,
            )
    return {"paths": [{"path": r["path"], "count": int(r["c"])} for r in rows]}


# ==========================================
# Onboarding Analytics Endpoints
# ==========================================

class OnboardingEvent(BaseModel):
    """Onboarding Event Model"""
    event_type: str = Field(..., pattern="^(tour_start|tour_complete|tour_skip|step_view|step_back|step_next)$")
    tour_id: str = Field(..., max_length=128)
    plan: str = Field(..., max_length=32)
    user_id: Optional[str] = Field(None, max_length=128)
    step_number: Optional[int] = Field(None, ge=0)
    total_steps: Optional[int] = Field(None, ge=0)
    completion_percentage: Optional[float] = Field(None, ge=0, le=100)
    timestamp: Optional[str] = None


class OnboardingStats(BaseModel):
    """Aggregierte Onboarding Statistics"""
    total_starts: int
    total_completions: int
    total_skips: int
    completion_rate: float
    average_steps_completed: float
    by_plan: Dict[str, Dict[str, Any]]


@router.post("/analytics/onboarding/event")
async def submit_onboarding_event(event: OnboardingEvent):
    """
    Submit Onboarding Event from Frontend
    
    Stores event in web_events table for centralized analytics.
    Available to all users (no auth required for frontend events).
    """
    if not getattr(postgres_client, "pool", None):
        return {"status": "accepted", "persisted": False}
    
    try:
        async with postgres_client.acquire() as conn:
            # Create onboarding_events table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS onboarding_events (
                    id BIGSERIAL PRIMARY KEY,
                    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    event_type VARCHAR(32) NOT NULL,
                    tour_id VARCHAR(128),
                    plan VARCHAR(32),
                    user_id VARCHAR(128),
                    step_number INTEGER,
                    total_steps INTEGER,
                    completion_percentage FLOAT,
                    properties JSONB
                )
            """)
            
            # Insert event
            await conn.execute("""
                INSERT INTO onboarding_events 
                (ts, event_type, tour_id, plan, user_id, step_number, total_steps, completion_percentage, properties)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                datetime.fromisoformat(event.timestamp) if event.timestamp else datetime.utcnow(),
                event.event_type,
                event.tour_id,
                event.plan,
                event.user_id,
                event.step_number,
                event.total_steps,
                event.completion_percentage,
                {}  # Additional properties can be added here
            )
        
        return {"status": "ok", "persisted": True}
    
    except Exception as e:
        # Swallow errors to not break UX
        return {"status": "accepted", "persisted": False, "error": str(e)}


@router.get("/analytics/onboarding/stats", response_model=OnboardingStats)
async def get_onboarding_stats(
    range: str = "month",
    plan: Optional[str] = None,
    user: dict = Depends(require_role("admin"))
):
    """
    Get Aggregated Onboarding Statistics
    
    Requires: Admin role
    
    Query Parameters:
    - range: day|week|month|all (default: month)
    - plan: Filter by specific plan (optional)
    
    Returns:
    - total_starts, total_completions, total_skips
    - completion_rate (%)
    - average_steps_completed
    - by_plan breakdown
    """
    if not getattr(postgres_client, "pool", None):
        return OnboardingStats(
            total_starts=0,
            total_completions=0,
            total_skips=0,
            completion_rate=0.0,
            average_steps_completed=0.0,
            by_plan={}
        )
    
    # Time window
    window_map = {
        "day": "NOW() - INTERVAL '1 day'",
        "week": "NOW() - INTERVAL '7 day'",
        "month": "NOW() - INTERVAL '30 day'",
        "all": "TO_TIMESTAMP(0)",
    }
    window = window_map.get(range, window_map["month"])
    
    async with postgres_client.acquire() as conn:
        # Overall stats
        if plan:
            total_starts = await conn.fetchval(
                f"SELECT COUNT(*) FROM onboarding_events WHERE event_type = 'tour_start' AND ts >= {window} AND plan = $1",
                plan
            )
            total_completions = await conn.fetchval(
                f"SELECT COUNT(*) FROM onboarding_events WHERE event_type = 'tour_complete' AND ts >= {window} AND plan = $1",
                plan
            )
            total_skips = await conn.fetchval(
                f"SELECT COUNT(*) FROM onboarding_events WHERE event_type = 'tour_skip' AND ts >= {window} AND plan = $1",
                plan
            )
        else:
            total_starts = await conn.fetchval(
                f"SELECT COUNT(*) FROM onboarding_events WHERE event_type = 'tour_start' AND ts >= {window}"
            )
            total_completions = await conn.fetchval(
                f"SELECT COUNT(*) FROM onboarding_events WHERE event_type = 'tour_complete' AND ts >= {window}"
            )
            total_skips = await conn.fetchval(
                f"SELECT COUNT(*) FROM onboarding_events WHERE event_type = 'tour_skip' AND ts >= {window}"
            )
        
        total_starts = int(total_starts or 0)
        total_completions = int(total_completions or 0)
        total_skips = int(total_skips or 0)
        
        # Completion rate
        completion_rate = (total_completions / total_starts * 100) if total_starts > 0 else 0.0
        
        # Average steps completed (from skip events)
        avg_steps = await conn.fetchval(
            f"SELECT AVG(step_number) FROM onboarding_events WHERE event_type = 'tour_skip' AND ts >= {window}"
        )
        average_steps_completed = float(avg_steps or 0.0)
        
        # By-plan breakdown
        plans_rows = await conn.fetch(f"""
            SELECT 
                plan,
                COUNT(*) FILTER (WHERE event_type = 'tour_start') as starts,
                COUNT(*) FILTER (WHERE event_type = 'tour_complete') as completions,
                COUNT(*) FILTER (WHERE event_type = 'tour_skip') as skips
            FROM onboarding_events
            WHERE ts >= {window}
            GROUP BY plan
        """)
        
        by_plan = {}
        for row in plans_rows:
            plan_name = row['plan']
            plan_starts = int(row['starts'] or 0)
            plan_completions = int(row['completions'] or 0)
            plan_skips = int(row['skips'] or 0)
            plan_rate = (plan_completions / plan_starts * 100) if plan_starts > 0 else 0.0
            
            by_plan[plan_name] = {
                'starts': plan_starts,
                'completions': plan_completions,
                'skips': plan_skips,
                'completion_rate': plan_rate
            }
    
    return OnboardingStats(
        total_starts=total_starts,
        total_completions=total_completions,
        total_skips=total_skips,
        completion_rate=completion_rate,
        average_steps_completed=average_steps_completed,
        by_plan=by_plan
    )


@router.get("/analytics/onboarding/events")
async def get_onboarding_events(
    limit: int = 100,
    event_type: Optional[str] = None,
    plan: Optional[str] = None,
    user: dict = Depends(require_role("admin"))
):
    """
    Get Raw Onboarding Events
    
    Requires: Admin role
    
    Query Parameters:
    - limit: Max events to return (default: 100, max: 1000)
    - event_type: Filter by event type (optional)
    - plan: Filter by plan (optional)
    
    Returns:
    - List of onboarding events (most recent first)
    """
    if limit < 1 or limit > 1000:
        limit = 100
    
    if not getattr(postgres_client, "pool", None):
        return {"events": []}
    
    async with postgres_client.acquire() as conn:
        # Build query
        query = "SELECT * FROM onboarding_events WHERE 1=1"
        params = []
        param_idx = 1
        
        if event_type:
            query += f" AND event_type = ${param_idx}"
            params.append(event_type)
            param_idx += 1
        
        if plan:
            query += f" AND plan = ${param_idx}"
            params.append(plan)
            param_idx += 1
        
        query += f" ORDER BY ts DESC LIMIT ${param_idx}"
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
    
    events = []
    for row in rows:
        events.append({
            'id': row['id'],
            'timestamp': row['ts'].isoformat(),
            'event_type': row['event_type'],
            'tour_id': row['tour_id'],
            'plan': row['plan'],
            'user_id': row['user_id'],
            'step_number': row['step_number'],
            'total_steps': row['total_steps'],
            'completion_percentage': row['completion_percentage'],
        })
    
    return {"events": events, "count": len(events)}


@router.get("/trend-data")
async def get_trend_data(
    timeframe: str = "7d",
    current_user: Dict = None
) -> Dict[str, Any]:
    """
    Get analytics trend data
    Admin Only
    
    Returns:
    - user_growth: New users over time
    - revenue: Revenue trends
    - activity: Platform activity metrics
    """
    from app.models.user import User
    
    # Check admin role
    if current_user and current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    try:
        # Mock trend data
        trends = {
            'user_growth': {
                'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'data': [5, 12, 8, 15, 20, 18, 25]
            },
            'revenue': {
                'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                'data': [1500, 2300, 1800, 2900]
            },
            'activity': {
                'traces': 150,
                'cases': 45,
                'api_calls': 5000
            }
        }
        
        return trends
    
    except Exception as e:
        logger.error(f"Error fetching trend data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


import logging
logger = logging.getLogger(__name__)


# ===================================
# ADVANCED ANALYTICS ENDPOINTS
# ===================================

from app.services.analytics_service import RealtimeAnalyticsService
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse


@router.get("/analytics/real-time")
async def get_real_time_metrics(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Get real-time system metrics"""
    service = RealtimeAnalyticsService(db)
    return service.get_real_time_metrics()


@router.get("/analytics/threat-categories")
async def get_threat_categories(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Get top threat categories"""
    service = RealtimeAnalyticsService(db)
    
    # Parse dates
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    return service.get_top_threat_categories(start, end, limit)


@router.get("/analytics/risk-distribution")
async def get_risk_distribution(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "day",
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Get risk score distribution over time"""
    service = RealtimeAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    return service.get_risk_distribution_over_time(start, end, interval)


@router.get("/analytics/geographic")
async def get_geographic_distribution(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Get geographic distribution of threats"""
    service = RealtimeAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    return service.get_geographic_distribution(start, end)


@router.get("/analytics/top-entities/{entity_type}")
async def get_top_entities(
    entity_type: str,
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Get top exchanges or mixers"""
    if entity_type not in ['exchange', 'mixer']:
        raise HTTPException(status_code=400, detail="entity_type must be 'exchange' or 'mixer'")
    
    service = RealtimeAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    return service.get_entity_flow(entity_type, start, end, limit)


@router.get("/analytics/comparison")
async def get_comparison(
    request: Request,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Compare two time periods"""
    service = RealtimeAnalyticsService(db)
    
    p1_start = datetime.fromisoformat(period1_start)
    p1_end = datetime.fromisoformat(period1_end)
    p2_start = datetime.fromisoformat(period2_start)
    p2_end = datetime.fromisoformat(period2_end)
    
    return service.get_comparison_data(p1_start, p1_end, p2_start, p2_end)


@router.get("/analytics/drill-down/{category}")
async def drill_down_category(
    category: str,
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Drill down into specific threat category"""
    service = RealtimeAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    return service.get_category_drilldown(category, start, end, limit)


@router.get("/analytics/export/csv")
async def export_csv(
    request: Request,
    data_type: str,  # 'threat_categories', 'risk_distribution', etc.
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Export data as CSV"""
    service = RealtimeAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    # Get data based on type
    if data_type == 'threat_categories':
        data = service.get_top_threat_categories(start, end, limit=100)
    elif data_type == 'risk_distribution':
        data = service.get_risk_distribution_over_time(start, end)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown data_type: {data_type}")
    
    # Export to CSV
    buffer = service.export_to_csv(data)
    
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=analytics_{data_type}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/analytics/export/excel")
async def export_excel(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """Export comprehensive analytics as Excel with multiple sheets"""
    service = RealtimeAnalyticsService(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    # Gather multiple datasets
    data_sheets = {
        'Threat Categories': service.get_top_threat_categories(start, end, limit=100),
        'Risk Distribution': service.get_risk_distribution_over_time(start, end),
        'Top Exchanges': service.get_top_entities('exchange', start, end, limit=50),
        'Top Mixers': service.get_top_entities('mixer', start, end, limit=50),
        'Geographic': service.get_geographic_distribution(start, end),
    }
    
    # Export to Excel
    buffer = service.export_to_excel(data_sheets)
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=analytics_report_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
        }
    )
