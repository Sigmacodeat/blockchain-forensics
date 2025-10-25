from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Optional
import random
import sys
import os
from datetime import datetime, timedelta

# Add shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

try:
    from auth import decode_access_token, create_access_token, TokenData
    from appsumo import activate_license, check_feature_access, PLAN_LIMITS
except ImportError:
    print("⚠️ Warning: Shared modules not found")
    TokenData = None

app = FastAPI(
    title="CryptoMetrics Analytics Pro API", 
    version="2.0.0",
    description="Multi-chain analytics with AppSumo integration"
)

security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Portfolio(BaseModel):
    total_value: float
    change_24h: float
    assets: List[Dict]

class TaxReportRequest(BaseModel):
    year: int
    jurisdiction: str
    addresses: List[str]

class AppSumoActivation(BaseModel):
    license_key: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Auth Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    if not TokenData:
        raise HTTPException(status_code=501, detail="Auth not configured")
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token_data

# AppSumo Endpoints
@app.post("/api/auth/appsumo/activate", response_model=TokenResponse)
async def activate_appsumo_license(request: AppSumoActivation):
    user_data = await activate_license(request.license_key, request.email, "analytics-pro")
    if not user_data:
        raise HTTPException(status_code=400, detail="Invalid license key")
    
    token = create_access_token({
        "sub": user_data["email"],
        "user_id": user_data["email"],
        "plan": user_data["plan"],
        "plan_tier": user_data["plan_tier"]
    })
    
    return TokenResponse(access_token=token, user=user_data)

@app.get("/api/auth/me")
async def get_me(user: TokenData = Depends(get_current_user)):
    return {"email": user.email, "plan": user.plan}

@app.get("/")
def root():
    return {
        "message": "CryptoMetrics Analytics Pro API",
        "status": "running",
        "version": "1.0.0",
        "features": [
            "Portfolio Tracking (35+ Chains)",
            "Tax Reports (10 Jurisdictions)",
            "NFT Analytics",
            "DeFi Dashboard (500+ Protocols)",
            "White-Label Support",
            "API Access"
        ]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "chains_supported": 35,
        "protocols_tracked": 500,
        "uptime": "99.9%"
    }

@app.get("/api/portfolio/{address}")
async def get_portfolio(address: str):
    """
    Get portfolio for a wallet address
    """
    # Simulate portfolio data
    assets = [
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "balance": round(random.uniform(1, 20), 2),
            "price": round(random.uniform(2000, 3000), 2),
            "value": 0,  # calculated below
            "change": round(random.uniform(-5, 10), 2),
            "allocation": 0  # calculated below
        },
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "balance": round(random.uniform(0.1, 1), 3),
            "price": round(random.uniform(40000, 50000), 2),
            "value": 0,
            "change": round(random.uniform(-3, 8), 2),
            "allocation": 0
        },
        {
            "symbol": "USDT",
            "name": "Tether",
            "balance": round(random.uniform(1000, 10000), 2),
            "price": 1.0,
            "value": 0,
            "change": 0.01,
            "allocation": 0
        }
    ]
    
    # Calculate values
    for asset in assets:
        asset["value"] = round(asset["balance"] * asset["price"], 2)
    
    total_value = sum(a["value"] for a in assets)
    
    # Calculate allocations
    for asset in assets:
        asset["allocation"] = round((asset["value"] / total_value) * 100, 0)
    
    portfolio_change = round(random.uniform(-5, 10), 2)
    
    return {
        "address": address,
        "total_value": round(total_value, 2),
        "change_24h": portfolio_change,
        "assets": assets,
        "chains": ["Ethereum", "Bitcoin", "Polygon"],
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/chains")
async def get_chains():
    """
    Get supported blockchain chains
    """
    return {
        "total": 35,
        "chains": [
            {"name": "Ethereum", "symbol": "ETH", "active": True},
            {"name": "Bitcoin", "symbol": "BTC", "active": True},
            {"name": "Polygon", "symbol": "MATIC", "active": True},
            {"name": "Arbitrum", "symbol": "ARB", "active": True},
            {"name": "Optimism", "symbol": "OP", "active": True},
            {"name": "Base", "symbol": "BASE", "active": True},
            {"name": "Avalanche", "symbol": "AVAX", "active": True},
            {"name": "Solana", "symbol": "SOL", "active": True},
            {"name": "BSC", "symbol": "BNB", "active": True},
            {"name": "Cosmos", "symbol": "ATOM", "active": True}
        ]
    }

@app.post("/api/tax/generate")
async def generate_tax_report(request: TaxReportRequest):
    """
    Generate tax report for specified year and jurisdiction
    """
    jurisdictions = ["US", "DE", "UK", "CA", "AU", "CH", "FR", "IT", "ES", "NL"]
    
    if request.jurisdiction not in jurisdictions:
        raise HTTPException(status_code=400, detail=f"Jurisdiction {request.jurisdiction} not supported")
    
    # Simulate tax report generation
    return {
        "report_id": f"TAX-{request.year}-{request.jurisdiction}-{random.randint(1000, 9999)}",
        "year": request.year,
        "jurisdiction": request.jurisdiction,
        "addresses": len(request.addresses),
        "status": "generated",
        "summary": {
            "total_transactions": random.randint(100, 1000),
            "capital_gains": round(random.uniform(1000, 50000), 2),
            "income": round(random.uniform(500, 10000), 2),
            "deductions": round(random.uniform(100, 5000), 2)
        },
        "download_url": f"/api/tax/download/TAX-{request.year}-{request.jurisdiction}",
        "generated_at": datetime.utcnow().isoformat()
    }

@app.get("/api/defi/protocols")
async def get_defi_protocols():
    """
    Get tracked DeFi protocols
    """
    return {
        "total": 500,
        "top_protocols": [
            {"name": "Uniswap", "tvl": 5200000000, "apy": 8.5},
            {"name": "Aave", "tvl": 4800000000, "apy": 5.2},
            {"name": "Curve", "tvl": 3600000000, "apy": 12.3},
            {"name": "Lido", "tvl": 32000000000, "apy": 4.1},
            {"name": "MakerDAO", "tvl": 7100000000, "apy": 6.8}
        ]
    }

@app.get("/api/nft/collections")
async def get_nft_collections():
    """
    Get NFT collections tracking
    """
    return {
        "total_collections": 150,
        "top_collections": [
            {"name": "Bored Ape Yacht Club", "floor_price": 32.5, "volume_24h": 1245.8},
            {"name": "CryptoPunks", "floor_price": 45.2, "volume_24h": 892.3},
            {"name": "Azuki", "floor_price": 12.8, "volume_24h": 456.7}
        ]
    }

@app.get("/api/stats")
async def get_stats():
    """
    Get platform statistics
    """
    return {
        "total_portfolios": 12458,
        "total_transactions": 1247893,
        "chains_supported": 35,
        "defi_protocols": 500,
        "nft_collections": 150,
        "tax_reports_generated": 3421,
        "avg_response_time": "89ms",
        "uptime": "99.9%"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
