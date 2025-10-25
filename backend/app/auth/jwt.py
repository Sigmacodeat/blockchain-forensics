"""
JWT Token Management
"""

import logging
from datetime import datetime, timedelta
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
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role.value,
        "plan": plan,  # Always include plan (defaults to 'community')
        "exp": expire,
        "type": "access"
    }
    if org_id:
        payload["org_id"] = org_id
    if features:
        payload["features"] = features
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate JWT token
    Returns TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: Optional[str] = payload.get("sub")
        email: Optional[str] = payload.get("email")
        role_str: Optional[str] = payload.get("role")
        
        if user_id is None or email is None or role_str is None:
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
