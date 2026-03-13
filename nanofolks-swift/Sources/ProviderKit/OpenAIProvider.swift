// OpenAIProvider.swift
// OpenAI LLM provider implementation.

import Foundation
import Core

// MARK: - OpenAI Provider

/// OpenAI API provider.
@available(macOS 14, *)
public actor OpenAIProvider: @preconcurrency LLMProvider {
    public let name = "openai"
    public let models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    
    private let apiKey: String
    private let baseUrl: String
    private let session: URLSession
    
    public init(apiKey: String, baseUrl: String = "https://api.openai.com/v1") {
        self.apiKey = apiKey
        self.baseUrl = baseUrl
        self.session = URLSession.shared
    }
    
    public func chat(request: LLMRequest) async throws -> LLMResponse {
        var urlRequest = URLRequest(url: URL(string: "\(baseUrl)/chat/completions")!)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = try buildRequestBody(request)
        urlRequest.httpBody = body
        
        let (data, httpResponse) = try await session.data(for: urlRequest)
        try validateHTTPResponse(httpResponse, data: data)
        let response = try JSONDecoder().decode(OpenAIResponse.self, from: data)
        
        return LLMResponse(
            id: response.id,
            content: response.choices.first?.message.content ?? "",
            model: response.model,
            usage: TokenUsage(
                promptTokens: response.usage?.prompt_tokens ?? 0,
                completionTokens: response.usage?.completion_tokens ?? 0,
                totalTokens: response.usage?.total_tokens ?? 0
            )
        )
    }
    
    public func chatStream(request: LLMRequest) -> AsyncThrowingStream<LLMStreamChunk, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    // Runtime fallback: perform a normal completion and emit as a single chunk.
                    // This avoids silently succeeding with no streamed content.
                    let response = try await chat(request: request)
                    continuation.yield(
                        LLMStreamChunk(
                            id: response.id,
                            delta: response.content,
                            isComplete: true,
                            toolCalls: response.toolCalls
                        )
                    )
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }
    
    public func embed(text: [String]) async throws -> [[Float]] {
        var urlRequest = URLRequest(url: URL(string: "\(baseUrl)/embeddings")!)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = try JSONSerialization.data(withJSONObject: [
            "input": text,
            "model": "text-embedding-ada-002"
        ])
        urlRequest.httpBody = body
        
        let (data, httpResponse) = try await session.data(for: urlRequest)
        try validateHTTPResponse(httpResponse, data: data)
        let response = try JSONDecoder().decode(OpenAIEmbeddingResponse.self, from: data)
        
        return response.data.map { $0.embedding }
    }
    
    public func isAvailable() async -> Bool {
        do {
            let url = URL(string: "\(baseUrl)/models")!
            var request = URLRequest(url: url)
            request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
            let (_, response) = try await session.data(for: request)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }
    
    public func estimateTokens(for messages: [Message]) -> Int {
        // Rough estimate: ~4 characters per token
        return messages.reduce(0) { $0 + $1.content.count / 4 }
    }
    
    private func buildRequestBody(_ request: LLMRequest, stream: Bool = false) throws -> Data {
        var body: [String: Any] = [
            "model": request.model ?? "gpt-4",
            "messages": request.messages.map { ["role": $0.role.rawValue, "content": $0.content] }
        ]
        
        if let temperature = request.temperature {
            body["temperature"] = temperature
        }
        
        if let maxTokens = request.maxTokens {
            body["max_tokens"] = maxTokens
        }
        
        if stream {
            body["stream"] = true
        }
        
        if let tools = request.tools {
            body["functions"] = tools.map { [
                "name": $0.name,
                "description": $0.description,
                "parameters": $0.parameters
            ]}
        }
        
        return try JSONSerialization.data(withJSONObject: body)
    }

    private func validateHTTPResponse(_ response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else {
            throw CoreError.providerError("Invalid OpenAI response type")
        }

        guard (200..<300).contains(http.statusCode) else {
            if let openAIError = try? JSONDecoder().decode(OpenAIErrorResponse.self, from: data) {
                throw CoreError.providerError("OpenAI API error (\(http.statusCode)): \(openAIError.error.message)")
            }

            let body = String(data: data, encoding: .utf8) ?? "<non-utf8 body>"
            throw CoreError.providerError("OpenAI API error (\(http.statusCode)): \(body)")
        }
    }
}

// MARK: - OpenAI Response Types

private struct OpenAIResponse: Codable {
    let id: String
    let model: String
    let choices: [OpenAIChoice]
    let usage: OpenAIUsage?
}

private struct OpenAIChoice: Codable {
    let message: OpenAIMessage
    let finish_reason: String?
}

private struct OpenAIMessage: Codable {
    let role: String
    let content: String
}

private struct OpenAIUsage: Codable {
    let prompt_tokens: Int
    let completion_tokens: Int
    let total_tokens: Int
}

private struct OpenAIEmbeddingResponse: Codable {
    let data: [OpenAIEmbedding]
}

private struct OpenAIEmbedding: Codable {
    let embedding: [Float]
}

private struct OpenAIErrorResponse: Codable {
    let error: OpenAIError
}

private struct OpenAIError: Codable {
    let message: String
    let type: String?
    let code: String?
}
