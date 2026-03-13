// ResponseCombiner.swift
// Combines multiple bot responses into a coherent conversation.
// Inspired by Python implementation: agent/response_combiner.py

import Core
import Foundation

/// Combines responses from multiple bots into a coherent output.
public actor ResponseCombiner {
    
    /// Configuration for response combining.
    public struct Config: Sendable {
        public let maxResponseLength: Int
        public let combineMode: CombineMode
        public let separator: String
        
        public init(
            maxResponseLength: Int = 2000,
            combineMode: CombineMode = .concatenate,
            separator: String = "\n\n"
        ) {
            self.maxResponseLength = maxResponseLength
            self.combineMode = combineMode
            self.separator = separator
        }
    }
    
    /// Mode for combining responses.
    public enum CombineMode: Sendable {
        case concatenate      // Join with separator
        case summarize        // Use LLM to summarize
        case pickBest         // Pick highest confidence response
        case sequential       // Present as threaded conversation
    }
    
    private let config: Config
    
    public init(config: Config = Config()) {
        self.config = config
    }
    
    // MARK: - Combining
    
    /// Combine multiple responses into one or more responses.
    public func combine(
        responses: [Response],
        for message: Message
    ) async -> [Response] {
        // Filter out empty responses
        let validResponses = responses.filter { !$0.content.isEmpty }
        
        guard validResponses.count > 1 else {
            return validResponses
        }
        
        switch config.combineMode {
        case .concatenate:
            return concatenate(responses: validResponses)
            
        case .summarize:
            // Would need LLM to summarize
            return concatenate(responses: validResponses)
            
        case .pickBest:
            return pickBest(responses: validResponses)
            
        case .sequential:
            return validResponses // Return as-is for sequential display
        }
    }
    
    // MARK: - Combining Strategies
    
    private func concatenate(responses: [Response]) -> [Response] {
        // Group responses by bot to avoid duplicates from same bot
        var seenBots: Set<String> = []
        var uniqueResponses: [Response] = []
        
        for response in responses {
            if !seenBots.contains(response.botName) {
                seenBots.insert(response.botName)
                uniqueResponses.append(response)
            }
        }
        
        if uniqueResponses.count == 1 {
            return uniqueResponses
        }
        
        // Build combined response with attribution
        var combinedContent = ""
        var totalTokens = 0
        var toolsInvoked: [String] = []
        
        for (index, response) in uniqueResponses.enumerated() {
            if index > 0 {
                combinedContent += config.separator
            }
            
            // Add bot attribution
            combinedContent += "**\(response.botName)**: \(response.content)"
            
            // Accumulate metadata
            totalTokens += response.metadata?.tokensUsed ?? 0
            if let tools = response.metadata?.toolsInvoked {
                toolsInvoked.append(contentsOf: tools)
            }
            
            // Check length limit
            if combinedContent.count > config.maxResponseLength {
                combinedContent = String(combinedContent.prefix(config.maxResponseLength))
                combinedContent += "\n\n_[Response truncated due to length]_"
                break
            }
        }
        
        let combinedResponse = Response(
            botName: "Fleet", // Or could use primary bot name
            content: combinedContent,
            metadata: ResponseMetadata(
                modelUsed: nil,
                tokensUsed: totalTokens,
                toolsInvoked: Array(Set(toolsInvoked)), // Remove duplicates
                confidence: nil
            )
        )
        
        return [combinedResponse]
    }
    
    private func pickBest(responses: [Response]) -> [Response] {
        // Pick the response with highest confidence or longest content
        let best = responses.max { a, b in
            let aConfidence = a.metadata?.confidence ?? 0.5
            let bConfidence = b.metadata?.confidence ?? 0.5
            return aConfidence < bConfidence
        }
        
        return best.map { [$0] } ?? responses
    }
    
    // MARK: - Formatting
    
    /// Format a multi-bot response for display.
    public func formatMultiBotResponse(
        responses: [Response],
        intro: String? = nil
    ) -> String {
        var result = ""
        
        if let intro = intro {
            result += "\(intro)\n\n"
        }
        
        for (index, response) in responses.enumerated() {
            if index > 0 {
                result += config.separator
            }
            result += "**\(response.botName)**: \(response.content)"
        }
        
        return result
    }
    
    /// Check if responses should be combined.
    public func shouldCombine(responses: [Response]) -> Bool {
        return responses.count > 1
    }
}