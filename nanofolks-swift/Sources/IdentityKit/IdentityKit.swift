// IdentityKit.swift
// Team and identity management for the nanofolks ecosystem.

import Core
import Foundation

// IdentityKit provides:
// - TeamManager: Manages team selection and bot profiles
// - Team loading from Teams/ directory
// - Bot profile loading with three-layer identity system
// - Workspace customization support

@_exported import struct Core.TeamProfile
@_exported import struct Core.BotTeamProfile
@_exported import struct Core.BotConfig
@_exported import struct Core.BotCapabilities
@_exported import struct Core.BotBehavior
@_exported import enum Core.BotRole
@_exported import struct Core.ReasoningConfig