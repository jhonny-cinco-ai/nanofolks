// LLMProviderProtocol.swift
// LLM provider interface for the nanofolks ecosystem.

import Foundation

// MARK: - LLM Provider Protocol

/// Protocol for LLM providers.
/// Implementations: OpenAIProvider, AnthropicProvider, LocalProvider, etc.
public protocol LLMProvider: Sendable {
    /// Provider name for identification.
    var name: String { get }
    
    /// Available models from this provider.
    var models: [String] { get }
    
    /// Send a chat completion request.
    func chat(request: LLMRequest) async throws -> LLMResponse
    
    /// Send a streaming chat completion request.
    func chatStream(request: LLMRequest) -> AsyncThrowingStream<LLMStreamChunk, Error>
    
    /// Generate embeddings for text.
    func embed(text: [String]) async throws -> [[Float]]
    
    /// Check if provider is available.
    func isAvailable() async -> Bool
    
    /// Get estimated token count for messages.
    func estimateTokens(for messages: [Message]) -> Int
}

// MARK: - LLM Stream Types

/// Streaming response chunk.
public struct LLMStreamChunk: Sendable, Codable {
    public let id: String
    public let delta: String
    public let isComplete: Bool
    public let toolCalls: [ToolCall]?
    
    public init(
        id: String = UUID().uuidString,
        delta: String,
        isComplete: Bool = false,
        toolCalls: [ToolCall]? = nil
    ) {
        self.id = id
        self.delta = delta
        self.isComplete = isComplete
        self.toolCalls = toolCalls
    }
}

// MARK: - Provider Factory Protocol

/// Factory for creating LLM provider instances.
public protocol ProviderFactory: Sendable {
    /// Create a provider instance.
    func createProvider(config: ProviderConfig) async throws -> any LLMProvider
    
    /// Get available provider names.
    func availableProviders() -> [String]
    
    /// Check if a provider is configured.
    func isProviderConfigured(name: String) -> Bool
}

// MARK: - Provider Registry Protocol

/// Registry for managing multiple providers.
public protocol ProviderRegistry: Sendable {
    /// Register a provider.
    func register(provider: any LLMProvider, for name: String)
    
    /// Get a provider by name.
    func getProvider(name: String) -> (any LLMProvider)?
    
    /// Get the default provider.
    func getDefaultProvider() -> (any LLMProvider)?
    
    /// Set the default provider.
    func setDefaultProvider(name: String) throws
    
    /// Route a request to the appropriate provider.
    func route(request: LLMRequest, preferredModel: String?) async throws -> LLMResponse
    
    /// Get all registered provider names.
    func getRegisteredProviders() -> [String]
}

// MARK: - Tiered Model Strategy

/// Tiered model strategy for local-first with cloud fallback.
public protocol TieredModelStrategy: Sendable {
    /// Determine which tier to use for a request.
    func determineTier(for request: LLMRequest) -> ModelTier
    
    /// Check if local model is available.
    func isLocalAvailable() async -> Bool
    
    /// Check if cloud model is available.
    func isCloudAvailable() async -> Bool
    
    /// Get cost estimate for cloud request.
    func estimateCost(for request: LLMRequest) -> TokenCost?
}

/// Model tier for tiered strategy.
public enum ModelTier: String, Sendable, Codable, CaseIterable {
    case local      // Fast, free, limited capability
    case cloud      // Powerful, costs money, full capability
    case auto       // Let strategy decide
}

/// Token cost information.
public struct TokenCost: Sendable, Codable {
    public let inputTokens: Int
    public let outputTokens: Int
    public let estimatedCost: Double   // Cost in dollars
    public let model: String
    
    public init(inputTokens: Int, outputTokens: Int, estimatedCost: Double, model: String) {
        self.inputTokens = inputTokens
        self.outputTokens = outputTokens
        self.estimatedCost = estimatedCost
        self.model = model
    }
}

// MARK: - Model Usage Tracking

/// Protocol for tracking model usage.
public protocol ModelUsageTracker: Sendable {
    /// Record usage for billing/transparency.
    func recordUsage(
        provider: String,
        model: String,
        inputTokens: Int,
        outputTokens: Int
    ) async throws
    
    /// Get usage for current period.
    func getUsage(period: UsagePeriod) async throws -> UsageSummary
    
    /// Check if user is within their budget.
    func isWithinBudget() async -> Bool
    
    /// Get remaining budget.
    func getRemainingBudget() async -> TokenBudget?
}

/// Usage period for tracking.
public enum UsagePeriod: String, Sendable, Codable, CaseIterable {
    case today
    case thisWeek
    case thisMonth
    case allTime
}

/// Usage summary for a period.
public struct UsageSummary: Sendable, Codable {
    public let period: UsagePeriod
    public let totalRequests: Int
    public let totalInputTokens: Int
    public let totalOutputTokens: Int
    public let totalCost: Double
    public let byModel: [String: ModelUsage]
    
    public init(
        period: UsagePeriod,
        totalRequests: Int,
        totalInputTokens: Int,
        totalOutputTokens: Int,
        totalCost: Double,
        byModel: [String: ModelUsage] = [:]
    ) {
        self.period = period
        self.totalRequests = totalRequests
        self.totalInputTokens = totalInputTokens
        self.totalOutputTokens = totalOutputTokens
        self.totalCost = totalCost
        self.byModel = byModel
    }
}

/// Usage by model.
public struct ModelUsage: Sendable, Codable {
    public let model: String
    public let requests: Int
    public let inputTokens: Int
    public let outputTokens: Int
    public let cost: Double
    
    public init(model: String, requests: Int, inputTokens: Int, outputTokens: Int, cost: Double) {
        self.model = model
        self.requests = requests
        self.inputTokens = inputTokens
        self.outputTokens = outputTokens
        self.cost = cost
    }
}

/// Token budget information.
public struct TokenBudget: Sendable, Codable {
    public let totalBudget: Int
    public let usedBudget: Int
    public let remainingBudget: Int
    public let resetDate: Date?
    
    public init(
        totalBudget: Int,
        usedBudget: Int,
        remainingBudget: Int,
        resetDate: Date? = nil
    ) {
        self.totalBudget = totalBudget
        self.usedBudget = usedBudget
        self.remainingBudget = remainingBudget
        self.resetDate = resetDate
    }
}