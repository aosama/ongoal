"""
OnGoal WebSocket Handlers - Real-time communication with frontend
"""
import json
import logging
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from backend.models import Message
from backend.pipelines import compute_goal_progress
from backend.pipeline_orchestrator import run_goal_pipeline
from backend.api_endpoints import conversation_repository

logger = logging.getLogger(__name__)


async def handle_websocket_connection(websocket: WebSocket, manager, conversation_id: str = "default"):
    """Handle WebSocket connection and message processing"""
    await manager.connect(websocket)

    conversation_repository.get_or_create(conversation_id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data["type"] == "user_message":
                await handle_user_message(message_data, conversation_id, websocket, manager)

            elif message_data["type"] == "toggle_pipeline":
                await handle_pipeline_toggle(message_data, conversation_id, websocket, manager)

            elif message_data["type"] == "get_conversation":
                await handle_get_conversation(conversation_id, websocket, manager)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def handle_user_message(message_data, conversation_id, websocket, manager):
    """Handle user message and run goal pipeline with async locking"""
    async with conversation_repository.with_lock(conversation_id):
        conversation = conversation_repository.get_or_create(conversation_id)

        user_message = message_data["message"]
        message_id = f"msg_{len(conversation.messages)}"

        user_msg = Message(
            id=message_id,
            content=user_message,
            role="user",
            timestamp=datetime.now().isoformat()
        )
        conversation.messages.append(user_msg)

        await run_goal_pipeline(conversation, user_message, message_id, websocket, manager)


async def handle_pipeline_toggle(message_data, conversation_id, websocket, manager):
    """Handle pipeline stage toggle"""
    conversation = conversation_repository.get_or_create(conversation_id)
    stage = message_data["stage"]
    enabled = message_data["enabled"]
    setattr(conversation.pipeline_settings, stage, enabled)

    await manager.send_message({
        "type": "pipeline_toggled",
        "stage": stage,
        "enabled": enabled
    }, websocket)


async def handle_get_conversation(conversation_id, websocket, manager):
    """Handle get conversation request"""
    conversation = conversation_repository.get_or_create(conversation_id)
    await manager.send_message({
        "type": "conversation_state",
        "conversation": {
            "id": conversation.id,
            "messages": [msg.model_dump() for msg in conversation.messages],
            "goals": [goal.model_dump() for goal in conversation.goals],
            "alerts": [alert.model_dump() for alert in conversation.alerts],
            "pipeline_settings": conversation.pipeline_settings.model_dump(),
            "goal_history": [entry.model_dump() for entry in conversation.goal_history],
            "goal_progress": compute_goal_progress(conversation),
        }
    }, websocket)