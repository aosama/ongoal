"""
OnGoal Connection Manager - WebSocket connection management
"""
import json
from typing import List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def send_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            # Handle WebSocket connection errors gracefully
            # Remove disconnected websocket from active connections
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    def get_connections(self) -> List[WebSocket]:
        """Return a copy of active connections for inspection."""
        return self.active_connections.copy()

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))
