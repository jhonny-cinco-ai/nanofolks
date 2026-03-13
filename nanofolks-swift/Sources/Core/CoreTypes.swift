// CoreTypes.swift
// Foundation types for the nanofolks ecosystem.
// No dependencies - this is the "Lego block base" that everything builds on.

import Foundation

// MARK: - Message Types

/// A message in a conversation.
public struct Message: Sendable, Codable {
    public let id: UUID
    public let role: MessageRole
    public let content: String
    public let timestamp: Date
    public let metadata: MessageMetadata?
    
    public init(
        id: UUID = UUID(),
        role: MessageRole,
        content: String,
        timestamp: Date = Date(),
        metadata: MessageMetadata? = nil
    ) {
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.metadata = metadata
    }
}

/// The role of a message in a conversation.
public enum MessageRole: String, Sendable, Codable, CaseIterable {
    case system
    case user
    case assistant
    case tool
}

/// Additional metadata for a message.
public struct MessageMetadata: Sendable, Codable {
    public let botName: String?
    public let channelId: String?
    public let roomId: String?
    public let context: [String: String]?
    
    public init(
        botName: String? = nil,
        channelId: String? = nil,
        roomId: String? = nil,
        context: [String: String]? = nil
    ) {
        self.botName = botName
        self.channelId = channelId
        self.roomId = roomId
        self.context = context
    }
}

// MARK: - Response Types

/// A response from a bot or LLM.
public struct Response: Sendable, Codable {
    public let id: UUID
    public let botName: String
    public let content: String
    public let timestamp: Date
    public let metadata: ResponseMetadata?
    
    public init(
        id: UUID = UUID(),
        botName: String,
        content: String,
        timestamp: Date = Date(),
        metadata: ResponseMetadata? = nil
    ) {
        self.id = id
        self.botName = botName
        self.content = content
        self.timestamp = timestamp
        self.metadata = metadata
    }
}

/// Additional metadata for a response.
public struct ResponseMetadata: Sendable, Codable {
    public let modelUsed: String?
    public let tokensUsed: Int?
    public let toolsInvoked: [String]?
    public let confidence: Double?
    
    public init(
        modelUsed: String? = nil,
        tokensUsed: Int? = nil,
        toolsInvoked: [String]? = nil,
        confidence: Double? = nil
    ) {
        self.modelUsed = modelUsed
        self.tokensUsed = tokensUsed
        self.toolsInvoked = toolsInvoked
        self.confidence = confidence
    }
}

// MARK: - Bot Types

/// Bot role within a team.
public enum BotRole: String, Sendable, Codable, CaseIterable {
    case leader
    case coder
    case researcher
    case social
    case creative
    case auditor
}

/// Bot configuration loaded from files.
public struct BotConfig: Sendable, Codable {
    public let name: String
    public let displayName: String
    public let icon: String
    public let description: String
    public let version: String
    public let enabled: Bool
    public let capabilities: BotCapabilities
    public let behavior: BotBehavior
    public let tools: [String]
    
    public init(
        name: String,
        displayName: String,
        icon: String,
        description: String,
        version: String = "1.0.0",
        enabled: Bool = true,
        capabilities: BotCapabilities = BotCapabilities(),
        behavior: BotBehavior = BotBehavior(),
        tools: [String] = []
    ) {
        self.name = name
        self.displayName = displayName
        self.icon = icon
        self.description = description
        self.version = version
        self.enabled = enabled
        self.capabilities = capabilities
        self.behavior = behavior
        self.tools = tools
    }
}

/// Bot capabilities definition.
public struct BotCapabilities: Sendable, Codable {
    public let canAudit: Bool
    public let canCode: Bool
    public let canDesign: Bool
    public let canInvokeOthers: Bool
    public let maxConcurrentTasks: Int
    
