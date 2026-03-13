// ToolProtocol.swift
// Tool interface definitions for the nanofolks ecosystem.

import Foundation

// MARK: - Tool Protocol

/// Base protocol for all tools.
public protocol Tool: Sendable {
    /// Tool name used for invocation.
    var name: String { get }
    
    /// Human-readable description.
    var description: String { get }
    
    /// Tool category for organization.
    var category: ToolCategory { get }
    
    /// Whether tool requires user confirmation before execution.
    var requiresConfirmation: Bool { get }
    
    /// Whether tool is safe to run automatically.
    var isSafe: Bool { get }
    
    /// Execute the tool with given parameters.
    func execute(parameters: [String: AnyCodable]) async throws -> ToolResult
    
    /// Get parameter schema for LLM function calling.
    func getSchema() -> ToolDefinition
    
    /// Validate parameters before execution.
    func validate(parameters: [String: AnyCodable]) -> Bool
}

// MARK: - Tool Category

/// Category for organizing tools.
public enum ToolCategory: String, Sendable, Codable, CaseIterable {
    case filesystem
    case shell
    case browser
    case everyday      // Calendar, reminders, contacts, etc.
    case communication // Email, messages
    case web
    case data
    case security
    case system
    case mcp           // Model Context Protocol
    case health
    case photos
    case maps
}

// MARK: - Tool Registry Protocol

/// Registry for managing and executing tools.
public protocol ToolRegistry: Sendable {
    /// Register a tool.
    func register(tool: any Tool) throws
    
    /// Unregister a tool.
    func unregister(toolName: String) throws
    
    /// Get all registered tools.
    func getAllTools() -> [any Tool]
    
    /// Get tools by category.
    func getToolsByCategory(_ category: ToolCategory) -> [any Tool]
    
    /// Get tool by name.
    func getTool(name: String) -> (any Tool)?
    
    /// Check if a tool is registered.
    func isRegistered(name: String) -> Bool
    
    /// Execute a tool by name.
    func execute(
        toolName: String,
        parameters: [String: AnyCodable]
    ) async throws -> ToolResult
    
    /// Get all tool schemas for LLM function calling.
    func getAllSchemas() -> [ToolDefinition]
    
    /// Get tool execution history.
    func getExecutionHistory(limit: Int) -> [ToolExecutionRecord]
}

// MARK: - Tool Execution Record

/// Record of a tool execution.
public struct ToolExecutionRecord: Sendable, Codable {
    public let id: String
    public let toolName: String
    public let parameters: [String: AnyCodable]
    public let result: ToolResult
    public let startTime: Date
    public let endTime: Date
    public let duration: TimeInterval
    public let botName: String?
    public let roomId: String?
    
    public init(
        id: String = UUID().uuidString,
        toolName: String,
        parameters: [String: AnyCodable],
        result: ToolResult,
        startTime: Date,
        endTime: Date,
        duration: TimeInterval,
        botName: String? = nil,
        roomId: String? = nil
    ) {
        self.id = id
        self.toolName = toolName
        self.parameters = parameters
        self.result = result
        self.startTime = startTime
        self.endTime = endTime
        self.duration = duration
        self.botName = botName
        self.roomId = roomId
    }
}

// MARK: - Tool Permission Protocol

/// Protocol for managing tool permissions.
public protocol ToolPermissionManager: Sendable {
    /// Check if a bot can use a tool.
    func canUse(botName: String, toolName: String) -> Bool
    
    /// Grant tool permission to a bot.
    func grantPermission(botName: String, toolName: String) throws
    
    /// Revoke tool permission from a bot.
    func revokePermission(botName: String, toolName: String) throws
    
    /// Get all tools a bot can use.
    func getAllowedTools(botName: String) -> [String]
    
    /// Get all bots that can use a tool.
    func getAllowedBots(toolName: String) -> [String]
}

// MARK: - Everyday Tool Protocols

/// Protocol for calendar integration.
public protocol CalendarTool: Tool {
    /// Create an event.
    func createEvent(
        title: String,
        startDate: Date,
        endDate: Date,
        notes: String?,
        location: String?
    ) async throws -> CalendarEvent
    
    /// Get events for a date range.
    func getEvents(from: Date, to: Date) async throws -> [CalendarEvent]
    
    /// Update an event.
    func updateEvent(eventId: String, changes: [String: AnyCodable]) async throws -> CalendarEvent
    
    /// Delete an event.
    func deleteEvent(eventId: String) async throws
}

/// Protocol for reminders integration.
public protocol RemindersTool: Tool {
    /// Create a reminder.
    func createReminder(
        title: String,
        dueDate: Date?,
        notes: String?,
        listName: String?
    ) async throws -> Reminder
    
    /// Get reminders.
    func getReminders(includeCompleted: Bool) async throws -> [Reminder]
    
    /// Complete a reminder.
    func completeReminder(reminderId: String) async throws
    
    /// Delete a reminder.
    func deleteReminder(reminderId: String) async throws
}

/// Protocol for contacts integration.
public protocol ContactsTool: Tool {
    /// Search for contacts.
    func search(query: String) async throws -> [Contact]
    
    /// Get contact by ID.
    func getContact(contactId: String) async throws -> Contact?
    
    /// Create a contact.
    func createContact(
        firstName: String,
        lastName: String?,
        email: String?,
        phone: String?
    ) async throws -> Contact
}

/// Protocol for weather integration.
public protocol WeatherTool: Tool {
    /// Get current weather for a location.
    func getCurrentWeather(location: String) async throws -> WeatherInfo
    
