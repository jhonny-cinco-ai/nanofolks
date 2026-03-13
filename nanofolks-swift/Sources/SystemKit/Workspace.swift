// Workspace.swift
// macOS workspace integration.

import AppKit
import Foundation

// MARK: - Workspace Tool

/// Manages macOS workspace operations.
public actor Workspace {
    private let fileManager = FileManager.default
    
    public init() {}
    
    // MARK: - File Operations
    
    /// Open a file or directory in Finder.
    public func openInFinder(path: String) async throws {
        let url = URL(fileURLWithPath: path).standardized
        try fileManager.attributesOfItem(atPath: url.path)
        NSWorkspace.shared.open(url.deletingLastPathComponent())
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }
    
    /// List contents of a directory.
    public func listDirectory(path: String) async throws -> [FileInfo] {
        let url = URL(fileURLWithPath: path).standardized
        let contents = try fileManager.contentsOfDirectory(at: url, includingPropertiesForKeys: [
            .nameKey, .isDirectoryKey, .fileSizeKey, .contentModificationDateKey
        ])
        
        return try contents.map { url in
            let attrs = try fileManager.attributesOfItem(atPath: url.path)
            return FileInfo(
                name: url.lastPathComponent,
                path: url.path,
                isDirectory: (attrs[.type] as? FileAttributeType) == .typeDirectory,
                size: attrs[.size] as? Int64 ?? 0,
                modifiedAt: attrs[.modificationDate] as? Date
            )
        }
    }
    
    /// Read file contents.
    public func readFile(path: String) async throws -> Data {
        let url = URL(fileURLWithPath: path).standardized
        return try Data(contentsOf: url)
    }
    
    /// Write data to file.
    public func writeFile(path: String, data: Data) async throws {
        let url = URL(fileURLWithPath: path).standardized
        try data.write(to: url)
    }
    
    // MARK: - App Operations
    
    /// Open an application by name.
    public func openApp(name: String) async throws {
        if let appUrl = NSWorkspace.shared.urlForApplication(withBundleIdentifier: name) {
            try await NSWorkspace.shared.openApplication(at: appUrl, configuration: NSWorkspace.OpenConfiguration())
        } else {
            throw WorkspaceError.appNotFound(name)
        }
    }
    
    /// Get list of running applications.
    public func getRunningApps() -> [AppInfo] {
        return NSWorkspace.shared.runningApplications.compactMap { app in
            guard let name = app.localizedName else { return nil }
            return AppInfo(
                name: name,
                bundleId: app.bundleIdentifier ?? "",
                isActive: app.isActive
            )
        }
    }
    
    // MARK: - URL Operations
    
    /// Open URL in default browser.
    public func openURL(_ url: String) async throws {
        guard let url = URL(string: url) else {
            throw WorkspaceError.invalidURL(url)
        }
        NSWorkspace.shared.open(url)
    }
}

// MARK: - Supporting Types

public struct FileInfo: Sendable, Codable {
    public let name: String
    public let path: String
    public let isDirectory: Bool
    public let size: Int64
    public let modifiedAt: Date?
    
    public init(name: String, path: String, isDirectory: Bool, size: Int64, modifiedAt: Date?) {
        self.name = name
        self.path = path
        self.isDirectory = isDirectory
        self.size = size
        self.modifiedAt = modifiedAt
    }
}

public struct AppInfo: Sendable, Codable {
    public let name: String
    public let bundleId: String
    public let isActive: Bool
    
    public init(name: String, bundleId: String, isActive: Bool) {
        self.name = name
        self.bundleId = bundleId
        self.isActive = isActive
    }
}

public enum WorkspaceError: Error, Sendable {
    case appNotFound(String)
    case invalidURL(String)
    case fileNotFound(String)
    case permissionDenied(String)
}