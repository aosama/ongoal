"""
OnGoal Backend - FastAPI server with WebSocket support for goal tracking
"""
import logging
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

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Initialize FastAPI app
app = FastAPI(title="OnGoal Backend", version="1.0.0")

# CORS middleware for Vue.js frontend
# Include both localhost and 127.0.0.1 variants so browser tests that navigate
# to http://127.0.0.1:8080 (the loopback IP form) are not blocked by preflight.
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8080,http://localhost:3000,http://127.0.0.1:8080,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
    logger.info("Starting OnGoal Backend Server on http://localhost:8000")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
