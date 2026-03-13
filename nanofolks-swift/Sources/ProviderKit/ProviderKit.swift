// ProviderKit.swift
// LLM provider implementations for the nanofolks ecosystem.

import Core
import Foundation

// ProviderKit provides:
// - OpenAIProvider: OpenAI API client
// - ProviderFactory: Creates provider instances
// - ProviderRegistry: Manages multiple providers
// - Future: LocalProvider, AnthropicProvider, etc.

@_exported import protocol Core.LLMProvider
@_exported import struct Core.LLMRequest
@_exported import struct Core.LLMResponse
@_exported import struct Core.LLMStreamChunk
@_exported import struct Core.TokenUsage
@_exported import struct Core.ProviderConfig