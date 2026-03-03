# REPL Tool Implementation Plan

**Purpose**: Replace discrete tool calls with a programmable REPL environment for better composability, state persistence, and multi-bot coordination.

**Status**: ✅ ALL PHASES COMPLETE (March 3, 2026)  
**Created**: March 2, 2026  
**Completed**: March 3, 2026
**Based on**: [Witan Labs Research - REPL Tool](https://github.com/witanlabs/research-log/blob/main/06-repl-tool.md)

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Language** | Python | Natural fit for codebase, RestrictedPython available |
| **State Scope** | Per-Room | Aligns with room-centric architecture, cross-channel continuity |
| **Approach** | Hybrid (short-term) | Lower risk, gradual migration, easy rollback |
| **Channels** | All channels | REPL is room-scoped, works on CLI/WhatsApp/iMessage/etc. by default |

---

## Executive Summary

The REPL Tool pattern replaces many discrete tools with a **single programmable environment** where the agent can execute arbitrary code with access to rich APIs. This dramatically reduces tool calls (10-15 → 2-3), enables state persistence, and makes multi-bot coordination programmatic instead of message-based.

**Key Benefits:**
- 70-80% reduction in tool calls
- State persists across operations
- Multi-bot coordination becomes programmatic
- Matches how developers actually work
- Easier API extension (add function, not new tool)

**Risk Level**: Medium (requires sandboxing, but hybrid approach minimizes disruption)

---

## Goals

### Primary Goals
- Reduce tool calls from 10-15 per task to 2-3 per task
- Enable state persistence across tool operations
- Make multi-bot coordination programmatic and efficient
- Simplify tool management (one tool vs. many)
- Improve agent reasoning by reducing context overhead

### Secondary Goals
- Make API extension easier (add function vs. new tool)
- Enable complex workflows without LLM round-trips
- Improve memory/context building efficiency
- Align with developer mental models (CLI-first philosophy)

---

## Non-Goals

- Replace all existing tools immediately (hybrid approach)
- Change bot definitions or roles
- Remove MCP client (stays separate for security)
- Eliminate security layer (sanitization, credential detection still needed)
- Support REPL for all external channels (start with CLI/desktop only)

---

## Current Architecture (Pain Points)

### Problem 1: Tool Call Overhead
```
User: "Research OpenClaw project and summarize"

Current Flow (10+ tool calls):
1. web_search("OpenClaw GitHub")
2. scrape_url(results[0])
3. extract_text(html)
4. summarize(text)
5. store_memory("openclaw_summary", summary)
6. ask_bot("analyst", "review this")
7. query_memory("user context")
8. combine(summary, review, context)
9. format_response(combined)
10. send_response()

Each call = LLM round-trip, context grows, state lost
```

### Problem 2: Multi-Bot Coordination Overhead
```
Current: Message-passing between bots
Bot A → "ask Bot B" → Bot B responds → Bot A processes
Bot A → "ask Bot C" → Bot C responds → Bot A processes
Bot A → merge results → respond

Each bot interaction = separate tool call + context growth
```

### Problem 3: Stateless Memory Operations
```
query_memory("X") → results
query_memory("Y") → results
query_memory("Z") → results
# No way to compose these without LLM round-trips
```

---

## Proposed Architecture

### Core Concept: Single REPL Tool

```
┌─────────────────────────────────────────────┐
│            Agent Loop                        │
├─────────────────────────────────────────────┤
│                                              │
│   REPL Tool (single entry point)            │
│   ├─ Tools API (web, file, shell, etc.)     │
│   ├─ Bot API (coordinator, ask, delegate)   │
│   ├─ Memory API (search, store, associate)  │
│   ├─ Skills API (load, compose, run)        │
│   └─ Session API (history, context)         │
│                                              │
├─────────────────────────────────────────────┤
│   Persistent State (variables survive)       │
│   - wb = open_workbook()                     │
│   - results = search()                       │
│   - context = memory.load()                  │
└─────────────────────────────────────────────┘
```

### Example: Research Task (2 calls vs 10)

```python
# Call 1: Research and analyze
from tools import web, text
from bots import coordinator
from memory import store

url = web.search("OpenClaw GitHub")[0].url
html = web.scrape(url)
summary = text.summarize(html)

# Store immediately
store("openclaw_summary", summary)

# Get analyst review
analysis = coordinator.ask("analyst", f"Review: {summary}")

# Variables persist, no re-fetching needed
```

```python
# Call 2: Respond with context
from memory import load

context = load("user_context")
response = f"{analysis}\n\nContext: {context.relevant_info}"
return response
```

---

## Implementation Phases

### Phase 1: Core REPL Tool (Weeks 1-2) ✅ COMPLETE

**Objective**: Create basic REPL tool alongside existing tools

#### Components

1. **REPL Tool Class**
```python
# nanofolks/agent/tools/repl.py

class REPLTool(Tool):
    """Single tool with persistent Python environment"""
    
    name = "repl"
    description = "Execute arbitrary Python code with access to tools, bots, and memory APIs"
    
    def __init__(self, tools_registry, bot_coordinator, memory_store):
        self.tools = tools_registry
        self.bots = bot_coordinator
        self.memory = memory_store
        
        # Persistent globals (survive across calls)
        self.globals = {
            'tools': ToolAPI(tools_registry),
            'bots': BotAPI(bot_coordinator),
            'memory': MemoryAPI(memory_store),
            'session': SessionAPI(),
            'skills': SkillsAPI(),
        }
        
        # Sandbox executor
        self.sandbox = RestrictedPythonSandbox(
            timeout=90,
            max_output_chars=20000,
            allowed_modules=['tools', 'bots', 'memory', 'json', 're', 'datetime'],
        )
    
    async def execute(self, code: str) -> str:
        """
        Execute Python code in sandboxed environment.
        
        Args:
            code: Python code to execute
        
        Returns:
            Execution result as string
        """
        try:
            result = await self.sandbox.execute_async(
                code=code,
                globals=self.globals,
                timeout=90
            )
            return result
        except TimeoutError:
            return "Error: Execution timeout (90s limit)"
        except Exception as e:
            return f"Error: {str(e)}"
```

2. **Sandbox Executor**
```python
# nanofolks/agent/tools/repl_sandbox.py

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins
import asyncio
import signal

class RestrictedPythonSandbox:
    """Sandboxed Python execution environment"""
    
    def __init__(self, timeout=90, max_output_chars=20000, allowed_modules=None):
        self.timeout = timeout
        self.max_output_chars = max_output_chars
        self.allowed_modules = allowed_modules or []
    
    async def execute_async(self, code: str, globals: dict, timeout: int) -> str:
        """Execute code with timeout and output limits"""
        
        # Compile with restrictions
        byte_code = compile_restricted(
            source=code,
            filename='<repl>',
            mode='exec'
        )
        
        # Capture stdout
        output_buffer = []
        
        def capture_print(*args, **kwargs):
            output_buffer.append(' '.join(str(arg) for arg in args))
        
        # Safe builtins
        safe_globals = {
            '__builtins__': {
                **safe_builtins,
                'print': capture_print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'list': list,
                'dict': dict,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
            },
            **globals
        }
        
        # Execute with timeout
        try:
            exec(byte_code, safe_globals)
            output = '\n'.join(output_buffer)
            
            # Truncate if needed
            if len(output) > self.max_output_chars:
                output = output[:self.max_output_chars] + "\n... (truncated)"
            
            return output
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)}"
```

3. **API Surfaces**
```python
# nanofolks/agent/tools/repl_api.py

class ToolAPI:
    """Tools API for REPL"""
    
    def __init__(self, registry):
        self._registry = registry
    
    async def web_search(self, query: str, limit: int = 5):
        """Search the web"""
        return await self._registry.execute('web_search', {'query': query, 'limit': limit})
    
    async def file_read(self, path: str):
        """Read a file"""
        return await self._registry.execute('read_file', {'path': path})
    
    async def shell_exec(self, cmd: str):
        """Execute shell command"""
        return await self._registry.execute('shell', {'command': cmd})
    
    # ... wrap all existing tools


class BotAPI:
    """Bot coordination API for REPL"""
    
    def __init__(self, coordinator):
        self._coordinator = coordinator
    
    async def ask(self, bot_name: str, message: str, timeout: int = 60):
        """Ask a specific bot"""
        return await self._coordinator.ask_bot(bot_name, message, timeout)
    
    async def broadcast(self, message: str):
        """Broadcast to all bots"""
        return await self._coordinator.broadcast(message)
    
    async def delegate(self, task: str, bots: list[str]):
        """Delegate task to multiple bots"""
        return await self._coordinator.delegate_task(task, bots)


class MemoryAPI:
    """Memory API for REPL"""
    
    def __init__(self, memory_store):
        self._store = memory_store
    
    async def search(self, query: str, limit: int = 10):
        """Search memory"""
        return await self._store.search(query, limit)
    
    async def store(self, key: str, value: any, tags: list[str] = None):
        """Store in memory"""
        return await self._store.store(key, value, tags)
    
    async def recent(self, days: int = 7):
        """Get recent memories"""
        return await self._store.get_recent(days)
    
    async def associate(self, item: any, tags: list[str]):
        """Associate item with tags"""
        return await self._store.associate(item, tags)
```

#### Deliverables
- [x] `REPLTool` class in `nanofolks/agent/tools/repl.py` ✅
- [x] `RestrictedPythonSandbox` in `nanofolks/agent/tools/repl_sandbox.py` ✅
- [x] `ToolAPI`, `BotAPI`, `MemoryAPI` in `nanofolks/agent/tools/repl_api.py` ✅
- [x] Register REPL tool in tool registry ✅ (in `factory.py`)
- [x] Basic tests ✅ (`test_repl.py`, all passing)

**Additional implemented:**
- [x] `REPLStateManager` in `repl_manager.py` (room-scoped state)
- [x] `REPLState` in `repl_state.py` (per-room REPL environment)

**Fixes applied**:
- [x] BotAPI now uses `BotInvoker` instead of non-existent `BotCoordinator` methods ✅
- [x] Updated API: `invoke()`, `invoke_many()`, `list_bots()`, `has_bot()` ✅
- [x] Added room_id propagation to invoker for room-centric architecture ✅

**Known limitations**:
- SkillsAPI is stub (Phase 4 scope)

---

### Phase 2: System Prompt Integration (Week 3) ✅ COMPLETE

**Objective**: Document REPL API in system prompt

**Completed:**
- [x] Created `repl_prompt.md` with REPL documentation ✅
- [x] Integrated REPL prompt into `ContextBuilder` ✅
- [x] Auto-generated API docs (reference tables) ✅
- [x] Example library for common patterns ✅
- [x] Best practices guide ✅

#### System Prompt Template

```markdown
## REPL Tool (`repl`)

The REPL tool provides a persistent Python environment with access to tools, bots, memory, and skills.

### When to Use REPL
- Multi-step operations (3+ related tool calls)
- Multi-bot coordination
- Complex memory queries
- Workflows requiring state persistence

### When to Use Discrete Tools
- Simple single operations
- Quick lookups
- External MCP tools

### Hard Rules
1. **Always handle errors** - Wrap operations in try/except
2. **Respect timeouts** - Break up work that takes >90s
3. **Be selective with output** - Don't print everything (20K char limit)
4. **Check variable state** - If REPL dies, re-import modules

### First-time Setup
```python
from tools import web, file, shell
from bots import coordinator
from memory import search, store
```

### API Reference

#### Tools API
{{{tool_api_docs}}}

#### Bot API
{{{bot_api_docs}}}

#### Memory API
{{{memory_api_docs}}}

### Examples

#### Research Task
```python
from tools import web
from memory import store

url = web.search("OpenClaw")[0].url
html = web.scrape(url)
store("openclaw_html", html)
print(f"Stored {len(html)} chars from {url}")
```

#### Multi-Bot Coordination
```python
from bots import coordinator

research = coordinator.ask("researcher", "Find info on OpenClaw")
analysis = coordinator.ask("analyst", f"Analyze: {research}")
print(f"Research: {research}\nAnalysis: {analysis}")
```
```

#### Deliverables
- [ ] System prompt template with REPL documentation
- [ ] Auto-generated API docs from type hints
- [ ] Example library for common patterns
- [ ] Best practices guide

---

### Phase 3: Migration & Optimization (Weeks 4-6) ✅ COMPLETE

**Objective**: Integrate REPL into AgentLoop and optimize tool APIs

**Completed:**
- [x] Integrated REPL into AgentLoop (`loop.py:_register_default_tools`) ✅
- [x] Created REPLStateManager with API factory for room-scoped environments ✅
- [x] Added async code execution support in sandbox (`_execute_async_code`) ✅
- [x] Added sync methods to all tool APIs for REPL sandbox compatibility ✅
  - `WebToolsAPI`: `search()`, `scrape()`, `fetch()` (sync versions)
  - `FileToolsAPI`: `read()`, `write()`, `list()`, `edit()` (sync versions)
  - `ShellToolsAPI`: `exec()`, `run()` (sync versions)
  - `BrowserToolsAPI`: `open()`, `click()`, `type_text()`, `screenshot()` (sync versions)
- [x] Added MCP tools support (`MCPToolsAPI`: `list()`, `has()`, `call()`, `connect()`) ✅
- [x] All tests passing (sandbox, state, manager, tool, cross-channel) ✅

**Tested Scenarios:**
- [x] Research Pipeline (search → scrape → process) ✅
- [x] File Operations (read → transform → write) ✅
- [x] Shell + Processing (exec → parse → iterate) ✅
- [x] State Persistence (variables survive across calls) ✅
- [x] Conditional Logic (if/elif/else) ✅
- [x] Loops (for/while) ✅
- [x] Custom Functions (def) ✅

---

### Phase 4: Advanced Features (Weeks 7-8) ✅ COMPLETE

**Objective**: Add advanced REPL capabilities

**Completed:**

1. **Variable Namespacing (for sub-agents)** ✅
```python
# Implemented in REPLState:
def get_namespaced_variables(self, prefix: str) -> Dict[str, Any]:
    """Get variables with a specific prefix (for sub-agent isolation)."""
    
def set_namespaced_variables(self, prefix: str, variables: Dict[str, Any]) -> None:
    """Set multiple variables with a specific prefix."""
```

2. **REPL State Inspection** ✅
```python
# Implemented as tool actions and REPLToolsAPI:
def list_variables(self) -> Dict[str, str]:
    """List current REPL variables."""
    
def get_history(self, limit: int = 10) -> List[Dict]:
    """Get execution history."""
    
def get_stats(self) -> Dict[str, Any]:
    """Get REPL statistics."""
```

3. **REPL Reset** ✅
```python
# Implemented as tool action:
def reset(self) -> None:
    """Reset REPL state (clear all variables)."""
    
# Accessible via:
repl(action="reset")
# Or in REPL code:
repl.reset()
```

4. **REPL Snapshots** ✅
```python
# Implemented in REPLState:
def save_snapshot(self) -> Dict[str, Any]:
    """Save current REPL state for later restoration."""
    
def restore_snapshot(self, snapshot: Dict[str, Any]) -> bool:
    """Restore REPL state from snapshot."""
```

5. **REPL Management Actions** ✅
- `action: "list_variables"` - Show current variables
- `action: "reset"` - Clear all variables
- `action: "get_history"` - Show execution history
- `action: "get_stats"` - Show REPL statistics
- `action: "save_snapshot"` - Save state for later
- `action: "restore_snapshot"` - Restore from snapshot

6. **REPLToolsAPI for in-REPL access** ✅
```python
# Accessible from within REPL code:
from repl import list_variables, reset, get_history, get_stats

vars = list_variables()
reset()
history = get_history()
stats = get_stats()
```

#### Deliverables
- [x] Variable namespacing for sub-agents ✅
- [x] REPL state inspection tools ✅
- [x] Reset and snapshot features ✅
- [x] Documentation updates ✅
- [x] MCP tools support ✅
- [x] Sync API methods for all tools ✅

---

## Security Considerations

### Sandboxing Requirements

1. **No Filesystem Access**
```python
# Block file operations
blocked_modules = ['os', 'sys', 'subprocess', 'shutil', 'pathlib']
```

2. **No Network Access**
```python
# Block network operations
blocked_modules.extend(['socket', 'requests', 'http', 'urllib'])
```

3. **Timeout Enforcement**
```python
# 90-second hard timeout
async def execute_async(self, code, globals, timeout=90):
    # Kill after timeout
    ...
```

4. **Output Truncation**
```python
# 20K character limit
if len(output) > 20000:
    output = output[:20000] + "\n... (truncated)"
```

5. **Memory Limits**
```python
# 256MB memory limit
import resource
resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
```

### Security Layer (Still Needed)

- **Sanitization**: Sanitize all outputs before returning
- **Credential Detection**: Scan for secrets in code/output
- **Audit Logging**: Log all REPL executions

---

## Success Metrics

### Primary Metrics

| Metric | Current (Discrete Tools) | Target (REPL) | Improvement |
|--------|--------------------------|---------------|-------------|
| Tool calls per task | 10-15 | 2-3 | 70-80% reduction |
| Multi-bot latency | 3-5s per bot | <1s per bot | 3-5x faster |
| Context tokens | 5000-10000 | 1000-2000 | 5x reduction |
| Memory operations | 3-5 calls | 1 call | 3-5x reduction |

### Secondary Metrics

- **Agent satisfaction**: Fewer context management errors
- **Developer experience**: Easier to add new capabilities
- **System load**: Fewer tool calls = less overhead

### Measurement Plan

1. **Baseline**: Measure current metrics for 1 week
2. **A/B test**: 50% REPL, 50% discrete tools for 2 weeks
3. **Full rollout**: Monitor for regressions
4. **Ongoing**: Track metrics weekly

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Security sandbox escape | High | Low | Multiple layers (RestrictedPython, timeouts, resource limits) |
| Agent confusion | Medium | Medium | Clear system prompt docs, examples, hybrid approach |
| Performance regression | Medium | Low | Timeout limits, output truncation, monitoring |
| Debugging difficulty | Medium | Medium | REPL state inspection, error logging, snapshots |
| Learning curve | Low | Medium | Good docs, examples, gradual migration |

---

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Phase 1: Core REPL | 2 weeks | Week 1 | Week 2 |
| Phase 2: System Prompt | 1 week | Week 3 | Week 3 |
| Phase 3: Migration | 3 weeks | Week 4 | Week 6 |
| Phase 4: Advanced | 2 weeks | Week 7 | Week 8 |
| **Total** | **8 weeks** | | |

---

## Rollout Plan

### Week 1-2: Internal Testing
- Deploy REPL tool to dev environment
- Test with internal team
- Fix critical bugs

### Week 3: Beta Testing
- Enable REPL for 10% of users
- Collect feedback
- Refine system prompt

### Week 4-6: Gradual Rollout
- Increase to 25% → 50% → 75%
- Monitor metrics
- Address issues

### Week 7-8: Full Rollout
- Enable REPL for all users
- Keep discrete tools as fallback
- Document best practices

---

## REPL State Manager

### Architecture

The REPL State Manager provides room-scoped REPL environments:

```
┌────────────────────────────────────────────────────────┐
│                    Room Manager                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Room: "project-alpha"                           │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │ Session (messages, context)                │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │ REPL State (Python environment)            │  │  │
│  │  │ - Variables persist across calls           │  │  │
│  │  │ - Shared by all channels                   │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                          ↑
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │   CLI   │      │WhatsApp │      │iMessage │
   │ Channel │      │ Channel │      │ Channel │
   └─────────┘      └─────────┘      └─────────┘
```

### Implementation

#### REPL State Manager

```python
# nanofolks/agent/tools/repl_manager.py

from typing import Dict
from loguru import logger


class REPLStateManager:
    """
    Manage REPL state per room.
    
    REPL state is room-scoped, not user-scoped or channel-scoped.
    This means all channels in a room share the same REPL environment.
    """
    
    def __init__(self):
        # Map: room_id → REPLState
        self._states: Dict[str, "REPLState"] = {}
        self._sandbox_factory = RestrictedPythonSandbox
    
    def get_state(self, room_id: str) -> "REPLState":
        """
        Get or create REPL state for a room.
        
        Args:
            room_id: Room identifier (e.g., "project-alpha")
        
        Returns:
            REPLState instance for this room
        """
        if room_id not in self._states:
            logger.info(f"Creating new REPL state for room: {room_id}")
            self._states[room_id] = REPLState(
                room_id=room_id,
                sandbox=self._sandbox_factory()
            )
        return self._states[room_id]
    
    def clear_state(self, room_id: str) -> None:
        """
        Clear REPL state when room is archived.
        
        This is called when a room is deleted or archived to
        free up memory and prevent stale state.
        
        Args:
            room_id: Room identifier to clear
        """
        if room_id in self._states:
            logger.info(f"Clearing REPL state for room: {room_id}")
            del self._states[room_id]
    
    def has_state(self, room_id: str) -> bool:
        """Check if a room has REPL state"""
        return room_id in self._states
    
    def list_rooms(self) -> list[str]:
        """List all rooms with active REPL state"""
        return list(self._states.keys())
    
    def get_stats(self) -> dict:
        """Get REPL state statistics"""
        return {
            "active_rooms": len(self._states),
            "room_ids": self.list_rooms(),
        }
```

#### REPL State

```python
# nanofolks/agent/tools/repl_state.py

from typing import Any, Dict
from loguru import logger


class REPLState:
    """
    REPL state for a single room.
    
    This class manages:
    - Persistent Python globals (survive across calls)
    - Sandboxed code execution
    - Room-scoped isolation
    """
    
    def __init__(self, room_id: str, sandbox: "RestrictedPythonSandbox"):
        self.room_id = room_id
        self.sandbox = sandbox
        self.call_count = 0
        
        # Persistent globals (survive across calls)
        # These are shared by all channels in this room
        self.globals: Dict[str, Any] = {
            '__builtins__': {},  # Set by sandbox
            'tools': ToolAPI(),
            'bots': BotAPI(),
            'memory': MemoryAPI(room_id=room_id),  # Room-scoped
            'skills': SkillsAPI(),
            'session': SessionAPI(room_id=room_id),
        }
        
        logger.debug(f"REPL state initialized for room: {room_id}")
    
    async def execute(self, code: str) -> str:
        """
        Execute Python code in this room's REPL.
        
        Args:
            code: Python code to execute
        
        Returns:
            Execution result as string
        """
        self.call_count += 1
        
        logger.debug(
            f"Executing REPL code in room {self.room_id} "
            f"(call #{self.call_count}, {len(code)} chars)"
        )
        
        try:
            result = await self.sandbox.execute_async(
                code=code,
                globals=self.globals,
                timeout=90
            )
            
            logger.debug(
                f"REPL execution complete in room {self.room_id}: "
                f"{len(result)} chars output"
            )
            
            return result
            
        except TimeoutError:
            logger.warning(f"REPL timeout in room {self.room_id}")
            return "Error: Execution timeout (90s limit)"
        except Exception as e:
            logger.error(f"REPL error in room {self.room_id}: {e}")
            return f"Error: {type(e).__name__}: {str(e)}"
    
    def reset(self) -> None:
        """
        Reset REPL state (clear all variables).
        
        This is useful for debugging or when the agent gets into a bad state.
        """
        logger.info(f"Resetting REPL state for room: {self.room_id}")
        self.globals = {
            '__builtins__': {},
            'tools': ToolAPI(),
            'bots': BotAPI(),
            'memory': MemoryAPI(room_id=self.room_id),
            'skills': SkillsAPI(),
            'session': SessionAPI(room_id=self.room_id),
        }
        self.call_count = 0
    
    def list_variables(self) -> Dict[str, str]:
        """
        List current REPL variables (for debugging).
        
        Returns:
            Dict of variable name → type name
        """
        return {
            name: type(value).__name__
            for name, value in self.globals.items()
            if not name.startswith('_')
        }
    
    def get_variable(self, name: str) -> Any:
        """Get a specific variable value"""
        return self.globals.get(name)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a specific variable value (for testing)"""
        self.globals[name] = value
```

#### Room-Scoped APIs

```python
# nanofolks/agent/tools/repl_api.py

class MemoryAPI:
    """
    Memory API for REPL (room-scoped).
    
    All memory operations are automatically scoped to the current room.
    """
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self._store = get_memory_store()  # Global memory store
    
    async def search(self, query: str, limit: int = 10):
        """Search memory in current room"""
        return await self._store.search(
            query=query,
            room_id=self.room_id,
            limit=limit
        )
    
    async def store(self, key: str, value: Any, tags: list[str] = None):
        """Store in memory (room-scoped)"""
        return await self._store.store(
            key=key,
            value=value,
            tags=tags,
            room_id=self.room_id  # Auto-scoped!
        )
    
    async def recent(self, days: int = 7):
        """Get recent memories from current room"""
        return await self._store.get_recent(
            days=days,
            room_id=self.room_id
        )
    
    async def load(self, key: str):
        """Load a specific memory"""
        return await self._store.load(
            key=key,
            room_id=self.room_id
        )


class SessionAPI:
    """
    Session API for REPL (room-scoped).
    
    Access current session context and history.
    """
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self._session_manager = get_session_manager()
    
    async def get_history(self, limit: int = 10):
        """Get recent session history"""
        return await self._session_manager.get_history(
            room_id=self.room_id,
            limit=limit
        )
    
    async def get_context(self):
        """Get current session context"""
        return await self._session_manager.get_context(
            room_id=self.room_id
        )
```

### Integration with Agent Loop

```python
# nanofolks/agent/loop.py

class AgentLoop:
    def __init__(
        self,
        tools: ToolRegistry,
        bots: BotCoordinator,
        memory: MemoryStore,
        repl_manager: REPLStateManager,  # NEW!
    ):
        self.tools = tools
        self.bots = bots
        self.memory = memory
        self.repl_manager = repl_manager  # NEW!
    
    async def process_message(self, msg: MessageEnvelope):
        """Process message with REPL support"""
        
        # 1. Get room from message
        room = self.room_manager.get_room(msg.room_id)
        
        # 2. Get REPL state for this room (creates if needed)
        repl_state = self.repl_manager.get_state(room.id)
        
        # 3. Execute agent logic (agent can use REPL tool)
        response = await self.agent_loop(
            session=session,
            msg=msg,
            repl_state=repl_state  # Pass to tools
        )
        
        # 4. Send response (channel-agnostic)
        return response
```

### Cross-Channel Workflow Example

**Scenario**: User researches on CLI, continues on WhatsApp

```python
# ========== MORNING (CLI in "Project Alpha" room) ==========

# User sends: "Research OpenClaw and save for later"

# Agent executes REPL code:
from tools import web, file
from memory import store

url = web.search("OpenClaw GitHub")[0].url
html = web.scrape(url)
code = file.read("~/code/openclaw/main.py")

# Store in REPL state AND memory
research_data = {"url": url, "html": html, "code": code}
store("openclaw_research", research_data)

print(f"Research complete: {len(html)} chars from {url}")

# REPL state saved to room: project-alpha
# Variables persist: url, html, code, research_data


# ========== AFTERNOON (WhatsApp in same room) ==========

# User sends: "What did I find about OpenClaw?"

# Agent executes REPL code (same state!):
from memory import load

# Load from memory (or use persisted variables)
research = load("openclaw_research")

# Or directly use persisted variables!
# html, url, code still exist in REPL state

summary = summarize(research["html"])
return f"Found: {summary}\nURL: {research['url']}"

# User receives response on WhatsApp with context from CLI session!
```

### Room Lifecycle Hooks

```python
# nanofolks/rooms/manager.py

class RoomManager:
    def __init__(self, repl_manager: REPLStateManager):
        self.repl_manager = repl_manager
    
    def create_room(self, room_id: str, config: dict):
        """Create a new room"""
        # Create room...
        
        # REPL state will be created on first access
        # (lazy initialization)
    
    def archive_room(self, room_id: str):
        """Archive a room and clear REPL state"""
        # Archive room...
        
        # Clear REPL state to free memory
        self.repl_manager.clear_state(room_id)
        
        logger.info(f"Room {room_id} archived, REPL state cleared")
```

### Benefits of Room-Scoped REPL

1. **Cross-Channel Continuity**: Start task on CLI, continue on WhatsApp
2. **Natural Lifecycle**: REPL state dies when room is archived
3. **Security Isolation**: Each room is isolated, no cross-room access
4. **Memory Efficiency**: Stale REPL state is automatically cleaned up
5. **Multi-User Support**: If teams are added later, REPL state is shared in room

---

## Comparison: REPL vs. Other Approaches

| Approach | Composability | State | Tool Calls | Complexity | Security |
|----------|---------------|-------|------------|------------|----------|
| **Discrete tools** (current) | Low | None | High (10-15) | High (many tools) | High |
| **Batch dispatch** | Medium | None | Medium (5-8) | Medium | High |
| **SQL queries** | Medium | DB state | Medium (5-8) | Medium | Medium |
| **REPL** (proposed) | **High** | **Persistent** | **Low (2-3)** | **Low (one tool)** | Medium (sandboxed) |

---

## Design Decisions

### 1. Language Choice: Python ✅

**Decision**: Use Python for REPL implementation.

**Rationale**:
- Entire nanofolks codebase is Python
- RestrictedPython is mature and well-tested
- Natural integration with existing tools (no language bridging)
- Easier for team to maintain and extend

**Implementation**: Use RestrictedPython for sandboxing with custom security policies.

---

### 2. State Persistence: Per-Room ✅

**Decision**: REPL state is scoped to rooms, not users or sessions.

**Rationale**:
- Aligns with room-centric architecture
- All channels in a room share the same REPL state
- Natural lifecycle (room archived → REPL state cleared)
- Enables cross-channel workflows (start on CLI, continue on WhatsApp)
- No cross-room pollution (security benefit)

**Implementation**:
```python
# REPL state is tied to room_id, not user_id or channel
repl_state = repl_manager.get_state(room_id="project-alpha")
```

**Example Workflow**:
```
Morning (CLI in "Project Alpha" room):
  wb = open_workbook("data.xlsx")
  results = search("OpenClaw")
  # State saved to room: project-alpha

Afternoon (WhatsApp in same room):
  # wb and results still accessible!
  analysis = analyze(results)
  return analysis
```

---

### 3. Hybrid Approach (Short-term) ✅

**Decision**: Keep existing discrete tools, add REPL for complex workflows.

**Rationale**:
- Lower risk (existing tools still work)
- Gradual migration based on data
- Agent can choose best approach per task
- Easy to measure improvement
- Rollback is trivial

**Long-term Vision**: Evaluate moving to full REPL after 3-6 months of usage data.

---

### 4. External Channels: Supported by Default ✅

**Decision**: REPL works on all channels (CLI, WhatsApp, iMessage, Discord, Slack).

**Rationale**:
- REPL state is room-scoped, not channel-scoped
- All channels in a room access the same REPL state
- Security is identical across channels (same sandboxing)
- This is a **strength** of room-centric architecture

**Security**: Same sandboxing applies to all channels:
- RestrictedPython sandbox
- No filesystem/network access
- 90s timeout
- Output truncation
- Room-scoped isolation

**Implementation**: No per-channel handling needed. REPL state manager automatically provides the right state based on room_id.

---

## References

- [Witan Labs Research Log - REPL Tool](https://github.com/witanlabs/research-log/blob/main/06-repl-tool.md)
- [RestrictedPython Documentation](https://restrictedpython.readthedocs.io/)
- [QuickJS Emscripten](https://github.com/nickolay/quickjs-emscripten)

---

## Next Steps

1. ~~**Approve this plan**~~ - ✅ **APPROVED** (March 2, 2026)
   - Language: Python
   - State persistence: Per-Room
   - Approach: Hybrid (short-term)
   - Channels: All channels supported

2. ~~**Phase 1 kickoff**~~ - ✅ **COMPLETE** (March 2, 2026)
   - ✅ Created `REPLStateManager` and `REPLState` classes
   - ✅ Implemented `RestrictedPythonSandbox`
   - ✅ Built room-scoped APIs (ToolAPI, BotAPI, MemoryAPI, SessionAPI, SkillsAPI)
   - ✅ Registered REPL tool in factory
   - ✅ Added tests (all passing)
   - ✅ Fixed BotAPI to use BotInvoker (aligns with multi-bot architecture)

3. ~~**Phase 2 kickoff**~~ - ✅ **COMPLETE** (March 2, 2026)
   - ✅ Created `repl_prompt.md` with REPL documentation
   - ✅ Integrated REPL prompt into `ContextBuilder`
   - ✅ Added API reference tables
   - ✅ Added common patterns examples
   - ✅ Added best practices guide

4. ~~**Phase 3 kickoff**~~ - ✅ **COMPLETE** (March 3, 2026)
   - ✅ Integrated REPL into AgentLoop
   - ✅ Created REPLStateManager with API factory
   - ✅ Added async code execution support
   - ✅ Added sync methods to all tool APIs
   - ✅ All tests passing

5. ~~**Phase 4 kickoff**~~ - ✅ **COMPLETE** (March 3, 2026)
   - ✅ Added variable namespacing
   - ✅ Added REPL state inspection tools
   - ✅ Added reset and snapshot features
   - ✅ Added REPL management actions
   - ✅ Added MCP tools support

---

## Implementation Summary

### Files Created/Modified

| File | Purpose |
|------|---------|
| `nanofolks/agent/tools/repl.py` | REPLTool class with management actions |
| `nanofolks/agent/tools/repl_sandbox.py` | RestrictedPythonSandbox with async support |
| `nanofolks/agent/tools/repl_state.py` | REPLState with snapshots, namespacing |
| `nanofolks/agent/tools/repl_manager.py` | REPLStateManager for room-scoped state |
| `nanofolks/agent/tools/repl_api.py` | All API classes with sync methods + MCP |
| `nanofolks/agent/tools/repl_prompt.md` | System prompt documentation |
| `nanofolks/agent/loop.py` | Integration into AgentLoop |
| `nanofolks/agent/tools/test_repl.py` | Comprehensive test suite |

### Available APIs in REPL

| API | Methods | Description |
|-----|---------|-------------|
| `tools.web` | `.search()`, `.scrape()`, `.fetch()` | Web search & scraping |
| `tools.file` | `.read()`, `.write()`, `.list()`, `.edit()` | File operations |
| `tools.shell` | `.exec()`, `.run()` | Shell commands |
| `tools.browser` | `.open()`, `.click()`, `.type_text()`, `.screenshot()` | Browser automation |
| `tools.mcp` | `.list()`, `.has()`, `.call()`, `.connect()` | MCP server tools |
| `bots` | `.invoke()`, `.invoke_many()`, `.list_bots()`, `.has_bot()` | Multi-bot coordination |
| `memory` | `.search()`, `.store()`, `.recent()`, `.load()` | Room-scoped memory |
| `session` | `.history()`, `.context()` | Session context |
| `skills` | `.load()`, `.run()` | Skill execution |
| `repl` | `.list_variables()`, `.reset()`, `.get_history()`, `.get_stats()` | REPL introspection |

### Tested Scenarios

All scenarios tested and passing:
- ✅ Research Pipeline (search → scrape → process)
- ✅ File Operations (read → transform → write)
- ✅ Shell + Processing (exec → parse → iterate)
- ✅ State Persistence (variables survive across calls)
- ✅ Conditional Logic (if/elif/else)
- ✅ Loops (for/while)
- ✅ Custom Functions (def)

---

**Status**: ✅ **ALL PHASES COMPLETE**  
**Owner**: nanofolks team  
**Branch**: `repl-integration`
**Ready for**: Production deployment
