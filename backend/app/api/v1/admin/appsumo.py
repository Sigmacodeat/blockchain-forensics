"""
AppSumo Admin API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.services.appsumo_service import AppSumoService
from app.api.v1.auth import require_admin

router = APIRouter(prefix="/appsumo", tags=["AppSumo Admin"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCHEMAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GenerateCodesRequest(BaseModel):
    product: str
    tier: int
    count: int
    expires_days: Optional[int] = None


class GenerateCodesResponse(BaseModel):
    success: bool
    codes: List[dict]
    count: int


class AnalyticsResponse(BaseModel):
    total_codes: int
    by_status: dict
    by_product: dict
    active_activations: int
    redemption_rate: float


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/codes/generate", response_model=GenerateCodesResponse)
async def generate_codes(
    request: GenerateCodesRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Generate AppSumo codes (Admin only)"""
    
    # Validate product
    if request.product not in AppSumoService.PRODUCTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid product. Must be one of: {list(AppSumoService.PRODUCTS.keys())}"
        )
    
    # Validate tier
    if request.tier not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tier must be 1, 2, or 3"
        )
    
    # Generate codes
    codes = await AppSumoService.generate_codes_bulk(
        db=db,
        product=request.product,
        tier=request.tier,
        count=request.count,
        admin_id=str(current_user.id),
        expires_days=request.expires_days
    )
    
    return GenerateCodesResponse(
        success=True,
        codes=codes,
        count=len(codes)
    )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Get AppSumo analytics (Admin only)"""
    analytics = await AppSumoService.get_analytics(db)
    return AnalyticsResponse(**analytics)


@router.get("/codes")
async def list_codes(
    product: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """List AppSumo codes with filters (Admin only)"""
    from app.models.appsumo import AppSumoCode
    from sqlalchemy import select
    
    query = select(AppSumoCode)
    
    if product:
        query = query.where(AppSumoCode.product == product)
    if status:
        query = query.where(AppSumoCode.status == status)
    
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    codes = result.scalars().all()
    
    return {
        "codes": [
            {
                "id": str(code.id),
                "code": code.code,
                "product": code.product,
                "tier": code.tier,
                "status": code.status,
                "created_at": code.created_at,
                "redeemed_at": code.redeemed_at,
                "expires_at": code.expires_at
            }
            for code in codes
        ],
        "total": len(codes),
        "limit": limit,
        "offset": offset
    }


@router.get("/products")
async def list_products():
    """List available products with tiers"""
    return {
        "products": AppSumoService.PRODUCTS
    }
