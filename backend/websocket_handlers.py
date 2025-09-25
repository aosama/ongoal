"""
OnGoal WebSocket Handlers - Real-time communication with frontend
"""
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from backend.models import Message, Conversation
from backend.goal_pipeline import infer_goals, merge_goals, evaluate_goal, stream_llm_response
from backend.api_endpoints import get_conversations_store


async def handle_websocket_connection(websocket: WebSocket, manager, conversation_id: str = "default"):
    """Handle WebSocket connection and message processing"""
    # WebSocket connection attempt
    await manager.connect(websocket)
    # WebSocket connected successfully for conversation: {conversation_id}
    
    # Get reference to conversations storage
    conversations = get_conversations_store()
    
    # Initialize conversation if not exists
    if conversation_id not in conversations:
        conversations[conversation_id] = Conversation(id=conversation_id)
    
    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()
            message_data = json.loads(data)
            # Received WebSocket message
            
            if message_data["type"] == "user_message":
                await handle_user_message(message_data, conversation_id, conversations, websocket, manager)
            
            elif message_data["type"] == "toggle_pipeline":
                await handle_pipeline_toggle(message_data, conversation_id, conversations, websocket, manager)
            
            elif message_data["type"] == "get_conversation":
                await handle_get_conversation(conversation_id, conversations, websocket, manager)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        # WebSocket error occurred
        manager.disconnect(websocket)


async def handle_user_message(message_data, conversation_id, conversations, websocket, manager):
    """Handle user message and run goal pipeline"""
    user_message = message_data["message"]
    message_id = f"msg_{len(conversations[conversation_id].messages)}"
    # Received user message
    
    # Store user message
    user_msg = Message(
        id=message_id,
        content=user_message,
        role="user",
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id].messages.append(user_msg)
    
    # Run goal pipeline with exact prompts from requirements
    conversation = conversations[conversation_id]
    
    # Stage 1: Goal Inference (if enabled)
    inferred_goals = []
    if conversation.pipeline_settings.get("infer", True):
        # Running goal inference
        inferred_goals = await infer_goals(
            user_message, 
            message_id, 
            len(conversation.goals)
        )
        # Found inferred goals
        user_msg.goals = inferred_goals
        
        # Send inferred goals to frontend for timeline population
        if inferred_goals:
            inferred_goals_data = [goal.model_dump() for goal in inferred_goals]
            # Sending inferred goals to timeline
            await manager.send_message({
                "type": "goals_inferred", 
                "goals": inferred_goals_data,
                "message_id": message_id
            }, websocket)
    
    # Stage 2: Goal Merging (if enabled and there are existing goals)
    final_goals = inferred_goals
    if conversation.pipeline_settings.get("merge", True) and conversation.goals and inferred_goals:
        # Running goal merge
        merged_goals = await merge_goals(conversation.goals, inferred_goals)
        # Merge completed
        
        # Replace conversation goals with merged result
        conversation.goals = merged_goals
        final_goals = merged_goals
    elif inferred_goals:
        # Just add new goals if merge is disabled
        conversation.goals.extend(inferred_goals)
        final_goals = conversation.goals
    
    # Send goals to frontend after inference/merge
    if final_goals:
        goals_data = [goal.model_dump() for goal in final_goals]
        # Sending goals to frontend
        await manager.send_message({
            "type": "goals_updated",
            "goals": goals_data,
            "message_id": message_id
        }, websocket)
    
    # Generate and stream LLM response
    assistant_message_id = f"msg_{len(conversations[conversation_id].messages)}"
    
    # Start streaming response
    response_text = await stream_llm_response(
        user_message, 
        manager,
        websocket, 
        assistant_message_id,
        conversation.messages
    )
    
    # Store assistant message
    assistant_msg = Message(
        id=assistant_message_id,
        content=response_text,
        role="assistant", 
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id].messages.append(assistant_msg)
    
    # Stage 3: Goal Evaluation (if enabled and there are active goals)
    if conversation.pipeline_settings.get("evaluate", True) and conversation.goals and response_text:
        # Running goal evaluation
        evaluations = []
        
        for goal in conversation.goals:
            if not goal.completed:  # Only evaluate active goals
                evaluation = await evaluate_goal(goal, response_text)
                evaluations.append(evaluation)
                
                # Update goal status based on evaluation
                goal.status = evaluation["category"]
        
        # Send evaluation results to frontend
        if evaluations:
            # Sending evaluations to frontend
            await manager.send_message({
                "type": "goals_evaluated",
                "evaluations": evaluations,
                "message_id": assistant_message_id
            }, websocket)


async def handle_pipeline_toggle(message_data, conversation_id, conversations, websocket, manager):
    """Handle pipeline stage toggle"""
    stage = message_data["stage"]
    enabled = message_data["enabled"]
    conversations[conversation_id].pipeline_settings[stage] = enabled

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
            "pipeline_settings": conversation.pipeline_settings
        }
    }, websocket)
