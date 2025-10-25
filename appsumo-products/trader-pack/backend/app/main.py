from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
from datetime import datetime

app = FastAPI(title="Professional Trader Pack API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                  allow_methods=["*"], allow_headers=["*"])

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
