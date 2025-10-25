"""
WebSocket for Real-Time Mempool Events
- Broadcasts pending tx insights (chain, tx_hash, from, to, value, heuristics)
- Pattern mirrors existing scanner/payment WS structure
"""
import logging
import asyncio
from typing import Set, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])  # will be mounted under /api/v1

# Active connections (all users get broadcast; no auth state in WS for now)
_active_mempool_conns: Set[WebSocket] = set()


@router.websocket("/mempool")
async def mempool_websocket(websocket: WebSocket):
    """
    WebSocket endpoint für Mempool-Updates.

    Client kann optional folgende Nachrichten senden:
      - { "action": "ping" } -> { "type": "pong" }
      - { "action": "subscribe", chains?: ["ethereum", "tron", ...] }

    Server sendet Broadcast-Nachrichten:
      - { "type": "mempool.tx", "chain": "ethereum", "tx_hash": "0x..", "from": "0x..", "to": "0x..", "value": 0.1, "heuristics": {...}, "timestamp": <float> }
      - { "type": "mempool.alert", "rule": "sanctions_evasion", "severity": "high", "tx": { ... }, "timestamp": <float> }
    """
    await websocket.accept()
    logger.info("Mempool WebSocket connected")
    _active_mempool_conns.add(websocket)
    try:
        while True:
            # Optional client messages
            try:
                data = await websocket.receive_json()
            except Exception:
                # No message, allow heartbeat by yielding control
                await asyncio.sleep(0)
                continue
            action = (data or {}).get("action")
            if action == "ping":
                await websocket.send_json({"type": "pong"})
            elif action == "subscribe":
                # Best-effort: store requested chains in connection state (not persisted)
                # For simplicity, we don't filter server-side yet.
                await websocket.send_json({
                    "type": "mempool.subscribed",
                    "chains": (data.get("chains") or []),
                    "timestamp": asyncio.get_event_loop().time(),
                })
    except WebSocketDisconnect:
        logger.info("Mempool WebSocket disconnected")
    except Exception as e:
        logger.error(f"Mempool WebSocket error: {e}")
    finally:
        _active_mempool_conns.discard(websocket)


async def broadcast_mempool_tx(event: Dict):
    """Broadcast a mempool transaction event to all connected clients."""
    if not _active_mempool_conns:
        return
    msg = {
        "type": "mempool.tx",
        **event,
        "timestamp": asyncio.get_event_loop().time(),
    }
    for ws in list(_active_mempool_conns):
        try:
            await ws.send_json(msg)
        except Exception as e:
            logger.warning(f"Failed to send mempool event: {e}")


async def broadcast_mempool_alert(alert: Dict):
    """Broadcast a mempool alert (e.g., heuristic/typology match)."""
    if not _active_mempool_conns:
        return
    msg = {
        "type": "mempool.alert",
        **alert,
        "timestamp": asyncio.get_event_loop().time(),
    }
    for ws in list(_active_mempool_conns):
        try:
            await ws.send_json(msg)
        except Exception as e:
            logger.warning(f"Failed to send mempool alert: {e}")
