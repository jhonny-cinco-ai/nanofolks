// BotKit.swift
// Bot loading and management for the nanofolks ecosystem.
// Loads bots from file-based configuration (Teams/{team}/).

import Core
import Foundation

// BotKit provides:
// - BotLoader: Loads bot configurations from markdown/JSON files
// - BotFactory: Creates bot instances from loaded configs
// - CharacterBot: Concrete bot implementation with personality
// - CompleteBotConfig: All bot configuration in one struct