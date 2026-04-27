# Structural Complexity Reduction — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Eliminate unnecessary indirection layers, duplicated patterns, and god functions from the OnGoal backend to make the codebase simpler and more maintainable.

**Architecture:** Remove `LLMService` (zero-value shim) and `goal_pipeline.py` (re-export shim). Replace `LLMService` calls with direct `get_provider()` usage. Extract a shared `call_llm_json` helper used by all pipeline modules. Break the 217-line `handle_user_message` into a pipeline orchestrator. Consolidate 3 scattered goal-history creation sites into one helper. Collapse 6 near-identical detection functions into a base class. Move inline LLM calls out of `api_endpoints.py` into the pipeline layer. Make test fixtures not spawn servers for unit-only tests.

**Tech Stack:** Python 3.13+, FastAPI, Pydantic, httpx, pytest

---

### Task 1: Delete LLMService, update all callers to use get_provider()

**Objective:** Remove the `LLMService` static class which adds no logic beyond delegating to `get_provider()`, and update all ~30 call sites.

**Files:**
- Delete: `backend/llm_service.py`
- Modify: `backend/llm_provider.py` (add `generate_json` convenience method + `is_available()` + `get_service_status()`)
- Modify: `backend/pipelines/goal_inference.py:13,48` — replace `LLMService` with `get_provider()`
- Modify: `backend/pipelines/goal_evaluation.py:12,35` — replace
- Modify: `backend/pipelines/goal_merge.py:13,128` — replace
- Modify: `backend/pipelines/goal_detection.py:8,51,91,131,175,228,282` — replace
- Modify: `backend/pipelines/keyphrase_extraction.py:11,34` — replace
- Modify: `backend/pipelines/llm_streaming.py:8,15,39` — replace
- Modify: `backend/api_endpoints.py:26-28,40-44,360,376` — replace
- Modify: `backend/goal_pipeline.py:22` — remove LLMService import
- Modify: `tests/backend/test_should_handle_service_errors_gracefully.py` — update all patches from `backend.goal_pipeline.LLMService.*` to `backend.llm_provider.get_provider` or module-level provider
- Modify: `tests/utils/llm_assertion_helpers.py:38` — already uses `get_provider()`, no change needed
- Test: All existing tests must still pass

**Step 1: Add convenience methods to `backend/llm_provider.py`**

The `LLMService` class had two public methods beyond the provider: `is_available()` and `get_service_status()`. Move these to module-level functions in `llm_provider.py`:

```python
def is_available() -> bool:
    return get_provider().is_available()

def get_service_status() -> Dict[str, Any]:
    import os
    provider = get_provider()
    status = provider.get_status()
    status["configured_provider"] = os.getenv("LLM_PROVIDER", "ollama")
    return status
```

Also remove the `from backend.llm_service import LLMService` re-export from `goal_pipeline.py:22`.

**Step 2: Replace all `LLMService.generate_response` calls in pipeline modules**

Every pipeline module imports `from backend.llm_service import LLMService` and calls `LLMService.generate_response(prompt, max_tokens=N)`. Replace with:

```python
from backend.llm_provider import get_provider
# ...
provider = get_provider()
response_text = await provider.generate(prompt, max_tokens=N)
```

**Step 3: Replace all `LLMService.generate_streaming_response` / `is_available` in `llm_streaming.py`**

```python
from backend.llm_provider import get_provider, is_available
# ...
if not is_available():
# ...
async for text_chunk in get_provider().generate_stream(messages_for_llm, max_tokens=2000):
```

**Step 4: Replace `LLMService` in `api_endpoints.py`**

Health and status endpoints:
```python
from backend.llm_provider import get_service_status, is_available
# ...
service_status = get_service_status()
```

Sentence similarity (line 376):
```python
from backend.llm_provider import get_provider
# ...
response_text = await get_provider().generate(prompt, max_tokens=1000)
```

**Step 5: Update test patches**

All `patch('backend.goal_pipeline.LLMService.*')` and `patch('backend.pipelines.X.LLMService.*')` must change to patch the provider at the module level. Since `get_provider()` returns a cached singleton, tests can patch `backend.llm_provider.get_provider` or use `reset_provider()`. The cleanest pattern:

```python
# Instead of patch('backend.pipelines.goal_inference.LLMService.generate_response', ...)
# Use:
from unittest.mock import patch, AsyncMock
with patch('backend.llm_provider.get_provider') as mock_get_provider:
    mock_provider = AsyncMock()
    mock_provider.generate.return_value = fake_response
    mock_get_provider.return_value = mock_provider
    goals = await infer_goals("Write a story", "msg_0")
```

