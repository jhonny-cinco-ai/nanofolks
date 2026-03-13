// FleetManager.swift
// Manages independent bot instances and orchestrates multi-bot conversations.

import Core
import BotKit
import ProviderKit
import PromptKit
import Foundation

/// Central manager for all bot instances in a room.
public actor FleetManager {
    private var bots: [BotRole: any Bot] = [:]
    private let botFactory: any BotFactory
    private let provider: any LLMProvider
    private let team: TeamProfile
    private let roomManager: RoomManager
    
    public init(
        botFactory: any BotFactory,
        provider: any LLMProvider,
        team: TeamProfile,
        roomManager: RoomManager
    ) {
        self.botFactory = botFactory
        self.provider = provider
        self.team = team
        self.roomManager = roomManager
    }
    
    // MARK: - Bot Lifecycle
    
    /// Load all bots for the current team.
    public func loadBots() async throws {
        for role in BotRole.allCases {
            let bot = try await botFactory.createBot(role: role, team: team)
            bots[role] = bot
        }
    }
    
    /// Get a bot by role.
    public func getBot(role: BotRole) -> (any Bot)? {
        return bots[role]
    }
    
    /// Get all loaded bots.
    public func getAllBots() -> [any Bot] {
        return Array(bots.values)
    }
    
    /// Unload a specific bot.
    public func unloadBot(role: BotRole) {
        bots.removeValue(forKey: role)
    }
    
    /// Unload all bots.
    public func unloadAllBots() {
        bots.removeAll()
    }
    
    // MARK: - Message Processing
    
    /// Process an incoming message with SmartDispatch.
    public func process(message: Message, in roomId: String) async throws -> [Response] {
        // Load room context
        let room = try await roomManager.getRoom(roomId: roomId)
        let history = try await roomManager.getHistory(roomId: roomId, limit: 50)
        
        // Create bot context
        let context = BotContext(
            roomId: roomId,
            conversationHistory: history,
            availableBots: Array(bots.keys),
            currentTeam: team
        )
        
        // Use SmartDispatch to determine which bots should respond
        let dispatch = SmartDispatch(
            provider: provider,
            bots: bots,
            room: room
        )
        
        let decision = try await dispatch.evaluate(message: message, context: context)
        
        // Process based on decision
        switch decision {
        case .singleBot(let role, _):
            return try await processWithSingleBot(role: role, message: message, context: context)
            
        case .multiBot(let roles):
            return try await processWithMultipleBots(roles: roles, message: message, context: context)
            
        case .allBots:
            return try await processWithAllBots(message: message, context: context)
            
        case .noBot:
            // No bot responded, maybe log this?
            return []
            
        case .urgent(let role):
            // Urgent message - prioritize this bot
            return try await processWithSingleBot(role: role, message: message, context: context)
        }
    }
    
    // MARK: - Private Processing
    
    private func processWithSingleBot(
        role: BotRole,
        message: Message,
        context: BotContext
    ) async throws -> [Response] {
        guard let bot = bots[role] else {
            throw FleetError.botNotLoaded(role)
        }
        
        let result = try await bot.process(message: message, context: context)
        
        switch result {
        case .respond(let response):
            return [response]
            
        case .delegate(let targetRole, _):
            // Delegate to another bot
            return try await processWithSingleBot(role: targetRole, message: message, context: context)
            
        case .clarify(let question, let options):
            // Bot needs clarification
            return [Response(
                botName: bot.config.displayName,
                content: "\(question) (\(options.joined(separator: ", ")))"
            )]
            
        case .noResponse:
            return []
            
        case .toolCall:
            return [Response(
                botName: bot.config.displayName,
                content: "I identified a tool action, but tool execution is not wired in this runtime yet."
            )]
            
        case .multiResponse(let responses):
            return responses
        }
    }
    
    private func processWithMultipleBots(
        roles: [BotRole],
        message: Message,
        context: BotContext
    ) async throws -> [Response] {
        // Process with all selected bots concurrently
        let responses = try await withThrowingTaskGroup(of: [Response].self) { group in
            for role in roles {
                group.addTask {
                    return try await self.processWithSingleBot(role: role, message: message, context: context)
                }
            }
            
            var allResponses: [Response] = []
            for try await responses in group {
                allResponses.append(contentsOf: responses)
            }
            return allResponses
        }
        
        // Combine responses using ResponseCombiner
        let combiner = ResponseCombiner()
        return await combiner.combine(responses: responses, for: message)
    }
    
    private func processWithAllBots(
        message: Message,
        context: BotContext
    ) async throws -> [Response] {
        return try await processWithMultipleBots(
            roles: Array(bots.keys),
            message: message,
            context: context
        )
    }
}

// MARK: - Fleet Error

public enum FleetError: Error, Sendable {
    case botNotLoaded(BotRole)
    case noBotsAvailable
    case dispatchFailed(String)
}
