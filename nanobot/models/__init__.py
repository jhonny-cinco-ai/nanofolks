"""Data models for multi-agent orchestration."""

from .workspace import Workspace, WorkspaceType, Message, SharedContext
from .role_card import RoleCard, RoleCardDomain, BotCapabilities, get_role_card, list_bots, is_valid_bot
from .bot_registry import BotRegistry, get_bot_registry, list_available_bots

__all__ = [
    # Workspace
    "Workspace",
    "WorkspaceType", 
    "Message",
    "SharedContext",
    # Role Card
    "RoleCard",
    "RoleCardDomain",
    "BotCapabilities",
    "get_role_card",
    "list_bots",
    "is_valid_bot",
    # Bot Registry
    "BotRegistry",
    "get_bot_registry",
    "list_available_bots",
]