However, this changes many test files. A simpler approach that minimizes test changes: leave `LLMService` name as a module-level alias in each pipeline file. This way test patches continue to work without changes. But that partially defeats the purpose. Alternative: for now, in each pipeline module, create a module-level `_provider = get_provider()` and patch `module._provider`. We'll do the simpler thing for now.

**Decision:** To minimize test churn, we add a `get_llm()` function to `llm_provider.py` that returns the provider, and in each pipeline module we do `_llm = get_provider()` at module level. Tests that currently patch `LLMService.generate_response` will be updated to patch `get_provider` properly.

Actually, the cleanest minimal-change approach: don't change test patching yet. First delete LLMService. Then in Task 2 when we delete goal_pipeline.py, we'll fix the test imports. The tests that patch `backend.pipelines.X.LLMService.*` will break because LLMService won't be importable. So we must fix them in this task.

**Step 6: Run tests**

```bash
source .venv/bin/activate
python -m pytest tests/backend/ -v --tb=short
```

Expected: all tests pass with updated imports and patches.

**Step 7: Commit**

```bash
git add -A
git commit -m "refactor: delete LLMService, use get_provider() directly"
```

---

### Task 2: Delete goal_pipeline.py shim, fix test imports

**Objective:** Remove `backend/goal_pipeline.py` (22-line re-export shim) and update all tests that import from it to import from `backend.pipelines` instead.

**Files:**
- Delete: `backend/goal_pipeline.py`
- Modify: `tests/backend/test_should_replace_outdated_goals.py:11` — `from backend.goal_pipeline` → `from backend.pipelines`
- Modify: `tests/backend/test_should_validate_infer_goals_input.py:2` — same
- Modify: `tests/backend/test_should_catch_regression_defects.py:8` — same
- Modify: `tests/backend/test_should_detect_advanced_patterns.py:8` — same
- Modify: `tests/backend/test_should_handle_story_modification_workflows.py:17` — same
- Modify: `tests/backend/test_should_comply_with_merge_operations.py:15` — same
- Modify: `tests/backend/test_should_merge_goals_correctly.py:15` — same
- Modify: `tests/backend/test_should_handle_service_errors_gracefully.py:11,35,53,70,90,111,136,195,212,276` — change imports AND all `patch('backend.goal_pipeline.LLMService.*')` → `patch('backend.llm_provider.get_provider')`

**Step 1: Update test imports**

In each file listed above, change:
```python
from backend.goal_pipeline import infer_goals
```
to:
```python
from backend.pipelines import infer_goals
```

**Step 2: Fix monkeypatch references**

In `test_should_replace_outdated_goals.py`, change:
```python
monkeypatch.setattr("backend.goal_pipeline.detect_contradiction", fake_detect)
```
to:
```python
monkeypatch.setattr("backend.pipelines.goal_merge.detect_contradiction", fake_detect)
```

**Step 3: Fix LLMService patches in test_should_handle_service_errors_gracefully.py**

Change all `patch('backend.goal_pipeline.LLMService.*')` to patch the provider. Use the pattern established in Task 1.

**Step 4: Update websocket_handlers.py import**

`websocket_handlers.py:10` already imports from `backend.pipelines` — no change needed.

**Step 5: Delete goal_pipeline.py**

```bash
rm backend/goal_pipeline.py
```

**Step 6: Run tests**

```bash
python -m pytest tests/backend/ -v --tb=short
```

Expected: all pass.

**Step 7: Commit**

```bash
git add -A
git commit -m "refactor: delete goal_pipeline.py shim, fix test imports"
```

---

### Task 3: Extract pipeline_orchestrator.py from websocket_handlers.py

**Objective:** Break the 217-line `handle_user_message` god function into smaller composable functions in a new `pipeline_orchestrator.py` module. The websocket handler should only handle connection lifecycle and message dispatch.

**Files:**
- Create: `backend/pipeline_orchestrator.py`
- Modify: `backend/websocket_handlers.py` — slim down to ~50 lines (connect/dispatch/disconnect)
- Test: All existing tests pass (no functional change)

**Step 1: Create `backend/pipeline_orchestrator.py`**

Extract the following functions from `handle_user_message`:

```python
async def run_goal_pipeline(conversation, user_message, message_id, websocket, manager):
    """Run the full goal pipeline: infer → merge → evaluate → detect alerts."""
    # Stage 1: inference
    # Stage 2: merge (with history tracking)
    # Stage 3: stream LLM response
    # Stage 4: evaluation
    # Stage 5: keyphrase extraction
    # Stage 6: detection alerts
    # Stage 7: progress
    return assistant_message_id, response_text


async def run_inference(conversation, user_message, message_id, websocket, manager):
    ...

async def run_merge(conversation, inferred_goals, message_id, websocket, manager):
    ...

async def run_evaluation(conversation, response_text, assistant_message_id, websocket, manager):
    ...

async def run_detection_alerts(conversation, response_text, assistant_message_id, websocket, manager):
    ...

async def send_goal_progress(conversation, websocket, manager):
    ...
```

