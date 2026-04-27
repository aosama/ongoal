# Repo Discovery Guide — OnGoal

> Agent-internal orientation map. Not user-facing documentation. Read this before exploring the codebase.

## Maintenance Mandate

1. **Before every commit**, ask: did I change anything this guide documents? If yes, update the guide in the same commit.
2. **At session start**, spot-check 2-3 key facts against the actual codebase (paths, versions, script names). If anything drifted, update immediately.
3. **Quarterly minimum**, re-verify if the repo hasn't been touched. Stale guidance is worse than no guidance.

- Last verified: 2026-04-26
- Changes since last verify: structural complexity reduction — deleted llm_service.py and goal_pipeline.py, added llm_caller.py, pipeline_orchestrator.py, sentence_similarity.py; extracted pipeline logic from websocket_handlers.py and api_endpoints.py

## Project Overview

OnGoal is a conversational AI goal-tracking system inspired by the research paper ["OnGoal: A Modular Multi-Modal UI for Goal Awareness in Conversational AI"](https://arxiv.org/abs/2508.21061). It extracts, merges, and evaluates goals from multi-turn LLM conversations in real-time via WebSocket. The single most important architectural fact: **the entire goal pipeline (infer → merge → evaluate → detect alerts) runs synchronously inside the WebSocket handler with per-conversation async locks, and all state is in-memory with no database**. This means: (1) state resets on server restart, (2) concurrent WebSocket + REST access is safe via `ConversationRepository.with_lock()`, and (3) tests must reset conversation state between runs.

## Known Gotchas

- **`backend/goal_pipeline.py` and `backend/llm_service.py` NO LONGER EXIST.** All pipeline logic lives in `backend/pipelines/`; all LLM access goes through `backend/llm_provider.py` (module-level functions) or `backend/llm_caller.py` (`call_llm_json`). Do not import from either deleted file.
- **`conversation_repository` in `api_endpoints.py` is the same singleton instance** used by `websocket_handlers.py` and `pipeline_orchestrator.py`. They share state implicitly. Do not create a second `ConversationRepository` anywhere.
- **Browser tests require both backend AND frontend servers.** The `conftest.py` `backend_url` fixture depends on `backend_server` (opt-in, not autouse). Unit tests don't start the server.
- **Test naming convention: all test files/functions start with `should`.** e.g. `test_should_provide_goal_crud_operations.py`.
- **`api_endpoints.py` exceeds the 300-line file limit** (466 lines). This is a known deviation.
- **`llm_provider.py` is the largest file** (519 lines) and also exceeds the 300-line limit.
- **The `_active_provider` global in `llm_provider.py` is cached.** Tests must call `reset_provider()` to pick up env var changes, or they'll reuse a stale provider instance.
- **Ollama cloud model names ending in `:cloud` or `-cloud`** are auto-detected and routed differently by the `OllamaProvider`. This suffix convention is not documented anywhere except in code comments.
- **`call_llm_json()` in `llm_caller.py` swallows LLM exceptions** and returns `None` with a logger warning. Pipeline callers handle the `None` fallback — do not add try/except around it.
- **Pipeline modules use `import backend.llm_provider as llm_provider`** (module pattern) instead of `from ... import function`. This is intentional so that test monkeypatches on `backend.llm_provider.get_provider` work correctly.
- **`run_backend.py:36` does `from main import app`** instead of `from backend.main import app` — pre-existing bug, not yet fixed.

## Conventions

- **Python 3.13+** required (3.11+ supported)
- **Always activate `.venv`** before running any code: `source .venv/bin/activate`
- **TDD required**: write tests first, then implementation. All test names start with "should"
- **Max 300 lines per file** (some files currently exceed this — known deviation)
- **No comments in code** unless explicitly asked (per AGENTS.md instructions)
- **No debug prints** — replace with comments if context needed
- **LLM provider configured via `.env`**: default is `ollama_cloud`. Never hardcode API keys.
- **Pydantic models** in `backend/models.py` are the single source of truth for data shapes
- **REST API uses snake_case** on the wire (per Python instructions — no camelCase aliases)
- **WebSocket message types**: `user_message`, `toggle_pipeline`, `get_conversation` (incoming); `goals_inferred`, `goals_updated`, `goals_evaluated`, `keyphrases_extracted`, `alerts_detected`, `goal_progress_updated`, `pipeline_toggled`, `conversation_state` (outgoing)

## Structure Map

```
ongoal/
├── backend/                    # FastAPI backend (Python)
│   ├── main.py                  # App entrypoint, CORS, WebSocket endpoints
│   ├── api_endpoints.py          # REST API routes + shared conversation_repository singleton (466 lines, exceeds 300 limit)
│   ├── websocket_handlers.py     # WebSocket message handling — delegates to pipeline_orchestrator (~89 lines)
│   ├── pipeline_orchestrator.py  # Goal pipeline orchestration — extracted from websocket_handlers (~243 lines)
│   ├── connection_manager.py     # WebSocket connection tracking
│   ├── models.py                 # Pydantic data models (Goal, Message, Conversation, etc.)
│   ├── repository.py             # In-memory ConversationRepository with async locks
│   ├── llm_provider.py           # Multi-provider LLM abstraction + module-level convenience functions (519 lines, exceeds 300 limit)
│   ├── llm_caller.py             # Shared call_llm_json() helper for all pipeline modules (~29 lines)
│   ├── json_parser.py            # Robust JSON extraction from LLM responses
│   └── pipelines/                # Core goal processing modules
│       ├── goal_inference.py     # Extract goals from user messages
│       ├── goal_merge.py         # Merge new + existing goals, replace outdated
│       ├── goal_evaluation.py    # Evaluate LLM response against goals
│       ├── goal_detection.py     # Alert detection (forgetting, contradiction, derailment, etc.) with _detect_flag base
│       ├── goal_progress.py      # Cross-message progress tracking
│       ├── keyphrase_extraction.py  # Keyphrase extraction from responses
│       ├── sentence_similarity.py   # Sentence similarity — extracted from api_endpoints
│       └── llm_streaming.py      # Streaming LLM response generation
├── frontend/                   # Vue.js 3 + D3.js + Tailwind CSS
│   ├── index.html              # Main UI structure
│   └── app.js                  # Goal visualization + WebSocket client
├── tests/
│   ├── conftest.py             # Session-scoped server fixtures (opt-in, not autouse), test isolation
│   ├── backend/                # Backend test files
│   ├── browser/                # Browser test files (Playwright)
│   └── utils/                  # LLM assertion helpers, timing utils
├── docs/
│   ├── plans/                  # Implementation plans (incl. structural-complexity-reduction)
│   └── requirements/           # TDD requirements, whitepaper sections, UX images
├── launch_ongoal.sh            # One-command launcher (backend + frontend)
├── run_backend.py              # Backend runner script
├── run_frontend.py             # Frontend static file server
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest config with markers
├── .env.example                # Environment variable template
└── AGENTS.md                   # Agent working instructions
```

## Entry Points

### Run the app
```bash
./launch_ongoal.sh              # Starts backend (port 8000) + frontend (port 8080)
# Or manually:
source .venv/bin/activate
python -m backend.main          # Backend on :8000
python run_frontend.py          # Frontend on :8080
```

### Run tests
```bash
source .venv/bin/activate
python test_runner.py backend   # Backend tests
python test_runner.py browser   # Browser tests (needs both servers)
python test_runner.py all       # Everything
# Or directly:
python -m pytest tests/backend/ -v          # Backend only
python -m pytest tests/backend/ -m "unit" -v  # Unit tests only
python -m pytest tests/browser/ -v         # Browser tests (conftest starts servers)
python -m pytest tests/browser/ --visible  # Visible browser (for debugging)
```

### Linting
No dedicated lint command is configured. Run `python -m pytest` to validate via tests.

## What to Verify

1. **Versions** — Python 3.13+, check `.venv/bin/python --version`
2. **Paths** — `backend/pipelines/` has 8 modules (incl. `sentence_similarity.py`, `llm_streaming.py`); `goal_pipeline.py` and `llm_service.py` do NOT exist; `pipeline_orchestrator.py` and `llm_caller.py` exist at `backend/` level
3. **Scripts** — `launch_ongoal.sh`, `test_runner.py` still work
4. **Config values** — `.env` LLM_PROVIDER default is `ollama_cloud`; ports 8000/8080
5. **Known exceptions** — `api_endpoints.py` (466 lines) and `llm_provider.py` (519 lines) still exceed 300-line limit
6. **Content structure** — `docs/requirements/` has `tdd-requirements/` and `full-whitepaper/`
7. **Dead ends** — `screenshots/` at root contains README images; `test.txt` at root appears to be a scratch file