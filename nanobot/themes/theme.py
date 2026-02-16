"""Theme data structures for personality customization."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ThemeName(Enum):
    """Available personality themes."""

    PIRATE_CREW = "pirate_crew"
    ROCK_BAND = "rock_band"
    SWAT_TEAM = "swat_team"
    FERAL_CLOWDER = "feral_clowder"
    EXECUTIVE_SUITE = "executive_suite"
    SPACE_CREW = "space_crew"


@dataclass
class BotTheming:
    """How a bot appears within a theme."""

    bot_title: str = ""  # Role title ("Captain", "Lead Singer", "Commander", etc.)
    personality: str = ""  # Brief personality description
    greeting: str = ""  # How bot introduces itself
    voice_directive: str = ""  # How bot should communicate
    emoji: str = ""  # Visual identifier
    bot_name: str = ""  # Character name within theme (e.g., "Blackbeard", "Slash")

    def get_default_display_name(self) -> str:
        """Get the default display name for this bot.
        
        Returns:
            bot_name if set, otherwise falls back to bot_title
        """
        return self.bot_name if self.bot_name else self.bot_title


@dataclass
class Theme:
    """Complete personality theme for the team."""

    name: ThemeName  # Theme identifier
    description: str  # Theme description
    leader: BotTheming  # leader theming
    researcher: BotTheming  # @researcher theming
    coder: BotTheming  # @coder theming
    social: BotTheming  # @social theming
    creative: BotTheming  # @creative theming
    auditor: BotTheming  # @auditor theming
    affinity_modifiers: Dict[str, float] = field(default_factory=dict)
    """Modifiers to affinity relationships in this theme"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional theme metadata"""

    def get_bot_theming(self, bot_role: str) -> Optional[BotTheming]:
        """Get theming for a specific bot.

        Args:
            bot_role: Role identifier (leader, researcher, coder, social, creative, auditor)

        Returns:
            BotTheming or None if bot not found
        """
        bot_map = {
            "leader": self.leader,
            "researcher": self.researcher,
            "coder": self.coder,
            "social": self.social,
            "creative": self.creative,
            "auditor": self.auditor,
        }
        return bot_map.get(bot_role)

    def get_all_bots_theming(self) -> Dict[str, BotTheming]:
        """Get theming for all 6 bots.

        Returns:
            Dictionary mapping bot roles to their theming
        """
        return {
            "leader": self.leader,
            "researcher": self.researcher,
            "coder": self.coder,
            "social": self.social,
            "creative": self.creative,
            "auditor": self.auditor,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name.value,
            "description": self.description,
            "bots": {
                "leader": {
                    "bot_title": self.leader.bot_title,
                    "bot_name": self.leader.bot_name,
                    "personality": self.leader.personality,
                    "greeting": self.leader.greeting,
                    "voice": self.leader.voice_directive,
                    "emoji": self.leader.emoji,
                },
                "researcher": {
                    "bot_title": self.researcher.bot_title,
                    "bot_name": self.researcher.bot_name,
                    "personality": self.researcher.personality,
                    "greeting": self.researcher.greeting,
                    "voice": self.researcher.voice_directive,
                    "emoji": self.researcher.emoji,
                },
                "coder": {
                    "bot_title": self.coder.bot_title,
                    "bot_name": self.coder.bot_name,
                    "personality": self.coder.personality,
                    "greeting": self.coder.greeting,
                    "voice": self.coder.voice_directive,
                    "emoji": self.coder.emoji,
                },
                "social": {
                    "bot_title": self.social.bot_title,
                    "bot_name": self.social.bot_name,
                    "personality": self.social.personality,
                    "greeting": self.social.greeting,
                    "voice": self.social.voice_directive,
                    "emoji": self.social.emoji,
                },
                "creative": {
                    "bot_title": self.creative.bot_title,
                    "bot_name": self.creative.bot_name,
                    "personality": self.creative.personality,
                    "greeting": self.creative.greeting,
                    "voice": self.creative.voice_directive,
                    "emoji": self.creative.emoji,
                },
                "auditor": {
                    "bot_title": self.auditor.bot_title,
                    "bot_name": self.auditor.bot_name,
                    "personality": self.auditor.personality,
                    "greeting": self.auditor.greeting,
                    "voice": self.auditor.voice_directive,
                    "emoji": self.auditor.emoji,
                },
            },
            "affinity_modifiers": self.affinity_modifiers,
        }
