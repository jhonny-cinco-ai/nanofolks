"""ResponseCombiner: Combines multiple bot responses into cohesive output.

This module handles formatting and combining responses from multiple bots
when using @all or @team mentions.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from loguru import logger

from nanofolks.bots.dispatch import DispatchTarget
from nanofolks.bus.events import MessageEnvelope


@dataclass
class BotResponse:
    """Response from a single bot."""

    bot_name: str
    content: str
    confidence: float = 0.8
    response_time_ms: int = 0
    metadata: Optional[Dict] = None


class ResponseCombiner:
    """Combines multiple bot responses into cohesive output.

    This class formats responses from multiple bots, adds bot identifiers
    (emoji, color), handles errors gracefully, and maintains response ordering.

    Attributes:
        BOT_EMOJIS: Mapping of bot names to emojis for display
        BOT_COLORS: Mapping of bot names to colors for CLI display
    """

    # Bot emoji mapping for display
    BOT_EMOJIS = {
        "leader": "👑",
        "researcher": "📊",
        "coder": "💻",
        "social": "📱",
        "creative": "🎨",
        "auditor": "🔍",
    }

    # Bot color mapping for CLI
    BOT_COLORS = {
        "leader": "blue",
        "researcher": "cyan",
        "coder": "green",
        "social": "magenta",
        "creative": "yellow",
        "auditor": "red",
    }

    def __init__(self):
        """Initialize the ResponseCombiner."""
        self.logger = logger.bind(component="ResponseCombiner")

    def combine(
        self, responses: List[MessageEnvelope], mode: DispatchTarget, include_header: bool = True
    ) -> MessageEnvelope:
        """Combine multiple bot responses into a single MessageEnvelope.

        Args:
            responses: List of bot responses (may contain exceptions)
            mode: The dispatch mode that triggered these responses
            include_header: Whether to include a header line

        Returns:
            A single MessageEnvelope with combined content
        """
        # Filter out errors and invalid responses
        valid_responses = []
        error_count = 0

        for response in responses:
            if isinstance(response, Exception):
                error_count += 1
                self.logger.warning(f"Bot response failed: {response}")
            elif response and response.content:
                valid_responses.append(response)
            else:
                error_count += 1
                self.logger.warning(f"Empty response received")

        if not valid_responses:
            # All bots failed
            self.logger.error(f"All {len(responses)} bots failed to respond")
            return MessageEnvelope(
                content="❌ All bots failed to respond. Please try again.",
                bot_name="system",
                metadata={"error": "all_bots_failed", "error_count": error_count},
            )

        # Format based on mode
        if mode == DispatchTarget.MULTI_BOT:
            return self._format_group_response(valid_responses, include_header)
        elif mode == DispatchTarget.TEAM_CONTEXT:
            return self._format_context_response(valid_responses, include_header)
        elif mode == DispatchTarget.SMART_DISCUSS:
            return self._format_smart_discuss_response(valid_responses, include_header)
        elif len(valid_responses) == 1:
            # Single response - return as-is
            return valid_responses[0]
        else:
            # Multiple responses but no specific mode - use group format
            return self._format_group_response(valid_responses, include_header)

    def _format_group_response(
        self, responses: List[MessageEnvelope], include_header: bool = True
    ) -> MessageEnvelope:
        """Format @all style multi-bot response.

        Args:
            responses: List of valid bot responses
            include_header: Whether to include a header line

        Returns:
            Formatted MessageEnvelope
        """
        parts = []

        if include_header:
            parts.append("🎭 **Multi-Bot Response**")
            parts.append("")

        # Sort responses by bot name for consistency
        sorted_responses = sorted(responses, key=lambda r: r.bot_name)

        for response in sorted_responses:
            emoji = self.BOT_EMOJIS.get(response.bot_name, "🤖")
            parts.append(f"{emoji} **@{response.bot_name}:**")
            parts.append(response.content)
            parts.append("")

        # Gather metadata
        responding_bots = [r.bot_name for r in responses]

        return MessageEnvelope(
            content="\n".join(parts).strip(),
            bot_name="multi",
            metadata={
                "multi_bot": True,
                "responding_bots": responding_bots,
                "bot_count": len(responses),
                "mode": DispatchTarget.MULTI_BOT.value,
            },
        )

    def _format_context_response(
        self, responses: List[MessageEnvelope], include_header: bool = True
    ) -> MessageEnvelope:
        """Format @team style context-aware response.

        Args:
            responses: List of valid bot responses
            include_header: Whether to include a header line

        Returns:
            Formatted MessageEnvelope
        """
        parts = []

        if include_header:
            parts.append("👥 **Team Response**")
            parts.append("")

        # Sort responses by bot name
        sorted_responses = sorted(responses, key=lambda r: r.bot_name)

        for response in sorted_responses:
            emoji = self.BOT_EMOJIS.get(response.bot_name, "🤖")
            parts.append(f"{emoji} **@{response.bot_name}:**")
            parts.append(response.content)
            parts.append("")

        responding_bots = [r.bot_name for r in responses]

        return MessageEnvelope(
            content="\n".join(parts).strip(),
            bot_name="team",
            metadata={
                "multi_bot": True,
                "responding_bots": responding_bots,
                "bot_count": len(responses),
                "mode": DispatchTarget.TEAM_CONTEXT.value,
            },
        )

    def combine_with_errors(
        self, responses: List[MessageEnvelope], mode: DispatchTarget, include_header: bool = True
    ) -> MessageEnvelope:
        """Combine responses including error information.

        Similar to combine() but includes error information for failed bots
        instead of filtering them out.

        Args:
            responses: List of bot responses (may contain exceptions)
            mode: The dispatch mode that triggered these responses
            include_header: Whether to include a header line

        Returns:
            Formatted MessageEnvelope with both success and error information
        """
        valid_responses = []
        errors = []

        for response in responses:
            if isinstance(response, Exception):
                errors.append(f"Error: {response}")
            elif response and response.content:
                valid_responses.append(response)
            else:
                errors.append("Empty response")

        # Combine valid responses
        combined = self.combine(valid_responses, mode, include_header)

        # Append error information if any
        if errors and valid_responses:
            error_section = "\n\n⚠️ **Notes:**\n" + "\n".join(f"- {e}" for e in errors[:3])
            combined.content += error_section
            combined.metadata["errors"] = errors
        elif errors and not valid_responses:
            return MessageEnvelope(
                content="❌ All bots failed:\n" + "\n".join(f"- {e}" for e in errors[:3]),
                bot_name="system",
                metadata={"errors": errors, "error_count": len(errors)},
            )

        return combined

    def _format_smart_discuss_response(
        self, responses: List[MessageEnvelope], include_header: bool = True
    ) -> MessageEnvelope:
        """Format @discuss style smart discussion response.

        Args:
            responses: List of valid bot responses
            include_header: Whether to include a header line

        Returns:
            Formatted MessageEnvelope
        """
        parts = []

        if include_header:
            parts.append("💬 **Smart Discussion**")
            parts.append("")

        # Sort responses by bot name for consistency
        sorted_responses = sorted(responses, key=lambda r: r.bot_name or "")

        for response in sorted_responses:
            emoji = self.BOT_EMOJIS.get(response.bot_name, "🤖")
            parts.append(f"{emoji} **@{response.bot_name}:**")
            parts.append(response.content)
            parts.append("")

        # Gather metadata
        responding_bots = [r.bot_name for r in responses if r.bot_name]

        return MessageEnvelope(
            content="\n".join(parts).strip(),
            bot_name="smart_discuss",
            metadata={
                "multi_bot": True,
                "responding_bots": responding_bots,
                "bot_count": len(responses),
                "mode": DispatchTarget.SMART_DISCUSS.value,
            },
        )

    def get_bot_emoji(self, bot_name: str) -> str:
        """Get emoji for a bot.

        Args:
            bot_name: Name of the bot

        Returns:
            Emoji string
        """
        return self.BOT_EMOJIS.get(bot_name, "🤖")

    def get_bot_color(self, bot_name: str) -> str:
        """Get color for a bot (for CLI display).

        Args:
            bot_name: Name of the bot

        Returns:
            Color name string
        """
        return self.BOT_COLORS.get(bot_name, "white")

    def format_single_response(self, response: MessageEnvelope, include_emoji: bool = True) -> str:
        """Format a single bot response.

        Args:
            response: Single bot response
            include_emoji: Whether to include bot emoji

        Returns:
            Formatted string
        """
        if include_emoji:
            emoji = self.BOT_EMOJIS.get(response.bot_name, "🤖")
            return f"{emoji} **@{response.bot_name}:**\n{response.content}"
        else:
            return f"**@{response.bot_name}:**\n{response.content}"


# Convenience function
def get_response_combiner() -> ResponseCombiner:
    """Get a ResponseCombiner instance.

    Returns:
        ResponseCombiner instance
    """
    return ResponseCombiner()
