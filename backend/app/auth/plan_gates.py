"""
Plan Gates - Authorization basierend auf Subscription Plans
"""
from typing import Callable
from fastapi import HTTPException
from functools import wraps

from app.models.user import SubscriptionPlan


# Plan Hierarchy (höhere Zahl = höherer Plan)
PLAN_HIERARCHY = {
    SubscriptionPlan.COMMUNITY: 0,
    SubscriptionPlan.STARTER: 1,
    SubscriptionPlan.PRO: 2,
    SubscriptionPlan.BUSINESS: 3,
    SubscriptionPlan.PLUS: 4,
    SubscriptionPlan.ENTERPRISE: 5
}


def is_plan_sufficient(required: SubscriptionPlan, user_plan: SubscriptionPlan) -> bool:
    """Check if user's plan is sufficient for required plan"""
    required_level = PLAN_HIERARCHY.get(required, 0)
    user_level = PLAN_HIERARCHY.get(user_plan, 0)
    return user_level >= required_level


def require_plan(plan: SubscriptionPlan):
    """
    Decorator to require minimum subscription plan
    
    Usage:
        @router.get("/investigator")
        @require_plan(SubscriptionPlan.PRO)
        async def get_investigator(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            # Check plan
            if not is_plan_sufficient(plan, current_user.plan):
                raise HTTPException(
                    status_code=403,
                    detail=f"Upgrade to {plan.value.title()} plan required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_admin(func: Callable):
    """
    Decorator to require admin role
    
    Usage:
        @router.get("/analytics")
        @require_admin
        async def get_analytics(...):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper
