---
applyTo: "**"
---

# Repo Discovery Guide (agent-only)

This document is an internal discovery + maintenance index for coding agents working in `ongoal`. It is not user-facing documentation.

Use this file like a cache.

- Prefer updating it when you discover drift (paths, scripts, test behavior), rather than keeping it perfectly current.
- Treat the "Last verified" timestamp as the main trust signal; if you only reformat or reorganize text, do not update it.

## Table of Contents

- Maintenance snapshot
- 1. High-signal docs (read-first index)
- 2. Architecture overview
- 3. Module map (ownership + boundaries)
- 4. Runtime entry points
- 5. High-signal code anchors
- 6. LLM provider system
- 7. Testing
- 8. Requirements and research docs
- 9. When to update this file

## Maintenance snapshot

- Last verified: 2026-04-17
- Verification scope: runtime scripts, backend/frontend startup, LLM provider abstraction layer (Ollama Cloud REST API / OpenRouter / Anthropic), goal pipeline (infer/merge/evaluate/keyphrase/detection), advanced detection (repetition/fixation/breakdown/progress), WebSocket + REST API surface (including goal-progress, sentence-similarity, goal-history), frontend goal detail panel + Events tab + keyphrase display + sentence highlighting modes, test suite (114/114 passing), conftest server fixtures, pytest.ini configuration.

## 1. High-signal docs (read-first index)

- Research paper inspiration: https://arxiv.org/abs/2508.21061
- Environment config template: `.env.example`
- TDD requirements: `docs/requirements/tdd-requirements/`
- Core system TDD spec: `docs/requirements/tdd-requirements/04-ongoal-system.md`
- LLM prompt templates (Appendix A.1/A.2/A.3): `docs/requirements/tdd-requirements/09-llm-prompts.md`
- Agent gate: `.github/instructions/congruency.instructions.md`

## 2. Architecture overview

```
Frontend (Vue.js 3 SPA)             Backend (FastAPI)
┌──────────────┐  WS + REST        ┌────────────────────┐
│ index.html    │◄─────────────────►│ main.py (app)       │
│ app.js        │  ws://:8000/ws    │  ├─ api_endpoints   │
│               │  http://:8000/api │  ├─ websocket_      │
└──────────────┘                    │  │  handlers         │
CDN: Vue 3, D3, Tailwind           │  ├─ connection_      │
Port: 8080                          │  │  manager          │
                                    │  ├─ models           │
                                    │  ├─ goal_pipeline    │
                                    │  ├─ llm_service      │
                                    │  └─ llm_provider     │
                                    │     (Ollama│OR│Claude)
                                    └────────────────────┘
                                    Port: 8000
```

Key architectural facts:

- **No database** — all state in in-memory `conversations` dict in `api_endpoints.py`; resets on server restart.
- **No build step** — frontend uses CDN-loaded Vue 3; Python `http.server` serves static files.
- **No Docker/CI** — no containerization or GitHub Actions configured.
- **Real-time** — WebSocket for streaming LLM responses + goal pipeline events; REST for goal CRUD.
- **Goal pipeline**: 3 LLM calls per conversation turn: infer → merge → evaluate. This is the main latency and cost driver.

## 3. Module map (ownership + boundaries)

