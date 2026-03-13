// BotFactory.swift
// Creates bot instances from loaded configurations.

import Core
import ProviderKit
import PromptKit
import Foundation

/// Factory for creating bot instances from file-based configurations.
@available(macOS 14, *)
public actor FileBotFactory: @preconcurrency BotFactory {
    private let loader: BotLoader
    private let provider: any LLMProvider
    private let promptLoader: PromptLoader?
    
    public init(
        loader: BotLoader,
        provider: any LLMProvider,
        promptLoader: PromptLoader? = nil
    ) {
        self.loader = loader
        self.provider = provider
        self.promptLoader = promptLoader
    }
    
    // MARK: - BotFactory Protocol
    
    public func createBot(role: BotRole, team: TeamProfile) async throws -> any Bot {
        // Load complete bot configuration
        let config = try await loader.loadBotConfig(role: role, team: team.name)
        
        // Create bot instance
        return CharacterBot(
            config: config,
            provider: provider,
            promptLoader: promptLoader
        )
    }
    
    nonisolated public func availableRoles() -> [BotRole] {
        return BotRole.allCases
    }
    
    nonisolated public func isRoleAvailable(role: BotRole, team: String) -> Bool {
        // Check if files exist for this role in the team
        let teamPath = URL(fileURLWithPath: "Teams/\(team)")
        let soulPath = teamPath.appendingPathComponent("\(role.rawValue)_SOUL.md")
        
        return FileManager.default.fileExists(atPath: soulPath.path)
    }
}

// MARK: - Character Bot Implementation

/// A bot with personality loaded from files.
public actor CharacterBot: Bot {
    public let id: String
    public let role: BotRole
    public let config: BotConfig
    
    private let completeConfig: CompleteBotConfig
    private let provider: any LLMProvider
    private let promptLoader: PromptLoader?
    
    public init(
        config: CompleteBotConfig,
        provider: any LLMProvider,
        promptLoader: PromptLoader? = nil
    ) {
        self.id = "\(config.team).\(config.role.rawValue).\(config.botName)"
        self.role = config.role
        self.completeConfig = config
        self.provider = provider
        self.promptLoader = promptLoader
        
        // Create BotConfig from CompleteBotConfig
        self.config = BotConfig(
            name: config.botName,
            displayName: config.displayName,
            icon: config.icon,
            description: config.description,
            version: "1.0.0",
            enabled: true,
            capabilities: config.roleCard.capabilities,
            behavior: BotBehavior(
                responseStyle: config.reasoning.mode,
                speakThreshold: config.reasoning.confidenceThreshold,
                maxResponseLength: 400,
                useMicroTurns: true
            ),
            tools: config.roleCard.permissions
        )
    }
    
    // MARK: - Bot Protocol
    
    public func process(message: Message, context: BotContext) async throws -> BotResult {
        // Build system prompt from bot personality
        let systemPrompt = try await buildSystemPrompt()
        
        // Build conversation context
        var messages: [Message] = [
            Message(role: .system, content: systemPrompt),
            Message(role: .system, content: "You are \(completeConfig.botName), \(completeConfig.identity.title) of the \(completeConfig.team).")
        ]
        
        // Add conversation history
        messages.append(contentsOf: context.conversationHistory.suffix(10))
        
        // Add current message
        messages.append(message)
        
        // Call LLM
        let request = LLMRequest(
            messages: messages,
            temperature: 0.7,
            maxTokens: 500
        )
        
        let response = try await provider.chat(request: request)
        
        // Create Response object
        let botResponse = Response(
            botName: completeConfig.botName,
            content: response.content,
            metadata: ResponseMetadata(
                modelUsed: response.model,
                tokensUsed: response.usage?.totalTokens,
                toolsInvoked: nil,
                confidence: 0.8
            )
        )
        
        return .respond(botResponse)
    }
    
    // MARK: - Private
    
    private func buildSystemPrompt() async throws -> String {
        // Prefer PromptKit template if available.
        if let promptLoader {
            let rendered = try await promptLoader.render(
                id: PromptTemplates.systemTemplate,
                variables: [
                    "bot_name": completeConfig.botName,
                    "bot_title": completeConfig.identity.title,
                    "soul": completeConfig.personality.vibe,
                    "role": completeConfig.roleCard.domain,
                    "identity": completeConfig.identity.description,
                    "behavior": completeConfig.reasoning.mode,
                    "voice": completeConfig.personality.voice
                ]
            )
            if !rendered.isEmpty {
                return rendered
            }
        }

        // Fallback prompt when templates are unavailable.
        var prompt = ""
        
        // Add personality
        prompt += completeConfig.personality.vibe + "\n\n"
        
        // Add role
        prompt += "Your role: \(completeConfig.roleCard.domain)\n\n"
        
        // Add capabilities
        if completeConfig.roleCard.capabilities.canInvokeOthers {
            prompt += "You can coordinate with other bots when needed.\n"
        }
        
        // Add constraints
        if !completeConfig.roleCard.hardBans.isEmpty {
            prompt += "\nImportant constraints:\n"
            for ban in completeConfig.roleCard.hardBans {
                prompt += "- \(ban)\n"
            }
        }
        
        // Add micro-turn instruction
        prompt += "\nKeep your responses concise (1-3 sentences) unless explaining something complex."
        
        return prompt
    }
}
