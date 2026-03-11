# nanofolks Swift Port Plan

**Purpose**: Native macOS implementation leveraging true OS-level integration  
**Scope**: Full parity with Python architecture + deep macOS system control  
**Rationale**: Desktop agent requiring real filesystem, browser, and app automation

**Status**: Python True Multi-Bot Architecture - COMPLETE ✅ | Swift Port - Planning Phase

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        nanofolks Swift App                          │
├─────────────────────────────────────────────────────────────────────┤
│  UI Layer (SwiftUI)                                                 │
│  - Main window, room list, chat view                               │
│  - Bot configuration panels                                         │
│  - Settings & preferences                                           │
├─────────────────────────────────────────────────────────────────────┤
│  Fleet Core (Swift)                                                 │
│  - FleetManager (replaces Agent orchestrator)                       │
│  - Independent bot instances (Actor-based)                          │
│  - MessageRouter & SmartDispatch                                    │
│  - Intent detection & flow routing                                  │
│  - SmartDiscuss (@discuss LLM-based selection)                      │
│  - Memory & embeddings                                              │
├─────────────────────────────────────────────────────────────────────┤
│  System Integration (Swift/macOS APIs)                             │
│  - Filesystem tools (NSWorkspace, FileManager)                     │
│  - Browser automation (Safari + AppleScript)                       │
│  - App control (NSRunningApplication, Accessibility)              │
│  - Shell execution (Process/NSTask)                                 │
│  - Notifications (UserNotifications)                                │
├─────────────────────────────────────────────────────────────────────┤
│  Data Layer (SwiftData/SQLite)                                      │
│  - Room/session persistence                                         │
│  - Message storage                                                   │
│  - Memory store & vector index                                      │
├─────────────────────────────────────────────────────────────────────┤
│  Nanofolks Cloud (Control Plane + LLM Proxy)                        │
│  - Login (OpenAuth or equivalent)                                   │
│  - Entitlements + metering + billing integration (e.g., Polar)      │
│  - Usage ledger + limits (monthly budget + overage)                 │
│  - Provider routing (gateway/router) + model allowlist (5-10 models)│
│  - Minimal user/profile metadata (e.g., Supabase/Convex)            │
├─────────────────────────────────────────────────────────────────────┤
│  External Providers                                                 │
│  - LLM gateways/routers (e.g., Vercel AI Gateway, OpenRouter)        │
│  - Direct LLM providers (OpenAI, Anthropic, etc.)                    │
│  - Experimental/specialized models (optional; later)                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Product & Platform Decisions (v1)

**Distribution**: Direct download from website (not App Store). Plan for notarization, hardened runtime, and an auto-update mechanism (e.g., Sparkle).

**Login**: Required to use the app (because v1 relies on online LLM calls). Design for graceful degradation when backend/provider is unavailable (view history, search local memory, drafts), but block new requests.

**Data philosophy**: Local-first. “Important user data” (agent memory/learning, room history) stays on-device by default. The server stores only what’s needed for auth, billing, metering, and abuse prevention.

**Backend role**: A thin “control plane” + LLM proxy. The macOS app never calls gateway/router or LLM providers directly in v1.

**Provider strategy**:
- Start with a gateway/router behind the proxy (simplifies multi-provider support and failover).
- Curate an allowlist of ~5–10 models (keep UX simple and costs predictable).
- Keep the interface abstract so we can later route directly to providers and/or add specialized/experimental models (including self-hosted options) without changing the client.

**Pricing strategy**:
- Subscription plans include a monthly usage budget (recommend token-based budgets; optionally display “~N standard requests”).
- Optional overage pay-as-you-go after included budget is exhausted (configurable per plan).

**Tenancy**:
- Single-user accounts for v1.
- Future-proof for teams by attaching entitlements/usage to an `account_id` (even if `account_id == user_id` in v1).

---

## Cloud Control Plane (Backend) – Scope for v1

### Why this exists
- Avoid shipping shared provider keys in the macOS app.
- Enforce plans/limits and compute usage consistently.
- Centralize billing state (active/canceled/past-due), abuse prevention, and provider routing.

### Minimal responsibilities
- **Auth**: login + session issuance (access token + refresh token).
- **Device registration**: bind sessions to `device_id`, allow revocation.
- **Entitlements**: plan lookup, included budget, overage setting, rate limits.
- **LLM proxy**: `/chat` and `/embeddings` endpoints; forward requests; record usage.
- **Metering**: append-only usage ledger + periodic rollups; emit billing events.
- **Admin** (minimal): user search, entitlement status, usage this period, revoke device, disable account.

### Suggested API surface (v1)
- `POST /auth/login` (or OAuth callback flow)
- `POST /auth/refresh`
- `POST /devices/register`
- `GET /me`
- `GET /me/entitlements`
- `GET /me/usage`
- `POST /llm/chat`
- `POST /llm/embeddings`
- `POST /webhooks/billing` (e.g., Polar webhook endpoint)
- `GET /admin/users?q=...`
- `GET /admin/users/:id`
- `POST /admin/users/:id/disable`
- `POST /admin/devices/:id/revoke`

### Data model (v1, team-ready)
- `accounts`: id, created_at, status, billing_customer_id
- `users`: id, email, created_at, status
- `memberships`: account_id, user_id, role (`owner` for v1)
- `devices`: id, account_id, user_id, created_at, last_seen_at, revoked_at
- `entitlements`: account_id, plan_id, period_start, period_end, included_budget, overage_enabled
- `usage_ledger`: id, account_id, user_id, device_id, ts, model, input_tokens, output_tokens, total_tokens, request_id, status
- `usage_rollups`: account_id, period_start, period_end, total_tokens (optional cache)

---

## Swift Layout

### File-Based Modular Bot Architecture

The Swift port uses a **data-driven, file-based bot system** where adding new bots requires **zero code changes** - just create a folder with configuration files.

