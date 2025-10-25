"""
WebSocket Connection Manager
Real-Time Trace Updates
"""

import logging
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    
    **Features:**
    - Trace progress updates
    - Real-time alerts
    - System notifications
    - Room-based subscriptions
    - Multi-room support per client
    """
    
    def __init__(self):
        # Active connections by trace_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # All connections
        self.all_connections: Set[WebSocket] = set()
        # Room subscriptions (room_name -> set of WebSockets)
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Client metadata (WebSocket -> metadata dict)
        self.client_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, trace_id: Optional[str] = None):
        """
        Accept new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            trace_id: Optional trace ID to subscribe to
        """
        await websocket.accept()
        self.all_connections.add(websocket)
        
        if trace_id:
            if trace_id not in self.active_connections:
                self.active_connections[trace_id] = set()
            self.active_connections[trace_id].add(websocket)

            logger.info(f"WebSocket connected for trace {trace_id}")
        else:
            logger.info("WebSocket connected (global)")
    
    def disconnect(self, websocket: WebSocket, trace_id: Optional[str] = None):
        """
        Remove WebSocket connection
        
        Args:
            websocket: WebSocket connection
            trace_id: Optional trace ID
        """
        self.all_connections.discard(websocket)
        
        if trace_id and trace_id in self.active_connections:
            self.active_connections[trace_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[trace_id]:
                del self.active_connections[trace_id]

        # Remove metadata and from rooms
        self.client_metadata.pop(websocket, None)
        for room, clients in list(self.rooms.items()):
            if websocket in clients:
                clients.discard(websocket)
                if not clients:
                    self.rooms.pop(room, None)
        
        logger.info("WebSocket disconnected")
    
    async def send_trace_update(self, trace_id: str, data: Dict):
        """
        Send update to all connections subscribed to a trace
        
        Args:
            trace_id: Trace ID
            data: Update data
        """
        if trace_id not in self.active_connections:
            return
        
        message = {
            "type": "trace_update",
            "trace_id": trace_id,
            "data": data
        }
        
        # Send to all subscribed connections
        disconnected = set()
        for connection in self.active_connections[trace_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn, trace_id)
    
    async def send_alert(self, data: Dict):
        """
        Send alert to all connected clients
        
        Args:
            data: Alert data
        """
        message = {
            "type": "alert",
            "data": data
        }
        
        disconnected = set()
        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending alert: {e}")
                disconnected.add(connection)
        
        # Clean up
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast(self, message: Dict):
        """
        Broadcast message to all connections
        
        Args:
            message: Message to broadcast
        """
        disconnected = set()
        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.add(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def join_room(self, websocket: WebSocket, room_name: str):
        """
        Subscribe client to a room
        
        Args:
            websocket: WebSocket connection
            room_name: Room identifier (e.g., "alerts", "high_risk", "bridge_events")
        """
        if room_name not in self.rooms:
            self.rooms[room_name] = set()
        
        self.rooms[room_name].add(websocket)
        logger.info(f"Client joined room: {room_name}")

    async def leave_room(self, websocket: WebSocket, room_name: str):
        """
        Unsubscribe client from a room
        
        Args:
            websocket: WebSocket connection
            room_name: Room identifier
        """
        if room_name in self.rooms:
            self.rooms[room_name].discard(websocket)
            
            # Clean up empty rooms
            if not self.rooms[room_name]:
                del self.rooms[room_name]
            
            logger.info(f"Client left room: {room_name}")

    def set_client_metadata(self, websocket: WebSocket, metadata: Dict[str, Any]) -> None:
        """Attach metadata (e.g., user_id, user_name) to a WebSocket client."""
        self.client_metadata[websocket] = metadata

    def get_client_metadata(self, websocket: WebSocket) -> Dict[str, Any]:
        return self.client_metadata.get(websocket, {})

    
    async def send_to_room(self, room_name: str, message: Dict):
        """
        Send message to all clients in a room
        
        Args:
            room_name: Room identifier
            message: Message to send
        """
        if room_name not in self.rooms:
            return
        
        disconnected = set()
        for connection in self.rooms[room_name]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to room {room_name}: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.leave_room(conn, room_name)

    async def send_collaboration_event(self, case_id: str, message: Dict[str, Any]):
        """Broadcast collaboration event to all participants of a case."""
        room_name = self.collab_room(case_id)
        await self.send_to_room(room_name, message)

    def collab_room(self, case_id: str) -> str:
        return f"collab:{case_id}"
    
    def get_stats(self) -> Dict:
        """
        Get connection statistics
        
        Returns:
            Statistics dict
        """
        return {
            "total_connections": len(self.all_connections),
            "trace_subscriptions": len(self.active_connections),
            "rooms": {
                room: len(clients) 
                for room, clients in self.rooms.items()
            }
        }


# Singleton instance
manager = ConnectionManager()
# Backward-compatible alias expected by workers and tests
connection_manager = manager
