# Section 04: The OnGoal System - TDD Requirements

## 4.1 Modeling Goals Using a Pipeline

### REQ-04-01-001: Goal Pipeline Architecture
**GIVEN**: A conversational AI system with user input:
**WHEN**: The system receives a user message:
**THEN**: The system should execute a three-stage pipeline (infer, merge, evaluate):
**ACCEPTANCE CRITERIA**:
- Pipeline has exactly three stages
- Each stage can be independently toggled on/off
- Pipeline processes goals sequentially through all stages

### REQ-04-01-002: Goal Definition Compliance
**GIVEN**: A user message containing potential conversational goals:
**WHEN**: The system analyzes the message:
**THEN**: Goals should be identified as questions, requests, offers, or suggestions only:
**ACCEPTANCE CRITERIA**:
- Only these four goal types are recognized
- Each goal is assigned exactly one type
- Goal definition matches research paper specification

### REQ-04-01-003: Independent LLM for Pipeline
**GIVEN**: A chat LLM handling user conversation and a separate pipeline LLM:
**WHEN**: The goal pipeline executes:
**THEN**: The pipeline should use the independent LLM (not the chat LLM):
**ACCEPTANCE CRITERIA**:
- Pipeline LLM is separate from chat LLM
- Pipeline can work with any decoder LLM architecture
- Pipeline supports Claude Haiku by default

## 4.1.1 Infer Stage

### REQ-04-01-101: Goal Inference from User Message
**GIVEN**: A user message in a conversation:
**WHEN**: The infer stage processes the message:
**THEN**: The system should extract all conversational goals from the message:
**ACCEPTANCE CRITERIA**:
- All questions, requests, offers, and suggestions are identified
- Goals are extracted verbatim as clauses
- Each goal includes type classification
- Output includes summary of how to address each goal

### REQ-04-01-102: Goal Inference JSON Format
**GIVEN**: Goals extracted from a user message:
**WHEN**: The infer stage completes:
**THEN**: The output should be valid JSON with specified structure:
**ACCEPTANCE CRITERIA**:
- JSON contains "clauses" array
- Each clause has "clause", "type", and "summary" fields
- Format matches specification exactly
- JSON is valid and parseable

## 4.1.2 Merge Stage

### REQ-04-01-201: Goal List Comparison
**GIVEN**: Existing goals from conversation history and newly inferred goals:
**WHEN**: The merge stage executes:
**THEN**: The system should compare and merge the goal lists:
**ACCEPTANCE CRITERIA**:
- Takes two inputs: old goals and new goals
- Analyzes similarity and conflicts between goals
- Outputs combined goal list

### REQ-04-01-202: Combine Operation
**GIVEN**: A new goal similar to an existing goal:
**WHEN**: The merge stage processes these goals:
**THEN**: The system should combine them into a single goal:
**ACCEPTANCE CRITERIA**:
- Similar goals are merged into one updated goal
- Operation is labeled as "combine"
- Both original goal numbers are tracked
- Combined goal incorporates elements of both

### REQ-04-01-203: Replace Operation
**GIVEN**: A new goal that contradicts an existing goal:
**WHEN**: The merge stage processes these goals:
**THEN**: The system should replace the old goal with the new one:
**ACCEPTANCE CRITERIA**:
- Contradictory goals trigger replacement
- Operation is labeled as "replace"
- Old goal is removed, new goal takes its place
- Both original goal numbers are tracked

### REQ-04-01-204: Keep Operation
**GIVEN**: A goal that is unique (not similar to any other goal):
**WHEN**: The merge stage processes this goal:
**THEN**: The system should keep the goal unchanged:
**ACCEPTANCE CRITERIA**:
- Unique goals are preserved
- Operation is labeled as "keep"
- Original goal number is tracked
- Goal content remains unchanged

### REQ-04-01-205: Merge JSON Output Format
**GIVEN**: Completed goal merge operations:
**WHEN**: The merge stage outputs results:
**THEN**: The output should be valid JSON with specified structure:
**ACCEPTANCE CRITERIA**:
- JSON contains "operations" array
- Each operation has "updated_goal", "operation", and "goal_numbers" fields
- Format matches specification exactly
- All three operation types are supported

## 4.1.3 Evaluate Stage

### REQ-04-01-301: Goal Evaluation Against LLM Response
**GIVEN**: A merged goal list and an LLM response to user message:
**WHEN**: The evaluate stage processes them:
**THEN**: Each goal should be evaluated against the LLM response:
**ACCEPTANCE CRITERIA**:
- Every final merged goal is evaluated
- Evaluation uses the LLM response as input
- Each goal receives one evaluation result