```
nanofolks-swift/
├── Bots/                              # BOT DEFINITIONS (Data-Driven)
│   ├── _templates/                    # Templates for creating new bots
│   │   ├── template.json              # Base bot template
│   │   └── README.md                  # How to create a bot
│   │
│   ├── leader/                        # Each bot = one folder
│   │   ├── bot.json                   # Core configuration (name, icon, capabilities)
│   │   ├── soul.md                    # Personality & values
│   │   ├── role.md                    # Role definition & responsibilities
│   │   ├── identity.md                # Identity card (SOUL/IDENTITY.md)
│   │   ├── tools.json                 # Tool permissions
│   │   └── reasoning.json             # Reasoning behavior config
│   │
│   ├── coder/                         # Coder bot
│   │   ├── bot.json
│   │   ├── soul.md
│   │   ├── role.md
│   │   └── ...
│   │
│   ├── creative/                      # Creative bot
│   ├── researcher/                    # Researcher bot
│   ├── auditor/                       # Auditor bot
│   └── social/                        # Social bot
│
├── Sources/
│   ├── nanofolks/                     # Main app (SwiftUI)
│   │   ├── App/
│   │   ├── Views/
│   │   ├── ViewModels/
│   │   └── Resources/
│   │
│   ├── Fleet/                         # FLEET MANAGEMENT (replaces Agent/)
│   │   ├── FleetManager.swift         # Manages all bot instances
│   │   ├── MessageRouter.swift        # Routes messages between bots/users
│   │   ├── SmartDispatch.swift        # @discuss intelligent selection
│   │   ├── ResponseCombiner.swift     # Combines multi-bot responses
│   │   └── RoomSessionManager.swift   # Shared room-centric sessions
│   │
│   ├── BotLoader/                     # DYNAMIC BOT LOADING
│   │   ├── BotLoader.swift            # Scans Bots/ folder, loads configs
│   │   ├── BotParser.swift            # Parses bot.json files
│   │   ├── BotValidator.swift         # Validates bot configurations
│   │   ├── BotConfiguration.swift     # Data models for bot configs
│   │   └── BotFactory.swift           # Creates bot instances from config
│   │
│   ├── BotCore/                       # BOT INFRASTRUCTURE (shared)
│   │   ├── BotProtocol.swift          # Protocol all bots implement
│   │   ├── ConcreteBot.swift          # Generic bot implementation
│   │   ├── BotContext.swift           # Context passed to bots
│   │   ├── BotToolsResolver.swift     # Resolves tool permissions
│   │   └── BotReasoningEngine.swift   # Generic reasoning engine
│   │
│   ├── Coordination/                  # BOT-TO-BOT COMMUNICATION
│   │   ├── BotCoordinationChannel.swift
│   │   ├── DMRoomManager.swift
│   │   ├── InsightTypes.swift
│   │   └── CoordinationMessage.swift
│   │
│   ├── Dispatch/                      # MESSAGE DISPATCH
│   │   ├── DispatchTarget.swift       # enum: leader, direct, multi, team, smart_discuss
│   │   ├── BotDispatch.swift          # Dispatch logic
│   │   └── RoomManager.swift
│   │
│   ├── Memory/                        # SHARED MEMORY
│   │   ├── Store.swift
│   │   ├── Embeddings.swift
│   │   ├── VectorIndex.swift
│   │   └── Models.swift
│   │
│   ├── Providers/                     # LLM PROVIDERS
│   │   ├── LLMProvider.swift
│   │   ├── OpenAIProvider.swift
│   │   ├── AnthropicProvider.swift
│   │   └── AppleIntelligenceProvider.swift  # Native Apple LLM
│   │
│   ├── Tools/                         # SHARED TOOLS
│   │   ├── Registry.swift
│   │   ├── Base/
│   │   ├── Permissions.swift
│   │   └── MCP/
│   │
│   ├── SystemControl/                 # macOS INTEGRATION
│   │   ├── Workspace.swift
│   │   ├── Browser.swift
│   │   ├── Filesystem.swift
│   │   ├── Shell.swift
│   │   ├── Accessibility.swift
│   │   ├── AppleScript.swift
│   │   └── Notifications.swift
│   │
│   ├── Security/
│   ├── Routines/
│   ├── Identity/
│   ├── Config/
│   └── Utils/
│
└── Tests/
    └── nanofolks-tests/
```

### Key Architectural Changes

**REMOVED:**
- ❌ `Agent/` folder - No master controller
- ❌ `Bots/Definitions.swift` - No hardcoded bot registry
- ❌ `Bots/Coordinator.swift` - Coordination moved to Fleet/

**ADDED:**
- ✅ `Bots/` at root - File-based bot definitions (data, not code)
- ✅ `Fleet/` - Fleet management layer (replaces Agent)
- ✅ `BotLoader/` - Dynamic loading system
- ✅ `BotCore/` - Shared bot infrastructure

### How Adding a New Bot Works

**Step 1: Create folder and files**
```bash
mkdir Bots/security

# Create bot.json
cat > Bots/security/bot.json << 'EOF'
{
  "name": "security",
  "display_name": "Security Expert",
  "icon": "🔒",
  "description": "Security and compliance specialist",
  "version": "1.0.0",
  "enabled": true,
  "capabilities": {
    "can_audit": true,
    "can_code": false,
    "can_design": false
  },
  "behavior": {
    "response_style": "cautionary",
    "speak_threshold": 0.6,
    "max_response_length": 400
  },
  "tools": ["security.scan", "compliance.check", "vulnerability.assess"]
}
EOF

# Create soul.md
cat > Bots/security/soul.md << 'EOF'
# SOUL - Security Expert

## Core Values
- Security is never optional
- Privacy by design
- Defense in depth

## Communication Style
- Clear about risks
- Provides actionable fixes
- Never alarmist
EOF

# Create role.md
cat > Bots/security/role.md << 'EOF'
# ROLE - Security Expert

## Responsibilities
- Security audits
- Vulnerability assessments
- Compliance reviews
- Privacy guidance
EOF
```

**Step 2: Restart app** - Bot is automatically loaded!

No code changes required. The bot appears immediately with:
- Full personality (from soul.md)
- Defined role (from role.md)
- Tool permissions (from tools.json)
- Behavior config (from bot.json)

### Bot Protocol

```swift
protocol Bot: Actor {
    nonisolated var configuration: BotConfiguration { get }
    nonisolated var name: String { get }
    nonisolated var icon: String { get }
    
    func process(message: Message, context: BotContext) async throws -> Response
    func evaluateUrgency(for message: Message) async -> Double
}

struct BotConfiguration: Codable {
    let name: String
    let display_name: String
    let icon: String
    let description: String
    let enabled: Bool
    var capabilities: BotCapabilities
    var behavior: BotBehavior
    var tools: [String]
    var soul: String?        // Loaded from soul.md
    var role: String?        // Loaded from role.md
    var identity: String?    // Loaded from identity.md
}
```

### Fleet Manager

```swift
actor FleetManager {
    private var activeBots: [String: any Bot] = [:]
    private let botLoader: BotLoader
    private let provider: LLMProvider
    
    // Load all bots from Bots/ folder
    func loadBots() async throws {
        let configs = try await botLoader.loadAllBots()
        
        for config in configs where config.enabled {
            let bot = BotFactory.create(from: config, provider: provider)
            activeBots[config.name] = bot
        }
    }
    
    // Dynamic reload (no restart needed)
    func reloadBots() async throws {
        // Stop current bots
        // Reload configurations
        // Restart with new configs
    }
    
    // Dispatch to selected bots
    func dispatch(message: Message, mode: DispatchMode) async -> [Response] {
        let selectedBots = await selectBots(for: message, mode: mode)
        
        return await withTaskGroup(of: Response.self) { group in
            for bot in selectedBots {
                group.addTask {
                    await bot.process(message: message, context: context)
                }
            }
            // Collect responses...
        }
    }
}
```

---

## V1 Parity Matrix

### Core Runtime & Orchestration

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| **Fleet management** (replaces Agent) | `bots/fleet.py` ✅ COMPLETE | `Fleet/FleetManager.swift` | Manages independent bot instances | Swift actors for concurrency |
| Message routing | `agent/message_router.py` ✅ COMPLETE | `Fleet/MessageRouter.swift` | Central message router | async/await with TaskGroup |
| Intent detection + flow router | `agent/intent_detector.py`, `agent/intent_flow_router.py` | `Fleet/Intent/` | QUICK/FULL flows and cancellation | Swift regex / NaturalLanguage |
| Project state + phases | `agent/project_state.py` | `Fleet/ProjectState.swift` | Persist flow state by room/session | SwiftData persistence |
| Multi-bot coordination | `agent/multi_bot_generator.py`, `bots/coordination.py` ✅ COMPLETE | `Fleet/MultiBot/` | Smart dispatch & coordination | Swift AsyncSequence |
| Tag parsing system | `systems/tag_handler.py` | `Fleet/TagHandler.swift` | `@bot` and `#room` tags | Native Swift string processing |
| SmartDiscuss | `bots/smart_dispatch.py` ✅ COMPLETE | `Fleet/SmartDispatch.swift` | @discuss LLM-based selection | Apple Intelligence framework |

---

