# Section 09: LLM Prompts - TDD Requirements

## A.1 Infer Goals Prompt

### REQ-09-01-001: Goal Inference Prompt Structure
**GIVEN**: A user dialogue message requiring goal extraction:
**WHEN**: The infer goals prompt is executed:
**THEN**: The prompt should instruct extraction of every clause verbatim:
**ACCEPTANCE CRITERIA**:
- Prompt specifies extraction of every clause exactly as it appears
- Instructions are clear about verbatim extraction requirement
- Prompt targets human dialogue in conversation with assistant

### REQ-09-01-002: Goal Type Classification Instruction
**GIVEN**: Clauses extracted from user dialogue:
**WHEN**: The infer goals prompt processes them:
**THEN**: Each clause should be classified as question, request, offer, or suggestion:
**ACCEPTANCE CRITERIA**:
- Only these four goal types are specified
- Classification instruction is explicit in prompt
- Each clause gets exactly one type assignment

### REQ-09-01-003: Goal Summary Generation Requirement
**GIVEN**: Each extracted clause with its type:
**WHEN**: The infer goals prompt completes processing:
**THEN**: A one-sentence summary of how to address the goal should be generated:
**ACCEPTANCE CRITERIA**:
- Summary is exactly one sentence
- Summary explains how to address the goal
- Summary is brief and actionable

### REQ-09-01-004: Infer Goals JSON Response Format Specification
**GIVEN**: The infer goals prompt execution:
**WHEN**: The LLM responds:
**THEN**: The response should be ONLY valid JSON with specific structure:
**ACCEPTANCE CRITERIA**:
- Response contains only JSON (no additional text)
- JSON has "clauses" array at root level
- Each clause object has "clause", "type", and "summary" fields
- JSON structure exactly matches specification
- Response is parseable as valid JSON

### REQ-09-01-005: Infer Goals Clause Field Content
**GIVEN**: A clause object in the JSON response:
**WHEN**: The clause field is populated:
**THEN**: It should contain the exact verbatim text from user dialogue:
**ACCEPTANCE CRITERIA**:
- Text is extracted exactly as it appears in original
- No paraphrasing or modification of original text
- Quotation marks and punctuation preserved
- Whitespace handling maintains original meaning

### REQ-09-01-006: Infer Goals Type Field Values
**GIVEN**: A clause object with type classification:
**WHEN**: The type field is set:
**THEN**: It should contain only one of the four valid goal types:
**ACCEPTANCE CRITERIA**:
- Type is "question", "request", "offer", or "suggestion"
- No other values are acceptable
- Type accurately reflects the nature of the clause
- Classification is consistent with definitions

### REQ-09-01-007: Infer Goals Summary Field Content
**GIVEN**: A clause object with goal summary:
**WHEN**: The summary field is populated:
**THEN**: It should contain exactly one sentence explaining goal resolution:
**ACCEPTANCE CRITERIA**:
- Summary is exactly one sentence
- Sentence is complete with proper punctuation
- Explanation is clear and actionable
- Summary relates directly to the specific clause

## A.2 Merge Goals Prompt

### REQ-09-02-001: Merge Goals Input Parameter Structure
**GIVEN**: Goal merge operation requirements:
**WHEN**: The merge prompt is prepared:
**THEN**: It should accept two specific input parameters:
**ACCEPTANCE CRITERIA**:
- old_goals_str_list parameter for existing goals
- new_goals_str_list parameter for newly inferred goals
- Both parameters are newline-delimited string lists
- Parameters contain numbered goal items

### REQ-09-02-002: Merge Goals Parameter Format Specification
**GIVEN**: Goal list parameters for merging:
**WHEN**: Parameters are formatted:
**THEN**: They should be newline-delimited numbered lists:
**ACCEPTANCE CRITERIA**:
- Goals are separated by newline characters
- Each goal has a number prefix (e.g., "1. ", "2. ")
- Format example: "1. Goal text\n2. Another goal"
- Numbering is consistent and sequential

### REQ-09-02-003: Three Merge Operations Definition
**GIVEN**: The merge goals prompt instructions:
**WHEN**: The LLM processes two goal lists:
**THEN**: It should use exactly three defined operations:
**ACCEPTANCE CRITERIA**:
- Replace operation for contradictory goals
- Combine operation for similar goals
- Keep operation for unique goals
- No other operations are permitted
- Each operation has specific criteria

### REQ-09-02-004: Replace Operation Specification
**GIVEN**: A new goal that contradicts an existing goal:
**WHEN**: The merge operation is determined:
**THEN**: Replace operation should be selected with specific goal number tracking:
**ACCEPTANCE CRITERIA**:
- Old contradictory goal is replaced by new goal
- Operation labeled as "Replace"
- Old goal number and new goal number are recorded
- Contradiction detection is consistent
- Replaced goal content comes from new goal