    /// Get weather forecast.
    func getForecast(location: String, days: Int) async throws -> [WeatherForecast]
}

/// Protocol for photos integration.
public protocol PhotosTool: Tool {
    /// Search for photos.
    func search(query: String, limit: Int) async throws -> [Photo]
    
    /// Get photo metadata.
    func getMetadata(photoId: String) async throws -> PhotoMetadata?
}

/// Protocol for maps integration.
public protocol MapsTool: Tool {
    /// Search for places.
    func searchPlaces(query: String, near: String?) async throws -> [Place]
    
    /// Get directions.
    func getDirections(from: String, to: String) async throws -> Directions
}

// MARK: - Everyday Tool Types

/// Calendar event.
public struct CalendarEvent: Sendable, Codable {
    public let id: String
    public let title: String
    public let startDate: Date
    public let endDate: Date
    public let notes: String?
    public let location: String?
    public let calendar: String
    
    public init(
        id: String,
        title: String,
        startDate: Date,
        endDate: Date,
        notes: String? = nil,
        location: String? = nil,
        calendar: String = "Default"
    ) {
        self.id = id
        self.title = title
        self.startDate = startDate
        self.endDate = endDate
        self.notes = notes
        self.location = location
        self.calendar = calendar
    }
}

/// Reminder.
public struct Reminder: Sendable, Codable {
    public let id: String
    public let title: String
    public let dueDate: Date?
    public let notes: String?
    public let listName: String
    public let isCompleted: Bool
    
    public init(
        id: String,
        title: String,
        dueDate: Date? = nil,
        notes: String? = nil,
        listName: String = "Reminders",
        isCompleted: Bool = false
    ) {
        self.id = id
        self.title = title
        self.dueDate = dueDate
        self.notes = notes
        self.listName = listName
        self.isCompleted = isCompleted
    }
}

/// Contact.
public struct Contact: Sendable, Codable {
    public let id: String
    public let firstName: String
    public let lastName: String?
    public let email: String?
    public let phone: String?
    public let organization: String?
    
    public init(
        id: String,
        firstName: String,
        lastName: String? = nil,
        email: String? = nil,
        phone: String? = nil,
        organization: String? = nil
    ) {
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.phone = phone
        self.organization = organization
    }
}

/// Weather information.
public struct WeatherInfo: Sendable, Codable {
    public let location: String
    public let temperature: Double
    public let condition: String
    public let humidity: Int
    public let windSpeed: Double
    public let forecast: String?
    
    public init(
        location: String,
        temperature: Double,
        condition: String,
        humidity: Int,
        windSpeed: Double,
        forecast: String? = nil
    ) {
        self.location = location
        self.temperature = temperature
        self.condition = condition
        self.humidity = humidity
        self.windSpeed = windSpeed
        self.forecast = forecast
    }
}

/// Weather forecast.
public struct WeatherForecast: Sendable, Codable {
    public let date: Date
    public let high: Double
    public let low: Double
    public let condition: String
    public let precipitation: Int
    
    public init(date: Date, high: Double, low: Double, condition: String, precipitation: Int) {
        self.date = date
        self.high = high
        self.low = low
        self.condition = condition
        self.precipitation = precipitation
    }
}

/// Photo.
public struct Photo: Sendable, Codable {
    public let id: String
    public let filename: String
    public let creationDate: Date?
    public let width: Int
    public let height: Int
    public let thumbnail: Data?
    
    public init(
        id: String,
        filename: String,
        creationDate: Date?,
        width: Int,
        height: Int,
        thumbnail: Data? = nil
    ) {
        self.id = id
        self.filename = filename
        self.creationDate = creationDate
        self.width = width
        self.height = height
        self.thumbnail = thumbnail
    }
}

/// Photo metadata.
public struct PhotoMetadata: Sendable, Codable {
    public let photoId: String
    public let location: String?
    public let camera: String?
    public let keywords: [String]
    public let people: [String]
    
    public init(
        photoId: String,
        location: String? = nil,
        camera: String? = nil,
        keywords: [String] = [],
        people: [String] = []
    ) {
        self.photoId = photoId
        self.location = location
        self.camera = camera
        self.keywords = keywords
        self.people = people
    }
}

/// Place (for maps).
public struct Place: Sendable, Codable {
    public let id: String
    public let name: String
    public let address: String
    public let coordinate: Coordinate?
    public let category: String?
    
    public init(
        id: String,
        name: String,
        address: String,
        coordinate: Coordinate? = nil,
        category: String? = nil
    ) {
        self.id = id
        self.name = name
        self.address = address
        self.coordinate = coordinate
        self.category = category
    }
}

/// Coordinate.
public struct Coordinate: Sendable, Codable {
    public let latitude: Double
    public let longitude: Double
    
    public init(latitude: Double, longitude: Double) {
        self.latitude = latitude
        self.longitude = longitude
    }
}

/// Directions.
public struct Directions: Sendable, Codable {
    public let steps: [DirectionStep]
    public let totalDistance: Double
    public let totalDuration: TimeInterval
    
    public init(steps: [DirectionStep], totalDistance: Double, totalDuration: TimeInterval) {
        self.steps = steps
        self.totalDistance = totalDistance
        self.totalDuration = totalDuration
    }
}

/// Direction step.
public struct DirectionStep: Sendable, Codable {
    public let instruction: String
    public let distance: Double
    public let duration: TimeInterval
    
    public init(instruction: String, distance: Double, duration: TimeInterval) {
        self.instruction = instruction
        self.distance = distance
        self.duration = duration
    }
}