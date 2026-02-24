"""Tag parsing system for multi-agent orchestration.

Parses Discord/Slack style tags from user messages:
- @bot mentions
    - Action keywords
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ParsedTags:
    """Result of parsing tags from a message."""

    bots: List[str] = field(default_factory=list)
    """List of bot names mentioned via @bot"""

    actions: List[str] = field(default_factory=list)
    """Action keywords detected (create, join, leave, etc.)"""

    raw_message: str = ""
    """Original message text"""

    mentions: Dict[str, str] = field(default_factory=dict)
    """Full context of each mention"""


class TagHandler:
    """Parse and validate tags in user messages."""

    # Regex patterns
    BOT_PATTERN = r"@([\w\-]+)"
    """Match @botname tags"""

    ACTION_PATTERN = r"^(create|join|leave|analyze|research|coordinate|archive|switch)\s"
    """Match action keywords at start of message"""

    def __init__(self):
        """Initialize tag handler."""
        pass

    def parse_tags(self, message: str) -> ParsedTags:
        """Extract all tags from message.

        Examples:
            "@researcher analyze this data"
            -> bots=["researcher"], actions=["analyze"]

        Args:
            message: User message to parse

        Returns:
            ParsedTags with extracted tags
        """
        # Extract @bot mentions
        bots = [m.group(1) for m in re.finditer(self.BOT_PATTERN, message)]

        # Extract action keywords
        actions = []
        action_match = re.match(self.ACTION_PATTERN, message, re.IGNORECASE)
        if action_match:
            actions.append(action_match.group(1).lower())

        return ParsedTags(
            bots=list(set(bots)),  # Remove duplicates
            actions=actions,
            raw_message=message,
            mentions=self._extract_mentions(message),
        )

    def _extract_mentions(self, message: str) -> Dict[str, str]:
        """Extract full context of each mention.

        Args:
            message: Message to extract from

        Returns:
            Dictionary mapping mention strings to context
        """
        mentions = {}

        # Extract @bot mentions with context
        for match in re.finditer(self.BOT_PATTERN, message):
            bot_name = match.group(1)
            start = max(0, match.start() - 20)
            end = min(len(message), match.end() + 20)
            context = message[start:end]
            mentions[f"@{bot_name}"] = context

        return mentions

    def validate_tags(
        self,
        parsed: ParsedTags,
        valid_bots: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate parsed tags against available entities.

        Args:
            parsed: ParsedTags from parse_tags()
            valid_bots: List of known bot names (None = skip validation)

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate bots
        if valid_bots is not None:
            for bot in parsed.bots:
                if bot not in valid_bots:
                    errors.append(f"Unknown bot: @{bot}")

        return len(errors) == 0, errors

    def extract_command(self, message: str) -> Optional[str]:
        """Extract action command from message.

        Args:
            message: Message to extract from

        Returns:
            Action command or None if not found
        """
        action_match = re.match(self.ACTION_PATTERN, message, re.IGNORECASE)
        return action_match.group(1).lower() if action_match else None

    def extract_message_text(self, message: str) -> str:
        """Extract message text without tags.

        Args:
            message: Message to clean

        Returns:
            Message with tags removed
        """
        # Remove @bot mentions
        text = re.sub(self.BOT_PATTERN, "", message)
        # Clean up extra whitespace
        text = " ".join(text.split())
        return text

    def has_bot_mention(self, message: str, bot_name: str) -> bool:
        """Check if specific bot is mentioned.

        Args:
            message: Message to check
            bot_name: Bot name to look for

        Returns:
            True if bot is mentioned
        """
        pattern = r"@" + re.escape(bot_name) + r"\b"
        return bool(re.search(pattern, message, re.IGNORECASE))

    def count_mentions(self, message: str) -> Dict[str, int]:
        """Count different types of mentions in message.

        Args:
            message: Message to analyze

        Returns:
            Dictionary with counts
        """
        return {
            "bots": len(set(m.group(1) for m in re.finditer(self.BOT_PATTERN, message))),
            "actions": 1 if re.match(self.ACTION_PATTERN, message, re.IGNORECASE) else 0,
        }