**Step 2: Rewrite `websocket_handlers.py` to use orchestrator**

```python
from backend.pipeline_orchestrator import run_goal_pipeline

async def handle_user_message(message_data, conversation_id, websocket, manager):
    async with conversation_repository.with_lock(conversation_id):
        conversation = conversation_repository.get_or_create(conversation_id)
        user_message = message_data["message"]
        message_id = f"msg_{len(conversation.messages)}"

        user_msg = Message(id=message_id, content=user_message, role="user", timestamp=datetime.now().isoformat())
        conversation.messages.append(user_msg)

        assistant_message_id, response_text = await run_goal_pipeline(
            conversation, user_message, message_id, websocket, manager
        )
```

**Step 3: Run tests**

```bash
python -m pytest tests/backend/ -v --tb=short
```

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: extract pipeline_orchestrator from websocket_handlers"
```

---

### Task 4: Create shared call_llm_json() helper

**Objective:** Extract the repeated "call LLM → parse JSON" pattern into a single `call_llm_json()` helper to eliminate ~12 copy-pasted code blocks.

**Files:**
- Create: `backend/llm_caller.py`
- Modify: All 6 pipeline modules to use `call_llm_json()` instead of inline LLM call + JSON parse
- Test: All existing tests pass

**Step 1: Create `backend/llm_caller.py`**

```python
async def call_llm_json(prompt: str, max_tokens: int = 1000, label: str = "") -> dict | None:
    """Call the LLM provider and return the parsed JSON object, or None on failure."""
    from backend.llm_provider import get_provider
    from backend.json_parser import extract_json_object
    try:
        provider = get_provider()
        response_text = await provider.generate(prompt, max_tokens=max_tokens)
        return extract_json_object(response_text)
    except Exception as e:
        if label:
            import logging
            logging.getLogger(__name__).warning("%s failed: %s", label, e)
        return None
```

**Step 2: Refactor each pipeline module**

Example — `goal_inference.py`:
```python
# Before:
from backend.llm_service import LLMService
response_text = await LLMService.generate_response(inference_prompt, max_tokens=1000)
from backend.json_parser import extract_json_object
response_data = extract_json_object(response_text)

# After:
from backend.llm_caller import call_llm_json
response_data = await call_llm_json(inference_prompt, max_tokens=1000, label="Goal inference")
```

Apply the same pattern to: `goal_evaluation.py`, `goal_merge.py`, `goal_detection.py`, `keyphrase_extraction.py`.

**Step 3: Run tests**

```bash
python -m pytest tests/backend/ -v --tb=short
```

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: extract call_llm_json() helper, eliminate 12 copy-paste patterns"
```

---

### Task 5: Move inline LLM calls from api_endpoints.py to pipelines

**Objective:** Move the inline LLM-calling code from `api_endpoints.py` (keyphrase extraction, sentence similarity) into the pipeline layer where it belongs.

**Files:**
- Modify: `backend/pipelines/keyphrase_extraction.py` — add `extract_keyphrases_for_conversation()` that takes a conversation
- Create: `backend/pipelines/sentence_similarity.py` — move sentence similarity logic from api_endpoints.py
- Modify: `backend/pipelines/__init__.py` — add new exports
- Modify: `backend/api_endpoints.py:311-398` — replace with pipeline calls
- Test: All existing tests pass

**Step 1: Create `backend/pipelines/sentence_similarity.py`**

Move the sentence splitting, prompt construction, LLM call, and result parsing from `api_endpoints.py:336-398` into a new function:

```python
async def compute_sentence_similarity(conversation) -> dict:
    """Compute similar and unique sentences across assistant responses."""
    # ... moved logic ...
```

**Step 2: Update api_endpoints.py to call pipeline functions**

```python
@router.post("/api/conversations/{conversation_id}/keyphrases")
async def extract_keyphrases(conversation_id: str):
    conversation = conversation_repository.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    from backend.pipelines import extract_keyphrases_for_conversation
    keyphrases = await extract_keyphrases_for_conversation(conversation)
    return {"keyphrases": keyphrases, ...}

@router.get("/api/conversations/{conversation_id}/sentence-similarity")
async def get_sentence_similarity(conversation_id: str):
    conversation = conversation_repository.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    from backend.pipelines import compute_sentence_similarity
    result = await compute_sentence_similarity(conversation)
    return result
```

**Step 3: Run tests**

