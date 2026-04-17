"""
WebSocket manager for real-time OTA progress updates.
"""
import json
from typing import Set, Optional
from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections and broadcasts messages to clients."""
    
    def __init__(self):
        # Set of connected WebSocket clients
        self.active_connections: Set[WebSocket] = set()
        # Mapping of device_id to WebSocket (for targeted messages)
        self.device_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, device_id: Optional[str] = None):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if device_id:
            self.device_connections[device_id] = websocket
        
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from device connections if present
        device_id = None
        for did, ws in list(self.device_connections.items()):
            if ws == websocket:
                del self.device_connections[did]
                device_id = did
                break
        
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict) -> None:
        """Send a message to all connected WebSocket clients."""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                print(f"WebSocket send error: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(ws)
    
    async def send_to_device(self, device_id: str, message: dict) -> bool:
        """Send a message to a specific client by device_id."""
        if device_id not in self.device_connections:
            return False
        
        websocket = self.device_connections[device_id]
        try:
            await websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            print(f"WebSocket send error to {device_id}: {e}")
            await self.disconnect(websocket)
            return False
    
    def get_connection_count(self) -> int:
        """Return the number of active connections."""
        return len(self.active_connections)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()