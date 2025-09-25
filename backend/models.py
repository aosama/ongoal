"""
OnGoal Data Models - Pydantic models for goal tracking system
"""
from typing import List, Dict, Optional
from pydantic import BaseModel


class Goal(BaseModel):
    id: str
    text: str
    type: str  # question, request, offer, suggestion
    status: Optional[str] = None  # confirmed, contradicted, ignored
    locked: bool = False
    completed: bool = False
    source_message_id: str
    created_at: str


class Message(BaseModel):
    id: str
    content: str
    role: str  # user, assistant
    timestamp: str
    goals: List[Goal] = []


class Conversation(BaseModel):
    id: str
    messages: List[Message] = []
    goals: List[Goal] = []
    pipeline_settings: Dict[str, bool] = {
        "infer": True,
        "merge": True, 
        "evaluate": True
    }
