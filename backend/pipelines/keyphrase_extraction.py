"""
Keyphrase Extraction Stage — Extract salient keyphrases from assistant responses.

Implements Appendix A.4 of the OnGoal requirements.
"""

import logging
from typing import List

from backend.llm_caller import call_llm_json

logger = logging.getLogger(__name__)


async def extract_keyphrases(assistant_response: str) -> List[str]:
    """Extract salient keyphrases from an assistant response (REQ-09-04-001-005)."""

    keyphrase_prompt = f"""You will be presented with an assistant response. Extract the most salient keyphrases from the response exactly as they appear verbatim. Focus on phrases that capture key topics and themes.

Respond ONLY with a valid JSON in the following format:

{{
  "keyphrases": ["<KEYPHRASE_1>", "<KEYPHRASE_2>"]
}}

Assistant response: {assistant_response}"""

    data = await call_llm_json(keyphrase_prompt, max_tokens=500, label="Keyphrase extraction")
    if data:
        return data.get("keyphrases", [])

    logger.warning("Keyphrase extraction: no JSON found in response")
    return []