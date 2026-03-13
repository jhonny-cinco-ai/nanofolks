// PromptLoader.swift
// Prompt management for the nanofolks ecosystem.
// Prompts are stored as markdown files, completely decoupled from code.

import Core
import Foundation

// MARK: - Prompt Loader

/// Loads and renders prompts from markdown files.
public actor PromptLoader {
    private let promptsDirectory: URL
    private var promptCache: [String: Prompt] = [:]
    
    public init(promptsDirectory: URL) {
        self.promptsDirectory = promptsDirectory
    }
    
    /// Load a prompt by ID.
    public func load(id: String) async throws -> Prompt {
        if let cached = promptCache[id] {
            return cached
        }
        
        let prompt = try loadFromFile(id: id)
        promptCache[id] = prompt
        return prompt
    }
    
    /// Render a prompt with variables.
    public func render(
        id: String,
        variables: [String: String] = [:]
    ) async throws -> String {
        let prompt = try await load(id: id)
        return prompt.render(with: variables)
    }
    
    /// Clear the prompt cache.
    public func clearCache() {
        promptCache.removeAll()
    }
    
    /// Reload prompts from disk.
    public func reload() async throws {
        promptCache.removeAll()
    }
    
    // MARK: - Private
    
    private func loadFromFile(id: String) throws -> Prompt {
        let filePath = promptsDirectory
            .appendingPathComponent(id.replacingOccurrences(of: ".", with: "/"))
            .appendingPathExtension("md")
        
        guard FileManager.default.fileExists(atPath: filePath.path) else {
            throw CoreError.fileNotFound("Prompt not found: \(id)")
        }
        
        let content = try String(contentsOf: filePath, encoding: .utf8)
        return try Prompt.parse(id: id, content: content)
    }
}

// MARK: - Prompt Model

/// A prompt loaded from a markdown file.
public struct Prompt: Sendable, Codable {
    public let id: String
    public let version: String
    public let models: [String]
    public let minTokens: Int
    public let maxTokens: Int
    public let tags: [String]
    public let variables: [PromptVariable]
    public let content: String
    
    public init(
        id: String,
        version: String = "1.0.0",
        models: [String] = [],
        minTokens: Int = 100,
        maxTokens: Int = 2000,
        tags: [String] = [],
        variables: [PromptVariable] = [],
        content: String
    ) {
        self.id = id
        self.version = version
        self.models = models
        self.minTokens = minTokens
        self.maxTokens = maxTokens
        self.tags = tags
        self.variables = variables
        self.content = content
    }
    
    /// Render prompt with variable substitutions.
    public func render(with variables: [String: String]) -> String {
        var rendered = content
        for (key, value) in variables {
            rendered = rendered.replacingOccurrences(
                of: "{\(key)}",
                with: value
            )
        }
        return rendered
    }
    
    /// Parse a prompt from markdown content with YAML frontmatter.
    public static func parse(id: String, content: String) throws -> Prompt {
        let lines = content.components(separatedBy: "\n")
        
        var yamlFrontmatter = ""
        var markdownContent = ""
        var inYAML = false
        var yamlEnded = false
        
        for line in lines {
            if line == "---" {
                if !yamlEnded {
                    if inYAML {
                        yamlEnded = true
                        inYAML = false
                    } else {
                        inYAML = true
                    }
                } else {
                    markdownContent += line + "\n"
                }
            } else if inYAML {
                yamlFrontmatter += line + "\n"
            } else {
                markdownContent += line + "\n"
            }
        }
        
        let metadata = parseYAMLFrontmatter(yamlFrontmatter)
        
        return Prompt(
            id: id,
            version: metadata["version"] as? String ?? "1.0.0",
            models: (metadata["models"] as? [String]) ?? [],
            minTokens: metadata["min_tokens"] as? Int ?? 100,
            maxTokens: metadata["max_tokens"] as? Int ?? 2000,
            tags: (metadata["tags"] as? [String]) ?? [],
            variables: parseVariables(from: markdownContent),
            content: markdownContent.trimmingCharacters(in: .whitespacesAndNewlines)
        )
    }
    
    private static func parseYAMLFrontmatter(_ yaml: String) -> [String: Any] {
        var metadata: [String: Any] = [:]
        
        for line in yaml.components(separatedBy: "\n") {
            let parts = line.split(separator: ":", maxSplits: 1)
            guard parts.count == 2 else { continue }
            
            let key = parts[0].trimmingCharacters(in: .whitespaces)
            let value = parts[1].trimmingCharacters(in: .whitespaces)
            
            if value.hasPrefix("[") && value.hasSuffix("]") {
                let arrayValue = value
                    .dropFirst()
                    .dropLast()
                    .split(separator: ",")
                    .map { $0.trimmingCharacters(in: .whitespaces).replacingOccurrences(of: "\"", with: "")}
                metadata[key] = arrayValue
            } else if let intValue = Int(value) {
                metadata[key] = intValue
            } else {
                metadata[key] = value.replacingOccurrences(of: "\"", with: "")
            }
        }
        
        return metadata
    }
    
    private static func parseVariables(from content: String) -> [PromptVariable] {
        let regex = try! NSRegularExpression(pattern: "\\{(\\w+)\\}")
        let matches = regex.matches(in: content, range: NSRange(content.startIndex..., in: content))
        
        var variables: [PromptVariable] = []
        var seen = Set<String>()
        
        for match in matches {
            guard let range = Range(match.range(at: 1), in: content) else { continue }
            let name = String(content[range])
            
            if !seen.contains(name) {
                seen.insert(name)
                variables.append(PromptVariable(name: name, description: nil))
            }
        }
        
        return variables
    }
}

/// A variable placeholder in a prompt.
public struct PromptVariable: Sendable, Codable {
    public let name: String
    public let description: String?
    
    public init(name: String, description: String? = nil) {
        self.name = name
        self.description = description
    }
}

// MARK: - Prompt Templates

/// Built-in prompt templates for common use cases.
public enum PromptTemplates {
    /// System template for bot prompts.
    public static let systemTemplate = "Bot/base/system_template"
    
    /// Micro-turn constraints.
    public static let microTurn = "Bot/base/micro_turn"
    
    /// Tool instructions.
    public static let toolInstructions = "Bot/base/tool_instructions"
    
    /// Urgency evaluation.
    public static let urgencyEvaluation = "System/smart_discuss/urgency_evaluation"
    
    /// Intent detection.
    public static let intentDetection = "System/intent/detection"
    
    /// Learning notification.
    public static let learnedNotification = "System/memory/learned_notification"
}