    public init(
        canAudit: Bool = false,
        canCode: Bool = false,
        canDesign: Bool = false,
        canInvokeOthers: Bool = false,
        maxConcurrentTasks: Int = 1
    ) {
        self.canAudit = canAudit
        self.canCode = canCode
        self.canDesign = canDesign
        self.canInvokeOthers = canInvokeOthers
        self.maxConcurrentTasks = maxConcurrentTasks
    }
}

/// Bot behavior configuration.
public struct BotBehavior: Sendable, Codable {
    public let responseStyle: String
    public let speakThreshold: Double
    public let maxResponseLength: Int
    public let useMicroTurns: Bool
    
    public init(
        responseStyle: String = "thoughtful",
        speakThreshold: Double = 0.5,
        maxResponseLength: Int = 400,
        useMicroTurns: Bool = true
    ) {
        self.responseStyle = responseStyle
        self.speakThreshold = speakThreshold
        self.maxResponseLength = maxResponseLength
        self.useMicroTurns = useMicroTurns
    }
}

// MARK: - Team Types

/// Team profile with personality theme.
public struct TeamProfile: Sendable, Codable {
    public let name: String
    public let displayName: String
    public let description: String
    public let theme: String
    public let emoji: String
    public let botProfiles: [String: BotTeamProfile]
    
    public init(
        name: String,
        displayName: String,
        description: String,
        theme: String,
        emoji: String,
        botProfiles: [String: BotTeamProfile] = [:]
    ) {
        self.name = name
        self.displayName = displayName
        self.description = description
        self.theme = theme
        self.emoji = emoji
        self.botProfiles = botProfiles
    }
}

/// Bot profile within a specific team.
public struct BotTeamProfile: Sendable, Codable {
    public let botRole: String
    public let teamName: String
    public let botName: String
    public let botTitle: String
    public let emoji: String
    public let personality: String
    public let greeting: String
    public let voice: String
    public let roleCard: String
    public let reasoning: ReasoningConfig
    public let permissions: [String]
    public let sources: [String: String]
    
    public init(
        botRole: String,
        teamName: String,
        botName: String,
        botTitle: String,
        emoji: String,
        personality: String,
        greeting: String,
        voice: String,
        roleCard: String,
        reasoning: ReasoningConfig,
        permissions: [String],
        sources: [String: String] = [:]
    ) {
        self.botRole = botRole
        self.teamName = teamName
        self.botName = botName
        self.botTitle = botTitle
        self.emoji = emoji
        self.personality = personality
        self.greeting = greeting
        self.voice = voice
        self.roleCard = roleCard
        self.reasoning = reasoning
        self.permissions = permissions
        self.sources = sources
    }
}

/// Reasoning configuration for a bot.
public struct ReasoningConfig: Sendable, Codable {
    public let mode: String
    public let stepByStep: Bool
    public let considersRisks: Bool
    public let providesMitigations: Bool
    public let confidenceThreshold: Double
    
    public init(
        mode: String = "thoughtful",
        stepByStep: Bool = true,
        considersRisks: Bool = false,
        providesMitigations: Bool = false,
        confidenceThreshold: Double = 0.8
    ) {
        self.mode = mode
        self.stepByStep = stepByStep
        self.considersRisks = considersRisks
        self.providesMitigations = providesMitigations
        self.confidenceThreshold = confidenceThreshold
    }
}

// MARK: - Room Types

/// A conversation room with context.
public struct Room: Sendable, Codable {
    public let id: String
    public let name: String
    public let context: String?
    public let participants: [String]
    public let createdAt: Date
    public let updatedAt: Date
    
