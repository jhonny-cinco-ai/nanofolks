# Multi-Agent Orchestration Analysis

**Date:** February 12, 2026  
**Project:** nanobot-turbo  
**Status:** Current capabilities analysis + enhancement roadmap

---

## Executive Summary

**Current State:** nanobot has **basic multi-agent support** via the Subagent/Spawn system, but it's designed for **background task execution** rather than true multi-agent orchestration.

**What's Working:**
- ✅ Spawn tool for background subagents
- ✅ Async task execution
- ✅ Message bus for agent communication
- ✅ Tool isolation (subagents get subset of tools)

**What's Missing:**
- ❌ Agent-to-agent artifact handoffs (structured data)
- ❌ Workflow orchestration (chaining, dependencies)
- ❌ Parallel agent execution coordination
- ❌ Agent specialization roles
- ❌ Work logs as consumable artifacts

---

## Current Multi-Agent Implementation

### 1. Subagent System (`nanobot/agent/subagent.py`)

**Purpose:** Background task execution

**How it works:**
```python
# Main agent spawns subagent
spawn_tool.execute(
    task="Analyze these 50 bookmarks and categorize them",
    label="Bookmark analysis"
)

# Subagent runs in background with:
# - Same LLM provider
# - Limited tools (no spawn, no message)
# - Focused system prompt
# - Isolated context

# Result announced via message bus
```

**Current Architecture:**
```
┌─────────────────┐
│   Main Agent    │
│   (full tools)  │
└────────┬────────┘
         │ spawn
         │
    ┌────▼────┐      ┌──────────────┐
    │Subagent │ ───▶ │  Message Bus │ ───▶ (announces result)
    │(limited │      └──────────────┘
    │ tools)  │
    └─────────┘
```

**Tools Available to Subagents:**
- ReadFileTool, WriteFileTool, ListDirTool
- ExecTool (with config)
- WebSearchTool, WebFetchTool (if API key provided)

