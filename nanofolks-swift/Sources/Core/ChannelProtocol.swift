// ChannelProtocol.swift
// Communication channel interface for the nanofolks ecosystem.

import Foundation

// MARK: - Channel Handler Protocol

/// Protocol for handling messages from different communication channels.
public protocol ChannelHandler: Sendable {
    /// Channel type this handler supports.
    var channel: Channel { get }
    
    /// Initialize the channel.
    func initialize() async throws
    
    /// Shut down the channel.
    func shutdown() async throws
    
    /// Send a message through this channel.
    func send(
        message: Response,
        roomId: String,
        metadata: [String: String]
    ) async throws
    
    /// Send a typing indicator.
    func sendTypingIndicator(roomId: String) async throws
    
    /// Subscribe to incoming messages.
    func subscribe(
        handler: @escaping (MessageEnvelope) async throws -> Void
    ) async throws
    
    /// Check if channel is connected.
    func isConnected() -> Bool
    
    /// Get channel-specific user info.
    func getUserInfo(userId: String) async throws -> ChannelUserInfo?
}

// MARK: - Channel Manager Protocol

/// Manager for multiple communication channels.
public protocol ChannelManager: Sendable {
    /// Register a channel handler.
    func register(handler: any ChannelHandler) throws
    
    /// Unregister a channel handler.
    func unregister(channel: Channel) throws
    
    /// Get handler for a channel.
    func getHandler(channel: Channel) -> (any ChannelHandler)?
    
    /// Initialize all registered channels.
    func initializeAll() async throws
    
    /// Shutdown all channels.
    func shutdownAll() async throws
    
    /// Broadcast message to all channels.
    func broadcast(
        message: Response,
        excludeChannels: [Channel]
    ) async throws
    
    /// Get all registered channels.
    func getRegisteredChannels() -> [Channel]
}

// MARK: - Channel User Info

/// User information from a channel.
public struct ChannelUserInfo: Sendable, Codable {
    public let userId: String
    public let displayName: String?
    public let username: String?
    public let avatarUrl: String?
    public let metadata: [String: String]
    
    public init(
        userId: String,
        displayName: String? = nil,
        username: String? = nil,
        avatarUrl: String? = nil,
        metadata: [String: String] = [:]
    ) {
        self.userId = userId
        self.displayName = displayName
        self.username = username
        self.avatarUrl = avatarUrl
        self.metadata = metadata
    }
}

// MARK: - Message Router Protocol

/// Protocol for routing messages to appropriate bots.
public protocol MessageRouter: Sendable {
    /// Route a message to the appropriate bot(s).
    func route(message: MessageEnvelope) async throws -> RoutingDecision
    
    /// Set the routing handler for processed messages.
    func setRoutingHandler(
        handler: @escaping (MessageEnvelope, RoutingDecision) async throws -> Void
    )
}

// MARK: - Routing Decision

/// Decision made by the message router.
public enum RoutingDecision: Sendable {
    case singleBot(BotRole, confidence: Double)
    case multiBot([BotRole])
    case allBots
    case noBot(reason: String)
    case urgent(BotRole)
    
    /// Get the primary bot role, if any.
    public var primaryBot: BotRole? {
        switch self {
        case .singleBot(let role, _):
            return role
        case .multiBot(let roles):
            return roles.first
        case .allBots:
            return .leader
        case .noBot:
            return nil
        case .urgent(let role):
            return role
        }
    }
    
    /// Get all bot roles involved.
    public var allBots: [BotRole] {
        switch self {
        case .singleBot(let role, _):
            return [role]
        case .multiBot(let roles):
            return roles
        case .allBots:
            return BotRole.allCases
        case .noBot:
            return []
        case .urgent(let role):
            return [role]
        }
    }
}

// MARK: - Message Priority

/// Priority for message processing.
public enum MessagePriority: Int, Sendable, Codable, CaseIterable, Comparable {
    case low = 0
    case normal = 1
    case high = 2
    case urgent = 3
    
    public static func < (lhs: MessagePriority, rhs: MessagePriority) -> Bool {
        return lhs.rawValue < rhs.rawValue
    }
}

// MARK: - Channel Events

/// Events that can occur on channels.
public enum ChannelEvent: Sendable {
    case messageReceived(MessageEnvelope)
    case messageSent(MessageEnvelope)
    case userJoined(channel: Channel, roomId: String, userId: String)
    case userLeft(channel: Channel, roomId: String, userId: String)
    case typingStarted(channel: Channel, roomId: String, userId: String)
    case typingStopped(channel: Channel, roomId: String, userId: String)
    case error(channel: Channel, error: Error)
    case connected(channel: Channel)
    case disconnected(channel: Channel)
}

/// Protocol for subscribing to channel events.
public protocol ChannelEventSubscriber: Sendable {
    /// Handle a channel event.
    func handle(event: ChannelEvent) async
}

// MARK: - Room Manager Protocol

/// Protocol for managing conversation rooms.
public protocol RoomManager: Sendable {
    /// Create a new room.
    func createRoom(
        name: String,
        context: String?,
        channel: Channel
    ) async throws -> Room
    
    /// Get a room by ID.
    func getRoom(roomId: String) async throws -> Room?
    
    /// Get all rooms.
    func getAllRooms() async throws -> [Room]
    
    /// Update room context.
    func updateRoomContext(roomId: String, context: String) async throws
    
    /// Archive a room.
    func archiveRoom(roomId: String) async throws
    
    /// Get message history for a room.
    func getHistory(
        roomId: String,
        limit: Int
    ) async throws -> [Message]
    
    /// Add message to history.
    func addMessage(
        roomId: String,
        message: Message
    ) async throws
}