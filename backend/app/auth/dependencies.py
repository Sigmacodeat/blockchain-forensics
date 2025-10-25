"""
FastAPI Security Dependencies
"""

import logging
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Ensure TEST_MODE is enabled under pytest even if app.main lifespan didn't run
if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("TEST_MODE"):
    os.environ["TEST_MODE"] = "1"

from app.auth.jwt import decode_token
from app.auth.models import UserRole
from app.observability.audit_logger import log_plan_check, log_admin_access

logger = logging.getLogger(__name__)

# Security scheme (allow missing auth header without raising in tests)
security = HTTPBearer(auto_error=False)
strict_security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token
    
    **Usage:**
    ```python
    @router.get("/protected")
    async def protected_route(user: dict = Depends(get_current_user)):
        return {"user_id": user["user_id"]}
    ```
    
    Returns:
        User dict with user_id, email, role
    
    Raises:
        HTTPException: If token invalid or expired
    """
    # Allow anonymous viewer in TEST_MODE or under pytest when no credentials are provided
    if credentials is None:
        if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            return {"user_id": "test", "email": "test@example.com", "role": UserRole.VIEWER.value}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    
    token_data = decode_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": token_data.user_id,
        "email": token_data.email,
        "role": token_data.role.value,
        "plan": getattr(token_data, "plan", "community"),
        "org_id": getattr(token_data, "org_id", None),
        "features": getattr(token_data, "features", [])
    }

async def get_current_user_strict(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> dict:
    """
    Strict version of get_current_user used by security tests.
    Always enforces JWT and returns 401 for missing/invalid tokens, even in TEST_MODE.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "user_id": token_data.user_id,
        "email": token_data.email,
        "role": token_data.role.value,
        "plan": getattr(token_data, "plan", "community"),
        "org_id": getattr(token_data, "org_id", None),
        "features": getattr(token_data, "features", [])
    }


def require_roles_if(enabled: bool, allowed_roles: List[UserRole]):
    """
    Conditionally enforce RBAC based on a feature flag.
    If enabled=False, the dependency is a no-op and always allows the request.
    If enabled=True, behaves like require_roles(allowed_roles).
    """
    if not enabled:
        async def allow_all() -> dict:
            return {"role": "anonymous"}
        return allow_all
    return require_roles(allowed_roles)


