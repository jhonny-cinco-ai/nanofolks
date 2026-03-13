// BotProtocol.swift
// Bot interface definitions for the nanofolks ecosystem.

import Foundation

// MARK: - Bot Protocol

/// The main bot protocol that all bots must implement.
/// Uses interface segregation - bots can implement multiple specialized protocols.
public protocol Bot: Sendable {
    /// Unique identifier for this bot instance.
    var id: String { get }
    
    /// Bot's role (leader, coder, researcher, etc.).
    var role: BotRole { get }
    
    /// Bot's configuration loaded from files.
    var config: BotConfig { get }
    
    /// Process a message and optionally respond.
    func process(message: Message, context: BotContext) async throws -> BotResult
}

// MARK: - Specialized Bot Protocols

/// Protocol for bots that can evaluate message urgency.
public protocol BotUrgencyEvaluator: Sendable {
    /// Evaluate how urgent a message is (0.0-1.0).
    func evaluateUrgency(for message: Message, context: BotContext) async -> Double
}

/// Protocol for bots that can respond to messages.
public protocol BotResponder: Sendable {
    /// Generate a response for a message.
    func respond(to message: Message, context: BotContext) async throws -> Response
}

/// Protocol for bots that can use tools.
public protocol BotToolUser: Sendable {
    /// Tools this bot is allowed to use.
    var allowedTools: [String] { get }
    
    /// Tool execution handler.
    var toolExecutor: ToolExecutor? { get }
}

/// Protocol for bots that can coordinate with other bots.
public protocol BotCoordinator: Sendable {
    /// Request coordination with another bot.
    func requestCoordination(
        with botRole: BotRole,
        message: Message,
        context: BotContext
    ) async throws -> CoordinationRequest
    
    /// Process a coordination request from another bot.
    func processCoordinationRequest(
        _ request: CoordinationRequest,
        context: BotContext
    ) async throws -> CoordinationResponse
}

// MARK: - Bot Context

/// Context provided to bots during message processing.
public struct BotContext: Sendable {
    public let roomId: String
    public let conversationHistory: [Message]
    public let availableBots: [BotRole]
    public let currentTeam: TeamProfile
    public let memory: MemoryRetrieval?
    public let metadata: [String: String]
    
    public init(
        roomId: String,
        conversationHistory: [Message] = [],
        availableBots: [BotRole] = [],
        currentTeam: TeamProfile,
        memory: MemoryRetrieval? = nil,
        metadata: [String: String] = [:]
    ) {
        self.roomId = roomId
        self.conversationHistory = conversationHistory
        self.availableBots = availableBots
        self.currentTeam = currentTeam
        self.memory = memory
        self.metadata = metadata
    }
}

/// Memory retrieval interface for bots.
public protocol MemoryRetrieval: Sendable {
    /// Retrieve relevant memories for a query.
    func retrieve(query: String, limit: Int) async throws -> [MemoryEntry]
    
    /// Store a memory entry.
    func store(entry: MemoryEntry) async throws
    
    /// Delete a memory entry.
    func delete(id: String) async throws
}

// MARK: - Bot Result

/// Result of bot processing.
public enum BotResult: Sendable {
    case respond(Response)
    case delegate(toBot: BotRole, reason: String)
    case clarify(question: String, options: [String])
    case noResponse(reason: String)
    case toolCall(ToolCall)
    case multiResponse([Response])
}

// MARK: - Coordination Types

/// Request for coordination between bots.
public struct CoordinationRequest: Sendable, Codable {
    public let id: String
    public let fromBot: BotRole
    public let toBot: BotRole
    public let message: Message
    public let context: [String: String]
    public let priority: Double
    public let requiresResponse: Bool
    
    public init(
        id: String = UUID().uuidString,
        fromBot: BotRole,
        toBot: BotRole,
        message: Message,
        context: [String: String] = [:],
        priority: Double = 0.5,
        requiresResponse: Bool = true
    ) {
        self.id = id
        self.fromBot = fromBot
        self.toBot = toBot
        self.message = message
        self.context = context
        self.priority = priority
        self.requiresResponse = requiresResponse
    }
}

/// Response to a coordination request.
public struct CoordinationResponse: Sendable, Codable {
    public let requestId: String
    public let fromBot: BotRole
    public let response: Response?
    public let status: CoordinationStatus
    public let additionalContext: [String: String]
    
    public init(
        requestId: String,
        fromBot: BotRole,
        response: Response? = nil,
        status: CoordinationStatus,
        additionalContext: [String: String] = [:]
    ) {
        self.requestId = requestId
        self.fromBot = fromBot
        self.response = response
        self.status = status
        self.additionalContext = additionalContext
    }
}

/// Status of a coordination request.
public enum CoordinationStatus: String, Sendable, Codable, CaseIterable {
    case accepted
    case rejected
    case deferred
    case delegated
    case completed
}

// MARK: - Bot Factory Protocol

/// Factory for creating bot instances.
public protocol BotFactory: Sendable {
    /// Create a bot instance for a given role.
    func createBot(role: BotRole, team: TeamProfile) async throws -> any Bot
    
    /// Get all available bot roles.
    func availableRoles() -> [BotRole]
    
    /// Check if a bot role is available for a team.
    func isRoleAvailable(role: BotRole, team: String) -> Bool
}

// MARK: - Bot Loader Protocol

/// Loader for bot configurations from files.
public protocol BotLoader: Sendable {
    /// Load bot configuration from files.
    func loadConfig(role: BotRole) async throws -> BotConfig
    
    /// Load bot soul (personality) from file.
    func loadSoul(role: BotRole, team: String) async throws -> String
    
    /// Load bot role definition from file.
    func loadRoleDefinition(role: BotRole) async throws -> String
    
    /// Load bot reasoning configuration from file.
    func loadReasoning(role: BotRole, team: String) async throws -> ReasoningConfig
}

// MARK: - Tool Executor Protocol

/// Protocol for executing tools.
public protocol ToolExecutor: Sendable {
    /// Execute a tool with given arguments.
    func execute(toolCall: ToolCall) async throws -> ToolResult
    
    /// Check if a tool is available.
    func isToolAvailable(name: String) -> Bool
    
    /// Get tool definition for LLM function calling.
    func getToolDefinition(name: String) -> ToolDefinition?
}