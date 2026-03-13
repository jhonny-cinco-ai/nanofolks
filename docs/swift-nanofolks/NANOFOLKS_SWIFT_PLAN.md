# nanofolks Swift Port Plan

**Purpose**: Native macOS companion app for everyday life assistance - helping non-technical users leverage technology through friendly characters, not technical bots.

**Audience**: People with little to no technical knowledge (mom-friendly). Characters with personalities, not developer tools.

**Scope**: Full parity with Python architecture + deep macOS system control + everyday life integration

**Rationale**: Desktop companion requiring real calendar, reminders, contacts, photos, and app automation for normal life tasks.

**Core Values**:
- **Characters, not bots**: Personality-rich companions organized in themed teams
- **Everyday tasks**: Calendar, reminders, shopping lists, health tracking - not coding tools
- **Local-first with cloud fallback**: Simple tasks run locally on any Mac, complex tasks use cloud
- **Security as foundation**: Privacy dashboard, data transparency, user control from day one
- **Memory as relationship**: Characters learn and remember, with user confirmation and visibility

**Status**: Python True Multi-Bot Architecture - COMPLETE ✅ | Swift Port - Implementation Started 🚧

## Single Source of Truth (Current Snapshot)

**As of**: March 13, 2026

| Area | Current Status | Notes |
|---|---|---|
| Core architecture | ✅ Implemented | Protocol/types foundation is in place and compiles |
| Fleet/Bot/Provider runtime | 🟡 Partial | Core paths exist; routing/details still have placeholders |
| Identity/Memory/System/Security | 🟡 Partial/Stub | Basic functionality exists; key subsystems still missing |
| ChannelKit/ToolKit/RoutineKit | ⚪ Scaffold | Module shells exist, no concrete implementations |
| EverydayKit/OnboardingKit/PrivacyKit | ⚪ Scaffold | Product-facing v1 features not implemented yet |
| Prompt content/templates | 🟡 Partial | Structure exists; only a small subset of files implemented |
| Team/role content | 🟡 Partial | Single team example with limited role coverage |
| Nanofolks app (SwiftUI) | ❌ Missing | `NanofolksApp` target/source not implemented yet |
| Build health | ✅ Passing | `swift build` succeeds |
| Test health | ❌ Missing tests | `swift test` currently reports no tests found |

**Detailed status**: See `V1 Parity Matrix` and `Implementation Status` sections below.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    nanofolks - Companion App                        │
│              "Your friendly character assistants"                  │
├─────────────────────────────────────────────────────────────────────┤
│  User Experience Layer (SwiftUI)                                   │
│  - Team selection (pirate_crew, space_crew, etc.)                  │
│  - Character introduction & onboarding                             │
│  - Daily assistant view, not developer tools                       │
│  - Privacy dashboard & cost transparency                           │
│  - "I learned this" notifications & confirmations                  │
├─────────────────────────────────────────────────────────────────────┤
│  Everyday Life Tools (NEW - for normal people)                    │
│  - Calendar integration (EventKit)                                │
│  - Reminders & tasks (Reminders framework)                         │
│  - Contacts lookup (Contacts framework)                            │
│  - Weather & local info (Weather API)                              │
│  - Photos & memories (Photos framework)                            │
│  - Maps & directions (MapKit)                                      │
│  - Email drafts (Message framework)                                 │
│  - Health tracking (HealthKit)                                      │
├─────────────────────────────────────────────────────────────────────┤
│  Character System (IdentityKit)                                    │
│  - Teams with personality themes                                    │
│  - Characters with names, not roles (Captain, not leader)          │
│  - Workspace customization (user can personalize)                  │
├─────────────────────────────────────────────────────────────────────┤
│  Fleet Core (Swift)                                                 │
│  - FleetManager (manages character instances)                       │
│  - SmartDispatch (who should respond?)                             │
│  - Memory & learning (with user confirmation)                      │
│  - Conversation repair ("Let me clarify...")                       │
├─────────────────────────────────────────────────────────────────────┤
│  Intelligence Layer (Tiered Strategy)                              │
│  - Local models: Urgency evaluation, classification, embeddings    │
│  - Cloud models: Complex reasoning, analysis, generation           │
│  - Fallback: Graceful degradation when offline/limited             │
├─────────────────────────────────────────────────────────────────────┤
│  Security & Privacy (Foundation)                                  │
│  - Privacy dashboard: What stays local vs goes to cloud            │
│  - Permission management: Easy toggles                              │
│  - Data transparency: Export, delete, retention                    │
│  - Audit logging: All actions tracked                              │
├─────────────────────────────────────────────────────────────────────┤
│  System Integration (Swift/macOS APIs)                             │
│  - Calendar, Reminders, Contacts (EventKit, Contacts)              │
│  - Photos, Maps, Weather (Photos, MapKit, Weather)                 │
│  - Email, Notes, Health (Message, HealthKit)                       │
│  - Filesystem, Browser, Apps (NSWorkspace, Safari)                 │
├─────────────────────────────────────────────────────────────────────┤
│  Data Layer (Local-First)                                          │
│  - All user data on-device by default                               │
│  - Cloud: Only auth, billing, metering, LLM proxy                  │
│  - Memory store & vector index (local embeddings)                  │
├─────────────────────────────────────────────────────────────────────┤
│  Nanofolks Cloud (Thin Control Plane)                              │
│  - Auth, entitlements, billing                                      │
│  - LLM proxy with provider routing                                 │
│  - Minimal metadata (no conversation content stored)               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Composability Architecture (Lego Blocks)

**Principle**: Each module is an independent, reusable "Lego block" that can work in isolation or be composed with others. Modules communicate through protocols (interfaces), not implementations.

### Dependency Graph

```
                              ┌─────────┐
                              │  Core   │  ← Minimal core, no dependencies
                              └────┬────┘
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        │              │           │           │              │
        ▼              ▼           ▼           ▼              ▼
┌───────────┐  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│ MemoryKit │  │ProviderKit│ │ PromptKit │ │ SystemKit │ │SecurityKit│
└─────┬─────┘  └─────┬─────┘ └─────┬─────┘ └───────────┘ └───────────┘
      │              │             │             │
      │              │             │             │
      ▼              ▼             ▼             ▼
┌───────────┐  ┌───────────┐ ┌───────────┐ ┌───────────┐
│  ToolKit  │  │ ChannelKit│ │PromptKit  │ │PromptKit  │  ← shared across modules
└─────┬─────┘  └─────┬─────┘ │ (injected)│ │ (injected)│
      │              │       └───────────┘ └───────────┘
      └────────┬─────┘             │
               ▼                   │
        ┌───────────┐              │
        │  BotKit   │◄─────────────┘
        └─────┬─────┘
              │
              ▼
        ┌───────────┐
        │ FleetKit  │
        └─────┬─────┘
              │
              ▼
        ┌───────────┐
        │   App     │  ← Composition root, assembles all blocks
        └───────────┘
```

### Core Principles

**1. Dependency Inversion (DIP)**
```swift
// Core defines interface - No dependencies
public protocol LLMProvider {
    func chat(messages: [Message]) async throws -> LLMResponse
}

// ProviderKit implements - Depends on Core
public class OpenAIProvider: LLMProvider { ... }

// FleetKit uses interface - Depends on Core only
public actor FleetManager {
    private let provider: LLMProvider  // Injected
}
```

**2. Interface Segregation**
```swift
// Split large protocols into focused ones
public protocol BotResponder {
    func process(message: Message) async throws -> Response
}

public protocol BotUrgencyEvaluator {
    func evaluateUrgency(for message: Message) async -> Double
}

// Bot implements only what it needs
public protocol Bot: BotResponder, BotUrgencyEvaluator {
    var name: String { get }
}
```

**3. Event-Driven Communication**
```swift
// Modules communicate via events, not direct calls
public enum BotEvent {
    case messageReceived(Message)
    case responseGenerated(Response)
    case coordinationNeeded(CoordinationRequest)
}

public protocol EventBus {
    func publish(_ event: BotEvent)
    func subscribe(handler: @escaping (BotEvent) -> Void)
}
```

### Independent Module Usage

**MemoryKit standalone:**
```swift
import MemoryKit

// Current concrete option
let memory = InMemoryStore()
try await memory.store(entry: MemoryEntry(content: "example"))
let results = try await memory.search(query: "example", limit: 10)
```

**ProviderKit standalone:**
```swift
import ProviderKit

let provider = OpenAIProvider(apiKey: "...")
let request = LLMRequest(messages: [Message(role: .user, content: "Hello")])
let response = try await provider.chat(request: request)
```

**PromptKit standalone:**
```swift
import PromptKit

// Load prompt from file
let promptLoader = PromptLoader(promptsDirectory: "Prompts/")
let prompt = try await promptLoader.load(id: "smart_discuss_urgency")

// Render with variables
let rendered = try await promptLoader.render(
    id: "intent_detection",
    variables: [
        "message": userMessage,
        "context": context
    ]
)

// Use in any LLM call
let response = try await provider.chat(
    messages: [
        .system(rendered),
        .user(userMessage)
    ]
)
```

**SystemKit standalone:**
```swift
import SystemKit

let workspace = Workspace()
workspace.openInFinder(path: "/Users/...")
workspace.openApp(name: "Safari")
```

### Composition Root Pattern

The app assembles everything at startup:

```swift
// Pseudocode architecture example (not current implementation)
// NanofolksApp/DIContainer.swift
public final class DIContainer {
    public let provider: LLMProvider
    public let memory: MemoryStore
    public let tools: ToolRegistry
    public let fleet: FleetManager
    public let channels: ChannelManager
    
    public init(config: AppConfig) async throws {
        // Assemble Lego blocks
        self.provider = try await ProviderFactory.create(config.provider)
        self.memory = MemoryStore(config.memory)
        self.tools = ToolRegistry(config.tools)
        self.fleet = await FleetManager(
            provider: provider,
            memory: memory,
            tools: tools
        )
        self.channels = ChannelManager()
        
        // Wire dependencies
        channels.setRoutingHandler { [fleet] message in
            try await fleet.process(message)
        }
    }
}
```

---

## Product & Platform Decisions (v1)

**Target Audience**: Non-technical users who want technology to help with everyday life. Characters with personalities, not developer tools. Mom-friendly design.

**Distribution**: Direct download from website (not App Store). Plan for notarization, hardened runtime, and an auto-update mechanism (e.g., Sparkle).

**Login**: Required to use the app (because v1 relies on online LLM calls). Design for graceful degradation when backend/provider is unavailable (view history, search local memory, drafts, use local models), but block complex requests requiring cloud.

**Data philosophy**: Local-first. "Important user data" (agent memory/learning, room history, calendar events, contacts) stays on-device by default. The server stores only what's needed for auth, billing, metering, and abuse prevention. **User can see exactly what stays local vs goes to cloud via Privacy dashboard.**

**Backend role**: A thin "control plane" + LLM proxy. The macOS app never calls gateway/router or LLM providers directly in v1.

**Model strategy (TIERED)**:
- **Local-first for simple tasks**: Urgency evaluation, classification, embeddings, simple Q&A
- **Cloud for complex tasks**: Reasoning, analysis, generation, coding assistance
- **Privacy-sensitive mode**: User can force local-only (limited capabilities, no cloud)
- **Graceful fallback**: If local model unavailable (older Mac), degrade to simpler prompts or cloud

**Provider strategy**:
- Start with a gateway/router behind the proxy (simplifies multi-provider support and failover).
- Curate an allowlist of ~5–10 models (keep UX simple and costs predictable).
- Keep the interface abstract so we can later route directly to providers and/or add specialized/experimental models (including self-hosted options) without changing the client.

**Pricing strategy**:
- Subscription plans include a monthly usage budget (recommend token-based budgets; optionally display "~N standard requests").
- **Cost transparency**: Users see estimated cost before complex cloud operations
- **Local model indicator**: Show when using free local computation
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

### Modular Architecture (Lego Blocks)

Each module is an independent Swift Package target that can be used standalone or composed together.

