# Unified Orchestrator Pipeline Plan (Python)

**Purpose**: Replace distributed routing logic with a single, explicit pipeline: tag -> intent -> dispatch -> collect -> final response.

**Goal**: Keep the multi-bot, communal spirit while making the orchestration consistent, observable, and easier to port to Go.

---

## Current Baseline (Today)
- Tag parsing is regex-based (bots + legacy #workspace + action keywords).
- Intent detection is hardcoded phrase matching (no LLM fallback).
- Dispatch/synthesis is distributed across router, flow handlers, and Leader behavior.

---

## Scope (This Plan)
- Python-only implementation (no migration needed).
- Keep team identity, roles, and collaboration intact.
- Produce a single, clear orchestration path for all channels.

---

## Proposed Pipeline

1) Tag
- Keep regex tagging for @bot and action keywords.
- Remove legacy #workspace tags (rooms are the canonical unit now).

2) Intent
- Hybrid intent detection:
  - Rule-based match first.
  - LLM fallback when confidence is low or ambiguous.
- Optional: allow multi-intent for compound requests.

3) Dispatch
- System decides which bots to involve, based on roles + tags + intent.
- Leader remains central but is invoked within the pipeline (not the orchestrator itself).

4) Collect Replies
- Wait for all assigned bots (with timeout).
- Ensure a standard response envelope for all bots.

5) Final Response
- Synthesis step (Leader or system) produces one user-facing response.

---

## Phased Implementation (Suggested Order)

### Phase 1: Cleanup + Tag Simplification
- Remove #workspace tag parsing and related fields.
- Update docs to reflect rooms as the only routing unit.

### Phase 2: Hybrid Intent
- Add confidence thresholds in IntentDetector.
- When confidence is low, call LLM for intent classification.
- Keep rule-based as default for speed.

### Phase 3: Orchestrator Spine
- Introduce a single orchestrator function (or class) that runs:
  tag -> intent -> dispatch -> collect -> final.
- Route all messages through this path (CLI + channels).

### Phase 4: Observability
- Log tag, intent, dispatch, and synthesis decisions.
- Add lightweight tracing fields to MessageEnvelope metadata.

### Phase 5: Tests
- Unit tests for tag parsing (no workspace tags).
- Intent classification tests (rule-only + LLM fallback stub).
- Integration tests for multi-bot flow consistency.

---

## Affected Areas
- /Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/systems/tag_handler.py
- /Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/agent/intent_detector.py
- /Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/agent/intent_flow_router.py
- /Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/bots/dispatch.py
- /Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/bus/events.py

---

## Success Criteria
- All channels follow one consistent orchestration path.
- Tags + intent decisions are visible in logs.
- Multi-bot flows are predictable and reproducible.
- Leader remains a collaborative bot, not hidden orchestration logic.

