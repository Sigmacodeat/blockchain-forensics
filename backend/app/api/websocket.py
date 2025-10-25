"""
WebSocket Endpoints für Real-Time Updates
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from datetime import datetime

logger = logging.getLogger(__name__)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        # Active connections per client
        self.active_connections: Set[WebSocket] = set()
        
        # Trace-specific subscriptions: trace_id -> set of websockets
        self.trace_subscriptions: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        
        # Remove from all trace subscriptions
        for trace_id, subscribers in list(self.trace_subscriptions.items()):
            subscribers.discard(websocket)
            if not subscribers:
                del self.trace_subscriptions[trace_id]
                
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    def subscribe_to_trace(self, trace_id: str, websocket: WebSocket):
        """Subscribe a websocket to trace updates"""
        if trace_id not in self.trace_subscriptions:
            self.trace_subscriptions[trace_id] = set()
        self.trace_subscriptions[trace_id].add(websocket)
        logger.debug(f"Subscribed to trace {trace_id}")
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific websocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
                disconnected.add(connection)
                
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
            
    async def broadcast_to_trace(self, trace_id: str, message: dict):
        """Send message to all subscribers of a specific trace"""
        subscribers = self.trace_subscriptions.get(trace_id, set())
        disconnected = set()
        
        for websocket in subscribers:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to trace subscriber: {e}")
                disconnected.add(websocket)
                
        # Clean up
        for ws in disconnected:
            self.disconnect(ws)


# Global instance
manager = ConnectionManager()

# Router
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time updates.
    
    Clients can subscribe to events by sending:
    {
        "action": "subscribe",
        "event_type": "trace.progress|trace.completed|alert.created",
        "trace_id": "optional-trace-id"
    }
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "subscribe":
                    trace_id = message.get("trace_id")
                    if trace_id:
                        manager.subscribe_to_trace(trace_id, websocket)
                        await manager.send_personal_message({
                            "type": "subscription.confirmed",
                            "trace_id": trace_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)
                        
                elif action == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """
    Minimal Chat WebSocket endpoint (stub).
    Receives user messages and returns a simple streaming-style response.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # basic protocol: raw text as user message
            # send typing indicator
            await websocket.send_json({
                "type": "chat.typing",
                "timestamp": datetime.utcnow().isoformat()
            })
            await asyncio.sleep(0.2)
            await websocket.send_json({
                "type": "chat.answer",
                "data": {
                    "reply": "Danke für deine Nachricht – Streaming Chat wird bald mit RAG & Tools erweitert.",
                },
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Chat client disconnected")

@router.websocket("/ws/trace/{trace_id}")
async def trace_websocket(websocket: WebSocket, trace_id: str):
    """
    Trace-specific WebSocket endpoint.
    Auto-subscribes to updates for the given trace_id.
    """
    await manager.connect(websocket)
    manager.subscribe_to_trace(trace_id, websocket)
    
    # Send confirmation
    await manager.send_personal_message({
        "type": "trace.subscribed",
        "trace_id": trace_id,
        "timestamp": datetime.utcnow().isoformat()
    }, websocket)
    
    try:
        # Keep connection alive and listen for pings
        while True:
            data = await websocket.receive_text()
            
            # Simple ping-pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client disconnected from trace {trace_id}")


# Helper functions for broadcasting events (to be called from other modules)

async def broadcast_trace_progress(
    trace_id: str,
    status: str,
    progress_percentage: float,
    nodes_discovered: int,
    edges_discovered: int,
    current_hop: int,
    message: Optional[str] = None
):
    """Broadcast trace progress update"""
    await manager.broadcast_to_trace(trace_id, {
        "type": "trace.progress",
        "data": {
            "trace_id": trace_id,
            "status": status,
            "progress_percentage": progress_percentage,
            "nodes_discovered": nodes_discovered,
            "edges_discovered": edges_discovered,
            "current_hop": current_hop,
            "message": message
        },
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_trace_completed(trace_id: str, result: dict):
    """Broadcast trace completion"""
    await manager.broadcast_to_trace(trace_id, {
        "type": "trace.completed",
        "data": {
            "trace_id": trace_id,
            **result
        },
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_alert(alert_data: dict):
    """Broadcast new alert to all clients"""
    await manager.broadcast({
        "type": "alert.created",
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_enrichment_completed(address: str, labels: list, risk_score: float):
    """Broadcast enrichment completion"""
    await manager.broadcast({
        "type": "enrichment.completed",
        "data": {
            "address": address,
            "labels": labels,
            "risk_score": risk_score
        },
        "timestamp": datetime.utcnow().isoformat()
    })
