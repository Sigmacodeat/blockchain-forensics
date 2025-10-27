"""
Authentication API Endpoints
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, cast
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
import os
import json
import base64
from urllib.parse import urlencode
import httpx
from app.config import settings
from sqlalchemy.orm import Session

from app.auth.models import UserCreate, UserLogin, User, Token, AuthResponse, UserRole
from app.auth.jwt import create_access_token, create_refresh_token, verify_password, get_password_hash, decode_token, REFRESH_TOKEN_EXPIRE_DAYS
from app.auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_user_strict,
    require_admin,
    require_admin_strict,
)
from app.db.session import get_db
from app.models.user import UserORM, SubscriptionPlan
from app.services.partner_service import partner_service
from app.services.two_factor_auth import two_fa_manager
from app.db.redis_client import redis_client
from jose import jwt as jose_jwt
from app.security.ssrf_guard import is_url_allowed

logger = logging.getLogger(__name__)
router = APIRouter()

# Legacy in-memory users db (deprecated, kept for backward compatibility)
# New code should use UserORM database queries instead
users_db: dict = {}

def _seed_e2e_users_db(db: Session) -> None:
    try:
        if os.getenv("E2E_SEED", "0") != "1":
            return
        existing = {e[0] for e in db.query(UserORM.email).all()}
        seeds = [
            {
                "email": "community@example.com",
                "username": "community",
                "password": "password123",
                "role": UserRole.VIEWER,
                "plan": SubscriptionPlan.COMMUNITY.value,
            },
            {
                "email": "pro@example.com",
                "username": "pro",
                "password": "password123",
                "role": UserRole.ANALYST,
                "plan": SubscriptionPlan.PRO.value,
            },
            {
                "email": "admin@example.com",
                "username": "admin",
                "password": "adminpass123",
                "role": UserRole.ADMIN,
                "plan": SubscriptionPlan.ENTERPRISE.value,
            },
        ]
        created = []
        for s in seeds:
            if s["email"] in existing:
                continue
            uid = str(uuid.uuid4())
            user = UserORM(
                id=uid,
                email=s["email"],
                username=s["username"],
                organization=None,
                hashed_password=get_password_hash(s["password"]),
                role=s["role"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                plan=s["plan"],
                features=[],
            )
            db.add(user)
            created.append(s["email"])
        if created:
            db.commit()
            logger.info("E2E users seeded (DB): %s", ", ".join(created))
    except Exception as e:
        logger.exception("Failed to seed E2E users (DB): %s", e)


@router.post("/register", response_model=AuthResponse, response_model_exclude_unset=False, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registriere neuen User
    
    **Features:**
    - Email-Validierung
    - Passwort-Hashing
    - Automatische Role-Zuweisung (Viewer)
    - JWT Token Generation
    """
    try:
        # Optional: seed E2E users into DB for local tests
        _seed_e2e_users_db(db)

        # Check if user exists
        existing = db.query(UserORM).filter(UserORM.email == str(user_data.email)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email bereits registriert"
            )
        
        if db.query(UserORM).filter(UserORM.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Benutzername bereits vergeben"
            )
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        now = datetime.utcnow()

        wants_discount = bool(getattr(user_data, "wants_institutional_discount", False))
        initial_verification_status = "pending" if wants_discount else "none"

        user_row = UserORM(
            id=user_id,
            email=str(user_data.email),
            username=user_data.username,
            organization=user_data.organization,
            organization_type=getattr(user_data, "organization_type", None),
            organization_name=getattr(user_data, "organization_name", None),
            institutional_discount_requested=wants_discount,
            institutional_discount_verified=False,
            verification_status=initial_verification_status,
            hashed_password=hashed_password,
            role=UserRole.VIEWER,
            is_active=True,
            created_at=now,
            updated_at=now,
            plan=SubscriptionPlan.COMMUNITY.value,
            features=[],
        )
        db.add(user_row)
        db.commit()
        # Optional: Referral-Zuordnung bei Registrierung (best-effort)
        try:
            if getattr(user_data, "referral_code", None):
                await partner_service.assign_referral(
                    referred_user_id=user_id,
                    referral_code=str(user_data.referral_code),
                    tracking_id=None,
                    source="register_form",
                )
        except Exception as _ref_err:
            logger.debug(f"Referral attribution skipped: {_ref_err}")
        
        # Generate tokens
        access_token = create_access_token(user_id, str(user_data.email), UserRole.VIEWER, plan="community", features=[])
        refresh_token = create_refresh_token(user_id)
        
        # Create response
        user = User(
            id=user_id,
            email=str(user_data.email),
            username=user_data.username,
            organization=user_data.organization,
            organization_type=getattr(user_data, "organization_type", None),
            organization_name=getattr(user_data, "organization_name", None),
            role=UserRole.VIEWER,
            is_active=True,
            created_at=now,
            plan=SubscriptionPlan.COMMUNITY.value,
            institutional_discount_requested=wants_discount,
            institutional_discount_verified=False,
            verification_status=initial_verification_status,
        )
        
        tokens = Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        logger.info(f"User registered: {user_data.email}")
        
        return AuthResponse(user=user, tokens=tokens)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse, response_model_exclude_unset=False)
