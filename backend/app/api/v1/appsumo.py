"""
AppSumo API Endpoints

Provides:
- Public endpoints (Code-Validation, Redemption)
- User endpoints (My Products)
- Admin endpoints (Code-Generation, Metrics)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import logging

from app.services.appsumo_service import AppSumoService
from app.models.appsumo import (
    AppSumoCodeRedemption,
    AppSumoCodeInfo,
    UserProductDetails,
    AppSumoMetricsSummary
)
from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin
from app.auth.jwt import create_access_token, create_refresh_token, get_password_hash
from app.auth.models import AuthResponse, Token, User, UserRole
from app.models.user import UserORM, SubscriptionPlan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appsumo", tags=["appsumo"])

# ==========================================
# PUBLIC ENDPOINTS (No Auth)
# ==========================================
@router.post("/validate-code", response_model=AppSumoCodeInfo)
async def validate_code(
    code: str = Query(..., description="AppSumo redemption code"),
    db: Session = Depends(get_db)
):
    """
    Validiert AppSumo-Code OHNE einzulösen
    
    Use Case: User gibt Code ein → sieht welches Product/Tier er bekommt
    """
    service = AppSumoService(db)
    code_info = service.validate_code(code)
    
    if not code_info.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=code_info.reason
        )
    
    return code_info


@router.post("/redeem", response_model=AuthResponse)
async def redeem_code(
    redemption: AppSumoCodeRedemption,
    db: Session = Depends(get_db)
):
    """
    Löst AppSumo-Code ein + erstellt User-Account
    
    Flow:
    1. Validate Code
    2. Create User (or find existing)
    3. Activate Product
    4. Return JWT for Auto-Login
    """
    service = AppSumoService(db)
    
    # 1. Validate Code first
    code_info = service.validate_code(redemption.code)
    if not code_info.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid code: {code_info.reason}"
        )
    
    # 2. Check if email exists
    existing_user = db.query(UserORM).filter(UserORM.email == redemption.email).first()

    if existing_user:
        # User exists → only activate product
        user_id = existing_user.id
        logger.info(f"Existing user {redemption.email} redeeming code")
    else:
        # Create new user
        now = datetime.utcnow()
        new_user = UserORM(
            email=redemption.email,
            username=redemption.email.split('@')[0],
            hashed_password=get_password_hash(redemption.password),
            role=UserRole.ANALYST.value,
            plan=SubscriptionPlan.COMMUNITY.value,
            is_active=True,
            created_at=now,
            updated_at=now,
            features=[],
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        user_id = new_user.id
        logger.info(f"Created new user {redemption.email}")
    
    # 3. Redeem code
    result = await service.redeem_code(
        code=redemption.code,
        user_id=str(user_id),
        email=redemption.email
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    # 4. Generate JWT for Auto-Login using central utilities
    user_row = db.query(UserORM).filter(UserORM.id == user_id).first()
    if not user_row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User not found after redemption")

    plan = user_row.plan or SubscriptionPlan.COMMUNITY.value
    features = list(user_row.features or [])
    role_enum = UserRole(str(user_row.role))

    access_token = create_access_token(
        str(user_row.id),
        str(user_row.email),
        role_enum,
        plan=str(plan),
        features=features
    )
    refresh_token = create_refresh_token(str(user_row.id))

    user_response = User(
        id=str(user_row.id),
        email=str(user_row.email),
        username=str(user_row.username) if user_row.username else str(user_row.email).split('@')[0],
        organization=str(user_row.organization) if user_row.organization else None,
        organization_type=str(user_row.organization_type) if user_row.organization_type else None,
        organization_name=str(user_row.organization_name) if user_row.organization_name else None,
        role=role_enum,
        is_active=bool(user_row.is_active),
        created_at=user_row.created_at or datetime.utcnow(),
        plan=str(plan),
        institutional_discount_requested=bool(user_row.institutional_discount_requested),
        institutional_discount_verified=bool(user_row.institutional_discount_verified),
        verification_status=user_row.verification_status or "none",
    )

    tokens = Token(access_token=access_token, refresh_token=refresh_token)

    return AuthResponse(user=user_response, tokens=tokens)


# ==========================================
# USER ENDPOINTS (Authenticated)
# ==========================================
@router.get("/my-products", response_model=List[UserProductDetails])
async def get_my_products(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all activated products for current user
    
    Use Case: User-Dashboard zeigt alle gekauften Produkte
    """
    service = AppSumoService(db)
    return service.get_user_products(str(current_user.id))


