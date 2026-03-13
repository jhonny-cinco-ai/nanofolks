// SmartDispatch.swift
// LLM-based urgency evaluation for multi-bot routing.
// Inspired by Python implementation: bots/smart_dispatch.py

import Core
import ProviderKit
import PromptKit
import Foundation

/// SmartDispatch evaluates which bot(s) should respond to a message.
public actor SmartDispatch {
    private let provider: any LLMProvider
    private let bots: [BotRole: any Bot]
    private let room: Room?
    private let threshold: Double
    
    public init(
        provider: any LLMProvider,
        bots: [BotRole: any Bot],
        room: Room? = nil,
        threshold: Double = 0.5
    ) {
        self.provider = provider
        self.bots = bots
        self.room = room
        self.threshold = threshold
    }
    
    // MARK: - Dispatch Evaluation
    
    /// Evaluate message urgency and determine routing decision.
    public func evaluate(
        message: Message,
        context: BotContext
    ) async throws -> RoutingDecision {
        // Single bot available - route directly
        if bots.count == 1, let role = bots.keys.first {
            return .singleBot(role, confidence: 1.0)
        }
        
        // Check for @mentions
        if let mentionedBot = extractMention(from: message.content) {
            return .singleBot(mentionedBot, confidence: 1.0)
        }
        
        // Check for urgent keywords
        if isUrgent(message: message) {
            return .urgent(.leader)
        }
        
        // Use LLM to evaluate all bots in a single call
        let evaluations = try await evaluateAllBots(message: message, context: context)
        
        // Make routing decision based on evaluations
        return makeDecision(from: evaluations)
    }
    
    // MARK: - LLM Evaluation
    
    private func evaluateAllBots(
        message: Message,
        context: BotContext
    ) async throws -> [BotEvaluation] {
        // Build bot descriptions
        let botDescriptions = bots.map { role, bot in
            "\(role.rawValue): \(bot.config.description)"
        }.joined(separator: "\n")
        
        // Build prompt
        let prompt = """
        You are an urgency evaluator for a multi-bot system. Evaluate how urgently each bot should respond to the following message.
        
        Message: "\(message.content)"
        
        Available bots:
        \(botDescriptions)
        
        Evaluate each bot on a scale of 0.0 to 1.0 where:
        - 0.0-0.3: Low urgency - not relevant to this bot
        - 0.4-0.6: Medium urgency - somewhat relevant
        - 0.7-0.9: High urgency - very relevant, should respond
        - 1.0: Critical urgency - this bot must respond
        
        Return a JSON array with evaluations:
        [
          {"bot": "leader", "urgency": 0.8, "reason": "Brief reason"},
          {"bot": "researcher", "urgency": 0.3, "reason": "Brief reason"},
          ...
        ]
        """
        
        let request = LLMRequest(
            messages: [
                Message(role: .system, content: prompt),
                Message(role: .user, content: "Evaluate: \(message.content)")
            ],
            model: nil, // Use default
            temperature: 0.3, // Lower temperature for consistency
            maxTokens: 500
        )
        
        let response = try await provider.chat(request: request)
        
        // Parse JSON response
        return try parseEvaluations(from: response.content)
    }
    
    private func parseEvaluations(from content: String) throws -> [BotEvaluation] {
        // Extract JSON array from response if wrapped in prose.
        let jsonString: String
        if let jsonStart = content.firstIndex(of: "["),
           let jsonEnd = content.lastIndex(of: "]"),
           jsonStart <= jsonEnd {
            jsonString = String(content[jsonStart...jsonEnd])
        } else {
            jsonString = content.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        
        guard let data = jsonString.data(using: .utf8) else {
            throw SmartDispatchError.parseError("Could not convert response to data")
        }
        
        struct EvaluationDTO: Codable {
            let bot: String
            let urgency: Double
            let reason: String?
        }
        
        let dtos = try JSONDecoder().decode([EvaluationDTO].self, from: data)
        if dtos.isEmpty {
            throw SmartDispatchError.parseError("No bot evaluations returned")
        }
        
        return dtos.compactMap { dto in
            guard let role = BotRole(rawValue: dto.bot) else { return nil }
            return BotEvaluation(
                botRole: role,
                urgency: max(0.0, min(1.0, dto.urgency)),
                reason: dto.reason
            )
        }
    }
    
    // MARK: - Decision Making
    
    private func makeDecision(from evaluations: [BotEvaluation]) -> RoutingDecision {
        // Sort by urgency
        let sorted = evaluations.sorted { $0.urgency > $1.urgency }
        
        // Check for critical urgency
        if let critical = sorted.first, critical.urgency >= 0.9 {
            return .urgent(critical.botRole)
        }
        
        // Get bots above threshold
        let aboveThreshold = sorted.filter { $0.urgency >= threshold }
        
        if aboveThreshold.isEmpty {
            return .noBot(reason: "No bot urgency above threshold \(threshold)")
        }
        
        if aboveThreshold.count == 1 {
            return .singleBot(aboveThreshold[0].botRole, confidence: aboveThreshold[0].urgency)
        }
        
        // Multiple bots above threshold
        return .multiBot(aboveThreshold.map { $0.botRole })
    }
    
    // MARK: - Helper Methods
    
    private func extractMention(from content: String) -> BotRole? {
        let mentions = ["@leader", "@captain", "@coder", "@gunner", "@researcher", "@navigator",
                       "@social", "@lookout", "@creative", "@artist", "@auditor", "@quartermaster"]
        
        for mention in mentions {
            if content.localizedCaseInsensitiveContains(mention) {
                // Map mention to bot role
                switch mention {
                case "@leader", "@captain": return .leader
                case "@coder", "@gunner": return .coder
                case "@researcher", "@navigator": return .researcher
                case "@social", "@lookout": return .social
                case "@creative", "@artist": return .creative
                case "@auditor", "@quartermaster": return .auditor
                default: continue
                }
            }
        }
        
        return nil
    }
    
    private func isUrgent(message: Message) -> Bool {
        let urgentKeywords = [
            "urgent", "emergency", "asap", "immediately", "critical",
            "help", "problem", "broken", "error", "failed"
        ]
        
        let lowerContent = message.content.lowercased()
        return urgentKeywords.contains { lowerContent.contains($0) }
    }
}

// MARK: - Supporting Types

/// Evaluation result for a single bot.
public struct BotEvaluation: Sendable {
    public let botRole: BotRole
    public let urgency: Double
    public let reason: String?
    
    public init(botRole: BotRole, urgency: Double, reason: String? = nil) {
        self.botRole = botRole
        self.urgency = urgency
        self.reason = reason
    }
}

/// Errors for SmartDispatch.
public enum SmartDispatchError: Error, Sendable {
    case parseError(String)
    case evaluationFailed(String)
}