| Module | Path | Responsibility |
|---|---|---|
| Backend app | `backend/main.py` | FastAPI app, CORS, WebSocket endpoints, uvicorn startup |
| Models | `backend/models.py` | Pydantic v2 models: `Goal`, `GoalEvaluation`, `Message`, `Conversation`, `PipelineSettings`, `GoalHistoryEntry` |
| REST API | `backend/api_endpoints.py` | All REST routes, in-memory conversations store, keyphrase/goal-progress/sentence-similarity endpoints |
| WebSocket | `backend/websocket_handlers.py` | WS message dispatch, pipeline orchestration, keyphrase + detection after response |
| Connections | `backend/connection_manager.py` | WS connection lifecycle (connect/disconnect/send) |
| Goal pipeline (compat) | `backend/goal_pipeline.py` | Compatibility re-exports; new code should import from `backend/pipelines/` |
| Inference | `backend/pipelines/goal_inference.py` | `infer_goals()` — extract goals from messages (Appendix A.1) |
| Merge | `backend/pipelines/goal_merge.py` | `merge_goals()`, `replace_outdated_goals()` — combine/refine goals (Appendix A.2) |
| Evaluation | `backend/pipelines/goal_evaluation.py` | `evaluate_goal()` — assess goal handling in responses (Appendix A.3) |
| LLM streaming | `backend/pipelines/llm_streaming.py` | `stream_llm_response()` — stream responses with mid-stream disconnect handling |
| Keyphrases | `backend/pipelines/keyphrase_extraction.py` | `extract_keyphrases()` — salient phrase extraction (Appendix A.4) |
| Detection | `backend/pipelines/goal_detection.py` | `detect_forgetting()`, `detect_contradiction()`, `detect_derailment()`, `detect_repetition()`, `detect_fixation()`, `detect_breakdown()` |
| Progress | `backend/pipelines/goal_progress.py` | `compute_goal_progress()` — cross-message tracking + completion classification |
| LLM service | `backend/llm_service.py` | Static-method façade delegating to active provider |
| LLM providers | `backend/llm_provider.py` | Abstract `LLMProvider` + Ollama/OpenRouter/Anthropic implementations, retry logic, cloud detection |
| Frontend HTML | `frontend/index.html` | SPA shell, Tailwind CSS, goal detail panel, Events tab with keyphrases + sentence modes |
| Frontend logic | `frontend/app.js` | Vue 3 Composition API: WebSocket + REST, goal selection, keyphrase/sentence display, evaluation detail, progress bars |

## 4. Runtime entry points

### Quick start

```bash
# Setup
./setup_env.sh                # Creates .venv, installs requirements

# Run both servers
./launch_ongoal.sh            # Starts backend (:8000) + frontend (:8080)

# Or run individually
.venv/bin/python run_backend.py    # uvicorn with hot-reload on :8000
.venv/bin/python run_frontend.py   # Python http.server on :8080
```

### Ports

| Service | Port | URL |
|---|---|---|
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| Frontend (static) | 8080 | http://localhost:8080 |
| WebSocket | 8000 | ws://localhost:8000/ws |

### Helper scripts

| Script | Purpose |
|---|---|
| `launch_ongoal.sh` | Master launcher — starts both servers, traps Ctrl+C |
| `setup_env.sh` | Creates `.venv/`, installs `requirements.txt` |
| `activatevirtualenv.sh` | Sources `.venv/bin/activate` |
| `reinstalldeps.sh` | Pip-freeze → uninstall all → reinstall from requirements |
| `run_backend.py` | Dev backend runner with `.env` validation |
| `run_frontend.py` | Dev frontend server with no-cache headers |
| `test_runner.py` | Unified test runner (unit/backend/browser/integration/smoke) |

### Prerequisites

