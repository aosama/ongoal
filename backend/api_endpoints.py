"""
OnGoal REST API Endpoints - HTTP endpoints for conversation management
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models import Conversation, Goal, Message, GoalAlert

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


@router.get("/api/llm-status")
async def llm_status():
    """Get detailed LLM provider status"""
    from backend.llm_service import LLMService

    return {
        "timestamp": datetime.now().isoformat(),
        **LLMService.get_service_status()
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
            "alerts": [alert.model_dump() for alert in conversation.alerts],
            "pipeline_settings": conversation.pipeline_settings.model_dump()
        }

    raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/api/conversations/{conversation_id}/alerts")
async def get_alerts(conversation_id: str):
    """Get all alerts for a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    return {
        "alerts": [alert.model_dump() for alert in conversation.alerts],
        "count": len(conversation.alerts)
    }


@router.delete("/api/conversations/{conversation_id}/alerts")
async def clear_alerts(conversation_id: str):
    """Clear all alerts for a conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    cleared_count = len(conversation.alerts)
    conversation.alerts = []

    return {
        "status": "success",
        "message": f"Cleared {cleared_count} alert(s)",
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/api/conversations/{conversation_id}/alerts/{alert_index}")
async def dismiss_alert(conversation_id: str, alert_index: int):
    """Dismiss a single alert by index"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    if alert_index < 0 or alert_index >= len(conversation.alerts):
        raise HTTPException(status_code=404, detail="Alert not found")

    conversation.alerts.pop(alert_index)

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat()
    }


class AlertInjectRequest(BaseModel):
    alert_type: str
    severity: str = "warning"
    goal_ids: List[str] = []
    message: str = ""
    suggestion: str = ""


@router.post("/api/conversations/{conversation_id}/alerts/_inject")
async def inject_alert(conversation_id: str, req: AlertInjectRequest):
    """Inject an alert for testing purposes"""
    if conversation_id not in conversations:
        conversations[conversation_id] = Conversation(id=conversation_id)

    conversation = conversations[conversation_id]
    alert = GoalAlert(
        alert_type=req.alert_type,
        severity=req.severity,
        goal_ids=req.goal_ids,
        message=req.message,
        suggestion=req.suggestion,
    )
    conversation.alerts.append(alert)

    return {
        "status": "success",
        "alert": alert.model_dump(),
        "timestamp": datetime.now().isoformat()
    }


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


@router.post("/api/conversations/{conversation_id}/keyphrases")
async def extract_keyphrases(conversation_id: str):
    """Extract keyphrases from the last assistant response (REQ-09-04)"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]

    # Find the last assistant message
    assistant_messages = [m for m in conversation.messages if m.role == "assistant"]
    if not assistant_messages:
        return {"keyphrases": [], "message_id": None}

    last_assistant = assistant_messages[-1]

    from backend.pipelines import extract_keyphrases as _extract_keyphrases
    keyphrases = await _extract_keyphrases(last_assistant.content)

    return {
        "keyphrases": keyphrases,
        "message_id": last_assistant.id,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/conversations/{conversation_id}/sentence-similarity")
async def get_sentence_similarity(conversation_id: str):
    """Get similar and unique sentences across assistant responses (REQ-04-03-006/007)"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    assistant_messages = [m for m in conversation.messages if m.role == "assistant"]

    if len(assistant_messages) < 2:
        return {"similar_sentences": [], "unique_sentences": [], "message_count": len(assistant_messages)}

    import re as _re
    sentence_map = []
    for msg in assistant_messages:
        sentences = [s.strip() for s in _re.split(r'(?<=[.!?])\s+', msg.content) if len(s.strip()) > 20]
        for s in sentences:
            sentence_map.append({"text": s, "message_id": msg.id})

    if len(sentence_map) < 2:
        return {"similar_sentences": [], "unique_sentences": sentence_map, "message_count": len(assistant_messages)}

    sentences_text = "\n".join(f"{i+1}. {s['text']}" for i, s in enumerate(sentence_map))

    from backend.llm_service import LLMService
    prompt = f"""You are comparing sentences from multiple assistant responses. Group sentences that express substantially the same idea into "similar" groups. Sentences that are unique (no matching sentence in other responses) should be listed as "unique".

Sentences:
{sentences_text}

Respond ONLY with valid JSON:

{{
  "similar_groups": [
    {{"sentence_indices": [1, 3], "theme": "<shared_theme>"}}
  ],
  "unique_indices": [2, 5]
}}"""

    try:
        response_text = await LLMService.generate_response(prompt, max_tokens=1000)
        import json as _json
        from backend.json_parser import extract_json_object
        data = extract_json_object(response_text)
        if data:
            similar = []
            for group in data.get("similar_groups", []):
                indices = group.get("sentence_indices", [])
                sentences = [sentence_map[i-1] for i in indices if 0 < i <= len(sentence_map)]
                similar.append({
                    "theme": group.get("theme", ""),
                    "sentences": sentences,
                })
            unique = [sentence_map[i-1] for i in data.get("unique_indices", []) if 0 < i <= len(sentence_map)]
            return {
                "similar_sentences": similar,
                "unique_sentences": unique,
                "message_count": len(assistant_messages),
            }
    except Exception:
        pass

    return {"similar_sentences": [], "unique_sentences": [], "message_count": len(assistant_messages)}


