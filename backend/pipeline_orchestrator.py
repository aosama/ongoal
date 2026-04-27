"""
Pipeline Orchestrator — Coordinates the goal processing pipeline.

Each stage is a focused async function. The orchestrator calls them in
sequence and broadcasts results over the WebSocket connection.
"""

import logging
from datetime import datetime
from typing import List

from backend.models import Goal, Message, GoalAlert
from backend.pipelines import (
    infer_goals, merge_goals, evaluate_goal, stream_llm_response,
    extract_keyphrases, detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, compute_goal_progress, detect_breakdown,
    replace_outdated_goals,
)

logger = logging.getLogger(__name__)


async def run_goal_pipeline(conversation, user_message: str, message_id: str, websocket, manager):
    """Run the full goal pipeline: infer → merge → stream → evaluate → detect.

    Returns (assistant_message_id, response_text).
    """
    await _run_inference(conversation, user_message, message_id, websocket, manager)
    await _run_merge(conversation, user_message, message_id, websocket, manager)

    assistant_message_id = f"msg_{len(conversation.messages)}"
    response_text = await _run_streaming(user_message, conversation.messages, assistant_message_id, websocket, manager)

    assistant_msg = Message(
        id=assistant_message_id,
        content=response_text,
        role="assistant",
        timestamp=datetime.now().isoformat()
    )
    conversation.messages.append(assistant_msg)

    await _run_evaluation(conversation, response_text, assistant_message_id, websocket, manager)
    await _run_keyphrases(response_text, assistant_message_id, websocket, manager)
    await _run_detection_alerts(conversation, response_text, assistant_message_id, websocket, manager)
    await _send_goal_progress(conversation, websocket, manager)

    return assistant_message_id, response_text


async def _run_inference(conversation, user_message: str, message_id: str, websocket, manager):
    if not conversation.pipeline_settings.infer:
        return

    user_msg = next(m for m in conversation.messages if m.id == message_id)
    inferred = await infer_goals(user_message, message_id, len(conversation.goals))
    user_msg.goals = inferred

    if inferred:
        await manager.send_message({
            "type": "goals_inferred",
            "goals": [g.model_dump() for g in inferred],
            "message_id": message_id,
        }, websocket)


async def _run_merge(conversation, user_message: str, message_id: str, websocket, manager):
    if not conversation.pipeline_settings.merge or not conversation.goals:
        inferred = _get_inferred_goals(conversation, message_id)
        if inferred:
            conversation.goals.extend(inferred)
        return

    inferred = _get_inferred_goals(conversation, message_id)
    if not inferred:
        return

    conversation.goals = await replace_outdated_goals(conversation.goals, inferred, message_id, conversation)

    old_goals_snapshot = {g.id: g.model_copy() for g in conversation.goals}
    merged_goals = await merge_goals(conversation.goals, inferred, message_id)

    turn_num = len([m for m in conversation.messages if m.role == "user"])
    for mg in merged_goals:
        prev_ids, prev_texts = _find_previous_goal_ids(mg, old_goals_snapshot, inferred)
        op = _determine_operation(prev_ids, mg.id)
        conversation.record_goal_history(
            turn=turn_num, operation=op, goal_id=mg.id,
            goal_text=mg.text, goal_type=mg.type,
            previous_goal_ids=prev_ids, previous_goal_texts=prev_texts,
        )

    conversation.goals = merged_goals

    goals_data = [g.model_dump() for g in merged_goals]
    await manager.send_message({
        "type": "goals_updated",
        "goals": goals_data,
        "message_id": message_id,
    }, websocket)


async def _run_streaming(user_message: str, conversation_messages, assistant_message_id: str, websocket, manager) -> str:
    return await stream_llm_response(
        user_message, manager, websocket, assistant_message_id, conversation_messages
    )


async def _run_evaluation(conversation, response_text: str, assistant_message_id: str, websocket, manager):
    if not conversation.pipeline_settings.evaluate or not conversation.goals or not response_text:
        return

    evaluations = []
    for goal in conversation.goals:
        if not goal.completed:
            evaluation = await evaluate_goal(goal, response_text)
            evaluations.append(evaluation)

    if evaluations:
        await manager.send_message({
            "type": "goals_evaluated",
            "evaluations": evaluations,
            "message_id": assistant_message_id,
        }, websocket)