### Rooms, Sessions, Messaging, Broker

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| Room manager + mappings | `bots/room_manager.py` | `Rooms/Manager.swift` | Channel↔room mapping | SwiftData @Model |
| Room model | `models/room.py` | `Rooms/Models.swift` | Schema matching | @Model class |
| Room-centric sessions | `session/room_session_manager.py` ✅ NEW | `Rooms/Sessions.swift` | Room-keyed sessions | SQLite.swift |
| CAS storage | `storage/cas_storage.py` | `Storage/CASStorage.swift` | Conflict-free writes | Swift actor + SQLite |
| Per-room broker | `broker/room_broker.py` | `Broker/RoomBroker.swift` | FIFO per room | Swift actor |
| Group commit | `broker/group_commit.py` | `Broker/GroupCommit.swift` | Batch durability | Swift async/await |
| Bus + queue | `bus/*` | `Bus/` | Event bus parity | Combine framework |
| Bot DM rooms | `bots/dm_room_manager.py` | `Rooms/DMRooms.swift` | Persistent DM history | SwiftData |

---

### Bots & Fleet Architecture

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| **File-Based Bot System** | N/A (new) ✅ COMPLETE | `Bots/` folder | Zero-code bot creation | Markdown + JSON configs |
| Bot loader + factory | `bots/dispatch.py` ✅ COMPLETE | `BotLoader/` | Dynamic loading from files | Actor-based concurrent loading |
| Bot protocol + core | `agent/loop.py` ✅ REFACTORED | `BotCore/` | Generic bot implementation | Swift protocol-oriented design |
| Fleet management | `bots/fleet.py` ✅ COMPLETE | `Fleet/FleetManager.swift` | Manages independent bot instances | Swift actors for thread safety |
| Message routing | `agent/message_router.py` ✅ COMPLETE | `Fleet/MessageRouter.swift` | Central message router | async/await with TaskGroup |
| Dispatch logic | `bots/dispatch.py` ✅ MODIFIED | `Dispatch/` | Routing decisions | enum-based dispatch targets |
| **SmartDiscuss** | `bots/smart_dispatch.py` ✅ COMPLETE | `Fleet/SmartDispatch.swift` | LLM-based urgency evaluation | Native Apple LLM framework |
| Bot coordination | `bots/coordination.py` ✅ COMPLETE | `Coordination/` | Bot-to-bot communication | AsyncStream for real-time |
| Room-centric sessions | `session/room_session_manager.py` ✅ COMPLETE | `Rooms/Sessions.swift` | Room-keyed sessions | SwiftData @Model |

---

## File-Based Bot Architecture Benefits

> **Validated by Python Implementation**: The file-based approach was successfully implemented in Python and proved practical for zero-code bot creation. Each bot folder contains configuration files (JSON) and personality definitions (Markdown), enabling rapid customization without code changes.

### Traditional vs. File-Based Approach

| Aspect | Traditional (Hardcoded) | File-Based (New) |
|---|---|---|
| **Adding a bot** | Edit source code, recompile | Create folder + files |
| **Bot customization** | Requires code changes | Edit markdown files |
| **Version control** | Code commits | Data files tracked separately |
| **Community sharing** | Share code | Share bot bundles |
| **Hot reloading** | Requires restart | Can reload without restart |
| **User extensibility** | Limited | Power users can create bots |

### Example: Adding "Security" Bot

**Traditional Approach:**
```swift
// 1. Edit Definitions.swift
enum BotType {
    case leader, coder, creative, researcher, social, auditor
    case security  // <-- Add this
}

// 2. Edit BotFactory.swift
func createBot(_ type: BotType) -> Bot {
    switch type {
    case .security:  // <-- Add case
        return SecurityBot()  // <-- Create new class
    }
}

// 3. Create SecurityBot.swift
class SecurityBot: Bot {  // <-- New file
    override func process(...) { ... }
}

// 4. Rebuild app
// 5. Restart app
```

**File-Based Approach:**
```bash
# Just create folder and files
mkdir Bots/security
cat > Bots/security/bot.json << 'JSON'
{
  "name": "security",
  "display_name": "Security Expert",
  "icon": "🔒",
  "enabled": true
}
JSON

cat > Bots/security/soul.md << 'MD'
# SOUL - Security Expert
## Core Values
- Security first
- Privacy by design
MD

# Restart app - bot is automatically loaded!
```

### Bot Configuration Files

**bot.json** - Core configuration
```json
{
  "name": "coder",
  "display_name": "Coder",
  "icon": "💻",
  "description": "Technical implementation expert",
  "version": "1.0.0",
  "enabled": true,
  
  "capabilities": {
    "can_code": true,
    "can_debug": true,
    "can_architect": true
  },
  
  "behavior": {
    "response_style": "technical",
    "speak_threshold": 0.5,
    "max_response_length": 500,
    "voice_tone": "professional"
  },
  
  "tools": [
    "filesystem.read",
    "filesystem.write", 
    "shell.execute",
    "code.analyze"
  ],
  
  "llm_config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "system_prompt_additions": [
      "You are an expert software engineer.",
      "Always consider edge cases."
    ]
  }
}
```

**soul.md** - Personality & values
```markdown
# SOUL - Coder

## Core Values
- Write clean, maintainable code
- Prioritize performance and security
- Explain technical concepts clearly

## Communication Style
- Direct and concise
- Uses technical terminology appropriately
- Provides code examples when relevant

## Constraints
- Never suggests unsafe practices
- Always considers edge cases
- Prefers standard libraries over dependencies
```

**role.md** - Role definition
```markdown
# ROLE - Coder

## Primary Responsibilities
- Code review and architecture
- Debugging and optimization
- API design and implementation
- Technical documentation

## Expertise Areas
- Python, JavaScript, TypeScript
- System architecture
- Database design
- DevOps and deployment

## Collaboration Patterns
- Works closely with Creative on UI implementation
- Consults Researcher for technical decisions
- Reports to Leader on technical blockers
```

**tools.json** - Tool permissions
```json
{
  "allowed_tools": [
    "filesystem.read",
    "filesystem.write",
    "shell.execute",
    "git.status",
    "code.analyze"
  ],
  "restricted_paths": [
    "~/.ssh",
    "/etc",
    "**/.env"
  ],
  "max_file_size": 1048576,
  "allowed_commands": [
    "git",
    "npm",
    "python",
    "docker"
  ]
}
```

**reasoning.json** - Reasoning configuration
```json
{
  "mode": "analytical",
  "step_by_step": true,
  "considers_alternatives": true,
  "provides_tradeoffs": true,
  "confidence_threshold": 0.8
}
```

### Dynamic Reloading

```swift
// Hot reload bots without app restart
class BotLoader {
    func startWatching() {
        let monitor = FolderMonitor(url: botsDirectory)
        
        monitor.onChange = { [weak self] in
            Task {
                await self?.reloadBots()
                NotificationCenter.default.post(
                    name: .botsReloaded,
                    object: nil
                )
            }
        }
    }
    
    func reloadBots() async {
        // Stop current bots gracefully
        // Reload configurations
        // Start new bots
        // Update UI
    }
}
```

### Validation

```swift
struct BotValidator {
    func validate(_ config: BotConfiguration) throws {
        // Required fields
        guard !config.name.isEmpty else {
            throw BotError.missingName
        }
        
        // Valid name (no spaces, special chars)
        guard config.name.matches(/^[a-z0-9_]+$/) else {
            throw BotError.invalidName(config.name)
        }
        
        // Valid tool references
        for tool in config.tools {
            guard ToolRegistry.hasTool(named: tool) else {
                throw BotError.unknownTool(tool)
            }
        }
        
        // Required files exist
        guard FileManager.default.fileExists(
            atPath: config.folder.appendingPathComponent("soul.md").path
        ) else {
            throw BotError.missingSoulFile
        }
    }
}
```