**NOT Available to Subagents:**
- SpawnTool (can't spawn sub-subagents)
- MessageTool (can't send messages directly)
- CronTool

**Communication Method:**
```python
# Subagent announces via message bus
self.bus.publish(InboundMessage(
    channel=origin["channel"],
    chat_id=origin["chat_id"],
    text=result_text,
    sender_id="subagent",
))
```

**Result Format:**
```
"I've analyzed your bookmarks and found 12 in the AI category, 
8 in productivity, and 5 uncategorized. The most common theme 
is machine learning tutorials."
```

**Problem:** This is natural language! Next agent must parse text to extract data.

---

### 2. Spawn Tool (`nanobot/agent/tools/spawn.py`)

**Current Implementation:**
```python
class SpawnTool(Tool):
    async def execute(self, task: str, label: str | None = None) -> str:
        return await self._manager.spawn(
            task=task,
            label=label,
            origin_channel=self._origin_channel,
            origin_chat_id=self._origin_chat_id,
        )
```

**Usage in Skills:**
```markdown
## Complex Analysis
For large datasets, spawn a subagent:
```spawn
{"task": "Analyze 1000 bookmarks for patterns", "label": "Pattern analysis"}
```

The subagent will report back when complete.
```

---

### 3. Message Bus (`nanobot/bus/events.py`, `nanobot/bus/queue.py`)

**Current Capabilities:**
- Async message passing
- Channel-based routing
- Event-driven architecture

**Agent Communication:**
```python
# Agent A publishes
bus.publish(InboundMessage(
    channel="cli",
    chat_id="main",
    text="Analysis complete: 15% bounce rate",
    sender_id="subagent-1",
))

# Agent B subscribes (main agent loop)
msg = await bus.get_message()
```

**Limitation:** All communication is text-based through the bus.

---

## What's Missing for True Multi-Agent Orchestration

### 1. Artifact Handoffs ❌

**Current:**
```
Agent A → Text → Agent B (must parse)
```

**Needed:**
```
Agent A → Structured Artifact → Agent B (direct consumption)
```

**Example:**
```python
# BAD: Agent B must parse this
"I found 3 issues: 15% bounce rate, -2.3% conversion, slow checkout"

# GOOD: Agent B gets structured data
{
  "issues": [
    {"metric": "bounce_rate", "value": 0.15, "severity": "high"},
    {"metric": "conversion_change", "value": -0.023, "severity": "medium"},
    {"metric": "checkout_speed", "value": "slow", "severity": "high"}
  ],
  "next_actions": ["optimize_checkout", "a/b_test_homepage"]
}
```

**Impact:** Agents waste cycles parsing natural language instead of acting on data.

---

### 2. Workflow Orchestration ❌

**Current:** Spawn-and-wait model

**Needed:** Workflow definition with dependencies

```python
# Desired workflow definition
workflow = AgentWorkflow(
    name="bookmark_digest",
    steps=[
        # Step 1: Fetch (Agent A)
        {
            "agent": "fetcher",
            "task": "Download bookmarks",
            "output_artifact": "bookmarks_raw"
        },
        # Step 2: Analyze (Agent B, depends on Step 1)
        {
            "agent": "analyzer",
            "task": "Categorize bookmarks",
            "input_artifact": "bookmarks_raw",
            "output_artifact": "bookmarks_categorized"
        },
        # Step 3: Summarize (Agent C, depends on Step 2)
        {
            "agent": "summarizer",
            "task": "Create digest",
            "input_artifact": "bookmarks_categorized",
            "output_artifact": "digest_final"
        }
    ],
    # Run Steps 2 and 3 in parallel after Step 1
    parallel_groups=[[2, 3]]
)
```

**Missing:**
- Workflow definition language
- Dependency resolution
- Parallel execution
- Result aggregation

---

### 3. Agent Specialization ❌

**Current:** All subagents use same system prompt + limited tools

**Needed:** Specialized agent types

```python
# Specialized agent configurations
AGENT_TYPES = {
    "researcher": {
        "tools": ["web_search", "web_fetch", "read_file"],
        "system_prompt": "You are a research specialist...",
        "max_tokens": 4000
    },
    "coder": {
        "tools": ["exec", "read_file", "write_file", "edit_file"],
        "system_prompt": "You are a code specialist...",
        "model": "claude-3.5-sonnet"
    },
    "analyst": {
        "tools": ["exec", "read_file", "write_file"],
        "system_prompt": "You are a data analyst...",
        "max_tokens": 2000
    }
}
```

---

### 4. Work Logs as Artifacts ❌

**Current:** Work logs (if implemented) are for human debugging

**Needed:** Work logs as structured artifacts for next agent

```python
# WorkLog should produce consumable artifacts
{
  "workflow_id": "bookmark_analysis_001",
  "producer": "analyzer_agent",
  "consumer": "summarizer_agent",
  "steps": [
    {
      "step": 1,
      "tool": "fetch_bookmarks",
      "input": {"count": 50},
      "output": {"bookmarks": [...]},
      "status": "success"
    },
    {
      "step": 2,
      "tool": "categorize",
      "input": {"items": 50},
      "output": {"categories": {...}},
      "status": "success"
    }
  ],
  "summary": {
    "total_bookmarks": 50,
    "categories_found": 5,
    "confidence": 0.91
  },
  "next_actions": ["summarize", "create_digest"]
}
```

---

### 5. Parallel Execution Coordination ❌

**Current:** Sequential spawning only

**Needed:** Parallel agent execution with result aggregation

```python
# Spawn 3 agents in parallel for different aspects
agents = [
    spawn("Analyze bounce rate", "bounce_analysis"),
    spawn("Analyze conversion", "conversion_analysis"),
    spawn("Analyze checkout", "checkout_analysis")
]

# Wait for all
results = await asyncio.gather(*agents)

# Aggregate
final_report = aggregate_results(results)
```

---

## Recommendations for Multi-Agent Enhancement

### Phase 1: Artifact Infrastructure
1. Implement `AgentArtifactStore` (as documented in RAW_WORK_LOGS_IMPLEMENTATION.md)
2. Add artifact generation to work logs
3. Create artifact schema versioning
4. Update subagent to produce artifacts, not just text

### Phase 2: Workflow Orchestration
1. Create `AgentWorkflow` class
2. Implement dependency resolution
3. Add parallel execution support
4. Create workflow definition DSL (YAML/JSON)

### Phase 3: Agent Specialization
1. Define agent type configurations
2. Add specialized system prompts
3. Create agent registry
4. Allow skill-based agent selection

### Phase 4: Advanced Coordination
1. Add agent-to-agent direct communication
2. Implement result aggregation patterns
3. Add workflow visualization
4. Create debugging tools for multi-agent workflows

---

## Integration with Raw Work Logs

The work logs implementation should enable multi-agent orchestration by:

1. **Structured Output:** Work logs produce both human-readable and agent-consumable artifacts
2. **Next Action Extraction:** `_extract_next_actions()` suggests what next agent should do
3. **Artifact Store:** Agents save work logs for other agents to consume
4. **Tool Chaining:** Each tool execution becomes a step in the workflow

---

## Current vs. Desired Comparison

| Feature | Current | Desired |
|---------|---------|---------|
| Agent Spawning | ✅ Background tasks | ✅ Specialized roles |
| Communication | ✅ Message bus (text) | ✅ Artifacts (structured) |
| Parallel Execution | ❌ Sequential only | ✅ Parallel with coordination |
| Workflow Definition | ❌ None | ✅ YAML/JSON workflows |
| Result Format | Text | Structured artifacts |
| Agent Types | Generic | Specialized (researcher, coder, etc.) |
| Debugging | Logs | Visual workflow graphs |

---

## Conclusion

**Current State:** nanobot has a solid foundation with the Subagent system, but it's primarily designed for **background task execution** rather than **multi-agent orchestration**.

**Next Steps:**
1. Implement work logs with artifact generation (documented)
2. Extend SpawnTool to accept agent types
3. Create ArtifactStore for agent handoffs
4. Build WorkflowOrchestrator for complex multi-agent chains

**Priority:** Medium - Current subagent system works for simple parallel tasks. Full orchestration needed for complex workflows like:
- Multi-step research pipelines
- Code review workflows
- Data processing chains
- Multi-domain analysis tasks

---

**Related Documents:**
- [RAW_WORK_LOGS_IMPLEMENTATION.md](RAW_WORK_LOGS_IMPLEMENTATION.md) - Work logs with artifacts
- [VoxYZ: Artifact Handoffs](https://www.voxyz.space/insights/agents-need-artifact-handoffs-not-chat-reports) - Why artifacts beat chat
- [VoxYZ: Work Logs](https://www.voxyz.space/insights/agent-work-logs-beat-polish-trust) - Transparency research
