// RoomSessionManager.swift
// Manages room-keyed sessions for conversation continuity.

import Core
import Foundation

/// Manages sessions keyed by room ID for conversation continuity.
public actor RoomSessionManager {
    private var sessions: [String: RoomSession] = [:]
    private let maxSessions: Int
    private let sessionTimeout: TimeInterval
    
    public init(
        maxSessions: Int = 100,
        sessionTimeout: TimeInterval = 3600 // 1 hour
    ) {
        self.maxSessions = maxSessions
        self.sessionTimeout = sessionTimeout
    }
    
    // MARK: - Session Management
    
    /// Get or create a session for a room.
    public func getSession(for roomId: String) -> RoomSession {
        if let existing = sessions[roomId] {
            // Check if session is still valid
            if Date().timeIntervalSince(existing.lastActivity) < sessionTimeout {
                var updated = existing
                updated.lastActivity = Date()
                sessions[roomId] = updated
                return updated
            }
        }
        
        // Create new session
        let newSession = RoomSession(
            roomId: roomId,
            createdAt: Date(),
            lastActivity: Date()
        )
        sessions[roomId] = newSession
        
        // Clean up old sessions if needed
        cleanupOldSessions()
        
        return newSession
    }
    
    /// End a session for a room.
    public func endSession(for roomId: String) {
        sessions.removeValue(forKey: roomId)
    }
    
    /// Get all active session room IDs.
    public func getActiveSessions() -> [String] {
        cleanupOldSessions()
        return Array(sessions.keys)
    }
    
    /// Check if a session exists for a room.
    public func hasSession(for roomId: String) -> Bool {
        return sessions[roomId] != nil
    }
    
    // MARK: - Cleanup
    
    private func cleanupOldSessions() {
        let now = Date()
        
        // Remove expired sessions
        sessions = sessions.filter { _, session in
            now.timeIntervalSince(session.lastActivity) < sessionTimeout
        }
        
        // If still over limit, remove oldest
        if sessions.count > maxSessions {
            let sorted = sessions.sorted { $0.value.lastActivity < $1.value.lastActivity }
            let toRemove = sorted.prefix(sessions.count - maxSessions)
            for (roomId, _) in toRemove {
                sessions.removeValue(forKey: roomId)
            }
        }
    }
}

// MARK: - Room Session

/// Session data for a room.
public struct RoomSession: Sendable, Codable {
    public let roomId: String
    public let createdAt: Date
    public var lastActivity: Date
    public var metadata: [String: String]
    
    public init(
        roomId: String,
        createdAt: Date,
        lastActivity: Date,
        metadata: [String: String] = [:]
    ) {
        self.roomId = roomId
        self.createdAt = createdAt
        self.lastActivity = lastActivity
        self.metadata = metadata
    }
}