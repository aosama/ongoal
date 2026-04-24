"""
LLM Streaming Stage — Stream assistant responses with mid-stream disconnect handling.
"""

import logging
from typing import List

from backend.llm_service import LLMService

logger = logging.getLogger(__name__)


async def stream_llm_response(message: str, connection_manager, websocket, message_id: str, conversation_messages: List):
    """Stream LLM response using the configured provider"""
    if not LLMService.is_available():
        error_msg = "LLM service unavailable - API key not configured"
        await connection_manager.send_message({
            "type": "error",
            "message": error_msg
        }, websocket)
        return error_msg

    try:
        messages_for_llm = []

        if conversation_messages:
            for msg in conversation_messages:
                messages_for_llm.append({
                    "role": msg.role,
                    "content": msg.content
                })

        messages_for_llm.append({
            "role": "user",
            "content": message
        })

        full_response = ""
        async for text_chunk in LLMService.generate_streaming_response(messages_for_llm, max_tokens=2000):
            full_response += text_chunk

            send_ok = await connection_manager.send_message({
                "type": "llm_response_chunk",
                "text": text_chunk,
                "message_id": message_id
            }, websocket)

            # Stop burning tokens if the client disconnected mid-stream
            if not send_ok:
                logger.info("WebSocket disconnected mid-stream (message %s) — stopping LLM", message_id)
                return full_response

        await connection_manager.send_message({
            "type": "llm_response_complete",
            "message_id": message_id,
            "full_text": full_response
        }, websocket)

        return full_response

    except Exception as e:
        logger.error("LLM streaming error: %s", e)
        error_msg = "Unable to generate response. Please check your API key configuration."
        await connection_manager.send_message({
            "type": "error",
            "message": error_msg
        }, websocket)
        return error_msg
