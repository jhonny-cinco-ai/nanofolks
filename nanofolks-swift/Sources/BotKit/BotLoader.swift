// BotLoader.swift
// Loads bot configurations from file-based system.
// Reads from Teams/{team}/ folder structure.

import Core
import Foundation

/// Loads bot configurations from markdown and JSON files.
public actor BotLoader {
    private let teamsDirectory: URL
    private let rolesDirectory: URL
    private let workspaceDirectory: URL
    
    public init(
        teamsDirectory: URL,
        rolesDirectory: URL,
        workspaceDirectory: URL
    ) {
        self.teamsDirectory = teamsDirectory
        self.rolesDirectory = rolesDirectory
        self.workspaceDirectory = workspaceDirectory
    }
    
    // MARK: - Loading
    
    /// Load complete bot configuration for a role in a team.
    public func loadBotConfig(
        role: BotRole,
        team: String
    ) async throws -> CompleteBotConfig {
        let botName = role.rawValue
        
        // Layer 1: Team context (optional)
        _ = try? await loadTeamContext(team)
        
        // Layer 2: Bot soul and identity (team-specific)
        let soul = try await loadBotSoul(team: team, bot: botName)
        let identity = try await loadBotIdentity(team: team, bot: botName)
        
        // Layer 3: Role capabilities (shared across teams)
        let roleCard = try await loadBotRole(bot: botName)
        
        // Behavior config
        let reasoning = try await loadBotReasoning(team: team, bot: botName)
        
        return CompleteBotConfig(
            role: role,
            team: team,
            botName: identity.name,
            displayName: identity.name,
            icon: identity.emoji,
            description: identity.description,
            personality: soul,
            identity: identity,
            roleCard: roleCard,
            reasoning: reasoning
        )
    }
    
    // MARK: - File Loading
    
    private func loadTeamContext(_ team: String) async throws -> TeamContext {
        let path = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("TEAM.md")
        
        guard FileManager.default.fileExists(atPath: path.path) else {
            throw BotLoaderError.fileNotFound("TEAM.md for team \(team)")
        }
        
        let content = try String(contentsOf: path, encoding: .utf8)
        return try TeamContext.parse(content)
    }
    
    private func loadBotSoul(team: String, bot: String) async throws -> BotSoul {
        // Check workspace override first
        let workspacePath = workspaceDirectory
            .appendingPathComponent("Bots")
            .appendingPathComponent(bot)
            .appendingPathComponent("SOUL.md")
        
        let teamPath = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("\(bot)_SOUL.md")
        
        let path = FileManager.default.fileExists(atPath: workspacePath.path)
            ? workspacePath
            : teamPath
        
        guard FileManager.default.fileExists(atPath: path.path) else {
            throw BotLoaderError.fileNotFound("\(bot)_SOUL.md")
        }
        
        let content = try String(contentsOf: path, encoding: .utf8)
        return try BotSoul.parse(content)
    }
    
    private func loadBotIdentity(team: String, bot: String) async throws -> BotIdentity {
        let workspacePath = workspaceDirectory
            .appendingPathComponent("Bots")
            .appendingPathComponent(bot)
            .appendingPathComponent("IDENTITY.md")
        
        let teamPath = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("\(bot)_IDENTITY.md")
        
        let path = FileManager.default.fileExists(atPath: workspacePath.path)
            ? workspacePath
            : teamPath
        
        guard FileManager.default.fileExists(atPath: path.path) else {
            throw BotLoaderError.fileNotFound("\(bot)_IDENTITY.md")
        }
        
        let content = try String(contentsOf: path, encoding: .utf8)
        return try BotIdentity.parse(content)
    }
    
    private func loadBotRole(bot: String) async throws -> BotRoleCard {
        let path = rolesDirectory
            .appendingPathComponent("\(bot)_ROLE.md")
        
        guard FileManager.default.fileExists(atPath: path.path) else {
            // Use default role card if not found
            return BotRoleCard(
                domain: bot,
                capabilities: BotCapabilities(),
                hardBans: [],
                permissions: []
            )
        }
        
        let content = try String(contentsOf: path, encoding: .utf8)
        return try BotRoleCard.parse(content)
    }
    
    private func loadBotReasoning(team: String, bot: String) async throws -> ReasoningConfig {
        let path = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("\(bot)_reasoning.json")
        
        guard FileManager.default.fileExists(atPath: path.path) else {
            return ReasoningConfig() // Default config
        }
        
        let data = try Data(contentsOf: path)
        return try JSONDecoder().decode(ReasoningConfig.self, from: data)
    }
}

// MARK: - Supporting Types

/// Complete bot configuration loaded from files.
public struct CompleteBotConfig: Sendable {
    public let role: BotRole
    public let team: String
    public let botName: String
    public let displayName: String
    public let icon: String
    public let description: String
    public let personality: BotSoul
    public let identity: BotIdentity
    public let roleCard: BotRoleCard
    public let reasoning: ReasoningConfig
    
    public init(
        role: BotRole,
        team: String,
        botName: String,
        displayName: String,
        icon: String,
        description: String,
        personality: BotSoul,
        identity: BotIdentity,
        roleCard: BotRoleCard,
        reasoning: ReasoningConfig
    ) {
        self.role = role
        self.team = team
        self.botName = botName
        self.displayName = displayName
        self.icon = icon
        self.description = description
        self.personality = personality
        self.identity = identity
        self.roleCard = roleCard
        self.reasoning = reasoning
    }
}

/// Errors for bot loading.
public enum BotLoaderError: Error, Sendable {
    case fileNotFound(String)
    case parseError(String)
    case invalidRole(String)
}