```
nanofolks-swift/
├── Prompts/                          # ALL PROMPTS (Data, not code)
│   ├── System/                        # System-level prompts
│   │   ├── smart_discuss/
│   │   │   ├── urgency_evaluation.md
│   │   │   ├── response_format.md
│   │   │   └── fallback_rules.md
│   │   ├── intent/
│   │   │   ├── detection.md
│   │   │   ├── flow_routing.md
│   │   │   └── cancellation.md
│   │   ├── memory/
│   │   │   ├── summarization.md
│   │   │   ├── retrieval.md
│   │   │   ├── learned_notification.md    # "I learned that..."
│   │   │   ├── learning_confirm.md        # "Is this correct?"
│   │   │   └── forget_request.md          # "Forget this"
│   │   └── coordination/
│   │       ├── bot_to_bot.md
│   │       └── insight_sharing.md
│   │
│   ├── Bot/                          # Bot prompts (SHARED TEMPLATES, not bot-specific)
│   │   └── base/
│   │       ├── system_template.md     # Base template: fills in {soul}, {role}, {identity}
│   │       ├── micro_turn.md          # Micro-turn constraints (1-3 sentences)
│   │       └── tool_instructions.md    # How to use tools (shared across all bots)
│   │
│   ├── Tools/                        # Tool prompts
│   │   ├── filesystem/
│   │   │   ├── read_instructions.md
│   │   │   ├── write_instructions.md
│   │   │   └── search_instructions.md
│   │   ├── shell/
│   │   │   ├── execute_instructions.md
│   │   │   └── safety_constraints.md
│   │   ├── browser/
│   │   │   ├── automation_instructions.md
│   │   │   └── form_filling.md
│   │   ├── mcp/
│   │   │   ├── protocol_instructions.md
│   │   │   └── secret_resolution.md
│   │   └── everyday/                  # NEW: Everyday life tools
│   │       ├── calendar_assistant.md
│   │       ├── reminder_assistant.md
│   │       ├── weather_assistant.md
│   │       ├── shopping_assistant.md
│   │       └── health_assistant.md
│   │
│   ├── UX/                            # User-facing prompts
│   │   ├── onboarding/                 # NEW: First-time user experience
│   │   │   ├── team_selection.md        # "Pick your companion team"
│   │   │   ├── character_intro.md       # "Meet your companions"
│   │   │   ├── first_conversation.md    # Guided first chat
│   │   │   ├── permission_simple.md     # Simple permission explanations
│   │   │   └── tutorial_flow.md         # Step-by-step walkthrough
│   │   ├── conversation/                # NEW: Conversation repair
│   │   │   ├── clarification.md        # "Let me make sure I understood..."
│   │   │   ├── misunderstood.md        # "I'm not sure what you mean..."
│   │   │   ├── simplify.md             # "Let me explain this simpler..."
│   │   │   └── progress_update.md      # "Here's what I'm doing..."
│   │   ├── privacy/                    # NEW: Privacy transparency
│   │   │   ├── data_stays_local.md     # Explanation of local data
│   │   │   ├── data_goes_cloud.md      # Explanation of cloud data
│   │   │   ├── permission_why.md        # Why we need each permission
│   │   │   └── export_data.md          # How to export your data
│   │   ├── errors/
│   │   │   ├── network_error.md
│   │   │   ├── rate_limit.md
│   │   │   ├── permission_denied.md
│   │   │   ├── local_unavailable.md    # NEW: Local model not available
│   │   │   └── cloud_unavailable.md    # NEW: Cloud model not available
│   │   ├── learning/                   # NEW: Learning moments
│   │   │   ├── learned_this.md          # "I learned that you prefer..."
│   │   │   ├── confirm_learning.md      # "Is this correct?"
│   │   │   ├── already_know.md          # "I remember you mentioned..."
│   │   │   └── forget_this.md          # "I've forgotten about..."
│   │   ├── cost/                       # NEW: Cost transparency
│   │   │   ├── local_free.md           # "This uses local computation (free)"
│   │   │   ├── cloud_cost_estimate.md   # "This will use ~X tokens"
│   │   │   └── budget_remaining.md      # "You have X tokens remaining"
│   │   └── messages/
│   │       ├── status_updates.md
│   │       ├── progress_indicators.md
│   │       └── confirmations.md
│   │
│   ├── Channels/                      # Channel prompts
│   │   ├── cli/
│   │   │   ├── welcome.md
│   │   │   ├── help.md
│   │   │   ├── commands.md
│   │   │   └── format_hints.md
│   │   ├── whatsapp/
│   │   │   ├── welcome.md
│   │   │   ├── commands.md
│   │   │   └── media_handling.md
│   │   └── imessage/
│   │       ├── welcome.md
│   │       └── commands.md
│   │
│   └── _templates/                    # Reusable templates
│       ├── few_shot.md
│       ├── chain_of_thought.md
│       ├── structured_output.md
│       └── conversation_context.md
│
├── Teams/                              # TEAM TEMPLATES (Built-in)
│   ├── pirate_crew/                    # Example team
│   │   ├── TEAM.md                     # Team description & vibe
│   │   ├── leader_SOUL.md              # Captain personality
│   │   ├── leader_IDENTITY.md          # Captain character/name
│   │   ├── coder_SOUL.md               # Gunner personality
│   │   ├── coder_IDENTITY.md           # Gunner character/name
│   │   ├── researcher_SOUL.md          # Navigator personality
│   │   ├── researcher_IDENTITY.md      # Navigator character/name
│   │   └── ... (other bots)
│   │
│   ├── space_crew/                     # Space exploration theme
│   │   └── ... (TEAM.md, {bot}_SOUL.md, {bot}_IDENTITY.md)
│   ├── rock_band/                      # Music/creative theme
│   ├── swat_team/                      # Tactical/precision theme
│   ├── feral_clowder/                  # Cat-themed scrappy team
│   └── executive_suite/                # Corporate/professional theme
│
├── Roles/                              # ROLE TEMPLATES (Same across all teams)
│   ├── leader_ROLE.md                  # Leader capabilities/constraints
│   ├── coder_ROLE.md                   # Coder capabilities/constraints
│   ├── researcher_ROLE.md              # Researcher capabilities/constraints
│   ├── social_ROLE.md                  # Social capabilities/constraints
│   ├── creative_ROLE.md                # Creative capabilities/constraints
│   └── auditor_ROLE.md                 # Auditor capabilities/constraints
│
├── Agents/                             # AGENT COORDINATION (Same across all teams)
│   ├── leader_AGENTS.md                # How leader coordinates agents
│   ├── coder_AGENTS.md                 # How coder coordinates agents
│   ├── researcher_AGENTS.md            # How researcher coordinates agents
│   ├── social_AGENTS.md                # How social coordinates agents
│   ├── creative_AGENTS.md              # How creative coordinates agents
│   └── auditor_AGENTS.md               # How auditor coordinates agents
│
├── Workspace/                          # USER CUSTOMIZATIONS (Overrides)
│   ├── Team/                           # Current team selection
│   │   └── current_team.json           # {"team": "pirate_crew"}
│   │
│   └── Bots/                           # BOT OVERRIDES (User customizations)
│       ├── _templates/
│       │   ├── template.json
│       │   └── README.md
│       │
│       ├── leader/                      # Override leader for this team
│       │   ├── SOUL.md                  # User-customized personality
│       │   ├── IDENTITY.md              # User-customized identity
│       │   ├── reasoning.json            # User-customized reasoning
│       │   └── tools.json               # User-customized tools
│       │
│       └── ... (other bots)
│
├── Sources/
│   ├── Core/...                # (same as before)
│   ├── PromptKit/...           # (same as before)
│   ├── BotKit/...              # (same as before)
│   ├── FleetKit/...            # (same as before)
│   ├── MemoryKit/...           # (same as before)
│   ├── ProviderKit/...         # (same as before)
│   ├── ToolKit/...             # (same as before)
│   ├── ChannelKit/...           # (same as before)
│   ├── SystemKit/                     # macOS INTEGRATION - Standalone
│   │   ├── Workspace.swift
│   │   ├── Browser.swift
│   │   ├── Filesystem.swift
│   │   ├── Shell.swift
│   │   ├── Accessibility.swift
│   │   ├── AppleScript.swift
│   │   └── Notifications.swift
│   │
│   ├── EverydayKit/                   # NEW: EVERYDAY LIFE TOOLS - Depends: Core, PromptKit
│   │   ├── CalendarTool.swift          # EventKit integration
│   │   ├── RemindersTool.swift         # Reminders framework
│   │   ├── ContactsTool.swift          # Contacts framework
│   │   ├── WeatherTool.swift           # Weather API
│   │   ├── PhotosTool.swift            # Photos framework
│   │   ├── MapsTool.swift              # MapKit integration
│   │   ├── EmailDraftTool.swift        # Message framework
│   │   ├── NotesTool.swift             # Notes app integration
│   │   └── HealthTool.swift            # HealthKit integration
│   │
│   ├── OnboardingKit/                 # NEW: FIRST-TIME UX - Depends: Core, PromptKit, IdentityKit
│   │   ├── TeamSelectionView.swift     # "Pick your companion team"
│   │   ├── CharacterIntroView.swift    # "Meet your companions"
│   │   ├── FirstConversation.swift     # Guided first chat
│   │   ├── PermissionOnboarding.swift  # Progressive permissions
│   │   ├── TutorialFlow.swift          # Step-by-step walkthrough
│   │   └── OnboardingState.swift       # Track onboarding progress
│   │
│   ├── PrivacyKit/                    # NEW: USER-FACING PRIVACY - Depends: Core, PromptKit, SecurityKit
│   │   ├── PrivacyDashboard.swift      # "Your Privacy" panel
│   │   ├── DataFlowVisualization.swift # What stays local vs cloud
│   │   ├── PermissionManager.swift     # Easy toggle controls
│   │   ├── DataRetentionSettings.swift # How long to keep data
│   │   ├── ExportMyData.swift          # GDPR-style export
│   │   └── CostDashboard.swift         # Usage & cost transparency
│   │
│   ├── SecurityKit/                   # SECURITY - Standalone
│   │   ├── Keyring.swift
│   │   ├── KeyVault.swift
│   │   ├── SecureMemory.swift
│   │   ├── Sanitizer.swift
│   │   ├── CredentialDetector.swift
│   │   └── AuditLogger.swift
│   │
│   ├── IdentityKit/                   # IDENTITY & TEAM MANAGEMENT
│   │   ├── TeamManager.swift
│   │   ├── TeamProfile.swift
│   │   ├── SoulLoader.swift
│   │   ├── RoleParser.swift
│   │   └── RelationshipParser.swift
│   │
│   ├── RoutineKit/...                  # (same as before)
│   │
│   └── NanofolksApp/                   # APP - ASSEMBLES ALL BLOCKS
│       ├── App/
│       │   ├── NanofolksApp.swift
│       │   ├── DIContainer.swift
│       │   └── AppDelegate.swift
│       ├── Views/
│       │   ├── ChatView.swift
│       │   ├── RoomListView.swift
│       │   ├── BotConfigView.swift
│       │   ├── SettingsView.swift
│       │   ├── TeamSelectionView.swift    # NEW: Team picker
│       │   ├── PrivacyDashboardView.swift # NEW: Privacy panel
│       │   └── CostUsageView.swift        # NEW: Cost transparency
│       ├── ViewModels/
│       │   ├── ChatViewModel.swift
│       │   └── RoomListViewModel.swift
│       └── Resources/
│
├── Tests/
│   ├── CoreTests/
│   ├── PromptKitTests/
│   ├── BotKitTests/
│   ├── FleetKitTests/
│   ├── IdentityKitTests/
│   ├── MemoryKitTests/
│   ├── ProviderKitTests/
│   ├── ToolKitTests/
│   ├── EverydayKitTests/                # NEW
│   ├── OnboardingKitTests/              # NEW
│   ├── PrivacyKitTests/                 # NEW
│   ├── SystemKitTests/
│   └── IntegrationTests/
│
├── Package.swift
└── README.md
```
```

### Key Architectural Changes

**REMOVED:**
- ❌ `Agent/` folder - No master controller
- ❌ `Bots/Definitions.swift` - No hardcoded bot registry
- ❌ `Bots/Coordinator.swift` - Coordination moved to FleetKit
- ❌ Monolithic module structure

**ADDED:**
- ✅ `Core/` - Minimal protocol-only module (no dependencies)
- ✅ `Bots/` at root - File-based bot definitions (data, not code)
- ✅ `*Kit` modules - Each is independent Lego block
- ✅ Dependency inversion - All dependencies point inward to Core
- ✅ `DIContainer` - Composition root that assembles blocks

**Composability Benefits:**
- Each `*Kit` module can be tested in isolation
- Modules can be reused in other projects (e.g., MemoryKit for any app)
- Clear dependency boundaries prevent circular dependencies
- Easy to swap implementations (OpenAI → Anthropic provider swap)
- Event-driven communication enables loose coupling

### Swift Package Structure

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "nanofolks",
    platforms: [.macOS(.v14)],
    
    products: [
        // Executable apps
        .executable(name: "nanofolks-cli", targets: ["NanofolksCLI"]),
        // Libraries (each is a Lego block)
        .library(name: "Core", targets: ["Core"]),
        .library(name: "PromptKit", targets: ["PromptKit"]),
        .library(name: "BotKit", targets: ["BotKit"]),
        .library(name: "FleetKit", targets: ["FleetKit"]),
        .library(name: "MemoryKit", targets: ["MemoryKit"]),
        .library(name: "ProviderKit", targets: ["ProviderKit"]),
        .library(name: "ToolKit", targets: ["ToolKit"]),
        .library(name: "ChannelKit", targets: ["ChannelKit"]),
        .library(name: "SystemKit", targets: ["SystemKit"]),
        .library(name: "EverydayKit", targets: ["EverydayKit"]),      // NEW
        .library(name: "OnboardingKit", targets: ["OnboardingKit"]),  // NEW
        .library(name: "PrivacyKit", targets: ["PrivacyKit"]),        // NEW
        .library(name: "SecurityKit", targets: ["SecurityKit"]),
        .library(name: "IdentityKit", targets: ["IdentityKit"]),
        .library(name: "RoutineKit", targets: ["RoutineKit"]),
    ],
    
    dependencies: [
        .package(url: "https://github.com/swift-embeddings/swift-embeddings", from: "0.1.0"),
        .package(url: "https://github.com/stephencelis/SQLite.swift", from: "0.14.0"),
        .package(url: "https://github.com/apple/swift-log", from: "1.5.0"),
        .package(url: "https://github.com/jpsim/Yams", from: "5.0.0"),  // YAML parsing for prompts
    ],
    
    targets: [
        // ═══════════════════════════════════════════════════════════════
        // CORE MODULE - No dependencies (protocol definitions only)
        // ═══════════════════════════════════════════════════════════════
        .target(
            name: "Core",
            dependencies: []
        ),
        
        // ═══════════════════════════════════════════════════════════════
        // STANDALONE MODULES - Depend only on Core or nothing
        // ═══════════════════════════════════════════════════════════════
        
        .target(
            name: "PromptKit",
            dependencies: ["Core", .product(name: "Yams", package: "Yams")]
        ),
        
        .target(
            name: "MemoryKit",
            dependencies: ["Core", .product(name: "SQLite", package: "SQLite.swift")]
        ),
        
        .target(
            name: "ProviderKit",
            dependencies: ["Core", "PromptKit"]  // Uses PromptKit for system prompts
        ),
        
        .target(
            name: "SystemKit",
            dependencies: []  // Standalone macOS integration
        ),
        
        .target(
            name: "SecurityKit",
            dependencies: []  // Standalone security utilities
        ),
        
        .target(
            name: "ChannelKit",
            dependencies: ["Core", "PromptKit"]  // Uses PromptKit for channel prompts
        ),
        
        // ═══════════════════════════════════════════════════════════════
        // EVERYDAY LIFE MODULES - For non-technical users
        // ═══════════════════════════════════════════════════════════════
        
        .target(
            name: "EverydayKit",
            dependencies: ["Core", "PromptKit"]  // Calendar, reminders, contacts, etc.
        ),
        
        .target(
            name: "OnboardingKit",
            dependencies: ["Core", "PromptKit", "IdentityKit"]  // First-time user experience
        ),
        
        .target(
            name: "PrivacyKit",
            dependencies: ["Core", "PromptKit", "SecurityKit"]  // Privacy dashboard & controls
        ),
        
        // ═══════════════════════════════════════════════════════════════
        // COMPOSED MODULES - Depend on Core + specific kits
        // ═══════════════════════════════════════════════════════════════
        
        .target(
            name: "BotKit",
            dependencies: ["Core", "PromptKit", "MemoryKit", "ToolKit"]
        ),
        
        .target(
            name: "ToolKit",
            dependencies: ["Core", "PromptKit", "MemoryKit", "SystemKit", "EverydayKit"]  // + EverydayKit
        ),
        
        .target(
            name: "IdentityKit",
            dependencies: ["Core", "PromptKit"]
        ),
        
        .target(
            name: "RoutineKit",
            dependencies: ["Core", "PromptKit", "MemoryKit"]
        ),
        
        // ═══════════════════════════════════════════════════════════════
        // ORCHESTRATION - Depends on Core + BotKit + PromptKit
        // ═══════════════════════════════════════════════════════════════
        
        .target(
            name: "FleetKit",
            dependencies: ["Core", "PromptKit", "BotKit", "ProviderKit"]
        ),
        
        // ═══════════════════════════════════════════════════════════════
        // APP - Composition root, assembles all blocks
        // ═══════════════════════════════════════════════════════════════
        
        .target(
            name: "NanofolksApp",
            dependencies: [
                "Core", "PromptKit", "BotKit", "FleetKit", "MemoryKit",
                "ProviderKit", "ToolKit", "ChannelKit",
                "SystemKit", "SecurityKit", "IdentityKit", "RoutineKit"
            ]
        ),
        
        .target(
            name: "NanofolksCLI",
            dependencies: ["FleetKit", "ChannelKit"]
        ),
        
        // ═══════════════════════════════════════════════════════════════
        // TESTS
        // ═══════════════════════════════════════════════════════════════
        
        .testTarget(name: "CoreTests", dependencies: ["Core"]),
        .testTarget(name: "PromptKitTests", dependencies: ["PromptKit"]),
        .testTarget(name: "BotKitTests", dependencies: ["BotKit"]),
        .testTarget(name: "FleetKitTests", dependencies: ["FleetKit"]),
        .testTarget(name: "MemoryKitTests", dependencies: ["MemoryKit"]),
        .testTarget(name: "ProviderKitTests", dependencies: ["ProviderKit"]),
        .testTarget(name: "ToolKitTests", dependencies: ["ToolKit"]),
        .testTarget(name: "SystemKitTests", dependencies: ["SystemKit"]),
        .testTarget(name: "EverydayKitTests", dependencies: ["EverydayKit"]),
        .testTarget(name: "OnboardingKitTests", dependencies: ["OnboardingKit"]),
        .testTarget(name: "PrivacyKitTests", dependencies: ["PrivacyKit"]),
        .testTarget(name: "IdentityKitTests", dependencies: ["IdentityKit"]),
        .testTarget(name: "IntegrationTests", dependencies: ["NanofolksApp"]),
    ]
)

### Module Dependency Summary

| Module | Dependencies | Can Use Standalone |
|--------|-------------|---------------------|
| Core | None | ✅ Yes |
| PromptKit | Core | ✅ Yes |
| MemoryKit | Core | ✅ Yes |
| ProviderKit | Core, PromptKit | ✅ Yes |
| SystemKit | None | ✅ Yes |
| SecurityKit | None | ✅ Yes |
| ChannelKit | Core, PromptKit | ✅ Yes |
| **EverydayKit** | Core, PromptKit | ✅ Yes (Calendar, etc.) |
| **OnboardingKit** | Core, PromptKit, IdentityKit | ✅ Yes (First-time UX) |
| **PrivacyKit** | Core, PromptKit, SecurityKit | ✅ Yes (Privacy dashboard) |
| ToolKit | Core, PromptKit, MemoryKit, SystemKit, EverydayKit | ⚠️ Partial |
| BotKit | Core, PromptKit, MemoryKit, ToolKit | ⚠️ Partial |
| IdentityKit | Core, PromptKit | ✅ Yes (Team management) |
| RoutineKit | Core, PromptKit, MemoryKit | ✅ Yes |
| FleetKit | Core, PromptKit, BotKit, ProviderKit | ❌ No |
| NanofolksApp | All | ❌ No (composition root) |

### Prompt System Architecture

**Principle**: All prompts are data files, completely decoupled from code. This enables:
- Hot-reload prompts without code changes
- A/B testing different prompt versions
- Localization/translation
- Version control prompts separately
- Reuse prompts across modules

**Prompt File Format**:
```markdown
# Prompts/System/smart_discuss/urgency_evaluation.md

