"""
WebSocket endpoint for real-time payment updates
Provides instant notifications when payment status changes
"""
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
from datetime import datetime

from app.db.postgres_client import postgres_client
from app.auth.middleware import get_current_user_ws

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])

# Active WebSocket connections
active_connections: Dict[int, list[WebSocket]] = {}


@router.websocket("/payment/{payment_id}")
async def payment_websocket(websocket: WebSocket, payment_id: int):
    """
    WebSocket endpoint for real-time payment status updates
    
    Sends updates every 5 seconds until payment is finished/failed
    
    Message format:
    {
        "type": "status_update",
        "payment_id": 12345,
        "payment_status": "confirming",
        "pay_in_hash": "0x123...",
        "updated_at": "2025-10-18T20:00:00Z"
    }
    """
    await websocket.accept()
    
    # Add connection to active connections
    if payment_id not in active_connections:
        active_connections[payment_id] = []
    active_connections[payment_id].append(websocket)
    
    try:
        # Send initial status
        payment = await postgres_client.fetchrow(
            "SELECT * FROM crypto_payments WHERE payment_id = $1",
            payment_id
        )
        
        if not payment:
            await websocket.send_json({
                "type": "error",
                "message": "Payment not found"
            })
            await websocket.close()
            return
        
        await websocket.send_json({
            "type": "connected",
            "payment_id": payment_id,
            "message": "WebSocket connected successfully"
        })
        
        last_status = None
        
        # Poll for updates
        while True:
            payment = await postgres_client.fetchrow(
                "SELECT payment_id, payment_status, pay_in_hash, updated_at, order_id "
                "FROM crypto_payments WHERE payment_id = $1",
                payment_id
            )
            
            if not payment:
                break
            
            current_status = payment["payment_status"]
            
            # Send update if status changed
            if current_status != last_status:
                await websocket.send_json({
                    "type": "status_update",
                    "payment_id": payment_id,
                    "payment_status": current_status,
                    "pay_in_hash": payment.get("pay_in_hash"),
                    "order_id": payment["order_id"],
                    "updated_at": payment["updated_at"].isoformat() if payment.get("updated_at") else None,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                last_status = current_status
                
                # Close connection if payment is finished/failed
                if current_status in ["finished", "failed", "expired"]:
                    await websocket.send_json({
                        "type": "final_status",
                        "payment_id": payment_id,
                        "payment_status": current_status,
                        "message": "Payment completed"
                    })
                    break
            
            # Wait 5 seconds before next check
            await asyncio.sleep(5)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for payment {payment_id}")
    except Exception as e:
        logger.error(f"WebSocket error for payment {payment_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        # Remove connection
        if payment_id in active_connections:
            if websocket in active_connections[payment_id]:
                active_connections[payment_id].remove(websocket)
            if not active_connections[payment_id]:
                del active_connections[payment_id]
        
        try:
            await websocket.close()
        except:
            pass


async def broadcast_payment_update(payment_id: int, status: str, tx_hash: str = None):
    """
    Broadcast payment update to all connected clients
    Called from webhook handler when payment status changes
    
    Args:
        payment_id: Payment ID
        status: New payment status
        tx_hash: Transaction hash (optional)
    """
    if payment_id not in active_connections:
        return
    
    message = {
        "type": "status_update",
        "payment_id": payment_id,
        "payment_status": status,
        "pay_in_hash": tx_hash,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Send to all connected clients
    disconnected = []
    for ws in active_connections[payment_id]:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    
    # Clean up disconnected clients
    for ws in disconnected:
        active_connections[payment_id].remove(ws)
    
    if not active_connections[payment_id]:
        del active_connections[payment_id]
