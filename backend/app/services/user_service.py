"""
User Service
Handles user management, plan updates, and authentication
"""
from datetime import datetime
from typing import Optional, Dict

from app.models.user import User, SubscriptionPlan, SubscriptionStatus


class UserService:
    """Service für User Management"""
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        # In real app: query database
        # Simplified for tests
        return None
    
    async def update_user_plan(
        self,
        user_id: str,
        plan: SubscriptionPlan,
        subscription_id: str,
        subscription_status: SubscriptionStatus,
        billing_cycle_start: datetime,
        billing_cycle_end: datetime
    ) -> Dict:
        """Update user's subscription plan"""
        # In real app: update database
        # Simplified for tests
        return {
            'status': 'success',
            'user_id': user_id,
            'plan': plan,
            'subscription_id': subscription_id,
            'subscription_status': subscription_status
        }
    
    async def update_subscription_period(
        self,
        subscription_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Dict:
        """Update subscription billing period"""
        return {
            'status': 'updated',
            'subscription_id': subscription_id,
            'period_start': period_start,
            'period_end': period_end
        }
    
    async def downgrade_to_community(
        self,
        user_id: Optional[str] = None,
        subscription_id: Optional[str] = None
    ) -> Dict:
        """Downgrade user to Community plan"""
        # In real app: find user and update
        return {
            'status': 'downgraded',
            'new_plan': SubscriptionPlan.COMMUNITY,
            'subscription_status': SubscriptionStatus.CANCELLED
        }
    
    async def create_user(
        self,
        email: str,
        password: str,
        username: str,
        plan: SubscriptionPlan = SubscriptionPlan.COMMUNITY
    ) -> User:
        """Create new user with Community plan by default"""
        # In real app: hash password, save to DB
        user = User(
            id=f"user_{datetime.now().timestamp()}",
            email=email,
            username=username,
            hashed_password=self._hash_password(password),
            plan=plan,
            subscription_status=SubscriptionStatus.ACTIVE if plan == SubscriptionPlan.COMMUNITY else SubscriptionStatus.NONE
        )
        return user
    
    def _hash_password(self, password: str) -> str:
        """Hash password (simplified)"""
        # In real app: use bcrypt/argon2
        return f"hashed_{password}"
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user"""
        # In real app: query DB, verify password
        return None


# Global instance
user_service = UserService()
