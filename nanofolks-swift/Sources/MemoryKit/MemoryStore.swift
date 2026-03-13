// MemoryStore.swift
// Memory storage implementations for the nanofolks ecosystem.

import Core
import Foundation

// MARK: - SQLite Memory Store

/// SQLite-based persistent memory store.
public actor SQLiteMemoryStore: MemoryStore {
    private let databasePath: URL
    private var connection: SQLiteConnection?
    
    public init(databasePath: URL) {
        self.databasePath = databasePath
    }
    
    public func initialize() async throws {
        connection = try SQLiteConnection(path: databasePath)
        try await createTables()
    }
    
    public func store(entry: MemoryEntry) async throws {
        guard let conn = connection else {
            throw CoreError.memoryError("Database not initialized")
        }
        
        let query = """
        INSERT INTO memories (id, content, embedding, metadata, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        let embeddingData = try JSONEncoder().encode(entry.embedding ?? [])
        let metadataJson = try JSONEncoder().encode(entry.metadata)
        
        try await conn.execute(query, parameters: [
            entry.id,
            entry.content,
            embeddingData,
            metadataJson,
            entry.createdAt,
            entry.updatedAt
        ])
    }
    
    public func retrieve(ids: [String]) async throws -> [MemoryEntry] {
        guard let conn = connection else {
            throw CoreError.memoryError("Database not initialized")
        }
        
        let placeholders = ids.map { _ in "?" }.joined(separator: ",")
        let query = "SELECT * FROM memories WHERE id IN (\(placeholders))"
        
        let rows = try await conn.query(query, parameters: ids)
        return rows.compactMap { row -> MemoryEntry? in
            let metadata = try? JSONDecoder().decode(MemoryMetadata.self, from: row["metadata"] as? Data ?? Data())
            let embedding = try? JSONDecoder().decode([Float].self, from: row["embedding"] as? Data ?? Data())
            return MemoryEntry(
                id: row["id"] as? String ?? "",
                content: row["content"] as? String ?? "",
                embedding: embedding,
                metadata: metadata ?? MemoryMetadata(type: .conversation),
                createdAt: row["created_at"] as? Date ?? Date(),
                updatedAt: row["updated_at"] as? Date ?? Date()
            )
        }
    }
    
    public func search(query: String, limit: Int) async throws -> [MemoryEntry] {
        guard let conn = connection else {
            throw CoreError.memoryError("Database not initialized")
        }
        
        let sql = """
        SELECT * FROM memories
        WHERE content LIKE ?
        ORDER BY importance DESC, created_at DESC
        LIMIT ?
        """
        
        let rows = try await conn.query(sql, parameters: ["%\(query)%", limit])
        return rows.compactMap { row -> MemoryEntry? in
            // Parse row same as above
            nil // Placeholder
        }
    }
    
    public func searchByEmbedding(embedding: [Float], limit: Int) async throws -> [MemoryEntry] {
        // TODO: Implement vector similarity search
        return []
    }
    
    public func delete(ids: [String]) async throws {
        guard let conn = connection else {
            throw CoreError.memoryError("Database not initialized")
        }
        
        let placeholders = ids.map { _ in "?" }.joined(separator: ",")
        let query = "DELETE FROM memories WHERE id IN (\(placeholders))"
        try await conn.execute(query, parameters: ids)
    }
    
    public func deleteRoom(roomId: String) async throws {
        guard let conn = connection else {
            throw CoreError.memoryError("Database not initialized")
        }
        
        let query = "DELETE FROM memories WHERE metadata->>'roomId' = ?"
        try await conn.execute(query, parameters: [roomId])
    }
    
    public func getMemoriesForBot(botName: String, limit: Int) async throws -> [MemoryEntry] {
        guard let conn = connection else {
            throw CoreError.memoryError("Database not initialized")
        }
        
        let query = """
        SELECT * FROM memories
        WHERE metadata->>'botName' = ?
        ORDER BY created_at DESC
        LIMIT ?
        """
        
        let rows = try await conn.query(query, parameters: [botName, limit])
        return rows.compactMap { _ -> MemoryEntry? in nil }
    }
    
    public func getStats() async throws -> MemoryStats {
        // TODO: Implement stats computation
        return MemoryStats(totalEntries: 0, totalTokens: 0)
    }
    
    private func createTables() async throws {
        guard let conn = connection else { return }
        
        let createMemoriesTable = """
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            embedding BLOB,
            metadata BLOB,
            created_at REAL,
            updated_at REAL
        )
        """
        
        try await conn.execute(createMemoriesTable, parameters: [])
        
        let createIndex = "CREATE INDEX IF NOT EXISTS idx_memories_content ON memories(content)"
        try await conn.execute(createIndex, parameters: [])
    }
}

// MARK: - SQLite Connection (Placeholder)

/// Placeholder for SQLite connection.
internal actor SQLiteConnection {
    private let path: URL
    
    init(path: URL) throws {
        self.path = path
        // Initialize SQLite connection
    }
    
    func execute(_ query: String, parameters: [Any]) async throws {
        // Execute query
    }
    
    func query(_ query: String, parameters: [Any]) async throws -> [[String: Any]] {
        // Execute query and return results
        return []
    }
}

// MARK: - In-Memory Store

/// In-memory memory store for testing.
public actor InMemoryStore: MemoryStore {
    private var entries: [String: MemoryEntry] = [:]
    
    public init() {}
    
    public func store(entry: MemoryEntry) async throws {
        entries[entry.id] = entry
    }
    
    public func retrieve(ids: [String]) async throws -> [MemoryEntry] {
        return ids.compactMap { entries[$0] }
    }
    
    public func search(query: String, limit: Int) async throws -> [MemoryEntry] {
        return entries.values
            .filter { $0.content.localizedCaseInsensitiveContains(query) }
            .sorted { $0.createdAt > $1.createdAt }
            .prefix(limit)
            .map { $0 }
    }
    
    public func searchByEmbedding(embedding: [Float], limit: Int) async throws -> [MemoryEntry] {
        // TODO: Implement embedding similarity
        return []
    }
    
    public func delete(ids: [String]) async throws {
        for id in ids {
            entries.removeValue(forKey: id)
        }
    }
    
    public func deleteRoom(roomId: String) async throws {
        entries = entries.filter { $0.value.metadata.roomId != roomId }
    }
    
    public func getMemoriesForBot(botName: String, limit: Int) async throws -> [MemoryEntry] {
        return entries.values
            .filter { $0.metadata.botName == botName }
            .sorted { $0.createdAt > $1.createdAt }
            .prefix(limit)
            .map { $0 }
    }
    
    public func getStats() async throws -> MemoryStats {
        return MemoryStats(
            totalEntries: entries.count,
            totalTokens: entries.values.reduce(0) { $0 + $1.content.count / 4 }
        )
    }
}