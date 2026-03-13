// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "nanofolks",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .library(
            name: "Core",
            targets: ["Core"]
        ),
        .library(
            name: "PromptKit",
            targets: ["PromptKit"]
        ),
        .library(
            name: "MemoryKit",
            targets: ["MemoryKit"]
        ),
        .library(
            name: "ProviderKit",
            targets: ["ProviderKit"]
        ),
        .library(
            name: "SystemKit",
            targets: ["SystemKit"]
        ),
        .library(
            name: "SecurityKit",
            targets: ["SecurityKit"]
        ),
        .library(
            name: "ChannelKit",
            targets: ["ChannelKit"]
        ),
        .library(
            name: "EverydayKit",
            targets: ["EverydayKit"]
        ),
        .library(
            name: "IdentityKit",
            targets: ["IdentityKit"]
        ),
        .library(
            name: "RoutineKit",
            targets: ["RoutineKit"]
        ),
        .library(
            name: "ToolKit",
            targets: ["ToolKit"]
        ),
        .library(
            name: "BotKit",
            targets: ["BotKit"]
        ),
        .library(
            name: "FleetKit",
            targets: ["FleetKit"]
        ),
        .library(
            name: "OnboardingKit",
            targets: ["OnboardingKit"]
        ),
        .library(
            name: "FleetKit",
            targets: ["FleetKit"]
        ),
        .executable(
            name: "nanofolks-cli",
            targets: ["NanofolksCLI"]
        ),
    ],
    dependencies: [
        // Future: Add dependencies here (e.g., SQLite, Networking)
    ],
    targets: [
        //══════════════════════════════════════════════════════════════════════
        // CORE - No dependencies (foundation protocols)
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "Core",
            dependencies: [],
            path: "Sources/Core"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // PROMPTKIT - Depends: Core
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "PromptKit",
            dependencies: ["Core"],
            path: "Sources/PromptKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // MEMORYKIT - Depends: Core
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "MemoryKit",
            dependencies: ["Core"],
            path: "Sources/MemoryKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // PROVIDERKIT - Depends: Core, PromptKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "ProviderKit",
            dependencies: ["Core", "PromptKit"],
            path: "Sources/ProviderKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // SYSTEMKIT - Standalone (macOS integration)
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "SystemKit",
            dependencies: [],
            path: "Sources/SystemKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // SECURITYKIT - Standalone (security utilities)
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "SecurityKit",
            dependencies: [],
            path: "Sources/SecurityKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // CHANNELKIT - Depends: Core, PromptKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "ChannelKit",
            dependencies: ["Core", "PromptKit"],
            path: "Sources/ChannelKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // EVERYDAYKIT - NEW: Everyday life tools - Depends: Core, PromptKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "EverydayKit",
            dependencies: ["Core", "PromptKit"],
            path: "Sources/EverydayKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // IDENTITYKIT - Depends: Core, PromptKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "IdentityKit",
            dependencies: ["Core", "PromptKit"],
            path: "Sources/IdentityKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // PRIVACYKIT - NEW: User-facing privacy - Depends: Core, PromptKit, SecurityKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "PrivacyKit",
            dependencies: ["Core", "PromptKit", "SecurityKit"],
            path: "Sources/PrivacyKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // ROUTINEKIT - Depends: Core, PromptKit, MemoryKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "RoutineKit",
            dependencies: ["Core", "PromptKit", "MemoryKit"],
            path: "Sources/RoutineKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // TOOLKIT - EXTERNAL INTEGRATIONS - Depends: Core, PromptKit, MemoryKit, SystemKit, EverydayKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "ToolKit",
            dependencies: ["Core", "PromptKit", "MemoryKit", "SystemKit", "EverydayKit"],
            path: "Sources/ToolKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // BOTKIT - Depends: Core, PromptKit, MemoryKit, ToolKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "BotKit",
            dependencies: ["Core", "PromptKit", "MemoryKit", "ToolKit"],
            path: "Sources/BotKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // ONBOARDINGKIT - NEW: First-time UX - Depends: Core, PromptKit, IdentityKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "OnboardingKit",
            dependencies: ["Core", "PromptKit", "IdentityKit"],
            path: "Sources/OnboardingKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // FLEETKIT - ORCHESTRATION - Depends: Core, PromptKit, BotKit, ProviderKit
        //══════════════════════════════════════════════════════════════════════
        
        .target(
            name: "FleetKit",
            dependencies: ["Core", "PromptKit", "BotKit", "ProviderKit"],
            path: "Sources/FleetKit"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // TESTS
        //══════════════════════════════════════════════════════════════════════
        
        .testTarget(
            name: "CoreTests",
            dependencies: ["Core"],
            path: "Tests/CoreTests"
        ),
        .testTarget(
            name: "PromptKitTests",
            dependencies: ["PromptKit"],
            path: "Tests/PromptKitTests"
        ),
        .testTarget(
            name: "MemoryKitTests",
            dependencies: ["MemoryKit"],
            path: "Tests/MemoryKitTests"
        ),
        .testTarget(
            name: "ProviderKitTests",
            dependencies: ["ProviderKit"],
            path: "Tests/ProviderKitTests"
        ),
        .testTarget(
            name: "SystemKitTests",
            dependencies: ["SystemKit"],
            path: "Tests/SystemKitTests"
        ),
        .testTarget(
            name: "SecurityKitTests",
            dependencies: ["SecurityKit"],
            path: "Tests/SecurityKitTests"
        ),
        .testTarget(
            name: "ChannelKitTests",
            dependencies: ["ChannelKit"],
            path: "Tests/ChannelKitTests"
        ),
        .testTarget(
            name: "EverydayKitTests",
            dependencies: ["EverydayKit"],
            path: "Tests/EverydayKitTests"
        ),
        .testTarget(
            name: "IdentityKitTests",
            dependencies: ["IdentityKit"],
            path: "Tests/IdentityKitTests"
        ),
        .testTarget(
            name: "PrivacyKitTests",
            dependencies: ["PrivacyKit"],
            path: "Tests/PrivacyKitTests"
        ),
        .testTarget(
            name: "RoutineKitTests",
            dependencies: ["RoutineKit"],
            path: "Tests/RoutineKitTests"
        ),
        .testTarget(
            name: "ToolKitTests",
            dependencies: ["ToolKit"],
            path: "Tests/ToolKitTests"
        ),
        .testTarget(
            name: "BotKitTests",
            dependencies: ["BotKit"],
            path: "Tests/BotKitTests"
        ),
        .testTarget(
            name: "OnboardingKitTests",
            dependencies: ["OnboardingKit"],
            path: "Tests/OnboardingKitTests"
        ),
        .testTarget(
            name: "FleetKitTests",
            dependencies: ["FleetKit"],
            path: "Tests/FleetKitTests"
        ),
        
        //══════════════════════════════════════════════════════════════════════
        // CLI EXECUTABLE
        //══════════════════════════════════════════════════════════════════════
        
        .executableTarget(
            name: "NanofolksCLI",
            dependencies: [
                "Core",
                "PromptKit",
                "FleetKit",
                "BotKit",
                "ProviderKit",
                "IdentityKit"
            ],
            path: "Sources/NanofolksCLI"
        ),
    ]
)