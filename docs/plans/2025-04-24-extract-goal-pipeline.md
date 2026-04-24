# Refactor: Extract Modules from `backend/goal_pipeline.py`

> **For Implementers:** Use subagent-driven-development skill to execute this plan task-by-task.

**Goal:** Split the 774-line `backend/goal_pipeline.py` into focused, testable modules (≤300 lines each) using strict TDD. Preserve backward compatibility via a re-export layer so zero existing tests break during the refactor.

**Architecture:** 
- Create `backend/pipelines/` package containing one module per pipeline stage.
- Each module is independently testable, owns its own prompt strings, and exposes a single public async function.
- `backend/goal_pipeline.py` becomes a thin compatibility layer that re-exports all symbols until migration is complete.
- TDD enforces the contract: write extraction test → watch it fail → extract module → watch it pass → run full suite.

**Tech Stack:** Python 3.13, FastAPI, pytest-asyncio, Pydantic v2. No new dependencies.

---

## Background: Why This Refactor Is Needed

The `backend/goal_pipeline.py` file is **774 lines** and contains **13 functions** spanning 7 distinct domains:

| Function | Lines | Domain |
|---|---|---|
| `infer_goals` | 91 | Goal Inference |
| `merge_goals` | 117 | Goal Merging |
| `replace_outdated_goals` | 49 | Goal Merging |
| `evaluate_goal` | 52 | Goal Evaluation |
| `stream_llm_response` | 56 | LLM Streaming |
| `extract_keyphrases` | 31 | Keyphrase Extraction |
| `detect_forgetting` | 50 | Detection |
| `detect_contradiction` | 39 | Detection |
| `detect_derailment` | 44 | Detection |
| `detect_repetition` | 44 | Detection |
| `detect_fixation` | 54 | Detection |
| `detect_breakdown` | 51 | Detection |
| `compute_goal_progress` | 78 | Progress Tracking |

These are mixed with inline LLM prompts (150+ lines), shared `Goal` model imports, and a monolithic `except Exception` error-handling pattern. The file violates the project's own 300-line maximum directive and is the primary source of bugs (3 regressions in the last month, all traced to merge/evaluate interactions in this single file).

**Target structure after refactor:**

```
backend/
  goal_pipeline.py          # COMPATIBILITY LAYER — thin re-exports, ≤50 lines
  pipelines/
    __init__.py             # Re-exports for new code
    goal_inference.py       # infer_goals only (~90 lines)
    goal_merge.py           # merge_goals, replace_outdated_goals (~100 lines)
    goal_evaluation.py      # evaluate_goal only (~60 lines)
    llm_streaming.py        # stream_llm_response only (~60 lines)
    keyphrase_extraction.py # extract_keyphrases only (~35 lines)
    goal_detection.py       # 6 detect_* functions (~150 lines)
    goal_progress.py        # compute_goal_progress only (~85 lines)
```

**Test strategy:**
- Existing tests continue importing from `backend.goal_pipeline` (compatibility layer).
- New extraction tests verify the new modules directly.
- Every task follows RED → GREEN run all tests → commit.

---

## Task 0: Setup the `backend/pipelines/` Package

**Objective:** Create the package directory so subsequent tasks have a place to land extracted code.

**Files:**
- Create: `backend/pipelines/__init__.py`
- Modify: `backend/__init__.py` (if needed for package resolution)

**Step 1: Write failing test**

```python
# tests/backend/test_should_extract_goal_inference_module.py
def test_should_import_goal_inference_from_pipelines():
    from backend.pipelines.goal_inference import infer_goals
    assert callable(infer_goals)
```

**Step 2: Run test to verify failure**

```bash
.venv/bin/python -m pytest tests/backend/test_should_extract_goal_inference_module.py -v
```
Expected: **FAIL** — `ModuleNotFoundError: No module named 'backend.pipelines'`

**Step 3: Write minimal implementation**

```python
# backend/pipelines/__init__.py
# Package marker for pipeline modules.
```

```bash
mkdir -p backend/pipelines
touch backend/pipelines/__init__.py
```

**Step 4: Run test to verify pass**

```bash
.venv/bin/python -m pytest tests/backend/test_should_extract_goal_inference_module.py -v
```
Expected: **PASS**

**Step 5: Run full test suite (regression check)**

```bash
.venv/bin/python -m pytest tests/backend/ -q
```
Expected: **114 passed** (zero regressions).

**Step 6: Commit**