---
meta:
  id: smart_discuss_urgency
  version: 1.0.0
  models: [gpt-4, claude-3, apple-intelligence]
  min_tokens: 100
  max_tokens: 500
  tags: [dispatch, multi-bot, urgency]
---

## Variables
- {message}: The user's message
- {bots}: List of available bots with descriptions
- {threshold}: Urgency threshold (default:0.5)

---

[Prompt content with {variable} placeholders]
```

**PromptKit Usage**:
```swift
// Load prompt from file
let prompt = try await promptLoader.load(id: "smart_discuss_urgency")

// Render with variables
let rendered = try await promptLoader.render(
    id: "smart_discuss_urgency",
    variables: [
        "message": message,
        "bots":formatBotList(bots),
        "threshold": "0.5"
    ]
)
```

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

# Create soul.md (personality & values)
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

# Create role.md (responsibilities)
cat > Bots/security/role.md << 'EOF'
# ROLE - Security Expert

## Responsibilities
- Security audits
- Vulnerability assessments
- Compliance reviews
- Privacy guidance
EOF

# Create reasoning.json (behavior config)
cat > Bots/security/reasoning.json << 'EOF'
{
  "mode": "cautionary",
  "step_by_step": true,
  "considers_risks": true,
  "provides_mitigations": true,
  "confidence_threshold": 0.9
}
EOF
```

**Step 2: Restart app** - Bot is automatically loaded!

No code changes required. The bot appears immediately with:
- Full personality (from `soul.md`)
- Defined role (from `role.md`)
- Behavior config (from `reasoning.json`)
- Tool permissions (from `tools.json`)

### Prompt Loading Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROMPT SOURCES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Bots/security/                    Prompts/Bot/base/                    │
│  ├── soul.md                       ├── system_template.md               │
│  ├── role.md                       ├── micro_turn.md                    │
│  ├── identity.md                   └── tool_instructions.md             │
│  ├── reasoning.json                                                     │
│  └── bot.json                       Prompts/System/smart_discuss/       │
│       └── behavior                  ├── urgency_evaluation.md            │
│                                      └── response_format.md              │
│                                                                          │
│  BOT-SPECIFIC                       SHARED TEMPLATES                     │
│  (per bot instance)                 (used by all bots)                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Bot Process Message:
    │
    ├── BotLoader.load("security")
    │       └──Loads: soul.md, role.md, identity.md, reasoning.json, bot.json
    │
    ├── PromptLoader.load("Bot/base/system_template.md")
    │       └── Template with placeholders: {soul}, {role}, {identity}
    │
    ├── PromptLoader.render(template, variables: {
    │       "soul": bot.soul,          // from Bots/security/soul.md
    │       "role": bot.role,          // from Bots/security/role.md
    │       "identity": bot.identity,  // from Bots/security/identity.md
    │       "behavior": bot.behavior   // from Bots/security/bot.json
    │   })
    │
    └── Send to LLM with rendered system prompt

SmartDisc Dispatch:
    │
    └── PromptLoader.load("System/smart_discuss/urgency_evaluation.md")
            └── Shared prompt used by FleetManager for all bots
```

### Key Distinction

| Source | Content | Scope |
|--------|---------|-------|
| `Bots/{name}/soul.md` | Personality, values | Bot-specific |
| `Bots/{name}/role.md` | Responsibilities | Bot-specific |
| `Bots/{name}/reasoning.json` | Behavior config | Bot-specific |
| `Prompts/Bot/base/system_template.md` | Template structure | Shared |
| `Prompts/Bot/base/micro_turn.md` | Response constraints | Shared |
| `Prompts/System/smart_discuss/urgency_evaluation.md` | Dispatch logic | Shared |

---

## Team Architecture

### Three-Layer Identity System

The system uses a three-layer identity system where **Teams** theme the same bot roles with different personalities:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IDENTITY LAYERS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Layer 1: TEAM-LEVEL (Team personality/vibe)                                │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Location: Teams/{team}/TEAM.md                                              │
│  Purpose: Team-wide context, coordination style, shared values              │
│  Example: "We are the Pirate Crew—rogue adventurers seeking treasure!"      │
│                                                                              │
│  Layer 2: TEAM-BOT-LEVEL (Bot personality per team)                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Location: Teams/{team}/{bot}_SOUL.md + {bot}_IDENTITY.md                   │
│  Purpose: Bot's personality, character name, relationships within team      │
│  Example: pirate_crew/leader_SOUL.md → Captain Blackbeard                  │
│           space_crew/leader_SOUL.md → Mission Commander                     │
│                                                                              │
│  Layer 3: BOT-LEVEL (Capabilities, same across all teams)                   │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Location: Roles/{bot}_ROLE.md + Agents/{bot}_AGENTS.md                     │
│  Purpose: Bot's capabilities, constraints, hard bans, agent coordination   │
│  Example: Roles/leader_ROLE.md → Can invoke bots, max 3 concurrent tasks   │
│                                                                              │
│  Override: WORKSPACE-LEVEL (User customizations)                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Location: Workspace/Bots/{bot}/                                            │
│  Purpose: User can override SOUL.md, IDENTITY.md per bot                    │
│  Example: Workspace/Bots/leader/SOUL.md → User's custom leader personality  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Team Examples

| Bot Role | Pirate Crew | Space Crew | Executive Suite | Rock Band |
|----------|-------------|------------|-----------------|-----------|
| leader | Captain Blackbeard | Mission Commander | CEO | Lead Singer |
| researcher | Navigator Sparrow | Science Officer Nova | VP Research | Musical Director |
| coder | Gunner Cannonball | Engineer Tech | CTO | Sound Engineer |
| social | Lookout Eagle Eye | Communications Link | CMO | Promoter |
| creative | Artist Seawolf | Visionary Star | Creative Director | Songwriter |
| auditor | Quartermaster One-Eye | Safety Officer Guardian | CFO | Producer |

### File Structure for Teams

```swift
// Teams/pirate_crew/TEAM.md
We are the Pirate Crew—rogue adventurers seeking digital treasure! 
We lead with bold strategy and a bit of swashbuckling spirit.

Sidekicks are internal helpers used to speed up focused work.
The main bots always merge results and speak to the room in their own voice.

// Teams/pirate_crew/leader_SOUL.md
# SOUL.md - Captain

🏴‍☠️ **Captain**

You are the Captain of this crew, leading us to treasure and adventure!

## Vibe
Commanding, bold, adventurous. You're the leader the crew wants on the voyage.

// Teams/pirate_crew/leader_IDENTITY.md
# IDENTITY.md - Captain

**Name:** Blackbeard
**Creature:** Captain
**Vibe:** Commanding, bold, adventurous, decisive
**Emoji:** 🏴‍☠️

## Relationship with the Crew
- **Navigator (Sparrow):** Your trusted first mate...
- **Gunner (Cannonball):** Reliable and eager for action...

// Roles/leader_ROLE.md (SAME for all teams)
# ROLE.md - Leader

## Domain
**Primary:** Coordination

## Capabilities
- ✅ Can invoke other bots: **YES**
- ✅ Can do routines: **YES**
- ✅ Max concurrent tasks: **3**

## HARD BANS
🚫 **No deploying to production without approval**
🚫 **No making final decisions on legal/compliance issues without user confirmation**
```

### Team Loading Flow

```swift
// IdentityKit/TeamManager.swift
public actor TeamManager {
    private var currentTeam: String = "pirate_crew"
    private let teamsDirectory: URL
    private let rolesDirectory: URL
    private let workspaceDirectory: URL
    
    public func selectTeam(_ teamName: String) async throws {
        currentTeam = teamName
        // Save selection
        try await saveTeamSelection(teamName)
    }
    
    public func getBotTeamProfile(botRole: String) async throws -> TeamProfile {
        // Layer 1: Team-level context
        let teamContext = try await loadTeamContext(currentTeam)
        
        // Layer 2: Team-bot personality
        let soul = try await loadBotSoul(
            team: currentTeam,
            bot: botRole,
            workspaceOverride: workspaceDirectory
        )
        let identity = try await loadBotIdentity(
            team: currentTeam,
            bot: botRole,
            workspaceOverride: workspaceDirectory
        )
        
        // Layer 3: Bot-level capabilities (same for all teams)
        let role = try await loadBotRole(bot: botRole)
        let agents = try await loadBotAgents(bot: botRole)
        
        return TeamProfile(
            botRole: botRole,
            teamName: currentTeam,
            botName: identity.name,          // e.g., "Blackbeard"
            botTitle: identity.title,        // e.g., "Captain"
            emoji: identity.emoji,          // e.g., "🏴‍☠️"
            personality: soul.vibe,
            greeting: soul.greeting,
            voice: soul.voice,
            roleCard: role,
            reasoning: identity.reasoning,
            permissions: role.permissions,
            sources: [
                "team": teamContext.file.path,
                "soul": soul.file.path,
                "identity": identity.file.path,
                "role": role.file.path
            ]
        )
    }
    
    private func loadBotSoul(
        team: String,
        bot: String,
        workspaceOverride: URL?
    ) async throws -> Soul {
        // Priority: workspace override > team template
        if let workspace = workspaceOverride {
            let workspacePath = workspace
                .appendingPathComponent("Bots")
                .appendingPathComponent(bot)
                .appendingPathComponent("SOUL.md")
            if FileManager.default.fileExists(atPath: workspacePath.path) {
                return try SoulLoader.load(from: workspacePath)
            }
        }
        
        // Fall back to team template
        let teamPath = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("\(bot)_SOUL.md")
        return try SoulLoader.load(from: teamPath)
    }
}

