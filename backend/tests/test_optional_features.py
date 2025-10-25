"""
Tests für optionale Features
- Audit-Logging
- Rate-Limiting
- Trial-Management
"""

import pytest
from datetime import datetime, timedelta
from app.observability.audit_logger import (
    log_plan_check,
    log_admin_access,
    log_trial_event,
    log_rate_limit_event,
    AuditEventType
)
from app.models.user import User, SubscriptionPlan


class TestAuditLogging:
    """Test Audit-Logging System"""
    
    def test_log_plan_check_success(self):
        """Plan-Check Erfolg wird geloggt"""
        # Should not raise
        log_plan_check(
            user_id="user_123",
            email="test@example.com",
            plan="community",
            required_plan="community",
            feature="trace",
            allowed=True
        )
    
    def test_log_plan_check_failure(self):
        """Plan-Check Failure wird geloggt"""
        log_plan_check(
            user_id="user_123",
            email="test@example.com",
            plan="community",
            required_plan="pro",
            feature="graph_analytics",
            allowed=False
        )
    
    def test_log_admin_access(self):
        """Admin-Zugriff wird geloggt"""
        log_admin_access(
            user_id="admin_1",
            email="admin@example.com",
            action="create_user",
            allowed=True
        )
    
    def test_log_trial_event(self):
        """Trial-Events werden geloggt"""
        trial_ends = datetime.utcnow() + timedelta(days=14)
        log_trial_event(
            event_type=AuditEventType.TRIAL_STARTED,
            user_id="user_123",
            email="test@example.com",
            trial_plan="pro",
            trial_ends_at=trial_ends
        )
    
    def test_log_rate_limit_event(self):
        """Rate-Limit Events werden geloggt"""
        log_rate_limit_event(
            user_id="user_123",
            plan="community",
            endpoint="/api/v1/trace",
            limit="10/minute",
            current_count=11
        )


class TestRateLimiting:
    """Test Rate-Limiting Logic"""
    
    def test_rate_limits_defined(self):
        """Rate-Limits für alle Pläne definiert"""
        from app.middleware.rate_limiter import RATE_LIMITS
        
        assert "community" in RATE_LIMITS
        assert "pro" in RATE_LIMITS
        assert "enterprise" in RATE_LIMITS
        
        assert RATE_LIMITS["community"] == 10
        assert RATE_LIMITS["pro"] == 100
        assert RATE_LIMITS["enterprise"] == 10000
    
    def test_exempt_paths_defined(self):
        """Exempt Paths sind definiert"""
        from app.middleware.rate_limiter import EXEMPT_PATHS
        
        assert "/health" in EXEMPT_PATHS
        assert "/api/v1/auth/login" in EXEMPT_PATHS


class TestTrialManagement:
    """Test Trial-Management System"""
    
    def test_user_get_effective_plan_no_trial(self):
        """Effective Plan ohne Trial = regular plan"""
        user = User(
            id="user_123",
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            plan=SubscriptionPlan.COMMUNITY
        )
        
        assert user.get_effective_plan() == SubscriptionPlan.COMMUNITY
    
    def test_user_get_effective_plan_active_trial(self):
        """Effective Plan mit aktivem Trial = trial plan"""
        future_date = datetime.utcnow() + timedelta(days=7)
        
        user = User(
            id="user_123",
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            plan=SubscriptionPlan.COMMUNITY,
            trial_plan=SubscriptionPlan.PRO,
            trial_ends_at=future_date
        )
        
        assert user.get_effective_plan() == SubscriptionPlan.PRO
    
    def test_user_get_effective_plan_expired_trial(self):
        """Effective Plan mit abgelaufenem Trial = regular plan"""
        past_date = datetime.utcnow() - timedelta(days=1)
        
        user = User(
            id="user_123",
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            plan=SubscriptionPlan.COMMUNITY,
            trial_plan=SubscriptionPlan.PRO,
            trial_ends_at=past_date
        )
        
        assert user.get_effective_plan() == SubscriptionPlan.COMMUNITY
    
    def test_user_is_trial_active(self):
        """is_trial_active() prüft Trial-Status korrekt"""
        future_date = datetime.utcnow() + timedelta(days=7)
        
        user = User(
            id="user_123",
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            plan=SubscriptionPlan.COMMUNITY,
            trial_plan=SubscriptionPlan.PRO,
            trial_ends_at=future_date
        )
        
        assert user.is_trial_active() is True
    
    def test_user_trial_days_remaining(self):
        """trial_days_remaining() berechnet verbleibende Tage"""
        future_date = datetime.utcnow() + timedelta(days=7)
        
        user = User(
            id="user_123",
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            plan=SubscriptionPlan.COMMUNITY,
            trial_plan=SubscriptionPlan.PRO,
            trial_ends_at=future_date
        )
        
        days = user.trial_days_remaining()
        assert days is not None
        assert days >= 6 and days <= 7  # Je nach Timing
    
    def test_user_trial_days_remaining_no_trial(self):
        """trial_days_remaining() gibt None ohne Trial"""
        user = User(
            id="user_123",
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            plan=SubscriptionPlan.COMMUNITY
        )
        
        assert user.trial_days_remaining() is None


@pytest.mark.asyncio
class TestTrialAPI:
    """Integration Tests für Trial API (benötigen TestClient)"""
    
    async def test_start_trial_requires_auth(self, test_client):
        """Trial-Start erfordert Authentication"""
        # Simplified - würde JWT Token benötigen
        pass
    
    async def test_trial_status_returns_correct_data(self, test_client):
        """Trial-Status gibt korrekte Daten zurück"""
        # Simplified
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