```bash
git add backend/pipelines/ tests/backend/test_should_extract_goal_inference_module.py
git commit -m "refactor: create backend/pipelines/ package for pipeline extraction"
```

---

## Task 1: Extract `goal_inference.py`

**Objective:** Move `infer_goals` and its prompt into a dedicated module ≤95 lines.

**Files:**
- Create: `backend/pipelines/goal_inference.py`
- Modify: `backend/goal_pipeline.py` (replace body with import)
- Test: `tests/backend/test_should_extract_goal_inference_module.py`

**Step 1: Write extraction test**

```python
# tests/backend/test_should_extract_goal_inference_module.py
import pytest
from datetime import datetime
from backend.models import Goal
from backend.pipelines.goal_inference import infer_goals

@pytest.mark.asyncio
async def test_should_infer_goals_from_new_module():
    """
    Verify infer_goals still works after extraction.
    We mock LLMService to avoid real API calls.
    """
    from unittest.mock import patch
    fake_response = '{"clauses": [{"clause": "Write a story", "type": "request", "summary": "Create a narrative"}]}'
    
    with patch('backend.pipelines.goal_inference.LLMService.generate_response', return_value=fake_response):
        goals = await infer_goals("Write a story", "msg_0")
    
    assert len(goals) == 1
    assert goals[0].text == "Write a story"
    assert goals[0].type == "request"
    assert goals[0].source_message_id == "msg_0"
```

**Step 2: Run test — verify RED**

```bash
.venv/bin/python -m pytest tests/backend/test_should_extract_goal_inference_module.py -v
```
Expected: **FAIL** — `ModuleNotFoundError: No module named 'backend.pipelines.goal_inference'`

**Step 3: Create the extracted module**

Copy the `infer_goals` function body (lines 27–91 of the original file) into the new module. The code stays **identical** — no behavior changes. Only the file location changes.

```python
# backend/pipelines/goal_inference.py
"""
Goal Inference Stage — Extract goals from natural language user messages.

Implements Appendix A.1 of the OnGoal requirements.
"""

import json
import logging
import re
from typing import List
from datetime import datetime

from dotenv import load_dotenv
from backend.models import Goal
from backend.llm_service import LLMService

load_dotenv()

logger = logging.getLogger(__name__)


async def infer_goals(message: str, message_id: str, existing_goals_count: int = 0) -> List[Goal]:
    """Extract goals from user message using exact prompt from OnGoal requirements (Appendix A.1)"""
    # ... entire existing body preserved verbatim ...
```

> **Congruency note:** Keep imports at the top. Keep the existing behavior, comments, and error-handling exactly as-is. The only change is the module path.

**Step 4: Update `goal_pipeline.py` to re-export**

```python
# backend/goal_pipeline.py — ADD at top (before existing code)
from backend.pipelines.goal_inference import infer_goals
# infer_goals now comes from the new module; remove old definition later
```

> **Important:** Do NOT delete the old `infer_goals` body yet. Add the import above it. The old body is now unreachable because the module-level name is shadowed by the import. This is the zero-risk compatibility trick.

**Step 5: Run extraction test — verify GREEN**

```bash
.venv/bin/python -m pytest tests/backend/test_should_extract_goal_inference_module.py -v
```
Expected: **PASS**

**Step 6: Run full backend suite — verify zero regressions**

```bash
.venv/bin/python -m pytest tests/backend/ -q
```
Expected: **114 passed**

**Step 7: Clean up old body in `goal_pipeline.py`**

Delete the old `infer_goals` function body (the unreachable one below the import).

**Step 8: Run full suite again**

```bash
.venv/bin/python -m pytest tests/backend/ -q
```
Expected: **114 passed**

**Step 9: Verify file lengths**

```bash
wc -l backend/pipelines/goal_inference.py backend/goal_pipeline.py
```
Expected: `goal_inference.py` ≤95 lines, `goal_pipeline.py` reduced by ~91 lines.

**Step 10: Commit**

```bash
git add backend/pipelines/goal_inference.py backend/goal_pipeline.py tests/backend/test_should_extract_goal_inference_module.py
git commit -m "refactor: extract infer_goals into backend/pipelines/goal_inference.py"
```

---

## Task 2: Extract `goal_evaluation.py`

**Objective:** Move `evaluate_goal` into its own module.

**Files:**
- Create: `backend/pipelines/goal_evaluation.py`
- Modify: `backend/goal_pipeline.py`
- Test: `tests/backend/test_should_extract_goal_evaluation_module.py`