// IdentityKit/TeamProfile.swift
public struct TeamProfile {
    public let botRole: String           // e.g., "leader"
    public let teamName: String          // e.g., "pirate_crew"
    public let botName: String           // e.g., "Blackbeard"
    public let botTitle: String          // e.g., "Captain"
    public let emoji: String             // e.g., "🏴‍☠️"
    public let personality: String       // From SOUL.md "Vibe"
    public let greeting: String          // From SOUL.md
    public let voice: String             // Voice directive
    public let roleCard: RoleCard        // Capabilities/constraints
    public let reasoning: ReasoningConfig
    public let permissions: ToolPermissions
    public let sources: [String: String] // Where each piece came from
}
```

### Team-Aware Bot Instantiation

```swift
// BotKit/BotFactory.swift
public struct BotFactory {
    private let teamManager: TeamManager
    private let promptLoader: PromptLoader
    
    public func createBot(role: String) async throws -> any Bot {
        // Get team-specific profile
        let profile = try await teamManager.getBotTeamProfile(botRole: role)
        
        // Load base template
        let systemTemplate = try await promptLoader.load(
            path: "Bot/base/system_template.md"
        )
        
        // Render with team-bot identity
        let systemPrompt = try promptLoader.render(
            template: systemTemplate,
            variables: [
                "team_name": profile.teamName,
                "team_context": "...",  // from TEAM.md
                "bot_name": profile.botName,      // "Blackbeard"
                "bot_title": profile.botTitle,    // "Captain"
                "bot_role": profile.botRole,      // "leader"
                "emoji": profile.emoji,           // "🏴‍☠️"
                "personality": profile.personality,
                "greeting": profile.greeting,
                "voice": profile.voice,
                "capabilities": profile.roleCard.capabilities,
                "hard_bans": profile.roleCard.hardBans
            ]
        )
        
        return ConcreteBot(
            configuration: BotConfiguration(
                name: profile.botRole,
                displayName: profile.botName,
                emoji: profile.emoji,
                systemPrompt: systemPrompt,
                permissions: profile.permissions
            )
        )
    }
}
```

### Switching Teams

```swift
// User changes team
await teamManager.selectTeam("space_crew")

// All bots reload with new personalities
let leader = try await botFactory.createBot(role: "leader")
// leader now has:
// - name: "Mission Commander"
// - emoji: "🚀"
// - personality: "Analytical, precise, mission-focused"

let coder = try await botFactory.createBot(role: "coder")
// coder now has:
// - name: "Tech"
// - emoji: "🔧"
// - personality: "Methodical, solution-oriented"
```

### Workspace Customization

Users can override team personalities without modifying templates:

```
Workspace/
├── Team/
│   └── current_team.json          # {"team": "pirate_crew"}
│
└── Bots/
    └── leader/
        ├── SOUL.md                # User's custom Captain personality
        └── IDENTITY.md            # User's custom Captain identity
```

### Built-in Teams

| Team | Theme | Vibe |
|------|-------|------|
| `pirate_crew` | Pirate adventure | Bold, swashbuckling, treasure-seeking |
| `space_crew` | Space exploration | Precise, mission-focused, scientific |
| `rock_band` | Music/creative | Creative, collaborative, expressive |
| `swat_team` | Tactical/precision | Disciplined, coordinated, efficient |
| `feral_clowder` | Cat-themed scrappy | Scrappy, resourceful, playful |
| `executive_suite` | Corporate/professional | Professional, strategic, results-driven |

---

## Everyday Life Tools (EverydayKit)

**Purpose**: Tools for non-technical users to manage everyday life, not developer tools.

### Why This Module Exists

The original plan focused on filesystem, shell, and browser tools - useful for developers but not for moms. EverydayKit provides tools that help normal people with daily tasks.

### Tool Categories

```swift
// EverydayKit/CalendarTool.swift
/// "Schedule my doctor appointment"
/// "What's on my calendar tomorrow?"
/// "Remind me about the meeting in 30 minutes"
class CalendarTool: Tool {
    // EventKit integration
    // Natural language date parsing
    // Conflict detection
}

// EverydayKit/RemindersTool.swift
/// "Add milk to my shopping list"
/// "Remind me to call mom at 5pm"
/// "What reminders do I have today?"
class RemindersTool: Tool {
    // Reminders framework integration
    // List management
    // Recurring reminders
}

// EverydayKit/ContactsTool.swift
/// "Find Sarah's phone number"
/// "What's John's email?"
/// "Add Mom as a contact"
class ContactsTool: Tool {
    // Contacts framework integration
    // Search by name, relationship
    // Create/update contacts
}

// EverydayKit/WeatherTool.swift
/// "Will I need an umbrella today?"
/// "What's the weather this weekend?"
class WeatherTool: Tool {
    // Weather API integration
    // Natural weather queries
    // Activity recommendations
}

// EverydayKit/PhotosTool.swift
/// "Find photos from last summer"
/// "Show me pictures of my cat"
/// "When did I visit the beach?"
class PhotosTool: Tool {
    // Photos framework integration
    // Search by date, location, people
    // Album management
}

// EverydayKit/MapsTool.swift
/// "How do I get to the grocery store?"
/// "What's nearby?"
/// "Find a coffee shop on my route"
class MapsTool: Tool {
    // MapKit integration
    // Directions
    // Points of interest
}

// EverydayKit/EmailDraftTool.swift
/// "Draft a reply to John about the meeting"
/// "Write an email to my boss asking for time off"
class EmailDraftTool: Tool {
    // Message framework integration
    // Draft composition
    // Template assistance
}

// EverydayKit/NotesTool.swift
/// "Note that I need to buy groceries"
/// "What did I note about the project?"
/// "Create a shopping list"
class NotesTool: Tool {
    // Notes app integration
    // List management
    // Search notes
}

// EverydayKit/HealthTool.swift
/// "Track that I took my medication"
/// "Log my symptoms"
/// "How am I feeling this week?"
class HealthTool: Tool {
    // HealthKit integration
    // Symptom tracking
    // Medication reminders
}
```

### Integration with Characters

Characters use these tools naturally in conversation:

```
User: "Schedule a doctor appointment for next Tuesday"

Captain (pirate_crew): "Aye! I'll add 'Doctor appointment' to yer calendar 
for Tuesday the 14th at 10am. Shall I set a reminder an hour before so ye 
don't be late to the ship's surgeon?"

Mission Commander (space_crew): "I've scheduled your doctor appointment 
for Tuesday at 10am. I've also blocked 30 minutes before for travel time. 
Your calendar is clear at that time. Shall I proceed?"
```

---

## Onboarding Experience (OnboardingKit)

**Purpose**: First-time user experience that makes non-technical users feel welcome and confident.

### Why This Module Exists

Non-technical users need guidance. They shouldn't see a blank chat or be asked to configure things. The app should feel like meeting new companions.

### Onboarding Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ONBOARDING FLOW                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Step 1: Welcome                                                         │
│  ────────────────────────────────────────────────────────────────────── │
│  "Welcome! Let's find the perfect companions for you."                  │
│                                                                          │
│  Step 2: Team Selection                                                  │
│  ────────────────────────────────────────────────────────────────────── │
│  "Which team vibe matches you?"                                          │
│  [🏴‍☠️ Pirate Crew] [🚀 Space Crew] [🎤 Rock Band]                        │
│  [🎯 SWAT Team] [🐱 Feral Clowder] [💼 Executive Suite]                │
│                                                                          │
│  Step 3: Character Introductions                                        │
│  ────────────────────────────────────────────────────────────────────── │
│  "Meet your companions:"                                                 │
│  [Captain Blackbeard] [Navigator Sparrow] [Gunner Cannonball]          │
│  "They'll help you with daily tasks, answer questions, and remember     │
│   what matters to you."                                                  │
│                                                                          │
│  Step 4: Guided First Conversation                                      │
│  ────────────────────────────────────────────────────────────────────── │
│  "Try asking: 'What's on my calendar today?' or 'Remind me to call mom'"│
│  [User types] → Character responds naturally                            │
│                                                                          │
│  Step 5: Permission Requests (Progressive)                              │
│  ────────────────────────────────────────────────────────────────────── │
│  "To help with your calendar, I need permission to access it."          │
│  [Allow] [Not now] [Explain why]                                        │
│                                                                          │
│  Step 6: Privacy Transparency                                           │
│  ────────────────────────────────────────────────────────────────────── │
│  "Your data stays on your Mac. Here's what stays local vs cloud..."    │
│                                                                          │
│  Step 7: You're Ready!                                                   │
│  ────────────────────────────────────────────────────────────────────── │
│  "Your companions are ready to help. Ask them anything!"                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Character Introduction Example

```swift
// OnboardingKit/CharacterIntroView.swift

/// Each character introduces themselves with personality
struct CharacterIntroduction {
    let team: String
    let character: TeamProfile
    
    func introduction() -> String {
        switch team {
        case "pirate_crew":
            return """
            Ahoy! I'm \(character.botName), the \(character.botTitle) of this crew!
            
            I'll help you navigate your daily tasks and keep the ship running smooth.
            Whether ye need to schedule something, find information, or just chat,
            I'm at yer service!
            
            What can I help ye with today?
            """
            
        case "space_crew":
            return """
            Greetings, crew member. I'm \(character.botName), Mission \(character.botTitle).
            
            I'm here to help you accomplish your objectives efficiently and effectively.
            My systems are calibrated to assist with scheduling, research, and analysis.
            
            How may I assist you?
            """
            
        // ... other teams
        }
    }
}
```

---

## Privacy & Transparency (PrivacyKit)

**Purpose**: User-facing privacy controls - not just backend security, but visible transparency.

### Privacy Dashboard

```swift
// PrivacyKit/PrivacyDashboard.swift

struct PrivacyDashboard {
    
    // ═════════════════════════════════════════════════════════════════
    // VISUAL: What Stays Local vs What Goes to Cloud
    // ═════════════════════════════════════════════════════════════════
    
    struct DataFlowVisualization {
        /// Shows users exactly where their data goes
        static func render() -> some View {
            VStack {
                Text("Your Data")
                
                // Local data (always stays on device)
                GroupBox("Stays on Your Mac 🏠") {
                    Text("✓ All conversations")
                    Text("✓ Calendar events")
                    Text("✓ Contacts")
                    Text("✓ Photos accessed")
                    Text("✓ Memory & learning")
                    Text("✓ Your preferences")
                }
                
                // Cloud data (only when necessary)
                GroupBox("Sent to Cloud ☁️") {
                    Text("• Your questions (to get answers)")
                    Text("• Usage metering (for billing)")
                    Text("• Login info (to verify you)")
                    
                    Text("\nWhy? Cloud servers help with complex questions.")
                    Text("You can limit this in Settings → Privacy")
                }
                
                Button("Export All My Data") { ... }
            }
        }
    }
    
    // ═════════════════════════════════════════════════════════════════
    // PERMISSION MANAGEMENT
    // ═════════════════════════════════════════════════════════════════
    
    struct PermissionManager {
        /// Easy toggles for each permission
        static func permissions() -> some View {
            List {
                Section("Calendar") {
                    Toggle("Allow calendar access", isOn: $calendarEnabled)
                    Text("Why? To schedule appointments and remind you.")
                }
                
                Section("Contacts") {
                    Toggle("Allow contacts access", isOn: $contactsEnabled)
                    Text("Why? To look up phone numbers and emails.")
                }
                
                Section("Photos") {
                    Toggle("Allow photos access", isOn: $photosEnabled)
                    Text("Why? To find and organize your memories.")
                }
                
                Section("Health") {
                    Toggle("Allow health data", isOn: $healthEnabled)
                    Text("Why? To track symptoms and medications.")
                }
            }
        }
    }
    
    // ═════════════════════════════════════════════════════════════════
    // COST TRANSPARENCY
    // ═════════════════════════════════════════════════════════════════
    
    struct CostDashboard {
        /// Show computing costs clearly
        
        static func usageView() -> some View {
            VStack {
                Text("This Month")
                HStack {
                    VStack {
                        Text("Local Computation")
                        Text("∞ FREE")
                        Text("(Runs on your Mac)")
                    }
                    VStack {
                        Text("Cloud Requests")
                        Text("847 / 1000")
                        ProgressView(value: 0.847)
                    }
                }
                
                Button("Use Local Only Mode") { ... }
                Text("Limits capabilities but free and private")
            }
        }
        
        static func costEstimate(for task: String) -> some View {
            VStack {
                if isLocalTask(task) {
                    Text("✓ Uses local computation (FREE)")
                } else {
                    Text("☁️ Uses cloud (~\(estimateTokens(task)) tokens)")
                    Text("You have \(remainingTokens) tokens remaining")
                }
            }
        }
    }
}
```

---

## Tiered Model Strategy

**Purpose**: Use local models for simple tasks, cloud for complex. Make this explicit and user-controllable.

### Task Classification

```swift
// ProviderKit/ModelTiering.swift

enum TaskComplexity {
    /// Runs entirely on-device (any M1+ Mac)
    case simple          // Classification, urgency eval, embeddings
    
