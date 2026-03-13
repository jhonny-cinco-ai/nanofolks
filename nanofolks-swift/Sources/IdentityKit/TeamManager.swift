// TeamManager.swift
// Team and identity management for the nanofolks ecosystem.

import Core
import Foundation

// MARK: - Team Manager

/// Manages team selection and bot profiles.
public actor TeamManager {
    private let teamsDirectory: URL
    private let rolesDirectory: URL
    private let workspaceDirectory: URL
    private var currentTeam: String = "pirate_crew"
    private var cachedTeams: [String: TeamProfile] = [:]
    
    public init(
        teamsDirectory: URL,
        rolesDirectory: URL,
        workspaceDirectory: URL
    ) {
        self.teamsDirectory = teamsDirectory
        self.rolesDirectory = rolesDirectory
        self.workspaceDirectory = workspaceDirectory
    }
    
    // MARK: - Team Selection
    
    /// Get the currently selected team.
    public func getCurrentTeam() -> String {
        return currentTeam
    }
    
    /// Select a team.
    public func selectTeam(_ teamName: String) async throws {
        guard try await teamExists(teamName) else {
            throw CoreError.teamNotFound(teamName)
        }
        currentTeam = teamName
        try await saveTeamSelection(teamName)
    }
    
    /// Get all available teams.
    public func getAvailableTeams() async throws -> [String] {
        let contents = try FileManager.default.contentsOfDirectory(at: teamsDirectory, includingPropertiesForKeys: nil)
        return contents
            .filter { $0.hasDirectoryPath }
            .map { $0.lastPathComponent }
            .filter { !$0.hasPrefix(".") && !$0.hasPrefix("_") }
    }
    
    // MARK: - Bot Profiles
    
    /// Get a bot's profile for the current team.
    public func getBotTeamProfile(botRole: BotRole) async throws -> BotTeamProfile {
        let cacheKey = "\(currentTeam)_\(botRole.rawValue)"
        
        if let cached = cachedTeams[cacheKey] {
            return cached.botProfiles[botRole.rawValue]!
        }
        
        let profile = try await loadBotTeamProfile(team: currentTeam, botRole: botRole)
        return profile
    }
    
    /// Get all bot profiles for the current team.
    public func getAllBotProfiles() async throws -> [String: BotTeamProfile] {
        var profiles: [String: BotTeamProfile] = [:]
        
        for role in BotRole.allCases {
            let profile = try await getBotTeamProfile(botRole: role)
            profiles[role.rawValue] = profile
        }
        
        return profiles
    }
    
    // MARK: - Private
    
    private func teamExists(_ teamName: String) async throws -> Bool {
        let teamPath = teamsDirectory.appendingPathComponent(teamName)
        return FileManager.default.fileExists(atPath: teamPath.path)
    }
    
    private func saveTeamSelection(_ teamName: String) async throws {
        let selectionPath = workspaceDirectory
            .appendingPathComponent("Team")
            .appendingPathComponent("current_team.json")
        
        let selection: [String: String] = ["team": teamName]
        let data = try JSONEncoder().encode(selection)
        try data.write(to: selectionPath)
    }
    
    private func loadBotTeamProfile(team: String, botRole: BotRole) async throws -> BotTeamProfile {
        // Load team context (Layer 1)
        let teamContext = try await loadTeamContext(team)
        
        // Load bot soul and identity (Layer 2)
        let soul = try await loadBotSoul(team: team, bot: botRole.rawValue)
        let identity = try await loadBotIdentity(team: team, bot: botRole.rawValue)
        
        // Load role definition (Layer 3)
        let roleCard = try await loadBotRole(bot: botRole.rawValue)
        let reasoning = try await loadBotReasoning(team: team, bot: botRole.rawValue)
        
        return BotTeamProfile(
            botRole: botRole.rawValue,
            teamName: team,
            botName: identity.name,
            botTitle: identity.title,
            emoji: identity.emoji,
            personality: soul.vibe,
            greeting: soul.greeting,
            voice: soul.voice,
            roleCard: roleCard.domain,
            reasoning: reasoning,
            permissions: roleCard.permissions
        )
    }
    
    private func loadTeamContext(_ team: String) async throws -> TeamContext {
        let path = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("TEAM.md")
        
        let content = try String(contentsOf: path, encoding: .utf8)
        return try TeamContext.parse(content)
    }
    
    private func loadBotSoul(team: String, bot: String) async throws -> BotSoul {
        let path = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("\(bot)_SOUL.md")
        
        // Check for workspace override first
        let workspacePath = workspaceDirectory
            .appendingPathComponent("Bots")
            .appendingPathComponent(bot)
            .appendingPathComponent("SOUL.md")
        
        let actualPath = FileManager.default.fileExists(atPath: workspacePath.path)
            ? workspacePath
            : path
        
        let content = try String(contentsOf: actualPath, encoding: .utf8)
        return try BotSoul.parse(content)
    }
    
    private func loadBotIdentity(team: String, bot: String) async throws -> BotIdentity {
        let path = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("\(bot)_IDENTITY.md")
        
        let workspacePath = workspaceDirectory
            .appendingPathComponent("Bots")
            .appendingPathComponent(bot)
            .appendingPathComponent("IDENTITY.md")
        
        let actualPath = FileManager.default.fileExists(atPath: workspacePath.path)
            ? workspacePath
            : path
        
        let content = try String(contentsOf: actualPath, encoding: .utf8)
        return try BotIdentity.parse(content)
    }
    
    private func loadBotRole(bot: String) async throws -> BotRoleCard {
        let path = rolesDirectory
            .appendingPathComponent("\(bot)_ROLE.md")
        
        let content = try String(contentsOf: path, encoding: .utf8)
        return try BotRoleCard.parse(content)
    }
    
    private func loadBotReasoning(team: String, bot: String) async throws -> ReasoningConfig {
        let path = teamsDirectory
            .appendingPathComponent(team)
            .appendingPathComponent("\(bot)_reasoning.json")
        
        guard FileManager.default.fileExists(atPath: path.path) else {
            return ReasoningConfig()
        }
        
        let data = try Data(contentsOf: path)
        return try JSONDecoder().decode(ReasoningConfig.self, from: data)
    }
}

