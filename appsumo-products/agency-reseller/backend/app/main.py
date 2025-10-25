from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from datetime import datetime

app = FastAPI(title="Agency Reseller Program API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                  allow_methods=["*"], allow_headers=["*"])

class ResellerRequest(BaseModel):
    company: str
    email: str

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