**Step 1: Write failing test**

```python
# tests/backend/test_should_extract_goal_evaluation_module.py
import pytest
from unittest.mock import patch
from backend.models import Goal, GoalEvaluation
from backend.pipelines.goal_evaluation import evaluate_goal

@pytest.mark.asyncio
async def test_should_evaluate_goal_from_new_module():
    fake_response = '{"category": "confirm", "explanation": "Addresses the goal", "examples": ["yes"]}'
    with patch('backend.pipelines.goal_evaluation.LLMService.generate_response', return_value=fake_response):
        goal = Goal(id="G0", text="Write a story", type="request", source_message_id="msg_0")
        result = await evaluate_goal(goal, "Here is a story...")
    
    assert result["category"] == "confirm"
    assert result["goal_id"] == "G0"
```

**Step 2: Run test — verify RED**

```bash
.venv/bin/python -m pytest tests/backend/test_should_extract_goal_evaluation_module.py -v
```
Expected: **FAIL** — `ModuleNotFoundError`

**Step 3: Extract module**

Copy `evaluate_goal` (lines 265–315 of original) into `backend/pipelines/goal_evaluation.py`. Preserve verbatim.

```python
# backend/pipelines/goal_evaluation.py
"""
Goal Evaluation Stage — Assess how assistant responses address tracked goals.

Implements Appendix A.3 of the OnGoal requirements.
"""

import json
import logging
import re
from typing import Dict

from backend.models import Goal, GoalEvaluation
from backend.llm_service import LLMService

logger = logging.getLogger(__name__)


async def evaluate_goal(goal: Goal, assistant_response: str) -> Dict:
    """Evaluate how assistant response addresses a goal ... """
    # ... body preserved verbatim ...
```

**Step 4: Add re-export to `goal_pipeline.py`**

```python
from backend.pipelines.goal_evaluation import evaluate_goal
```

**Step 5: Run extraction test — GREEN**

```bash
.venv/bin/python -m pytest tests/backend/test_should_extract_goal_evaluation_module.py -v
```

**Step 6: Run full suite — no regressions**

```bash
.venv/bin/python -m pytest tests/backend/ -q
```

**Step 7: Delete old `evaluate_goal` body from `goal_pipeline.py`**

**Step 8: Full suite again — 114 passed**

**Step 9: Commit**

```bash
git add backend/pipelines/goal_evaluation.py backend/goal_pipeline.py tests/backend/test_should_extract_goal_evaluation_module.py
git commit -m "refactor: extract evaluate_goal into backend/pipelines/goal_evaluation.py"
```

---

## Task 3: Extract `llm_streaming.py`

**Objective:** Move `stream_llm_response` into its own module.

**Files:**
- Create: `backend/pipelines/llm_streaming.py`
- Modify: `backend/goal_pipeline.py`
- Test: `tests/backend/test_should_extract_llm_streaming_module.py`

**Step 1: Write failing test**

```python
# tests/backend/test_should_extract_llm_streaming_module.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.pipelines.llm_streaming import stream_llm_response

@pytest.mark.asyncio
async def test_should_stream_from_new_module():
    mock_ws = AsyncMock()
    mock_mgr = AsyncMock()
    mock_mgr.send_message = AsyncMock(return_value=True)
    
    async def fake_stream(*args, **kwargs):
        yield "Hello "
        yield "world"
    
    with patch('backend.pipelines.llm_streaming.LLMService.generate_streaming_response', fake_stream):
        result = await stream_llm_response("Hi", mock_mgr, mock_ws, "msg_1", [])
    
    assert result == "Hello world"
```

**Step 2: Run test — verify RED**

**Step 3: Extract module**

Copy `stream_llm_response` (lines 318–374 of original) into `backend/pipelines/llm_streaming.py`. Preserve verbatim.

```python
# backend/pipelines/llm_streaming.py
"""
LLM Streaming Stage — Stream assistant responses with mid-stream disconnect handling.
"""

import logging
from typing import List

from backend.llm_service import LLMService

logger = logging.getLogger(__name__)


async def stream_llm_response(message: str, connection_manager, websocket, message_id: str, conversation_messages: List):
    """Stream LLM response ... """
    # ... body preserved verbatim ...
```

**Step 4: Add re-export to `goal_pipeline.py`**

```python
from backend.pipelines.llm_streaming import stream_llm_response
```

**Step 5: Run extraction test — GREEN**

