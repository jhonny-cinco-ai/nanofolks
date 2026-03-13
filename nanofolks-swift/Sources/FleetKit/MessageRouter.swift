// MessageRouter.swift
// Central message router that coordinates messages between channels and FleetManager.

import Core
import ChannelKit
import Foundation

/// Routes incoming messages to the FleetManager and handles responses.
public actor MessageRouter {
    private let fleetManager: FleetManager
    private var routingHandler: ((MessageEnvelope, RoutingDecision) async throws -> Void)?
    private var responseHandler: ((Response, String, Channel) async throws -> Void)?
    
    public init(fleetManager: FleetManager) {
        self.fleetManager = fleetManager
    }
    
    // MARK: - Routing
    
    /// Set the routing handler callback.
    public func setRoutingHandler(
        _ handler: @escaping (MessageEnvelope, RoutingDecision) async throws -> Void
    ) {
        self.routingHandler = handler
    }

    /// Set the response sender callback.
    public func setResponseHandler(
        _ handler: @escaping (Response, String, Channel) async throws -> Void
    ) {
        self.responseHandler = handler
    }
    
    /// Route an incoming message envelope.
    public func route(_ envelope: MessageEnvelope) async throws -> RoutingDecision {
        // Process through FleetManager
        let responses = try await fleetManager.process(
            message: envelope.message,
            in: envelope.roomId
        )
        
        // Determine routing decision based on responses
        let decision: RoutingDecision
        if responses.isEmpty {
            decision = .noBot(reason: "No bot generated a response")
        } else if responses.count == 1 {
            let primaryRole = inferRole(fromBotName: responses[0].botName) ?? .leader
            decision = .singleBot(
                primaryRole,
                confidence: responses[0].metadata?.confidence ?? 0.5
            )
        } else {
            let roles = Array(Set(responses.compactMap { inferRole(fromBotName: $0.botName) }))
            decision = roles.isEmpty ? .allBots : .multiBot(roles)
        }
        
        // Call routing handler if set
        if let handler = routingHandler {
            try await handler(envelope, decision)
        }
        
        return decision
    }
    
    /// Handle a response and send it back through the appropriate channel.
    public func sendResponse(
        _ response: Response,
        to roomId: String,
        through channel: Channel
    ) async throws {
        guard let handler = responseHandler else {
            throw CoreError.configurationError("Response handler not configured")
        }
        try await handler(response, roomId, channel)
    }

    // MARK: - Private

    private func inferRole(fromBotName botName: String) -> BotRole? {
        let normalized = botName.lowercased()

        if let exact = BotRole(rawValue: normalized) {
            return exact
        }

        for role in BotRole.allCases where normalized.contains(role.rawValue) {
            return role
        }

        let aliasMap: [BotRole: [String]] = [
            .leader: ["captain"],
            .coder: ["gunner"],
            .researcher: ["navigator"],
            .social: ["lookout"],
            .creative: ["artist"],
            .auditor: ["quartermaster"]
        ]

        for (role, aliases) in aliasMap where aliases.contains(where: normalized.contains) {
            return role
        }

        return nil
    }
}
