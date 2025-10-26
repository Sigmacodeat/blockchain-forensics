from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import random
from datetime import datetime
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

def _main_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if MAIN_BACKEND_API_KEY:
        headers["X-API-Key"] = MAIN_BACKEND_API_KEY
    if MAIN_BACKEND_JWT:
        headers["Authorization"] = f"Bearer {MAIN_BACKEND_JWT}"
    return headers

app = FastAPI(title="Complete Security Analytics API", version="2.0.0")

security = HTTPBearer()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                  allow_methods=["*"], allow_headers=["*"])

class AppSumoActivation(BaseModel):
    license_key: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    if not TokenData:
        raise HTTPException(status_code=501, detail="Auth not configured")
    token_data = decode_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token_data

@app.post("/api/auth/appsumo/activate")
async def activate_appsumo_license(req: AppSumoActivation):
    user_data = await activate_license(req.license_key, req.email, "complete-security")
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
    return {"message": "Complete Security Analytics API", "status": "running", "version": "2.0.0",
            "features": ["Threat Detection", "Firewall", "Audit Logs", "Compliance", "Real-Time Alerts"]}

@app.get("/health")
def health():
    return {"status": "healthy", "threats_blocked": 1247, "monitored_addresses": 5421}

@app.get("/api/security/scan")
async def security_scan():
    return {"scan_id": f"SEC-{random.randint(10000,99999)}", "threats_found": random.randint(0, 5),
            "risk_level": random.choice(["low", "medium", "high"]), 
            "scanned_at": datetime.utcnow().isoformat()}

@app.get("/api/security/threats")
async def get_threats():
    threats = [{"id": i, "type": random.choice(["Phishing", "Malware", "Scam", "Hack"]),
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "status": random.choice(["blocked", "monitoring"])} for i in range(1, 6)]
    return {"total_threats": 1247, "active_threats": threats}

@app.get("/api/security/rules")
async def get_firewall_rules():
    """Proxy zu Haupt-Backend /api/v1/firewall/rules (falls konfiguriert), sonst Mock."""
    if not MAIN_BACKEND_URL:
        # Mock response
        return {"rules": [
            {"rule_id": "rule_1", "rule_type": "address", "action": "block", "enabled": True},
            {"rule_id": "rule_2", "rule_type": "contract", "action": "warn", "enabled": True}
        ]}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{MAIN_BACKEND_URL}/api/v1/firewall/rules",
                headers=_main_headers(),
            )
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {e}")

@app.get("/api/stats")
async def get_stats():
    return {"threats_blocked": 1247, "addresses_monitored": 5421, "uptime": "99.9%"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
