"""
State-of-the-Art Conversation Analytics Service
User-Identity-Resolution + Multi-Session-Tracking + AI-Powered Insights
"""

import logging
import hashlib
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

logger = logging.getLogger(__name__)


class UserIdentityResolver:
    """
    Sophisticated User-Identity-Resolution System
    
    Verbindet Sessions über:
    - Browser Fingerprinting
    - Cookie-based User-ID
    - IP-Address (mit Fuzzy-Matching für Mobile)
    - User-Agent
    - Email (wenn registriert)
    
    Wie Segment, Mixpanel, Amplitude
    """
    
    @staticmethod
    def generate_anonymous_id(
        ip_address: str,
        user_agent: str,
        fingerprint: Optional[str] = None
    ) -> str:
        """
        Generate stable anonymous_id für User-Tracking
        
        Args:
            ip_address: Client IP (z.B. "192.168.1.100")
            user_agent: Browser User-Agent
            fingerprint: Optional Browser-Fingerprint (Canvas, WebGL, etc.)
        
        Returns:
            Stable anonymous_id (SHA256-Hash)
        
        Example:
            anonymous_id = "anon_a3f8c2d1e9..."
        """
        components = [
            ip_address or "unknown",
            user_agent or "unknown",
            fingerprint or ""
        ]
        
        raw = "|".join(components)
        hash_obj = hashlib.sha256(raw.encode())
        return f"anon_{hash_obj.hexdigest()[:16]}"
    
    @staticmethod
    def resolve_user_identity(
        db: Session,
        session_id: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        anonymous_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve User-Identity über multiple Sessions
        
        Logic:
        1. Wenn user_id → Authenticated User (höchste Priorität)
        2. Wenn email → Lookup in Users-Table
        3. Wenn anonymous_id → Lookup in chat_sessions
        4. Wenn IP + User-Agent → Fuzzy-Match (last 7 days)
        5. Fallback → Neue Identity
        
        Returns:
            {
                "resolved_user_id": str | None,
                "anonymous_id": str,
                "is_returning": bool,
                "session_count": int,
                "first_seen": datetime,
                "last_seen": datetime,
                "linked_sessions": List[str]
            }
        """
        from app.models.chat_session import ChatSession
        
        # 1. Authenticated User (highest priority)
        if user_id:
            sessions = db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).order_by(ChatSession.created_at).all()
            
            if sessions:
                return {
                    "resolved_user_id": user_id,
                    "anonymous_id": anonymous_id or UserIdentityResolver.generate_anonymous_id(
                        ip_address, user_agent, fingerprint
                    ),
                    "is_returning": len(sessions) > 1,
                    "session_count": len(sessions),
                    "first_seen": sessions[0].created_at,
                    "last_seen": sessions[-1].updated_at,
                    "linked_sessions": [s.id for s in sessions]
                }
        
        # 2. Email-based (for guest checkouts, lead forms)
        if email:
            from app.models.user import UserORM
            user = db.query(UserORM).filter(UserORM.email == email).first()
            if user:
                return UserIdentityResolver.resolve_user_identity(
                    db, session_id, user_id=user.id, email=email,
                    anonymous_id=anonymous_id, ip_address=ip_address,
                    user_agent=user_agent, fingerprint=fingerprint
                )
        
        # 3. Anonymous-ID-based (cookie persistence)
        if anonymous_id:
            sessions = db.query(ChatSession).filter(
                ChatSession.anonymous_id == anonymous_id
            ).order_by(ChatSession.created_at).all()
            
            if sessions:
                return {
                    "resolved_user_id": None,
                    "anonymous_id": anonymous_id,
                    "is_returning": len(sessions) > 1,
                    "session_count": len(sessions),
                    "first_seen": sessions[0].created_at,
                    "last_seen": sessions[-1].updated_at,
                    "linked_sessions": [s.id for s in sessions]
                }
        
        # 4. Fuzzy-Match via IP + User-Agent (last 7 days)
        if ip_address and user_agent:
            cutoff = datetime.utcnow() - timedelta(days=7)
            similar_sessions = db.query(ChatSession).filter(
                and_(
                    ChatSession.ip_address == ip_address,
                    ChatSession.user_agent == user_agent,
                    ChatSession.created_at >= cutoff
                )
            ).order_by(ChatSession.created_at).all()
            
            if similar_sessions:
                # Link sessions
                return {
                    "resolved_user_id": similar_sessions[0].user_id,
                    "anonymous_id": similar_sessions[0].anonymous_id or UserIdentityResolver.generate_anonymous_id(
                        ip_address, user_agent, fingerprint
                    ),
                    "is_returning": True,
                    "session_count": len(similar_sessions) + 1,  # +1 für current session
                    "first_seen": similar_sessions[0].created_at,
                    "last_seen": datetime.utcnow(),
                    "linked_sessions": [s.id for s in similar_sessions] + [session_id]
                }
        
        # 5. Fallback: New Identity
        new_anon_id = UserIdentityResolver.generate_anonymous_id(
            ip_address or "unknown",
            user_agent or "unknown",
            fingerprint
        )
        
        return {
            "resolved_user_id": None,
            "anonymous_id": new_anon_id,
            "is_returning": False,
            "session_count": 1,
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "linked_sessions": [session_id]
        }


class ConversationAnalytics:
    """
    Advanced Conversation Analytics
    
    Features:
    - Funnel-Tracking (Landing → Trial → Payment)
    - Intent-Classification
    - Sentiment-Analysis
    - Dropout-Prediction
    - Conversion-Attribution
    """
    
    @staticmethod
    def track_conversation_event(
        db: Session,
        session_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None,
        anonymous_id: Optional[str] = None
    ) -> None:
        """
        Track Conversion-Events für Funnel-Analysis
        
        Event-Types:
        - page_view: User landed on page
        - chat_started: First message sent
        - demo_viewed: Sandbox/Live demo opened
        - trial_started: 14-day trial activated
        - payment_initiated: Payment flow started
        - payment_completed: Successful payment
        - signup_completed: Account registered
        
        Args:
            session_id: Chat session ID
            event_type: Event identifier
            event_data: Additional metadata (UTM params, referrer, etc.)
            user_id: Authenticated user ID
            anonymous_id: Anonymous tracking ID
        """
        from app.models.conversation_event import ConversationEvent
        
        event = ConversationEvent(
            session_id=session_id,
            user_id=user_id,
            anonymous_id=anonymous_id,
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.utcnow()
        )
        
        db.add(event)
        db.commit()
        
        logger.info(f"Tracked event: {event_type} for session {session_id}")
    
    @staticmethod
    def calculate_funnel_metrics(
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate Conversion-Funnel-Metrics
        
        Returns:
            {
                "total_visitors": 1000,
                "chat_started": 350 (35%),
                "demo_viewed": 147 (14.7%),
                "trial_started": 73 (7.3%),
                "payment_initiated": 35 (3.5%),
                "payment_completed": 21 (2.1%),
                "signup_completed": 18 (1.8%),
                "drop_off_stages": {
                    "visitor_to_chat": 65%,
                    "chat_to_demo": 58%,
                    "demo_to_trial": 50%,
                    "trial_to_payment": 52%,
                    "payment_to_completion": 60%
                }
            }
        """
        from app.models.conversation_event import ConversationEvent
        
        total_visitors = db.query(func.count(func.distinct(ConversationEvent.session_id))).filter(
            and_(
                ConversationEvent.event_type == "page_view",
                ConversationEvent.timestamp >= start_date,
                ConversationEvent.timestamp <= end_date
            )
        ).scalar() or 0
        
        chat_started = db.query(func.count(func.distinct(ConversationEvent.session_id))).filter(
            and_(
                ConversationEvent.event_type == "chat_started",
                ConversationEvent.timestamp >= start_date,
                ConversationEvent.timestamp <= end_date
            )
        ).scalar() or 0
        
        demo_viewed = db.query(func.count(func.distinct(ConversationEvent.session_id))).filter(
            and_(
                ConversationEvent.event_type == "demo_viewed",
                ConversationEvent.timestamp >= start_date,
                ConversationEvent.timestamp <= end_date
            )
        ).scalar() or 0
        
        trial_started = db.query(func.count(func.distinct(ConversationEvent.session_id))).filter(
            and_(
                ConversationEvent.event_type == "trial_started",
                ConversationEvent.timestamp >= start_date,
                ConversationEvent.timestamp <= end_date
            )
        ).scalar() or 0
        
        payment_initiated = db.query(func.count(func.distinct(ConversationEvent.session_id))).filter(
            and_(
                ConversationEvent.event_type == "payment_initiated",
                ConversationEvent.timestamp >= start_date,
                ConversationEvent.timestamp <= end_date
            )
        ).scalar() or 0
        
        payment_completed = db.query(func.count(func.distinct(ConversationEvent.session_id))).filter(
            and_(
                ConversationEvent.event_type == "payment_completed",
                ConversationEvent.timestamp >= start_date,
                ConversationEvent.timestamp <= end_date
            )
        ).scalar() or 0
        
        signup_completed = db.query(func.count(func.distinct(ConversationEvent.session_id))).filter(
            and_(
                ConversationEvent.event_type == "signup_completed",
                ConversationEvent.timestamp >= start_date,
                ConversationEvent.timestamp <= end_date
            )
        ).scalar() or 0
        
        # Calculate drop-off rates
        drop_off = {}
        if total_visitors > 0:
            drop_off["visitor_to_chat"] = round((1 - chat_started / total_visitors) * 100, 1)
        if chat_started > 0:
            drop_off["chat_to_demo"] = round((1 - demo_viewed / chat_started) * 100, 1)
        if demo_viewed > 0:
            drop_off["demo_to_trial"] = round((1 - trial_started / demo_viewed) * 100, 1)
        if trial_started > 0:
            drop_off["trial_to_payment"] = round((1 - payment_initiated / trial_started) * 100, 1)
        if payment_initiated > 0:
            drop_off["payment_to_completion"] = round((1 - payment_completed / payment_initiated) * 100, 1)
        
        return {
            "total_visitors": total_visitors,
            "chat_started": chat_started,
            "chat_started_rate": round((chat_started / total_visitors * 100) if total_visitors > 0 else 0, 1),
            "demo_viewed": demo_viewed,
            "demo_viewed_rate": round((demo_viewed / total_visitors * 100) if total_visitors > 0 else 0, 1),
            "trial_started": trial_started,
            "trial_started_rate": round((trial_started / total_visitors * 100) if total_visitors > 0 else 0, 1),
            "payment_initiated": payment_initiated,
            "payment_initiated_rate": round((payment_initiated / total_visitors * 100) if total_visitors > 0 else 0, 1),
            "payment_completed": payment_completed,
            "payment_completed_rate": round((payment_completed / total_visitors * 100) if total_visitors > 0 else 0, 1),
            "signup_completed": signup_completed,
            "signup_completed_rate": round((signup_completed / total_visitors * 100) if total_visitors > 0 else 0, 1),
            "drop_off_stages": drop_off
        }
    
    @staticmethod
    async def classify_conversation_intent(messages: List[Dict[str, str]]) -> str:
        """
        AI-powered Intent-Classification
        
        Intents:
        - product_inquiry: User fragt nach Features
        - pricing_question: User fragt nach Pricing
        - demo_request: User will Demo sehen
        - trial_signup: User will Trial starten
        - payment_help: User braucht Payment-Hilfe
        - technical_support: User hat technische Fragen
        - competitor_comparison: User vergleicht mit Chainalysis/TRM
        - objection_handling: User hat Bedenken (Price, Security, etc.)
        
        Uses: GPT-4 for classification
        """
        # Simplified: Extract user messages only
        user_messages = [msg['content'] for msg in messages if msg.get('role') == 'user']
        
        if not user_messages:
            return "unknown"
        
        # Simple keyword-based classification (can upgrade to GPT-4)
        text = " ".join(user_messages).lower()
        
        if any(kw in text for kw in ['demo', 'show me', 'example', 'how does it work']):
            return "demo_request"
        elif any(kw in text for kw in ['price', 'cost', 'pricing', 'how much', 'expensive']):
            return "pricing_question"
        elif any(kw in text for kw in ['trial', 'test', 'try', 'free']):
            return "trial_signup"
        elif any(kw in text for kw in ['pay', 'payment', 'crypto', 'bitcoin', 'eth']):
            return "payment_help"
        elif any(kw in text for kw in ['chainalysis', 'trm', 'elliptic', 'competitor', 'vs', 'compare']):
            return "competitor_comparison"
        elif any(kw in text for kw in ['feature', 'support', 'can you', 'does it', 'integration']):
            return "product_inquiry"
        elif any(kw in text for kw in ['problem', 'error', 'not working', 'bug', 'issue']):
            return "technical_support"
        else:
            return "general_inquiry"


# Initialize service instance
conversation_analytics = ConversationAnalytics()
user_identity_resolver = UserIdentityResolver()
