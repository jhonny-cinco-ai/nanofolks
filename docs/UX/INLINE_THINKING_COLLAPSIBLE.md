# Inline Thinking Display: Collapsible Implementation Plan

**Status:** Phase 1 & 2 Complete, Phase 3 Planned  
**Phase:** 3 (Polish & Enhancement)  
**Priority:** Medium  
**Complexity:** Medium

## Overview

Enable users to see bot thinking/reasoning inline in the chat flow through a collapsible section. By default, collapsed with a one-line summary. Users can expand to see detailed work log entries showing decisions, tool calls, and reasoning.

### Goals
- Provide transparency into bot reasoning without cluttering normal responses
- Allow users to understand "why" without explicit `/explain` command
- Keep normal chat flow clean and fast
- Support both single-bot and multi-bot scenarios

## Current State

**What works:**
- Work logs are captured and stored in `WorkLogManager`
- `/explain`, `/logs`, `/how` commands show logs post-hoc
- `work_log_manager.get_formatted_log()` can format entries
- `SidebarManager` and `LayoutManager` exist but are underutilized

**What's missing:**
- Real-time toggle in chat flow
- Inline collapsible display
- Summary generation from entries
- State tracking (expanded/collapsed)

## Proposed Solution

### 1. Summary Generator (`ThinkingSummaryBuilder`)

**Location:** `nanobot/cli/ui/thinking_summary.py`

```python
class ThinkingSummaryBuilder:
    def generate_summary(log: WorkLog, max_actions: int = 2) -> str:
        """Generate one-line summary of thinking.
        
        Examples:
        - "Created coordination room, invited 2 bots"
        - "Analyzed requirements, selected medium model"
        - "Executed 3 tools: read_file, edit_file, execute"
        """
        
    def generate_details(log: WorkLog, bot_name: str = None) -> list[str]:
        """Generate expanded view lines.
        
        Returns:
        - Step N 🎯 Decision: <message>
        - Step N 🔧 Tool: <tool_name>() → <result>
        - Step N ✅ Complete: <message>
        """
```

**Logic:**
1. Filter entries by level: `DECISION`, `TOOL`, `ERROR`
2. Extract key info: category, message, tool_name, confidence
3. For summary: concatenate 1-2 main actions (tools + decisions)
4. For details: format each entry with step number, icon, message

### 2. Collapsible Display Component (`ThinkingDisplay`)

**Location:** `nanobot/cli/ui/thinking_display.py`

```python
class ThinkingDisplay:
    def __init__(self, work_log: WorkLog):
        self.log = work_log
        self.expanded = False
        self.summary = ThinkingSummaryBuilder.generate_summary(log)
        self.details = ThinkingSummaryBuilder.generate_details(log)
    
    def render_collapsed(self) -> str:
        """Render single-line collapsed view.
        
        Output:
        💭 Thinking: <summary> [press SPACE to expand]
        """
        
    def render_expanded(self) -> str:
        """Render multi-line expanded view.
        
        Output:
        💭 Thinking [expanded] [press SPACE to collapse]
           Step 1 🎯 Decision: ...
           Step 2 🔧 Tool: ...
           ...
        """
        
    def toggle(self) -> None:
        """Switch between expanded/collapsed."""
```

### 3. Integration Point in Chat Flow

**Location:** `nanobot/cli/commands.py` (agent command, interactive mode)

**Current flow (line 1701-1703):**
```python
with _thinking_ctx():
    response = await agent_loop.process_direct(...)
_print_agent_response(response, render_markdown=markdown)
```

**New flow:**
```python
with _thinking_ctx():
    response = await agent_loop.process_direct(...)
_print_agent_response(response, render_markdown=markdown)

# NEW: Show thinking logs
thinking_display = await _show_thinking_logs(agent_loop)
await _handle_thinking_toggle(thinking_display)
```

### 4. Input Handling

**New function:** `_handle_thinking_toggle(thinking_display)`

```python
async def _handle_thinking_toggle(display: ThinkingDisplay) -> None:
    """Wait for user to toggle thinking view.
    
    - Shows collapsed by default
    - SPACE: toggle expanded/collapsed
    - Any other input: continue to next prompt
    """
    while True:
        key = await async_input()  # Non-blocking key read
        
        if key == " ":  # Space bar
            display.toggle()
            console.clear_line()
            console.print(display.render())
        else:
            # Put key back in buffer, continue to next prompt
            break
```

### 5. State Tracking

**Per-message state:**
```python
# In run_interactive():
thinking_states = {}  # message_index -> expanded/collapsed

# After response:
msg_index = len(messages)
thinking_states[msg_index] = display.expanded
```

## Data Flow

```
User input
    ↓
process_direct() runs
    ↓
WorkLog entries created in DB
    ↓
Agent returns response text
    ↓
_print_agent_response() displays answer
    ↓
_show_thinking_logs():
  - Fetch latest WorkLog from WorkLogManager
  - Generate summary
  - Render collapsed state
    ↓
User presses SPACE to expand
    ↓
_handle_thinking_toggle():
  - Fetch detail entries
  - Re-render expanded
    ↓
User presses any other key
    ↓
Continue to next prompt
```

## UI Examples

### Scenario 1: Simple Question

```
User: What's a good project structure?

🤖 nanobot
Here's a recommended structure...

💭 Thinking: Selected model, generated response [SPACE]
```

Expanded:
```
💭 Thinking [↓]
   Step 1 🎯 Decision: Need to select appropriate model complexity
   Step 2 🎯 Decision: Medium tier sufficient for code generation
   Step 3 🔧 Tool: LLM call (claude-sonnet) → 2.3s, 95% confidence

[Press any key to continue...]
```

