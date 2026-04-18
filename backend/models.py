"""
OnGoal Data Models - Pydantic models for goal tracking system

Based on requirements from docs/requirements/tdd-requirements/04-ongoal-system.md
and prompt templates in 09-llm-prompts.md.
"""

from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class GoalEvaluation(BaseModel):
    """Evaluation of how an assistant response addresses a goal (REQ-04-01-301–305)"""

    goal_id: str
    category: str  # confirm, contradict, ignore
    explanation: str = ""
    examples: List[str] = []
    confidence: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    def is_confirmed(self) -> bool:
        return self.category == "confirm"

    def is_contradicted(self) -> bool:
        return self.category == "contradict"

    def is_ignored(self) -> bool:
        return self.category == "ignore"


class GoalAlert(BaseModel):
    """A detection alert for goal anomalies (REQ-03-01/02)"""

    alert_type: str  # forgetting, contradiction, derailment, repetition, breakdown
    severity: str = "warning"  # info, warning, critical
    goal_ids: List[str] = []
    message: str = ""
    suggestion: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Goal(BaseModel):
    """A conversational goal extracted from user dialogue (REQ-04-01-101–305)"""

    id: str
    text: str
    type: str  # question, request, offer, suggestion
    summary: str = ""  # One-sentence summary of how to address this goal (REQ-09-01-003)
    status: Optional[str] = None  # confirmed, contradicted, ignored
    locked: bool = False
    completed: bool = False
    source_message_id: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    evaluation: Optional[GoalEvaluation] = None


class Message(BaseModel):
    """A single message in the conversation"""

    id: str
    content: str
    role: str  # user, assistant
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    goals: List[Goal] = []


class PipelineSettings(BaseModel):
    """Toggle settings for the goal pipeline stages"""

    infer: bool = True
    merge: bool = True
    evaluate: bool = True


class GoalHistoryEntry(BaseModel):
    """A record of a goal mutation for history/restore (REQ-04-02-205)"""

    turn: int
    operation: str  # keep, combine, replace, infer
    goal_id: str
    goal_text: str
    goal_type: str
    previous_goal_ids: List[str] = []
    previous_goal_texts: List[str] = []
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Conversation(BaseModel):
    """A conversation with tracked goals"""

    id: str
    messages: List[Message] = []
    goals: List[Goal] = []
    alerts: List[GoalAlert] = []
    pipeline_settings: PipelineSettings = Field(default_factory=PipelineSettings)
    goal_history: List[GoalHistoryEntry] = []

    def get_goal_by_id(self, goal_id: str) -> Optional[Goal]:
        """Find a goal by its ID"""
        for goal in self.goals:
            if goal.id == goal_id:
                return goal
        return None
