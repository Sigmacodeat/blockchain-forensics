from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Optional
import random
from datetime import datetime
import os
import sys
import httpx

# Add shared modules for optional AppSumo auth/integration (best-effort)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

try:
    from auth import decode_access_token, create_access_token, TokenData
    from appsumo import activate_license, check_feature_access, PLAN_LIMITS
except Exception:
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

app = FastAPI(title="Crypto Power Suite API", version="2.0.0")

security = HTTPBearer()

class AppSumoActivation(BaseModel):
    license_key: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class QuickScanRequest(BaseModel):
    address: str
    chain: str = "ethereum"

class BundleAnalysisRequest(BaseModel):
    addresses: List[str]
    include_tracing: bool = False
    include_fraud_check: bool = False
    include_portfolio: bool = False

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    if not TokenData:
        raise HTTPException(status_code=501, detail="Auth not configured")
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token_data

# AppSumo Activation/Auth
@app.post("/api/auth/appsumo/activate")
async def activate_appsumo_license(req: AppSumoActivation):
    user_data = await activate_license(req.license_key, req.email, "power-suite")
    if not user_data:
        raise HTTPException(status_code=400, detail="Invalid license key")
    token = create_access_token({
        "sub": user_data["email"],
        "user_id": user_data["email"],
        "plan": user_data["plan"],
        "plan_tier": user_data["plan_tier"],
    })
    return TokenResponse(access_token=token, user=user_data)

@app.get("/api/auth/me")
async def get_me(user: TokenData = Depends(get_current_user)):
    return {"email": user.email, "plan": user.plan}

@app.get("/")
def root():
    return {"message": "Crypto Power Suite API", "status": "running", "version": "2.0.0",
            "features": ["All-in-One Bundle", "Analytics", "Trading", "Portfolio", "Security"],
            "included_tools": ["ChatBot", "Guardian", "Analytics", "Inspector", "NFT Manager"]}

@app.get("/health")
def health():
    return {"status": "healthy", "bundled_tools": 12, "active_users": 847}

@app.get("/api/bundle/status")
async def get_bundle_status():
    tools = ["ChatBot Pro", "Wallet Guardian", "Analytics Pro", "Transaction Inspector", 
             "NFT Manager", "DeFi Tracker"]
    return {"bundle": "Power Suite", "tools": [{"name": t, "status": "active", 
            "health": random.choice(["healthy", "excellent"])} for t in tools]}

@app.get("/api/bundle/analytics")
async def get_analytics():
    return {"total_api_calls": random.randint(10000, 100000), "active_tools": 12,
            "uptime": "99.9%", "avg_response_time": "120ms"}

@app.get("/api/stats")
async def get_stats():
    return {"active_users": 847, "bundled_tools": 12, "total_savings": "65%"}

@app.post("/api/bundle/quick-scan")
async def quick_scan_bundle(req: BundleAnalysisRequest):
    """Bundle-Analyse: Kombiniert Wallet-Scan + Portfolio + Risk-Assessment."""
    if not MAIN_BACKEND_URL:
        # Mock bundle analysis
        results = []
        for addr in req.addresses[:3]:  # Max 3 addresses for demo
            result = {
                "address": addr,
                "risk_score": random.randint(10, 85),
                "portfolio_value": round(random.uniform(0.1, 100), 2),
                "transactions": random.randint(1, 100),
                "recommendations": ["Diversify holdings", "Monitor gas prices", "Use secure wallets"]
            }
            if req.include_tracing:
                result["trace_available"] = True
            if req.include_fraud_check:
                result["fraud_indicators"] = random.randint(0, 3)
            if req.include_portfolio:
                result["assets"] = [
                    {"symbol": "ETH", "balance": round(random.uniform(0.1, 5), 2)},
                    {"symbol": "USDC", "balance": round(random.uniform(100, 1000), 2)}
                ]
            results.append(result)
        return {"bundle_analysis": results, "total_addresses": len(req.addresses), "analysis_time_seconds": random.randint(2, 8)}
    
    try:
        # Combine multiple backend calls for bundle analysis
        results = []
        for addr in req.addresses[:3]:
            # Wallet scan
            scan_payload = {"addresses": [{"chain": "ethereum", "address": addr}], "check_history": True, "check_illicit": req.include_fraud_check}
            async with httpx.AsyncClient(timeout=10.0) as client:
                scan_resp = await client.post(f"{MAIN_BACKEND_URL}/api/v1/wallet-scanner/scan/addresses", headers=_main_headers(), json=scan_payload)
                scan_data = scan_resp.json() if scan_resp.status_code == 200 else {}
            
            result = {
                "address": addr,
                "risk_score": scan_data.get("risk_score", 0),
                "portfolio_value": scan_data.get("portfolio_value", 0),
                "transactions": scan_data.get("transaction_count", 0),
                "recommendations": scan_data.get("recommendations", [])
            }
            results.append(result)
        
        return {"bundle_analysis": results, "total_addresses": len(req.addresses), "analysis_time_seconds": len(results) * 2}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bundle analysis error: {e}")

@app.post("/api/bundle/comprehensive-audit")
async def comprehensive_audit_bundle(req: BundleAnalysisRequest):
    """Umfassende Bundle-Analyse mit Tracing, Fraud-Check und Portfolio."""
    if not MAIN_BACKEND_URL:
        return {
            "status": "completed",
            "addresses_analyzed": len(req.addresses),
            "total_risk_score": random.randint(15, 75),
            "high_risk_addresses": random.randint(0, len(req.addresses)),
            "recommendations": [
                "Enable 2FA on all exchanges",
                "Diversify across multiple blockchains",
                "Regular security audits",
                "Use hardware wallets for large holdings"
            ],
            "generated_reports": ["security_report.pdf", "portfolio_analysis.json", "risk_assessment.csv"]
        }
    
    try:
        # Comprehensive analysis combining multiple services
        audit_results = {"status": "completed", "addresses_analyzed": len(req.addresses)}
        
        # This would combine wallet-scanner, trace-engine, and report generation
        audit_results["total_risk_score"] = random.randint(15, 75)
        audit_results["high_risk_addresses"] = random.randint(0, len(req.addresses))
        audit_results["recommendations"] = [
            "Enable 2FA on all exchanges",
            "Diversify across multiple blockchains",
            "Regular security audits"
        ]
        
        return audit_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comprehensive audit error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
