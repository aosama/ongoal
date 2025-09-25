"""
OnGoal REST API Endpoints - HTTP endpoints for conversation management
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models import Conversation, Goal, Message

# Create router for API endpoints
router = APIRouter()

# In-memory storage only
conversations = {}


@router.get("/")
async def root():
    return {"message": "OnGoal Backend API", "version": "1.0.0"}


@router.get("/api/health")
async def health_check():
    from backend.llm_service import LLMService

    service_status = LLMService.get_service_status()

    return {
        "status": "healthy" if service_status["available"] else "degraded",
        "timestamp": datetime.now().isoformat(),
        "llm_service": service_status
    }


@router.post("/api/conversations/{conversation_id}/reset")
async def reset_conversation(conversation_id: str):
    """Reset conversation state - CRITICAL for test isolation"""
    if conversation_id in conversations:
        del conversations[conversation_id]

    # Create fresh conversation
    conversations[conversation_id] = Conversation(id=conversation_id)

    return {
        "status": "success",
        "message": f"Conversation {conversation_id} reset",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    if conversation_id in conversations:
        conversation = conversations[conversation_id]
        return {
            "id": conversation.id,
            "messages": [msg.model_dump() for msg in conversation.messages],
            "goals": [goal.model_dump() for goal in conversation.goals],
            "pipeline_settings": conversation.pipeline_settings
        }

    raise HTTPException(status_code=404, detail="Conversation not found")


# Request/Response models for goal CRUD operations
class GoalCreateRequest(BaseModel):
    text: str
    type: str  # question, request, offer, suggestion
    source_message_id: str

class GoalUpdateRequest(BaseModel):
    text: Optional[str] = None
    type: Optional[str] = None
    locked: Optional[bool] = None
    completed: Optional[bool] = None
    status: Optional[str] = None

# Goal CRUD Endpoints
@router.post("/api/conversations/{conversation_id}/goals")
async def create_goal(conversation_id: str, goal_request: GoalCreateRequest):
    """Create a new goal manually"""
    if conversation_id not in conversations:
        conversations[conversation_id] = Conversation(id=conversation_id)

    conversation = conversations[conversation_id]
    goal_id = f"G{len(conversation.goals)}_manual"

    new_goal = Goal(
        id=goal_id,
        text=goal_request.text,
        type=goal_request.type,
        source_message_id=goal_request.source_message_id,
        created_at=datetime.now().isoformat()
    )

    conversation.goals.append(new_goal)

    return {
        "status": "success",
        "goal": new_goal.model_dump(),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/api/conversations/{conversation_id}/goals")
async def get_goals(conversation_id: str):
    """Get all goals for a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    return {
        "goals": [goal.model_dump() for goal in conversation.goals],
        "count": len(conversation.goals)
    }

@router.get("/api/conversations/{conversation_id}/goals/{goal_id}")
async def get_goal(conversation_id: str, goal_id: str):
    """Get a specific goal by ID"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    goal = next((g for g in conversation.goals if g.id == goal_id), None)

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return {"goal": goal.model_dump()}

@router.put("/api/conversations/{conversation_id}/goals/{goal_id}")
async def update_goal(conversation_id: str, goal_id: str, goal_update: GoalUpdateRequest):
    """Update a specific goal"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    goal = next((g for g in conversation.goals if g.id == goal_id), None)

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Update fields if provided
    if goal_update.text is not None:
        goal.text = goal_update.text
    if goal_update.type is not None:
        goal.type = goal_update.type
    if goal_update.locked is not None:
        goal.locked = goal_update.locked
    if goal_update.completed is not None:
        goal.completed = goal_update.completed
    if goal_update.status is not None:
        goal.status = goal_update.status

    return {
        "status": "success",
        "goal": goal.model_dump(),
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/api/conversations/{conversation_id}/goals/{goal_id}")
async def delete_goal(conversation_id: str, goal_id: str):
    """Delete a specific goal"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    goal_index = next((i for i, g in enumerate(conversation.goals) if g.id == goal_id), None)

    if goal_index is None:
        raise HTTPException(status_code=404, detail="Goal not found")

    deleted_goal = conversation.goals.pop(goal_index)

    return {
        "status": "success",
        "message": f"Goal {goal_id} deleted",
        "deleted_goal": deleted_goal.model_dump(),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/api/conversations/{conversation_id}/goals/{goal_id}/lock")
async def lock_goal(conversation_id: str, goal_id: str):
    """Lock a goal to prevent automatic updates"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    goal = next((g for g in conversation.goals if g.id == goal_id), None)

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal.locked = True

    return {
        "status": "success",
        "message": f"Goal {goal_id} locked",
        "goal": goal.model_dump(),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/api/conversations/{conversation_id}/goals/{goal_id}/unlock")
async def unlock_goal(conversation_id: str, goal_id: str):
    """Unlock a goal to allow automatic updates"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    goal = next((g for g in conversation.goals if g.id == goal_id), None)

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    goal.locked = False

    return {
        "status": "success",
        "message": f"Goal {goal_id} unlocked",
        "goal": goal.model_dump(),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/api/conversations")
async def list_conversations():
    """List all conversations"""
    conversation_ids = list(conversations.keys())
    return {
        "conversations": conversation_ids,
        "count": len(conversation_ids)
    }

def get_conversations_store():
    """Get reference to conversations storage for websocket handler"""
    return conversations
