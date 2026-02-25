# Turbo Memory Completion Plan (Python)

**Goal**: Complete the current Turbo memory architecture so it’s functionally complete and easier to port to Go later.

---

## Phase A — Complete Core Memory Design (High ROI)

### A0) Align Schema + Models (Prerequisite)
**Why**: Store and graph logic still reference old edge/fact fields (e.g., `object_value`, `evidence_count`), so persistence is inconsistent.

**Plan**:
- Align `TurboMemoryStore` edge/fact CRUD with current table schema.
- Update `KnowledgeGraphManager` to use current Edge/Fact fields.
- Fix extraction to use `valid_from` instead of non-existent `created_at`.

**Touchpoints**:
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/store.py`
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/graph.py`
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/extraction.py`

### A1) Persist Edges + Facts from Extraction
**Why**: Knowledge graph is mostly empty; edges/facts are not stored.

**Current gap**:
- `BackgroundProcessor._extract_pending_events` extracts entities but skips edges/facts.

**Plan**:
- Persist edges in `TurboMemoryStore` (`edges` table).
- Persist facts in `TurboMemoryStore` (`facts` table).
- Add or complete helper methods on the store if needed.
- Update staleness counters for summaries when edges/facts added.

**Touchpoints**:
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/background.py`
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/store.py`
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/models.py`

---

### A2) Task Events into Memory
**Why**: Room tasks are important, but memory doesn’t see them unless a bot mentions them.

**Plan**:
- On task create/update/handoff, write a memory event.
- Include room_id + task metadata.

**Touchpoints**:
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/models/room.py`
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/store.py`

---

## Phase B — Improve Context Quality (Medium ROI)

### B1) Relevance Scoring in Context Assembly
**Why**: ContextAssembler uses fixed top-N selections, not relevance scoring.

**Plan**:
- Score summaries and events by relevance (semantic + recency + frequency).
- Select items that fit token budget based on score.

**Touchpoints**:
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/context.py`
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/retrieval.py`

---

### B2) Align Naming: channel -> room
**Why**: Summary tree uses channel naming even though rooms are the real unit.

**Plan**:
- Rename summary nodes to `room:*`.
- Keep backward compatibility by reading old `channel:*` nodes if present.

**Touchpoints**:
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/summaries.py`
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/context.py`

---

## Phase C — Safety + Performance

### C1) Index Integrity / Rebuild Hook
**Why**: HNSW index can drift or get corrupted.

**Plan**:
- Add a method to rebuild the index from events in SQLite.
- Expose a CLI maintenance command (optional).

**Touchpoints**:
- `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/memory/vector_index.py`

---

## Success Criteria
- Entities, facts, and edges all persist correctly.
- Task events are reflected in memory (room-aware).
- Context assembly is relevance‑aware.
- Summary naming is room‑centric.
- Memory index can be rebuilt if needed.