async def login(credentials: UserLogin, db: Session = Depends(get_db), request: Request = None):
    """
    User Login
    
    **Features:**
    - Email/Password Authentication
    - JWT Token Generation
    - Access & Refresh Tokens
    """
    try:
        # Optional: seed E2E users into DB for local tests
        _seed_e2e_users_db(db)

        # Find user by email
        user_row = db.query(UserORM).filter(UserORM.email == str(credentials.email)).first()
        if not user_row:
            # Brute-force backoff (best-effort)
            try:
                await redis_client._ensure_connected()
                if redis_client.client and request is not None:
                    ip = request.client.host if request and request.client else "unknown"
                    key = f"auth:bf:{str(credentials.email).lower()}:{ip}"
                    cnt = await redis_client.client.incr(key)
                    await redis_client.client.expire(key, 900)  # 15 minutes
                    if int(cnt) > 5:
                        raise HTTPException(status_code=429, detail="Too many attempts. Try later.")
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Email oder Passwort"
            )
        
        # Verify password
        if not verify_password(credentials.password, cast(str, user_row.hashed_password)):
            # Brute-force backoff (best-effort)
            try:
                await redis_client._ensure_connected()
                if redis_client.client and request is not None:
                    ip = request.client.host if request and request.client else "unknown"
                    key = f"auth:bf:{str(credentials.email).lower()}:{ip}"
                    cnt = await redis_client.client.incr(key)
                    await redis_client.client.expire(key, 900)
                    if int(cnt) > 5:
                        raise HTTPException(status_code=429, detail="Too many attempts. Try later.")
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Email oder Passwort"
            )
        
        # Check if active
        if not bool(user_row.is_active):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deaktiviert"
            )
        # Optional 2FA enforcement for admins
        try:
            if os.getenv("ENFORCE_2FA_FOR_ADMINS") == "1" and str(user_row.role) == str(UserRole.ADMIN):
                # Only enforce if 2FA is set up for the user
                uid = str(user_row.id)
                if uid in two_fa_manager.user_secrets:
                    otp = request.headers.get("x-otp") if request is not None else None
                    if not otp or not two_fa_manager.verify_2fa_login(uid, otp):
                        raise HTTPException(status_code=401, detail="2FA erforderlich")
        except HTTPException:
            raise
        except Exception:
            # fail-closed would be safer, but keep compatibility: fail-open if 2FA infra missing
            pass
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {credentials.email}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )
    
    # Ensure defaults
    plan = user_row.plan or SubscriptionPlan.COMMUNITY.value
    features = user_row.features or []

    # Generate tokens with plan/features
    # Note: user_row.role is now a string from DB, not an Enum
    # Convert UUID to string explicitly
    user_id_str = str(user_row.id)
    access_token = create_access_token(
        user_id_str,
        str(user_row.email),
        UserRole(str(user_row.role)),
        plan=str(plan),
        features=list(features) if features else []
    )
    refresh_token = create_refresh_token(user_id_str)
    
    # Create response
    user = User(
        id=user_id_str,
        email=str(user_row.email),
        username=str(user_row.username) if user_row.username else str(user_row.email).split('@')[0],
        organization=str(user_row.organization) if user_row.organization else None,
        role=UserRole(str(user_row.role)),
        is_active=bool(user_row.is_active),
        created_at=user_row.created_at,
        plan=str(plan),
    )
    
    tokens = Token(
        access_token=access_token,
        refresh_token=refresh_token
    )
    
    logger.info(f"User logged in: {credentials.email}")
    
    return AuthResponse(user=user, tokens=tokens)


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user_strict)):
    """
    User Logout
    
    **Note:** Currently stateless (JWT). In production, implement token blacklist.
    """
    logger.info(f"User logged out: {current_user['email']}")
    return {"message": "Erfolgreich abgemeldet"}