### Benefits Summary

1. **Zero-Code Bot Creation**: Add bots by creating folders/files
2. **Version Control Friendly**: Bots are data, easily versioned
3. **Community Sharing**: Share bot configurations as bundles
4. **Hot Reloading**: Update bots without app restart  
5. **User Extensibility**: Power users can create custom bots
6. **Easy Customization**: Edit markdown to change personality
7. **Modular**: Enable/disable bots via `enabled: false`

---

### Memory & Knowledge

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| Memory store + models | `memory/store.py`, `memory/models.py` | `Memory/Store.swift`, `Memory/Models.swift` | Schema and CRUD | SwiftData @Model |
| Embeddings + vector index | `memory/embeddings.py`, `memory/vector_index.py` | `Memory/Embeddings.swift`, `Memory/VectorIndex.swift` | Vector memory | **swift-embeddings (bge-small)** |
| Retrieval + summaries + graph | `memory/retrieval.py`, `memory/summaries.py`, `memory/graph.py` | `Memory/Retrieval.swift`, `Memory/Summaries.swift`, `Memory/Graph.swift` | Context building | Swift async/await |
| Background jobs | `memory/background.py` | `Memory/Background.swift` | Long-running tasks | Swift Concurrency TaskGroup |

---

### Tools, Skills, MCP

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| Tool registry + base tools | `agent/tools/*.py` | `Tools/` | File, shell, web, memory, MCP | **Deep macOS integration** |
| Tool permissions | `agent/tools/permissions.py` | `Tools/Permissions.swift` | Per-bot restrictions | Swift actor |
| MCP client | `agent/tools/mcp.py` | `Tools/MCP.swift` | Secret resolution | URLSession |
| Skill packs | `skills/*` | `Tools/Skills/` | Discover and run local skills | FileManager + Process |

---

### Security

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| Keyring + keyvault | `security/keyring_manager.py`, `security/keyvault.swift` | `Security/Keyring.swift`, `Security/KeyVault.swift` | Local-first secrets | Security.framework |
| Secure memory + sanitization | `security/secure_memory.py`, `security/sanitizer.py` | `Security/SecureMemory.swift`, `Security/Sanitizer.swift` | Sanitize logs/UI | Swift string processing |
| Credential detection + audit | `security/credential_detector.py`, `security/audit_logger.py` | `Security/CredentialDetector.swift`, `Security/AuditLogger.swift` | Scan and audit | Regex patterns |
| Symbolic converter | `security/symbolic_converter.py` | `Security/SymbolicConverter.swift` | MCP secret resolution | String processing |

---

### Providers and Channels

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| Provider registry + LLM | `providers/*` | `Providers/` | LiteLLM compatibility | URLSession networking |
| Channel manager + connectors | `channels/*` | `Channels/` | Telegram, Discord, Slack, Email | URLSession + AsyncStream |

---

### Identity, Teams, Templates, Soul

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| Team manager | `teams/manager.py` | `Identity/TeamManager.swift` | Team selection | SwiftData |
| Templates + discovery | `templates/*` | `Identity/Templates.swift` | Team/identity/soul templates | FileManager |
| Soul manager | `soul/manager.py` | `Identity/SoulManager.swift` | SOUL.md + IDENTITY/ROLE | FileManager |
| Identity + role parsing | `identity/*`, `models/role_card.py` | `Identity/RoleParser.swift` | Role cards and relationships | String processing |

---

### Routines & Scheduling

| Subsystem | Python Source | Swift v1 Target | Parity Notes | Swift-Specific |
|---|---|---|---|---|
| Routines service + types | `routines/*` | `Routines/Service.swift`, `Routines/Models.swift` | Timezone support | Swift Date/Calendar |
| Team routines manager | `routines/team/*` | `Routines/TeamRoutines.swift` | Checks and notifications | Timer + NotificationCenter |
| Dashboard server | `routines/team/dashboard_server.py` | `Routines/Dashboard.swift` | HTTP + WS metrics | Vapor or native HTTP |

---

### Local Models & Intelligence Layer

Your Python codebase already supports local models via LiteLLM. The Swift port can leverage the same capabilities:

#### Supported Local Models (from existing Python)

| Provider | Implementation | Swift Integration |
|----------|---------------|------------------|
| **Ollama** | OpenAI-compatible API | URLSession → `http://localhost:11434/v1/chat/completions` |
| **LM Studio** | OpenAI-compatible API | URLSession → `http://localhost:1234/v1/chat/completions` |
| **llama.cpp server** | OpenAI-compatible API | URLSession → `http://localhost:8080/v1/chat/completions` |
| **Apple Foundation Models** | Native Apple Silicon | Use `LLM` framework (macOS 14.4+) |

#### Swift Provider Architecture

```swift
// Local Ollama/LM Studio provider (OpenAI-compatible)
class LocalLLMProvider: LLMProvider {
    private let baseURL: URL
    private let model: String
    
    func chat(messages: [Message]) async throws -> LLMResponse {
        let url = baseURL.appendingPathComponent("v1/chat/completions")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "model": model,
            "messages": messages.map { ["role": $0.role, "content": $0.content] },
            "stream": false
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        // Parse OpenAI-compatible response...
    }
}

// Apple Intelligence (native on Apple Silicon)
class AppleIntelligenceProvider: LLMProvider {
    func chat(messages: [Message]) async throws -> LLMResponse {
        // Use Apple's LLM framework (macOS 14.4+)
        let llm = LLM(model: "com.apple.on-device")
        let response = try await llm.generate(messages: messages)
        return LLMResponse(content: response)
    }
}
```

#### Local Embeddings

Your Python uses FastEmbed with `BAAI/bge-small-en-v1.5`. Swift has equivalent options:

##### Option 1: swift-embeddings (Recommended - Pure Swift/MLX)

```swift
// Native Swift using MLX - no Python dependencies
import SwiftEmbeddings

class NativeEmbeddingProvider {
    private var modelContainer: ModelContainer?
    
    func load() async throws {
        // bge-small-en-v1.5 (same as Python!)
        modelContainer = try await Bert.loadModelBundle(
            from: "BAAI/bge-small-en-v1.5",
            loadConfig: .default
        )
    }
    
    func embed(texts: [String]) async throws -> [[Float]] {
        guard let container = modelContainer else { 
            throw EmbeddingError.notLoaded 
        }
        
        return try await container.perform { model, tokenizer, pooling in
            let inputs = texts.map { tokenizer.encode(text: $0) }
            // ... process through model
            return embeddings.map { $0.asArray(Float.self) }
        }
    }
}
```

**Hardware:** ~40MB VRAM (any M1+ Mac, even 8GB RAM models)

##### Option 2: mlx-embeddings (Python via MLX)

```swift
// Python mlx-embeddings called from Swift
// pip install mlx-embeddings
// Downloads mlx-community/bge-small-en-v1.5-8bit (35.5 MB)
```

##### Option 3: Ollama (if already running)

```swift
// Local Ollama - if you already run Ollama for LLM
class LocalEmbeddingProvider {
    private let baseURL = URL(string: "http://localhost:11434")!
    
    func embed(texts: [String]) async throws -> [[Float]] {
        let url = baseURL.appendingPathComponent("v1/embeddings")
        
        var results: [[Float]] = []
        for text in texts {
            let body: [String: Any] = [
                "model": "nomic-embed-text",  // or bge-small if pulled
                "input": text
            ]
            // ... HTTP request
        }
        return results
    }
}
```

