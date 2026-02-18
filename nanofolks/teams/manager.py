"""Team manager for applying and switching teams."""

from typing import Optional

from nanofolks.teams.presets import AVAILABLE_TEAMS, get_team, list_teams
from nanofolks.teams.team import Team


class TeamManager:
    """Manage team selection and application."""

    def __init__(self, default_team: str = "pirate_crew"):
        """Initialize team manager.

        Args:
            default_team: Default team name (pirate_crew, rock_band, swat_team, feral_clowder, executive_suite, space_crew)
        """
        self.current_team: Optional[Team] = get_team(default_team)
        if self.current_team is None:
            self.current_team = AVAILABLE_TEAMS[0]  # Fall back to first team

    def list_teams(self) -> list[dict]:
        """Get list of available teams.

        Returns:
            List of team dictionaries with name, display_name, description, emoji
        """
        return list_teams()

    def select_team(self, team_name: str) -> Optional[Team]:
        """Select a team.

        Args:
            team_name: Team name (pirate_crew, rock_band, etc.)

        Returns:
            Selected team or None if not found
        """
        team = get_team(team_name)
        if team:
            self.current_team = team
            return team
        return None

    def get_current_team(self) -> Optional[Team]:
        """Get currently active team.

        Returns:
            Current team or None
        """
        return self.current_team

    def get_current_team_name(self) -> Optional[str]:
        """Get name of currently active team.

        Returns:
            Team name or None
        """
        if self.current_team:
            return self.current_team.name.value
        return None

    def get_bot_theming(self, bot_role: str) -> dict:
        """Get theming for a specific bot in current team.

        Args:
            bot_role: Role identifier (leader, researcher, coder, social, creative, auditor)

        Returns:
            Dictionary with bot theming info (bot_title, bot_name, personality, greeting, voice, emoji)
        """
        if not self.current_team:
            return {}

        theming = self.current_team.get_bot_theming(bot_role)
        if theming:
            return {
                "bot_title": theming.bot_title,
                "bot_name": theming.bot_name,
                "personality": theming.personality,
                "greeting": theming.greeting,
                "voice": theming.voice_directive,
                "emoji": theming.emoji,
            }
        return {}

    def get_all_bots_theming(self) -> dict:
        """Get theming for all bots in current team.

        Returns:
            Dictionary mapping bot roles to their theming
        """
        if not self.current_team:
            return {}

        all_theming = {}
        for bot_role, theming in self.current_team.get_all_bots_theming().items():
            all_theming[bot_role] = {
                "bot_title": theming.bot_title,
                "bot_name": theming.bot_name,
                "personality": theming.personality,
                "greeting": theming.greeting,
                "voice": theming.voice_directive,
                "emoji": theming.emoji,
            }
        return all_theming

    def to_dict(self) -> dict:
        """Convert current team to dictionary.

        Returns:
            Team dictionary representation
        """
        if self.current_team:
            return self.current_team.to_dict()
        return {}