**Step 6: Run full suite — 114 passed**

**Step 7: Delete old body**

**Step 8: Full suite again**

**Step 9: Commit**

```bash
git add backend/pipelines/llm_streaming.py backend/goal_pipeline.py tests/backend/test_should_extract_llm_streaming_module.py
git commit -m "refactor: extract stream_llm_response into backend/pipelines/llm_streaming.py"
```

---

## Task 4: Extract `keyphrase_extraction.py`

**Objective:** Move `extract_keyphrases` into its own module.

**Files:**
- Create: `backend/pipelines/keyphrase_extraction.py`
- Modify: `backend/goal_pipeline.py`
- Test: `tests/backend/test_should_extract_keyphrase_module.py`

**Steps 1–9 follow the same pattern as Tasks 1–3.**

**Commit:**

```bash
git add backend/pipelines/keyphrase_extraction.py backend/goal_pipeline.py tests/backend/test_should_extract_keyphrase_module.py
git commit -m "refactor: extract extract_keyphrases into backend/pipelines/keyphrase_extraction.py"
```

---

## Task 5: Extract `goal_progress.py`

**Objective:** Move `compute_goal_progress` into its own module.

**Files:**
- Create: `backend/pipelines/goal_progress.py`
- Modify: `backend/goal_pipeline.py`
- Test: `tests/backend/test_should_extract_goal_progress_module.py`

**Step 1: Write failing test**

```python
# tests/backend/test_should_extract_goal_progress_module.py
import pytest
from backend.models import Goal, Message, Conversation
from backend.pipelines.goal_progress import compute_goal_progress
from datetime import datetime

@pytest.mark.backend
def test_should_compute_progress_from_new_module():
    conv = Conversation(id="test")
    g = Goal(id="G0", text="Write a story", type="request", source_message_id="msg_0")
    conv.goals.append(g)
    result = compute_goal_progress(conv)
    assert len(result) == 1
    assert result[0]["goal_id"] == "G0"
```

**Steps 2–9 follow the same pattern.**

**Commit:**

```bash
git add backend/pipelines/goal_progress.py backend/goal_pipeline.py tests/backend/test_should_extract_goal_progress_module.py
git commit -m "refactor: extract compute_goal_progress into backend/pipelines/goal_progress.py"
```

---

## Task 6: Extract `goal_merge.py`

**Objective:** Move `merge_goals` and `replace_outdated_goals` into a single module.

**Files:**
- Create: `backend/pipelines/goal_merge.py`
- Modify: `backend/goal_pipeline.py`
- Test: `tests/backend/test_should_extract_goal_merge_module.py`

**Step 1: Write extraction tests**

```python
# tests/backend/test_should_extract_goal_merge_module.py
import pytest
from backend.models import Goal
from backend.pipelines.goal_merge import merge_goals, replace_outdated_goals

@pytest.mark.backend
def test_should_merge_goals_from_new_module():
    from unittest.mock import patch
    fake_response = '{"operations": [{"updated_goal": "Write a good story", "operation": "combine", "goal_numbers": ["1", "1"]}]}'
    with patch('backend.pipelines.goal_merge.LLMService.generate_response', return_value=fake_response):
        old = [Goal(id="G0_old", text="Write a story", type="request", source_message_id="msg_0")]
        new = [Goal(id="G0_new", text="Write a good story", type="request", source_message_id="msg_1")]
        result = merge_goals(old, new, "msg_1")
    assert len(result) == 1
    assert "good" in result[0].text
```

**Steps 2–9 follow the same pattern.**

> **Note:** `merge_goals` and `replace_outdated_goals` are deeply coupled (one calls the other via `detect_contradiction`). Extract both into the same module so they stay together during this phase. A future refactor could separate them further, but YAGNI applies.

**Commit:**

```bash
git add backend/pipelines/goal_merge.py backend/goal_pipeline.py tests/backend/test_should_extract_goal_merge_module.py
git commit -m "refactor: extract merge_goals + replace_outdated_goals into backend/pipelines/goal_merge.py"
```

---

## Task 7: Extract `goal_detection.py`

**Objective:** Move all 6 `detect_*` functions into one module.

**Files:**
- Create: `backend/pipelines/goal_detection.py`
- Modify: `backend/goal_pipeline.py`
- Test: `tests/backend/test_should_extract_goal_detection_module.py`

**Step 1: Write extraction tests (one per function)**

