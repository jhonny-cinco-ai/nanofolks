"""Team system for personality customization."""

from .manager import TeamManager
from .presets import (
    AVAILABLE_TEAMS,
    EXECUTIVE_SUITE,
    FERAL_CLOWDER,
    PIRATE_CREW,
    ROCK_BAND,
    SPACE_CREW,
    SWAT_TEAM,
    get_team,
    list_teams,
)
from .team import BotTeamProfile, Team, TeamName

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
