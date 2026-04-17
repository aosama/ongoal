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

## Remaining

- [ ] Alerts display in frontend UI (Events tab or toast)
- [ ] D3 goal timeline/Sankey visualization
- [ ] Goal history/restore (undo merge, restore forgotten goals)
- [ ] Text highlighting in chat (keyphrase highlighting in messages)
- [ ] Individual goal view/detail panel (REQ-04-02-103)
- [ ] Repetition detection (REQ-03-02-006)
- [ ] Communication breakdown detection (REQ-03-01-007)
- [ ] Goal progress tracking across messages (REQ-03-02-001)
- [ ] Goal completion determination (REQ-03-02-004)
- [ ] Chat log navigation/filtering by goal (REQ-03-02-005)
- [ ] Responsive/mobile layout
- [ ] Persist conversation state (DB or file, not just in-memory)
- [ ] Open source polish (no debug prints, clean docs, CI)