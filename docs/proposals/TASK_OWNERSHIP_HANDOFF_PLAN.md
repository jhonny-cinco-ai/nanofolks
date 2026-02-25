# Task Ownership + Handoff Plan (Python)

**Purpose**: Make task responsibility explicit across the multi‑bot system and enable clean handoffs between bots.

**Why**: Clear ownership improves coordination, makes task status visible in CLI, and prepares the system for dashboards and Go parity.

---

## Current Architecture (What Exists)

**Room Tasks (user‑visible, room‑scoped)**
- Model: `RoomTask` in `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/models/room.py`
- Stored in `Room.tasks` with fields: `id`, `title`, `owner`, `status`, `priority`, `due_date`, `metadata`.
- Room APIs: `add_task`, `assign_task`, `update_task_status`, `list_tasks`.
- Already used by CLI task commands (room tasks).

**Coordinator Tasks (internal, system health)**
- `BotCoordinator` in `/Users/rickovelar/Desktop/WORK/AI_Experiments/nanofolks-project/nanofolks/nanofolks/bots/coordinator.py`
- Tracks internal bot work with team routines timeouts.
- Not user‑visible, not tied to room task ownership.

**Gap**
- There is no explicit handoff tracking between bots for room tasks.
- Ownership changes are allowed, but no recorded “handoff event.”
- Bot assignment (Leader invoking a bot) does not always create a room task record.

---

## Goals
1. Every task has a single clear owner (user or bot).
2. Ownership changes are recorded as handoffs (who -> who, why, when).
3. Leader assignment creates a room task automatically (1 task per bot assignment, with optional subtasks).
4. CLI can show tasks by owner, status, and handoff history.

---

## Proposed Model Additions

### 1) Handoff Tracking
Add `handoffs` to `RoomTask.metadata`:

```
{
  "handoffs": [
    {
      "from": "leader",
      "to": "researcher",
      "reason": "Need competitor data",
      "timestamp": "2026-02-24T18:00:00Z"
    }
  ]
}
```

### 2) Ownership Policy
- Owner can mark task as done.
- Owner can request transfer (handoff) to another bot.
- Leader can reassign any task.

---

## Implementation Phases

### Phase 1: Core Model + Storage
- Extend `RoomTask` with helper methods:
  - `add_handoff(from_bot, to_bot, reason)`
  - `set_owner(new_owner, reason)` (records handoff)
- Ensure serialization includes `handoffs` in metadata.

### Phase 2: Room APIs
- Add room methods:
  - `handoff_task(task_id, new_owner, reason, from_owner)`
  - `list_tasks(owner=..., status=...)`

### Phase 3: Leader Assignments -> Task Creation
- When Leader assigns a bot, create a `RoomTask` automatically with:
  - `owner = assigned bot`
  - `status = todo`
  - `metadata.subtasks = [...]`

### Phase 4: CLI Commands
- Extend CLI tasks:
  - `tasks list` (filter by owner/status)
  - `tasks handoff <id> --to <bot> --reason "..."`
  - `tasks history <id>` (handoff history)

### Phase 5: AI Tooling (Optional)
- Add tool functions for bots to:
  - create tasks
  - handoff tasks
  - mark complete
  - list by owner/status

---

## Success Criteria
- Every bot assignment creates a task with a clear owner.
- Handoff history is visible via CLI.
- Task status is reliable and auditable per room.
- Works without changing the internal coordinator tasks (separate concern).

