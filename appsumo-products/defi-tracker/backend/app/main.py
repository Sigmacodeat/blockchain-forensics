from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import random
from datetime import datetime
import os
import sys
import httpx
from fastapi.responses import Response

# Add shared modules for optional AppSumo auth/integration (best-effort)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
try:
    from auth import decode_access_token, create_access_token, TokenData  # type: ignore
    from appsumo import activate_license, check_feature_access, PLAN_LIMITS  # type: ignore
except Exception:
    TokenData = None  # type: ignore

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
    title="DeFi Yield Tracker API",
    version="2.0.0",
    description="Track DeFi yields, APY, and farming opportunities across protocols"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PositionRequest(BaseModel):
    wallet: str
    chain: str = "ethereum"

class TraceStartRequest(BaseModel):
    source_address: str
    direction: Optional[str] = "forward"
    max_depth: Optional[int] = 3
    max_nodes: Optional[int] = 500
    save_to_graph: Optional[bool] = False

@app.get("/")
def root():
    return {
        "message": "DeFi Yield Tracker API",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "Yield Tracking",
            "APY Monitoring",
            "Farming Opportunities",
            "Multi-Protocol Support",
            "IL Calculator"
        ]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "protocols_tracked": 500,
        "chains_supported": 15,
        "tvl_total": "125B"
    }

@app.get("/api/protocols")
async def get_protocols():
    """Get top DeFi protocols with yields"""
    protocols = [
        {
            "name": "Aave",
            "chain": "Ethereum",
            "tvl": round(random.uniform(5, 15), 2) * 1e9,
            "apy_avg": round(random.uniform(2, 8), 2),
            "top_pool": {
                "asset": "USDC",
                "apy": round(random.uniform(3, 10), 2),
                "tvl": round(random.uniform(500, 2000), 2) * 1e6
            }
        },
        {
            "name": "Uniswap V3",
            "chain": "Ethereum",
            "tvl": round(random.uniform(3, 8), 2) * 1e9,
            "apy_avg": round(random.uniform(5, 15), 2),
            "top_pool": {
                "asset": "ETH/USDC",
                "apy": round(random.uniform(10, 25), 2),
                "tvl": round(random.uniform(200, 800), 2) * 1e6
            }
        },
        {
            "name": "Curve",
            "chain": "Ethereum",
            "tvl": round(random.uniform(4, 10), 2) * 1e9,
            "apy_avg": round(random.uniform(3, 12), 2),
            "top_pool": {
                "asset": "3pool",
                "apy": round(random.uniform(5, 15), 2),
                "tvl": round(random.uniform(1000, 3000), 2) * 1e6
            }
        },
        {
            "name": "Lido",
            "chain": "Ethereum",
            "tvl": round(random.uniform(15, 35), 2) * 1e9,
            "apy_avg": round(random.uniform(3, 5), 2),
            "top_pool": {
                "asset": "stETH",
                "apy": round(random.uniform(3.5, 4.5), 2),
                "tvl": round(random.uniform(15000, 30000), 2) * 1e6
            }
        },
        {
            "name": "GMX",
            "chain": "Arbitrum",
            "tvl": round(random.uniform(0.4, 1.2), 2) * 1e9,
            "apy_avg": round(random.uniform(15, 40), 2),
            "top_pool": {
                "asset": "GLP",
                "apy": round(random.uniform(20, 45), 2),
                "tvl": round(random.uniform(300, 800), 2) * 1e6
            }
        }
    ]
    
    return {
        "total": 500,
        "top_protocols": protocols
    }