```python
# tests/backend/test_should_extract_goal_detection_module.py
import pytest
from backend.models import Goal, Message
from backend.pipelines.goal_detection import (
    detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, detect_breakdown,
)

@pytest.mark.backend
async def test_should_detect_forgetting_from_new_module():
    from unittest.mock import patch
    with patch('backend.pipelines.goal_detection.LLMService.generate_response', return_value='{"forgotten_goals": []}'):
        result = await detect_forgetting([], "response")
    assert result == []

@pytest.mark.backend
async def test_should_detect_contradiction_from_new_module():
    from unittest.mock import patch
    with patch('backend.pipelines.goal_detection.LLMService.generate_response', return_value='{"contradictions": []}'):
        result = await detect_contradiction([Goal(id="G0", text="A", type="request", source_message_id="m")])
    assert result == []

# ... similar smoke tests for detect_derailment, detect_repetition, detect_fixation, detect_breakdown
```

**Steps 2–9 follow the same pattern.**

> **File length concern:** This module will be ~150 lines. Within the 300-line limit.

**Commit:**

```bash
git add backend/pipelines/goal_detection.py backend/goal_pipeline.py tests/backend/test_should_extract_goal_detection_module.py
git commit -m "refactor: extract detect_* functions into backend/pipelines/goal_detection.py"
```

---

## Task 8: Convert `goal_pipeline.py` to a Pure Re-Export Module

**Objective:** Strip `goal_pipeline.py` down to a compatibility-only module.

**Files:**
- Modify: `backend/goal_pipeline.py`

**Step 1: Read current `goal_pipeline.py`**

Confirm only `from backend.pipelines.X import Y` lines remain.

**Step 2: Clean up to ≤50 lines**

```python
"""
OnGoal Pipeline — Compatibility re-export layer.

All functions have been extracted into focused modules under backend/pipelines/.
New code should import from backend.pipelines directly; this file is preserved
for backward compatibility until all importers are migrated.
"""

from backend.pipelines.goal_inference import infer_goals
from backend.pipelines.goal_merge import merge_goals, replace_outdated_goals
from backend.pipelines.goal_evaluation import evaluate_goal
from backend.pipelines.llm_streaming import stream_llm_response
from backend.pipelines.keyphrase_extraction import extract_keyphrases
from backend.pipelines.goal_detection import (
    detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, detect_breakdown,
)
from backend.pipelines.goal_progress import compute_goal_progress
```

**Step 3: Run full backend test suite**

```bash
.venv/bin/python -m pytest tests/backend/ -q
```
Expected: **114 passed**

**Step 4: Verify file sizes**

```bash
wc -l backend/goal_pipeline.py backend/pipelines/*.py
```
Expected: every file ≤300 lines.

**Step 5: Commit**

```bash
git add backend/goal_pipeline.py
git commit -m "refactor: convert goal_pipeline.py to pure re-export compatibility layer"
```

---

## Task 9: Update `backend/pipelines/__init__.py` for Convenience

**Objective:** Let new code import from `backend.pipelines` directly.

**Files:**
- Modify: `backend/pipelines/__init__.py`

**Step 1: Write failing test**

```python
# tests/backend/test_should_import_pipelines_convenience.py
def test_should_import_all_from_pipelines_package():
    from backend.pipelines import infer_goals, merge_goals, evaluate_goal
    assert callable(infer_goals)
    assert callable(merge_goals)
    assert callable(evaluate_goal)
```

**Step 2: Implement `__init__.py`**

```python
"""OnGoal Pipeline Stages — Import convenience.

Example:
    from backend.pipelines import infer_goals, evaluate_goal
"""

from backend.pipelines.goal_inference import infer_goals
from backend.pipelines.goal_merge import merge_goals, replace_outdated_goals
from backend.pipelines.goal_evaluation import evaluate_goal
from backend.pipelines.llm_streaming import stream_llm_response
from backend.pipelines.keyphrase_extraction import extract_keyphrases
from backend.pipelines.goal_detection import (
    detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, detect_breakdown,
)
from backend.pipelines.goal_progress import compute_goal_progress
```

**Step 3: Run test — GREEN**

**Step 4: Full suite — 114 passed**

**Step 5: Commit**

```bash
git add backend/pipelines/__init__.py tests/backend/test_should_import_pipelines_convenience.py
git commit -m "refactor: add re-exports to backend/pipelines/__init__.py for convenience imports"
```

---

## Task 10: Update Import Paths in Key Callers