    /// Prefer local, fallback to cloud if unavailable
    case moderate        // Simple Q&A, formatting, short responses
    
    /// Cloud only (complex reasoning)
    case complex         // Coding, analysis, long-form generation
    
    /// Always local, no cloud fallback (privacy-sensitive)
    case privacySensitive
}

enum ModelTier {
    case localAppleIntelligence  // M-series chips, macOS 14.4+
    case localOllama             // Requires Ollama running
    case cloudOpenAI             // Via proxy
    case cloudAnthropic          // Via proxy
    
    var estimatedCost: Cost {
        switch self {
        case .localAppleIntelligence, .localOllama:
            return .free
        case .cloudOpenAI, .cloudAnthropic:
            return .perToken
        }
    }
}

struct ModelSelector {
    static func selectModel(for task: TaskComplexity, userPreference: UserPreference) -> ModelTier {
        switch task {
        case .simple, .privacySensitive:
            // Always use local
            return selectLocalModel()
            
        case .moderate:
            // Prefer local, fallback to cloud
            if canUseLocal() {
                return selectLocalModel()
            }
            return selectCloudModel()
            
        case .complex:
            // Cloud only
            return selectCloudModel()
        }
    }
    
    static func canUseLocal() -> Bool {
        // Check Mac capabilities
        #if os(macOS)
        if #available(macOS 14.4, *) {
            // Apple Intelligence available
            return true
        }
        // Check for Ollama
        return isOllamaRunning()
        #else
        return false
        #endif
    }
}
```

### User Settings

```swift
struct ModelSettings {
    enum CloudUsage {
        case always           // Always use cloud for best quality
        case preferLocal      // Use local when possible (privacy + cost)
        case localOnly        // No cloud, limited capabilities
    }
    
    @AppStorage("cloudUsage") var cloudUsage: CloudUsage = .preferLocal
}
```

### Prompt Integration

```markdown
# Prompts/System/urgency_evaluation.md

---
complexity: simple
prefer_local: true
---

This prompt is used for urgency evaluation.
It should run on LOCAL models to save costs and improve latency.

If local model unavailable, fallback to cloud with user notification:
"⚠️ Using cloud for this quick task. Enable local models in Settings to save costs."
```

---

## User-Facing Learning

**Purpose**: Make memory visible. Users should know what the character learned and be able to confirm/correct/forgot.

### Learning Moments

```swift
// MemoryKit/LearningNotification.swift

struct LearningNotification {
    
    /// Character announces what it learned
    static func format(learning: Learning, botName: String) -> String {
        """
        \(botName): I learned something about you!
        
        "\(learning.content)"
        
        Is this correct? [Yes] [No, that's wrong] [Forget this]
        """
    }
    
    /// Examples:
    /// Captain: "I learned that you prefer morning meetings before 10am. Is this correct?"
    /// Navigator: "I noticed you often ask about weather on weekends. Should I remember this?"
}

// MemoryKit/LearningCategories.swift

struct LearningCategories {
    /// Organize learnings by topic for easy management
    static let categories = [
        "Preferences",     // "You prefer X", "You like Y"
        "Contacts",        // "Sarah is your sister", "John is your boss"
        "Projects",        // "You're working on X", "Project Y deadline is..."
        "Events",          // "Doctor appointment on Tuesday"
        "Health",          // "You're allergic to X", "You take Y medication"
        "Habits",          // "You usually check email in the morning"
    ]
    
    static func formatForUser() -> String {
        """
        What I've Learned About You
        
        📋 Preferences (12)
           • You prefer morning meetings before 10am
           • You like coffee from Café Nero
           ...
        
        👥 Contacts (5)
           • Sarah is your sister
           • John is your boss at Acme Inc
           ...
        
        📁 Projects (3)
           • Kitchen renovation is ongoing
           • You're planning a trip to Japan
           ...
        
        [Edit] [Export] [Delete All]
        """
    }
}
```

### Learning Confirmation Prompt

```markdown
# Prompts/UX/learning/learned_this.md

---
trigger: new_learning
format: notification
---

{bot_name} here! I learned something about you:

**"{learning_content}"**

- ✅ Yes, remember this
- ❌ No, that's not right
- 🗑️ Forget this

[View all learnings]
```

---

## Conversation Repair

**Purpose**: Non-technical users need guidance when misunderstandings happen. Characters should proactively clarify.

### Clarification Prompts

```markdown
# Prompts/UX/conversation/clarification.md

---
trigger: ambiguity_detected
---

{bot_name}: Let me make sure I understood correctly...

You're asking about {topic}, right? Here's what I think you want:

**{interpreted_request}**

Is that correct?

- ✓ Yes, exactly
- ✗ No, let me rephrase
- ? I'm not sure, explain more options
```

```markdown
# Prompts/UX/conversation/misunderstood.md

---
trigger: confidence_low
---

{bot_name}: I want to make sure I help you correctly.

"{user_message}"

I'm not 100% sure what you mean by "{unclear_term}". Could you:
- Explain it in different words
- Give me an example
- Or I can suggest: {suggestions}
```

```markdown
# Prompts/UX/conversation/simplify.md

---
trigger: technical_concept
---

{bot_name}: I noticed I started using technical terms. Let me explain that simpler:

**Instead of:** {technical_explanation}
**Think of it like:** {simple_analogy}

