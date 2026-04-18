"""
OnGoal WebSocket Handlers - Real-time communication with frontend
"""
import json
import logging
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from backend.models import Message, Conversation, GoalAlert
from backend.goal_pipeline import (
    infer_goals, merge_goals, evaluate_goal, stream_llm_response,
    extract_keyphrases, detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, compute_goal_progress, detect_breakdown,
)
from backend.api_endpoints import get_conversations_store

logger = logging.getLogger(__name__)


async def handle_websocket_connection(websocket: WebSocket, manager, conversation_id: str = "default"):
    """Handle WebSocket connection and message processing"""
    await manager.connect(websocket)

    conversations = get_conversations_store()

    if conversation_id not in conversations:
        conversations[conversation_id] = Conversation(id=conversation_id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data["type"] == "user_message":
                await handle_user_message(message_data, conversation_id, conversations, websocket, manager)

            elif message_data["type"] == "toggle_pipeline":
                await handle_pipeline_toggle(message_data, conversation_id, conversations, websocket, manager)

            elif message_data["type"] == "get_conversation":
                await handle_get_conversation(conversation_id, conversations, websocket, manager)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def handle_user_message(message_data, conversation_id, conversations, websocket, manager):
    """Handle user message and run goal pipeline"""
    user_message = message_data["message"]
    message_id = f"msg_{len(conversations[conversation_id].messages)}"

    user_msg = Message(
        id=message_id,
        content=user_message,
        role="user",
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id].messages.append(user_msg)

    conversation = conversations[conversation_id]

    # Stage 1: Goal Inference
    inferred_goals = []
    if conversation.pipeline_settings.infer:
        inferred_goals = await infer_goals(
            user_message, message_id, len(conversation.goals)
        )
        user_msg.goals = inferred_goals

        if inferred_goals:
            inferred_goals_data = [goal.model_dump() for goal in inferred_goals]
            await manager.send_message({
                "type": "goals_inferred",
                "goals": inferred_goals_data,
                "message_id": message_id
            }, websocket)

    # Stage 2: Goal Merging
    final_goals = inferred_goals
    if conversation.pipeline_settings.merge and conversation.goals and inferred_goals:
        old_goals_snapshot = {g.id: g.model_copy() for g in conversation.goals}
        merged_goals = await merge_goals(conversation.goals, inferred_goals, message_id)

        turn_num = len([m for m in conversation.messages if m.role == 'user'])
        for mg in merged_goals:
            prev_ids = []
            prev_texts = []
            for oid, og in old_goals_snapshot.items():
                if og.text in mg.text or mg.text in og.text:
                    prev_ids.append(oid)
                    prev_texts.append(og.text)
            for ig in inferred_goals:
                if ig.id not in old_goals_snapshot and (ig.text in mg.text or mg.text in ig.text):
                    if ig.id not in prev_ids:
                        prev_ids.append(ig.id)
                        prev_texts.append(ig.text)
            op = 'keep'
            if len(prev_ids) > 1:
                op = 'combine'
            elif prev_ids and prev_ids[0] != mg.id:
                op = 'replace'
            if not prev_ids:
                op = 'infer'
            from backend.models import GoalHistoryEntry
            conversation.goal_history.append(GoalHistoryEntry(
                turn=turn_num,
                operation=op,
                goal_id=mg.id,
                goal_text=mg.text,
                goal_type=mg.type,
                previous_goal_ids=prev_ids,
                previous_goal_texts=prev_texts,
            ))

        conversation.goals = merged_goals
        final_goals = merged_goals
    elif inferred_goals:
        conversation.goals.extend(inferred_goals)
        final_goals = conversation.goals

    if final_goals:
        goals_data = [goal.model_dump() for goal in final_goals]
        await manager.send_message({
            "type": "goals_updated",
            "goals": goals_data,
            "message_id": message_id
        }, websocket)

    # Generate and stream LLM response
    assistant_message_id = f"msg_{len(conversations[conversation_id].messages)}"

    response_text = await stream_llm_response(
        user_message, manager, websocket, assistant_message_id, conversation.messages
    )

    assistant_msg = Message(
        id=assistant_message_id,
        content=response_text,
        role="assistant",
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id].messages.append(assistant_msg)

    # Stage 3: Goal Evaluation
    if conversation.pipeline_settings.evaluate and conversation.goals and response_text:
        evaluations = []

        for goal in conversation.goals:
            if not goal.completed:
                evaluation = await evaluate_goal(goal, response_text)
                evaluations.append(evaluation)

        if evaluations:
            await manager.send_message({
                "type": "goals_evaluated",
                "evaluations": evaluations,
                "message_id": assistant_message_id
            }, websocket)

    # Stage 4: Keyphrase extraction
    if response_text and len(response_text) > 20:
        keyphrases = await extract_keyphrases(response_text)
        if keyphrases:
            await manager.send_message({
                "type": "keyphrases_extracted",
                "keyphrases": keyphrases,
                "message_id": assistant_message_id
            }, websocket)

    # Stage 5: Detection alerts
    new_alerts = []

    # 5a: Forgetting detection
    forgetting_results = await detect_forgetting(conversation.goals, response_text)
    for item in forgetting_results:
        alert = GoalAlert(
            alert_type="forgetting",
            severity="warning",
            goal_ids=[item.get("goal_id", "")],
            message=item.get("reason", "Goal appears forgotten"),
            suggestion=item.get("suggestion", ""),
        )
        new_alerts.append(alert)

    # 5b: Contradiction detection
    contradiction_results = await detect_contradiction(conversation.goals)
    for item in contradiction_results:
        alert = GoalAlert(
            alert_type="contradiction",
            severity="critical",
            goal_ids=[item.get("goal_id_1", ""), item.get("goal_id_2", "")],
            message=item.get("reason", "Goals contradict each other"),
            suggestion=item.get("resolution", ""),
        )
        new_alerts.append(alert)

    # 5c: Derailment detection
    derailment_result = await detect_derailment(conversation.goals, response_text)
    if derailment_result:
        alert = GoalAlert(
            alert_type="derailment",
            severity="warning",
            goal_ids=[g.id for g in conversation.goals if not g.completed],
            message=derailment_result.get("reason", "Response has derailed from goals"),
            suggestion=derailment_result.get("suggestion", ""),
        )
        new_alerts.append(alert)

    # 5d: Repetition detection
    repetition_result = await detect_repetition(conversation.messages)
    if repetition_result:
        alert = GoalAlert(
            alert_type="repetition",
            severity="warning",
            goal_ids=[g.id for g in conversation.goals if not g.completed],
            message=repetition_result.get("repeated_content", "Assistant is repeating content"),
            suggestion=repetition_result.get("suggestion", ""),
        )
        new_alerts.append(alert)

    # 5e: Fixation detection
    fixation_result = await detect_fixation(conversation.goals)
    if fixation_result:
        goal_ids = fixation_result.get("fixated_goal_ids", []) + fixation_result.get("neglected_goal_ids", [])
        alert = GoalAlert(
            alert_type="fixation",
            severity="warning",
            goal_ids=goal_ids,
            message=fixation_result.get("reason", "Assistant shows goal fixation"),
            suggestion=fixation_result.get("suggestion", ""),
        )
        new_alerts.append(alert)

    # 5f: Communication breakdown detection
    breakdown_result = await detect_breakdown(conversation.messages, conversation.goals)
    if breakdown_result:
        alert = GoalAlert(
            alert_type="breakdown",
            severity="critical",
            goal_ids=breakdown_result.get("repeated_goal_ids", []),
            message=breakdown_result.get("reason", "Communication breakdown detected"),
            suggestion=breakdown_result.get("suggestion", ""),
        )
        new_alerts.append(alert)

    if new_alerts:
        conversation.alerts.extend(new_alerts)
        alerts_data = [a.model_dump() for a in new_alerts]
        await manager.send_message({
            "type": "alerts_detected",
            "alerts": alerts_data,
            "message_id": assistant_message_id
        }, websocket)

    progress = compute_goal_progress(conversation)
    if progress:
        await manager.send_message({
            "type": "goal_progress_updated",
            "progress": progress,
        }, websocket)


async def handle_pipeline_toggle(message_data, conversation_id, conversations, websocket, manager):
    """Handle pipeline stage toggle"""
    stage = message_data["stage"]
    enabled = message_data["enabled"]
    setattr(conversations[conversation_id].pipeline_settings, stage, enabled)

    await manager.send_message({
        "type": "pipeline_toggled",
        "stage": stage,
        "enabled": enabled
    }, websocket)


async def handle_get_conversation(conversation_id, conversations, websocket, manager):
    """Handle get conversation request"""
    conversation = conversations[conversation_id]
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