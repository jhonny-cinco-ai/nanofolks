"""Theme system for personality customization."""

from .theme import Theme, ThemeName, BotTheming
from .presets import (
    PIRATE_CREW,
    ROCK_BAND,
    SWAT_TEAM,
    PROFESSIONAL,
    SPACE_CREW,
    AVAILABLE_THEMES,
    get_theme,
    list_themes,
)
from .manager import ThemeManager

__all__ = [
    "Theme",
    "ThemeName",
    "BotTheming",
    "PIRATE_CREW",
    "ROCK_BAND",
    "SWAT_TEAM",
    "PROFESSIONAL",
    "SPACE_CREW",
    "AVAILABLE_THEMES",
    "get_theme",
    "list_themes",
    "ThemeManager",
]
