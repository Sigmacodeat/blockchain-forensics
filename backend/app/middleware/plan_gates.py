"""
Plan Gates Middleware
Server-side enforcement of subscription plan restrictions
"""
from typing import Callable, List, Optional
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.config.pricing import get_plan_config
from app.db.session import get_db


class PlanGateMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing plan-based access control"""

    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/api/v1/auth",
            "/api/v1/health",
            "/api/v1/docs",
            "/api/v1/openapi.json",
            "/api/v1/billing/plans",  # Allow viewing plans
            "/api/v1/billing/create-checkout",  # Allow creating payments
            "/api/v1/webhooks",  # Allow webhooks
        ]

    async def dispatch(self, request: Request, call_next):
        # Skip middleware for excluded paths
        for excluded in self.excluded_paths:
            if request.url.path.startswith(excluded):
                return await call_next(request)

        # Check plan requirements for protected endpoints
        try:
            # Get user from request (if authenticated)
            user = getattr(request.state, 'user', None)
            if not user:
                # Try to get from auth dependency if available
                try:
                    user = await get_current_user(request)
                    request.state.user = user
                except:
                    pass

            if user and hasattr(user, 'subscription_plan'):
                plan_name = user.subscription_plan or 'free'
                plan_config = get_plan_config(plan_name)

                # Check endpoint-specific requirements
                endpoint_requirements = self._get_endpoint_requirements(request.url.path)

                if endpoint_requirements:
                    required_plan = endpoint_requirements.get('min_plan')
                    required_features = endpoint_requirements.get('features', [])

                    if required_plan and not self._plan_satisfies_requirement(plan_name, required_plan):
                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": "Plan upgrade required",
                                "message": f"This feature requires {required_plan} plan or higher",
                                "current_plan": plan_name,
                                "required_plan": required_plan,
                                "upgrade_url": "/billing"
                            }
                        )

                    # Check feature requirements
                    user_features = plan_config.get('features', [])
                    missing_features = [f for f in required_features if f not in user_features]
                    if missing_features:
                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": "Feature not available",
                                "message": f"Your plan doesn't include: {', '.join(missing_features)}",
                                "current_plan": plan_name,
                                "missing_features": missing_features,
                                "upgrade_url": "/billing"
                            }
                        )

        except Exception as e:
            # Log error but don't block request
            print(f"Plan gate middleware error: {e}")
            pass

        return await call_next(request)

    def _get_endpoint_requirements(self, path: str) -> Optional[dict]:
        """Get plan/feature requirements for specific endpoints"""

        requirements_map = {
            # AI Agent features
            "/api/v1/ai-agents": {"min_plan": "basic", "features": ["ai_insights"]},
            "/api/v1/ai-agents/": {"min_plan": "basic", "features": ["ai_insights"]},

            # Advanced analytics
            "/api/v1/analytics/advanced": {"min_plan": "pro", "features": ["advanced_analytics"]},
            "/api/v1/analytics/export": {"min_plan": "pro", "features": ["bulk_export"]},

            # Compliance features
            "/api/v1/compliance/reports": {"min_plan": "pro", "features": ["compliance_reports"]},
            "/api/v1/compliance/audit": {"min_plan": "enterprise", "features": ["audit_trail"]},

            # Bulk operations
            "/api/v1/cases/bulk": {"min_plan": "pro", "features": ["bulk_operations"]},
            "/api/v1/exports/bulk": {"min_plan": "pro", "features": ["bulk_export"]},

            # API access
            "/api/v1/integrations": {"min_plan": "pro", "features": ["api_access"]},
            "/api/v1/webhooks/custom": {"min_plan": "pro", "features": ["custom_webhooks"]},

            # Advanced tracing
            "/api/v1/tracing/advanced": {"min_plan": "basic", "features": ["advanced_tracing"]},
            "/api/v1/tracing/cross-chain": {"min_plan": "pro", "features": ["cross_chain_tracing"]},

            # Enterprise features
            "/api/v1/organizations": {"min_plan": "enterprise", "features": ["multi_user"]},
            "/api/v1/reports/custom": {"min_plan": "enterprise", "features": ["custom_reports"]},
        }

        # Check for exact matches first
        if path in requirements_map:
            return requirements_map[path]

        # Check for prefix matches (e.g., /api/v1/ai-agents/123)
        for prefix, reqs in requirements_map.items():
            if path.startswith(prefix):
                return reqs

        return None

    def _plan_satisfies_requirement(self, current_plan: str, required_plan: str) -> bool:
        """Check if current plan meets the minimum requirement"""

        plan_hierarchy = {
            'free': 0,
            'basic': 1,
            'pro': 2,
            'enterprise': 3
        }

        current_level = plan_hierarchy.get(current_plan.lower(), 0)
        required_level = plan_hierarchy.get(required_plan.lower(), 999)

        return current_level >= required_level


# Dependency for route-level plan checking
def require_plan(min_plan: str, features: Optional[List[str]] = None):
    """Dependency to require specific plan/features for route access"""

    def dependency(current_user: User = Depends(get_current_user)):
        plan_name = current_user.subscription_plan or 'free'
        plan_config = get_plan_config(plan_name)

        # Check plan level
        if not PlanGateMiddleware()._plan_satisfies_requirement(plan_name, min_plan):
            raise HTTPException(
                status_code=403,
                detail=f"This feature requires {min_plan} plan or higher. Current plan: {plan_name}"
            )

        # Check features
        if features:
            user_features = plan_config.get('features', [])
            missing_features = [f for f in features if f not in user_features]
            if missing_features:
                raise HTTPException(
                    status_code=403,
                    detail=f"Your plan doesn't include: {', '.join(missing_features)}"
                )

        return current_user

    return dependency


# Convenience functions for common requirements
def require_basic_plan():
    return require_plan("basic")

def require_pro_plan():
    return require_plan("pro")

def require_enterprise_plan():
    return require_plan("enterprise")

def require_ai_insights():
    return require_plan("basic", ["ai_insights"])

def require_advanced_analytics():
    return require_plan("pro", ["advanced_analytics"])

def require_api_access():
    return require_plan("pro", ["api_access"])