### REQ-04-01-302: Three-Category Evaluation System
**GIVEN**: A goal being evaluated against an LLM response:
**WHEN**: The evaluation completes:
**THEN**: The result should be one of three categories: confirm, contradict, or ignore:
**ACCEPTANCE CRITERIA**:
- Only these three categories are used
- Each goal gets exactly one category
- Categories are mutually exclusive

### REQ-04-01-303: Evaluation Explanations
**GIVEN**: A goal evaluation result:
**WHEN**: The evaluation stage outputs the result:
**THEN**: The system should provide an explanation for the evaluation:
**ACCEPTANCE CRITERIA**:
- Explanation is exactly one sentence
- Explains relationship between response and goal
- Clarifies why the category was chosen

### REQ-04-01-304: Supporting Evidence Extraction
**GIVEN**: An LLM response being evaluated against a goal:
**WHEN**: The evaluation determines a category:
**THEN**: The system should extract supporting evidence phrases:
**ACCEPTANCE CRITERIA**:
- Phrases are extracted verbatim from LLM response
- Evidence supports the evaluation category
- Multiple examples can be extracted
- Examples appear exactly as in original response

### REQ-04-01-305: Evaluation JSON Output Format
**GIVEN**: Completed goal evaluation:
**WHEN**: The evaluate stage outputs results:
**THEN**: The output should be valid JSON with specified structure:
**ACCEPTANCE CRITERIA**:
- JSON contains "category", "explanation", and "examples" fields
- Category is one of the three valid values
- Examples array contains verbatim phrases
- Format matches specification exactly

## 4.2 Visualizing Goals in the Chat UI

### REQ-04-02-001: In-Situ and Ex-Situ Visualization Integration
**GIVEN**: Goal pipeline data for a conversation:
**WHEN**: The chat interface displays the conversation:
**THEN**: Both inline and sidebar visualizations should be present:
**ACCEPTANCE CRITERIA**:
- In-situ visualizations appear within chat messages
- Ex-situ visualizations appear in separate progress panel
- Both types integrate goal pipeline data
- Visualizations update in real-time

## 4.2.1 In-Situ Goal Evaluations

### REQ-04-02-101: Goal Glyphs Under User Messages
**GIVEN**: A user message with inferred goals:
**WHEN**: The message is displayed in the chat:
**THEN**: Goal glyphs should appear under the user message:
**ACCEPTANCE CRITERIA**:
- Glyphs indicate inferred goals from user message
- Glyphs appear directly below user message
- Number of glyphs matches number of inferred goals

### REQ-04-02-102: Goal Glyphs Under LLM Messages
**GIVEN**: An LLM response with evaluated goals:
**WHEN**: The response is displayed in the chat:
**THEN**: Goal glyphs should appear under the LLM message with evaluation colors:
**ACCEPTANCE CRITERIA**:
- Glyphs reflect final merged goals and evaluations
- Green glyphs for "confirm" evaluations
- Red glyphs for "contradict" evaluations
- Yellow glyphs for "ignore" evaluations

### REQ-04-02-103: Goal Glyph Click Interaction for User Goals
**GIVEN**: A goal glyph under a user message:
**WHEN**: The user clicks the glyph:
**THEN**: An inline explanation panel should open:
**ACCEPTANCE CRITERIA**:
- Panel explains how the goal was inferred
- Panel highlights the user phrase that generated the goal
- Panel appears inline with the message
- Only one panel can be open at a time

### REQ-04-02-104: Goal Glyph Click Interaction for LLM Goals
**GIVEN**: A goal glyph under an LLM message:
**WHEN**: The user clicks the glyph:
**THEN**: An inline explanation panel should open with evaluation details:
**ACCEPTANCE CRITERIA**:
- Panel includes evaluation explanation
- Panel shows supporting evidence from LLM response
- Evidence is highlighted in context
- Panel appears inline with the message

### REQ-04-02-105: Quick Assessment Via Goal Glyphs
**GIVEN**: A conversation with multiple messages and goal glyphs:
**WHEN**: A user scrolls through the conversation:
**THEN**: They should be able to quickly assess goal progress:
**ACCEPTANCE CRITERIA**:
- Color coding allows rapid assessment
- Goal status is visible without clicking
- Temporal progress is trackable through scrolling

## 4.2.2 Ex-Situ Progress Panel