async def _run_keyphrases(response_text: str, assistant_message_id: str, websocket, manager):
    if not response_text or len(response_text) <= 20:
        return

    keyphrases = await extract_keyphrases(response_text)
    if keyphrases:
        await manager.send_message({
            "type": "keyphrases_extracted",
            "keyphrases": keyphrases,
            "message_id": assistant_message_id,
        }, websocket)


async def _run_detection_alerts(conversation, response_text: str, assistant_message_id: str, websocket, manager):
    new_alerts = []

    forgetting_results = await detect_forgetting(conversation.goals, response_text)
    for item in forgetting_results:
        new_alerts.append(GoalAlert(
            alert_type="forgetting", severity="warning",
            goal_ids=[item.get("goal_id", "")],
            message=item.get("reason", "Goal appears forgotten"),
            suggestion=item.get("suggestion", ""),
        ))

    contradiction_results = await detect_contradiction(conversation.goals)
    for item in contradiction_results:
        new_alerts.append(GoalAlert(
            alert_type="contradiction", severity="critical",
            goal_ids=[item.get("goal_id_1", ""), item.get("goal_id_2", "")],
            message=item.get("reason", "Goals contradict each other"),
            suggestion=item.get("resolution", ""),
        ))

    derailment_result = await detect_derailment(conversation.goals, response_text)
    if derailment_result:
        new_alerts.append(GoalAlert(
            alert_type="derailment", severity="warning",
            goal_ids=[g.id for g in conversation.goals if not g.completed],
            message=derailment_result.get("reason", "Response has derailed from goals"),
            suggestion=derailment_result.get("suggestion", ""),
        ))

    repetition_result = await detect_repetition(conversation.messages)
    if repetition_result:
        new_alerts.append(GoalAlert(
            alert_type="repetition", severity="warning",
            goal_ids=[g.id for g in conversation.goals if not g.completed],
            message=repetition_result.get("repeated_content", "Assistant is repeating content"),
            suggestion=repetition_result.get("suggestion", ""),
        ))

    fixation_result = await detect_fixation(conversation.goals)
    if fixation_result:
        goal_ids = fixation_result.get("fixated_goal_ids", []) + fixation_result.get("neglected_goal_ids", [])
        new_alerts.append(GoalAlert(
            alert_type="fixation", severity="warning",
            goal_ids=goal_ids,
            message=fixation_result.get("reason", "Assistant shows goal fixation"),
            suggestion=fixation_result.get("suggestion", ""),
        ))

    breakdown_result = await detect_breakdown(conversation.messages, conversation.goals)
    if breakdown_result:
        new_alerts.append(GoalAlert(
            alert_type="breakdown", severity="critical",
            goal_ids=breakdown_result.get("repeated_goal_ids", []),
            message=breakdown_result.get("reason", "Communication breakdown detected"),
            suggestion=breakdown_result.get("suggestion", ""),
        ))

    if new_alerts:
        conversation.alerts.extend(new_alerts)
        await manager.send_message({
            "type": "alerts_detected",
            "alerts": [a.model_dump() for a in new_alerts],
            "message_id": assistant_message_id,
        }, websocket)


async def _send_goal_progress(conversation, websocket, manager):
    progress = compute_goal_progress(conversation)
    if progress:
        await manager.send_message({
            "type": "goal_progress_updated",
            "progress": progress,
        }, websocket)


def _get_inferred_goals(conversation, message_id: str) -> List[Goal]:
    user_msg = next((m for m in conversation.messages if m.id == message_id), None)
    if user_msg and user_msg.goals:
        return user_msg.goals
    return []


def _find_previous_goal_ids(merged_goal, old_goals_snapshot, inferred_goals):
    prev_ids = []
    prev_texts = []
    for oid, og in old_goals_snapshot.items():
        if og.text in merged_goal.text or merged_goal.text in og.text:
            prev_ids.append(oid)
            prev_texts.append(og.text)
    for ig in inferred_goals:
        if ig.id not in old_goals_snapshot and (ig.text in merged_goal.text or merged_goal.text in ig.text):
            if ig.id not in prev_ids:
                prev_ids.append(ig.id)
                prev_texts.append(ig.text)
    return prev_ids, prev_texts


def _determine_operation(prev_ids, merged_goal_id):
    if not prev_ids:
        return "infer"
    if len(prev_ids) > 1:
        return "combine"
    if prev_ids[0] != merged_goal_id:
        return "replace"
    return "keep"