### REQ-09-02-005: Combine Operation Specification
**GIVEN**: A new goal that is similar to an existing goal:
**WHEN**: The merge operation is determined:
**THEN**: Combine operation should create a unified goal:
**ACCEPTANCE CRITERIA**:
- Similar goals are merged into single updated goal
- Operation labeled as "Combine"
- Old goal number and new goal number are recorded
- Combined goal incorporates elements of both goals
- Similarity detection is consistent

### REQ-09-02-006: Keep Operation Specification
**GIVEN**: A goal that is unique (not similar to any other goal):
**WHEN**: The merge operation is determined:
**THEN**: Keep operation should preserve the goal unchanged:
**ACCEPTANCE CRITERIA**:
- Unique goals remain in final list
- Operation labeled as "Keep"
- Original goal number is recorded
- Goal content remains exactly the same
- Uniqueness detection is consistent

### REQ-09-02-007: Merge Goals JSON Response Format
**GIVEN**: Completed merge operations:
**WHEN**: The merge goals prompt generates response:
**THEN**: Response should be ONLY valid JSON with operations array:
**ACCEPTANCE CRITERIA**:
- Response contains only JSON (no additional text)
- JSON has "operations" array at root level
- Each operation object has required fields
- JSON structure matches specification exactly
- Response is parseable as valid JSON

### REQ-09-02-008: Merge Operation Object Structure
**GIVEN**: An operation in the merge results:
**WHEN**: The operation object is created:
**THEN**: It should contain updated_goal, operation, and goal_numbers fields:
**ACCEPTANCE CRITERIA**:
- "updated_goal" field contains the final goal text
- "operation" field contains operation type (Replace/Combine/Keep)
- "goal_numbers" array contains relevant original goal numbers
- All fields are populated appropriately for operation type
- Field types match specification

### REQ-09-02-009: Goal Numbers Tracking Requirement
**GIVEN**: Any merge operation (Replace, Combine, or Keep):
**WHEN**: The operation is recorded:
**THEN**: Original goal numbers should be tracked in goal_numbers array:
**ACCEPTANCE CRITERIA**:
- Replace: [old_goal_number, new_goal_number]
- Combine: [old_goal_number, new_goal_number]
- Keep: [original_goal_number]
- Numbers correspond to input list positions
- Array format is consistent across operation types

## A.3 Evaluate Goals Prompt

### REQ-09-03-001: Evaluate Goals Input Parameter
**GIVEN**: Goal evaluation requirements:
**WHEN**: The evaluate prompt is prepared:
**THEN**: It should accept a goal_str parameter:
**ACCEPTANCE CRITERIA**:
- goal_str parameter contains a single conversational goal
- Parameter is formatted as a string
- Example format: "Use figurative language."
- Goal text is clear and specific

### REQ-09-03-002: Goal Evaluation Context Specification
**GIVEN**: The evaluate goals prompt structure:
**WHEN**: Evaluation is performed:
**THEN**: Both human dialogue and assistant response should be provided as context:
**ACCEPTANCE CRITERIA**:
- Prompt includes human dialogue for context
- Assistant response is provided for evaluation
- Context is sufficient for accurate evaluation
- Both elements are clearly identified

### REQ-09-03-003: Three-Category Evaluation System
**GIVEN**: A goal being evaluated against an assistant response:
**WHEN**: The evaluation is performed:
**THEN**: The result should be exactly one of three categories:
**ACCEPTANCE CRITERIA**:
- "confirm" category for goals that are addressed
- "contradict" category for goals that are opposed
- "ignore" category for goals that are not addressed
- Only these three categories are valid
- Each goal receives exactly one category

### REQ-09-03-004: Evaluation Explanation Requirement
**GIVEN**: A goal evaluation with assigned category:
**WHEN**: The explanation is generated:
**THEN**: It should be exactly one sentence explaining the relationship:
**ACCEPTANCE CRITERIA**:
- Explanation is exactly one sentence
- Sentence explains relationship between response and goal
- Explanation is clear and specific
- Explanation justifies the assigned category

### REQ-09-03-005: Supporting Evidence Extraction
**GIVEN**: An assistant response being evaluated:
**WHEN**: Evidence is extracted:
**THEN**: Clauses should be extracted verbatim as supporting examples:
**ACCEPTANCE CRITERIA**:
- Examples are extracted exactly as they appear in response
- Multiple examples can be extracted
- Examples support the assigned evaluation category
- No paraphrasing or modification of original text

### REQ-09-03-006: Evaluate Goals JSON Response Format
**GIVEN**: Completed goal evaluation:
**WHEN**: The evaluate goals prompt generates response:
**THEN**: Response should be ONLY valid JSON with evaluation structure:
**ACCEPTANCE CRITERIA**:
- Response contains only JSON (no additional text)
- JSON has "category", "explanation", and "examples" fields at root
- Structure matches specification exactly
- Response is parseable as valid JSON