### REQ-04-02-201: Three-Tab Progress Panel Structure
**GIVEN**: The OnGoal interface:
**WHEN**: The progress panel is displayed:
**THEN**: It should contain exactly three tabs: Goals, Timeline, Events:
**ACCEPTANCE CRITERIA**:
- Panel appears next to the chat interface
- Three tabs are clearly labeled
- Tabs can be switched between
- Each tab serves different evaluation objectives

### REQ-04-02-202: Goals Tab - Goal List Widget Display
**GIVEN**: The Goals tab is selected:
**WHEN**: The tab content loads:
**THEN**: All final goals should be displayed as widgets:
**ACCEPTANCE CRITERIA**:
- Each goal appears as a separate widget
- Widgets contain text description of goal
- Goals shown are the final merged goals from pipeline
- List updates as conversation progresses

### REQ-04-02-203: Goals Tab - Lock Goal Control
**GIVEN**: A goal widget in the Goals tab:
**WHEN**: A user interacts with the lock control:
**THEN**: The goal should be locked from being merged:
**ACCEPTANCE CRITERIA**:
- Lock control is present on each goal widget
- Locked goals are excluded from merge operations
- Lock status is visually indicated
- Lock can be toggled on/off

### REQ-04-02-204: Goals Tab - Complete Goal Control
**GIVEN**: A goal widget in the Goals tab:
**WHEN**: A user marks a goal as complete:
**THEN**: The goal should be removed from future evaluations:
**ACCEPTANCE CRITERIA**:
- Complete control is present on each goal widget
- Completed goals don't appear in new evaluations
- Complete status is visually indicated
- Action can be undone if needed

### REQ-04-02-205: Goals Tab - Restore Previously Merged Goals
**GIVEN**: Goals that were previously merged or replaced:
**WHEN**: A user accesses restore functionality:
**THEN**: They should be able to restore previous goal versions:
**ACCEPTANCE CRITERIA**:
- Restore functionality is accessible from Goals tab
- Previously merged goals can be recovered
- Restored goals re-enter the active goal list
- History of goal changes is maintained

### REQ-04-02-206: Timeline Tab - Sankey Visualization Structure
**GIVEN**: The Timeline tab is selected:
**WHEN**: The tab content loads:
**THEN**: A Sankey-based timeline should visualize pipeline history:
**ACCEPTANCE CRITERIA**:
- Visualization flows from top to bottom
- Each user prompt/LLM response pair has three rows
- Row 1: Inferred goals with connection lines
- Row 2: Final goals with merge operation lines
- Row 3: Evaluation result icons

### REQ-04-02-207: Timeline Tab - Inferred Goals Row
**GIVEN**: The Timeline visualization for a user message:
**WHEN**: Row 1 is displayed:
**THEN**: It should show inferred goals with connection lines to existing goals:
**ACCEPTANCE CRITERIA**:
- Newly inferred goals are displayed
- Lines connect to related existing goals
- Visual indicates goal relationships
- Row is clearly the first of three

### REQ-04-02-208: Timeline Tab - Final Goals Row
**GIVEN**: The Timeline visualization after merge operations:
**WHEN**: Row 2 is displayed:
**THEN**: It should show final goals with operation lines from above rows:
**ACCEPTANCE CRITERIA**:
- Final merged goals are displayed
- Lines indicate combine, replace, and keep operations
- Connection to row 1 goals is visually clear
- Row is clearly the second of three

### REQ-04-02-209: Timeline Tab - Evaluation Results Row
**GIVEN**: The Timeline visualization after goal evaluation:
**WHEN**: Row 3 is displayed:
**THEN**: It should show evaluation result icons:
**ACCEPTANCE CRITERIA**:
- Icons represent evaluation results (confirm, contradict, ignore)
- Check icon for "confirm"
- Cross icon for "contradict"
- Prohibited sign for "ignore"
- Icons connect to final goals from row 2

### REQ-04-02-210: Timeline Tab - Message Navigation
**GIVEN**: The Timeline tab with numbered user/LLM icons:
**WHEN**: A user clicks on an icon:
**THEN**: The chat window should scroll to the corresponding message:
**ACCEPTANCE CRITERIA**:
- User icons and LLM icons are numbered and clickable
- Clicking scrolls chat to exact message
- Navigation works bidirectionally
- Visual feedback indicates the connection

### REQ-04-02-211: Events Tab - Pipeline Operations List
**GIVEN**: The Events tab is selected:
**WHEN**: The tab content loads:
**THEN**: Pipeline events should be displayed in a grouped list:
**ACCEPTANCE CRITERIA**:
- Events are grouped by user prompt/LLM response pairs
- List shows pipeline operations in chronological order
- Verbose descriptions are provided for each event
- Events correspond to infer, merge, and evaluate operations

