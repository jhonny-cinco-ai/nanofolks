# True Multi-Bot Architecture Implementation Plan

**Status**: Draft  
**Created**: 2026-03-09  
**Author**: Architecture Review  
**Priority**: High  

---

## Executive Summary

This document outlines the transition from the current "single-bot with multi-bolt-on" architecture to a true multi-bot peer-to-peer system. The current system routes all messages through a single AgentLoop instance (typically "leader"), with multi-bot responses generated as sub-routines. The proposed architecture creates independent bot instances that can operate in parallel, share room context, and coordinate without bottlenecks.

**Key Benefits:**
- Independent bot instances with isolated execution
- Scalable architecture (add bots without core changes)
- Room-centric sessions (shared across bots)
- Peer-to-peer bot coordination
- Cleaner separation of concerns
- Better testing and debugging capabilities

**Estimated Timeline**: 8-12 days (see detailed breakdown below)

---

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Proposed Architecture](#proposed-architecture)
3. [Implementation Phases](#implementation-phases)
4. [Migration Strategy](#migration-strategy)
5. [Testing Approach](#testing-approach)
6. [Timeline and Risks](#timeline-and-risks)

---

## Current Architecture Analysis

### Component Overview

#### 1. AgentLoop (`agent/loop.py`)

**Current Design:**
- Single bot instance per AgentLoop
- Takes `bot_name` parameter (defaults to "leader")
- Contains multi-bolt-on logic for parallel responses

**Key Legacy Patterns:**

```python
# Line 82-102: Single bot identity
def __init__(self, bot_name: str = "leader", ...):
    self.bot_name = bot_name  # ONE bot per instance
    self.reasoning_config = get_reasoning_config(self.bot_name)
```

```python
# Lines 929-1113: Multi-bot as sub-routine
async def _handle_multi_bot_response(self, msg, dispatch_result, session):
    # Called FROM a single bot's AgentLoop
    # Not truly independent bot instances
    generator = MultiBotResponseGenerator(...)
    responses = await generator.generate_responses(...)
```

**Problem:** Multi-bot logic is embedded within a single bot's execution context, creating coupling and preventing true parallelism.

#### 2. BotDispatch (`bots/dispatch.py`)

**Current Design:**
- Implements "Leader-First" routing
- 5 dispatch modes: LEADER_FIRST, DIRECT_BOT, DM, MULTI_BOT, TEAM_CONTEXT

**Key Legacy Pattern:**

```python
# Lines 153-163: Default routes through leader
return DispatchResult(
    target=DispatchTarget.LEADER_FIRST,
    primary_bot="leader",
    secondary_bots=secondary,
    reason="Default: Leader coordinates response"
)
```

**Problem:** All messages funnel through leader by default, creating a bottleneck.

#### 3. MultiBotResponseGenerator (`agent/multi_bot_generator.py`)

**Current Design:**
- Generates parallel responses from multiple bots
- Builds communal context with bot identities
- Called as a sub-routine within AgentLoop

**Key Code:**

```python
# Lines 100-168: Parallel generation
async def generate_responses(self, user_message, bot_names, mode, ...):
    tasks = [
        self._generate_single_response(bot_name, ...)
        for bot_name in bot_names
    ]
    responses = await asyncio.gather(*tasks)
```

**Problem:** Responses are generated in isolation without true bot instances or shared state.

#### 4. RoomManager (`bots/room_manager.py`)

**Current Design:**
- Manages rooms with bot participants
- Supports DM rooms for bot-to-bot communication
- Already multi-bot aware

**Good Pattern:**

```python
# Lines 185-226: DM room support
def get_or_create_dm_room(self, bots: List[str], ...):
    room_id = self._generate_dm_room_id(bots)
    # Creates persistent DM room for bot coordination
```

**Status:** Already aligned with multi-bot architecture.

#### 5. BotCoordinator (`bots/coordinator.py`)

**Current Design:**
- Fleet coordination with task tracking
- Monitor loop for stuck tasks
- Designed for multi-bot from start

**Good Pattern:**

```python
# Lines 169-202: Monitor loop
async def _monitor_loop(self):
    # Monitors team routines and reassigns stuck tasks
    # Already designed for multi-bot coordination
```

**Status:** Already aligned with multi-bot architecture.

---

### Current Message Flow

```
User Message
    ↓
MessageBus (inbound)
    ↓
AgentLoop (leader instance)
    ├─ Check dispatch mode
    ├─ If MULTI_BOT or TEAM_CONTEXT:
    │   ├─ Create MultiBotResponseGenerator
    │   ├─ Generate parallel responses (sub-routine)
    │   └─ Combine and return
    └─ Else:
        └─ Process as single bot
    ↓
MessageBus (outbound)
    ↓
User
```

**Problems:**
1. Single AgentLoop instance processes all messages
2. Multi-bot responses lack true bot instances
3. No shared session state across bots
4. Leader is a bottleneck for all coordination

---

## Proposed Architecture

### Core Concept: Fleet of Independent Bots

Instead of one AgentLoop handling multiple bots as sub-routines, create a fleet of independent AgentLoop instances, each representing a single bot. An orchestrator routes messages to appropriate bots without being a bot itself.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator (NEW)                        │
│  - No bot identity                                           │
│  - Routes messages to bots                                   │
│  - Manages room context                                      │
│  - Coordinates bot fleet                                     │
└─────────────────────────────────────────────────────────────┘
         ↓              ↓              ↓              ↓
    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
    │ leader │    │ coder  │    │research│    │creative│
    │AgentLoop│   │AgentLoop│   │AgentLoop│   │AgentLoop│
    │        │    │        │    │        │    │        │
    │ - Tools│    │ - Tools│    │ - Tools│    │ - Tools│
    │ - Memory│   │ - Memory│   │ - Memory│   │ - Memory│
    └────────┘    └────────┘    └────────┘    └────────┘
         ↓              ↓              ↓              ↓
    ┌─────────────────────────────────────────────────────────┐
    │              RoomSessionManager (NEW)                    │
    │  - One session per room                                 │
    │  - Shared across all bots in room                       │
    │  - Persistent conversation history                      │
    └─────────────────────────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────────────────────────┐
    │              BotCoordinationChannel (NEW)                │
    │  - Real-time bot-to-bot messaging                       │
    │  - Insight sharing                                       │
    │  - Task coordination                                     │
    └─────────────────────────────────────────────────────────┘
```

### New Components

#### 1. BotFleet (`bots/fleet.py`)

**Purpose:** Manages all active bot instances.

**Responsibilities:**
- Start/stop bot instances
- Route messages to specific bots
- Broadcast messages to multiple bots
- Track bot health and status

**Key Methods:**

```python
class BotFleet:
    """Manages all active bot instances."""
    
    def __init__(self, workspace, provider, config):
        self.bots: Dict[str, AgentLoop] = {}
        self.orchestrator = None
        self.bus = MessageBus()
        
    async def start_bot(self, bot_name: str) -> AgentLoop:
        """Start a bot instance."""
        if bot_name in self.bots:
            return self.bots[bot_name]
        
        bot = AgentLoop(
            bot_name=bot_name,
            bus=self.bus,
            provider=self.provider,
            workspace=self.workspace,
            session_manager=self.session_manager,  # Shared!
            ...
        )
        self.bots[bot_name] = bot
        await bot.run()
        return bot
    
    async def stop_bot(self, bot_name: str) -> None:
        """Stop a bot instance."""
        if bot_name in self.bots:
            await self.bots[bot_name].stop()
            del self.bots[bot_name]
    
    async def broadcast_to_bots(
        self, 
        bot_names: List[str],
        message: MessageEnvelope
    ) -> List[MessageEnvelope]:
        """Send message to multiple bots in parallel."""
        tasks = [
            self.bots[bot_name].process_message(message)
            for bot_name in bot_names
            if bot_name in self.bots
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_active_bots(self) -> List[str]:
        """Get list of active bot names."""
        return list(self.bots.keys())
```

#### 2. Orchestrator (`agent/orchestrator.py`)

**Purpose:** Routes messages to bots WITHOUT being a bot itself.

**Responsibilities:**
- Receive messages from bus
- Determine dispatch strategy
- Route to appropriate bot(s)
- Combine responses when needed
- Manage room context

**Key Methods:**

```python
class Orchestrator:
    """Routes messages to bots without being a bot itself."""
    
    def __init__(self, fleet: BotFleet, room_manager: RoomManager):
        self.fleet = fleet
        self.room_manager = room_manager
        self.dispatch = BotDispatch()
        self.response_combiner = ResponseCombiner()
        
    async def process_message(self, msg: MessageEnvelope) -> MessageEnvelope:
        """Route message to appropriate bot(s)."""
        
        # Get room context
        room = self.room_manager.get_room(msg.room_id)
        
        # Determine dispatch strategy
        dispatch_result = self.dispatch.dispatch_message(
            message=msg.content,
            room=room,
            is_dm=False
        )
        
        # Route based on dispatch mode
        if dispatch_result.target == DispatchTarget.DIRECT_BOT:
            # Single bot handles it
            return await self.fleet.bots[dispatch_result.primary_bot].process_message(msg)
        
        elif dispatch_result.target in [DispatchTarget.MULTI_BOT, DispatchTarget.TEAM_CONTEXT]:
            # Multiple bots respond in parallel
            responses = await self.fleet.broadcast_to_bots(
                dispatch_result.bots,
                msg
            )
            return self.response_combiner.combine(responses, dispatch_result.mode)
        
        elif dispatch_result.target == DispatchTarget.LEADER_FIRST:
            # Leader coordinates (but as independent bot)
            return await self.fleet.bots["leader"].process_message(msg)
        
        else:  # DM
            return await self.fleet.bots[dispatch_result.primary_bot].process_message(msg)
    
    async def run(self) -> None:
        """Run the orchestrator loop."""
        self._running = True
        while self._running:
            msg = await self.bus.consume_inbound()
            response = await self.process_message(msg)
            if response:
                await self.bus.publish_outbound(response)
```

#### 3. RoomSessionManager (`session/room_session_manager.py`)

**Purpose:** Manages sessions per room, not per bot.

**Responsibilities:**
- One session per room
- Shared across all bots in room
- Persistent conversation history
- Room-level memory context

**Key Methods:**

```python
class RoomSessionManager:
    """Manages sessions per room, not per bot."""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.room_sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        
    async def get_session(self, room_id: str) -> Session:
        """Get session for a room (shared by all bots in room)."""
        async with self._lock:
            if room_id not in self.room_sessions:
                self.room_sessions[room_id] = Session(
                    room_id=room_id,
                    workspace=self.workspace
                )
            return self.room_sessions[room_id]
    
    async def save_session(self, room_id: str) -> None:
        """Persist session to disk."""
        async with self._lock:
            if room_id in self.room_sessions:
                await self.room_sessions[room_id].save()
```

#### 4. BotCoordinationChannel (`bots/coordination.py`)

**Purpose:** Real-time bot-to-bot communication.

**Responsibilities:**
- Broadcast insights between bots
- Share discoveries and findings
- Coordinate task execution
- Persistent DM room history

**Key Methods:**

```python
class BotCoordinationChannel:
    """Real-time bot-to-bot communication."""
    
    def __init__(self, room_manager: RoomManager, bus: MessageBus):
        self.room_manager = room_manager
        self.bus = bus
        
    async def broadcast_insight(
        self,
        from_bot: str,
        insight: str,
        relevant_bots: List[str],
        insight_type: str = "discovery"
    ) -> None:
        """Bot shares insight with other bots."""
        for bot_name in relevant_bots:
            if bot_name == from_bot:
                continue
            
            # Get or create DM room
            room = self.room_manager.get_or_create_dm_room([from_bot, bot_name])
            
            # Log message to DM room
            self.room_manager.log_dm_message(
                sender_bot=from_bot,
                recipient_bot=bot_name,
                content=insight,
                message_type=insight_type
            )
            
            # Also send via bus for real-time notification
            await self.bus.publish_outbound(MessageEnvelope(
                channel="internal",
                chat_id=f"dm-{from_bot}-{bot_name}",
                content=insight,
                bot_name=from_bot,
                metadata={"type": "coordination", "insight_type": insight_type}
            ))
```

#### 5. ResponseCombiner (`agent/response_combiner.py`)

**Purpose:** Combines multiple bot responses into cohesive output.

**Responsibilities:**
- Format multi-bot responses
- Add bot identifiers (emoji, color)
- Handle errors gracefully
- Maintain response ordering

**Key Methods:**

```python
class ResponseCombiner:
    """Combines multiple bot responses into cohesive output."""
    
    BOT_EMOJIS = {
        "leader": "👑",
        "researcher": "📊",
        "coder": "💻",
        "social": "📱",
        "creative": "🎨",
        "auditor": "🔍",
    }
    
    def combine(
        self, 
        responses: List[MessageEnvelope],
        mode: DispatchTarget
    ) -> MessageEnvelope:
        """Combine multiple bot responses."""
        
        # Filter out errors
        valid_responses = [
            r for r in responses 
            if not isinstance(r, Exception) and r.content
        ]
        
        if not valid_responses:
            return MessageEnvelope(
                content="❌ All bots failed to respond",
                bot_name="system"
            )
        
        # Format based on mode
        if mode == DispatchTarget.MULTI_BOT:
            return self._format_group_response(valid_responses)
        elif mode == DispatchTarget.TEAM_CONTEXT:
            return self._format_context_response(valid_responses)
        else:
            return valid_responses[0]  # Single response
    
    def _format_group_response(self, responses: List[MessageEnvelope]) -> MessageEnvelope:
        """Format @all style response."""
        parts = ["🎭 **Multi-Bot Response**\n"]
        
        for response in responses:
            emoji = self.BOT_EMOJIS.get(response.bot_name, "🤖")
            parts.append(f"{emoji} **@{response.bot_name}:**")
            parts.append(response.content)
            parts.append("")
        
        return MessageEnvelope(
            content="\n".join(parts),
            bot_name="multi",
            metadata={"responding_bots": [r.bot_name for r in responses]}
        )
```

---

### Refactored AgentLoop

**Changes:**
- Remove multi-bolt-on logic
- Accept shared session manager
- Process messages as single bot only
- No dispatch detection

**Before (Current):**

```python
class AgentLoop:
    def __init__(self, bot_name: str = "leader", ...):
        self.bot_name = bot_name
        # ... multi-bolt-on logic ...
        
    async def _process_message(self, msg):
        # Check for multi-bot dispatch
        dispatch_result = self._check_multi_bot_dispatch(msg, session)
        if dispatch_result:
            return await self._handle_multi_bot_response(msg, dispatch_result, session)
        # ... normal processing ...
```

**After (Proposed):**

```python
class AgentLoop:
    """Single bot agent - no multi-bolt-on logic."""
    
    def __init__(
        self, 
        bot_name: str,
        bus: MessageBus,
        provider: LLMProvider,
        session_manager: RoomSessionManager,  # Shared!
        ...
    ):
        self.bot_name = bot_name
        self.bus = bus
        self.provider = provider
        self.session_manager = session_manager
        # ... single bot setup ...
        
    async def process_message(self, msg: MessageEnvelope) -> MessageEnvelope:
        """Process a message as THIS bot only."""
        
        # Get room session (shared across bots)
        session = await self.session_manager.get_session(msg.room_id)
        
        # Build context
        context = await self._build_context(msg, session)
        
        # Call LLM
        response = await self.provider.chat(
            messages=context,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Execute tools if needed
        if response.tool_calls:
            await self._execute_tools(response.tool_calls)
        
        # Save to shared session
        session.add_message("user", msg.content)
        session.add_message("assistant", response.content)
        await self.session_manager.save_session(msg.room_id)
        
        return MessageEnvelope(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=response.content,
            bot_name=self.bot_name,
            room_id=msg.room_id
        )
    
    # REMOVED: _check_multi_bot_dispatch
    # REMOVED: _handle_multi_bot_response
```

---

## Implementation Phases

### Phase 1: Extract Orchestrator (Days 1-2)

**Goal:** Create Orchestrator class and move dispatch logic from AgentLoop.

**Tasks:**

1. **Create Orchestrator class** (`agent/orchestrator.py`)
   - [ ] Define class structure
   - [ ] Implement `process_message()` method
   - [ ] Implement `run()` loop
   - [ ] Add error handling

2. **Create ResponseCombiner** (`agent/response_combiner.py`)
   - [ ] Implement `combine()` method
   - [ ] Add formatting logic for different modes
   - [ ] Handle errors gracefully

3. **Update BotDispatch** (`bots/dispatch.py`)
   - [ ] Keep existing logic (already good)
   - [ ] Add method to get all bots for a room
   - [ ] Add method to check bot availability

4. **Create integration tests**
   - [ ] Test single bot routing
   - [ ] Test multi-bot routing
   - [ ] Test error handling

**Files to Create:**
- `nanofolks/agent/orchestrator.py`
- `nanofolks/agent/response_combiner.py`

**Files to Modify:**
- `nanofolks/bots/dispatch.py` (minor updates)

**Testing:**
```bash
# Test orchestrator routing
pytest tests/test_orchestrator.py -v

# Test response combining
pytest tests/test_response_combiner.py -v
```

**Success Criteria:**
- Orchestrator can route messages to bots
- ResponseCombiner formats multi-bot responses correctly
- All tests pass

---

### Phase 2: Create Bot Fleet (Days 3-5)

**Goal:** Implement BotFleet manager and start multiple AgentLoop instances.

**Tasks:**

1. **Create BotFleet class** (`bots/fleet.py`)
   - [ ] Implement `start_bot()` method
   - [ ] Implement `stop_bot()` method
   - [ ] Implement `broadcast_to_bots()` method
   - [ ] Add health monitoring

2. **Update AgentLoop initialization**
   - [ ] Accept shared session manager
   - [ ] Accept shared bus
   - [ ] Remove multi-bolt-on logic (temporarily keep for rollback)

3. **Create fleet manager integration**
   - [ ] Initialize fleet on startup
   - [ ] Start default bots (leader, coder, researcher, etc.)
   - [ ] Add bot lifecycle management

4. **Create integration tests**
   - [ ] Test starting multiple bots
   - [ ] Test broadcasting messages
   - [ ] Test bot health monitoring

**Files to Create:**
- `nanofolks/bots/fleet.py`

**Files to Modify:**
- `nanofolks/agent/loop.py` (accept shared dependencies)
- `nanofolks/cli/chat.py` (initialize fleet)

**Testing:**
```bash
# Test fleet management
pytest tests/test_bot_fleet.py -v

# Test multi-bot execution
pytest tests/test_multi_bot_execution.py -v
```

**Success Criteria:**
- Multiple AgentLoop instances can run simultaneously
- Fleet can broadcast messages to multiple bots
- Bots can be started/stopped dynamically

---

### Phase 3: Room-Centric Sessions (Days 6-8)

**Goal:** Refactor session manager to be room-based instead of bot-based.

**Tasks:**

1. **Create RoomSessionManager** (`session/room_session_manager.py`)
   - [ ] Implement `get_session()` method
   - [ ] Implement `save_session()` method
   - [ ] Add session persistence
   - [ ] Add session cleanup

2. **Update Session model**
   - [ ] Add `room_id` field
   - [ ] Add `participants` field
   - [ ] Update serialization

3. **Update AgentLoop to use RoomSessionManager**
   - [ ] Replace `self.sessions` with shared manager
   - [ ] Update context building to use room session
   - [ ] Update message saving to room session

4. **Create migration script**
   - [ ] Convert existing sessions to room-based
   - [ ] Preserve conversation history
   - [ ] Test migration on sample data

5. **Create integration tests**
   - [ ] Test session sharing across bots
   - [ ] Test session persistence
   - [ ] Test session cleanup

**Files to Create:**
- `nanofolks/session/room_session_manager.py`
- `scripts/migrate_sessions_to_rooms.py`

**Files to Modify:**
- `nanofolks/session/manager.py` (update Session model)
- `nanofolks/agent/loop.py` (use RoomSessionManager)
- `nanofolks/session/dual_mode.py` (update factory)

**Testing:**
```bash
# Test room session manager
pytest tests/test_room_session_manager.py -v

# Test session sharing
pytest tests/test_session_sharing.py -v

# Run migration script
python scripts/migrate_sessions_to_rooms.py --dry-run
```

**Success Criteria:**
- Sessions are shared across bots in same room
- Conversation history persists across bot switches
- Migration script works without data loss

---

### Phase 4: Remove Multi-Bolt-On Logic (Days 9-10)

**Goal:** Clean up AgentLoop by removing embedded multi-bot logic.

**Tasks:**

1. **Remove from AgentLoop:**
   - [ ] Delete `_check_multi_bot_dispatch()` method
   - [ ] Delete `_handle_multi_bot_response()` method
   - [ ] Remove MultiBotResponseGenerator dependency
   - [ ] Update docstrings

2. **Update imports and dependencies**
   - [ ] Remove unused imports
   - [ ] Update type hints
   - [ ] Clean up __init__.py

3. **Update tests**
   - [ ] Remove tests for deleted methods
   - [ ] Update integration tests
   - [ ] Add new tests for fleet-based multi-bot

4. **Update documentation**
   - [ ] Update architecture docs
   - [ ] Update developer guide
   - [ ] Update API reference

**Files to Modify:**
- `nanofolks/agent/loop.py` (major cleanup)
- `nanofolks/agent/multi_bot_generator.py` (keep for now, may deprecate later)
- `tests/test_agent_loop.py` (update tests)

**Testing:**
```bash
# Run all tests
pytest tests/ -v

# Check for regressions
pytest tests/test_multi_bot_scenarios.py -v
```

**Success Criteria:**
- AgentLoop is clean and focused on single bot
- All multi-bot functionality works via fleet
- No regressions in existing functionality

---

### Phase 5: Enhanced Coordination (Days 11-12)

**Goal:** Implement real-time bot-to-bot communication.

**Tasks:**

1. **Create BotCoordinationChannel** (`bots/coordination.py`)
   - [ ] Implement `broadcast_insight()` method
   - [ ] Implement `request_help()` method
   - [ ] Implement `share_discovery()` method
   - [ ] Add DM room integration

2. **Update AgentLoop to use coordination channel**
   - [ ] Add coordination channel to __init__
   - [ ] Add method to broadcast insights
   - [ ] Add method to receive coordination messages

3. **Create coordination scenarios**
   - [ ] Bot discovers relevant info → shares with others
   - [ ] Bot needs help → requests from relevant bots
   - [ ] Bot completes task → notifies coordinator

4. **Create integration tests**
   - [ ] Test insight broadcasting
   - [ ] Test help requests
   - [ ] Test DM room persistence

**Files to Create:**
- `nanofolks/bots/coordination.py`

**Files to Modify:**
- `nanofolks/agent/loop.py` (add coordination methods)
- `nanofolks/bots/room_manager.py` (enhance DM room support)

**Testing:**
```bash
# Test coordination channel
pytest tests/test_bot_coordination.py -v

# Test DM room integration
pytest tests/test_dm_rooms.py -v
```

**Success Criteria:**
- Bots can broadcast insights to each other
- DM rooms persist coordination history
- Coordination improves response quality

---

## Migration Strategy

### Backward Compatibility

**Approach:** Maintain backward compatibility during transition.

**Strategy:**

1. **Feature Flags**
   ```python
   # config/schema.py
   class FeatureFlags:
       use_fleet_architecture: bool = False  # Default to old behavior
       use_room_sessions: bool = False
       use_orchestrator: bool = False
   ```

2. **Dual Mode Support**
   ```python
   # cli/chat.py
   if config.features.use_fleet_architecture:
       # New architecture
       fleet = BotFleet(...)
       orchestrator = Orchestrator(fleet, room_manager)
       await orchestrator.run()
   else:
       # Old architecture
       agent = AgentLoop(bot_name="leader", ...)
       await agent.run()
   ```

3. **Gradual Rollout**
   - Week 1: Test with feature flags off (old behavior)
   - Week 2: Enable orchestrator (Phase 1)
   - Week 3: Enable fleet (Phase 2)
   - Week 4: Enable room sessions (Phase 3)
   - Week 5: Remove feature flags (Phase 4)

### Data Migration

**Session Migration:**

```python
# scripts/migrate_sessions_to_rooms.py
async def migrate_sessions():
    """Convert bot-based sessions to room-based sessions."""
    
    old_manager = SessionManager(workspace)
    new_manager = RoomSessionManager(workspace)
    
    # For each old session
    for session_id, session in old_manager.sessions.items():
        # Extract room_id from session metadata
        room_id = session.metadata.get("room_id", "general")
        
        # Get or create room session
        room_session = await new_manager.get_session(room_id)
        
        # Copy messages
        for msg in session.messages:
            room_session.add_message(msg["role"], msg["content"])
        
        # Save
        await new_manager.save_session(room_id)
```

### Rollback Plan

**If issues arise:**

1. **Immediate Rollback**
   - Set feature flags to False
   - Restart application
   - Old architecture resumes

2. **Data Rollback**
   - Keep old session files
   - Migration script creates copies
   - Can revert to old sessions

3. **Monitoring**
   - Track error rates
   - Monitor response times
   - Watch for memory leaks

---

## Testing Approach

### Unit Tests

**Test Coverage:**

1. **Orchestrator Tests** (`tests/test_orchestrator.py`)
   ```python
   def test_route_to_single_bot():
       """Test routing to single bot."""
       
   def test_route_to_multiple_bots():
       """Test routing to multiple bots."""
       
   def test_error_handling():
       """Test error handling in routing."""
   ```

2. **BotFleet Tests** (`tests/test_bot_fleet.py`)
   ```python
   def test_start_bot():
       """Test starting a bot instance."""
       
   def test_broadcast_to_bots():
       """Test broadcasting to multiple bots."""
       
   def test_bot_health_monitoring():
       """Test health monitoring."""
   ```

3. **RoomSessionManager Tests** (`tests/test_room_session_manager.py`)
   ```python
   def test_get_session():
       """Test getting room session."""
       
   def test_session_sharing():
       """Test session sharing across bots."""
       
   def test_session_persistence():
       """Test session persistence."""
   ```

### Integration Tests

**Test Scenarios:**

1. **Multi-Bot Conversation** (`tests/integration/test_multi_bot_conversation.py`)
   ```python
   async def test_all_bots_respond():
       """Test @all triggers all bots to respond."""
       user_msg = "@all what do you think?"
       responses = await orchestrator.process_message(user_msg)
       assert len(responses) == 6  # All 6 bots
       
   async def test_team_context_routing():
       """Test @team routes to relevant bots."""
       user_msg = "@team analyze this code"
       responses = await orchestrator.process_message(user_msg)
       assert "coder" in [r.bot_name for r in responses]
       assert "auditor" in [r.bot_name for r in responses]
   ```

2. **Session Sharing** (`tests/integration/test_session_sharing.py`)
   ```python
   async def test_session_shared_across_bots():
       """Test session is shared across bots in same room."""
       room_id = "test-room"
       
       # Bot 1 processes message
       await bot1.process_message(MessageEnvelope(
           content="Hello",
           room_id=room_id
       ))
       
       # Bot 2 should see the message
       session = await session_manager.get_session(room_id)
       assert len(session.messages) == 2  # user + assistant
   ```

3. **Bot Coordination** (`tests/integration/test_bot_coordination.py`)
   ```python
   async def test_insight_broadcasting():
       """Test bot broadcasts insight to others."""
       await coder.broadcast_insight(
           insight="Found a security vulnerability",
           relevant_bots=["auditor", "leader"]
       )
       
       # Check DM rooms
       dm_room = room_manager.get_or_create_dm_room(["coder", "auditor"])
       assert len(dm_room.messages) > 0
   ```

### Performance Tests

**Benchmarks:**

1. **Response Time**
   - Single bot: < 2 seconds
   - Multi-bot (3 bots): < 5 seconds
   - Multi-bot (6 bots): < 8 seconds

2. **Memory Usage**
   - Single bot: ~200 MB
   - Fleet (6 bots): ~800 MB
   - No memory leaks over 1 hour

3. **Concurrency**
   - Handle 10 concurrent messages
   - No race conditions
   - No deadlocks

---

## Timeline and Risks

### Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Phase 1: Extract Orchestrator | 2 days | Day 1 | Day 2 |
| Phase 2: Create Bot Fleet | 3 days | Day 3 | Day 5 |
| Phase 3: Room-Centric Sessions | 3 days | Day 6 | Day 8 |
| Phase 4: Remove Multi-Bolt-On Logic | 2 days | Day 9 | Day 10 |
| Phase 5: Enhanced Coordination | 2 days | Day 11 | Day 12 |
| **Total** | **12 days** | | |

### Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|--------------|------------|
| **Breaking existing functionality** | High | Medium | Feature flags, gradual rollout, comprehensive tests |
| **Performance degradation** | Medium | Low | Performance benchmarks, profiling, optimization |
| **Memory leaks in fleet** | High | Medium | Health monitoring, cleanup routines, leak detection |
| **Session migration data loss** | Critical | Low | Backup before migration, dry-run mode, rollback plan |
| **Coordination complexity** | Medium | Medium | Start simple, iterate based on usage patterns |
| **Team learning curve** | Low | High | Documentation, code comments, pair programming |

### Success Metrics

**Quantitative:**
- [ ] All existing tests pass
- [ ] New test coverage > 80%
- [ ] Response time within benchmarks
- [ ] Memory usage within limits
- [ ] Zero data loss during migration

**Qualitative:**
- [ ] Code is cleaner and more maintainable
- [ ] Bots can operate independently
- [ ] Room context is properly shared
- [ ] Coordination improves response quality
- [ ] Architecture is extensible for future features

---

## Appendix A: File Structure

### New Files

```
nanofolks/
├── agent/
│   ├── orchestrator.py           # NEW: Routes messages to bots
│   └── response_combiner.py      # NEW: Combines multi-bot responses
├── bots/
│   ├── fleet.py                  # NEW: Manages bot instances
│   └── coordination.py           # NEW: Bot-to-bot communication
└── session/
    └── room_session_manager.py   # NEW: Room-based sessions

scripts/
└── migrate_sessions_to_rooms.py  # NEW: Migration script

tests/
├── test_orchestrator.py          # NEW
├── test_bot_fleet.py             # NEW
├── test_room_session_manager.py  # NEW
├── test_response_combiner.py     # NEW
└── test_bot_coordination.py      # NEW
```

### Modified Files

```
nanofolks/
├── agent/
│   └── loop.py                   # MODIFIED: Remove multi-bolt-on logic
├── bots/
│   ├── dispatch.py               # MODIFIED: Minor updates
│   └── room_manager.py           # MODIFIED: Enhanced DM support
├── session/
│   ├── manager.py                # MODIFIED: Update Session model
│   └── dual_mode.py              # MODIFIED: Update factory
└── cli/
    └── chat.py                   # MODIFIED: Initialize fleet
```

---

## Appendix B: Configuration Schema

```python
# config/schema.py

class FeatureFlags:
    """Feature flags for gradual rollout."""
    
    use_fleet_architecture: bool = False
    use_room_sessions: bool = False
    use_orchestrator: bool = False
    use_bot_coordination: bool = False

class FleetConfig:
    """Configuration for bot fleet."""
    
    auto_start_bots: List[str] = ["leader", "coder", "researcher"]
    max_concurrent_bots: int = 10
    bot_health_check_interval: int = 30  # seconds
    bot_timeout: int = 60  # seconds

class OrchestratorConfig:
    """Configuration for orchestrator."""
    
    default_routing: str = "leader_first"  # or "direct", "smart"
    max_parallel_bots: int = 6
    response_timeout: int = 30  # seconds

class CoordinationConfig:
    """Configuration for bot coordination."""
    
    enable_insight_broadcast: bool = True
    enable_help_requests: bool = True
    dm_room_retention_days: int = 30
```

---

## Appendix C: Example Usage

### Starting the Fleet

```python
# cli/chat.py

from nanofolks.bots.fleet import BotFleet
from nanofolks.agent.orchestrator import Orchestrator
from nanofolks.session.room_session_manager import RoomSessionManager

async def main():
    # Initialize components
    session_manager = RoomSessionManager(workspace)
    fleet = BotFleet(workspace, provider, config)
    
    # Start default bots
    for bot_name in config.fleet.auto_start_bots:
        await fleet.start_bot(bot_name)
    
    # Create orchestrator
    orchestrator = Orchestrator(fleet, room_manager)
    
    # Run
    await orchestrator.run()
```

### Broadcasting to Multiple Bots

```python
# Example: User says "@all what do you think?"

# Orchestrator receives message
msg = MessageEnvelope(
    content="@all what do you think?",
    room_id="general"
)

# Dispatch determines MULTI_BOT mode
dispatch_result = dispatch.dispatch_message(msg.content, room)

# Fleet broadcasts to all bots
responses = await fleet.broadcast_to_bots(
    bot_names=["leader", "coder", "researcher", "creative", "social", "auditor"],
    message=msg
)

# ResponseCombiner formats output
combined = response_combiner.combine(responses, DispatchTarget.MULTI_BOT)

# Output:
# 🎭 **Multi-Bot Response**
# 
# 👑 **@leader:**
# I think we should consider all perspectives...
# 
# 💻 **@coder:**
# From a technical standpoint...
# 
# 📊 **@researcher:**
# Based on the data...
```

### Bot Coordination

```python
# Example: Coder discovers security issue

# Inside AgentLoop (coder)
async def process_message(self, msg):
    # ... analyze code ...
    
    if security_issue_detected:
        # Broadcast to relevant bots
        await self.coordination_channel.broadcast_insight(
            from_bot="coder",
            insight=f"Security vulnerability found in {file_path}",
            relevant_bots=["auditor", "leader"],
            insight_type="security"
        )
    
    # Continue normal processing
    return response
```

---

## Conclusion

This implementation plan provides a clear path from the current single-bot-with-multi-bolt-on architecture to a true multi-bot peer-to-peer system. The phased approach ensures minimal disruption while delivering significant architectural improvements.

**Key Takeaways:**
1. Independent bot instances eliminate bottlenecks
2. Room-centric sessions enable proper context sharing
3. Orchestrator provides clean separation of concerns
4. Coordination channel enables real-time bot collaboration
5. Feature flags ensure safe rollout

**Next Steps:**
1. Review and approve this plan
2. Set up feature flags in config
3. Begin Phase 1 implementation
4. Monitor progress and adjust timeline as needed

---

**Document History:**
- 2026-03-09: Initial draft created
- [Future dates will be added as plan evolves]
