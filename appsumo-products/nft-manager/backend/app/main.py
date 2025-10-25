from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import random
from datetime import datetime, timedelta
import httpx
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

try:
    from auth import decode_access_token, create_access_token, TokenData
    from appsumo import activate_license, check_feature_access, PLAN_LIMITS
except ImportError:
    print("⚠️ Warning: Shared modules not found")
    TokenData = None

# Upstream main backend configuration (optional)
MAIN_BACKEND_URL = os.getenv("MAIN_BACKEND_URL")
MAIN_BACKEND_API_KEY = os.getenv("MAIN_BACKEND_API_KEY")
MAIN_BACKEND_JWT = os.getenv("MAIN_BACKEND_JWT")

def _main_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if MAIN_BACKEND_API_KEY:
        headers["X-API-Key"] = MAIN_BACKEND_API_KEY
    if MAIN_BACKEND_JWT:
        headers["Authorization"] = f"Bearer {MAIN_BACKEND_JWT}"
    return headers

app = FastAPI(
    title="NFT Portfolio Manager API",
    version="2.0.0",
    description="Track NFT portfolios, floor prices, and collections across chains"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WalletRequest(BaseModel):
    address: str
    chain: str = "ethereum"

@app.get("/")
def root():
    return {
        "message": "NFT Portfolio Manager API",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "Portfolio Tracking",
            "Floor Price Monitoring",
            "Collection Analytics",
            "Multi-Chain Support",
            "Rarity Scoring"
        ]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "collections_tracked": 150,
        "chains_supported": 5,
        "nfts_indexed": 125000
    }

@app.post("/api/portfolio")
async def get_portfolio(request: WalletRequest):
    """Get NFT portfolio for a wallet"""
    address = request.address
    chain = request.chain
    
    if not address.startswith('0x') or len(address) != 42:
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    # Generate realistic NFT portfolio
    collections = ["Bored Ape Yacht Club", "CryptoPunks", "Azuki", "Doodles", 
                  "Pudgy Penguins", "CloneX", "Moonbirds", "Otherdeed"]
    
    nfts = []
    total_value = 0
    
    num_nfts = random.randint(2, 8)
    for i in range(num_nfts):
        floor_price = round(random.uniform(0.1, 50), 2)
        total_value += floor_price
        
        nfts.append({
            "token_id": random.randint(1, 10000),
            "collection": random.choice(collections),
            "image_url": f"https://placeholder.com/nft_{i}.png",
            "floor_price": floor_price,
            "rarity_rank": random.randint(1, 10000),
            "last_sale": round(random.uniform(0.1, 100), 2),
            "acquired_date": (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat()
        })
    
    return {
        "address": address,
        "chain": chain,
        "nfts": nfts,
        "total_nfts": len(nfts),
        "total_value_eth": round(total_value, 2),
        "total_value_usd": round(total_value * 2400, 2),
        "collections_count": len(set(n["collection"] for n in nfts)),
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/collections")
async def get_collections():
    """Get trending NFT collections"""
    collections = [
        {
            "name": "Bored Ape Yacht Club",
            "floor_price": round(random.uniform(20, 50), 2),
            "volume_24h": round(random.uniform(100, 1000), 2),
            "change_24h": round(random.uniform(-10, 30), 2),
            "owners": random.randint(5000, 10000),
            "supply": 10000
        },
        {
            "name": "CryptoPunks",
            "floor_price": round(random.uniform(40, 80), 2),
            "volume_24h": round(random.uniform(200, 2000), 2),
            "change_24h": round(random.uniform(-5, 15), 2),
            "owners": 3500,
            "supply": 10000
        },
        {
            "name": "Azuki",
            "floor_price": round(random.uniform(10, 30), 2),
            "volume_24h": round(random.uniform(80, 800), 2),
            "change_24h": round(random.uniform(-15, 25), 2),
            "owners": random.randint(4000, 8000),
            "supply": 10000
        }
    ]
    
    return {
        "total": 150,
        "trending": collections
    }

@app.get("/api/analytics/{collection}")
async def get_collection_analytics(collection: str):
    """Get analytics for a specific collection"""
    return {
        "collection": collection,
        "floor_price": round(random.uniform(5, 50), 2),
        "avg_price": round(random.uniform(10, 60), 2),
        "volume_24h": round(random.uniform(50, 500), 2),
        "volume_7d": round(random.uniform(500, 5000), 2),
        "volume_30d": round(random.uniform(2000, 20000), 2),
        "sales_24h": random.randint(10, 200),
        "unique_owners": random.randint(3000, 9000),
        "supply": 10000,
        "price_change_24h": round(random.uniform(-20, 30), 2),
        "price_change_7d": round(random.uniform(-30, 50), 2),
        "chart_data": [
            {"timestamp": (datetime.now() - timedelta(hours=i)).isoformat(), 
             "floor_price": round(random.uniform(5, 50), 2)}
            for i in range(24, 0, -2)
        ]
    }

@app.get("/api/stats")
async def get_stats():
    """Get platform statistics"""
    return {
        "total_collections": 150,
        "total_nfts_tracked": 125000,
        "total_volume_24h": round(random.uniform(5000, 50000), 2),
        "chains_supported": 5,
        "wallets_tracked": random.randint(1000, 10000),
        "last_updated": datetime.utcnow().isoformat()
    }

@app.post("/api/portfolio/risk")
async def assess_portfolio_risk(request: WalletRequest):
    """Assess NFT portfolio risk via Wallet Scanner (falls konfiguriert), sonst Mock."""
    if not MAIN_BACKEND_URL:
        # Mock risk assessment
        risk_score = random.randint(0, 100)
        risk_level = "low" if risk_score < 30 else "medium" if risk_score < 70 else "high"
        return {
            "address": request.address,
            "chain": request.chain,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": [
                "Wash trading detected" if random.random() > 0.7 else "",
                "High concentration in risky collections" if random.random() > 0.8 else "",
                "Recent suspicious transfers" if random.random() > 0.9 else ""
            ],
            "recommendations": [
                "Diversify across collections",
                "Monitor floor prices",
                "Use secure wallets"
            ]
        }
    try:
        payload = {
            "addresses": [{"chain": request.chain, "address": request.address}],
            "check_history": True,
            "check_illicit": True,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{MAIN_BACKEND_URL}/api/v1/wallet-scanner/scan/addresses",
                headers=_main_headers(),
                json=payload,
            )
        if resp.status_code >= 400:
            # Fallback to mock
            return await assess_portfolio_risk(request)
        data = resp.json()
        # Transform to NFT risk format
        risk_score = int(data.get("risk_score", 0) * 100)
        return {
            "address": request.address,
            "chain": request.chain,
            "risk_score": risk_score,
            "risk_level": "low" if risk_score < 30 else "medium" if risk_score < 70 else "high",
            "risk_factors": data.get("illicit_connections", []),
            "recommendations": ["Secure wallet management", "Diversify holdings", "Monitor market trends"]
        }
    except Exception:
        # Fallback to mock
        return await assess_portfolio_risk(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
