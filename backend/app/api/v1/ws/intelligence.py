"""
WebSocket endpoint for Intelligence Network live updates.
Broadcasts events: flag.created, flag.confirmed, check.performed, member.joined
"""

import logging
import json
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime


logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Intelligence WS connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Intelligence WS disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: dict):
        """Broadcast event to all connected clients"""
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {e}")
                disconnected.add(connection)
        
        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/intelligence")
async def intelligence_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for Intelligence Network live updates.
    
    Events:
    - flag.created: New flag submitted
    - flag.confirmed: Flag confirmed by investigator
    - check.performed: Address checked against network
    - member.joined: New member/investigator joined
    - stats.updated: Network statistics updated
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive, client sends ping
            data = await websocket.receive_text()
            
            # Echo ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_flag_created(flag: dict):
    """Broadcast when new flag is created"""
    await manager.broadcast("flag.created", {
        "flag_id": flag.get("flag_id"),
        "address": flag.get("address"),
        "chain": flag.get("chain"),
        "reason": flag.get("reason"),
        "amount_usd": flag.get("amount_usd"),
        "investigator_id": flag.get("investigator_id"),
    })


async def broadcast_flag_confirmed(flag: dict):
    """Broadcast when flag is confirmed"""
    await manager.broadcast("flag.confirmed", {
        "flag_id": flag.get("flag_id"),
        "address": flag.get("address"),
        "confirmations": flag.get("confirmations"),
        "status": flag.get("status"),
    })


async def broadcast_check_performed(address: str, chain: str, risk_score: float):
    """Broadcast when address check is performed"""
    await manager.broadcast("check.performed", {
        "address": address,
        "chain": chain,
        "risk_score": risk_score,
    })


async def broadcast_member_joined(member_type: str, org_name: str):
    """Broadcast when new member joins network"""
    await manager.broadcast("member.joined", {
        "member_type": member_type,
        "org_name": org_name,
    })


async def broadcast_stats_updated(stats: dict):
    """Broadcast when network stats are updated"""
    await manager.broadcast("stats.updated", stats)
