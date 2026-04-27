"""
Sentence Similarity — Compare sentences across assistant responses.

Identifies similar and unique sentences to highlight overlap
and distinct content in multi-turn conversations.
"""

import re
from typing import Dict, List

from backend.llm_caller import call_llm_json


async def compute_sentence_similarity(conversation) -> Dict:
    """Compute similar and unique sentences across assistant responses (REQ-04-03-006/007)."""
    assistant_messages = [m for m in conversation.messages if m.role == "assistant"]

    if len(assistant_messages) < 2:
        return {
            "similar_sentences": [],
            "unique_sentences": [{"text": m.content, "message_id": m.id} for m in assistant_messages] if assistant_messages else [],
            "message_count": len(assistant_messages),
        }

    sentence_map: List[Dict] = []
    for msg in assistant_messages:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', msg.content) if len(s.strip()) > 20]
        for s in sentences:
            sentence_map.append({"text": s, "message_id": msg.id})

    if len(sentence_map) < 2:
        return {"similar_sentences": [], "unique_sentences": sentence_map, "message_count": len(assistant_messages)}

    sentences_text = "\n".join(f"{i+1}. {s['text']}" for i, s in enumerate(sentence_map))

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

    data = await call_llm_json(prompt, max_tokens=1000, label="Sentence similarity")
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

    return {"similar_sentences": [], "unique_sentences": [], "message_count": len(assistant_messages)}