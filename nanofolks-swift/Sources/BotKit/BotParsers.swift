// BotParsers.swift
// Parsers for bot configuration markdown files.

import Core
import Foundation

// MARK: - Bot Soul Parser

/// Bot personality loaded from SOUL.md.
public struct BotSoul: Sendable, Codable {
    public let vibe: String
    public let greeting: String
    public let voice: String
    public let values: [String]
    
    public init(vibe: String, greeting: String, voice: String, values: [String]) {
        self.vibe = vibe
        self.greeting = greeting
        self.voice = voice
        self.values = values
    }
    
    public static func parse(_ markdown: String) throws -> BotSoul {
        var vibe = ""
        var greeting = ""
        var voice = ""
        var values: [String] = []
        
        let lines = markdown.components(separatedBy: "\n")
        var currentSection = ""
        
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            
            // Parse section headers
            if trimmed.hasPrefix("## ") {
                currentSection = String(trimmed.dropFirst(3)).lowercased()
                continue
            }
            
            // Parse content based on section
            switch currentSection {
            case "vibe":
                if !trimmed.isEmpty && !trimmed.hasPrefix("#") {
                    vibe = trimmed
                }
            case "greeting":
                if !trimmed.isEmpty && !trimmed.hasPrefix("#") {
                    greeting = trimmed
                }
            case "voice":
                if !trimmed.isEmpty && !trimmed.hasPrefix("#") && !trimmed.hasPrefix("-") {
                    voice = trimmed
                }
            case "values":
                if trimmed.hasPrefix("- ") {
                    values.append(String(trimmed.dropFirst(2)))
                }
            default:
                break
            }
        }
        
        // Fallback: if vibe is empty, try to extract from first paragraph
        if vibe.isEmpty {
            let paragraphs = markdown.components(separatedBy: "\n\n")
            for paragraph in paragraphs {
                let clean = paragraph.trimmingCharacters(in: .whitespacesAndNewlines)
                if !clean.isEmpty && !clean.hasPrefix("#") {
                    vibe = clean
                    break
                }
            }
        }
        
        return BotSoul(
            vibe: vibe,
            greeting: greeting,
            voice: voice,
            values: values
        )
    }
}

// MARK: - Bot Identity Parser

/// Bot identity loaded from IDENTITY.md.
public struct BotIdentity: Sendable, Codable {
    public let name: String
    public let title: String
    public let emoji: String
    public let description: String
    
    public init(name: String, title: String, emoji: String, description: String) {
        self.name = name
        self.title = title
        self.emoji = emoji
        self.description = description
    }
    
    public static func parse(_ markdown: String) throws -> BotIdentity {
        var name = ""
        var title = ""
        var emoji = ""
        var description = ""
        
        let lines = markdown.components(separatedBy: "\n")
        
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            
            // Parse "**Name:** Value" format
            if trimmed.hasPrefix("**Name:**") {
                name = String(trimmed.dropFirst(9)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("**Title:**") {
                title = String(trimmed.dropFirst(10)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("**Creature:**") {
                title = String(trimmed.dropFirst(13)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("**Emoji:**") {
                emoji = String(trimmed.dropFirst(10)).trimmingCharacters(in: .whitespaces)
            } else if trimmed.hasPrefix("**Vibe:**") {
                description = String(trimmed.dropFirst(9)).trimmingCharacters(in: .whitespaces)
            }
        }
        
        // Fallback: extract emoji from first line if present
        if emoji.isEmpty {
            for char in markdown {
                if char.isEmoji {
                    emoji = String(char)
                    break
                }
            }
        }
        
        return BotIdentity(
            name: name,
            title: title,
            emoji: emoji,
            description: description
        )
    }
}

// MARK: - Bot Role Card Parser

/// Bot capabilities loaded from ROLE.md.
public struct BotRoleCard: Sendable, Codable {
    public let domain: String
    public let capabilities: BotCapabilities
    public let hardBans: [String]
    public let permissions: [String]
    
    public init(domain: String, capabilities: BotCapabilities, hardBans: [String], permissions: [String]) {
        self.domain = domain
        self.capabilities = capabilities
        self.hardBans = hardBans
        self.permissions = permissions
    }
    
    public static func parse(_ markdown: String) throws -> BotRoleCard {
        var domain = ""
        var canInvokeOthers = false
        var canCode = false
        var canDesign = false
        var maxConcurrentTasks = 1
        var hardBans: [String] = []
        var permissions: [String] = []
        
        let lines = markdown.components(separatedBy: "\n")
        var currentSection = ""
        
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            
            // Parse section headers
            if trimmed.hasPrefix("## ") {
                currentSection = String(trimmed.dropFirst(3)).lowercased()
                continue
            }
            
            // Parse content
            switch currentSection {
            case "domain":
                if trimmed.hasPrefix("**Primary:**") {
                    domain = String(trimmed.dropFirst(12)).trimmingCharacters(in: .whitespaces)
                }
            case "capabilities":
                if trimmed.contains("Can invoke other bots") {
                    canInvokeOthers = trimmed.contains("YES")
                } else if trimmed.contains("Max concurrent tasks") {
                    if let number = trimmed.components(separatedBy: CharacterSet.decimalDigits.inverted).compactMap(Int.init).first {
                        maxConcurrentTasks = number
                    }
                }
            case "hard bans", "hard bans 🚫":
                if trimmed.hasPrefix("🚫") || trimmed.hasPrefix("-") {
                    let ban = trimmed
                        .replacingOccurrences(of: "🚫", with: "")
                        .replacingOccurrences(of: "-", with: "")
                        .trimmingCharacters(in: .whitespaces)
                    if !ban.isEmpty {
                        hardBans.append(ban)
                    }
                }
            default:
                break
            }
        }
        
        return BotRoleCard(
            domain: domain,
            capabilities: BotCapabilities(
                canAudit: false,
                canCode: canCode,
                canDesign: canDesign,
                canInvokeOthers: canInvokeOthers,
                maxConcurrentTasks: maxConcurrentTasks
            ),
            hardBans: hardBans,
            permissions: permissions
        )
    }
}

// MARK: - Team Context Parser

/// Team context loaded from TEAM.md.
public struct TeamContext: Sendable, Codable {
    public let name: String
    public let description: String
    public let vibe: String
    public let coordinationStyle: String
    public let sharedValues: [String]
    
    public init(name: String, description: String, vibe: String, coordinationStyle: String, sharedValues: [String]) {
        self.name = name
        self.description = description
        self.vibe = vibe
        self.coordinationStyle = coordinationStyle
        self.sharedValues = sharedValues
    }
    
    public static func parse(_ markdown: String) throws -> TeamContext {
        let lines = markdown.components(separatedBy: "\n")
        var description = ""
        var vibe = ""
        var values: [String] = []
        
        var inVibeSection = false
        
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            
            if trimmed.hasPrefix("## Team Vibe") {
                inVibeSection = true
                continue
            }
            
            if trimmed.hasPrefix("## ") {
                inVibeSection = false
            }
            
            if inVibeSection && trimmed.hasPrefix("- ") {
                values.append(String(trimmed.dropFirst(2)))
            }
            
            if !trimmed.isEmpty && !trimmed.hasPrefix("#") && description.isEmpty {
                description = trimmed
            }
        }
        
        return TeamContext(
            name: "",
            description: description,
            vibe: vibe,
            coordinationStyle: "",
            sharedValues: values
        )
    }
}

// MARK: - Extensions

extension Character {
    var isEmoji: Bool {
        guard let scalar = unicodeScalars.first else { return false }
        return scalar.properties.isEmoji && scalar.value > 0x238C
    }
}