Does that make more sense?
```

---

## V1 Parity Matrix

**Legend**: ✅ Implemented, 🟡 Partial, ⚪ Scaffold, ❌ Missing

### Core Runtime & Orchestration

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Fleet management (replaces Agent) | `bots/fleet.py` | ✅ `FleetKit/FleetManager.swift` | `FleetKit/FleetManager.swift` | Implemented core lifecycle + dispatch wiring |
| Message routing | `agent/message_router.py` | 🟡 `FleetKit/MessageRouter.swift` | `FleetKit/MessageRouter.swift` | Contains placeholder decision mapping and send path |
| Intent detection + flow router | `agent/intent_detector.py`, `agent/intent_flow_router.py` | ❌ Not implemented | `FleetKit/Intent/` | No Swift intent flow module yet |
| Project state + phases | `agent/project_state.py` | ❌ Not implemented | `FleetKit/ProjectState.swift` | No project phase persistence in Swift yet |
| Multi-bot coordination | `agent/multi_bot_generator.py`, `bots/coordination.py` | 🟡 Partial | `FleetKit/MultiBot/` | SmartDispatch exists, but no dedicated coordination channel module |
| Tag parsing system | `systems/tag_handler.py` | ❌ Not implemented | `Core/TagHandler.swift` | No tag handler file in Swift |
| SmartDiscuss | `bots/smart_dispatch.py` | ✅ `FleetKit/SmartDispatch.swift` | `FleetKit/SmartDispatch.swift` | Implemented with LLM scoring + threshold routing |

---

### Rooms, Sessions, Messaging, Broker

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Room manager + mappings | `bots/room_manager.py` | 🟡 Protocol only (`Core/ChannelProtocol.swift`) + CLI `StubRoomManager` | `Core/RoomManager.swift` | No production room manager implementation yet |
| Room model | `models/room.py` | ✅ `Core/CoreTypes.swift` (`Room`) | `Core/Models/Room.swift` | Basic struct exists (not SwiftData model) |
| Room-centric sessions | `session/room_session_manager.py` | ✅ `FleetKit/RoomSessionManager.swift` | `FleetKit/RoomSessionManager.swift` | Implemented in-memory actor with timeout cleanup |
| CAS storage | `storage/cas_storage.py` | ❌ Not implemented | `MemoryKit/CASStorage.swift` | Missing |
| Per-room broker | `broker/room_broker.py` | ❌ Not implemented | `Core/RoomBroker.swift` | Missing |
| Group commit | `broker/group_commit.py` | ❌ Not implemented | `Core/GroupCommit.swift` | Missing |
| Bus + queue | `bus/*` | ❌ Not implemented | `Core/EventBus.swift` | Missing |
| Bot DM rooms | `bots/dm_room_manager.py` | ❌ Not implemented | `Core/DMRooms.swift` | Missing |

---

### Bots & Fleet Architecture

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| File-based bot system | N/A (new) | 🟡 Partial (`BotLoader`, `BotFactory`, `BotParsers`) | `BotKit/` + `Teams/` + `Roles/` | Runtime exists; shipped content coverage is minimal |
| Bot loader + factory | `bots/dispatch.py` | ✅ `BotKit/` | `BotKit/` | Implemented with actor-based loader/factory |
| Bot protocol + core | `agent/loop.py` | ✅ `Core/BotProtocol.swift` | `Core/BotProtocol.swift` | Implemented protocol surface |
| Fleet management | `bots/fleet.py` | ✅ `FleetKit/FleetManager.swift` | `FleetKit/FleetManager.swift` | Implemented |
| Message routing | `agent/message_router.py` | 🟡 `FleetKit/MessageRouter.swift` | `FleetKit/MessageRouter.swift` | Partial due to placeholder logic |
| Dispatch logic | `bots/dispatch.py` | ❌ Not implemented as separate module | `Core/DispatchMode.swift` | Routing decisions exist but no dedicated dispatch module/type |
| SmartDiscuss | `bots/smart_dispatch.py` | ✅ `FleetKit/SmartDispatch.swift` | `FleetKit/SmartDispatch.swift` | Implemented |
| Bot coordination channel | `bots/coordination.py` | ❌ Not implemented | `Core/CoordinationChannel.swift` | Missing |
| Room-centric sessions | `session/room_session_manager.py` | ✅ `FleetKit/RoomSessionManager.swift` | `FleetKit/RoomSessionManager.swift` | Implemented |

---

## File-Based Bot Architecture Benefits

> **Current Swift reality**: the architecture supports file-based loading, but the project has not yet reached full "zero-code bot creation" readiness because parser completeness, validation, and content coverage are still in progress.

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

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Memory store + models | `memory/store.py`, `memory/models.py` | 🟡 `MemoryKit/MemoryStore.swift` | `MemoryKit/Store.swift`, `MemoryKit/Models.swift` | In-memory path works; SQLite path mostly placeholder |
| Embeddings + vector index | `memory/embeddings.py`, `memory/vector_index.py` | ⚪ Protocols only | `MemoryKit/Embeddings.swift`, `MemoryKit/VectorIndex.swift` | No concrete vector index implementation |
| Retrieval + summaries + graph | `memory/retrieval.py`, `memory/summaries.py`, `memory/graph.py` | ❌ Not implemented | `MemoryKit/Retrieval.swift`, `MemoryKit/Summaries.swift`, `MemoryKit/Graph.swift` | Missing |
| Background jobs | `memory/background.py` | ❌ Not implemented | `MemoryKit/Background.swift` | Missing |

---

### Tools, Skills, MCP

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Tool registry + base tools | `agent/tools/*.py` | ⚪ `ToolKit/ToolKit.swift` scaffold | `ToolKit/` | No concrete tool registry/tools yet |
| Tool permissions | `agent/tools/permissions.py` | ⚪ Not implemented | `ToolKit/Permissions.swift` | Missing |
| MCP client | `agent/tools/mcp.py` | ⚪ Not implemented | `ToolKit/MCP/MCPClient.swift` | Missing |
| Skill packs | `skills/*` | ⚪ Not implemented | `ToolKit/Skills/` | Missing |

---

### Security

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Keyring + keyvault | `security/keyring_manager.py`, `security/keyvault.py` | 🟡 `SecurityKit/Keyring.swift` | `SecurityKit/Keyring.swift`, `SecurityKit/KeyVault.swift` | Keyring exists; KeyVault missing |
| Secure memory + sanitization | `security/secure_memory.py`, `security/sanitizer.py` | ❌ Not implemented | `SecurityKit/SecureMemory.swift`, `SecurityKit/Sanitizer.swift` | Missing |
| Credential detection + audit | `security/credential_detector.py`, `security/audit_logger.py` | 🟡 Partial (`AuditLogger` in `Keyring.swift`) | `SecurityKit/CredentialDetector.swift`, `SecurityKit/AuditLogger.swift` | Audit logger exists; detector missing |
| Symbolic converter | `security/symbolic_converter.py` | ❌ Not implemented | `SecurityKit/SymbolicConverter.swift` | Missing |

---

### Everyday Life Tools (NEW)

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Everyday tools module | N/A (new) | ⚪ `EverydayKit/EverydayKit.swift` scaffold | `EverydayKit/*.swift` concrete tools | No concrete tool implementations yet |
| Calendar / Reminders / Contacts / Weather / Photos / Maps / Email / Notes / Health | N/A (new) | ❌ Not implemented | `EverydayKit/*Tool.swift` | Planned only |

---

### Onboarding (NEW)

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Onboarding module | N/A (new) | ⚪ `OnboardingKit/OnboardingKit.swift` scaffold | `OnboardingKit/*` views/flows | No concrete onboarding implementation yet |
| Team selection / intro / first chat / permissions / tutorial | N/A (new) | ❌ Not implemented | `OnboardingKit/*.swift` | Planned only |

---

### Privacy & Transparency (NEW)

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Privacy module | N/A (new) | ⚪ `PrivacyKit/PrivacyKit.swift` scaffold | `PrivacyKit/*` | No concrete privacy dashboard features yet |
| Privacy dashboard / data-flow / permissions / export / cost dashboard | N/A (new) | ❌ Not implemented | `PrivacyKit/*.swift` | Planned only |
| Learning notifications/categories UX | N/A (new) | ❌ Not implemented | `MemoryKit/Learning*.swift` | Missing |

---

### Tiered Model Strategy (NEW)

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Model tiering | N/A (new) | ⚪ Protocol surface in `Core/LLMProviderProtocol.swift` only | `ProviderKit/ModelTiering.swift` | No concrete strategy implementation |
| Local model selection | N/A (new) | ❌ Not implemented | `ProviderKit/LocalModelSelector.swift` | Missing |
| Cost estimation | N/A (new) | ❌ Not implemented | `ProviderKit/CostEstimator.swift` | Missing |
| Local fallback | N/A (new) | ❌ Not implemented | `ProviderKit/LocalFallback.swift` | Missing |

---

### Providers and Channels

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Provider registry + LLM | `providers/*` | 🟡 OpenAI provider only (`ProviderKit/OpenAIProvider.swift`) | `ProviderKit/` | Single provider; no registry/factory implementation |
| Channel manager + connectors | `channels/*` | ⚪ `ChannelKit/ChannelKit.swift` scaffold | `ChannelKit/` | No concrete channel handlers |

---

### Identity, Teams, Templates, Soul

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Team manager | `teams/manager.py` | 🟡 `IdentityKit/TeamManager.swift` | `IdentityKit/TeamManager.swift` | Selection/loading exists; parser outputs are currently stubbed |
| Team profiles | `teams/profiles.py` | ✅ Core types exist (`TeamProfile`, `BotTeamProfile`) | `IdentityKit/TeamProfile.swift` | Types present, richer profile subsystem pending |
| Template discovery | `templates/discovery.py` | ❌ Not implemented | `IdentityKit/TemplateDiscovery.swift` | Missing |
| SOUL loader | `soul/manager.py` | 🟡 Inlined in `TeamManager`/`BotLoader` | `IdentityKit/SoulLoader.swift` | Dedicated loader missing |
| Identity + role parsing | `identity/role_parser.py`, `models/role_card.py` | 🟡 Partial parser code in `BotKit/BotParsers.swift`; stub parser in `IdentityKit/TeamManager.swift` | `IdentityKit/RoleParser.swift` | Incomplete and split across modules |
| Relationship parsing | `identity/relationship_parser.py` | ❌ Not implemented | `IdentityKit/RelationshipParser.swift` | Missing |
| Workspace override | `workspace/bots/` | 🟡 Path support present | `Workspace/Bots/` | Mechanism exists; shipped workspace content minimal |

---

### Routines & Scheduling

| Subsystem | Python Source | Swift Current | Swift v1 Target | Current Parity Notes |
|---|---|---|---|---|
| Routines service + types | `routines/*` | ⚪ `RoutineKit/RoutineKit.swift` scaffold | `RoutineKit/Service.swift`, `RoutineKit/Models.swift` | Missing |
| Team routines manager | `routines/team/*` | ❌ Not implemented | `RoutineKit/TeamRoutines.swift` | Missing |
| Dashboard server | `routines/team/dashboard_server.py` | ❌ Not implemented | `RoutineKit/Dashboard.swift` | Missing |

---

### Local Models & Intelligence Layer

**Current status**: local model providers are **not implemented yet** in Swift.

**Target direction**: leverage the same local-model capabilities used in Python.

#### Supported Local Models (from existing Python, for Swift roadmap)

| Provider | Implementation | Swift Integration |
|----------|---------------|------------------|
| **Ollama** | OpenAI-compatible API | URLSession → `http://localhost:11434/v1/chat/completions` |
| **LM Studio** | OpenAI-compatible API | URLSession → `http://localhost:1234/v1/chat/completions` |
| **llama.cpp server** | OpenAI-compatible API | URLSession → `http://localhost:8080/v1/chat/completions` |
| **Apple Foundation Models** | Native Apple Silicon | Use `LLM` framework (macOS 14.4+) |

#### Proposed Swift Provider Architecture (Roadmap)

> The following snippets are pseudocode to illustrate architecture direction.

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

#### Local Embeddings (Roadmap)

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

#### Config Integration (Roadmap)

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

#### Fallback Strategy (Roadmap)

Your Python code already implements fallback (local first → API). Swift can do the same:

```swift
func chatWithFallback(messages: [Message]) async throws -> LLMResponse {
    let request = LLMRequest(messages: messages)

    // Try local first
    if config.useLocalModel {
        do {
            return try await localProvider.chat(request: request)
        } catch {
            logger.warning("Local model failed: \(error), falling back to API")
        }
    }
    // Fallback to cloud API
    return try await cloudProvider.chat(request: request)
}
```

---

## Python Dependencies → Swift Mapping (Proposed)

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

## Dependency Summary (Current vs Planned)

### External Dependencies (Swift Packages)

**Current state (March 13, 2026):** `Package.swift` has no external package dependencies declared yet.

**Planned candidates:**

| Package | Purpose | Planned For | macOS Support |
|---------|---------|---------|---------------|
| **swift-embeddings** | Native MLX embeddings (bge-small) | MemoryKit | Native (MLX) |
| SQLite.swift | Database | MemoryKit | Native |
| swift-log | Structured logging | Core | Native |
| MLX | MLX framework (for swift-embeddings) | MemoryKit | Native (Apple Silicon) |

### Module Architecture (Target Design)

| Strategy | Count (Target) | Examples |
|----------|-------|----------|
| **Zero dependencies (Core)** | 1 | Core (protocols only) |
| **Standalone modules** | 5 | SystemKit, SecurityKit, MemoryKit, ProviderKit, ChannelKit |
| **Composed modules** | 3 | ToolKit, BotKit, RoutineKit |
| **Orchestration** | 1 | FleetKit |
| **App assembly** | 1 | NanofolksApp (composition root, not implemented yet) |

### Built-in Frameworks (Potential Usage)

| Framework | Usage |
|-----------|-------|
| Foundation | Core utilities |
| SwiftUI | UI framework |
| SwiftData | Persistence (macOS 14+) |
| Combine | Reactive programming |
| Security | Keychain, encryption |
| UserNotifications | System notifications |
| SafariServices | Browser integration |
| Accessibility | UI automation |
| Speech | Voice input/output |
| EventKit | Calendar integration |
| Intents | Shortcuts integration |
| LLM | Apple Intelligence (macOS 14.4+, Apple Silicon only) |

---

## System Control Layer (Roadmap Differentiator)

This is where Swift can differentiate vs Go/Python once implemented:

### macOS APIs to Leverage (Planned)

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

### Browser Automation Strategy (Planned)

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

### File System Tools (Example Design)

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

**Current Swift implementation**: urgency-based bot selection exists in `FleetKit/SmartDispatch.swift`.

**Not implemented yet**: a full tagged dispatch mode (`@discuss`) integrated with channel-level routing and mode selection.

**Target behavior** for SmartDiscuss (`@discuss`):
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

### Proposed Full Swift Implementation (Roadmap)

> Pseudocode example for the target integrated `@discuss` flow.

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

### Fallback Strategy (Roadmap)

```swift
if llmProvider.available {
    return await evaluateWithLLM(message, participants)
} else {
    // Fallback to rule-based keyword matching
    return evaluateWithRules(message, participants)
}
```

### Integration with Swift Features (Roadmap)

- **Apple Intelligence**: Uses local on-device LLM for urgency evaluation
- **Swift Concurrency**: Parallel urgency evaluation with async/await
- **SwiftData**: Cache urgency patterns for repeated queries

---

## macOS-Specific Features

**Current status**: no `NanofolksApp` target/source exists yet.

### Menu Bar Agent Mode (Planned)

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

### Touch Bar Support (if applicable, planned)

### Notifications & Haptics (planned)

### Keyboard Shortcuts (planned)

### Share Extensions (planned)

---

## Dependencies

### Swift Package Manager

**Current status**: these are planned dependencies; not all are declared in `Package.swift` yet.

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

> **Design Philosophy**: Build independent modules first, then compose them. Each module should be testable in isolation and usable standalone. The CLI serves as the first integration point for validating module composition.

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

### Module Build Order (Historical Plan)

> This checklist reflects the original phased plan. For current real implementation status, use the "Implementation Status" section below.

**Phase 0: Core Foundation (Week 1)**
- [ ] Core module (protocols only, no implementation)
  - BotProtocol, LLMProvider, ToolProtocol, MemoryProtocol
  - Core models: Message, Response, BotConfiguration, Room
  - Core types: BotID, RoomID, DispatchMode, EventBus
- [ ] PromptKit module (prompt management)
  - PromptLoader: loads prompts from files
  - PromptParser: parses YAML frontmatter
  - PromptRenderer: variable substitution
  - PromptCache: caching system
  - PromptValidator: validates prompts
  - PromptHotReload: hot reload capability
- [ ] Create base prompts structure
  - Prompts/System/smart_discuss/
  - Prompts/System/intent/
  - Prompts/System/memory/
  - Prompts/Bot/base/
  - Prompts/_templates/

**Phase 1: Standalone Modules (Weeks 2-4)**
- [ ] ProviderKit (LLM providers)
  - OpenAI provider via URLSession
  - Provider factory pattern
  - Uses PromptKit for system prompts
- [ ] SystemKit (macOS integration)
  - Filesystem, Shell, Workspace tools
  - Standalone, no dependencies
- [ ] SecurityKit (security utilities)
  - Keyring, KeyVault, Sanitizer
  - Standalone, no dependencies
- [ ] MemoryKit (storage)
  - SQLite-based memory store
  - Embeddings (swift-embeddings)
  - Vector index
- [ ] ChannelKit (messaging channels)
  - CLI channel first
  - WebSocket channel base
  - Uses PromptKit for channel prompts

**Phase 2: Composed Modules (Weeks 5-6)**
- [ ] ToolKit (depends on Core + PromptKit + MemoryKit + SystemKit)
  - Registry, Permissions, Base tools
  - Uses PromptKit for tool instructions
  - MCP client
- [ ] BotKit (depends on Core + PromptKit + MemoryKit + ToolKit)
  - BotLoader, BotFactory, ConcreteBot
  - File-based bot system
  - Loads prompts from PromptKit
- [ ] IdentityKit (depends on Core + PromptKit)
  - TeamManager, SoulManager, RoleParser

**Phase 3: Orchestration (Weeks 7-8)**
- [ ] FleetKit (depends on Core + PromptKit + BotKit + ProviderKit)
  - FleetManager, MessageRouter
  - SmartDispatch, ResponseCombiner
  - Uses PromptKit for urgency evaluation, response formatting

**Phase 4: Integration & CLI (Weeks 9-10)** 🟡 PARTIALLY COMPLETE
- [x] **NanofolksCLI** - Basic CLI tool for testing (NOT full REPL)
  - ✅ Composition root - wire up all modules
  - ✅ Simple command: `swift run nanofolks-cli --team pirate_crew --api-key <key>`
  - ✅ Basic chat loop: user types → bot responds
  - ✅ Minimal formatting, basic output
  - ✅ Exit command (`exit` or `quit`)
  - ✅ Bot loading from Teams/ directory
  - ✅ OpenAI integration with API key
  - ✅ **Purpose**: Test FleetKit + BotKit + ProviderKit + IdentityKit integration
  - ⚠️ **Current caveat**: CLI still uses a stub room manager and incomplete template data
  - **Scope**: Kept simple - no fancy REPL features (history, autocomplete, etc.)

> **Note**: Full REPL with history, autocomplete, arrow keys, etc. is **Phase X (Future)**. Python implementation showed this is complex and not well-integrated. Focus on simple CLI for testing now, proper REPL later if needed.

**Phase 5: Desktop App (Weeks 11-14)**
- [ ] NanofolksApp
  - SwiftUI views
  - Settings UI
  - Menu bar integration
  - Uses PromptKit for UX messages

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
| **Multi-Bot Architecture** | 🟡 Fleet foundation implemented (partial) | N/A | ✅ Fleet-based (COMPLETE) |
| **SmartDiscuss (@discuss)** | 🟡 Urgency evaluator implemented; full mode integration pending | N/A | ✅ LLM-based (COMPLETE) |
| **File-Based Bots** | 🟡 Loader/parsers implemented; full content/validation pending | N/A | ✅ Zero-code (COMPLETE) |
| **Modular Architecture** | ✅ Strong package/module foundation | N/A | ⚠️ Monolithic |

---

## Composability Benefits Summary

### Why Lego Block Architecture?

> Most items in this section are target-state benefits. The architecture foundation exists, but full isolation/reuse claims depend on filling current module gaps.

**1. Independent Testing**
```swift
// Example using current concrete store
let memory = InMemoryStore()
let results = try await memory.search(query: "test", limit: 5)
XCTAssertTrue(results.isEmpty)

// Provider test example (interface-level)
let provider = MockProvider()
let response = try await provider.chat(request: LLMRequest(messages: []))
XCTAssertNotNil(response)
```

**2. Reusability**
- `MemoryKit` can be used in any app needing vector storage
- `ProviderKit` can be used in any LLM-based app
- `SystemKit` can be used in any macOS automation tool
- `SecurityKit` can be used in any app needing keychain/encryption

**3. Easy Swapping**
```swift
// Pseudocode illustrating dependency inversion
// Swap OpenAI for Anthropic - change one line
let provider: LLMProvider = AnthropicProvider()  // was: OpenAIProvider()

// Swap SQLite for SwiftData - change MemoryStore implementation
let memory: MemoryStoring = SwiftDataMemoryStore()  // was: SQLiteMemoryStore()
```

**4. Incremental Migration**
- Can port Python modules one at a time
- Each `*Kit` can be developed independently
- No big-bang rewrite required

**5. Clear Boundaries**
- Each module has a single responsibility
- Dependencies flow inward to Core
- No circular dependencies possible

### Module Isolation Guarantees

| Module | Isolation Level | Can Use In Other Projects |
|--------|----------------|---------------------------|
| Core | **100% isolated** | ✅ Yes - protocol definitions |
| PromptKit | **100% isolated** | ✅ Yes - prompt loading/rendering |
| SystemKit | **100% isolated** | ✅ Yes - macOS tools |
| SecurityKit | **100% isolated** | ✅ Yes - security utilities |
| MemoryKit | **Core dependency only** | ✅ Yes - vector storage |
| ProviderKit | **Core + PromptKit** | ✅ Yes - LLM clients |
| ChannelKit | **Core + PromptKit** | ✅ Yes - messaging |
| ToolKit | **Core + PromptKit + MemoryKit + SystemKit** | ⚠️ Partial - needs context |
| BotKit | **Core + PromptKit + MemoryKit + ToolKit** | ⚠️ Partial - needs tools |
| IdentityKit | **Core + PromptKit** | ✅ Yes - identity management |
| RoutineKit | **Core + PromptKit + MemoryKit** | ✅ Yes - scheduling |
| FleetKit | **All dependencies** | ❌ No - orchestration only |

---

## Prompt System Benefits

### Why Separate Prompts from Code?

> Target-state benefits below; current PromptKit implementation is partial and does not yet provide full hot-reload/validation workflows.

**1. Hot Reloading (target)**
```swift
// Target behavior:
// Change prompt file, app reflects changes immediately
// No rebuild, no restart needed
let promptLoader = PromptLoader(promptsDirectory: "Prompts/")
try await promptLoader.reload()
```

**2. Version Control**
```bash
# Prompts are tracked separately from code
git add Prompts/System/smart_discuss/urgency_evaluation.md
git commit -m "Improve urgency evaluation prompt"
```

**3. A/B Testing**
```swift
// Test different prompt versions
let promptV1 = try await promptLoader.load(id: "smart_discuss_urgency_v1")
let promptV2 = try await promptLoader.load(id: "smart_discuss_urgency_v2")

// Compare results...
```

**4. Localization**
```
Prompts/
├── en/
│   └── System/smart_discuss/urgency_evaluation.md
├── es/
│   └── System/smart_discuss/urgency_evaluation.md
└── ja/
    └── System/smart_discuss/urgency_evaluation.md
```

**5. Reusability Across Modules**
```swift
// Same prompt used in different contexts
let systemPrompt = try await promptLoader.load(
    path: "Bot/base/system_template.md"
)

// Used by:
// - BotKit for bot system prompts
// - FleetKit for response formatting
// - ToolKit for tool instructions
```

**6. Transparency & Debugging**
```swift
// See exactly what prompt was sent to LLM
let rendered = try await promptLoader.render(
    id: "smart_discuss_urgency",
    variables: ["message": userMessage, "bots": botList]
)

print(rendered)  // Full prompt visible
```

---

## Decision Criteria

### Choose Swift if:
- macOS-native experience is primary goal
- Deep OS integration needed (browser automation, accessibility)
- You're willing to be Apple-platform-only for v1
- **Modular architecture is important** (Lego blocks approach)

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

**Status (Audit Snapshot - March 13, 2026)**: Swift implementation is **partially complete**. Core architecture compiles, but many modules are still scaffolds or stubs.
**Architecture**: Modular Lego Block Design is in place at the package/target level, but several modules are documentation-only placeholders.
**Prompts**: Prompt directory structure exists, but only a small subset of prompt files are implemented.
**Teams**: Team system is wired, but shipped content is minimal (single example team with partial bot data).
**Build**: ✅ `swift build` succeeds (all targets compile)
**Tests**: ❌ `swift test` reports no tests found (test targets exist but contain no test files)
**Next Step**: Complete parity-critical runtime modules first (MemoryKit, IdentityKit parsing, Fleet routing correctness), then implement EverydayKit/PrivacyKit/OnboardingKit and the SwiftUI app.

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

### Swift Implementation Progress 🚧 (Reality-Based)

**Started**: March 2025

**Project Structure Created** (`nanofolks-swift/`):
```
✅ Package.swift - Swift Package Manager configuration and targets
✅ Sources/ - Module directories created
✅ Tests/ - Test targets declared
⚠️ Prompts/ - Directory structure exists, but only a few prompt files currently exist
⚠️ Teams/ - Single `pirate_crew` example with leader-only assets
⚠️ Roles/ - Only `leader_ROLE.md` currently exists
⚠️ Workspace/ - Directory exists; no meaningful shipped override content yet
```

**Modules Implementation Status**:

| Module | Status | Description |
|--------|--------|-------------|
| Core | ✅ Complete | Core protocols and shared types are implemented |
| PromptKit | 🟡 Partial | Prompt loading/rendering works; parser/validation/hot-reload depth is limited |
| MemoryKit | 🟡 Partial Stub | In-memory store works; SQLite layer and vector search are mostly placeholders |
| ProviderKit | 🟡 Partial | OpenAI chat/embeddings implemented; streaming path is stubbed; no tiered/local routing implementation |
| SystemKit | 🟡 Partial Stub | Basic workspace/file/app helpers implemented; broader system tool surface not implemented |
| SecurityKit | 🟡 Partial Stub | Keychain + audit logging present; broader security suite from plan not implemented |
| IdentityKit | 🟡 Partial | Team selection exists; parser implementations are currently stubbed/empty |
| ChannelKit | ⚪ Scaffold | Module shell only, no concrete channel handlers |
| EverydayKit | ⚪ Scaffold | Module shell only, no concrete everyday tools yet |
| PrivacyKit | ⚪ Scaffold | Module shell only, no dashboard/controls implementations yet |
| RoutineKit | ⚪ Scaffold | Module shell only, no routines engine yet |
| ToolKit | ⚪ Scaffold | Module shell only, no registry/permissions/MCP implementations yet |
| BotKit | 🟡 Partial | Loader/factory/parsers implemented; data coverage and full file-based architecture are incomplete |
| OnboardingKit | ⚪ Scaffold | Module shell only, no onboarding views/flows yet |
| FleetKit | 🟡 Partial | Core orchestration exists; routing/decision details still contain placeholders |

**Core Module Created** (`Sources/Core/`):
- ✅ `CoreTypes.swift` - Message, Response, Bot, Team, Tool, Memory, Channel types
- ✅ `BotProtocol.swift` - Bot, BotFactory, BotLoader, BotCoordinator protocols
- ✅ `LLMProviderProtocol.swift` - LLMProvider, ProviderRegistry, TieredModelStrategy
- ✅ `MemoryProtocol.swift` - MemoryStore, EmbeddingService, MemoryManager
- ✅ `ToolProtocol.swift` - Tool, ToolRegistry, Calendar, Reminders, Contacts protocols
- ✅ `ChannelProtocol.swift` - ChannelHandler, ChannelManager, MessageRouter

**Prompt Structure Status** (`Prompts/`):
- ✅ Implemented files:
  - `System/smart_discuss/urgency_evaluation.md`
  - `System/memory/learned_notification.md`
  - `Bot/base/system_template.md`
- ⚠️ Many directories exist (`UX/*`, `Channels/*`, `Tools/*`) but most planned files are not yet implemented

**Team Structure Status** (`Teams/pirate_crew/`):
- ✅ `TEAM.md`, `leader_SOUL.md`, `leader_IDENTITY.md`, `leader_reasoning.json`
- ⚠️ Other bot role files for this team are not present yet

**FleetKit Module Created** (`Sources/FleetKit/`):
- ✅ `FleetManager.swift` - Manages bot instances, coordinates conversations
- ✅ `SmartDispatch.swift` - LLM-based urgency evaluation (0-1 scale, threshold 0.5)
- ✅ `ResponseCombiner.swift` - Merges multi-bot responses with attribution
- ✅ `MessageRouter.swift` - Routes messages between channels and FleetManager
- ✅ `RoomSessionManager.swift` - Room-keyed sessions with timeout (1 hour)
- ✅ `FleetKit.swift` - Module documentation

**BotKit Module Created** (`Sources/BotKit/`):
- ✅ `BotLoader.swift` - Loads bot configs from Teams/{team}/ files (SOUL.md, IDENTITY.md, reasoning.json)
- ✅ `BotFactory.swift` - Creates bot instances (FileBotFactory, CharacterBot)
- ✅ `BotParsers.swift` - Parsers for markdown files (BotSoul, BotIdentity, BotRoleCard)
- ✅ `BotKit.swift` - Module documentation

**ProviderKit Module Created** (`Sources/ProviderKit/`):
- ✅ `OpenAIProvider.swift` - OpenAI API client (chat, streaming, embeddings)
- ✅ `ProviderKit.swift` - Module documentation
- Features: Chat completions, streaming responses, embeddings, availability check

**IdentityKit Module Created** (`Sources/IdentityKit/`):
- ✅ `TeamManager.swift` - Manages team selection and bot profiles
- ✅ `IdentityKit.swift` - Module documentation
- Features: Load teams from Teams/, bot profile loading, workspace customization

**Build Status**: ✅ `swift build` succeeds (targets compile)

**CLI Module Status** (`Sources/NanofolksCLI/`):
- ✅ `main.swift` - Basic CLI executable
- ✅ Command-line argument parsing (--team, --api-key)
- ✅ System initialization (TeamManager, BotLoader, FleetManager)
- ✅ Simple chat loop with readLine()
- ✅ Exit commands (exit, quit)
- ✅ Usage: `swift run nanofolks-cli --team pirate_crew --api-key sk-...`
- ⚠️ Uses a stub room manager and depends on incomplete team data, so full multi-bot behavior is not production-ready

**Build + Test Status**:
- ✅ `swift build` succeeds
- ⚠️ Build emits package hygiene warnings (duplicate `FleetKit` product, empty test targets)
- ❌ `swift test` fails with `no tests found`

**Next Steps (Re-prioritized by Current Gaps)**:
1. Fix package hygiene and test baseline (remove duplicate product, add first real tests)
2. Complete IdentityKit parsers (Team/Soul/Identity/Role parsing from markdown)
3. Complete MemoryKit persistence (real SQLite layer, vector search, stats)
4. Harden FleetKit routing correctness (remove placeholder routing decisions, improve mapping)
5. Implement Tiered Model Strategy + local/cloud fallback in ProviderKit
6. Implement ToolKit/ChannelKit foundations (registry, permissions, first concrete channel/tool)
7. Implement EverydayKit concrete tools (calendar/reminders/contacts first)
8. Implement PrivacyKit and OnboardingKit user-facing features
9. Phase 5: Create `NanofolksApp` (SwiftUI desktop app)

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
│  CLI (direct access - basic tool)   │
│  WhatsApp Channel (via bridge)      │
│  iMessage Channel (via API)         │
└─────────────────────────────────────┘
```

### CLI vs REPL Clarification

**CLI (Command Line Interface) - What we need now:**
- Simple tool to run the system: `swift run nanofolks-cli --team pirate_crew`
- Basic chat loop: type message → get response → repeat
- Minimal features: just enough to test FleetKit + BotKit
- **Purpose**: Development/testing tool, validate module integration
- **Scope**: Keep it minimal, avoid complexity

**REPL (Read-Eval-Print Loop) - Future consideration:**
- Rich interactive prompt with history, autocomplete, arrow keys
- Command history (up/down arrows)
- Tab completion for commands
- Syntax highlighting
- **Status**: Python implementation struggled with this - complex to integrate well
- **Decision**: Defer to Phase X (Future), focus on simple CLI + SwiftUI app for now

> **Lesson from Python**: Full REPL integration was problematic. Simple CLI is sufficient for testing. Users will primarily use the SwiftUI desktop app or messaging channels (WhatsApp, iMessage).

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

---

## Target Audience Alignment

### Non-Technical User Focus (Mom-Friendly)

| Feature | Traditional Developer Focus | Nanofolks Mom-Friendly Focus |
|---------|------------------------------|------------------------------|
| **Terminology** | "LLM providers", "API endpoints" | "Companions", "Teams" |
| **Onboarding** | Technical setup, API keys | Pick your team, meet characters |
| **Tasks** | Code, files, shell commands | Calendar, reminders, weather |
| **Learning** | Backend memory only | "I learned..." notifications |
| **Privacy** | Security logs | Visual privacy dashboard |
| **Cost** | Usage hidden | "This uses X tokens" transparency |
| **Conversation** | One-shot interactions | Conversational repair |
| **Characters** | Generic bots | Pirate Captain, Navigator, etc. |

### Key Differences from Developer Tools

1. **Characters, not bots**: Captain Blackbeard, not "leader_agent_01"
2. **Everyday tasks**: Calendar, weather, shopping lists - not code
3. **Visual transparency**: "Here's what I learned" vs invisible memory
4. **Progressive onboarding**: Team selection → character intro → guided chat
5. **Privacy dashboard**: What stays local vs goes to cloud is visible
6. **Cost awareness**: Users see "This will use X tokens" before complex operations
7. **Conversation repair**: "Let me clarify..." vs silent assumptions

---

## Summary Scorecard (Current Reality)

| Objective | Implementation | Status |
|-----------|---------------|--------|
| **Non-technical users** | Mostly planned | ⚠️ Not delivered yet (onboarding/privacy UX are scaffolds) |
| **Characters, not bots** | Basic foundation | 🟡 Partial (single team with limited bot assets) |
| **Everyday life tasks** | Planned modules only | ❌ Not implemented yet |
| **Local + cloud models** | OpenAI cloud path only | 🟡 Partial (tiered/local strategy not implemented) |
| **Security as foundation** | Keychain + audit logging | 🟡 Partial |
| **Memory as learning** | Interfaces + partial store | 🟡 Partial/Stub |
| **Modular architecture** | Package/targets structured | ✅ Strong foundation |
| **Cost transparency** | Planned in PrivacyKit | ❌ Not implemented yet |

---

**Status**: Swift Implementation 🚧 (Foundation built, feature parity pending)
- Core module: ✅ Complete (protocols, types)
- PromptKit: 🟡 Partial
- FleetKit: 🟡 Partial
- BotKit: 🟡 Partial
- ProviderKit: 🟡 Partial
- IdentityKit: 🟡 Partial
- NanofolksCLI: 🟡 Basic CLI complete (dev/testing use)
- MemoryKit: 🟡 Stub/Partial
- SystemKit: 🟡 Stub/Partial
- SecurityKit: 🟡 Stub/Partial
- ChannelKit / ToolKit / RoutineKit: ⚪ Scaffold only
- EverydayKit / PrivacyKit / OnboardingKit: ⚪ Scaffold only
- Build: ✅ Compiles
- Tests: ❌ No implemented test cases yet
- Prompt files: ⚠️ Sparse (3 files currently)
- Team templates: ⚠️ Minimal (single team, leader-only bot content)
- Roles: ⚠️ Minimal (leader role file only)

**Architecture**: Modular Lego Block Design foundation is in place; user-facing modules remain largely unimplemented.
**Audience**: Non-technical user focus remains the product goal, but current implementation is still developer-facing.
**Next Step**: Close parity-critical backend/runtime gaps before building the SwiftUI app shell.

---

## Future: EverydayAutomationKit (v1.1+)

**Based on Ghost OS research** - Self-learning workflow automation for non-technical users.

### Why This Module

Ghost OS (https://github.com/ghostwright/ghost-os) demonstrates a powerful approach:
- **Accessibility tree first** - Structured data over pixel guessing
- **Self-learning recipes** - Watch user once, replay forever
- **MCP protocol** - Works with Claude Code, Cursor, any MCP client
- **~7,000 lines of Swift** - Proven architecture on macOS

**For nanofolks**: Characters learn everyday tasks from users and replay them automatically.

### Recipe System Architecture

```swift
// EverydayAutomationKit/RecipeTypes.swift

/// A parameterized, replayable workflow learned from user actions
struct Recipe: Codable {
    let schemaVersion: Int
    let name: String                    // "Send Gmail email"
    let description: String              // Human-readable description
    let app: String?                     // "Google Chrome", "Mail", etc.
    let params: [String: RecipeParam]?   // Parameterized inputs
    let preconditions: RecipePreconditions? // Must be true before run
    let steps: [RecipeStep]              // Ordered actions
    let onFailure: String?               // "stop" or "skip"
}

struct RecipeParam: Codable {
    let type: String                    // "string", "number", "email"
    let description: String              // "Email address of recipient"
    let required: Bool?
}

struct RecipePreconditions: Codable {
    let appRunning: String?             // App must be running
    let urlContains: String?            // URL must contain string
    let focusedElement: String?         // Element must be focused
}

struct RecipeStep: Codable {
    let id: Int
    let action: String                  // click, type, press, hotkey, scroll, wait
    let target: Locator?                // AXRole + computedNameContains
    let params: [String: String]?       // {{param}} substitution
    let waitAfter: RecipeWaitCondition? // Wait for state change
    let note: String?                   // Human-readable description
    let onFailure: String?             // Step-level failure handling
}

struct Locator: Codable {
    let criteria: [LocatorCriterion]?   // AXRole, AXDOMIdentifier
    let computedNameContains: String?   // Text in element name
}

struct RecipeWaitCondition: Codable {
    let condition: String               // elementExists, elementGone, urlChange, delay
    let target: Locator?
    let value: String?
    let timeout: Double?
}
```

### Example Recipe (Learned from User)

```json
{
  "schema_version": 2,
  "name": "send-gmail-email",
  "description": "Send an email via Gmail",
  "app": "Google Chrome",
  "params": {
    "recipient": {
      "type": "string",
      "description": "Email address of recipient",
      "required": true
    },
    "subject": {
      "type": "string",
      "description": "Email subject line",
      "required": true
    },
    "body": {
      "type": "string",
      "description": "Email body text",
      "required": true
    }
  },
  "preconditions": {
    "app_running": "Google Chrome",
    "url_contains": "mail.google.com"
  },
  "steps": [
    {
      "id": 1,
      "action": "click",
      "target": {
        "criteria": [{"attribute": "AXRole", "value": "AXButton"}],
        "computedNameContains": "Compose"
      },
      "wait_after": {
        "condition": "elementExists",
        "value": "To recipients",
        "timeout": 5
      },
      "note": "Open compose window"
    },
    {
      "id": 2,
      "action": "type",
      "target": {
        "criteria": [{"attribute": "AXRole", "value": "AXComboBox"}],
        "computedNameContains": "To recipients"
      },
      "params": {"text": "{{recipient}}"},
      "note": "Enter recipient email"
    },
    {
      "id": 3,
      "action": "press",
      "params": {"key": "tab"},
      "note": "Confirm autocomplete and move to Subject"
    },
    {
      "id": 4,
      "action": "type",
      "target": {"computedNameContains": "Subject"},
      "params": {"text": "{{subject}}"},
      "note": "Enter subject line"
    },
    {
      "id": 5,
      "action": "press",
      "params": {"key": "tab"},
      "note": "Move to body"
    },
    {
      "id": 6,
      "action": "type",
      "params": {"text": "{{body}}"},
      "note": "Enter email body at focus"
    },
    {
      "id": 7,
      "action": "hotkey",
      "params": {"keys": "cmd,return"},
      "wait_after": {
        "condition": "elementGone",
        "value": "Send",
        "timeout": 10
      },
      "note": "Send email with Cmd+Return"
    }
  ],
  "on_failure": "stop"
}
```

### Module Structure

```
EverydayAutomationKit/              # v1.1+ MODULE - Depends: Core, PromptKit, SystemKit
├── RecipeTypes.swift              # Data models
├── RecipeStore.swift              # JSON persistence in ~/Library/Application Support/
├── RecipeEngine.swift             # Step-by-step execution
├── RecipeSynthesizer.swift        # LLM-assisted recipe creation
│
├── Perception/                    # See what's on screen
│   ├── AXTreeReader.swift          # AXorcist integration (Accessibility tree)
│   ├── ElementFinder.swift         # Query elements by role, name, DOM id
│   ├── UIContext.swift             # Current app, window, URL, focused element
│   └── ElementInspector.swift      # Complete element metadata
│
├── Actions/                        # Execute actions
│   ├── ClickAction.swift           # Click elements
│   ├── TypeAction.swift            # Type text into fields
│   ├── PressAction.swift           # Press single keys
│   ├── HotkeyAction.swift          # Key combinations (Cmd+C, etc.)
│   ├── ScrollAction.swift          # Scroll in windows
│   ├── HoverAction.swift           # Hover over elements
│   ├── DragAction.swift            # Drag from point to point
│   ├── LongPressAction.swift       # Press and hold
│   ├── FocusAction.swift           # Bring app/window to front
│   └── WaitAction.swift            # Wait for conditions
│
├── Learning/                       # Self-learning workflows
│   ├── ActionRecorder.swift        # CGEvent tap + AX context enrichment
│   ├── ActionSynthesizer.swift     # Convert raw actions to parameterized recipes
│   ├── LearningSession.swift       # "Watch me" session management
│   └── ActionEnricher.swift        # Add AX tree context to raw events
│
├── Vision/                         # Fallback when AX tree fails
│   ├── ShowUIModel.swift           # Local vision model (ShowUI-2B)
│   ├── VisualGrounding.swift       # Find elements by sight
│   └── ScreenshotAnnotator.swift  # Number elements on screenshot
│
└── Integration/                    # Character integration
    ├── CharacterRecipeBridge.swift # Characters use recipes internally
    ├── RecipeLearning.swift        # "Watch me do this" flow
    └── RecipeSuggestion.swift      // Suggest recipes from patterns
```

### Self-Learning Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SELF-LEARNING WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User:                    "Captain, watch me send an email"            │
│                                                                          │
│  Captain (character):     "Aye! I'm watching yer every move."            │
│                           starts ActionRecorder                          │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    ACTION RECORDER                                │    │
│  │                                                                   │    │
│  │  Event tap (CGEvent):     Accessibility Tree:                    │    │
│  │  - Mouse click at (x, y)  - Element at (x, y) = AXButton        │    │
│  │  - Key press 'a'          - Element role = AXTextField           │    │
│  │  - Key press 'b'          - Element name = "To recipients"      │    │
│  │  - ...                     - Element value = "current text"       │    │
│  │                                                                   │    │
│  │  Raw events + AX context = Enriched action sequence              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  User:                    "Ok, done"                                    │
│                                                                          │
│  Captain:                  ActionSynthesizer processes:                  │
│                           1. 8 enriched actions                         │
│                           2. Identify parameters (recipient, subject)   │
│                           3. Add preconditions (Gmail must be open)     │
│                           4. Add wait conditions                        │
│                           5. Save as recipe                             │
│                                                                          │
│                           "Arr, I've learned this workflow!             │
│                            Next time just tell me who, what subject,     │
│                            and I'll handle the clicking and typing."      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    SAVED RECIPE                                   │    │
│  │                                                                   │    │
│  │  name: "send-gmail-email"                                        │    │
│  │  params: {recipient, subject, body}                              │    │
│  │  preconditions: {app_running: "Chrome", url_contains: "gmail"}   │    │
│  │  steps: [click Compose, type {recipient}, tab, type {subject},  │    │
│  │          tab, type {body}, hotkey Cmd+Return]                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  LATER:                                                                  │
│                                                                          │
│  User:                    "Captain, send an email to bob@work.com       │
│                            about the Q3 report"                          │
│                                                                          │
│  Captain:                  "Aye! Sending email..."                      │
│                           [executes recipe with params]                  │
│                           "Done! The message is sent, cap'n!"            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Character-Integrated Learning

```swift
// Integration/CharacterRecipeBridge.swift

/// Characters use recipes internally - invisible to users
actor CharacterRecipeBridge {
    private let recipeEngine: RecipeEngine
    private let teamManager: TeamManager
    private let learningSession: LearningSession?
    
    /// User asks character to learn a task
    func startLearning(
        character: TeamProfile,
        taskDescription: String
    ) async throws -> LearningSession {
        let session = LearningSession(
            taskId: UUID(),
            character: character.botName,
            description: taskDescription,
            recorder: ActionRecorder()
        )
        
        // Character acknowledges
        await emitCharacterMessage(
            from: character,
            message: "\(character.botName): I'm watching! Show me how you \(taskDescription)."
        )
        
        return session
    }
    
    /// User finishes demonstrating
    func stopLearning(session: LearningSession) async throws -> Recipe {
        // Get enriched actions
        let enrichedActions = try session.recorder.stop()
        
        // Synthesize into recipe
        let recipe = try await ActionSynthesizer.synthesize(
            actions: enrichedActions,
            description: session.description,
            llmProvider: provider  // Use LLM to identify parameters
        )
        
        // Save to character's learned tasks
        try RecipeStore.save(recipe, for: session.character)
        
        // Character confirms
        await emitCharacterMessage(
            from: session.character,
            message: "\(session.character): Got it! Next time just tell me what you need and I'll do it."
        )
        
        return recipe
    }
    
    /// User asks character to execute a learned task
    func executeLearnedTask(
        character: TeamProfile,
        taskName: String,
        params: [String: String]
    ) async throws -> RecipeRunResult {
        // Load recipe
        guard let recipe = try RecipeStore.load(named: taskName, for: character.botName) else {
            throw RecipeError.notFound(taskName)
        }
        
        // Execute
        let result = try RecipeEngine.run(recipe: recipe, params: params)
        
        // Character narrates progress
        for stepResult in result.stepResults {
            if stepResult.success {
                await emitCharacterMessage(
                    from: character,
                    message: "\(character.botName): \(stepResult.note ?? "Working...")"
                )
            }
        }
        
        return result
    }
}
```

### EverydayAutomationKit vs Ghost OS

| Aspect | Ghost OS | nanofolks EverydayAutomationKit |
|--------|----------|----------------------------------|
| **Target user** | Developers | Non-technical users (moms) |
| **Interface** | CLI commands (ghost_run, ghost_learn) | Natural language via characters |
| **Recipe storage** | `~/.ghost-os/recipes/` | MemoryKit + character-specific |
| **Visibility** | JSON files visible | Invisible to users, managed by characters |
| **Learning trigger** | `ghost_learn_start` | "Watch me do this" conversation |
| **Learning completion** | `ghost_learn_stop` | "Ok, done" natural conversation |
| **Execution trigger** | `ghost_run recipe:"name"` | "Captain, send an email to..." |
| **Error handling** | Technical error messages | Character apologizes and suggests alternatives |
| **Precondition failures** | "Precondition failed: URL should contain..." | "Hmm, I need Gmail to be open first. Should I open it?" |

### Tool Integration with EverydayKit

EverydayAutomationKit complements EverydayKit:

```swift
// EverydayKit provides simple tool calls:
// - CalendarTool: "Schedule a meeting at 3pm"
// - RemindersTool: "Remind me to call mom"

// EverydayAutomationKit extends with learned workflows:
// - "Watch me send an email" → Learn → "Send an email to X about Y"
// - "Watch me book a flight" → Learn → "Book a flight to X on Y date"
```

### Implementation Phases

**Phase 1 (v1.1): Recipe System**
- RecipeTypes, RecipeStore, RecipeEngine
- Basic actions: click, type, press, hotkey
- Recipe loading/saving

**Phase 2 (v1.2): Perception**
- AXTreeReader (AXorcist integration)
- ElementFinder, UIContext
- ElementInspector

**Phase 3 (v1.3): Actions**
- Scroll, Hover, Drag, LongPress
- Focus management
- Wait conditions

**Phase 4 (v1.4): Self-Learning**
- ActionRecorder (CGEvent tap)
- ActionSynthesizer (LLM-assisted)
- Character integration

**Phase 5 (v1.5): Vision Fallback**
- ShowUI-2B local model
- Visual grounding when AX fails
- Screenshot annotation

### Dependencies

```swift
// Package.swift addition
.target(
    name: "EverydayAutomationKit",
    dependencies: [
        "Core",
        "PromptKit",
        "SystemKit",
        .product(name: "AXorcist", package: "AXorcist")  // AX tree
    ]
)
```

### Ghost OS Credit

Ghost OS by ghostwright (https://github.com/ghostwright/ghost-os) demonstrates:
- Accessibility tree first approach (~29 tools)
- Self-learning recipes (CGEvent + AX enrichment)
- MCP protocol integration
- ~7,000 lines of Swift

Licensed MIT. Key concepts adapted for non-technical users.