### REQ-04-02-212: Events Tab - Message Navigation
**GIVEN**: The Events tab with message references:
**WHEN**: A user clicks on a numbered user or LLM icon:
**THEN**: The chat window should scroll to the corresponding message:
**ACCEPTANCE CRITERIA**:
- Icons are numbered and clickable in events list
- Clicking scrolls chat to exact message
- Navigation matches Timeline tab functionality
- Visual feedback shows message correspondence

## 4.2.3 Individual Goal View

### REQ-04-02-301: Goal Selection for Individual View
**GIVEN**: The Goals tab with goal widgets:
**WHEN**: A user selects/clicks on a specific goal widget:
**THEN**: The interface should switch to individual goal view:
**ACCEPTANCE CRITERIA**:
- Goal selection is clearly indicated in Goals tab
- Interface transitions to filtered view
- Selected goal remains highlighted
- Easy way to return to full view

### REQ-04-02-302: Chat Filtering for Selected Goal
**GIVEN**: A goal selected for individual view:
**WHEN**: The individual goal view activates:
**THEN**: The chat window should show only LLM responses evaluated against that goal:
**ACCEPTANCE CRITERIA**:
- Only relevant LLM responses are displayed
- User messages remain for context
- Filtered messages maintain chronological order
- Clear indication that filtering is active

### REQ-04-02-303: Individual Goal Progress Panel Transformation
**GIVEN**: Individual goal view is active:
**WHEN**: The progress panel updates:
**THEN**: It should show evaluations list for the selected goal:
**ACCEPTANCE CRITERIA**:
- Progress panel transforms from three tabs to evaluations list
- List shows all evaluations for selected goal
- Each evaluation entry shows evaluation result and details
- List is chronologically ordered

### REQ-04-02-304: Evaluation Selection and Chat Navigation
**GIVEN**: The individual goal evaluations list:
**WHEN**: A user selects/clicks on an evaluation:
**THEN**: The chat window should scroll to the corresponding LLM response:
**ACCEPTANCE CRITERIA**:
- Each evaluation in list is clickable
- Clicking scrolls to exact LLM response
- Selected evaluation is highlighted
- Response is highlighted or indicated in chat

### REQ-04-02-305: Goal Comparison Over Time
**GIVEN**: Individual goal view showing multiple responses:
**WHEN**: A user scans the filtered messages:
**THEN**: They should be able to easily compare LLM responses for that goal:
**ACCEPTANCE CRITERIA**:
- Responses are visually comparable
- Temporal sequence is clear
- Patterns like repeating phrases are identifiable
- Inconsistent responses are detectable
- Forgotten requests are visible

## 4.3 Highlighting Text to Support Sensemaking

### REQ-04-03-001: Goal Evaluation Example Highlighting
**GIVEN**: A goal explanation panel is open with examples:
**WHEN**: The examples are displayed:
**THEN**: They should be highlighted inline in the LLM response with evaluation colors:
**ACCEPTANCE CRITERIA**:
- Examples are highlighted within original LLM response text
- Green highlighting for "confirm" examples
- Yellow highlighting for "ignore" examples
- Red highlighting for "contradict" examples
- Highlighting appears when explanation panel is open

### REQ-04-03-002: Cross-Response Example Comparison
**GIVEN**: Multiple LLM responses with highlighted examples:
**WHEN**: A user views the responses:
**THEN**: They should be able to compare highlighted text across responses:
**ACCEPTANCE CRITERIA**:
- Highlighting persists across multiple responses
- Same goal examples use consistent colors
- Patterns in highlighted text are visually apparent
- Consistency assessment is possible through visual comparison

### REQ-04-03-003: Individual Goal View Default Highlighting
**GIVEN**: Individual goal view is active:
**WHEN**: LLM responses are displayed:
**THEN**: Goal evaluation examples should be highlighted by default:
**ACCEPTANCE CRITERIA**:
- Highlighting appears without opening explanation panels
- All evaluation examples for selected goal are highlighted
- Color coding matches evaluation results
- Highlighting covers all relevant LLM responses in view

### REQ-04-03-004: Text Highlighting Mode Toggle
**GIVEN**: Individual goal view with highlighting options:
**WHEN**: A user accesses highlighting controls:
**THEN**: Three additional highlighting modes should be available:
**ACCEPTANCE CRITERIA**:
- Key phrases highlighting mode available
- Similar sentences highlighting mode available
- Unique sentences highlighting mode available
- Modes can be toggled on/off independently
- Multiple modes can be active simultaneously

