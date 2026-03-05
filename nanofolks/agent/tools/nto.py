"""
Nanofolks Token Optimizer (NTO)

A native Python token optimization system for nanofolks tools that reduces
LLM token consumption by 60-85% through intelligent filtering and compression.

Inspired by RTK (Rust Token Killer) patterns, adapted for nanofolks-specific tools.
"""

import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class FilterLevel(str, Enum):
    """Token optimization level."""

    NONE = "none"
    """Keep everything, no compression."""

    MINIMAL = "minimal"
    """Light compression - truncate text, limit results, strip verbose metadata."""

    AGGRESSIVE = "aggressive"
    """Heavy compression - aggressive truncation, minimal results, strip all metadata."""


@dataclass
class TokenStats:
    """Token savings statistics for a single operation."""

    original_tokens: int
    """Original token count before compression."""

    compressed_tokens: int
    """Compressed token count after optimization."""

    savings_percent: float
    """Percentage of tokens saved."""

    operation: str
    """Operation name (e.g., 'compress_web_results')."""

    timestamp: str
    """ISO format timestamp of the operation."""

    @property
    def tokens_saved(self) -> int:
        """Number of tokens saved."""
        return self.original_tokens - self.compressed_tokens


@dataclass
class NTOConfig:
    """NTO configuration settings."""

    enabled: bool = True
    """Enable NTO token optimization."""

    default_level: FilterLevel = FilterLevel.MINIMAL
    """Default compression level."""

    track_savings: bool = True
    """Track token savings statistics."""

    # Web tool settings
    web_max_results: int = 10
    """Maximum web search results to return."""

    web_max_snippet_length: int = 200
    """Maximum snippet length in characters."""

    web_max_page_length: int = 1000
    """Maximum web page content length."""

    # Bot tool settings
    bot_max_response_tokens: int = 500
    """Maximum bot response tokens."""

    # Memory tool settings
    memory_top_k: int = 5
    """Top K memory results to return."""

    memory_max_content_length: int = 300
    """Maximum memory content length."""

    # Session tool settings
    session_max_messages: int = 10
    """Maximum session messages to return."""

    session_max_message_length: int = 200
    """Maximum message content length."""

    # Log settings
    log_max_unique_errors: int = 10
    """Maximum unique errors to show."""

    log_max_unique_warnings: int = 5
    """Maximum unique warnings to show."""


