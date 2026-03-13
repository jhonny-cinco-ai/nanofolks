// main.swift
// Basic CLI tool for testing nanofolks - simple chat interface.
// Usage: swift run nanofolks-cli --team pirate_crew --api-key YOUR_KEY

import Core
import FleetKit
import BotKit
import ProviderKit
import IdentityKit
import Foundation

@main
struct NanofolksCLI {
    static func main() async throws {
        print("🏴‍☠️  nanofolks CLI")
        print("==================\n")
        
        // Parse arguments
        let args = CommandLine.arguments
        let teamName = parseArgument(args, key: "--team") ?? "pirate_crew"
        let apiKey = parseArgument(args, key: "--api-key") ?? ""
        
        // Validate API key
        guard !apiKey.isEmpty else {
            print("❌ Error: OpenAI API key required")
            print("Usage: swift run nanofolks-cli --team <team> --api-key <key>")
            print("")
            print("Example:")
            print("  swift run nanofolks-cli --team pirate_crew --api-key sk-...")
            return
        }
        
        // Setup paths
        let currentDir = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        let teamsDir = currentDir.appendingPathComponent("Teams")
        let rolesDir = currentDir.appendingPathComponent("Roles")
        let workspaceDir = currentDir.appendingPathComponent("Workspace")
        
        // Check if teams directory exists
        guard FileManager.default.fileExists(atPath: teamsDir.path) else {
            print("❌ Error: Teams directory not found at \(teamsDir.path)")
            print("Make sure you're running from the nanofolks-swift directory")
            return
        }
        
        // Initialize components
        print("📁 Loading team: \(teamName)...")
        
        let teamManager = TeamManager(
            teamsDirectory: teamsDir,
            rolesDirectory: rolesDir,
            workspaceDirectory: workspaceDir
        )
        
        // Select team
        do {
            try await teamManager.selectTeam(teamName)
        } catch {
            print("❌ Error: Could not load team '\(teamName)': \(error)")
            return
        }
        
        // Get team profile
        let teamProfile = TeamProfile(
            name: teamName,
            displayName: teamName.replacingOccurrences(of: "_", with: " ").capitalized,
            description: "",
            theme: "",
            emoji: "🏴‍☠️",
            botProfiles: [:]
        )
        
        print("✅ Team loaded: \(teamProfile.displayName)")
        print("")
        
        // Initialize provider
        print("🔌 Connecting to OpenAI...")
        let provider = OpenAIProvider(apiKey: apiKey)
        
        let isAvailable = await provider.isAvailable()
        guard isAvailable else {
            print("❌ Error: Could not connect to OpenAI API")
            print("Check your API key and internet connection")
            return
        }
        print("✅ Connected to OpenAI")
        print("")
        
        // Initialize bot loader and factory
        let botLoader = BotLoader(
            teamsDirectory: teamsDir,
            rolesDirectory: rolesDir,
            workspaceDirectory: workspaceDir
        )
        
        let botFactory = FileBotFactory(
            loader: botLoader,
            provider: provider
        )
        
        // Initialize FleetManager with stub room manager
        let roomManager = StubRoomManager()
        let fleetManager = FleetManager(
            botFactory: botFactory,
            provider: provider,
            team: teamProfile,
            roomManager: roomManager
        )
        
        // Load bots
        print("🤖 Loading bots...")
        do {
            try await fleetManager.loadBots()
            let bots = await fleetManager.getAllBots()
            print("✅ Loaded \(bots.count) bots:")
            for bot in bots {
                print("   • \(bot.config.displayName) (\(bot.config.icon))")
            }
        } catch {
            print("⚠️  Warning: Could not load all bots: \(error)")
            print("   Some bots may be missing their configuration files")
        }
        print("")
        
        // Get leader bot greeting
        if let leaderBot = await fleetManager.getBot(role: .leader) {
            print("\(leaderBot.config.icon) \(leaderBot.config.displayName): Ahoy matey! I'm \(leaderBot.config.displayName), your \(leaderBot.config.description)")
        }
        print("")
        print("Type your message and press Enter. Type 'exit' or 'quit' to stop.")
        print("Use @botname to mention specific bots (e.g., @navigator, @coder)")
        print("")
        
        // Chat loop
        var messageCount = 0
        let roomId = "cli-session-\(UUID().uuidString)"
        
        while true {
            print("> ", terminator: "")
            
            guard let input = readLine()?.trimmingCharacters(in: .whitespaces) else {
                continue
            }
            
            // Check for exit commands
            if input.lowercased() == "exit" || input.lowercased() == "quit" {
                print("\n👋 Fair winds! See you soon.")
                break
            }
            
            // Skip empty input
            if input.isEmpty {
                continue
            }
            
            // Create message
            let message = Message(role: .user, content: input)
            messageCount += 1
            
            // Process through FleetManager
            print("🤔 Thinking...")
            
            do {
                let responses = try await fleetManager.process(message: message, in: roomId)
                
                if responses.isEmpty {
                    print("🤖 [No response]")
                } else {
                    for response in responses {
                        print("\(response.botName): \(response.content)")
                    }
                }
                
            } catch {
                print("❌ Error: \(error.localizedDescription)")
            }
            
            print("")
        }
    }
    
    // MARK: - Helpers
    
    static func parseArgument(_ args: [String], key: String) -> String? {
        guard let index = args.firstIndex(of: key), index + 1 < args.count else {
            return nil
        }
        return args[index + 1]
    }
}

// MARK: - Stub Room Manager

actor StubRoomManager: RoomManager {
    private var rooms: [String: Room] = [:]
    private var histories: [String: [Message]] = [:]
    
    func createRoom(name: String, context: String?, channel: Channel) async throws -> Room {
        let room = Room(name: name, context: context)
        rooms[room.id] = room
        histories[room.id] = []
        return room
    }
    
    func getRoom(roomId: String) async throws -> Room? {
        return rooms[roomId]
    }
    
    func getAllRooms() async throws -> [Room] {
        return Array(rooms.values)
    }
    
    func updateRoomContext(roomId: String, context: String) async throws {
        if var room = rooms[roomId] {
            rooms[roomId] = Room(
                id: room.id,
                name: room.name,
                context: context,
                participants: room.participants
            )
        }
    }
    
    func archiveRoom(roomId: String) async throws {
        rooms.removeValue(forKey: roomId)
        histories.removeValue(forKey: roomId)
    }
    
    func getHistory(roomId: String, limit: Int) async throws -> [Message] {
        return histories[roomId]?.suffix(limit) ?? []
    }
    
    func addMessage(roomId: String, message: Message) async throws {
        histories[roomId, default: []].append(message)
    }
}