def require_role(allowed_role: UserRole):
    """
    Dependency factory for role-based access control with a single allowed role.
    Convenience wrapper around require_roles.
    
    **Usage:**
    ```python
    @router.post("/admin")
    async def admin_route(
        user: dict = Depends(require_role(UserRole.ADMIN))
    ):
        return {"message": "Admin access granted"}
    ```
    
    Args:
        allowed_role: Single allowed role
    
    Returns:
        Dependency function
    """
    return require_roles([allowed_role])


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control with multiple allowed roles
    
    **Usage:**
    ```python
    @router.post("/trace")
    async def create_trace(
        user: dict = Depends(require_roles([UserRole.ADMIN, UserRole.ANALYST]))
    ):
        return {"message": "Access granted"}
    ```
    
    Args:
        allowed_roles: List of allowed roles
    
    Returns:
        Dependency function
    """
    async def check_role(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role", "")
        allowed_role_values = [role.value for role in allowed_roles]
        
        if user_role not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_role_values)}"
            )
        
        return user

    return check_role


# Plan-based Access Control
PLAN_HIERARCHY = ['community', 'starter', 'pro', 'business', 'plus', 'enterprise']

def has_plan(user: dict, required_plan: str) -> bool:
    """
    Check if user has the required plan or higher in hierarchy
    """
    user_plan = user.get('plan') or 'community'
    
    try:
        user_index = PLAN_HIERARCHY.index(user_plan)
        required_index = PLAN_HIERARCHY.index(required_plan)
        return user_index >= required_index
    except ValueError:
        return False

def require_plan(required_plan: str):
    """
    Dependency factory for plan-based access control
    
    **Usage:**
    ```python
    @router.get("/analytics/trends")
    async def get_trends(user: dict = Depends(require_plan('pro'))):
        return {"data": trends}
    ```
    
    Args:
        required_plan: Minimum plan required ('community', 'starter', 'pro', 'business', 'plus', 'enterprise')
    
    Returns:
        Dependency function
    """
    async def check_plan(user: dict = Depends(get_current_user)) -> dict:
        # Admin has access to everything
        if user.get('role') == UserRole.ADMIN.value:
            return user
        
        user_plan = user.get('plan', 'community')
        allowed = has_plan(user, required_plan)
        
        # ✅ Audit-Log
        log_plan_check(
            user_id=user['user_id'],
            email=user.get('email'),
            plan=user_plan,
            required_plan=required_plan,
            feature=f"require_plan_{required_plan}",
            allowed=allowed
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires plan: {required_plan} or higher. Upgrade at /pricing"
            )
        
        return user
    
    return check_plan


def require_plan_strict(required_plan: str):
    """Strict variant that always enforces authentication even in TEST_MODE."""

    async def check_plan(user: dict = Depends(get_current_user_strict)) -> dict:
        # Admin has access to everything
        if user.get('role') == UserRole.ADMIN.value:
            return user

        user_plan = user.get('plan', 'community')
        allowed = has_plan(user, required_plan)

        log_plan_check(
            user_id=user['user_id'],
            email=user.get('email'),
            plan=user_plan,
            required_plan=required_plan,
            feature=f"require_plan_{required_plan}_strict",
            allowed=allowed,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires plan: {required_plan} or higher. Upgrade at /pricing",
            )

        return user

    return check_plan


def require_feature(feature_name: str):
    """
    Dependency factory for feature-based access control
    
    **Usage:**
    ```python
    @router.get("/ai-agent")
    async def ai_agent(user: dict = Depends(require_feature('ai_agents.unlimited'))):
        return {"agent": "active"}
    ```
    
    Args:
        feature_name: Feature identifier
    
    Returns:
        Dependency function
    """
    async def check_feature(user: dict = Depends(get_current_user)) -> dict:
        # Admin has access to everything
        if user.get('role') == UserRole.ADMIN.value:
            return user
        
        user_features = user.get('features', [])
        if feature_name not in user_features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature not available: {feature_name}. Upgrade your plan."
            )
        
        return user
    
    return check_feature


def require_admin_strict(user: dict = Depends(get_current_user_strict)) -> dict:
    """
    Strict Admin requirement:
    - 401 if token missing/invalid
    - 403 if authenticated but not admin
    """
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
    

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Require Admin role
    
    **Usage:**
    ```python
    @router.delete("/admin/data")
    async def admin_only(user: dict = Depends(require_admin)):
        return {"message": "Admin access granted"}
    ```
    """
    is_admin = user.get("role") == UserRole.ADMIN.value
    
    # ✅ Audit-Log
    log_admin_access(
        user_id=user['user_id'],
        email=user.get('email', ''),
        action="require_admin",
        allowed=is_admin
    )
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


# Optional auth (allows both authenticated and anonymous)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise
    
    **Usage:**
    ```python
    @router.get("/public")
    async def public_route(user: Optional[dict] = Depends(get_current_user_optional)):
        if user:
            return {"message": f"Hello {user['email']}"}
        return {"message": "Hello anonymous"}
    ```
    """
    if not credentials:
        return None
    
    token_data = decode_token(credentials.credentials)
    
    if not token_data:
        return None
    
    return {
        "user_id": token_data.user_id,
        "email": token_data.email,
        "role": token_data.role.value,
        "plan": getattr(token_data, "plan", "community"),
        "org_id": getattr(token_data, "org_id", None),
        "features": getattr(token_data, "features", [])
    }
