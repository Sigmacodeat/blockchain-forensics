"""
Usage-Tracking-Service für Token-basierte Abrechnung
=====================================================

Features:
- Tracked alle API-Calls automatisch
- Berechnet Token-Cost pro Feature
- Enforced Monthly Quotas
- Gibt Breakdowns nach Feature
- Logged in PostgreSQL für Audit
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from app.config import settings
from app.db.redis_client import redis_client
from app.db.postgres_client import postgres_client
from app.services.partner_service import partner_service

logger = logging.getLogger(__name__)


# ============================================================================
# TOKEN-KOSTEN PRO FEATURE
# ============================================================================

TOKEN_COSTS = {
    "trace_start": 10,
    "trace_expand": 5,
    "graph_query": 3,
    "pattern_detection": 8,
    "ai_agent_query": 5,
    "risk_score": 2,
    "wallet_scan": 7,
    "report_generate": 4,
    "case_create": 3,
    "case_update": 1,
    "webhook_trigger": 2
}


# ============================================================================
# MONTHLY QUOTAS PRO PLAN
# ============================================================================

PLAN_QUOTAS = {
    "community": 100,      # 100 Tokens/Monat
    "starter": 500,        # 500 Tokens/Monat
    "pro": -1,             # Unlimited
    "business": -1,        # Unlimited
    "plus": -1,            # Unlimited
    "enterprise": -1       # Unlimited
}


# ============================================================================
# USAGE-TRACKING-SERVICE
# ============================================================================

class UsageTrackingService:
    """
    Service für Usage-Tracking & Quota-Enforcement
    
    Features:
    - Auto-Tracking aller API-Calls
    - Token-basierte Abrechnung
    - Monthly Quota-Enforcement
    - Feature-Breakdown
    - Audit-Logging in PostgreSQL
    """
    
    def __init__(self):
        self.redis = redis_client
        self.db = postgres_client
    
    async def track_api_call(
        self,
        user_id: str,
        feature: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Tracked einen API-Call und berechnet Token-Cost
        
        Args:
            user_id: User-ID
            feature: Feature-Name (z.B. 'trace_start')
            metadata: Optional metadata (endpoint, method, etc.)
        
        Returns:
            {
                "tokens_used": 10,
                "tokens_total": 90,
                "quota_exceeded": False
            }
        """
        try:
            tokens = TOKEN_COSTS.get(feature, 1)
            
            # Aktuellen Usage aus Redis holen
            month_key = f"usage:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
            current_usage = int(await self.redis.get(month_key) or 0)
            
            # Add tokens
            new_usage = current_usage + tokens
            await self.redis.set(month_key, new_usage)
            await self.redis.expire(month_key, 60 * 60 * 24 * 35)  # 35 Tage TTL
            
            # Feature-spezifisches Tracking
            feature_key = f"usage:{user_id}:{datetime.utcnow().strftime('%Y-%m')}:{feature}"
            await self.redis.incr(feature_key)
            await self.redis.expire(feature_key, 60 * 60 * 24 * 35)
            
            # PostgreSQL für Audit (async in background)
            try:
                await self._log_to_postgres(user_id, feature, tokens, metadata)
            except Exception as e:
                logger.warning(f"Failed to log to PostgreSQL: {e}")
            # Partner nutzungsbasierte Provision (best-effort)
            try:
                await partner_service.record_commission_on_usage(user_id=user_id, feature=feature, tokens=tokens)
            except Exception:
                pass
            
            return {
                "tokens_used": tokens,
                "tokens_total": new_usage,
                "quota_exceeded": False
            }
        
        except Exception as e:
            logger.error(f"Error tracking API call: {e}")
            # Fallback: Tracke nicht, aber blockiere nicht
            return {
                "tokens_used": 0,
                "tokens_total": 0,
                "quota_exceeded": False
            }
    
    async def check_quota(self, user_id: str, plan: str) -> bool:
        """
        Prüft ob User noch Quota hat
        
        Args:
            user_id: User-ID
            plan: Plan-Name (z.B. 'pro')
        
        Returns:
            True wenn OK, False wenn Quota exceeded
        """
        try:
            quota = PLAN_QUOTAS.get(plan, 100)
            
            # Unlimited Plans
            if quota == -1:
                return True
            
            # Check aktuellen Usage
            month_key = f"usage:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
            current_usage = int(await self.redis.get(month_key) or 0)
            
            return current_usage < quota
        
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            # Bei Fehler: Erlaube Request (fail-open)
            return True
    
    async def get_usage_breakdown(self, user_id: str) -> Dict[str, int]:
        """
        Gibt Usage-Breakdown nach Feature zurück
        
        Args:
            user_id: User-ID
        
        Returns:
            {
                "trace_start": 50,
                "ai_agent_query": 25,
                "graph_query": 15,
                "total": 90
            }
        """
        try:
            month = datetime.utcnow().strftime('%Y-%m')
            pattern = f"usage:{user_id}:{month}:*"
            
            breakdown = {}
            total = 0
            
            # Scan alle Feature-Keys
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                
                for key in keys:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    parts = key_str.split(":")
                    
                    # Format: usage:user_id:YYYY-MM:feature
                    if len(parts) == 4:
                        feature = parts[3]
                        count = int(await self.redis.get(key) or 0)
                        tokens = count * TOKEN_COSTS.get(feature, 1)
                        breakdown[feature] = tokens
                        total += tokens
                
                if cursor == 0:
                    break
            
            breakdown["total"] = total
            return breakdown
        
        except Exception as e:
            logger.error(f"Error getting usage breakdown: {e}")
            return {"total": 0}
    
    async def get_current_usage(self, user_id: str, plan: str) -> Dict[str, Any]:
        """
        Gibt aktuellen Usage zurück
        
        Args:
            user_id: User-ID
            plan: Plan-Name
        
        Returns:
            {
                "tokens_used": 90,
                "quota": 100,
                "quota_percentage": 90.0,
                "resets_at": "2025-11-01T00:00:00Z"
            }
        """
        try:
            month_key = f"usage:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
            current_usage = int(await self.redis.get(month_key) or 0)
            
            quota = PLAN_QUOTAS.get(plan, 100)
            
            # Reset-Date (1. des nächsten Monats)
            now = datetime.utcnow()
            next_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)
            reset_date = next_month.replace(day=1)
            
            return {
                "tokens_used": current_usage,
                "quota": quota if quota != -1 else "unlimited",
                "quota_percentage": (current_usage / quota * 100) if quota != -1 else 0,
                "resets_at": reset_date.isoformat() + "Z"
            }
        
        except Exception as e:
            logger.error(f"Error getting current usage: {e}")
            return {
                "tokens_used": 0,
                "quota": "unlimited",
                "quota_percentage": 0,
                "resets_at": ""
            }
    
    async def reset_monthly_quota(self, user_id: str):
        """
        Resettet Monthly Quota (für CRON-Job)
        
        Args:
            user_id: User-ID
        """
        try:
            # Aktuellen Monat
            month = datetime.utcnow().strftime('%Y-%m')
            
            # Alle Keys für diesen User & Monat
            pattern = f"usage:{user_id}:{month}:*"
            
            cursor = 0
            deleted = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                
                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Reset monthly quota for user {user_id}: {deleted} keys deleted")
        
        except Exception as e:
            logger.error(f"Error resetting monthly quota: {e}")
    
    async def _log_to_postgres(
        self,
        user_id: str,
        feature: str,
        tokens: int,
        metadata: Optional[Dict]
    ):
        """
        Logged Usage in PostgreSQL für Audit
        
        Args:
            user_id: User-ID
            feature: Feature-Name
            tokens: Token-Count
            metadata: Metadata
        """
        try:
            query = """
                INSERT INTO usage_logs (user_id, feature, tokens, metadata, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """
            
            import json
            metadata_json = json.dumps(metadata or {})
            
            await self.db.execute(query, user_id, feature, tokens, metadata_json)
        
        except Exception as e:
            logger.warning(f"Failed to log to PostgreSQL: {e}")
            # Nicht kritisch - Redis ist Source of Truth


# ============================================================================
# SINGLETON
# ============================================================================

usage_tracking_service = UsageTrackingService()
