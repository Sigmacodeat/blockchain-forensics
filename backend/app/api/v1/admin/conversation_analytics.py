"""
Advanced Conversation-Analytics API
Für Admin-Dashboard: Deep-Dive in User-Journey, Conversion-Funnel, AI-Insights
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.auth.dependencies import require_admin
from app.models.chat_session import ChatSession, ChatMessage, ConversationEvent
from app.services.conversation_analytics import (
    ConversationAnalytics,
    UserIdentityResolver
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/conversation-analytics", tags=["Admin - Conversation Analytics"])


@router.get("/overview")
async def get_conversation_overview(
    days: int = Query(7, description="Zeitraum in Tagen"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Conversation-Overview für Admin-Dashboard
    
    Returns:
    - total_sessions: Anzahl Sessions
    - total_messages: Anzahl Messages
    - total_users: Unique Users (anonymous + authenticated)
    - avg_messages_per_session: Durchschnitt
    - avg_session_duration: Durchschnittliche Dauer
    - returning_users: % Wiederkehrende User
    - conversion_rate: % Sessions mit Conversion-Event
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()
    
    # Total sessions
    total_sessions = db.query(func.count(ChatSession.id)).filter(
        ChatSession.created_at >= start_date
    ).scalar() or 0
    
    # Total messages
    total_messages = db.query(func.count(ChatMessage.id)).join(ChatSession).filter(
        ChatSession.created_at >= start_date
    ).scalar() or 0
    
    # Total unique users (anonymous_id + user_id)
    total_anonymous = db.query(func.count(func.distinct(ChatSession.anonymous_id))).filter(
        and_(
            ChatSession.created_at >= start_date,
            ChatSession.anonymous_id.isnot(None)
        )
    ).scalar() or 0
    
    total_authenticated = db.query(func.count(func.distinct(ChatSession.user_id))).filter(
        and_(
            ChatSession.created_at >= start_date,
            ChatSession.user_id.isnot(None)
        )
    ).scalar() or 0
    
    total_users = total_anonymous + total_authenticated
    
    # Avg messages per session
    avg_messages = round(total_messages / total_sessions, 1) if total_sessions > 0 else 0
    
    # Returning users (users mit >1 session)
    returning_users_count = db.query(ChatSession.anonymous_id).filter(
        and_(
            ChatSession.created_at >= start_date,
            ChatSession.anonymous_id.isnot(None)
        )
    ).group_by(ChatSession.anonymous_id).having(
        func.count(ChatSession.id) > 1
    ).count()
    
    returning_rate = round((returning_users_count / total_users * 100) if total_users > 0 else 0, 1)
    
    # Conversion rate (sessions mit payment_completed oder signup_completed)
    converted_sessions = db.query(func.count(func.distinct(ConversationEvent.session_id))).filter(
        and_(
            ConversationEvent.timestamp >= start_date,
            ConversationEvent.event_type.in_(['payment_completed', 'signup_completed'])
        )
    ).scalar() or 0
    
    conversion_rate = round((converted_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1)
    
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "total_users": total_users,
        "avg_messages_per_session": avg_messages,
        "returning_users_count": returning_users_count,
        "returning_users_rate": returning_rate,
        "converted_sessions": converted_sessions,
        "conversion_rate": conversion_rate,
        "period_days": days
    }


@router.get("/funnel")
async def get_conversion_funnel(
    days: int = Query(30, description="Zeitraum in Tagen"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Conversion-Funnel-Analyse
    
    Returns kompletten Funnel:
    Landing → Chat → Demo → Trial → Payment → Signup
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()
    
    funnel = ConversationAnalytics.calculate_funnel_metrics(db, start_date, end_date)
    
    return funnel


@router.get("/sessions")
async def get_sessions(
    skip: int = Query(0, description="Offset"),
    limit: int = Query(50, description="Limit"),
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    anonymous_id: Optional[str] = Query(None, description="Filter by anonymous_id"),
    has_conversion: Optional[bool] = Query(None, description="Filter by conversion"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Liste aller Chat-Sessions mit Metadata
    
    Returns:
    - sessions: List[Session-Details]
    - total: Total count
    """
    query = db.query(ChatSession)
    
    # Filters
    if user_id:
        query = query.filter(ChatSession.user_id == user_id)
    if anonymous_id:
        query = query.filter(ChatSession.anonymous_id == anonymous_id)
    if has_conversion is not None:
        if has_conversion:
            # Sessions mit Conversion-Events
            query = query.join(ConversationEvent).filter(
                ConversationEvent.event_type.in_(['payment_completed', 'signup_completed'])
            )
        else:
            # Sessions ohne Conversion
            query = query.outerjoin(ConversationEvent).filter(
                ConversationEvent.id.is_(None)
            )
    
    total = query.count()
    sessions = query.order_by(desc(ChatSession.created_at)).offset(skip).limit(limit).all()
    
    # Serialize sessions
    sessions_data = []
    for session in sessions:
        # Count messages
        message_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.session_id == session.id
        ).scalar() or 0
        
        # Get events
        events = db.query(ConversationEvent).filter(
            ConversationEvent.session_id == session.id
        ).order_by(ConversationEvent.timestamp).all()
        
        sessions_data.append({
            "id": session.id,
            "user_id": session.user_id,
            "anonymous_id": session.anonymous_id,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "fingerprint": session.fingerprint,
            "utm_source": session.utm_source,
            "utm_medium": session.utm_medium,
            "utm_campaign": session.utm_campaign,
            "referrer": session.referrer,
            "language": session.language,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "is_active": session.is_active,
            "message_count": message_count,
            "events": [
                {
                    "type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.event_data
                }
                for event in events
            ]
        })
    
    return {
        "sessions": sessions_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Detaillierte Session-Ansicht mit allen Messages & Events
    
    Für Deep-Dive-Analyse im Admin-Dashboard
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Get all messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp).all()
    
    # Get all events
    events = db.query(ConversationEvent).filter(
        ConversationEvent.session_id == session_id
    ).order_by(ConversationEvent.timestamp).all()
    
    # Resolve user identity
    identity = UserIdentityResolver.resolve_user_identity(
        db,
        session_id=session.id,
        user_id=session.user_id,
        anonymous_id=session.anonymous_id,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        fingerprint=session.fingerprint
    )
    
    # Classify intent
    message_dicts = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    # Simple sync intent classification (can be upgraded to async GPT-4)
    intent = "unknown"
    user_messages = [msg.content for msg in messages if msg.role == 'user']
    if user_messages:
        text = " ".join(user_messages).lower()
        if any(kw in text for kw in ['demo', 'show me']):
            intent = "demo_request"
        elif any(kw in text for kw in ['price', 'cost', 'pricing']):
            intent = "pricing_question"
        elif any(kw in text for kw in ['trial', 'test']):
            intent = "trial_signup"
        elif any(kw in text for kw in ['pay', 'payment', 'crypto']):
            intent = "payment_help"
    
    return {
        "session": {
            "id": session.id,
            "user_id": session.user_id,
            "anonymous_id": session.anonymous_id,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "fingerprint": session.fingerprint,
            "utm_params": {
                "source": session.utm_source,
                "medium": session.utm_medium,
                "campaign": session.utm_campaign,
                "term": session.utm_term,
                "content": session.utm_content
            },
            "referrer": session.referrer,
            "language": session.language,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "is_active": session.is_active
        },
        "identity": identity,
        "intent": intent,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in messages
        ],
        "events": [
            {
                "id": event.id,
                "type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.event_data
            }
            for event in events
        ]
    }


