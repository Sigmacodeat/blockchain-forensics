"""
Template Backend für AppSumo Produkte
Kopiere dieses Template und passe es an dein Produkt an
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from auth import decode_access_token, TokenData
from appsumo import verify_license, activate_license, check_feature_access, check_usage_limit
from database import User, create_tables, get_user_by_email, check_rate_limit, increment_api_calls

# Initialize FastAPI
app = FastAPI(
    title="Product Name API",
    version="2.0.0",
    description="Production-ready AppSumo product with auth, billing, and rate limiting"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer()

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class AppSumoActivation(BaseModel):
    license_key: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current user from JWT token"""
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data

async def check_user_rate_limit(user: TokenData = Depends(get_current_user)):
    """Check if user is within rate limits"""
    # In production: Query database
    # For MVP: Simple check based on plan
    pass

async def require_feature(feature: str):
    """Dependency to require a specific feature"""
    async def _require_feature(user: TokenData = Depends(get_current_user)):
        # Extract plan tier from plan name (tier_1 -> 1)
        try:
            tier = int(user.plan.split('_')[1])
        except:
            tier = 1
        
        if not check_feature_access(tier, feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a higher plan tier"
            )
        return user
    return _require_feature

# Auth Endpoints
@app.post("/api/auth/appsumo/activate", response_model=TokenResponse)
async def activate_appsumo_license(request: AppSumoActivation):
    """Activate AppSumo license and create user account"""
    product_id = "your-product-id"  # Change per product
    
    # Activate license
    user_data = await activate_license(request.license_key, request.email, product_id)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license key"
        )
    
    # Create access token
    from auth import create_access_token
    token_payload = {
        "sub": user_data["email"],
        "user_id": user_data["email"],  # Use email as ID for MVP
        "plan": user_data["plan"],
        "plan_tier": user_data["plan_tier"]
    }
    access_token = create_access_token(token_payload)
    
    return TokenResponse(
        access_token=access_token,
        user={
            "email": user_data["email"],
            "plan": user_data["plan"],
            "features": user_data["features"],
            "limits": user_data["limits"]
        }
    )

@app.get("/api/auth/me")
async def get_current_user_info(user: TokenData = Depends(get_current_user)):
    """Get current user information"""
    return {
        "email": user.email,
        "plan": user.plan,
        "user_id": user.user_id
    }

# Health & Status
@app.get("/")
def root():
    return {
        "message": "Product API",
        "version": "2.0.0",
        "status": "running",
        "auth": "enabled",
        "rate_limiting": "enabled"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

# Example Protected Endpoint
@app.get("/api/protected")
@limiter.limit("100/day")
async def protected_endpoint(user: TokenData = Depends(get_current_user)):
    """Example protected endpoint with rate limiting"""
    return {
        "message": "You have access!",
        "user": user.email,
        "plan": user.plan
    }

# Example Feature-Gated Endpoint
@app.get("/api/advanced-feature")
async def advanced_feature(user: TokenData = Depends(require_feature("advanced_features"))):
    """Example endpoint requiring advanced features (Tier 2+)"""
    return {
        "message": "Advanced feature accessed!",
        "user": user.email
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