### REQ-09-03-007: Evaluation Category Field Values
**GIVEN**: The category field in evaluation response:
**WHEN**: The field is populated:
**THEN**: It should contain only one of the three valid categories:
**ACCEPTANCE CRITERIA**:
- Value is "confirm", "contradict", or "ignore"
- No other values are acceptable
- Category accurately reflects evaluation result
- Spelling and case match specification exactly

### REQ-09-03-008: Evaluation Examples Array Format
**GIVEN**: The examples field in evaluation response:
**WHEN**: Supporting evidence is provided:
**THEN**: It should be an array of verbatim text excerpts:
**ACCEPTANCE CRITERIA**:
- Examples are in array format
- Each example is a string
- Text is extracted verbatim from assistant response
- Array can contain multiple examples
- Empty array is valid if no supporting evidence found

## A.4 Keyphrase Extraction Prompt

### REQ-09-04-001: Keyphrase Extraction Input
**GIVEN**: An assistant response requiring keyphrase analysis:
**WHEN**: The keyphrase extraction prompt is executed:
**THEN**: The prompt should process the complete assistant response:
**ACCEPTANCE CRITERIA**:
- Takes full assistant response as input
- Analyzes entire response text
- No truncation or filtering of input
- Processes all content regardless of length

### REQ-09-04-002: Verbatim Phrase Extraction Requirement
**GIVEN**: An assistant response being analyzed:
**WHEN**: Keyphrases are extracted:
**THEN**: Phrases should be extracted exactly as they appear in the response:
**ACCEPTANCE CRITERIA**:
- Phrases are verbatim from original response
- No paraphrasing or modification allowed
- Punctuation and capitalization preserved
- Original text formatting maintained

### REQ-09-04-003: Salient Topic Focus
**GIVEN**: Extracted phrases from assistant response:
**WHEN**: Keyphrases are selected:
**THEN**: Only phrases that capture the most salient topics should be included:
**ACCEPTANCE CRITERIA**:
- Phrases represent key topics and themes
- Most important concepts are prioritized
- Less relevant phrases are excluded
- Selection captures response essence
- Topical relevance is clearly apparent

### REQ-09-04-004: Keyphrase Extraction JSON Format
**GIVEN**: Completed keyphrase extraction:
**WHEN**: The prompt generates response:
**THEN**: Response should be ONLY valid JSON with keyphrases array:
**ACCEPTANCE CRITERIA**:
- Response contains only JSON (no additional text)
- JSON has "keyphrases" array at root level
- Array contains string elements
- Structure matches specification exactly
- Response is parseable as valid JSON

### REQ-09-04-005: Keyphrases Array Content
**GIVEN**: The keyphrases array in the response:
**WHEN**: The array is populated:
**THEN**: Each element should be a salient phrase from the response:
**ACCEPTANCE CRITERIA**:
- Each array element is a string
- Strings contain verbatim phrases from response
- Phrases are topically significant
- Array can contain multiple keyphrases
- Phrases are distinct and non-redundant

## General Prompt Requirements

### REQ-09-99-001: JSON-Only Response Enforcement
**GIVEN**: Any OnGoal system prompt execution:
**WHEN**: The LLM generates a response:
**THEN**: The response should contain ONLY valid JSON with no additional text:
**ACCEPTANCE CRITERIA**:
- No explanatory text before JSON
- No commentary after JSON
- No markdown code blocks
- No additional formatting
- Pure JSON response only

### REQ-09-99-002: Prompt Consistency Across Operations
**GIVEN**: All OnGoal prompt implementations:
**WHEN**: Prompts are reviewed for consistency:
**THEN**: Similar patterns and requirements should be applied uniformly:
**ACCEPTANCE CRITERIA**:
- JSON format requirements are consistent
- Verbatim extraction requirements are consistent
- Output structure specifications follow same patterns
- Error handling approaches are uniform

### REQ-09-99-003: Prompt Robustness for Edge Cases
**GIVEN**: OnGoal prompts processing various inputs:
**WHEN**: Edge cases or unusual inputs are encountered:
**THEN**: Prompts should handle them gracefully:
**ACCEPTANCE CRITERIA**:
- Empty inputs produce valid responses
- Very long inputs are processed correctly
- Unusual formatting doesn't break parsing
- Error conditions produce valid JSON
- Graceful degradation when LLM fails to follow instructions

### REQ-09-99-004: Prompt Performance and Efficiency
**GIVEN**: OnGoal prompts in production use:
**WHEN**: Multiple prompt executions occur:
**THEN**: Prompts should be efficient and produce consistent results:
**ACCEPTANCE CRITERIA**:
- Prompts are concise while maintaining clarity
- Token usage is optimized
- Consistent outputs for similar inputs
- Reasonable processing time
- Reliable JSON parsing success rate