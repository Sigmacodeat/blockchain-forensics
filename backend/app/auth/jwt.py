"""
JWT Token Management
"""

import logging
from datetime import datetime, timedelta
import uuid
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.auth.models import TokenData, UserRole

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(user_id: str, email: str, role: UserRole, *, plan: str = 'community', org_id: str | None = None, features: list[str] | None = None) -> str:
    """Create JWT access token with plan, org_id, and features"""
    now = datetime.utcnow()
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    issuer = getattr(settings, "JWT_ISSUER", None) or getattr(settings, "APP_NAME", None)
    audience = getattr(settings, "JWT_AUDIENCE", None) or getattr(settings, "APP_NAME", None)
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role.value,
        "plan": plan,  # Always include plan (defaults to 'community')
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    if issuer:
        payload["iss"] = issuer
    if audience:
        payload["aud"] = audience
    if org_id:
        payload["org_id"] = org_id
    if features:
        payload["features"] = features
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token"""
    now = datetime.utcnow()
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    issuer = getattr(settings, "JWT_ISSUER", None) or getattr(settings, "APP_NAME", None)
    audience = getattr(settings, "JWT_AUDIENCE", None) or getattr(settings, "APP_NAME", None)
    
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    if issuer:
        payload["iss"] = issuer
    if audience:
        payload["aud"] = audience
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate JWT token
    Returns TokenData if valid, None otherwise
    """
    try:
        # Optional audience/issuer validation if configured; keep backward compatible when unset
        issuer = getattr(settings, "JWT_ISSUER", None)
        audience = getattr(settings, "JWT_AUDIENCE", None)
        options = {"verify_aud": bool(audience)}
        if audience:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM], audience=audience, options=options)
        else:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM], options=options)
        if issuer and payload.get("iss") != issuer:
            return None
        
        user_id: Optional[str] = payload.get("sub")
        tok_type: Optional[str] = payload.get("type")
        email: Optional[str] = payload.get("email")
        role_str: Optional[str] = payload.get("role")
        
        if user_id is None:
            return None
        # Allow refresh tokens which typically do not carry email/role
        if tok_type == "refresh":
            role = UserRole.VIEWER
            email = email or ""
        else:
            if email is None or role_str is None:
                return None
            role = UserRole(role_str)
        plan = payload.get("plan", "community")  # Default to 'community'
        org_id = payload.get("org_id")  # Optional for multi-tenancy
        feats = payload.get("features") or []
        
        return TokenData(user_id=user_id, email=email, role=role, plan=plan, org_id=org_id, features=feats)
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None
