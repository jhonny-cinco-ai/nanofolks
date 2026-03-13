// Keyring.swift
// Secure credential storage using macOS Keychain.

import Foundation
import Security

// MARK: - Keyring

/// Secure credential storage using macOS Keychain.
public actor Keyring {
    private let service = "com.nanofolks.app"
    
    public init() {}
    
    // MARK: - Credential Management
    
    /// Store a credential securely.
    public func store(key: String, value: String) async throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: value.data(using: .utf8)!
        ]
        
        // Delete existing item first
        SecItemDelete(query as CFDictionary)
        
        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        
        guard status == errSecSuccess else {
            throw SecurityError.keychainError(status)
        }
    }
    
    /// Retrieve a credential.
    public func retrieve(key: String) async throws -> String? {
        var query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess else {
            return nil
        }
        
        guard let data = result as? Data else {
            return nil
        }
        
        return String(data: data, encoding: .utf8)
    }
    
    /// Delete a credential.
    public func delete(key: String) async throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key
        ]
        
        SecItemDelete(query as CFDictionary)
    }
    
    /// Check if a credential exists.
    public func exists(key: String) async -> Bool {
        do {
            return try await retrieve(key: key) != nil
        } catch {
            return false
        }
    }
}

// MARK: - Security Error

public enum SecurityError: Error, Sendable {
    case keychainError(OSStatus)
    case encryptionError(String)
    case decryptionError(String)
    case keyNotFound(String)
}

// MARK: - Audit Logger

/// Audit logging for security events.
public actor AuditLogger {
    private let logFile: URL
    
    public init() {
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        self.logFile = appSupport.appendingPathComponent("nanofolks").appendingPathComponent("audit.log")
        
        try? FileManager.default.createDirectory(at: logFile.deletingLastPathComponent(), withIntermediateDirectories: true)
    }
    
    /// Log a security event.
    public func log(event: AuditEvent) async throws {
        var entry = "[\(timestamp())] \(event.type.rawValue)"
        entry += " | user: \(event.userId ?? "unknown")"
        entry += " | action: \(event.action)"
        entry += " | resource: \(event.resource)"
        if let details = event.details {
            entry += " | details: \(details)"
        }
        entry += "\n"
        
        try appendToLog(entry)
    }
    
    private func timestamp() -> String {
        let formatter = ISO8601DateFormatter()
        return formatter.string(from: Date())
    }
    
    private func appendToLog(_ entry: String) throws {
        let data = entry.data(using: .utf8)!
        if FileManager.default.fileExists(atPath: logFile.path) {
            let handle = try FileHandle(forWritingTo: logFile)
            handle.seekToEndOfFile()
            handle.write(data)
            handle.closeFile()
        } else {
            try data.write(to: logFile)
        }
    }
}

// MARK: - Audit Event

public struct AuditEvent: Sendable, Codable {
    public let type: AuditEventType
    public let userId: String?
    public let action: String
    public let resource: String
    public let details: String?
    public let timestamp: Date
    
    public init(
        type: AuditEventType,
        userId: String? = nil,
        action: String,
        resource: String,
        details: String? = nil,
        timestamp: Date = Date()
    ) {
        self.type = type
        self.userId = userId
        self.action = action
        self.resource = resource
        self.details = details
        self.timestamp = timestamp
    }
}

public enum AuditEventType: String, Sendable, Codable, CaseIterable {
    case authentication
    case authorization
    case dataAccess
    case dataModification
    case configurationChange
    case securityEvent
}