@router.get("/intents")
async def get_intent_distribution(
    days: int = Query(30, description="Zeitraum in Tagen"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Intent-Distribution (wie viele Sessions pro Intent)
    
    Returns:
    {
        "demo_request": 125,
        "pricing_question": 89,
        "trial_signup": 67,
        "payment_help": 45,
        "technical_support": 23,
        ...
    }
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all sessions mit Messages
    sessions = db.query(ChatSession).filter(
        ChatSession.created_at >= start_date
    ).all()
    
    intent_counts = {}
    
    for session in sessions:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).all()
        
        # Classify intent
        user_messages = [msg.content for msg in messages if msg.role == 'user']
        if not user_messages:
            continue
        
        text = " ".join(user_messages).lower()
        
        intent = "general_inquiry"
        if any(kw in text for kw in ['demo', 'show me', 'example']):
            intent = "demo_request"
        elif any(kw in text for kw in ['price', 'cost', 'pricing', 'how much']):
            intent = "pricing_question"
        elif any(kw in text for kw in ['trial', 'test', 'try', 'free']):
            intent = "trial_signup"
        elif any(kw in text for kw in ['pay', 'payment', 'crypto', 'bitcoin']):
            intent = "payment_help"
        elif any(kw in text for kw in ['chainalysis', 'trm', 'elliptic', 'compare']):
            intent = "competitor_comparison"
        elif any(kw in text for kw in ['feature', 'support', 'can you']):
            intent = "product_inquiry"
        elif any(kw in text for kw in ['problem', 'error', 'not working']):
            intent = "technical_support"
        
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    return {
        "intents": intent_counts,
        "total_sessions": len(sessions),
        "period_days": days
    }


@router.get("/attribution")
async def get_attribution_report(
    days: int = Query(30, description="Zeitraum in Tagen"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Attribution-Report: Welche Traffic-Sources konvertieren am besten?
    
    Returns:
    {
        "by_source": {"google": 123, "twitter": 45, ...},
        "by_medium": {"cpc": 89, "organic": 67, ...},
        "by_campaign": {"summer_2025": 34, ...}
    }
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Sessions by UTM-Source
    source_stats = db.query(
        ChatSession.utm_source,
        func.count(ChatSession.id).label('count')
    ).filter(
        and_(
            ChatSession.created_at >= start_date,
            ChatSession.utm_source.isnot(None)
        )
    ).group_by(ChatSession.utm_source).all()
    
    # Sessions by UTM-Medium
    medium_stats = db.query(
        ChatSession.utm_medium,
        func.count(ChatSession.id).label('count')
    ).filter(
        and_(
            ChatSession.created_at >= start_date,
            ChatSession.utm_medium.isnot(None)
        )
    ).group_by(ChatSession.utm_medium).all()
    
    # Sessions by UTM-Campaign
    campaign_stats = db.query(
        ChatSession.utm_campaign,
        func.count(ChatSession.id).label('count')
    ).filter(
        and_(
            ChatSession.created_at >= start_date,
            ChatSession.utm_campaign.isnot(None)
        )
    ).group_by(ChatSession.utm_campaign).all()
    
    # Sessions by Referrer
    referrer_stats = db.query(
        ChatSession.referrer,
        func.count(ChatSession.id).label('count')
    ).filter(
        and_(
            ChatSession.created_at >= start_date,
            ChatSession.referrer.isnot(None)
        )
    ).group_by(ChatSession.referrer).order_by(desc('count')).limit(10).all()
    
    return {
        "by_source": {stat.utm_source: stat.count for stat in source_stats},
        "by_medium": {stat.utm_medium: stat.count for stat in medium_stats},
        "by_campaign": {stat.utm_campaign: stat.count for stat in campaign_stats},
        "top_referrers": [{"url": stat.referrer, "count": stat.count} for stat in referrer_stats],
        "period_days": days
    }