@router.get("/api/conversations/{conversation_id}/goal-progress")
async def get_goal_progress(conversation_id: str):
    """Get goal progress tracking across messages (REQ-03-02-001, REQ-03-02-004)"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    from backend.pipelines import compute_goal_progress
    progress = compute_goal_progress(conversation)

    return {
        "progress": progress,
        "goal_count": len(progress),
    }


def get_conversations_store():
    """Get reference to conversations storage for websocket handler"""
    return conversations


@router.get("/api/conversations/{conversation_id}/goal-history")
async def get_goal_history(conversation_id: str):
    """Get goal mutation history for restore functionality (REQ-04-02-205)"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    return {
        "goal_history": [entry.model_dump() for entry in conversation.goal_history],
        "turn_count": len([m for m in conversation.messages if m.role == "user"])
    }


@router.post("/api/conversations/{conversation_id}/goal-history/{entry_index}/restore")
async def restore_goal_from_history(conversation_id: str, entry_index: int):
    """Restore a previous goal version from history (REQ-04-02-205)"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    if entry_index < 0 or entry_index >= len(conversation.goal_history):
        raise HTTPException(status_code=400, detail="Invalid history entry index")

    entry = conversation.goal_history[entry_index]
    restored_goal = Goal(
        id=entry.goal_id,
        text=entry.goal_text,
        type=entry.goal_type,
        source_message_id="restored",
        created_at=entry.timestamp,
        locked=False,
    )

    existing = conversation.get_goal_by_id(entry.goal_id)
    if existing:
        existing.text = entry.goal_text
        existing.type = entry.goal_type
        existing.created_at = entry.timestamp
    else:
        conversation.goals.append(restored_goal)

    return {
        "goal": restored_goal.model_dump(),
        "message": f"Restored goal {entry.goal_id} from turn {entry.turn}"
    }


# Request/Response models for manual goal replacement
class GoalReplaceRequest(BaseModel):
    new_text: str
    new_type: str = "request"


class GoalReplaceResponse(BaseModel):
    status: str
    old_goal: dict
    new_goal: dict
    message: str
    timestamp: str


@router.post("/api/conversations/{conversation_id}/goals/{goal_id}/replace")
async def replace_goal(conversation_id: str, goal_id: str, req: GoalReplaceRequest):
    """Manually replace an existing goal with a new version.

    Marks the old goal as replaced, creates a new goal, and records
    the operation in goal_history.
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]
    goal = next((g for g in conversation.goals if g.id == goal_id), None)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Mark oldgoal as replaced (in-place so other refs see the update)
    goal.status = "replaced"

    # Create replacement goal
    new_goal_id = f"{goal_id}R{len(conversation.goals)}"
    new_goal = Goal(
        id=new_goal_id,
        text=req.new_text,
        type=req.new_type,
        source_message_id="manual_replace",
        created_at=datetime.now().isoformat(),
    )
    conversation.goals.append(new_goal)

    # History tracking
    from backend.models import GoalHistoryEntry
    turn = len([m for m in conversation.messages if m.role == "user"])
    conversation.goal_history.append(GoalHistoryEntry(
        turn=turn,
        operation="replace",
        goal_id=goal.id,
        goal_text=goal.text,
        goal_type=goal.type,
        previous_goal_ids=[new_goal.id],
        previous_goal_texts=[new_goal.text],
    ))

    return {
        "status": "success",
        "old_goal": goal.model_dump(),
        "new_goal": new_goal.model_dump(),
        "message": f"Replaced goal {goal_id} with {new_goal_id}",
        "timestamp": datetime.now().isoformat()
    }
