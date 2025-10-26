from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import random
from datetime import datetime
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
try:
    from auth import decode_access_token, create_access_token, TokenData
    from appsumo import activate_license
except Exception:
    TokenData = None

app = FastAPI(title="Professional Trader Pack API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                  allow_methods=["*"], allow_headers=["*"])

security = HTTPBearer()

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
    user_data = await activate_license(req.license_key, req.email, "trader-pack")
    if not user_data:
        raise HTTPException(status_code=400, detail="Invalid license key")
    token = create_access_token({
        "sub": user_data["email"],
        "user_id": user_data["email"],
        "plan": user_data["plan"],
        "plan_tier": user_data["plan_tier"],
    })
    return {"access_token": token, "token_type": "bearer", "user": user_data}

@app.get("/api/auth/me")
async def get_me(user: TokenData = Depends(get_current_user)):
    return {"email": user.email, "plan": user.plan}

@app.get("/")
def root():
    return {"message": "Professional Trader Pack API", "status": "running", "version": "2.0.0",
            "features": ["Advanced Charts", "Trading Signals", "Portfolio", "Risk Management", "Alerts"]}

@app.get("/health")
def health():
    return {"status": "healthy", "signals_generated": 847, "active_traders": 234}

@app.get("/api/signals")
async def get_signals():
    signals = [{"id": i, "pair": random.choice(["BTC/USD", "ETH/USD", "SOL/USD"]),
                "type": random.choice(["buy", "sell"]), "confidence": random.randint(60, 95),
                "price": round(random.uniform(1000, 50000), 2)} for i in range(1, 6)]
    return {"total": 847, "signals": signals}

@app.get("/api/portfolio")
async def get_portfolio():
    return {"total_value": round(random.uniform(10000, 100000), 2), 
            "pnl_24h": round(random.uniform(-1000, 2000), 2),
            "positions": random.randint(5, 15), "win_rate": round(random.uniform(50, 75), 1)}

@app.get("/api/stats")
async def get_stats():
    return {"signals_generated": 847, "active_traders": 234, "avg_win_rate": 68.5}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
