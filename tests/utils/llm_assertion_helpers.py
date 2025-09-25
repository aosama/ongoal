"""
LLM-based assertion helpers for semantic testing

Uses Claude Haiku to make intelligent assertions about goals and language
instead of relying on exact keyword matching.
"""

import json
import os
from anthropic import AsyncAnthropic
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMAssertionResult:
    """Result of an LLM-based assertion"""
    def __init__(self, passed: bool, reason: str, confidence: str = "high"):
        self.passed = passed
        self.reason = reason
        self.confidence = confidence
    
    def __str__(self):
        return f"LLM Assertion: {'PASS' if self.passed else 'FAIL'} - {self.reason} (confidence: {self.confidence})"


class LLMAssertionHelper:
    """Helper class for making LLM-based assertions in tests"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("ANTHROPIC_MODEL")
        if not self.model:
            raise ValueError("ANTHROPIC_MODEL environment variable is required for test assertions")
    
    async def assert_goal_semantic_match(self, goals: List[Dict], expected_concept: str, context: str = "") -> LLMAssertionResult:
        """
        Assert that a list of goals contains a specific concept semantically
        
        Args:
            goals: List of goal dictionaries with 'text' and 'type' fields
            expected_concept: The concept to look for (e.g., "make the story shorter")
            context: Additional context for the assertion
        
        Returns:
            LLMAssertionResult with pass/fail and reason
        """
        
        goals_text = "\n".join([f"- [{goal.get('type', 'unknown')}] {goal.get('text', '')}" for goal in goals])
        
        prompt = f"""You are evaluating whether a list of goals contains a specific concept.

CONTEXT: {context if context else "Testing goal extraction and merging in a conversational AI system."}

GOALS TO EVALUATE:
{goals_text}

EXPECTED CONCEPT: "{expected_concept}"

TASK: Determine if any of the goals semantically captures or relates to the expected concept. Consider:
- Exact matches
- Paraphrases and synonyms  
- Combined/merged goals that incorporate the concept
- Related concepts that serve the same purpose

Respond ONLY with valid JSON in this format:
{{
  "passed": true/false,
  "reason": "Brief explanation of your decision",
  "confidence": "high/medium/low"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON response
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            result_data = json.loads(response_text)
            
            return LLMAssertionResult(
                passed=result_data.get("passed", False),
                reason=result_data.get("reason", "No reason provided"),
                confidence=result_data.get("confidence", "unknown")
            )
            
        except Exception as e:
            # Fallback to conservative assertion
            return LLMAssertionResult(
                passed=False,
                reason=f"LLM assertion failed due to error: {str(e)}",
                confidence="low"
            )
    
    async def assert_goal_preserved_through_merge(self, 
                                                original_goals: List[Dict],
                                                new_goals: List[Dict], 
                                                merged_goals: List[Dict],
                                                target_concept: str) -> LLMAssertionResult:
        """
        Assert that a concept from new_goals is preserved in the merged result
        
        Args:
            original_goals: The initial goals before merge
            new_goals: The new goals being merged in
            merged_goals: The final merged result
            target_concept: The concept that should be preserved
        
        Returns:
            LLMAssertionResult with pass/fail and reason
        """
        
        original_text = "\n".join([f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in original_goals])
        new_text = "\n".join([f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in new_goals])
        merged_text = "\n".join([f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in merged_goals])
        
        prompt = f"""You are evaluating a goal merging operation to ensure important concepts are preserved.

TARGET CONCEPT TO PRESERVE: "{target_concept}"

ORIGINAL GOALS:
{original_text}

NEW GOALS BEING MERGED:
{new_text}

FINAL MERGED GOALS:
{merged_text}

TASK: Determine if the target concept from the new goals is properly preserved in the merged result. The concept may be:
- Kept as a separate goal
- Combined with an existing similar goal
- Integrated into an existing goal's text

The concept should NOT be completely lost unless there's a valid reason (e.g., direct contradiction).

Respond ONLY with valid JSON in this format:
{{
  "passed": true/false,
  "reason": "Explanation of whether and how the concept was preserved",
  "confidence": "high/medium/low"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON response
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            result_data = json.loads(response_text)
            
            return LLMAssertionResult(
                passed=result_data.get("passed", False),
                reason=result_data.get("reason", "No reason provided"),
                confidence=result_data.get("confidence", "unknown")
            )
            
        except Exception as e:
            # Fallback to conservative assertion
            return LLMAssertionResult(
                passed=False,
                reason=f"LLM assertion failed due to error: {str(e)}",
                confidence="low"
            )

    async def assert_goals_capture_message_intent(self, 
                                                message: str,
                                                goals: List[Dict],
                                                expected_intents: List[str]) -> LLMAssertionResult:
        """
        Assert that extracted goals properly capture the intended meanings from a message
        
        Args:
            message: The original user message
            goals: The extracted goals
            expected_intents: List of intents that should be captured
        
        Returns:
            LLMAssertionResult with pass/fail and reason
        """
        
        goals_text = "\n".join([f"- [{g.get('type', 'unknown')}] {g.get('text', '')}" for g in goals])
        intents_text = "\n".join([f"- {intent}" for intent in expected_intents])
        
        prompt = f"""You are evaluating whether extracted goals properly capture the user's intended meanings.

USER MESSAGE:
"{message}"

EXTRACTED GOALS:
{goals_text}

EXPECTED INTENTS TO CAPTURE:
{intents_text}

TASK: Determine if the extracted goals adequately capture all the expected intents from the user message. Consider:
- Are the main requests/questions/suggestions identified?
- Are important details and constraints preserved?
- Is the overall intent correctly understood?

Respond ONLY with valid JSON in this format:
{{
  "passed": true/false,
  "reason": "Explanation of how well the goals capture the intended meanings",
  "confidence": "high/medium/low"
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON response  
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            
            result_data = json.loads(response_text)
            
            return LLMAssertionResult(
                passed=result_data.get("passed", False),
                reason=result_data.get("reason", "No reason provided"),
                confidence=result_data.get("confidence", "unknown")
            )
            
        except Exception as e:
            # Fallback to conservative assertion
            return LLMAssertionResult(
                passed=False,
                reason=f"LLM assertion failed due to error: {str(e)}",
                confidence="low"
            )


# Global helper instance for easy use in tests
llm_assert = LLMAssertionHelper()