### Scenario 2: Multi-Bot Room Creation

```
User: Set up a project coordination room with researcher and coder

🤖 nanobot
Coordination room created with researcher and coder ready for collaboration.

💭 Thinking: Created room, invited 2 bots [SPACE]
```

Expanded:
```
💭 Thinking [↓]
   Step 1 🎯 Decision: Multi-bot task requires coordination room
   Step 2 🔧 Tool: create_room("project-coord", type="coordination")
   Step 3 🔧 Tool: invite_bot("researcher") → success
   Step 4 🔧 Tool: invite_bot("coder") → success
   Step 5 ✅ Complete: All bots ready

[Press any key to continue...]
```

### Scenario 3: Tool Execution with Error Recovery

```
User: Analyze the config file

🤖 nanobot
Configuration analysis complete. Found 3 optimization opportunities...

💭 Thinking: Executed 3 tools, fixed encoding issue [SPACE]
```

Expanded:
```
💭 Thinking [↓]
   Step 1 🎯 Decision: Need to read and analyze config
   Step 2 🔧 Tool: read_file("config.json") → UTF-8 error
   Step 3 🔄 Correction: Retry with encoding='utf-8'
   Step 4 🔧 Tool: read_file("config.json", encoding='utf-8') → success
   Step 5 🔧 Tool: analyze_structure() → 3 issues found
   Step 6 ✅ Complete: Analysis ready

[Press any key to continue...]
```

## Implementation Steps

### Phase 1: Core Components (Week 1) ✅ COMPLETE
- [x] Create `ThinkingSummaryBuilder` class
   - [x] Summary generation logic
   - [x] Detail extraction from entries
   - [x] Bot filtering for multi-agent
   
- [x] Create `ThinkingDisplay` component
   - [x] Collapsed/expanded rendering
   - [x] Toggle state management
   - [x] Icon/formatting utilities
   
- [x] Create `InputHandler` for async key reading
   - [x] Cross-platform support (Unix/Windows/macOS)
   - [x] Non-blocking single keypress detection
   
- [x] Comprehensive test suite (15 tests, all passing)

### Phase 2: Integration (Week 2) ✅ COMPLETE
- [x] Create `_show_thinking_logs()` function
   - [x] Fetch work log from manager
   - [x] Initialize display
   - [x] Handle render/refresh
   
- [x] Create `_handle_thinking_toggle()` for input
   - [x] Non-blocking key reading
   - [x] SPACE bar detection
   - [x] Line clearing and re-render
   
- [x] Update agent command flow
   - [x] Insert thinking display after response (single message mode)
   - [x] Insert thinking display after response (interactive mode)
   - [x] Wire up toggle handling
   
- [x] Comprehensive integration tests (13 tests, all passing)
   - [x] Manager to display workflow
   - [x] Async toggle functionality
   - [x] Display rendering with proper formatting
   - [x] User interaction flow

### Phase 3: Polish (Week 3)
- [ ] State tracking across messages
- [ ] Keyboard escape sequences
- [ ] Color/icon consistency
- [ ] Edge cases (empty logs, errors, multi-bot)
- [ ] Testing with different room types

### Phase 4: Enhancements (Future)
- [ ] `/thinking on|off` global toggle
- [ ] `--thinking` CLI flag (always on/off)
- [ ] Filter by bot in display
- [ ] Timeline view of decisions
- [ ] Confidence/timing metrics

## Dependencies & Changes

### New Files
- `nanobot/cli/ui/thinking_summary.py` (ThinkingSummaryBuilder)
- `nanobot/cli/ui/thinking_display.py` (ThinkingDisplay)
- `nanobot/cli/ui/input_handler.py` (async key reading)

### Modified Files
- `nanobot/cli/commands.py` - agent command integration
- `nanobot/cli/ui/__init__.py` - exports

### No Breaking Changes
- Backward compatible (can be toggled off)
- Existing commands unaffected
- Work log format unchanged

## Testing Strategy

### Unit Tests
- Summary generation from various log entries
- Collapsed/expanded rendering
- State toggling

### Integration Tests
- Full chat flow with thinking display
- Multi-bot scenarios
- Error cases (no logs, empty logs)
- Keyboard input handling

### Manual Testing
- Single-bot simple questions
- Multi-bot room creation
- Tool chains with errors
- Rapid toggles
- Long-running tasks

## Metrics & Success Criteria

- ✅ Thinking display renders without delay (<100ms)
- ✅ Toggle responds instantly to SPACE keypress
- ✅ Summary generation covers 80%+ of cases well
- ✅ No terminal artifacts or redraw issues
- ✅ Works in both compact and full terminal sizes
- ✅ User research: 70%+ find it helpful for understanding decisions

## Future Enhancements

1. **Streaming thinking** - Show entries as they happen
2. **Filtering** - `/thinking @bot` to see specific bot's logs
3. **Comparison** - Show what different bots decided
4. **Confidence visualization** - Color-code by confidence score
5. **Timeline** - Visual representation of decision flow
6. **Search** - `/thinking search <keyword>` from chat
7. **Export** - Save thinking logs to file

## Open Questions

1. Should thinking always be available or configurable per session?
2. For multi-bot rooms, show all bots or just leader?
3. How many detail lines before scrolling needed?
4. Should expanded state persist across messages?
5. Include metrics (confidence, timing) in collapsed view?

## References

- Current work log implementation: `nanobot/agent/work_log.py`
- Work log manager: `nanobot/agent/work_log_manager.py`
- Interactive mode: `nanobot/cli/commands.py` (lines 1351-1720)
- UI components: `nanobot/cli/ui/` (StatusBar, TeamRoster, etc.)
