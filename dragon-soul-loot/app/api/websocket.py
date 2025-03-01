from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Any
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active connections
        self.active_connections: List[WebSocket] = []
        # Last broadcast messages (for new connections)
        self.last_messages: Dict[str, Any] = {
            "raid_status": None,
            "loot_assignment": None,
            "priorities": None
        }
    
    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send last messages to new connection
        for msg_type, msg in self.last_messages.items():
            if msg:
                await websocket.send_json({
                    "type": msg_type,
                    "data": msg,
                    "timestamp": datetime.now().isoformat()
                })
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message_type: str, data: Any):
        """Broadcast a message to all connected clients"""
        # Store as last message of this type
        self.last_messages[message_type] = data
        
        # Prepare the message
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Mark for removal
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_personal_message(self, message: Any, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)

# Create a connection manager instance
manager = ConnectionManager()

async def handle_websocket(websocket: WebSocket):
    """Handle WebSocket connections and messages"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "data": {
                "status": "connected",
                "message": "Connected to Dragon Soul Loot Manager WebSocket"
            },
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Listen for messages from the client
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            
            # Parse the message
            try:
                message = json.loads(data)
                
                # Handle client messages (if needed)
                # Currently we just echo back client messages
                await manager.send_personal_message({
                    "type": "echo",
                    "data": message,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
            except json.JSONDecodeError:
                # Invalid JSON
                await manager.send_personal_message({
                    "type": "error",
                    "data": {
                        "message": "Invalid JSON message"
                    },
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        # Client disconnected
        manager.disconnect(websocket)
    except Exception as e:
        # Other errors
        manager.disconnect(websocket)
        print(f"WebSocket error: {str(e)}")

# Functions to broadcast updates from API routes

async def broadcast_raid_status(raid_status: Dict[str, Any]):
    """Broadcast raid status updates"""
    await manager.broadcast("raid_status", raid_status)

async def broadcast_loot_assignment(loot_assignment: Dict[str, Any]):
    """Broadcast loot assignment updates"""
    await manager.broadcast("loot_assignment", loot_assignment)

async def broadcast_priorities(priorities: List[Dict[str, Any]]):
    """Broadcast loot priority updates"""
    await manager.broadcast("priorities", priorities) 