##### Default Model: `BAAI/bge-small-en-v1.5`

This matches your Python config exactly:

#### Config Integration

The Swift config should mirror your Python schema:

```swift
struct LLMConfig {
    var provider: LLMProviderType  // .openai, .anthropic, .ollama, .lmStudio, .apple
    var apiKey: String?
    var apiBase: String?  // e.g., "http://localhost:11434"
    var defaultModel: String
    var useLocalModel: Bool
    var localModel: String  // e.g., "llama3", "mistral"
    
    var embeddingProvider: EmbeddingProviderType  // .native (MLX), .ollama, .api
    // Default: BAAI/bge-small-en-v1.5 (same as Python FastEmbed)
    var embeddingLocalModel: String = "BAAI/bge-small-en-v1.5"
}
```

#### Fallback Strategy

Your Python code already implements fallback (local first → API). Swift can do the same:

```swift
func chatWithFallback(messages: [Message]) async throws -> LLMResponse {
    // Try local first
    if config.useLocalModel {
        do {
            return try await localProvider.chat(messages: messages)
        } catch {
            logger.warning("Local model failed: \(error), falling back to API")
        }
    }
    // Fallback to cloud API
    return try await cloudProvider.chat(messages: messages)
}
```

---

## Python Dependencies → Swift Mapping

### Database & Storage

| Python | Swift | Strategy |
|--------|-------|----------|
| `sqlite3` (built-in) | **SQLite.swift** | Direct mapping - same SQLite, Swift wrapper |
| `hnswlib` | **Custom + MLX** | Use swift-embeddings for vector ops, or simple in-memory index |

### TurboMemoryStore Database Schema

The memory system uses these SQLite tables:

```swift
// SwiftData or SQLite.swift implementation
struct Event { id, content, timestamp, roomId, botId, embedding }
struct Entity { id, name, type, properties, timestamp }
struct Edge { id, sourceId, targetId, relationType }
struct Fact { id, subject, predicate, object, confidence }
struct Topic { id, name, embedding }
struct SummaryNode { id, content, timestamp, parentId }
struct Learning { id, content, botId, tags, timestamp }
struct Migration { id, name, appliedAt }
```

**Key:** WAL mode for concurrency (same as Python).

### LLM & Embeddings

| Python | Swift | Strategy |
|--------|-------|----------|
| `litellm` | **Custom URLSession** | Reimplement: OpenAI, Anthropic, Ollama, LM Studio APIs |
| `fastembed` | **swift-embeddings** | Native MLX with bge-small-en-v1.5 |
| `hnswlib` | **swift-embeddings** | Vector operations via MLX |

### Web & Networking

| Python | Swift | Strategy |
|--------|-------|----------|
| `httpx` | **URLSession** | Built-in |
| `websockets` | **URLSessionWebSocketTask** | Built-in |
| `scrapling` | **URLSession + SwiftSoup** | HTML parsing |
| `readability-lxml` | **SwiftSoup** | HTML extraction |

### Data Processing

| Python | Swift | Strategy |
|--------|-------|----------|
| `pypdf` | **PDFKit** | Built-in macOS |
| `pydantic` | **Codable** | Built-in Swift |
| `json-repair` | **Custom** | Simple JSON fixing |

### Channels (Telegram, Discord, Slack, etc.)

| Python | Swift | Strategy |
|--------|-------|----------|
| `python-telegram-bot` | **URLSession** | REST API calls |
| `slack-sdk` | **URLSession** | REST API calls |
| `python-socketio` | **URLSessionWebSocketTask** | Socket.IO protocol |

### MCP & Tools

| Python | Swift | Strategy |
|--------|-------|----------|
| `mcp` | **Custom** | JSON-RPC over stdio (same protocol) |
| `keyring` | **Security.framework** | Keychain access |

### CLI & UI

| Python | Swift | Strategy |
|--------|-------|----------|
| `typer` | **SwiftUI** | Native menu bar + window |
| `rich` | **SwiftUI** | Native styling |
| `prompt-toolkit` | **SwiftUI** | Input handling |

### Scheduling & Cron

| Python | Swift | Strategy |
|--------|-------|----------|
| `croniter` | **Swift Date + Calendar** | Reimplement cron parsing |

### Logging & Monitoring

| Python | Swift | Strategy |
|--------|-------|----------|
| `loguru` | **swift-log** | Structured logging |
| `croniter` | **Custom** | Schedule parsing |

### macOS-Specific

| Python | Swift | Strategy |
|--------|-------|----------|
| `apple-fm-sdk` | **LLM framework** | Native Apple Intelligence |

---

## Dependency Summary

| Strategy | Count | Examples |
|----------|-------|----------|
| **Built-in Swift** | 12+ | URLSession, PDFKit, Security, SwiftData, Codable |
| **SPM Package** | 4 | swift-embeddings, SQLite.swift, swift-log, MLX |
| **Reimplement** | 5 | LLM provider, MCP, channel connectors, cron |
| **API Calls** | 2 | GLiner → LLM, hnswlib → MLX vector ops |

---

## System Control Layer (Key Differentiator)

This is where Swift shines vs Go/Python:

### macOS APIs to Leverage

| Capability | Swift API | Use Case |
|------------|-----------|----------|
| Open apps/folders | `NSWorkspace.shared.open()` | File browser, app launching |
| File operations | `FileManager`, `NSFileCoordinator` | Read/write with security |
| Browser control | `SafariServices`, AppleScript | Open URLs, fill forms |
| UI automation | `AXUIElement` (Accessibility) | Click, type, read UI |
| App control | `NSRunningApplication` | List running apps, activate |
| Shell commands | `Process` (formerly NSTask) | Execute commands |
| System notifications | `UserNotifications` | Alert the user |
| Speech synthesis | `AVSpeechSynthesizer` | Voice output |
| Speech recognition | `Speech` framework | Voice input |
| Calendar/Contacts | EventKit, Contacts | System integration |
| Shortcuts | `Intents` framework | Run macOS Shortcuts |
| Screen capture | `CGWindowListCreateImage` | Screenshot tools |
| Clipboard | `NSPasteboard` | Copy/paste automation |

### Browser Automation Strategy

```
┌─────────────────────────────────────────────────────┐
│              Browser Automation Layer               │
├─────────────────────────────────────────────────────┤
│  1. AppleScript directly to Safari                  │
│     - open location, get URL of document            │
│     - Interact with DOM via JavaScript              │
├─────────────────────────────────────────────────────┤
│  2. SFSafariViewController (for embedded)          │
├─────────────────────────────────────────────────────┤
│  3. Accessibility API (AXUIElement)                 │
│     - Read button labels, click elements            │
│     - Works with any app, not just browsers         │
└─────────────────────────────────────────────────────┘
```

### File System Tools

```swift
// Example: Swift-native filesystem tool
class FilesystemTool {
    func readFile(path: String) async throws -> String {
        let url = URL(fileURLWithPath: path)
        return try String(contentsOf: url, encoding: .utf8)
    }
    
    func writeFile(path: String, content: String) async throws {
        let url = URL(fileURLWithPath: path)
        try content.write(to: url, atomically: true, encoding: .utf8)
    }
    
    func openInFinder(path: String) {
        NSWorkspace.shared.selectFile(path, inFileViewerRootedAtPath: "")
    }
    
    func openWithApp(path: String, app: String) {
        NSWorkspace.shared.open(URL(fileURLWithPath: path), 
                                withApplicationAt: URL(fileURLWithPath: app))
    }
}
```

