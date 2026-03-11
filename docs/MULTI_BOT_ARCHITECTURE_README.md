# True Multi-Bot Architecture

This document describes the new multi-bot fleet architecture implementation for nanofolks.

## Overview

The new architecture replaces the single-bot-with-multi-bolt-on pattern with a true peer-to-peer multi-bot system where:

- Each bot runs as an independent `AgentLoop` instance
- A `MessageRouter` coordinates message routing without being a bot itself
- A `BotFleet` manages all bot instances
- A `RoomSessionManager` provides room-centric sessions shared across bots
- A `BotCoordinationChannel` enables real-time bot-to-bot communication

## Architecture Components

### 1. ResponseCombiner (`agent/response_combiner.py`)

Combines multiple bot responses into cohesive output.

```python
from nanofolks.agent.response_combiner import ResponseCombiner

combiner = ResponseCombiner()
result = combiner.combine(responses, DispatchTarget.MULTI_BOT)
```

**Features:**
- Multi-bot and team context formatting
- Bot emoji and color mappings
- Error handling for failed responses
- Response ordering and deduplication

### 2. MessageRouter (`agent/message_router.py`)

Routes messages to appropriate bot(s) without being a bot itself.

```python
from nanofolks.agent.message_router import MessageRouter

router = MessageRouter(bus, fleet, room_manager)
response = await router.route_message(message)
```

**Features:**
- Single bot routing
- Multi-bot broadcasting
- Room context management
- Error handling and recovery

### 3. BotFleet (`bots/fleet.py`)

Manages multiple independent bot instances.

```python
from nanofolks.bots.fleet import BotFleet

fleet = BotFleet(workspace, provider, bus, session_manager)
await fleet.start()
await fleet.start_bot("leader")
responses = await fleet.broadcast_to_bots(["leader", "coder"], message)
```

**Features:**
- Dynamic bot start/stop
- Health monitoring
- Parallel message broadcasting
- Idle bot cleanup

### 4. RoomSessionManager (`session/room_session_manager.py`)

Manages sessions per room instead of per bot.

```python
from nanofolks.session.room_session_manager import RoomSessionManager

session_manager = RoomSessionManager(workspace)
session = await session_manager.get_session("general")
session.add_message("user", "Hello", bot_name="leader")
```

**Features:**
- Room-centric session storage
- Shared across all bots in a room
- Persistent conversation history
- Participant management

### 5. BotCoordinationChannel (`bots/coordination.py`)

Enables real-time bot-to-bot communication.

```python
from nanofolks.bots.coordination import BotCoordinationChannel, InsightType

coordination = BotCoordinationChannel(room_manager, bus)
await coordination.broadcast_insight(
    from_bot="coder",
    insight="Found a bug",
    relevant_bots=["auditor", "leader"],
    insight_type=InsightType.BUG
)
```

**Features:**
- Broadcast insights
- Request help
- Report security issues
- Persistent DM room history

## Configuration

### Feature Flags

Enable the new architecture in your config:

```yaml
# config.yaml
features:
  use_fleet_architecture: true
  use_room_sessions: true
  use_message_router: true
  use_bot_coordination: true

fleet:
  auto_start_bots:
    - leader
    - coder
    - researcher
  max_concurrent_bots: 10
  idle_timeout_seconds: 300
  enable_leader_first: true
```

## Usage

### Quick Start

```python
from nanofolks.multi_bot_integration import initialize_fleet_architecture
from nanofolks.config.loader import load_config
from nanofolks.providers.factory import create_provider

# Load config
config = load_config()
workspace = config.workspace_path
provider = create_provider(config)

# Initialize fleet
fleet, router = await initialize_fleet_architecture(
    config, workspace, provider
)

# Start routing
await router.run()
```

### Message Flow Example

```python
from nanofolks.bus.events import MessageEnvelope

# User sends: "@all what do you think?"
msg = MessageEnvelope(
    content="@all what do you think?",
    room_id="general",
    channel="cli"
)

# Router determines MULTI_BOT dispatch
response = await router.route_message(msg)

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

### Bot Coordination Example

```python
# Inside AgentLoop (coder bot)
if security_issue_detected:
    await self.coordination_channel.broadcast_insight(
        from_bot="coder",
        insight=f"Security vulnerability in {file_path}",
        relevant_bots=["auditor", "leader"],
        insight_type=InsightType.SECURITY
    )
```

## Migration

### From Existing Sessions

Use the migration script to convert existing sessions:

```bash
# Dry run to see what would be migrated
python scripts/migrate_sessions_to_rooms.py --dry-run

