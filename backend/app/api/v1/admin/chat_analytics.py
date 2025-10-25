"""
Admin-Endpoint für Chat-Analytics
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Literal
from app.db.session import get_db
from app.models.chat_feedback import ChatFeedback, FeedbackType
from app.api.dependencies import get_current_admin_user

router = APIRouter()


@router.get("/chat-analytics", summary="Chat-Analytics für Admin-Dashboard")
async def get_chat_analytics(
    range: Literal['24h', '7d', '30d'] = Query('24h', description="Zeitraum"),
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Liefert Chat-Analytics für Admin-Dashboard.
    
    **Nur für Admins zugänglich**
    
    Returns:
    - total_conversations: Anzahl unique Sessions
    - total_messages: Anzahl Feedback-Einträge (approximation)
    - positive_feedback: Anzahl positive Bewertungen
    - negative_feedback: Anzahl negative Bewertungen
    - avg_messages_per_conversation: Durchschnitt
    - active_sessions_24h: Sessions in letzten 24h
    - top_intents: Häufigste Intents (placeholder)
    - hourly_distribution: Messages pro Stunde
    """
    
    # Calculate time range
    now = datetime.utcnow()
    if range == '24h':
        start_time = now - timedelta(hours=24)
    elif range == '7d':
        start_time = now - timedelta(days=7)
    else:  # 30d
        start_time = now - timedelta(days=30)
    
    # Total conversations (unique sessions)
    total_conversations = db.query(func.count(func.distinct(ChatFeedback.session_id)))\
        .filter(ChatFeedback.created_at >= start_time)\
        .scalar() or 0
    
    # Total messages (same as feedback count for now)
    total_messages = db.query(func.count(ChatFeedback.id))\
        .filter(ChatFeedback.created_at >= start_time)\
        .scalar() or 0
    
    # Positive feedback
    positive_feedback = db.query(func.count(ChatFeedback.id))\
        .filter(
            ChatFeedback.created_at >= start_time,
            ChatFeedback.feedback_type == FeedbackType.POSITIVE
        )\
        .scalar() or 0
    
    # Negative feedback
    negative_feedback = db.query(func.count(ChatFeedback.id))\
        .filter(
            ChatFeedback.created_at >= start_time,
            ChatFeedback.feedback_type == FeedbackType.NEGATIVE
        )\
        .scalar() or 0
    
    # Average messages per conversation
    avg_messages = (total_messages / total_conversations) if total_conversations > 0 else 0
    
    # Active sessions in last 24h
    active_sessions_24h = db.query(func.count(func.distinct(ChatFeedback.session_id)))\
        .filter(ChatFeedback.created_at >= (now - timedelta(hours=24)))\
        .scalar() or 0
    
    # Hourly distribution (für 24h-Ansicht)
    hourly_data = []
    for hour in range(24):
        hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=23-hour)
        hour_end = hour_start + timedelta(hours=1)
        
        count = db.query(func.count(ChatFeedback.id))\
            .filter(
                ChatFeedback.created_at >= hour_start,
                ChatFeedback.created_at < hour_end
            )\
            .scalar() or 0
        
        hourly_data.append({
            "hour": hour,
            "count": count
        })
    
    # Top intents (placeholder - würde Intent-Tracking brauchen)
    top_intents = [
        {"intent": "Transaction Tracing", "count": 45},
        {"intent": "Address Lookup", "count": 32},
        {"intent": "Wallet Scanner", "count": 28},
        {"intent": "Risk Analysis", "count": 21},
        {"intent": "Compliance Check", "count": 18}
    ]
    
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback,
        "avg_messages_per_conversation": round(avg_messages, 1),
        "active_sessions_24h": active_sessions_24h,
        "top_intents": top_intents,
        "hourly_distribution": hourly_data
    }