---

## SmartDiscuss: LLM-Based Bot Selection

### Overview

**SmartDiscuss** is a new dispatch mode (`@discuss`) that enables intelligent group chat where:
1. **All room participants** evaluate their urgency to respond
2. **Only high-urgency bots** (threshold >= 0.5) generate responses
3. **Micro-turn responses** (1-3 sentences) create natural conversational flow
4. **LLM-based evaluation** understands nuanced context better than regex

### How It Works

```
User: "@discuss How should we implement dark mode in our design canvas?"

Phase 1: Urgency Evaluation (Single LLM Call)
├─ LLM analyzes: "design canvas" needs creative + coder expertise
├─ LLM evaluates all 6 bots in parallel:
│   creative: 0.90 - "Color theory and design expertise essential"
│   coder: 0.75 - "Canvas implementation needs technical knowledge"
│   researcher: 0.60 - "Could research user preferences"
│   leader: 0.50 - "Strategic coordination valuable"
│   auditor: 0.20 - "Accessibility review not immediately needed"
│   social: 0.10 - "Marketing not relevant to technical question"
└─ Returns: urgency scores for all bots

Phase 2: Response Generation (Selected Bots Only)
├─ Filter: urgency >= 0.5
├─ Sort: by urgency (highest first)
└─ Selected bots respond in micro-turns:
    🎨 creative: "We need a semantic color system that maps light theme colors to dark equivalents..."
    💻 coder: "For canvas implementation, CSS custom properties work best..."
    📊 researcher: "Studies show 73% of users prefer dark mode at night..."
    👑 leader: "Let's prioritize the semantic system first. Timeline: 3 days."
```

### Swift Implementation

```swift
// SmartDispatch.swift
actor SmartDispatch {
    private let roomManager: RoomManager
    private let llmProvider: LLMProvider
    private let speakThreshold: Double = 0.5
    
    func dispatchSmartDiscuss(
        message: String,
        roomId: String,
        participants: [Bot]
    ) async throws -> DispatchResult {
        // Phase 1: LLM evaluates all bots
        let urgencies = await evaluateUrgencyWithLLM(
            message: message,
            participants: participants
        )
        
        // Phase 2: Select high-urgency bots
        let selectedBots = urgencies
            .filter { $0.score >= speakThreshold }
            .sorted { $0.score > $1.score }
        
        return DispatchResult(
            target: .smartDiscuss,
            primaryBot: selectedBots.first?.name ?? "leader",
            secondaryBots: selectedBots.dropFirst().map { $0.name },
            reason: "SmartDiscuss: \(selectedBots.count) bots by urgency",
            urgencies: urgencies  // Include all scores for debugging
        )
    }
    
    private func evaluateUrgencyWithLLM(
        message: String,
        participants: [Bot]
    ) async -> [BotUrgency] {
        // Single LLM call evaluates all bots - cost efficient!
        let prompt = createUrgencyPrompt(message: message, bots: participants)
        
        let response = await llmProvider.chat(
            messages: [
                .system("""
                You are a relevance assessor for a multi-bot system.
                Rate each bot's urgency to respond (0.0-1.0).
                0.0 = not relevant, 1.0 = highly relevant
                Be decisive - most scores should be 0.0-0.3 with 2-4 bots above 0.5
                """),
                .user(prompt)
            ],
            temperature: 0.1  // Low temp for consistent evaluation
        )
        
        return parseUrgencyResponse(response.content)
    }
    
    private func createUrgencyPrompt(
        message: String,
        bots: [Bot]
    ) -> String {
        var prompt = "Message: \"\(message)\"\n\n"
        prompt += "Rate each bot's urgency to respond (0.0-1.0):\n\n"
        
        for bot in bots {
            prompt += "- \(bot.name): \(bot.description)\n"
        }
        
        prompt += "\nReturn as JSON: {\"botname\": {\"score\": 0.8, \"reason\": \"why\"}}"
        return prompt
    }
}

// Usage in MessageRouter
actor MessageRouter {
    func route(message: String, roomId: String) async -> [Response] {
        let dispatchResult = await dispatch(message: message, roomId: roomId)
        
        switch dispatchResult.target {
        case .smartDiscuss:
            return await routeSmartDiscuss(message, dispatchResult)
        case .multiBot:
            return await routeToMultipleBots(message, dispatchResult)
        case .leader:
            return await routeToLeader(message)
        case .direct(let botName):
            return await routeToBot(message, botName: botName)
        // ... other cases
        }
    }
    
    private func routeSmartDiscuss(
        _ message: String,
        _ dispatch: DispatchResult
    ) async -> [Response] {
        let selectedBots = await getBots(dispatch.secondaryBots)
        
        return await withTaskGroup(of: Response.self) { group in
            for bot in selectedBots {
                group.addTask {
                    await bot.process(
                        message: message,
                        context: BotContext(
                            roomId: roomId,
                            mode: .microTurn  // 1-3 sentences
                        )
                    )
                }
            }
            
            var responses: [Response] = []
            for await response in group {
                responses.append(response)
            }
            return responses.sorted { 
                dispatch.urgencies[$0.botName] > dispatch.urgencies[$1.botName]
            }
        }
    }
}
```

### Comparison with Other Dispatch Modes

| Mode | Trigger | Who Responds | Response Style | Use Case |
|------|---------|--------------|----------------|----------|
| **@all** | `@all` | Everyone (6 bots) | Full independent answers | Maximum coverage |
| **@team** | `@team` | Keyword-matched bots | Full answers by relevance | Topic-based selection |
| **@discuss** | `@discuss` | LLM-selected bots (2-4) | Micro-turns (1-3 sentences) | **Deep focused discussion** |
| **Default** | No tag | Leader only | Full answer | Simple questions |

### Key Advantages

1. **Contextual Understanding**: LLM understands nuanced implications
   - "design canvas" → creative (0.9) + **coder (0.75)** (regex would miss coder)
   - "collaborative editing" → **coder (0.9)** + researcher (0.6)

2. **Cost Efficient**: 1 LLM call evaluates all 6 bots vs 6 separate calls

3. **Natural Flow**: Micro-turns create conversational dynamics

4. **Explicit Control**: User chooses when to use smart discussion

### Fallback Strategy

```swift
if llmProvider.available {
    return await evaluateWithLLM(message, participants)
} else {
    // Fallback to rule-based keyword matching
    return evaluateWithRules(message, participants)
}
```

### Integration with Swift Features

- **Apple Intelligence**: Uses local on-device LLM for urgency evaluation
- **Swift Concurrency**: Parallel urgency evaluation with async/await
- **SwiftData**: Cache urgency patterns for repeated queries

---

## macOS-Specific Features

### Menu Bar Agent Mode

```swift
// Nanofolks as a menu bar app (Agent app)
class NanofolksApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    var body: some Scene {
        MenuBarExtra("Nanofolks", systemImage: "person.3") {
            Button("Open Chat") { ... }
            Button("Quick Action") { ... }
            Divider()
            Button("Quit") { ... }
        }
        .menuBarExtraStyle(.menu)
        
        Window("Nanofolks", id: "main") { ... }
    }
}
```

### Touch Bar Support (if applicable)

### Notifications & Haptics

### Keyboard Shortcuts

### Share Extensions

---

## Dependencies

### Swift Package Manager