**Objective:** Migrate direct callers to import from `backend.pipelines` instead of the compatibility layer. This is optional but recommended to demonstrate the new pattern.

**Files:**
- Modify: `backend/websocket_handlers.py`
- Modify: `backend/api_endpoints.py`
- Modify: `tests/` imports (gradually)

**Step 1: Update `websocket_handlers.py` imports**

Old:
```python
from backend.goal_pipeline import (
    infer_goals, merge_goals, evaluate_goal, stream_llm_response,
    extract_keyphrases, detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, compute_goal_progress, detect_breakdown,
    replace_outdated_goals,
)
```

New:
```python
from backend.pipelines import (
    infer_goals, merge_goals, evaluate_goal, stream_llm_response,
    extract_keyphrases, detect_forgetting, detect_contradiction, detect_derailment,
    detect_repetition, detect_fixation, compute_goal_progress, detect_breakdown,
    replace_outdated_goals,
)
```

**Step 2: Run full suite — 114 passed**

**Step 3: Commit**

```bash
git add backend/websocket_handlers.py
git commit -m "refactor: migrate websocket_handlers to import from backend.pipelines"
```

**Step 4: Update `api_endpoints.py` imports**

Old:
```python
from backend.goal_pipeline import extract_keyphrases as _extract_keyphrases
from backend.goal_pipeline import compute_goal_progress
```

New:
```python
from backend.pipelines import extract_keyphrases as _extract_keyphrases
from backend.pipelines import compute_goal_progress
```

**Step 5: Run full suite — 114 passed**

**Step 6: Commit**

```bash
git add backend/api_endpoints.py
git commit -m "refactor: migrate api_endpoints to import from backend.pipelines"
```

---

## Task 11: Update AGENTS.md / Repo Discovery Guide

**Objective:** Document the new module structure.

**Files:**
- Modify: `.github/instructions/repo-discovery-guide.instructions.md`

**Step 1: Update the Module Map section**

Replace the old `goal_pipeline.py` entry with the new pipeline entries:

```markdown
| Goal pipeline | `backend/pipelines/` | Core goal processing: infer, merge, evaluate |
| Goal inference | `backend/pipelines/goal_inference.py` | `infer_goals()` — extract goals from user messages |
| Goal merge | `backend/pipelines/goal_merge.py` | `merge_goals()`, `replace_outdated_goals()` |
| Goal evaluation | `backend/pipelines/goal_evaluation.py` | `evaluate_goal()` |
| LLM streaming | `backend/pipelines/llm_streaming.py` | `stream_llm_response()` |
| Keyphrase extraction | `backend/pipelines/keyphrase_extraction.py` | `extract_keyphrases()` |
| Goal detection | `backend/pipelines/goal_detection.py` | `detect_forgetting()`, `detect_contradiction()`, etc. |
| Goal progress | `backend/pipelines/goal_progress.py` | `compute_goal_progress()` |
```

**Step 2: Commit**

```bash
git add .github/instructions/repo-discovery-guide.instructions.md
git commit -m "docs: update repo discovery guide with new pipeline module structure"
```

---

## Verification Checklist

At the end of this plan, confirm:

| Check | Command | Expected |
|---|---|---|
| All tests pass | `.venv/bin/python -m pytest tests/backend/ -q` | 114 passed |
| No regressions | `.venv/bin/python -m pytest tests/ -q` | All suites pass |
| File length compliance | `wc -l backend/pipelines/*.py backend/goal_pipeline.py` | Every file ≤300 lines |
| Imports work | `python -c "from backend.pipelines import *; print('OK')"` | No errors |
| Backward compatibility | `python -c "from backend.goal_pipeline import infer_goals; print('OK')"` | No errors |

---

## Rollback Plan

If at any point the full suite shows regressions:

1. **Do not panic.** The compatibility layer means `goal_pipeline.py` still works.
2. Identify the failing test(s).
3. Check if the extracted module is missing an import (e.g., `LLMService`, `Goal`, `GoalEvaluation`).
4. Check if `patch` paths in tests need updating (e.g., `patch('backend.goal_pipeline.LLMService...')` → `patch('backend.pipelines.goal_inference.LLMService...')`).
5. If stuck, revert the last commit: `git revert HEAD`.

> **Patience rule:** If a test suddenly fails and you don't know why, revert, take smaller steps, and restart the TDD cycle.

---

*Plan written using strict TDD discipline: every module comes with a failing test first, then the extraction, then a full regression suite run. The compatibility layer ensures zero downtime for existing imports.*
