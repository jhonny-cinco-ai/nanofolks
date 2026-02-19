"""Team manager for applying and switching teams using template-based discovery."""

from typing import Optional, Dict, List

from nanofolks.templates import (
    discover_themes,
    get_theme,
    list_themes,
    get_bot_theming,
    get_all_bots_theming,
)


class TeamManager:
    """Manage team selection and application using template-based discovery."""

    def __init__(self, default_team: str = "pirate_crew"):
        """Initialize team manager.

        Args:
            default_team: Default team name (pirate_crew, rock_band, swat_team, feral_clowder, executive_suite, space_crew)
        """
        self.current_theme: Optional[str] = default_team
        self._theme_data: Optional[Dict] = None
        
        # Load the default theme
        self._load_theme(default_team)

    def _load_theme(self, theme_name: str) -> bool:
        """Load theme data from templates.
        
        Args:
            theme_name: Name of the theme to load
            
        Returns:
            True if theme loaded successfully, False otherwise
        """
        theme_data = get_theme(theme_name)
        if theme_data:
            self._theme_data = theme_data
            self.current_theme = theme_name
            return True
        return False

    def list_teams(self) -> List[Dict]:
        """Get list of available teams.

        Returns:
            List of team dictionaries with name, display_name, description, emoji
        """
        return list_themes()

    def select_team(self, team_name: str) -> Optional[Dict]:
        """Select a team.

        Args:
            team_name: Team name (pirate_crew, rock_band, etc.)

        Returns:
            Selected team data or None if not found
        """
        if self._load_theme(team_name):
            return self._theme_data
        return None

    def get_current_team(self) -> Optional[Dict]:
        """Get currently active team.

        Returns:
            Current team data or None
        """
        return self._theme_data

    def get_current_team_name(self) -> Optional[str]:
        """Get name of currently active team.

        Returns:
            Team name or None
        """
        return self.current_theme

    def get_bot_theming(self, bot_role: str) -> Dict:
        """Get theming for a specific bot in current team.

        Args:
            bot_role: Role identifier (leader, researcher, coder, social, creative, auditor)

        Returns:
            Dictionary with bot theming info (bot_title, bot_name, personality, greeting, voice, emoji)
        """
        if not self.current_theme:
            return {}

        return get_bot_theming(bot_role, self.current_theme) or {}

    def get_all_bots_theming(self) -> Dict[str, Dict]:
        """Get theming for all bots in current team.

        Returns:
            Dictionary mapping bot roles to their theming
        """
        if not self.current_theme:
            return {}

        return get_all_bots_theming(self.current_theme)

    def to_dict(self) -> Dict:
        """Convert current team to dictionary.

        Returns:
            Team dictionary representation
        """
        if self._theme_data:
            return {
                "name": self._theme_data["name"],
                "description": self._theme_data["description"],
                "bots": {
                    bot_name: bot_data.to_dict() if hasattr(bot_data, 'to_dict') else bot_data
                    for bot_name, bot_data in self._theme_data.get("bots", {}).items()
                }
            }
        return {}