@router.get("/me", response_model=User, response_model_exclude_unset=False)
async def get_current_user_info(current_user: dict = Depends(get_current_user_strict), db: Session = Depends(get_db)):
    """
    Get Current User Info
    
    Returns authenticated user's information
    """
    user_row = db.query(UserORM).filter(UserORM.id == cast(str, current_user["user_id"])).first()
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User nicht gefunden"
        )
    
    return User(
        id=cast(str, user_row.id),
        email=cast(str, user_row.email),
        username=cast(str, user_row.username) if user_row.username else cast(str, user_row.email).split('@')[0],
        organization=cast(str | None, user_row.organization),
        role=UserRole(cast(str, user_row.role)),
        is_active=bool(user_row.is_active),
        created_at=cast(datetime, user_row.created_at),
        plan=cast(str, user_row.plan or SubscriptionPlan.COMMUNITY.value),
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    Refresh Access Token
    
    **Usage:**
    Provide refresh_token to get new access_token
    """
    token_data = decode_token(refresh_token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger Refresh Token"
        )
    # Check token type and rotation blacklist
    try:
        claims = jose_jwt.get_unverified_claims(refresh_token)
        if claims.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Ungültiger Token-Typ")
        old_jti = claims.get("jti")
        if old_jti:
            await redis_client._ensure_connected()
            if redis_client.client:
                blkey = f"rt:blacklist:{old_jti}"
                if await redis_client.client.exists(blkey):
                    raise HTTPException(status_code=401, detail="Token widerrufen")
    except HTTPException:
        raise
    except Exception:
        pass
    
    # Get user
    user_row = db.query(UserORM).filter(UserORM.id == token_data.user_id).first()
    if not user_row or not user_row.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User nicht gefunden oder deaktiviert"
        )
    
    # Ensure defaults for plan/features
    plan = user_row.plan or SubscriptionPlan.COMMUNITY.value
    features = user_row.features or []

    # Generate new tokens carrying plan/features
    access_token = create_access_token(
        cast(str, user_row.id),
        cast(str, user_row.email),
        UserRole(cast(str, user_row.role)),
        plan=cast(str, plan),
        features=cast(list[str], features)
    )
    new_refresh_token = create_refresh_token(cast(str, user_row.id))
    # Revoke old refresh token jti (best-effort)
    try:
        if old_jti and redis_client and getattr(redis_client, "client", None):
            ttl = 86400 * int(REFRESH_TOKEN_EXPIRE_DAYS)
            await redis_client.client.setex(f"rt:blacklist:{old_jti}", ttl, "1")
    except Exception:
        pass
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token
    )


# Admin Endpoints

@router.post("/admin/create-user", response_model=User)
async def admin_create_user(
    user_data: UserCreate,
    role: UserRole = UserRole.VIEWER,
    current_user: dict = Depends(require_admin_strict),
    db: Session = Depends(get_db),
):
    """
    Admin: Create User with specific role
    
    **Requires:** Admin Role
    """
    
    # Check if user exists
    if db.query(UserORM).filter(UserORM.email == str(user_data.email)).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email bereits registriert"
        )
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    now = datetime.utcnow()

    row = UserORM(
        id=user_id,
        email=str(user_data.email),
        username=user_data.username,
        organization=user_data.organization,
        hashed_password=hashed_password,
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
        plan=SubscriptionPlan.COMMUNITY.value,
        features=[],
    )
    db.add(row)
    db.commit()

    logger.info(f"Admin created user: {user_data.email} with role {role}")
    
    return User(
        id=user_id,
        email=str(user_data.email),
        username=user_data.username,
        organization=user_data.organization,
        role=role,
        is_active=True,
        created_at=now,
        plan=SubscriptionPlan.COMMUNITY.value,
    )


# --- OAuth (Google) ---

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"


def _get_backend_callback_url(request: Request) -> str:
    # Build absolute callback URL for this request
    # Prefer configured BACKEND_URL to avoid mismatches behind proxies (invalid_grant)
    try:
        backend_base = getattr(settings, "BACKEND_URL", None)
    except Exception:
        backend_base = None
    if backend_base:
        return backend_base.rstrip("/") + settings.OAUTH_CALLBACK_PATH
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    base = f"{scheme}://{host}"
    return base + settings.OAUTH_CALLBACK_PATH


@router.get("/oauth/google/config")
async def oauth_google_config(request: Request):
    """Test endpoint to check Google OAuth configuration"""
    callback_url = _get_backend_callback_url(request)
    
    return {
        "configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
        "client_id": settings.GOOGLE_CLIENT_ID[:20] + "..." if settings.GOOGLE_CLIENT_ID else None,
        "callback_url": callback_url,
        "admin_emails": settings.ADMIN_EMAILS,
    }


@router.get("/oauth/google")
async def oauth_google_start(request: Request, redirect_uri: str):
    """Start Google OAuth flow and redirect to Google consent screen.
    redirect_uri: frontend URL to return to after login (e.g., https://app.example.com/login)
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        # Konfiguration fehlt: liefere einen klaren 503 statt 500
        logger.error("Google OAuth not configured - missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")
        raise HTTPException(status_code=503, detail="Google OAuth nicht konfiguriert. Bitte GOOGLE_CLIENT_ID und GOOGLE_CLIENT_SECRET setzen.")

    callback_url = _get_backend_callback_url(request)
    state_payload = {"redirect_uri": redirect_uri}
    state = base64.urlsafe_b64encode(json.dumps(state_payload).encode()).decode()

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = GOOGLE_AUTH_ENDPOINT + "?" + urlencode(params)
    logger.info(f"Redirecting to Google OAuth with callback URL: {callback_url}")
    return RedirectResponse(url)


@router.get("/oauth/google/callback")
async def oauth_google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    if error:
        logger.error(f"OAuth error from Google: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth Fehler: {error}")
    if not code or not state:
        logger.error("OAuth callback missing code or state")
        raise HTTPException(status_code=400, detail="Ungültiger OAuth-Callback")

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth not configured")
        raise HTTPException(status_code=503, detail="Google OAuth nicht konfiguriert. Bitte GOOGLE_CLIENT_ID und GOOGLE_CLIENT_SECRET setzen.")

    try:
        state_obj = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        frontend_redirect = state_obj.get("redirect_uri")
        if not frontend_redirect:
            raise ValueError("redirect_uri fehlt")
        # Validate decoded frontend redirect target
        allowed_frontend_host = None
        try:
            from urllib.parse import urlparse
            if getattr(settings, "FRONTEND_URL", None):
                allowed_frontend_host = urlparse(settings.FRONTEND_URL).hostname
        except Exception:
            allowed_frontend_host = None
        allowed_hosts = [allowed_frontend_host] if allowed_frontend_host else None
        if not is_url_allowed(frontend_redirect, allowed_hosts=allowed_hosts):
            raise HTTPException(status_code=400, detail="Ungültige redirect_uri")
    except Exception as e:
        logger.error(f"Failed to decode state: {e}")
        raise HTTPException(status_code=400, detail="Ungültiger state")

    callback_url = _get_backend_callback_url(request)
    logger.info(f"OAuth callback URL: {callback_url}")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Exchange code for tokens
            logger.info("Exchanging code for tokens with Google")
            token_resp = await client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": callback_url,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                logger.error(f"Token exchange failed: {token_resp.status_code} - {token_resp.text}")
                raise HTTPException(status_code=400, detail=f"Token-Austausch fehlgeschlagen: {token_resp.text}")
            token_data = token_resp.json()

            access_token_google = token_data.get("access_token")
            if not access_token_google:
                logger.error("No access token in response")
                raise HTTPException(status_code=400, detail="Kein Access Token erhalten")

            # Fetch userinfo
            logger.info("Fetching user info from Google")
            ui_resp = await client.get(
                GOOGLE_USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token_google}"},
            )
            if ui_resp.status_code != 200:
                logger.error(f"Userinfo request failed: {ui_resp.status_code} - {ui_resp.text}")
                raise HTTPException(status_code=400, detail="Userinfo fehlgeschlagen")
            ui = ui_resp.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth-Verarbeitung fehlgeschlagen: {str(e)}")

    email = ui.get("email")
    name = ui.get("name") or (email.split("@")[0] if email else "user")
    sub = ui.get("sub")

    if not email:
        logger.error("No email in Google userinfo response")
        raise HTTPException(status_code=400, detail="Email nicht verfügbar")

    logger.info(f"Processing OAuth login for email: {email}")

    # Find or create user in DB
    try:
        db_user = db.query(UserORM).filter(UserORM.email == str(email)).first()
        if not db_user:
            user_id = str(uuid.uuid4())
            desired_role = UserRole.ADMIN if str(email).lower() in set(settings.ADMIN_EMAILS or []) else UserRole.VIEWER
            logger.info(f"Creating new user via OAuth: {email} with role {desired_role}")
            db_user = UserORM(
                id=user_id,
                email=str(email),
                username=name,
                organization=None,
                hashed_password="",
                role=desired_role,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                plan=SubscriptionPlan.COMMUNITY.value,
                features=[],
            )
            db.add(db_user)
            db.commit()
        else:
            logger.info(f"Existing user logging in via OAuth: {email}")
            if str(email).lower() in set(settings.ADMIN_EMAILS or []) and (db_user.role != UserRole.ADMIN):
                logger.info(f"Upgrading user {email} to admin role")
                db_user.role = UserRole.ADMIN
                db.commit()
    except Exception as e:
        logger.exception(f"Database error during OAuth user creation/update: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")

    # Issue platform tokens
    plan = db_user.plan or SubscriptionPlan.COMMUNITY.value
    features = db_user.features or []

    platform_access = create_access_token(
        cast(str, db_user.id),
        cast(str, db_user.email),
        UserRole(cast(str, db_user.role)),
        plan=cast(str, plan),
        features=cast(list[str], features)
    )
    platform_refresh = create_refresh_token(cast(str, db_user.id))

    user = User(
        id=cast(str, db_user.id),
        email=cast(str, db_user.email),
        username=cast(str, db_user.username) if db_user.username else cast(str, db_user.email).split('@')[0],
        organization=cast(str | None, db_user.organization),
        role=UserRole(cast(str, db_user.role)),
        is_active=bool(db_user.is_active),
        created_at=cast(datetime, db_user.created_at),
        plan=cast(str, plan),
    )

    # Redirect back to frontend with tokens & user info (base64 JSON to avoid encoding issues)
    # Use Pydantic v2 JSON mode to ensure datetime and other types are JSON serializable
    user_json = user.model_dump(mode="json")
    payload = {
        "access_token": platform_access,
        "refresh_token": platform_refresh,
        "user": user_json,
        "provider": "google",
    }
    qp = urlencode({
        "oauth": "google",
        "data": base64.urlsafe_b64encode(json.dumps(payload).encode()).decode(),
    })
    return RedirectResponse(url=f"{frontend_redirect}?{qp}")
