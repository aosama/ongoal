---
applyTo: "**"
---

# Progress Tracker (agent-maintained)

**KEEP THIS FILE UPDATED after every meaningful change.** Add completed items under Done, move remaining items as they are finished, add new items as they are discovered.

## Done

- [x] LLM provider abstraction (Ollama/OpenRouter/Anthropic)
- [x] Cloud LLM migration (Ollama Cloud, retry logic, thinking-field handling)
- [x] Goal pipeline: infer, merge, evaluate, keyphrase extraction
- [x] Enhanced data models (GoalEvaluation, Goal.summary, PipelineSettings, GoalAlert)
- [x] WebSocket streaming + real-time goal pipeline events
- [x] REST API: goal CRUD, keyphrases, alerts endpoints
- [x] Frontend: clickable goal glyphs with evaluation detail expansion
- [x] Frontend: Events tab with keyphrases + goal event log
- [x] Frontend: goal type badges (GOAL_TYPES), evaluation status styles (EVAL_STYLES)
- [x] Frontend: alerts WS handler + dismiss helpers
- [x] Detection pipeline: forgetting, contradiction, derailment (backend)
- [x] 63/63 backend tests passing
- [x] Alerts display in Events tab — severity-styled cards, goal links, dismiss, toast notifications (REQ-04-02-211, REQ-03-03-001, REQ-03-01-003)
- [x] Alert REST API: GET alerts, DELETE dismiss by index, DELETE clear all, POST inject for testing
- [x] 69/69 backend tests passing (6 new alert API tests)
- [x] In-situ goal glyphs under chat messages (REQ-04-02-101/102)
- [x] Glyph click → inline explanation panel (REQ-04-02-103/104)
- [x] Text highlighting: evaluation examples inline in LLM responses when glyph panel open (REQ-04-03-001)
- [x] Keyphrase highlighting mode toggle in Events tab (REQ-04-03-004)
- [x] Shared vs unique keyphrase visual distinction with legend (REQ-04-03-005)
- [x] Evaluation-to-assistant message mapping on conversation_state reload
- [x] Individual goal view: click goal → filtered chat + evaluations list sidebar (REQ-04-02-301–305)
- [x] Default evaluation highlighting in individual goal view (REQ-04-03-003)
- [x] Evaluation click → scroll to corresponding LLM response (REQ-04-02-304)
- [x] D3 Sankey-style timeline visualization with infer/merge/evaluate rows + connecting paths (REQ-04-02-206–209)
- [x] Goal mutation history tracking + restore UI (REQ-04-02-205)
- [x] Goal history REST API: GET history, POST restore
- [x] Repetition detection: LLM-based comparison of recent assistant responses, alert with suggestions (REQ-03-02-006)
- [x] Goal fixation detection: detect fixated vs neglected goals via LLM analysis, alert with suggestions (REQ-03-03-002)
- [x] Goal progress tracking across messages: confirm/ignore/contradict counts, progress percentage, status labels (REQ-03-02-001)
- [x] Goal completion determination: auto-classify as likely_complete/progressing/at_risk/contradicted/active (REQ-03-02-004)
- [x] Goal progress REST API: GET /api/conversations/{id}/goal-progress
- [x] Goal progress progress bar in goal cards with status badge + evaluation counts
- [x] Goal progress WS event (goal_progress_updated) after each turn
- [x] Repetition + fixation alert types with icons (🔄/🎯) in Events tab
- [x] 85/85 backend tests passing (16 new: 13 advanced detection + 3 progress API)
- [x] Communication breakdown detection: detect user rephrasing same unmet goal, alert with suggestions (REQ-03-01-007)
- [x] Chat log navigation/filtering by goal: message count per goal card (📨 badge), individual view shows evaluations + message count (REQ-03-02-005)
- [x] Similar/unique sentence highlighting modes: LLM-based sentence comparison, purple=violet similar + cyan=unique highlights in chat (REQ-04-03-006/007)
- [x] Sentence similarity REST API: GET /api/conversations/{id}/sentence-similarity
- [x] Breakdown alert icon (💬) in Events tab
- [x] 91/91 backend tests passing (6 new: 3 breakdown detection + 2 sentence similarity API + 1 progress)
- [x] Open source polish: verbose comments cleaned, CORS configurable via env, no debug prints, no TODOs
- [x] Regression: fixed merged goals inheriting wrong source_message_id (goals shown under wrong user message)
- [x] Regression: fixed eval example highlighting breaking markdown heading syntax (orphaned ###)
- [x] 94/94 backend tests passing (3 new regression tests)

## Remaining

- [ ] Persist conversation state (DB or file, not just in-memory) — user prefers in-memory only
- [ ] Open source polish (no debug prints, clean docs, CI) — mostly done; CI not configured