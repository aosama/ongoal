"""
Goal Progress Stage — Compute cross-message goal progress tracking.

Implements REQ-03-02-001 and REQ-03-02-004.
"""

from typing import List, Dict


def compute_goal_progress(conversation) -> List[Dict]:
    """Compute goal progress tracking across all messages (REQ-03-02-001, REQ-03-02-004).

    For each active goal, counts confirm/ignore/contradict across all
    evaluations and derives a progress summary with completion status.
    """
    progress = []
    for goal in conversation.goals:
        if goal.completed:
            progress.append({
                "goal_id": goal.id,
                "goal_text": goal.text,
                "confirm_count": 0,
                "ignore_count": 0,
                "contradict_count": 0,
                "total_evaluations": 0,
                "progress_pct": 100,
                "completion_status": "completed_manual",
            })
            continue

        confirm_count = 0
        ignore_count = 0
        contradict_count = 0

        for msg in conversation.messages:
            if msg.role == "assistant" and msg.goals:
                for msg_goal in msg.goals:
                    if msg_goal.id == goal.id and msg_goal.evaluation:
                        cat = msg_goal.evaluation.category
                        if cat == "confirm":
                            confirm_count += 1
                        elif cat == "ignore":
                            ignore_count += 1
                        elif cat == "contradict":
                            contradict_count += 1

        if goal.evaluation:
            current = goal.evaluation.category
            if current == "confirm":
                confirm_count += 1
            elif current == "ignore":
                ignore_count += 1
            elif current == "contradict":
                contradict_count += 1

        total = confirm_count + ignore_count + contradict_count
        if total == 0:
            pct = 0
        else:
            pct = int((confirm_count / total) * 100)

        if confirm_count >= 2 and ignore_count == 0 and contradict_count == 0:
            completion_status = "likely_complete"
        elif confirm_count >= 1 and pct >= 60:
            completion_status = "progressing"
        elif ignore_count > confirm_count:
            completion_status = "at_risk"
        elif contradict_count > 0:
            completion_status = "contradicted"
        else:
            completion_status = "active"

        progress.append({
            "goal_id": goal.id,
            "goal_text": goal.text,
            "confirm_count": confirm_count,
            "ignore_count": ignore_count,
            "contradict_count": contradict_count,
            "total_evaluations": total,
            "progress_pct": pct,
            "completion_status": completion_status,
        })
    return progress
