"""KYT (Know Your Transaction) API - Real-Time Transaction Monitoring"""
import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Body
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
try:
    # Pydantic v2
    from pydantic import model_validator  # type: ignore
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    model_validator = None  # type: ignore
    ConfigDict = None  # type: ignore
try:
    # Pydantic v1
    from pydantic.class_validators import root_validator  # type: ignore
except Exception:  # pragma: no cover
    root_validator = None  # type: ignore

from app.services.kyt_engine import kyt_engine, Transaction, RiskLevel
from app.auth.dependencies import require_plan, has_plan
from app.auth.jwt import decode_token
from app.db.postgres_client import postgres_client
import hashlib
import os

router = APIRouter()
logger = logging.getLogger(__name__)

class AnalyzeTransactionRequest(BaseModel):
    """Request model for transaction analysis."""
    tx_hash: Optional[str] = Field(None, description="Transaction hash")
    chain: str = Field(..., description="Blockchain name")
    # Accept legacy keys via pre-normalization ('from','to','value')
    from_address: Optional[str] = Field(None, description="Sender address")
    to_address: Optional[str] = Field(None, description="Receiver address")
    value_eth: float = Field(0.0, description="Value in ETH")
    value_usd: Optional[float] = Field(None, description="Value in USD")
    block_number: Optional[int] = Field(None, description="Block number")
    timestamp: Optional[datetime] = Field(None, description="Transaction timestamp")

    # Pydantic v2 config
    if ConfigDict is not None:  # type: ignore
        model_config = ConfigDict(populate_by_name=True, extra='ignore')  # type: ignore

    # Pre-normalization to support legacy keys on both pydantic v1 and v2
    if model_validator is not None:
        @model_validator(mode="before")  # type: ignore
        def _normalize(cls, values):  # type: ignore
            if isinstance(values, dict):
                v = dict(values)
                if 'from' in v and 'from_address' not in v:
                    v['from_address'] = v.get('from')
                if 'to' in v and 'to_address' not in v:
                    v['to_address'] = v.get('to')
                if 'value' in v and 'value_eth' not in v:
                    v['value_eth'] = v.get('value')
                return v
            return values
    elif root_validator is not None:
        @root_validator(pre=True)  # type: ignore
        def _normalize(cls, values):  # type: ignore
            if isinstance(values, dict):
                v = dict(values)
                if 'from' in v and 'from_address' not in v:
                    v['from_address'] = v.get('from')
                if 'to' in v and 'to_address' not in v:
                    v['to_address'] = v.get('to')
                if 'value' in v and 'value_eth' not in v:
                    v['value_eth'] = v.get('value')
                return v
            return values

async def _authorize_ws(ws: WebSocket, required_plan: str = "business") -> dict | None:
    """Authorize WebSocket using Bearer JWT or X-API-Key. Returns user dict or None."""
    # Try Bearer JWT
    try:
        auth = ws.headers.get("authorization") or ws.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            token_data = decode_token(token)
            if token_data:
                user = {
                    "user_id": getattr(token_data, "user_id", None),
                    "plan": getattr(token_data, "plan", "community"),
                    "email": getattr(token_data, "email", None),
                }
                # plan gate for JWT users
                if not has_plan(user, required_plan):
                    return None
                return user
    except Exception:
        pass

    # Try X-API-Key (DB-backed)
    try:
        api_key = ws.headers.get("x-api-key") or ws.query_params.get("api_key")  # type: ignore[attr-defined]
        if api_key:
            h = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
            # In TEST_MODE or if DB unavailable, deny to avoid bypass
            if os.getenv("TEST_MODE") == "1" or not getattr(postgres_client, "pool", None):
                return None
            row = await postgres_client.fetchrow(
                "SELECT tier FROM api_keys WHERE hash_sha256 = $1 AND revoked = FALSE LIMIT 1",
                h,
            )
            if row:
                # Accept valid API keys (tier governs rate limits via gateway; WS plan-gate skipped)
                return {"user_id": "api-key", "plan": row.get("tier", "pro")}
    except Exception:
        pass
    return None


@router.websocket("/ws/kyt")
async def kyt_stream(ws: WebSocket):
    """WebSocket endpoint for real-time KYT alerts.
    
    Client sends: {"action": "subscribe", "user_id": "..."}
    Server sends: {"type": "kyt.result", "data": {...}}
    """
    # Authorize first (JWT must satisfy business plan; API key must exist and be active)
    user = await _authorize_ws(ws, required_plan="business")
    if not user:
        # 4401 Unauthorized (WS custom code)
        try:
            await ws.close(code=4401)
        except Exception:
            pass
        return

    await ws.accept()
    user_id = None
    queue = None
    
    try:
        # Expect subscribe message
        raw = await ws.receive_text()
        msg = json.loads(raw)
        
        if msg.get("action") != "subscribe":
            await ws.send_text(json.dumps({"type": "error", "detail": "Expected 'subscribe' action"}))
            return
            
        user_id = msg.get("user_id") or "anonymous"
        
        # Subscribe to KYT engine
        queue = kyt_engine.subscribe(user_id)
        
        await ws.send_text(json.dumps({
            "type": "kyt.subscribed",
            "user_id": user_id
        }))
        
        # Stream KYT results
        while True:
            # Wait for result from engine
            result = await queue.get()
            await ws.send_text(json.dumps(result))
            
    except WebSocketDisconnect:
        logger.info(f"KYT WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"KYT WebSocket error: {e}")
        try:
            await ws.send_text(json.dumps({"type": "error", "detail": str(e)}))
        except:
            pass
    finally:
        if user_id and queue:
            kyt_engine.unsubscribe(user_id, queue)

@router.post("/kyt/analyze")
async def analyze_transaction(request: AnalyzeTransactionRequest, current_user: dict = Depends(require_plan("business"))):
    """Analyze a single transaction (REST endpoint).
    
    Args:
        request: Transaction data
        
    Returns:
        KYT analysis result
    """
    try:
        tx = Transaction(
            tx_hash=request.tx_hash or "manual:" + (request.from_address or "") + ":" + (request.to_address or ""),
            chain=request.chain,
            from_address=request.from_address or "",
            to_address=request.to_address or "",
            value_eth=request.value_eth,
            value_usd=request.value_usd or (request.value_eth * 3000),  # Rough estimate
            timestamp=request.timestamp or datetime.now(),
            block_number=request.block_number or 0
        )
        
        result = await kyt_engine.analyze_transaction(tx)
        
        return {
            "tx_hash": result.tx_hash,
            "risk_level": result.risk_level.value,
            "risk_score": result.risk_score,
            "alerts": result.alerts,
            "from_labels": result.from_labels,
            "to_labels": result.to_labels,
            "from_risk": result.from_risk,
            "to_risk": result.to_risk,
            "sanctions_hit": result.sanctions_hit,
            "high_risk_hit": result.high_risk_hit,
            "mixer_hit": result.mixer_hit,
            "analysis_time_ms": result.analysis_time_ms
        }
    except Exception as e:
        logger.error(f"Failed to analyze transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kyt/stats")
async def kyt_stats(current_user: dict = Depends(require_plan("business"))):
    """Get KYT engine statistics."""
    return {
        "active_subscribers": sum(len(queues) for queues in kyt_engine.subscribers.values()),
        "total_users": len(kyt_engine.subscribers),
        "status": "running" if kyt_engine._running else "stopped"
    }