```bash
python -m pytest tests/backend/ -v --tb=short
```

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: move inline LLM calls from api_endpoints to pipelines"
```

---

### Task 6: Consolidate goal history creation into 1 helper

**Objective:** Replace 3 scattered `GoalHistoryEntry(...)` creation sites with a single `record_goal_history()` helper on the `Conversation` model.

**Files:**
- Modify: `backend/models.py` — add `record_goal_history()` method to `Conversation`
- Modify: `backend/websocket_handlers.py:108-117` — use helper
- Modify: `backend/pipelines/goal_merge.py:57` — use helper
- Modify: `backend/api_endpoints.py:508-518` — use helper
- Test: All existing tests pass

**Step 1: Add `record_goal_history()` to `Conversation`**

```python
class Conversation(BaseModel):
    # ... existing fields ...

    def record_goal_history(self, turn: int, operation: str, goal_id: str,
                            goal_text: str, goal_type: str,
                            previous_goal_ids: list[str] = None,
                            previous_goal_texts: list[str] = None):
        from backend.models import GoalHistoryEntry
        self.goal_history.append(GoalHistoryEntry(
            turn=turn,
            operation=operation,
            goal_id=goal_id,
            goal_text=goal_text,
            goal_type=goal_type,
            previous_goal_ids=previous_goal_ids or [],
            previous_goal_texts=previous_goal_texts or [],
        ))
```

**Step 2: Replace all 3 call sites**

In websocket_handlers.py, goal_merge.py, and api_endpoints.py, replace inline `GoalHistoryEntry(...)` + `.append()` with:
```python
conversation.record_goal_history(turn=turn, operation=op, goal_id=..., ...)
```

**Step 3: Run tests**

```bash
python -m pytest tests/backend/ -v --tb=short
```

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: consolidate goal history creation into Conversation.record_goal_history()"
```

---

### Task 7: Restructure detection into DetectionRunner base

**Objective:** Collapse 6 near-identical detection functions in `goal_detection.py` (294 lines) into a base pattern, reducing ~120 lines of boilerplate.

**Files:**
- Modify: `backend/pipelines/goal_detection.py` — create base function + declarative specs
- Test: All existing tests pass

**Step 1: Create a generic `run_detection` function**

```python
async def _run_detection(prompt: str, max_tokens: int, bool_key: str, result_keys: dict, label: str) -> Optional[dict]:
    data = await call_llm_json(prompt, max_tokens=max_tokens, label=label)
    if not data or not data.get(bool_key, False):
        return None
    return {k: data.get(k, default) for k, (default) in result_keys.items()}
```

**Step 2: Refactor each detection function**

```python
async def detect_derailment(goals, assistant_response):
    if not goals or not assistant_response:
        return None
    # ... build prompt ...
    return await _run_detection(prompt, 600, "derailment",
        {"reason": ("",), "suggestion": ("",)}, "Derailment detection")
```

**Step 3: Run tests**

```bash
python -m pytest tests/backend/ -v --tb=short
```

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: collapse detection boilerplate with _run_detection helper"
```

---

### Task 8: Make conftest server fixtures non-autouse for unit tests

**Objective:** Unit tests should not wait for a backend server to start. Change `backend_server` from `autouse=True` to opt-in, and mark unit tests appropriately.

**Files:**
- Modify: `tests/conftest.py:236-237` — remove `autouse=True` from `backend_server`
- Modify: `tests/conftest.py:257-262` — remove `autouse=True` from `clean_state`, make it depend on `backend_server`
- Modify: `tests/backend/` — add `@pytest.mark.usefixtures("backend_server")` to tests that need the server
- Test: All existing tests pass

**Step 1: Change conftest.py**

```python
@pytest.fixture(scope="session")
def backend_server():
    # ... unchanged, but no autouse ...

@pytest.fixture(autouse=True)
def clean_state(backend_server):
    # Now only runs when backend_server is active
    if _backend_server:
        _backend_server.reset_state()
    yield
```

Wait — this would break unit tests that don't use `backend_server` because `clean_state` won't fire. Better approach: separate `clean_state` from `backend_server`:

```python
@pytest.fixture(scope="session")
def backend_server():
    """Opt-in fixture: backend server for integration/browser tests."""
    ...

@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before each test (only if server is running)."""
    ...
```

**Step 2: Mark unit tests**

Add `@pytest.mark.unit` to tests that don't need the server. These already exist in some files. For tests marked `unit`, the server won't start (since `backend_server` is no longer autouse).

**Step 3: Run tests**

```bash
python -m pytest tests/backend/ -v --tb=short
```

**Step 4: Commit**

```bash
git add -A
git commit -m "refactor: make server fixture opt-in, unit tests no longer wait for server"
```