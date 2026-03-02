# REPL Tool Implementation Plan

**Purpose**: Replace discrete tool calls with a programmable REPL environment for better composability, state persistence, and multi-bot coordination.

**Status**: Proposed  
**Created**: March 2, 2026  
**Based on**: [Witan Labs Research - REPL Tool](https://github.com/witanlabs/research-log/blob/main/06-repl-tool.md)

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

### Phase 1: Core REPL Tool (Weeks 1-2)

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
- [ ] `REPLTool` class in `nanofolks/agent/tools/repl.py`
- [ ] `RestrictedPythonSandbox` in `nanofolks/agent/tools/repl_sandbox.py`
- [ ] `ToolAPI`, `BotAPI`, `MemoryAPI` in `nanofolks/agent/tools/repl_api.py`
- [ ] Register REPL tool in tool registry
- [ ] Basic tests

---

### Phase 2: System Prompt Integration (Week 3)

**Objective**: Document REPL API in system prompt

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

### Phase 3: Migration & Optimization (Weeks 4-6)

**Objective**: Migrate high-value use cases to REPL

#### High-Value Targets

1. **Multi-Bot Workflows**
```python
# Before: 5 tool calls
ask_bot("researcher", "search X")
ask_bot("analyst", "analyze X")
ask_bot("writer", "summarize X")

# After: 1 REPL call
from bots import coordinator
research = coordinator.ask("researcher", "search X")
analysis = coordinator.ask("analyst", f"analyze {research}")
summary = coordinator.ask("writer", f"summarize {analysis}")
```

2. **Complex Memory Operations**
```python
# Before: 3 tool calls
query_memory("project:X")
query_memory("recent:7d")
query_memory("user:preferences")

# After: 1 REPL call
from memory import search, recent, load
project = search("project:X")
recent_items = recent(7)
prefs = load("user_preferences")
context = project.merge(recent_items).filter(prefs)
```

3. **Research Pipelines**
```python
# Before: 6 tool calls
web_search()
scrape_url()
extract_text()
summarize()
store_memory()
format_response()

# After: 2 REPL calls
# Call 1: Research
from tools import web
from memory import store
url = web.search("X")[0].url
content = web.scrape(url).extract_text()
store("research_X", content)

# Call 2: Respond
from memory import load
from tools import text
research = load("research_X")
summary = text.summarize(research)
return summary
```

#### Migration Strategy

1. **Identify high-call-count workflows** (logs analysis)
2. **Create REPL equivalents** with benchmarks
3. **A/B test** (50% users get REPL, 50% get discrete tools)
4. **Measure improvement** (tool calls, latency, token usage)
5. **Gradual rollout** based on results

#### Deliverables
- [ ] Migrate 3-5 high-value workflows
- [ ] Benchmark comparison (REPL vs. discrete tools)
- [ ] Migration guide for developers
- [ ] Telemetry dashboard

---

### Phase 4: Advanced Features (Weeks 7-8)

**Objective**: Add advanced REPL capabilities

#### Features

1. **Variable Namespacing (for sub-agents)**
```python
# Each sub-agent gets isolated namespace
class REPLTool:
    def __init__(self, var_prefix=""):
        self.var_prefix = var_prefix
    
    def execute(self, code, globals):
        # Prefix all variables
        prefixed_globals = {
            f"{self.var_prefix}_{k}": v 
            for k, v in globals.items()
        }
        # ...
```

2. **REPL State Inspection**
```python
# Tool to inspect REPL state
def inspect_repl():
    """Show current REPL variables"""
    from tools import repl
    return repl.list_variables()
```

3. **REPL Reset**
```python
# Reset REPL state
def reset_repl():
    """Clear REPL state"""
    from tools import repl
    repl.clear()
```

4. **REPL Snapshots**
```python
# Save/restore REPL state
snapshot = repl.save_snapshot()
# ... later ...
repl.restore_snapshot(snapshot)
```

#### Deliverables
- [ ] Variable namespacing for sub-agents
- [ ] REPL state inspection tools
- [ ] Reset and snapshot features
- [ ] Documentation updates

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

## Comparison: REPL vs. Other Approaches

| Approach | Composability | State | Tool Calls | Complexity | Security |
|----------|---------------|-------|------------|------------|----------|
| **Discrete tools** (current) | Low | None | High (10-15) | High (many tools) | High |
| **Batch dispatch** | Medium | None | Medium (5-8) | Medium | High |
| **SQL queries** | Medium | DB state | Medium (5-8) | Medium | Medium |
| **REPL** (proposed) | **High** | **Persistent** | **Low (2-3)** | **Low (one tool)** | Medium (sandboxed) |

---

## Open Questions

1. **Language choice**: Python vs. JavaScript?
   - Python: Natural fit, RestrictedPython available
   - JavaScript: Better for QuickJS sandboxing (Witan's approach)
   
2. **State persistence scope**: Per-session vs. per-user?
   - Per-session: Simpler, isolated
   - Per-user: More powerful, but privacy concerns

3. **Hybrid vs. full REPL**: Keep discrete tools or deprecate?
   - Hybrid: Lower risk, gradual adoption
   - Full REPL: Simpler, but higher risk

4. **External channels**: Enable REPL for WhatsApp/iMessage?
   - CLI/Desktop: Yes (trusted)
   - External channels: Maybe (security review needed)

---

## References

- [Witan Labs Research Log - REPL Tool](https://github.com/witanlabs/research-log/blob/main/06-repl-tool.md)
- [RestrictedPython Documentation](https://restrictedpython.readthedocs.io/)
- [QuickJS Emscripten](https://github.com/nickolay/quickjs-emscripten)

---

## Next Steps

1. **Approve this plan** - Review with team
2. **Phase 1 kickoff** - Start REPL tool implementation
3. **Set up telemetry** - Baseline metrics
4. **Create examples** - Document common patterns
5. **Begin migration** - High-value workflows first

---

**Status**: Ready for review  
**Owner**: TBD  
**Target Start**: Week 1 (pending approval)
