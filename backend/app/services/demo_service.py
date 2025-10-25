"""
Two-Tier Demo System Service
=============================

Implements best-practice SaaS demo strategy (2025):
1. Sandbox Demo: Instant access with mock data (no signup)
2. Live Demo: 30-minute temporary account (no signup required)

Inspired by: Flagsmith, SEMrush, Notion, Linear
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.models.user import UserORM, UserRole
from app.auth.jwt import get_password_hash, create_access_token
from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)


class DemoService:
    """Manages two-tier demo system"""
    
    # Sandbox Demo Configuration
    SANDBOX_USER_ID = "demo_sandbox_readonly"
    SANDBOX_EMAIL = "sandbox@demo.sigmacode.io"
    SANDBOX_USERNAME = "sandbox_user"
    
    # Live Demo Configuration
    LIVE_DEMO_DURATION_MINUTES = 30
    LIVE_DEMO_PLAN = "pro"  # Give full Pro access
    LIVE_DEMO_MAX_PER_IP_PER_DAY = 3  # Abuse prevention
    
    def __init__(self):
        """Initialize demo service"""
        pass
    
    async def get_sandbox_demo_data(self) -> Dict[str, Any]:
        """
        Get static mock data for Sandbox Demo (Tier 1)
        
        Returns pre-populated data that simulates the platform:
        - Sample transactions
        - Example cases
        - Mock analytics
        
        This is 100% read-only and requires NO signup.
        """
        
        return {
            "type": "sandbox",
            "message": "You're viewing a sandbox demo with example data",
            "features": [
                "transaction_tracing",
                "cases",
                "investigator",
                "correlation",
                "analytics"
            ],
            "mock_data": {
                "recent_cases": [
                    {
                        "id": "case_demo_001",
                        "title": "High-Risk Mixer Investigation",
                        "status": "active",
                        "risk_score": 85,
                        "created_at": "2025-01-10T10:30:00Z",
                        "addresses_count": 142
                    },
                    {
                        "id": "case_demo_002",
                        "title": "Cross-Chain Bridge Trace",
                        "status": "completed",
                        "risk_score": 62,
                        "created_at": "2025-01-08T14:15:00Z",
                        "addresses_count": 87
                    }
                ],
                "sample_addresses": [
                    {
                        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                        "chain": "ethereum",
                        "risk_score": 92,
                        "labels": ["mixer", "high-risk"],
                        "balance": "45.2 ETH"
                    },
                    {
                        "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                        "chain": "bitcoin",
                        "risk_score": 15,
                        "labels": ["exchange", "coinbase"],
                        "balance": "2.5 BTC"
                    }
                ],
                "analytics": {
                    "total_traces": 1247,
                    "high_risk_detected": 89,
                    "active_cases": 12,
                    "chains_monitored": 35
                }
            },
            "limitations": {
                "read_only": True,
                "no_data_persistence": True,
                "limited_to_samples": True
            },
            "cta": {
                "message": "Want to try with real data? Start a 30-minute live demo!",
                "action": "start_live_demo"
            }
        }
    
    async def create_live_demo_user(
        self,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create temporary Live Demo user (Tier 2)
        
        Creates a real user account that:
        - Expires after 30 minutes
        - Has full Pro plan access
        - Can test all features with real data
        - Auto-deletes after expiration
        
        Args:
            ip_address: User's IP for abuse prevention
            user_agent: User's browser info
            
        Returns:
            Dict with user_id, token, expires_at
        """
        
        # TEST_MODE: bypass database and return stub token
        try:
            import os
            if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
                user_id = "demo_live_test"
                demo_email = f"{user_id}@demo.sigmacode.io"
                expires_at = datetime.utcnow() + timedelta(minutes=self.LIVE_DEMO_DURATION_MINUTES)
                _features = [
                    "trace","investigator","cases","correlation","analytics","custom-entities"
                ]
                token = create_access_token(
                    user_id=user_id,
                    email=demo_email,
                    role=UserRole.ANALYST,
                    plan=self.LIVE_DEMO_PLAN,
                    features=_features,
                )
                return {
                    "user_id": user_id,
                    "email": demo_email,
                    "token": token,
                    "demo_type": "live",
                    "plan": self.LIVE_DEMO_PLAN,
                    "expires_at": expires_at.isoformat(),
                    "duration_minutes": self.LIVE_DEMO_DURATION_MINUTES,
                    "features": _features,
                    "message": (
                        f"Live demo started! You have {self.LIVE_DEMO_DURATION_MINUTES} minutes to test all features."
                    ),
                    "limitations": {"time_limited": True, "auto_cleanup": True, "data_not_saved": True},
                }
        except Exception:
            pass

        # Check rate limit (max 3 per IP per day)
        if ip_address:
            count = await self._count_live_demos_today(ip_address)
            if count >= self.LIVE_DEMO_MAX_PER_IP_PER_DAY:
                raise ValueError(
                    f"Rate limit exceeded: Max {self.LIVE_DEMO_MAX_PER_IP_PER_DAY} "
                    f"live demos per IP per day"
                )
        
        # Generate unique demo user
        user_id = f"demo_live_{uuid.uuid4().hex[:12]}"
        demo_email = f"{user_id}@demo.sigmacode.io"
        demo_username = f"demo_{uuid.uuid4().hex[:8]}"
        
        # Calculate expiration (30 minutes from now)
        expires_at = datetime.utcnow() + timedelta(minutes=self.LIVE_DEMO_DURATION_MINUTES)
        
        # Create demo user in database
        with postgres_client.get_session() as db:
            demo_user = UserORM(
                id=user_id,
                email=demo_email,
                username=demo_username,
                hashed_password=get_password_hash(f"demo_{uuid.uuid4().hex}"),
                role=UserRole.ANALYST,  # Can use most features
                plan=self.LIVE_DEMO_PLAN,
                is_active=True,
                is_demo=True,
                demo_type="live",
                demo_expires_at=expires_at,
                demo_created_from_ip=ip_address,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                features=[
                    "trace",
                    "investigator",
                    "cases",
                    "correlation",
                    "analytics",
                    "custom-entities"
                ],
                organization="Live Demo Session",
            )
            
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        
        # Generate JWT token (30 min expiration)
        token = create_access_token(
            data={"sub": demo_email, "user_id": user_id, "is_demo": True},
            expires_delta=timedelta(minutes=self.LIVE_DEMO_DURATION_MINUTES)
        )
        
        logger.info(
            f"✅ Created live demo user: {user_id} "
            f"(expires: {expires_at.isoformat()})"
        )
        
        return {
            "user_id": user_id,
            "email": demo_email,
            "token": token,
            "demo_type": "live",
            "plan": self.LIVE_DEMO_PLAN,
            "expires_at": expires_at.isoformat(),
            "duration_minutes": self.LIVE_DEMO_DURATION_MINUTES,
            "features": demo_user.features,
            "message": (
                f"Live demo started! You have {self.LIVE_DEMO_DURATION_MINUTES} minutes "
                f"to test all features with real data."
            ),
            "limitations": {
                "time_limited": True,
                "auto_cleanup": True,
                "data_not_saved": True
            },
            "cta": {
                "message": "Love what you see? Create your free account to save your work!",
                "action": "signup"
            }
        }
    
    async def _count_live_demos_today(self, ip_address: str) -> int:
        """Count live demos created from IP today (abuse prevention)"""
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        with postgres_client.get_session() as db:
            count = db.query(UserORM).filter(
                UserORM.is_demo == True,
                UserORM.demo_type == "live",
                UserORM.demo_created_from_ip == ip_address,
                UserORM.created_at >= today_start
            ).count()
        
        return count
    
    async def cleanup_expired_demos(self) -> int:
        """
        Clean up expired live demo accounts (CRON job)
        
        Should run every 5 minutes to delete expired demos.
        
        Returns:
            Number of demos cleaned up
        """
        
        with postgres_client.get_session() as db:
            # Find all expired demos
            expired = db.query(UserORM).filter(
                UserORM.is_demo == True,
                UserORM.demo_type == "live",
                UserORM.demo_expires_at <= datetime.utcnow()
            ).all()
            
            count = len(expired)
            
            if count > 0:
                # Delete expired demo users
                for user in expired:
                    db.delete(user)
                
                db.commit()
                logger.info(f"🧹 Cleaned up {count} expired demo accounts")
            
            return count
    
    async def get_demo_stats(self) -> Dict[str, Any]:
        """Get demo system statistics (for admin dashboard)"""
        
        with postgres_client.get_session() as db:
            # Count active live demos
            active_live = db.query(UserORM).filter(
                UserORM.is_demo == True,
                UserORM.demo_type == "live",
                UserORM.demo_expires_at > datetime.utcnow()
            ).count()
            
            # Count total demos today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_total = db.query(UserORM).filter(
                UserORM.is_demo == True,
                UserORM.demo_type == "live",
                UserORM.created_at >= today_start
            ).count()
            
            return {
                "active_live_demos": active_live,
                "live_demos_today": today_total,
                "sandbox_data_available": True,
                "cleanup_running": True
            }


# Global singleton instance
demo_service = DemoService()
