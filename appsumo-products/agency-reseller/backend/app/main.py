from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import random
from datetime import datetime
import os
import sys

app = FastAPI(title="Agency Reseller Program API", version="2.0.0")

# Add shared modules for AppSumo
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
try:
    from auth import decode_access_token, create_access_token, TokenData
    from appsumo import activate_license
except Exception:
    TokenData = None

security = HTTPBearer()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                  allow_methods=["*"], allow_headers=["*"])

class ResellerRequest(BaseModel):
    company: str
    email: str

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
    user_data = await activate_license(req.license_key, req.email, "agency-reseller")
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
    return {"message": "Agency Reseller Program API", "status": "running", "version": "2.0.0",
            "features": ["White-Label", "Commission Tracking", "Client Management", "Billing"]}

@app.get("/health")
def health():
    return {"status": "healthy", "active_resellers": 47, "total_clients": 284}

@app.post("/api/register-reseller")
async def register_reseller(request: ResellerRequest):
    return {"reseller_id": f"RS-{random.randint(10000,99999)}", "company": request.company,
            "commission_rate": 30, "status": "pending_approval", 
            "registered_at": datetime.utcnow().isoformat()}

@app.get("/api/commission/{reseller_id}")
async def get_commission(reseller_id: str):
    return {"reseller_id": reseller_id, "total_commission": round(random.uniform(1000, 50000), 2),
            "pending": round(random.uniform(500, 5000), 2), "paid": round(random.uniform(5000, 45000), 2),
            "commission_rate": 30}

@app.get("/api/clients/{reseller_id}")
async def get_clients(reseller_id: str):
    clients = [{"id": i, "name": f"Client {i}", "plan": random.choice(["Pro", "Plus", "Enterprise"]),
                "mrr": random.randint(50, 500)} for i in range(1, 6)]
    return {"reseller_id": reseller_id, "total_clients": len(clients), "clients": clients}

@app.get("/api/stats")
async def get_stats():
    return {"active_resellers": 47, "total_clients": 284, "total_mrr": 142500}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
