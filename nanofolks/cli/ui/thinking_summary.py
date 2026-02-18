"""Summary generator for bot thinking/reasoning logs.

This module provides utilities to generate one-line summaries and detailed
breakdowns of bot reasoning steps from work logs.
"""

from typing import List, Optional

from nanofolks.agent.work_log import LogLevel, WorkLog, WorkLogEntry


class ThinkingSummaryBuilder:
    """Generates summaries and detail views from work logs.

    Converts detailed work log entries into user-friendly summaries
    that can be displayed inline in chat. Handles tool execution,
    decisions, and corrections.
    """

    LEVEL_ICONS = {
        LogLevel.DECISION: "🎯",
        LogLevel.TOOL: "🔧",
        LogLevel.CORRECTION: "🔄",
        LogLevel.UNCERTAINTY: "❓",
        LogLevel.WARNING: "⚠️",
        LogLevel.ERROR: "❌",
        LogLevel.THINKING: "🧠",
        LogLevel.INFO: "ℹ️",
        LogLevel.HANDOFF: "🤝",
        LogLevel.COORDINATION: "📋",
    }

    # Order of importance for summary extraction
    PRIORITY_LEVELS = [
        LogLevel.ERROR,
        LogLevel.COORDINATION,
        LogLevel.DECISION,
        LogLevel.TOOL,
        LogLevel.CORRECTION,
        LogLevel.WARNING,
        LogLevel.THINKING,
        LogLevel.INFO,
    ]

    @staticmethod
    def generate_summary(log: WorkLog, max_actions: int = 2) -> str:
        """Generate one-line summary of thinking.

        Args:
            log: The work log to summarize
            max_actions: Maximum number of actions to include

        Returns:
            One-line summary string

        Examples:
            - "Created coordination room, invited 2 bots"
            - "Analyzed requirements, selected medium model"
            - "Executed 3 tools: read_file, edit_file, execute"
        """
        if not log.entries:
            return "No thinking steps recorded"

        # Filter to key entry types
        key_entries = ThinkingSummaryBuilder._filter_key_entries(log)

        if not key_entries:
            return "Processing complete"

        # Extract main actions
        actions = []
        tool_count = 0

        for entry in key_entries[:max_actions * 2]:  # Get more than we need
            if entry.level == LogLevel.TOOL:
                tool_count += 1
                if tool_count == 1:
                    # First tool, include its name
                    actions.append(f"executed {entry.tool_name}()")
                # Count additional tools
            elif entry.level == LogLevel.DECISION:
                # Extract short decision
                summary_text = ThinkingSummaryBuilder._extract_summary_text(entry)
                if summary_text:
                    actions.append(summary_text)
            elif entry.level == LogLevel.CORRECTION:
                actions.append(f"fixed {entry.message[:30]}")
            elif entry.level == LogLevel.COORDINATION:
                summary_text = ThinkingSummaryBuilder._extract_summary_text(entry)
                if summary_text:
                    actions.append(summary_text)

            if len(actions) >= max_actions:
                break

        # Add tool count if we had multiple tools
        if tool_count > 1:
            actions.append(f"{tool_count - 1} more tools")

        if not actions:
            return "Processing complete"

        # Join actions with commas
        summary = ", ".join(actions[:max_actions])
        return summary

    @staticmethod
    def generate_details(log: WorkLog, bot_name: Optional[str] = None) -> List[str]:
        """Generate expanded view lines.

        Args:
            log: The work log to detail
            bot_name: Optional filter to show only specific bot's entries

        Returns:
            List of formatted detail lines ready for display

        Example output:
            - "Step 1 🎯 Decision: Selected model, generated response"
            - "Step 2 🔧 Tool: read_file() → success"
            - "Step 3 ✅ Complete: Analysis ready"
        """
        if not log.entries:
            return ["No thinking steps recorded"]

        lines = []

        # Filter entries if bot_name specified
        entries = log.entries
        if bot_name:
            entries = [e for e in entries if e.bot_name == bot_name]

        if not entries:
            return [f"No thinking steps for bot '{bot_name}'"]

        # Format each entry
        for entry in entries:
            # Build the line with icon and step number
            icon = ThinkingSummaryBuilder.LEVEL_ICONS.get(entry.level, "•")

            # Format based on entry type
            if entry.level == LogLevel.TOOL:
                tool_result = entry.tool_status or "unknown"
                detail = f"Step {entry.step} {icon} Tool: {entry.tool_name}() → {tool_result}"
            elif entry.level == LogLevel.DECISION:
                detail = f"Step {entry.step} {icon} Decision: {entry.message}"
            elif entry.level == LogLevel.CORRECTION:
                detail = f"Step {entry.step} {icon} Correction: {entry.message}"
            elif entry.level == LogLevel.ERROR:
                error_msg = entry.tool_error or entry.message
                detail = f"Step {entry.step} {icon} Error: {error_msg}"
            elif entry.level == LogLevel.COORDINATION:
                detail = f"Step {entry.step} {icon} Coordination: {entry.message}"
            else:
                detail = f"Step {entry.step} {icon} {entry.level.value.title()}: {entry.message}"

            # Add confidence if available
            if entry.confidence is not None:
                confidence_pct = int(entry.confidence * 100)
                detail += f" ({confidence_pct}%)"

            # Add duration if available
            if entry.duration_ms is not None:
                detail += f" [{entry.duration_ms}ms]"

            lines.append(detail)

        return lines

    @staticmethod
    def _filter_key_entries(log: WorkLog) -> List[WorkLogEntry]:
        """Filter work log to only key decision/action entries.

        Args:
            log: The work log to filter

        Returns:
            Filtered list of key entries
        """
        key_levels = {
            LogLevel.DECISION,
            LogLevel.TOOL,
            LogLevel.CORRECTION,
            LogLevel.ERROR,
            LogLevel.COORDINATION,
        }

        return [e for e in log.entries if e.level in key_levels]

    @staticmethod
    def _extract_summary_text(entry: WorkLogEntry) -> Optional[str]:
        """Extract a short summary from an entry.

        Args:
            entry: The work log entry

        Returns:
            Short summary text, or None if nothing to extract
        """
        msg = entry.message

        # Clean up common prefixes
        if msg.startswith("🚨 Escalation: "):
            msg = msg[15:]

        # Truncate to reasonable length
        if len(msg) > 40:
            msg = msg[:37] + "..."

        return msg if msg else None

    @staticmethod
    def get_summary_stats(log: WorkLog) -> dict:
        """Get statistics about the thinking process.

        Args:
            log: The work log to analyze

        Returns:
            Dictionary with stats
        """
        return {
            "total_steps": len(log.entries),
            "decisions": len([e for e in log.entries if e.level == LogLevel.DECISION]),
            "tools": len([e for e in log.entries if e.level == LogLevel.TOOL]),
            "errors": len([e for e in log.entries if e.level == LogLevel.ERROR]),
            "corrections": len([e for e in log.entries if e.level == LogLevel.CORRECTION]),
            "total_duration_ms": sum(e.duration_ms or 0 for e in log.entries),
        }