    public init(
        id: String = UUID().uuidString,
        name: String,
        context: String? = nil,
        participants: [String] = [],
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.context = context
        self.participants = participants
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

// MARK: - Tool Types

/// Tool execution result.
public struct ToolResult: Sendable, Codable {
    public let toolName: String
    public let success: Bool
    public let output: String
    public let error: String?
    public let metadata: [String: String]?
    
    public init(
        toolName: String,
        success: Bool,
        output: String,
        error: String? = nil,
        metadata: [String: String]? = nil
    ) {
        self.toolName = toolName
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata
    }
}

/// Tool call request.
public struct ToolCall: Sendable, Codable {
    public let id: String
    public let name: String
    public let arguments: [String: AnyCodable]
    
    public init(
        id: String = UUID().uuidString,
        name: String,
        arguments: [String: AnyCodable] = [:]
    ) {
        self.id = id
        self.name = name
        self.arguments = arguments
    }
}

/// Generic Codable wrapper for Any values.
public struct AnyCodable: Sendable, Codable {
    public let value: Any
    
    public init(_ value: Any) {
        self.value = value
    }
    
    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let string = try? container.decode(String.self) {
            value = string
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            value = ""
        }
    }
    
    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        switch value {
        case let string as String:
            try container.encode(string)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let bool as Bool:
            try container.encode(bool)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dict as [String: Any]:
            try container.encode(dict.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}

// MARK: - LLM Types

/// LLM request configuration.
public struct LLMRequest: Sendable {
    public let messages: [Message]
    public let model: String?
    public let temperature: Double?
    public let maxTokens: Int?
    public let tools: [ToolDefinition]?
    
    public init(
        messages: [Message],
        model: String? = nil,
        temperature: Double? = nil,
        maxTokens: Int? = nil,
        tools: [ToolDefinition]? = nil
    ) {
        self.messages = messages
        self.model = model
        self.temperature = temperature
        self.maxTokens = maxTokens
        self.tools = tools
    }
}

/// LLM response.
public struct LLMResponse: Sendable, Codable {
    public let id: String
    public let content: String
    public let model: String
    public let usage: TokenUsage?
    public let toolCalls: [ToolCall]?
    public let finishReason: String?
    
    public init(
        id: String = UUID().uuidString,
        content: String,
        model: String,
        usage: TokenUsage? = nil,
        toolCalls: [ToolCall]? = nil,
        finishReason: String? = nil
    ) {
        self.id = id
        self.content = content
        self.model = model
        self.usage = usage
        self.toolCalls = toolCalls
        self.finishReason = finishReason
    }
}

/// Token usage information.
public struct TokenUsage: Sendable, Codable {
    public let promptTokens: Int
    public let completionTokens: Int
    public let totalTokens: Int
    
    public init(promptTokens: Int, completionTokens: Int, totalTokens: Int) {
        self.promptTokens = promptTokens
        self.completionTokens = completionTokens
        self.totalTokens = totalTokens
    }
}

/// Tool definition for LLM function calling.
public struct ToolDefinition: Sendable, Codable {
    public let name: String
    public let description: String
    public let parameters: [String: ParameterSchema]
    
    public init(name: String, description: String, parameters: [String: ParameterSchema] = [:]) {
        self.name = name
        self.description = description
        self.parameters = parameters
    }
}

/// Parameter schema for tool definitions.
public struct ParameterSchema: Sendable, Codable {
    public let type: String
    public let description: String?
    public let enumValues: [String]?
    public let required: Bool
    
    public init(
        type: String,
        description: String? = nil,
        enumValues: [String]? = nil,
        required: Bool = true
    ) {
        self.type = type
        self.description = description
        self.enumValues = enumValues
        self.required = required
    }
    
    enum CodingKeys: String, CodingKey {
        case type, description
        case enumValues = "enum"
        case required
    }
}

// MARK: - Memory Types

/// Memory entry for storage.
public struct MemoryEntry: Sendable, Codable {
    public let id: String
    public let content: String
    public let embedding: [Float]?
    public let metadata: MemoryMetadata
    public let createdAt: Date
    public let updatedAt: Date
    
    public init(
        id: String = UUID().uuidString,
        content: String,
        embedding: [Float]? = nil,
        metadata: MemoryMetadata,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.content = content
        self.embedding = embedding
        self.metadata = metadata
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

/// Metadata for a memory entry.
public struct MemoryMetadata: Sendable, Codable {
    public let type: MemoryType
    public let botName: String?
    public let roomId: String?
    public let importance: Double
    public let tags: [String]
    
    public init(
        type: MemoryType,
        botName: String? = nil,
        roomId: String? = nil,
        importance: Double = 0.5,
        tags: [String] = []
    ) {
        self.type = type
        self.botName = botName
        self.roomId = roomId
        self.importance = importance
        self.tags = tags
    }
}

/// Type of memory entry.
public enum MemoryType: String, Sendable, Codable, CaseIterable {
    case conversation
    case fact
    case preference
    case decision
    case outcome
    case feedback
}

// MARK: - Channel Types

/// Communication channel identifier.
public enum Channel: String, Sendable, Codable, CaseIterable {
    case cli
    case slack
    case discord
    case whatsapp
    case imessage
    case api
}

/// Message envelope for routing.
public struct MessageEnvelope: Sendable, Codable {
    public let id: String
    public let channel: Channel
    public let roomId: String
    public let senderId: String
    public let message: Message
    public let metadata: [String: String]
    
    public init(
        id: String = UUID().uuidString,
        channel: Channel,
        roomId: String,
        senderId: String,
        message: Message,
        metadata: [String: String] = [:]
    ) {
        self.id = id
        self.channel = channel
        self.roomId = roomId
        self.senderId = senderId
        self.message = message
        self.metadata = metadata
    }
}

// MARK: - Error Types

/// Core error types.
public enum CoreError: Error, Sendable {
    case botNotFound(String)
    case teamNotFound(String)
    case toolNotFound(String)
    case channelNotSupported(String)
    case memoryError(String)
    case providerError(String)
    case configurationError(String)
    case fileNotFound(String)
    case parsingError(String)
    case invalidResponse(String)
    case rateLimited(retryAfter: TimeInterval)
    case unauthorized
    case timeout
}

// MARK: - Configuration Types

/// Provider configuration.
public struct ProviderConfig: Sendable, Codable {
    public let name: String
    public let model: String
    public let apiKey: String?
    public let baseUrl: String?
    public let temperature: Double
    public let maxTokens: Int
    
    public init(
        name: String,
        model: String,
        apiKey: String? = nil,
        baseUrl: String? = nil,
        temperature: Double = 0.7,
        maxTokens: Int = 2000
    ) {
        self.name = name
        self.model = model
        self.apiKey = apiKey
        self.baseUrl = baseUrl
        self.temperature = temperature
        self.maxTokens = maxTokens
    }
}

/// Memory configuration.
public struct MemoryConfig: Sendable, Codable {
    public let storageType: StorageType
    public let embeddingModel: String
    public let maxEntries: Int
    public let retentionDays: Int
    
    public init(
        storageType: StorageType = .sqlite,
        embeddingModel: String = "local",
        maxEntries: Int = 10000,
        retentionDays: Int = 90
    ) {
        self.storageType = storageType
        self.embeddingModel = embeddingModel
        self.maxEntries = maxEntries
        self.retentionDays = retentionDays
    }
}

/// Storage type for memory.
public enum StorageType: String, Sendable, Codable, CaseIterable {
    case sqlite
    case inMemory
    case fileSystem
}

/// App-level configuration.
public struct AppConfig: Sendable, Codable {
    public let team: String
    public let providers: [ProviderConfig]
    public let memory: MemoryConfig
    public let workspacePath: String
    
    public init(
        team: String = "pirate_crew",
        providers: [ProviderConfig] = [],
        memory: MemoryConfig = MemoryConfig(),
        workspacePath: String = "~/.nanofolks/workspace"
    ) {
        self.team = team
        self.providers = providers
        self.memory = memory
        self.workspacePath = workspacePath
    }
}