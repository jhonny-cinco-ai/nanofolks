"""Team system for personality customization."""

from .team import Team, TeamName, BotTeamProfile
from .presets import (
    PIRATE_CREW,
    ROCK_BAND,
    SWAT_TEAM,
    FERAL_CLOWDER,
    EXECUTIVE_SUITE,
    SPACE_CREW,
    AVAILABLE_TEAMS,
    get_team,
    list_teams,
)
from .manager import TeamManager

__all__ = [
    "Team",
    "TeamName",
    "BotTeamProfile",
    "PIRATE_CREW",
    "ROCK_BAND",
    "SWAT_TEAM",
    "FERAL_CLOWDER",
    "EXECUTIVE_SUITE",
    "SPACE_CREW",
    "AVAILABLE_TEAMS",
    "get_team",
    "list_teams",
    "TeamManager",
]