| Package | Purpose | macOS Support |
|---------|---------|---------------|
| **swift-embeddings** | Native MLX embeddings (bge-small!) | Native (MLX) |
| swift-llm | LLM API clients | Native |
| SQLite.swift | Database | Native |
| Soto | AWS SDK (if needed) | Native |
| swift-nio | Networking | Native |
| apple/swift-http-types | HTTP | Native |
| mlx | MLX framework (for swift-embeddings) | Native (Apple Silicon) |

### Frameworks (built-in)

- **Foundation** - Core utilities
- **SwiftUI** - UI framework
- **SwiftData** - Persistence (macOS 14+)
- **Combine** - Reactive programming
- **Security** - Keychain, encryption
- **UserNotifications** - System notifications
- **SafariServices** - Browser integration
- **Accessibility** - UI automation
- **Speech** - Voice input/output
- **EventKit** - Calendar integration
- **Intents** - Shortcuts integration
- **LLM** - Apple Intelligence (macOS 14.4+, Apple Silicon only)

---

## Porting Strategy

> **Design Philosophy**: CLI-first approach. Build a solid command-line core before adding UI, external channels, or backend dependencies. The CLI serves as the foundation that everything else builds upon.

### Lessons from Python Implementation

**What Worked Well:**
1. **Fleet Architecture**: Independent bot instances coordinated by FleetManager is much cleaner than a master Agent orchestrator
2. **File-Based Bots**: Zero-code bot creation via folders/files is practical and maintainable
3. **SmartDispatch**: LLM-based urgency evaluation (0.5 threshold) successfully identifies relevant bots
4. **Single LLM Call**: Evaluating all bots in one call is cost-effective (vs 6 separate calls)
5. **Two-Phase Architecture**: Phase 1 (eval) → Phase 2 (respond) creates clear separation of concerns

**Implementation Details:**
- **Urgency Prompt Template**: System prompt emphasizes decisive scoring (most bots should score 0.0-0.3, only 2-4 above 0.5)
- **Temperature**: Use 0.1 for consistent evaluation
- **Fallback**: Rule-based keyword matching if LLM unavailable
- **Response Ordering**: Sort by urgency score (highest first) for natural conversation flow

**What Needs Refinement:**
1. **Micro-Turn Enforcement**: System prompt constraints help but need stronger enforcement
2. **Threshold Tuning**: 0.5 works well but may need per-bot customization
3. **Interrupt Logic**: Bot-to-bot interruption not yet implemented (future enhancement)
4. **Dynamic Selection**: Currently only at dispatch time, not mid-conversation

**Swift-Specific Considerations:**
- Use Swift Actors for bot instances (thread-safe, concurrent)
- Leverage Apple Intelligence for urgency evaluation (local, fast)
- Use SwiftData for room sessions (native persistence)
- Combine framework for event bus (replaces Python asyncio queues)

### Phase 0: Control Plane MVP (Weeks 0-1)
- [ ] Choose backend hosting (Railway/Vercel/VPS) and DB (Supabase/Convex)
- [ ] Implement OpenAuth login flow + session issuance
- [ ] Add billing provider webhook integration (e.g., Polar) + entitlement state
- [ ] Implement `/llm/chat` proxy (single model) + usage ledger
- [ ] Minimal admin UI/pages (user lookup + status + usage + revoke device)

### Phase 1: Core CLI Foundation (Weeks 1-3)

**Note**: Starting with Fleet architecture (not Agent loop) based on Python implementation success

- [ ] Swift CLI project setup (not app target - pure command-line)
- [ ] **Fleet architecture** (replaces Agent loop)
  - [ ] FleetManager for bot coordination (Actor-based)
  - [ ] MessageRouter for message dispatch
  - [ ] Single-bot mode (leader only) - start simple
- [ ] Intent detection & routing
- [ ] Basic LLM integration (direct providers - no backend yet)
  - [ ] OpenAI provider via URLSession
  - [ ] Simple chat completion API
- [ ] Simple REPL-style CLI interface
- [ ] Room/session management (in-memory + SQLite.swift)
- [ ] Basic logging and error handling
- [ ] Load single "leader" bot from file (BOTS/leader/bot.json)

### Phase 2: Core Tools & System Integration (Weeks 4-5)
- [ ] Tool registry & base protocol
- [ ] Filesystem tools (FileManager, NSWorkspace)
- [ ] Shell execution (Process/NSTask)
- [ ] Browser automation basics (Safari + AppleScript)
- [ ] System notifications (UserNotifications)
- [ ] Tool permissions system

### Phase 3: Memory & Knowledge (Weeks 6-7)
- [ ] Memory store with SQLite (SwiftData or SQLite.swift)
- [ ] Embedding generation (swift-embeddings with bge-small-en-v1.5)
- [ ] Vector index & retrieval
- [ ] Context building & summarization
- [ ] Session compaction

### Phase 4: File-Based Bot Architecture (Weeks 8-10)

**Implementation notes based on Python completion:**
- Threshold 0.5 works well for urgency filtering
- Single LLM call for all bots is cost-effective
- Micro-turns (1-3 sentences) create natural flow
- Fallback to rule-based if LLM unavailable

- [ ] **File-based bot system** (zero-code bot creation)
  - [ ] Bots/ folder structure with templates
  - [ ] bot.json schema (name, icon, capabilities, behavior, speak_threshold)
  - [ ] soul.md, role.md, identity.md support
  - [ ] tools.json for tool permissions
  - [ ] reasoning.json for behavior config
- [ ] **BotLoader** dynamic loading system
  - [ ] Scan Bots/ folder on startup
  - [ ] Parse JSON + markdown files
  - [ ] Validate bot configurations (name format, tool existence)
  - [ ] Hot reload capability (watch folder changes)
- [ ] **BotCore** infrastructure
  - [ ] Bot protocol (Actor-based for Swift)
  - [ ] ConcreteBot generic implementation
  - [ ] BotContext for shared state
  - [ ] Tool resolution from permissions
  - [ ] Bot evaluateUrgency() method for SmartDiscuss
- [ ] **Fleet** management layer
  - [ ] FleetManager (replaces Agent)
  - [ ] MessageRouter for dispatch (handles SMART_DISCUSS)
  - [ ] RoomSessionManager for shared sessions
  - [ ] Bot-to-bot coordination channel
  - [ ] RoomBroker for FIFO per-room processing
- [ ] **SmartDispatch** (@discuss trigger)
  - [ ] Two-phase architecture: Phase 1 (LLM urgency eval), Phase 2 (selected bots respond)
  - [ ] Urgency evaluation prompt template (single LLM call)
  - [ ] Threshold filtering (>= 0.5 to speak)
  - [ ] Fallback to rule-based keyword matching
  - [ ] Sort by urgency score (highest first)
- [ ] **ResponseCombiner** (multi-bot responses)
  - [ ] Format single vs multiple responses
  - [ ] Include bot icons/names
  - [ ] Handle overlapping content intelligently
  - [ ] Configurable response ordering (urgency-based)
- [ ] **Micro-turn enforcement**
  - [ ] System prompt constraints (1-3 sentences)
  - [ ] Optional max token limits
  - [ ] Natural conversation flow indicator

### Phase 5: CLI Channel (Weeks 10-11)
- [ ] Formalize CLI as a first-class channel
- [ ] Channel manager & base protocol
- [ ] CLI input/output handling
- [ ] Command parsing & routing
- [ ] Channel-to-room mapping

### Phase 6: Desktop App UI (Weeks 12-14)
- [ ] Convert CLI project → macOS app target
- [ ] SwiftUI views (chat, rooms, settings)
- [ ] Menu bar integration
- [ ] Settings & preferences UI
- [ ] Polish & UX refinement
- [ ] Testing