class NanofolksTokenOptimizer:
    """
    RTK-inspired token optimizer for nanofolks tools.

    Applies proven filtering patterns from RTK to nanofolks-specific data structures:
    - Web API responses
    - Bot conversation messages
    - Memory search results
    - Session history
    - Log files
    """

    def __init__(self, config: Optional[NTOConfig] = None):
        """
        Initialize NTO.

        Args:
            config: NTO configuration. Uses defaults if None.
        """
        self.config = config or NTOConfig()
        self._stats: List[TokenStats] = []

        # RTK-inspired regex patterns for normalization
        self.timestamp_re = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}[.,]?\d*\s*")
        self.uuid_re = re.compile(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        )
        self.url_re = re.compile(r"https?://[^\s]+")

    # ========================================
    # Web Tool Compression
    # ========================================

    def compress_web_results(
        self, results: List[Dict[str, Any]], level: Optional[FilterLevel] = None
    ) -> str:
        """
        Compress web search results.

        RTK Pattern: Truncate text fields, limit results, strip verbose metadata.

        Args:
            results: List of web search result dictionaries
            level: Compression level (uses config default if None)

        Returns:
            Compressed JSON string

        Savings: 60-80%
        """
        if not self.config.enabled:
            return json.dumps(results, indent=2)

        level = level or self.config.default_level

        if level == FilterLevel.NONE:
            return json.dumps(results, indent=2)

        # Determine max results based on level
        max_results = (
            self.config.web_max_results
            if level == FilterLevel.MINIMAL
            else min(5, self.config.web_max_results)
        )

        compressed = []
        for result in results[:max_results]:
            item = {
                "title": self._truncate(
                    result.get("title", ""), 100 if level == FilterLevel.AGGRESSIVE else 150
                ),
                "url": result.get("url", ""),
            }

            # Add snippet based on level
            if level == FilterLevel.MINIMAL:
                item["snippet"] = self._truncate(
                    result.get("snippet", ""), self.config.web_max_snippet_length
                )
            elif level == FilterLevel.AGGRESSIVE:
                item["snippet"] = self._truncate(
                    result.get("snippet", ""), min(100, self.config.web_max_snippet_length)
                )

            compressed.append(item)

        output = json.dumps(compressed, indent=2)
        self._track_savings(json.dumps(results), output, "compress_web_results")
        return output

    def compress_web_page(self, content: str, level: Optional[FilterLevel] = None) -> str:
        """
        Compress scraped web page content.

        RTK Pattern: Strip HTML tags, normalize whitespace, truncate.

        Args:
            content: Raw HTML or text content
            level: Compression level (uses config default if None)

        Returns:
            Compressed text

        Savings: 70-90%
        """
        if not self.config.enabled:
            return content

        level = level or self.config.default_level

        if level == FilterLevel.NONE:
            return content

        # Remove HTML tags (RTK-inspired pattern)
        text = re.sub(r"<[^>]+>", "", content)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        # Truncate based on level
        max_chars = (
            self.config.web_max_page_length
            if level == FilterLevel.MINIMAL
            else min(500, self.config.web_max_page_length)
        )
        truncated = self._truncate(text, max_chars)

        self._track_savings(content, truncated, "compress_web_page")
        return truncated

    # ========================================
    # Bot Response Compression
    # ========================================

    def compress_bot_response(
        self, response: str, max_tokens: Optional[int] = None, level: Optional[FilterLevel] = None
    ) -> str:
        """
        Compress bot response.

        RTK Pattern: Truncate or summarize if too long.

        Args:
            response: Bot response text
            max_tokens: Maximum tokens allowed (uses config default if None)
            level: Compression level (uses config default if None)

        Returns:
            Compressed response text

        Savings: 50-70%
        """
        if not self.config.enabled:
            return response

        level = level or self.config.default_level

        if level == FilterLevel.NONE:
            return response

        max_tokens = max_tokens or self.config.bot_max_response_tokens

        # Estimate tokens (RTK's heuristic: ~4 chars per token)
        estimated_tokens = self._estimate_tokens(response)

        if estimated_tokens <= max_tokens:
            return response

        # Truncate with ellipsis
        max_chars = max_tokens * 4
        truncated = self._truncate(response, max_chars)

        self._track_savings(response, truncated, "compress_bot_response")
        return truncated

    # ========================================
    # Memory Result Compression
    # ========================================

    def compress_memory_results(
        self,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        include_metadata: bool = False,
        level: Optional[FilterLevel] = None,
    ) -> str:
        """
        Compress memory search results.

        RTK Pattern: Top-K results, strip metadata, truncate content.

        Args:
            results: List of memory result dictionaries
            top_k: Number of top results to keep (uses config default if None)
            include_metadata: Whether to include metadata
            level: Compression level (uses config default if None)

        Returns:
            Compressed JSON string

        Savings: 70-85%
        """
        if not self.config.enabled:
            return json.dumps(results, indent=2)

        level = level or self.config.default_level

        if level == FilterLevel.NONE:
            return json.dumps(results, indent=2)

        top_k = top_k or self.config.memory_top_k
        max_content_length = (
            self.config.memory_max_content_length
            if level == FilterLevel.MINIMAL
            else min(150, self.config.memory_max_content_length)
        )

        compressed = []
        for result in results[:top_k]:
            item = {
                "content": self._truncate(result.get("content", ""), max_content_length),
                "score": result.get("score", 0),
            }

            # Include minimal metadata only in MINIMAL mode
            if include_metadata and level == FilterLevel.MINIMAL:
                if "timestamp" in result:
                    item["timestamp"] = result["timestamp"]

            compressed.append(item)

        output = json.dumps(compressed, indent=2)
        self._track_savings(json.dumps(results), output, "compress_memory_results")
        return output

    # ========================================
    # Session History Compression
    # ========================================

    def compress_session_history(
        self,
        history: List[Dict[str, Any]],
        max_messages: Optional[int] = None,
        include_system: bool = False,
        level: Optional[FilterLevel] = None,
    ) -> str:
        """
        Compress session history.

        RTK Pattern: Keep recent messages, filter system messages, truncate content.

        Args:
            history: List of message dictionaries
            max_messages: Maximum messages to keep (uses config default if None)
            include_system: Whether to include system messages
            level: Compression level (uses config default if None)

        Returns:
            Compressed JSON string

        Savings: 60-80%
        """
        if not self.config.enabled:
            return json.dumps(history, indent=2)

        level = level or self.config.default_level

        if level == FilterLevel.NONE:
            return json.dumps(history, indent=2)

        max_messages = max_messages or self.config.session_max_messages
        max_message_length = (
            self.config.session_max_message_length
            if level == FilterLevel.MINIMAL
            else min(100, self.config.session_max_message_length)
        )

        # Filter system messages if needed
        filtered = [msg for msg in history if include_system or msg.get("role") != "system"]

        # Keep last N messages
        recent = filtered[-max_messages:]

        # Truncate message content
        compressed = []
        for msg in recent:
            item = {
                "role": msg.get("role"),
                "content": self._truncate(msg.get("content", ""), max_message_length),
            }
            compressed.append(item)

        output = json.dumps(compressed, indent=2)
        self._track_savings(json.dumps(history), output, "compress_session_history")
        return output

    # ========================================
    # JSON Schema Extraction
    # ========================================

    def extract_json_schema(self, data: Dict[str, Any], max_depth: int = 3) -> str:
        """
        Extract JSON schema without values.

        RTK Pattern: Show structure and types only.

        Args:
            data: Dictionary to extract schema from
            max_depth: Maximum depth to traverse

        Returns:
            Schema representation as string

        Savings: 80-95%
        """
        if not self.config.enabled:
            return json.dumps(data, indent=2)

        schema = self._extract_schema(data, depth=0, max_depth=max_depth)
        original_json = json.dumps(data, indent=2)
        self._track_savings(original_json, schema, "extract_json_schema")
        return schema

    def _extract_schema(self, value: Any, depth: int, max_depth: int) -> str:
        """RTK's schema extraction logic adapted for Python."""
        indent = "  " * depth

        if depth > max_depth:
            return f"{indent}..."

        if value is None:
            return f"{indent}null"
        elif isinstance(value, bool):
            return f"{indent}bool"
        elif isinstance(value, int):
            return f"{indent}int"
        elif isinstance(value, float):
            return f"{indent}float"
        elif isinstance(value, str):
            if len(value) > 50:
                return f"{indent}string[{len(value)}]"
            elif value.startswith("http"):
                return f"{indent}url"
            else:
                return f"{indent}string"
        elif isinstance(value, list):
            if not value:
                return f"{indent}[]"
            else:
                first_schema = self._extract_schema(value[0], depth + 1, max_depth)
                if len(value) == 1:
                    return f"{indent}[\n{first_schema}\n{indent}]"
                else:
                    return f"{indent}[{first_schema.strip()}] ({len(value)})"
        elif isinstance(value, dict):
            if not value:
                return f"{indent}{{}}"
            else:
                lines = [f"{indent}{{"]
                keys = sorted(value.keys())

                # RTK limits to 15 keys
                for i, key in enumerate(keys[:15]):
                    val = value[key]
                    val_schema = self._extract_schema(val, depth + 1, max_depth)

                    # Inline simple types
                    if isinstance(val, (type(None), bool, int, float, str)):
                        lines.append(f"{indent}  {key}: {val_schema.strip()}")
                    else:
                        lines.append(f"{indent}  {key}:")
                        lines.append(val_schema)

                if len(keys) > 15:
                    lines.append(f"{indent}  ... +{len(keys) - 15} more keys")

                lines.append(f"{indent}}}")
                return "\n".join(lines)

        return f"{indent}unknown"

    # ========================================
    # Log Deduplication
    # ========================================

    def deduplicate_logs(self, logs: str, max_unique: Optional[int] = None) -> str:
        """
        Deduplicate and summarize logs.

        RTK Pattern: Normalize, count occurrences, show top errors/warnings.

        Args:
            logs: Log content as string
            max_unique: Maximum unique errors to show (uses config default if None)

        Returns:
            Summarized log output

        Savings: 70-85%
        """
        if not self.config.enabled:
            return logs

        max_unique = max_unique or self.config.log_max_unique_errors

        error_counts: Dict[str, int] = {}
        warn_counts: Dict[str, int] = {}
        unique_errors: List[str] = []
        unique_warnings: List[str] = []

        for line in logs.split("\n"):
            line_lower = line.lower()

            # Normalize for deduplication (RTK pattern)
            normalized = self._normalize_log_line(line)

            # Categorize
            if "error" in line_lower or "fatal" in line_lower or "panic" in line_lower:
                if normalized not in error_counts:
                    unique_errors.append(line)
                error_counts[normalized] = error_counts.get(normalized, 0) + 1
            elif "warn" in line_lower:
                if normalized not in warn_counts:
                    unique_warnings.append(line)
                warn_counts[normalized] = warn_counts.get(normalized, 0) + 1

        # Build summary (RTK format)
        result = []
        result.append("📊 Log Summary")
        result.append(f"   ❌ {sum(error_counts.values())} errors ({len(error_counts)} unique)")
        result.append(f"   ⚠️  {sum(warn_counts.values())} warnings ({len(warn_counts)} unique)")
        result.append("")

        # Top errors with counts
        if unique_errors:
            result.append("❌ ERRORS:")
            sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)

            for i, (normalized, count) in enumerate(sorted_errors[:max_unique]):
                # Find original message
                original = unique_errors[
                    [self._normalize_log_line(e) for e in unique_errors].index(normalized)
                ]
                truncated = self._truncate(original, 100)

                if count > 1:
                    result.append(f"   [×{count}] {truncated}")
                else:
                    result.append(f"   {truncated}")

            if len(sorted_errors) > max_unique:
                result.append(f"   ... +{len(sorted_errors) - max_unique} more unique errors")
            result.append("")

        # Top warnings with counts
        if unique_warnings:
            result.append("⚠️  WARNINGS:")
            sorted_warnings = sorted(warn_counts.items(), key=lambda x: x[1], reverse=True)

            for i, (normalized, count) in enumerate(
                sorted_warnings[: self.config.log_max_unique_warnings]
            ):
                original = unique_warnings[
                    [self._normalize_log_line(w) for w in unique_warnings].index(normalized)
                ]
                truncated = self._truncate(original, 100)

                if count > 1:
                    result.append(f"   [×{count}] {truncated}")
                else:
                    result.append(f"   {truncated}")

            if len(sorted_warnings) > self.config.log_max_unique_warnings:
                result.append(
                    f"   ... +{len(sorted_warnings) - self.config.log_max_unique_warnings} more unique warnings"
                )

        output = "\n".join(result)
        self._track_savings(logs, output, "deduplicate_logs")
        return output

    # ========================================
    # Helper Methods
    # ========================================

    def _truncate(self, text: str, max_chars: int) -> str:
        """
        RTK's truncation pattern with ellipsis.

        Args:
            text: Text to truncate
            max_chars: Maximum characters

        Returns:
            Truncated text with "..." if needed
        """
        if text is None:
            return ""

        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."

    def _normalize_log_line(self, line: str) -> str:
        """
        RTK's log normalization pattern.

        Replaces variable parts (timestamps, UUIDs, etc.) with placeholders
        for deduplication.

        Args:
            line: Log line to normalize

        Returns:
            Normalized log line
        """
        normalized = self.timestamp_re.sub("", line)
        normalized = self.uuid_re.sub("<UUID>", normalized)
        normalized = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", normalized)
        normalized = re.sub(r"\b\d{4,}\b", "<NUM>", normalized)
        normalized = re.sub(r"/[\w./\-]+", "<PATH>", normalized)
        return normalized.strip()

    def _estimate_tokens(self, text: str) -> int:
        """
        RTK's token estimation heuristic (~4 chars per token).

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return int(len(text) / 4)

    def _track_savings(self, original: str, compressed: str, operation: str):
        """
        Track token savings (RTK's tracking pattern).

        Args:
            original: Original content
            compressed: Compressed content
            operation: Operation name
        """
        if not self.config.track_savings:
            return

        original_tokens = self._estimate_tokens(original)
        compressed_tokens = self._estimate_tokens(compressed)

        if original_tokens > 0:
            savings = TokenStats(
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                savings_percent=(((original_tokens - compressed_tokens) / original_tokens) * 100),
                operation=operation,
                timestamp=datetime.now().isoformat(),
            )
            self._stats.append(savings)

    # ========================================
    # Statistics Methods
    # ========================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cumulative token savings statistics.

        Returns:
            Dictionary with statistics including total savings, averages, and breakdowns
        """
        if not self._stats:
            return {
                "total_original_tokens": 0,
                "total_compressed_tokens": 0,
                "total_saved": 0,
                "average_savings_percent": 0.0,
                "operations": 0,
                "by_operation": {},
            }

        total_original = sum(s.original_tokens for s in self._stats)
        total_compressed = sum(s.compressed_tokens for s in self._stats)
        total_saved = total_original - total_compressed
        avg_savings = sum(s.savings_percent for s in self._stats) / len(self._stats)

        return {
            "total_original_tokens": total_original,
            "total_compressed_tokens": total_compressed,
            "total_saved": total_saved,
            "average_savings_percent": avg_savings,
            "operations": len(self._stats),
            "by_operation": self._get_stats_by_operation(),
        }

    def _get_stats_by_operation(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics grouped by operation type."""
        by_op: Dict[str, List[TokenStats]] = {}

        for stat in self._stats:
            if stat.operation not in by_op:
                by_op[stat.operation] = []
            by_op[stat.operation].append(stat)

        result = {}
        for op, stats in by_op.items():
            total_original = sum(s.original_tokens for s in stats)
            total_compressed = sum(s.compressed_tokens for s in stats)
            avg_savings = sum(s.savings_percent for s in stats) / len(stats)

            result[op] = {
                "count": len(stats),
                "total_original_tokens": total_original,
                "total_compressed_tokens": total_compressed,
                "total_saved": total_original - total_compressed,
                "average_savings_percent": avg_savings,
            }

        return result

    def reset_stats(self):
        """Reset all statistics."""
        self._stats.clear()


# ========================================
# Factory Function
# ========================================


def create_nto_wrapper(config: Optional[NTOConfig] = None) -> NanofolksTokenOptimizer:
    """
    Create NTO wrapper for integration with nanofolks tools.

    Args:
        config: NTO configuration. Uses defaults if None.

    Returns:
        Configured NanofolksTokenOptimizer instance

    Usage:
        nto = create_nto_wrapper()

        # In WebSearchTool
        results = await self._search(query)
        return nto.compress_web_results(results)

        # In BotInvokeTool
        response = await self._invoke_bot(bot_role, message)
        return nto.compress_bot_response(response)
    """
    return NanofolksTokenOptimizer(config)