### REQ-04-03-005: Key Phrases Extraction and Highlighting
**GIVEN**: Individual goal view with key phrases mode enabled:
**WHEN**: The highlighting is applied:
**THEN**: Shared and unique key phrases should be highlighted across responses:
**ACCEPTANCE CRITERIA**:
- Key phrases are extracted using generative LLM
- Shared phrases across responses are visually indicated
- Unique phrases per response are visually distinguished
- Phrase extraction follows specified prompt format
- Highlighting updates as new responses are added

### REQ-04-03-006: Similar Sentences Identification and Highlighting
**GIVEN**: Individual goal view with similar sentences mode enabled:
**WHEN**: The highlighting is applied:
**THEN**: Sentence pairs with highest similarity should be highlighted:
**ACCEPTANCE CRITERIA**:
- Sentences are tokenized for analysis
- Text embeddings computed using generative LLM
- Pairwise cosine similarity calculated between sentences
- Highest similarity pairs are visually highlighted
- Similar sentences are easily identifiable across responses

### REQ-04-03-007: Unique Sentences Identification and Highlighting
**GIVEN**: Individual goal view with unique sentences mode enabled:
**WHEN**: The highlighting is applied:
**THEN**: Sentences with lowest average similarity should be highlighted:
**ACCEPTANCE CRITERIA**:
- Average similarity computed for each sentence against all others
- Sentences with lowest average similarity identified as unique
- Unique sentences are visually highlighted distinctly
- Uniqueness is calculated across all responses in goal view
- Highlighting helps identify novel content

### REQ-04-03-008: Global LLM Behavior Pattern Detection
**GIVEN**: Text highlighting modes revealing patterns across responses:
**WHEN**: A user reviews the highlighted content:
**THEN**: Global LLM behaviors should be identifiable:
**ACCEPTANCE CRITERIA**:
- Repetitive patterns are visually apparent
- Topic drift over time is detectable
- Inconsistencies between responses are highlighted
- Distractions from main goals are identifiable
- Behavioral changes over conversation length are visible

## 4.4 Usage Scenario Requirements

### REQ-04-04-001: Multi-Turn Dialogue Support
**GIVEN**: A user engaging in extended conversation with LLM:
**WHEN**: OnGoal interface is used throughout the session:
**THEN**: The system should maintain goal tracking across all turns:
**ACCEPTANCE CRITERIA**:
- Goals persist across multiple conversation turns
- Goal pipeline operates on every user message
- Progress tracking spans entire conversation
- Context is maintained throughout session

### REQ-04-04-002: Exploratory Data Analysis Workflow Support
**GIVEN**: A user performing data analysis tasks with LLM assistance:
**WHEN**: They use OnGoal to manage the conversation:
**THEN**: The system should support iterative goal refinement and progress tracking:
**ACCEPTANCE CRITERIA**:
- Initial broad goals can be refined over time
- Ignored goals are clearly identified for follow-up
- Goal progress is tracked across analysis iterations
- Users can drill down into specific goal histories

## 4.5 Implementation Requirements

### REQ-04-05-001: Python Backend with Anthropic Claude Integration
**GIVEN**: The OnGoal system backend implementation:
**WHEN**: The goal pipeline executes:
**THEN**: It should be implemented in Python using Anthropic Claude API:
**ACCEPTANCE CRITERIA**:
- Backend implemented in Python
- Uses Anthropic library for API calls
- Targets Claude Haiku model by default
- Results are streamed to frontend interface

### REQ-04-05-002: LLM Architecture Flexibility
**GIVEN**: The OnGoal system architecture:
**WHEN**: Different LLM models need to be supported:
**THEN**: The system should work with any decoder LLM architecture:
**ACCEPTANCE CRITERIA**:
- Architecture is model-agnostic for decoder LLMs
- Easy adaptation to open-source LLMs
- Support for local LLMs (e.g., PyTorch)
- Configuration allows model switching

### REQ-04-05-003: Vue.js Frontend Implementation
**GIVEN**: The OnGoal system frontend:
**WHEN**: The user interface is rendered:
**THEN**: It should be implemented using Vue.js framework:
**ACCEPTANCE CRITERIA**:
- Frontend built with Vue.js
- Responsive interface design
- Real-time updates from backend
- Cross-browser compatibility

### REQ-04-05-004: D3.js Visualizations
**GIVEN**: The OnGoal visualization components:
**WHEN**: Goal data needs to be visualized:
**THEN**: Visualizations should be built using D3.js:
**ACCEPTANCE CRITERIA**:
- Timeline visualization uses D3.js
- Sankey diagrams implemented with D3.js
- Interactive visualization elements
- Smooth animations and transitions