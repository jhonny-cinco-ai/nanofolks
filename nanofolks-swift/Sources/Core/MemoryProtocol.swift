// MemoryProtocol.swift
// Memory storage interface for the nanofolks ecosystem.

import Foundation

// MARK: - Memory Store Protocol

/// Protocol for memory storage implementations.
/// Implementations: SQLiteMemoryStore, InMemoryMemoryStore, FileSystemMemoryStore
public protocol MemoryStore: Sendable {
    /// Store a memory entry.
    func store(entry: MemoryEntry) async throws
    
    /// Retrieve memory entries by ID.
    func retrieve(ids: [String]) async throws -> [MemoryEntry]
    
    /// Search for memories by content similarity.
    func search(query: String, limit: Int) async throws -> [MemoryEntry]
    
    /// Search for memories by embedding similarity.
    func searchByEmbedding(embedding: [Float], limit: Int) async throws -> [MemoryEntry]
    
    /// Delete memory entries by ID.
    func delete(ids: [String]) async throws
    
    /// Delete all memories for a room.
    func deleteRoom(roomId: String) async throws
    
    /// Get all memories for a bot.
    func getMemoriesForBot(botName: String, limit: Int) async throws -> [MemoryEntry]
    
    /// Get memory statistics.
    func getStats() async throws -> MemoryStats
}

// MARK: - Embedding Service Protocol

/// Protocol for generating embeddings.
public protocol EmbeddingService: Sendable {
    /// Generate embedding for text.
    func embed(text: String) async throws -> [Float]
    
    /// Generate embeddings for multiple texts.
    func embedBatch(texts: [String]) async throws -> [[Float]]
    
    /// Get the dimensionality of embeddings.
    func getDimension() -> Int
    
    /// Get the model name used for embeddings.
    func getModelName() -> String
}

// MARK: - Memory Manager Protocol

/// Higher-level memory management.
public protocol MemoryManager: Sendable {
    /// Store a conversation turn.
    func storeConversation(
        message: Message,
        response: Response,
        roomId: String,
        botName: String
    ) async throws
    
    /// Store a learned fact about the user.
    func storeFact(
        fact: String,
        category: FactCategory,
        confidence: Double
    ) async throws
    
    /// Store a user preference.
    func storePreference(
        key: String,
        value: String,
        context: String?
    ) async throws
    
    /// Retrieve relevant context for a message.
    func getRelevantContext(
        for message: Message,
        roomId: String,
        botName: String
    ) async throws -> MemoryContext
    
    /// Forget memories matching criteria.
    func forget(criteria: ForgetCriteria) async throws
    
    /// Summarize old conversations.
    func summarize(roomId: String, olderThan days: Int) async throws
    
    /// Export all memories.
    func export() async throws -> MemoryExport
    
    /// Import memories.
    func importFrom(export: MemoryExport) async throws
}

// MARK: - Memory Types

/// Statistics about stored memories.
public struct MemoryStats: Sendable, Codable {
    public let totalEntries: Int
    public let totalTokens: Int
    public let entriesByType: [MemoryType: Int]
    public let entriesByBot: [String: Int]
    public let oldestEntry: Date?
    public let newestEntry: Date?
    public let storageSize: Int64
    
    public init(
        totalEntries: Int,
        totalTokens: Int,
        entriesByType: [MemoryType: Int] = [:],
        entriesByBot: [String: Int] = [:],
        oldestEntry: Date? = nil,
        newestEntry: Date? = nil,
        storageSize: Int64 = 0
    ) {
        self.totalEntries = totalEntries
        self.totalTokens = totalTokens
        self.entriesByType = entriesByType
        self.entriesByBot = entriesByBot
        self.oldestEntry = oldestEntry
        self.newestEntry = newestEntry
        self.storageSize = storageSize
    }
}

/// Category for learned facts.
public enum FactCategory: String, Sendable, Codable, CaseIterable {
    case personalInfo      // "User's name is John"
    case preference        // "User prefers concise responses"
    case relationship      // "User's spouse is Jane"
    case habit            // "User checks email every morning"
    case goal             // "User wants to learn Swift"
    case constraint       // "User doesn't want to use cloud services"
    case context          // "User works in marketing"
    case other
}

/// Criteria for forgetting memories.
public struct ForgetCriteria: Sendable, Codable {
    public let ids: [String]?
    public let olderThan: Date?
    public let types: [MemoryType]?
    public let botName: String?
    public let roomId: String?
    public let tags: [String]?
    
    public init(
        ids: [String]? = nil,
        olderThan: Date? = nil,
        types: [MemoryType]? = nil,
        botName: String? = nil,
        roomId: String? = nil,
        tags: [String]? = nil
    ) {
        self.ids = ids
        self.olderThan = olderThan
        self.types = types
        self.botName = botName
        self.roomId = roomId
        self.tags = tags
    }
}

/// Context retrieved from memory.
public struct MemoryContext: Sendable {
    public let recentMessages: [Message]
    public let relevantFacts: [MemoryEntry]
    public let relevantPreferences: [MemoryEntry]
    public let summaries: [String]
    public let totalTokens: Int
    
    public init(
        recentMessages: [Message] = [],
        relevantFacts: [MemoryEntry] = [],
        relevantPreferences: [MemoryEntry] = [],
        summaries: [String] = [],
        totalTokens: Int = 0
    ) {
        self.recentMessages = recentMessages
        self.relevantFacts = relevantFacts
        self.relevantPreferences = relevantPreferences
        self.summaries = summaries
        self.totalTokens = totalTokens
    }
}

/// Export format for memories.
public struct MemoryExport: Sendable, Codable {
    public let version: String
    public let exportDate: Date
    public let entries: [MemoryEntry]
    public let metadata: ExportMetadata
    
    public init(
        version: String = "1.0",
        exportDate: Date = Date(),
        entries: [MemoryEntry],
        metadata: ExportMetadata
    ) {
        self.version = version
        self.exportDate = exportDate
        self.entries = entries
        self.metadata = metadata
    }
}

/// Metadata for memory export.
public struct ExportMetadata: Sendable, Codable {
    public let teamName: String
    public let botNames: [String]
    public let totalEntries: Int
    public let dateRange: DateRange?
    
    public init(
        teamName: String,
        botNames: [String],
        totalEntries: Int,
        dateRange: DateRange? = nil
    ) {
        self.teamName = teamName
        self.botNames = botNames
        self.totalEntries = totalEntries
        self.dateRange = dateRange
    }
}

/// Date range for exports.
public struct DateRange: Sendable, Codable {
    public let start: Date
    public let end: Date
    
    public init(start: Date, end: Date) {
        self.start = start
        self.end = end
    }
}

// MARK: - Learning Protocol

/// Protocol for user-facing learning notifications.
public protocol LearningNotification: Sendable {
    /// Notify user that something was learned.
    func notifyLearning(
        fact: String,
        category: FactCategory,
        confidence: Double
    ) async throws -> LearningNotificationResult
    
    /// Ask user to confirm a learned fact.
    func confirmLearning(
        fact: String,
        category: FactCategory
    ) async throws -> LearningConfirmationResult
    
    /// Forget a learned fact.
    func forgetFact(factId: String) async throws
}

/// Result of learning notification.
public enum LearningNotificationResult: Sendable {
    case acknowledged
    case dismissed
    case confirmed
    case corrected(correction: String)
}

/// Result of learning confirmation.
public enum LearningConfirmationResult: Sendable {
    case confirmed
    case rejected
    case corrected(correction: String)
}