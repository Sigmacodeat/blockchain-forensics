"""
WebSocket for Wallet Scanner Progress (Bulk Scans)
Real-time updates analog zu Payment WebSocket
"""

import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])

# Active connections per user
active_connections: dict[str, Set[WebSocket]] = {}


@router.websocket("/scanner/{user_id}")
async def scanner_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint für Scanner-Progress-Updates.
    
    Client sendet: { "action": "subscribe", "scan_id": "..." }
    Server sendet: { "type": "scan.progress", "scan_id": "...", "progress": 0.5, "current": 5, "total": 10, "message": "..." }
    """
    await websocket.accept()
    logger.info(f"Scanner WebSocket connected: user={user_id}")
    
    if user_id not in active_connections:
        active_connections[user_id] = set()
    active_connections[user_id].add(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "subscribe":
                scan_id = data.get("scan_id")
                logger.info(f"User {user_id} subscribed to scan {scan_id}")
                # Bestätigung
                await websocket.send_json({
                    "type": "scan.subscribed",
                    "scan_id": scan_id,
                    "timestamp": asyncio.get_event_loop().time()
                })
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        logger.info(f"Scanner WebSocket disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"Scanner WebSocket error: {e}")
    finally:
        if user_id in active_connections:
            active_connections[user_id].discard(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]


async def broadcast_scan_progress(user_id: str, scan_id: str, progress: float, current: int, total: int, message: str = ""):
    """Broadcast progress update to all connected clients for a user."""
    if user_id not in active_connections:
        return
    
    msg = {
        "type": "scan.progress",
        "scan_id": scan_id,
        "progress": progress,
        "current": current,
        "total": total,
        "message": message,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    for ws in list(active_connections[user_id]):
        try:
            await ws.send_json(msg)
        except Exception as e:
            logger.warning(f"Failed to send to {user_id}: {e}")


async def broadcast_scan_complete(user_id: str, scan_id: str, result: dict):
    """Broadcast completion with result."""
    if user_id not in active_connections:
        return
    
    msg = {
        "type": "scan.complete",
        "scan_id": scan_id,
        "result": result,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    for ws in list(active_connections[user_id]):
        try:
            await ws.send_json(msg)
        except Exception as e:
            logger.warning(f"Failed to send to {user_id}: {e}")
