"""Team system for personality customization using template-based discovery."""

from .manager import TeamManager
from .profiles import TeamProfile, get_bot_team_profile, get_all_bot_team_profiles

__all__ = [
    "TeamManager",
    "TeamProfile",
    "get_bot_team_profile",
    "get_all_bot_team_profiles",
]
