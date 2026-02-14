"""Configuration utilities for bot themes and custom names.

Provides functions to load and apply user preferences for:
- Crew themes (pirate, rock band, etc.)
- Custom bot display names
"""

import json
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

from nanobot.config.loader import get_data_dir
from nanobot.themes import ThemeManager


class BotAppearanceConfig:
    """Manages bot appearance configuration (themes and custom names)."""
    
    def __init__(self):
        """Initialize appearance config."""
        self.config_dir = get_data_dir()
        self.theme_file = self.config_dir / "theme_config.json"
        self.names_file = self.config_dir / "bot_custom_names.json"
        
        # Load configurations
        self._theme_manager: Optional[ThemeManager] = None
        self._custom_names: Dict[str, str] = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load theme and name configurations from disk."""
        # Load theme
        if self.theme_file.exists():
            try:
                theme_config = json.loads(self.theme_file.read_text())
                current_theme = theme_config.get("current_theme", "pirate_crew")
                self._theme_manager = ThemeManager(current_theme)
                logger.debug(f"Loaded theme: {current_theme}")
            except Exception as e:
                logger.warning(f"Failed to load theme config: {e}")
                self._theme_manager = ThemeManager("pirate_crew")
        else:
            # Default to pirate crew
            self._theme_manager = ThemeManager("pirate_crew")
        
        # Load custom names
        if self.names_file.exists():
            try:
                self._custom_names = json.loads(self.names_file.read_text())
                logger.debug(f"Loaded custom names for {len(self._custom_names)} bots")
            except Exception as e:
                logger.warning(f"Failed to load bot names config: {e}")
                self._custom_names = {}
    
    @property
    def theme_manager(self) -> Optional[ThemeManager]:
        """Get the current theme manager.
        
        Returns:
            ThemeManager instance or None
        """
        return self._theme_manager
    
    def get_custom_name(self, bot_name: str) -> Optional[str]:
        """Get custom display name for a bot.
        
        Args:
            bot_name: Bot identifier (nanobot, researcher, coder, etc.)
            
        Returns:
            Custom name if set, None otherwise
        """
        return self._custom_names.get(bot_name.lower())
    
    def get_bot_appearance(self, bot_name: str) -> Dict[str, Optional[str]]:
        """Get complete appearance config for a bot.
        
        This combines theme defaults with user customizations.
        
        Args:
            bot_name: Bot identifier
            
        Returns:
            Dictionary with display_name, title, greeting, etc.
        """
        result = {
            "display_name": None,
            "title": None,
            "greeting": None,
            "voice": None,
            "emoji": None,
        }
        
        # Get theme defaults
        if self._theme_manager and self._theme_manager.current_theme:
            theming = self._theme_manager.get_bot_theming(bot_name)
            if theming:
                result["title"] = theming.get("title")
                result["greeting"] = theming.get("greeting")
                result["voice"] = theming.get("voice")
                result["emoji"] = theming.get("emoji")
                # Default display name is the title
                result["display_name"] = theming.get("title")
        
        # Override with custom name if set
        custom_name = self.get_custom_name(bot_name)
        if custom_name:
            result["display_name"] = custom_name
        
        return result
    
    def reload(self) -> None:
        """Reload configurations from disk."""
        self._load_configs()
        logger.info("Reloaded bot appearance configuration")


# Global instance
_appearance_config: Optional[BotAppearanceConfig] = None


def get_appearance_config() -> BotAppearanceConfig:
    """Get the global appearance configuration.
    
    Returns:
        BotAppearanceConfig instance (creates if needed)
    """
    global _appearance_config
    if _appearance_config is None:
        _appearance_config = BotAppearanceConfig()
    return _appearance_config


def reset_appearance_config() -> None:
    """Reset the global appearance configuration (forces reload)."""
    global _appearance_config
    _appearance_config = None
