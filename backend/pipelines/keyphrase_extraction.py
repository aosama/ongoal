"""
Keyphrase Extraction Stage — Extract salient keyphrases from assistant responses.

Implements Appendix A.4 of the OnGoal requirements.
"""

import json
import logging
import re
from typing import List

from backend.llm_service import LLMService

logger = logging.getLogger(__name__)


async def extract_keyphrases(assistant_response: str) -> List[str]:
    """Extract salient keyphrases from an assistant response (REQ-09-04-001–005).

    Uses the keyphrase extraction prompt from OnGoal Requirements Appendix A.4.
    Returns a list of verbatim phrases capturing the most salient topics.
    """

    keyphrase_prompt = f"""You will be presented with an assistant response. Extract the most salient keyphrases from the response exactly as they appear verbatim. Focus on phrases that capture key topics and themes.

Respond ONLY with a valid JSON in the following format:

{{
  "keyphrases": ["<KEYPHRASE_1>", "<KEYPHRASE_2>"]
}}

Assistant response: {assistant_response}"""

    try:
        response_text = await LLMService.generate_response(keyphrase_prompt, max_tokens=500)

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("keyphrases", [])

        logger.warning("Keyphrase extraction: no JSON found in response")
        return []

    except Exception as e:
        logger.warning("Keyphrase extraction failed: %s", e)
        return []