- Python 3.13+
- Ollama Cloud API key (default): get one from [ollama.com/settings/api-keys](https://ollama.com/settings/api-keys)
- Default model: `gemma4:31b-cloud` (configurable via `OLLAMA_CLOUD_MODEL` in `.env`)
- Cloud models run on Ollama's servers — no local GPU needed
- If using the **local Ollama daemon** (`LLM_PROVIDER=ollama`), install Ollama locally and pull the model instead

## 5. High-signal code anchors

Fastest places to start reading when diagnosing runtime behavior:

- App bootstrap + WebSocket routes: `backend/main.py`
- All REST endpoints + conversations store: `backend/api_endpoints.py`
- Goal pipeline stages (infer/merge/evaluate/stream/detect/progress): `backend/pipelines/`
- LLM provider factory + implementations: `backend/llm_provider.py`
- LLM service façade: `backend/llm_service.py`
- Data models: `backend/models.py`
- WebSocket dispatch: `backend/websocket_handlers.py`
- Frontend state + WS/REST calls: `frontend/app.js`
- Frontend markup + styles: `frontend/index.html`

## 6. LLM provider system

Configuration via `.env`:

```
LLM_PROVIDER=ollama_cloud                   # ollama_cloud (REST API), openrouter, anthropic, ollama (local daemon)
OLLAMA_CLOUD_BASE_URL=https://ollama.com/v1   # Ollama Cloud REST endpoint
OLLAMA_CLOUD_API_KEY=                         # From https://ollama.com/settings/api-keys
OLLAMA_CLOUD_MODEL=gemma4:31b-cloud           # Browse models at https://ollama.com/models
OLLAMA_MAX_RETRIES=3                          # retry transient failures (429, 500, 502, 503, 504)
OLLAMA_RETRY_DELAY_MS=1000                    # initial backoff delay, doubles each retry
OPENROUTER_API_KEY=                           # For openrouter
OPENROUTER_MODEL=google/gemma-2-9b-it:free
ANTHROPIC_API_KEY=                            # For anthropic
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

**Ollama Cloud REST API** (default) calls Ollama's hosted API directly using a Bearer API key. This is the recommended provider for stable demos. Requires an API key from [ollama.com/settings/api-keys](https://ollama.com/settings/api-keys). Browse available models at [ollama.com/models](https://ollama.com/models).

Provider registry in `backend/llm_provider.py`:

- `get_provider()` — cached factory, reads `LLM_PROVIDER` env var
- `reset_provider()` — clears cache, useful for testing or config changes
- Each provider implements `generate()`, `generate_stream()`, `is_available()`, `get_status()`
- Ollama creates a fresh `httpx.AsyncClient` per request (avoids "Event loop is closed" in tests)
- Cloud "thinking" models (minimax-m2.7, qwen3.5) emit a `thinking` field before `content`; generate() falls back to thinking when content is empty
- Status endpoint: `GET /api/llm-status` returns provider name, model, availability, cost tier

## 7. Testing

### Test structure

```
tests/
├── conftest.py              # Session-scoped server fixtures
├── backend/                 # 12 backend test files
├── browser/                 # 6 Playwright browser test files
└── utils/                   # llm_assertion_helpers.py, timing_utils.py
```

### Running tests

```bash
# All backend tests
.venv/bin/python -m pytest tests/backend/ -v

# Unit tests only (no LLM calls)
.venv/bin/python -m pytest tests/backend/test_should_validate_goal_data_models.py tests/backend/test_should_handle_service_errors_gracefully.py -v

# Via test runner
.venv/bin/python test_runner.py --category backend
```

### Test markers

Defined in `pytest.ini`: `unit`, `backend`, `browser`, `integration`, `asyncio`, `slow`.

### Conftest fixtures

- `backend_server` — session-scoped, autouse; starts uvicorn on :8000, waits for `/api/health`
- `frontend_server` — session-scoped; Python http.server on dynamic port (8080+)
- `clean_state` — per-test, autouse; resets conversation state via REST
- `--visible` — custom CLI flag for headed Playwright testing

### LLM assertion helpers

`tests/utils/llm_assertion_helpers.py` — uses the configured LLM provider for semantic assertions instead of exact string matching. Access via `get_llm_assert()`. Includes JSON repair for truncated model output.

### Known test flakiness

- Tests that call `infer_goals()` / `merge_goals()` depend on LLM quality — local models may not always produce parseable JSON or merge correctly.
- WebSocket tests require the backend server (auto-started by conftest).
- Browser tests require Playwright Chromium: `.venv/bin/python -m playwright install --with-deps chromium`

## 8. Requirements and research docs

Located in `docs/requirements/`:

- `tdd-requirements/` — 10 numbered TDD spec files (00–09), derived from the research paper
- `whitepapersections/` — Raw whitepaper section drafts (00–09 subdirs)
- `full-whitepaper/` — Complete whitepaper text
- `ux-images/` — UI mockup screenshots

Key TDD specs:

- `04-ongoal-system.md` — Core pipeline, infer, merge, evaluate requirements
- `03-design-challenges.md` — 35+ advanced requirements (forgetting detection, contradiction, derailment) — mostly not yet implemented
- `09-llm-prompts.md` — LLM prompt templates from Appendix A.1/A.2/A.3

## 9. When to update this file

- If startup scripts, ports, or server behavior changes, update the runtime entry points section.
- If LLM provider configuration or providers change, update the LLM provider system section.
- If test structure or conftest behavior changes, update the testing section.
- If module ownership/boundaries change, update the module map and the anchor paths.