@app.post("/api/positions")
async def get_positions(request: PositionRequest):
    """Get DeFi positions for a wallet"""
    wallet = request.wallet
    
    if not wallet.startswith('0x') or len(wallet) != 42:
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    positions = []
    total_value = 0
    total_yield_daily = 0
    
    protocols = ["Aave", "Uniswap", "Curve", "Lido", "Compound"]
    assets = ["USDC", "ETH", "DAI", "WBTC", "stETH"]
    
    num_positions = random.randint(2, 6)
    for i in range(num_positions):
        value = round(random.uniform(500, 50000), 2)
        apy = round(random.uniform(2, 35), 2)
        daily_yield = round((value * apy / 100) / 365, 2)
        
        total_value += value
        total_yield_daily += daily_yield
        
        positions.append({
            "protocol": random.choice(protocols),
            "asset": random.choice(assets),
            "value_usd": value,
            "apy": apy,
            "daily_yield": daily_yield,
            "position_type": random.choice(["Lending", "LP", "Staking", "Farming"]),
            "health_factor": round(random.uniform(1.5, 5.0), 2) if random.random() > 0.5 else None
        })
    
    return {
        "wallet": wallet,
        "positions": positions,
        "total_positions": len(positions),
        "total_value_usd": round(total_value, 2),
        "daily_yield_usd": round(total_yield_daily, 2),
        "monthly_yield_usd": round(total_yield_daily * 30, 2),
        "yearly_yield_usd": round(total_yield_daily * 365, 2),
        "avg_apy": round(sum(p["apy"] for p in positions) / len(positions), 2),
        "last_updated": datetime.utcnow().isoformat()
    }

@app.get("/api/opportunities")
async def get_opportunities():
    """Get best yield farming opportunities"""
    opportunities = [
        {
            "protocol": "GMX",
            "chain": "Arbitrum",
            "pool": "GLP",
            "apy": round(random.uniform(25, 45), 2),
            "tvl": round(random.uniform(300, 800), 2),
            "risk_level": "medium",
            "assets_required": ["ETH", "USDC", "WBTC"],
            "il_risk": "low"
        },
        {
            "protocol": "Uniswap V3",
            "chain": "Ethereum",
            "pool": "ETH/USDC 0.05%",
            "apy": round(random.uniform(15, 30), 2),
            "tvl": round(random.uniform(500, 1500), 2),
            "risk_level": "medium-high",
            "assets_required": ["ETH", "USDC"],
            "il_risk": "medium"
        },
        {
            "protocol": "Curve",
            "chain": "Ethereum",
            "pool": "3pool + CRV",
            "apy": round(random.uniform(8, 18), 2),
            "tvl": round(random.uniform(1000, 3000), 2),
            "risk_level": "low",
            "assets_required": ["USDC", "USDT", "DAI"],
            "il_risk": "very-low"
        }
    ]
    
    return {
        "total": 50,
        "top_opportunities": opportunities,
        "filters": ["APY > 15%", "TVL > $1M", "Risk: Low-Medium"]
    }

@app.get("/api/stats")
async def get_stats():
    """Get platform statistics"""
    return {
        "protocols_tracked": 500,
        "total_tvl": round(random.uniform(100, 150), 2),
        "chains_supported": 15,
        "avg_apy": round(random.uniform(5, 12), 2),
        "highest_apy": round(random.uniform(50, 150), 2),
        "users_tracked": random.randint(5000, 25000),
        "last_updated": datetime.utcnow().isoformat()
    }

@app.post("/api/trace/start")
async def trace_start_proxy(req: TraceStartRequest):
    """Proxy zu Haupt-Backend /api/v1/trace/start (falls konfiguriert), sonst 501."""
    if not MAIN_BACKEND_URL:
        raise HTTPException(status_code=501, detail="MAIN_BACKEND_URL not configured")
    try:
        payload = {
            "source_address": req.source_address,
            "direction": req.direction,
            "max_depth": req.max_depth,
            "max_nodes": req.max_nodes,
            "save_to_graph": req.save_to_graph,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{MAIN_BACKEND_URL}/api/v1/trace/start",
                headers=_main_headers(),
                json=payload,
            )
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {e}")

@app.get("/api/trace/{trace_id}/report")
async def trace_report_proxy(trace_id: str, format: str = "json"):
    """Proxy zu Haupt-Backend /api/v1/trace/id/{trace_id}/report?format=..."""
    if not MAIN_BACKEND_URL:
        raise HTTPException(status_code=501, detail="MAIN_BACKEND_URL not configured")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{MAIN_BACKEND_URL}/api/v1/trace/id/{trace_id}/report",
                headers=_main_headers(),
                params={"format": format},
            )
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        media = "application/json"
        if format == "pdf":
            media = "application/pdf"
        elif format == "csv":
            media = "text/csv"
        return Response(content=resp.content, media_type=media)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
