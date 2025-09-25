"""
OnGoal Backend - FastAPI server with WebSocket support for goal tracking
"""
import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from backend.connection_manager import ConnectionManager
from backend.api_endpoints import router
from backend.websocket_handlers import handle_websocket_connection

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="OnGoal Backend", version="1.0.0")

# CORS middleware for Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Initialize connection manager
manager = ConnectionManager()


# WebSocket endpoint with conversation ID support
@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint_with_id(websocket: WebSocket, conversation_id: str = "default"):
    await handle_websocket_connection(websocket, manager, conversation_id)

# Legacy WebSocket endpoint for backward compatibility
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket_connection(websocket, manager, "default")


if __name__ == "__main__":
    print("🚀 Starting OnGoal Backend Server...")
    print("📍 Server URL: http://localhost:8000")
    print("🔗 WebSocket URL: ws://localhost:8000/ws")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
