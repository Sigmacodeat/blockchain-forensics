from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import random
from datetime import datetime

app = FastAPI(title="AI Dashboard Commander API", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
                  allow_methods=["*"], allow_headers=["*"])

class CommandRequest(BaseModel):
    command: str
    context: dict = {}

@app.get("/")
def root():
    return {"message": "AI Dashboard Commander API", "status": "running", "version": "2.0.0",
            "features": ["Natural Language Commands", "Smart Widgets", "Auto-Actions", "Voice Control"]}

@app.get("/health")
def health():
    return {"status": "healthy", "commands_processed": 12547, "widgets_active": 25}

@app.post("/api/execute-command")
async def execute_command(request: CommandRequest):
    cmd = request.command.lower()
    action = "unknown"
    result = {}
    
    if "show" in cmd or "display" in cmd:
        action = "display"
        result = {"widget": "Analytics", "data": {"value": random.randint(1000, 10000)}}
    elif "create" in cmd or "add" in cmd:
        action = "create"
        result = {"created": "New Widget", "id": random.randint(100, 999)}
    elif "update" in cmd or "refresh" in cmd:
        action = "update"
        result = {"updated": True, "timestamp": datetime.utcnow().isoformat()}
    
    return {"command": request.command, "action": action, "result": result, 
            "executed_at": datetime.utcnow().isoformat()}

@app.get("/api/widgets")
async def get_widgets():
    widgets = [{"id": i, "name": f"Widget {i}", "type": random.choice(["Chart", "Table", "Stats"])}
               for i in range(1, 11)]
    return {"total": 25, "widgets": widgets}

@app.get("/api/stats")
async def get_stats():
    return {"commands_processed": 12547, "widgets_active": 25, "users": 1247}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
