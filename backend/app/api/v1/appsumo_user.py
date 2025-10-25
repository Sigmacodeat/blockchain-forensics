"""
AppSumo User API - Code Redemption
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.services.appsumo_service import AppSumoService
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/appsumo", tags=["AppSumo"])


class RedeemCodeRequest(BaseModel):
    code: str


class RedeemCodeResponse(BaseModel):
    success: bool
    product: str = None
    product_name: str = None
    tier: int = None
    features: dict = None
    error: str = None


@router.post("/redeem", response_model=RedeemCodeResponse)
async def redeem_code(
    request: RedeemCodeRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Redeem AppSumo code"""
    
    # Get IP and User-Agent
    ip_address = http_request.client.host
    user_agent = http_request.headers.get('user-agent')
    
    # Redeem
    result = await AppSumoService.redeem_code(
        db=db,
        code=request.code,
        user_id=str(current_user.id),
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not result['success']:
        return RedeemCodeResponse(
            success=False,
            error=result['error']
        )
    
    return RedeemCodeResponse(
        success=True,
        product=result['product'],
        product_name=result['product_name'],
        tier=result['tier'],
        features=result['features']
    )


@router.get("/my-products")
async def get_my_products(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's activated products"""
    activations = await AppSumoService.get_user_activations(
        db=db,
        user_id=str(current_user.id)
    )
    
    return {
        "products": activations,
        "count": len(activations)
    }