@router.get("/has-access/{product}")
async def check_product_access(
    product: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Checks if user has access to a specific product
    
    Use Case: Frontend prüft ob Feature sichtbar sein soll
    """
    service = AppSumoService(db)
    has_access = service.has_product_access(str(current_user.id), product)
    tier = service.get_product_tier(str(current_user.id), product) if has_access else None
    
    return {
        "product": product,
        "has_access": has_access,
        "tier": tier
    }


# ==========================================
# ADMIN ENDPOINTS
# ==========================================
@router.post("/admin/generate-codes", dependencies=[Depends(require_admin)])
async def generate_codes(
    product: str = Query(..., description="Product: chatbot, firewall, inspector, commander"),
    tier: int = Query(..., ge=1, le=3, description="Tier: 1, 2, 3"),
    count: int = Query(..., ge=1, le=10000, description="Number of codes"),
    batch_id: Optional[str] = Query(None, description="Optional batch identifier"),
    db: Session = Depends(get_db)
):
    """
    Generiert AppSumo-Codes für Upload
    
    Use Case: Admin generiert 1000 Codes → CSV-Download → an AppSumo schicken
    """
    if product not in ["chatbot", "firewall", "inspector", "commander"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product. Must be: chatbot, firewall, inspector, commander"
        )
    
    service = AppSumoService(db)
    
    logger.info(f"Admin generating {count} codes for {product} Tier {tier}")
    
    codes = service.generate_codes(
        product=product,
        tier=tier,
        count=count,
        batch_id=batch_id
    )
    
    return {
        "success": True,
        "product": product,
        "tier": tier,
        "count": len(codes),
        "batch_id": batch_id or f"{product}-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "codes": codes,
        "download_hint": "Save these codes to CSV and upload to AppSumo"
    }


@router.get("/admin/metrics", dependencies=[Depends(require_admin)])
async def get_metrics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated AppSumo metrics
    
    Use Case: Admin-Dashboard zeigt Revenue, Redemptions, etc.
    """
    service = AppSumoService(db)
    return service.get_metrics_summary(start_date, end_date)


@router.get("/admin/recent-redemptions", dependencies=[Depends(require_admin)])
async def get_recent_redemptions(
    limit: int = Query(10, ge=1, le=100, description="Number of redemptions"),
    db: Session = Depends(get_db)
):
    """
    Returns recent code redemptions
    
    Use Case: Admin-Dashboard zeigt letzte Aktivierungen
    """
    service = AppSumoService(db)
    return service.get_recent_redemptions(limit)


@router.get("/admin/stats", dependencies=[Depends(require_admin)])
async def get_admin_stats(
    db: Session = Depends(get_db)
):
    """
    Returns quick stats für Admin-Dashboard
    """
    from app.models.appsumo import AppSumoCodeORM, UserProductORM
    from sqlalchemy import func
    
    total_codes = db.query(func.count(AppSumoCodeORM.id)).scalar()
    redeemed_codes = db.query(func.count(AppSumoCodeORM.id)).filter(
        AppSumoCodeORM.status == "redeemed"
    ).scalar()
    active_products = db.query(func.count(UserProductORM.id)).filter(
        UserProductORM.status == "active"
    ).scalar()
    
    return {
        "total_codes_generated": total_codes,
        "codes_redeemed": redeemed_codes,
        "codes_remaining": total_codes - redeemed_codes,
        "conversion_rate": round((redeemed_codes / total_codes * 100), 2) if total_codes > 0 else 0,
        "active_products": active_products
    }