# Actual migration
python scripts/migrate_sessions_to_rooms.py
```

### Gradual Rollout

The architecture supports gradual rollout via feature flags:

1. **Phase 1**: Enable fleet architecture with leader only
   ```yaml
   features:
     use_fleet_architecture: true
   fleet:
     auto_start_bots: ["leader"]
   ```

2. **Phase 2**: Add more bots
   ```yaml
   fleet:
     auto_start_bots: ["leader", "coder", "researcher"]
   ```

3. **Phase 3**: Enable room sessions
   ```yaml
   features:
     use_room_sessions: true
   ```

4. **Phase 4**: Enable coordination
   ```yaml
   features:
     use_bot_coordination: true
   ```

## File Structure

```
nanofolks/
├── agent/
│   ├── response_combiner.py      # NEW: Combines multi-bot responses
│   └── message_router.py          # NEW: Routes messages to bots
├── bots/
│   ├── fleet.py                   # NEW: Manages bot instances
│   └── coordination.py            # NEW: Bot-to-bot communication
├── session/
│   └── room_session_manager.py   # NEW: Room-based sessions
├── config/
│   └── schema.py                  # MODIFIED: Added feature flags
└── multi_bot_integration.py       # NEW: Integration helpers

scripts/
└── migrate_sessions_to_rooms.py   # NEW: Migration script

tests/
└── test_response_combiner.py      # NEW: Tests

examples/
└── cli_fleet_integration_example.py  # NEW: Usage example
```

## API Reference

### ResponseCombiner

- `combine(responses, mode, include_header=True)` - Combine multiple responses
- `combine_with_errors(responses, mode)` - Combine including error details
- `get_bot_emoji(bot_name)` - Get emoji for a bot
- `get_bot_color(bot_name)` - Get color for a bot

### MessageRouter

- `route_message(msg)` - Route message to appropriate bot(s)
- `run()` - Start the router loop
- `stop()` - Stop the router
- `set_current_room(room_id)` - Set current room context
- `get_stats()` - Get router statistics

### BotFleet

- `start_bot(bot_name)` - Start a bot instance
- `stop_bot(bot_name)` - Stop a bot instance
- `broadcast_to_bots(bot_names, message)` - Broadcast to multiple bots
- `get_active_bots()` - Get list of active bots
- `get_fleet_stats()` - Get fleet statistics
- `cleanup_idle_bots(timeout)` - Stop idle bots

### RoomSessionManager

- `get_session(room_id)` - Get room session
- `save_session(room_id)` - Save session to disk
- `add_participant(room_id, bot_name)` - Add bot to room
- `remove_participant(room_id, bot_name)` - Remove bot from room
- `clear_session(room_id)` - Clear session messages
- `list_rooms()` - List all rooms

### BotCoordinationChannel

- `broadcast_insight(from_bot, insight, relevant_bots)` - Broadcast insight
- `request_help(from_bot, help_request, relevant_bots)` - Request help
- `share_discovery(from_bot, discovery, relevant_bots)` - Share discovery
- `report_security_issue(from_bot, issue, severity, relevant_bots)` - Report security
- `get_coordination_history(bot1, bot2)` - Get coordination history

## Testing

Run tests:

```bash
# ResponseCombiner tests
pytest tests/test_response_combiner.py -v

# All tests
pytest tests/ -v
```

## Troubleshooting

### Bots Not Starting

Check logs for errors:
```python
logger.info(f"Active bots: {fleet.get_active_bots()}")
logger.info(f"Fleet stats: {fleet.get_fleet_stats()}")
```

### Session Not Persisting

Ensure RoomSessionManager is properly initialized:
```python
session_manager = RoomSessionManager(workspace)
fleet = BotFleet(..., session_manager=session_manager)
```

### Messages Not Routing

Check feature flags:
```python
from nanofolks.multi_bot_integration import get_multi_bot_components

status = get_multi_bot_components(config)
print(status)
```

## Performance Considerations

- **Memory**: Each bot instance uses ~200MB RAM
- **Latency**: Multi-bot responses take longer (parallel execution)
- **Scaling**: Supports up to 10 concurrent bots (configurable)
- **Cleanup**: Idle bots auto-stop after 5 minutes (configurable)

## Future Enhancements

- [ ] Bot-to-bot direct messaging
- [ ] Dynamic bot spawning based on workload
- [ ] Cross-room bot coordination
- [ ] Bot specialization profiles
- [ ] Advanced routing strategies

## Contributing

When adding new features:

1. Add tests in `tests/`
2. Update this README
3. Add example usage in `examples/`
4. Update feature flags if needed

## License

Same as nanofolks project.