### Phase 7: Hardening & Distribution (Weeks 15-16)
- [ ] Security layer (Keychain, sanitization, credential detection)
- [ ] MCP client implementation
- [ ] Auto-update mechanism (Sparkle)
- [ ] Notarization & hardened runtime
- [ ] Documentation
- [ ] Final testing

### Phase 8: External Channels (Weeks 17-18)
- [ ] WhatsApp connector (via existing Node.js bridge or native Swift)
- [ ] iMessage connector (Apple Business Chat or local Messages.app)
- [ ] Channel authentication & session management
- [ ] Message format normalization

### Phase 9: Backend Integration (Weeks 19-20)
- [ ] Auth client & session management
- [ ] LLM proxy integration (switch from direct providers)
- [ ] Entitlements & usage tracking
- [ ] Billing UX & enforcement
- [ ] Graceful degradation when backend unavailable

### Future Phases (Post-v1)
- [ ] Telegram connector
- [ ] Discord connector
- [ ] Slack connector
- [ ] Email channel (IMAP/SMTP)
- [ ] Additional LLM providers
- [ ] Team/enterprise features

---

## Comparison: Swift vs Go vs Python

| Aspect | Swift | Go | Python (current - Multi-Bot) |
|--------|-------|-----|-------------------|
| **macOS Integration** | ✅ Native APIs | ❌ Shell only | ❌ Shell only |
| **Cross-platform** | Apple only | ✅ Excellent | ✅ Excellent |
| **LLM Integration** | ✅ URLSession + Apple Intelligence | ✅ Native | ✅ Native |
| **Local Embeddings** | ✅ swift-embeddings (bge-small) | ⚠️ External API | ✅ FastEmbed |
| **Concurrency** | ✅ Actors/async | ✅ Goroutines | ✅ AsyncIO |
| **UI Development** | ✅ SwiftUI | ⚠️ Web | ⚠️ Web |
| **Build size** | Medium | Small | Medium |
| **Startup time** | Fast | Fastest | Slow |
| **Multi-Bot Architecture** | ✅ Fleet-based (planned) | N/A | ✅ Fleet-based (COMPLETE) |
| **SmartDiscuss (@discuss)** | ✅ LLM-based (planned) | N/A | ✅ LLM-based (COMPLETE) |
| **File-Based Bots** | ✅ Zero-code (planned) | N/A | ✅ Zero-code (COMPLETE) |

---

## Decision Criteria

### Choose Swift if:
- macOS-native experience is primary goal
- Deep OS integration needed (browser automation, accessibility)
- You're willing to be Apple-platform-only for v1

### Choose Go if:
- Cross-platform desktop is important
- You're okay with "shallow" OS integration (shell commands)
- Team has Go expertise

### Keep Python if:
- Rapid prototyping is priority
- Cross-platform is mandatory
- ML/NLP ecosystem is critical (for now, less relevant with LLM APIs)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Swift vector search | No native vector DB | ✅ Native MLX embeddings (bge-small), same as Python |
| Limited NLP libs | Intent detection harder | Use LLM for NER, regex fallback |
| Channel SDKs | Fewer Swift libs | Use REST APIs directly |
| Team expertise | Learning curve | LLM-assisted coding |
| Mandatory login/backend outage | App becomes unusable | Degrade gracefully (local history/search/drafts), robust retry + clear status UI |
| Direct distribution hardening | Install/update friction | Notarization + hardened runtime + auto-update mechanism |
| macOS permissions (AX/Apple Events) | Tooling unreliable | Guided onboarding + permission checks + fail-safe tool fallbacks |

---

**Status**: Planning (Python Implementation COMPLETE)  
**Next Step**: Confirm backend stack (hosting + DB + billing) and implement Phase 0, then begin Phase 1 CLI foundation

---

## Implementation Status

### Python True Multi-Bot Architecture: COMPLETE ✅

The Python implementation has been completed with the following components:

**New Modules Created:**
- `agent/response_combiner.py` - Combines multi-bot responses with smart formatting
- `agent/message_router.py` - Routes messages to bots, handles SMART_DISCUSS dispatch mode
- `bots/fleet.py` - Manages independent bot instances (replaces Agent orchestrator)
- `bots/coordination.py` - Bot-to-bot communication channel (DM rooms, insights)
- `bots/smart_dispatch.py` - LLM-based urgency evaluation for @discuss
- `session/room_session_manager.py` - Room-centric sessions shared across bots
- `config/schema.py` - Feature flags for gradual rollout
- `multi_bot_integration.py` - Helper functions for integration

**Modified Modules:**
- `bots/dispatch.py` - Added SMART_DISCUSS dispatch target, @discuss trigger recognition

**Migration & Documentation:**
- `scripts/migrate_sessions_to_rooms.py` - Session to room migration tool
- `docs/MULTI_BOT_ARCHITECTURE_README.md` - Complete architecture documentation
- `IMPLEMENTATION_SUMMARY.md` - Implementation summary with examples

**Tests:**
- `tests/test_response_combiner.py` - Response combiner unit tests

### Key Insights from Python Implementation

1. **SmartDispatch Works**: LLM-based urgency evaluation (0.5 threshold) successfully identifies relevant bots
2. **Single LLM Call Efficiency**: Evaluating all bots in one call is cost-effective vs 6 separate calls
3. **Micro-Turns Matter**: Limiting responses to 1-3 sentences creates natural conversation flow
4. **File-Based Bots**: Zero-code bot creation via folders/files is practical and maintainable
5. **Fleet Architecture**: Independent bot instances coordinated by FleetManager is cleaner than master Agent

---

## Architecture Clarification: Channels vs. UI App

### Channels
External platforms where users interact with the agent:
- **WhatsApp** - Users message from their phone via WhatsApp
- **iMessage** - Users message from iPhone/Mac
- **Telegram/Discord/Slack** - Other messaging platforms (future)
- **CLI** - Terminal interface (built into the core)

### UI App (macOS Desktop App)
- NOT a channel - it's the native "home base" interface
- Talks directly to the agent core (no external APIs)
- Everything else (CLI, WhatsApp, iMessage) are "entrances" that feed into the same agent

```
┌─────────────────────────────────────┐
│         Agent Core (Swift)          │
├─────────────────────────────────────┤
│  macOS UI App (direct access)       │
│  CLI (direct access)                │
│  WhatsApp Channel (via bridge)      │
│  iMessage Channel (via API)         │
└─────────────────────────────────────┘
```

### WhatsApp Bridge (Current Implementation)
The Python project uses a Node.js bridge for WhatsApp:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         YOUR COMPUTER                                │
├─────────────────────────────────────────────────────────────────────┤
│   ┌──────────────────┐         WebSocket         ┌────────────────┐ │
│   │   Python/Swift   │ ◄─────────────────────────►│  Node.js       │ │
│   │   App            │      ws://127.0.0.1:3001   │  Bridge        │ │
│   │                  │                            │  (Baileys)     │ │
│   └──────────────────┘                            └───────┬────────┘ │
│                                                           │          │
│                                                    ┌──────▼──────┐   │
│                                                    │  WhatsApp   │   │
│                                                    │  Servers    │   │
│                                                    └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Why a bridge?** WhatsApp has no official API for personal accounts. Baileys (Node.js) implements the WhatsApp Web protocol.

**Swift options:**
1. Keep the Node.js bridge (Swift WebSocket client to existing bridge)
2. Create a Swift-native bridge (more work, single binary)

**Recommendation**: Start with Option 1 (keep bridge), evaluate Option 2 post-v1.