// MARK: - Supporting Types

/// Team context loaded from TEAM.md.
public struct TeamContext: Sendable, Codable {
    public let name: String
    public let description: String
    public let vibe: String
    public let coordinationStyle: String
    public let sharedValues: [String]
    
    public static func parse(_ markdown: String) throws -> TeamContext {
        // Parse markdown frontmatter and content
        // Simplified version - would need full markdown parsing
        return TeamContext(
            name: "",
            description: "",
            vibe: "",
            coordinationStyle: "",
            sharedValues: []
        )
    }
}

/// Bot soul loaded from {bot}_SOUL.md.
public struct BotSoul: Sendable, Codable {
    public let vibe: String
    public let greeting: String
    public let voice: String
    public let values: [String]
    
    public static func parse(_ markdown: String) throws -> BotSoul {
        // Parse markdown frontmatter and content
        return BotSoul(vibe: "", greeting: "", voice: "", values: [])
    }
}

/// Bot identity loaded from {bot}_IDENTITY.md.
public struct BotIdentity: Sendable, Codable {
    public let name: String
    public let title: String
    public let emoji: String
    public let description: String
    
    public static func parse(_ markdown: String) throws -> BotIdentity {
        // Parse markdown frontmatter and content
        return BotIdentity(name: "", title: "", emoji: "", description: "")
    }
}

/// Bot role card loaded from {bot}_ROLE.md.
public struct BotRoleCard: Sendable, Codable {
    public let domain: String
    public let capabilities: BotCapabilities
    public let hardBans: [String]
    public let permissions: [String]
    
    public static func parse(_ markdown: String) throws -> BotRoleCard {
        // Parse markdown
        return BotRoleCard(
            domain: "",
            capabilities: BotCapabilities(),
            hardBans: [],
            permissions: []
        )
    }
}