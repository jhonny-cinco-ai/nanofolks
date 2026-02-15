"""Bot definitions - now uses file-based templates.

This file now just re-exports from the central role_card module.
All bot personality data comes from template files:
- bots/ - AGENTS.md templates
- soul/ - SOUL.md templates (per theme)
- identity/ - IDENTITY.md templates (per theme)

Use BotRegistry to access bot configurations.
"""

from nanobot.models.role_card import (
    RoleCard,
    RoleCardDomain,
    BotCapabilities,
    BUILTIN_BOTS,
    get_role_card,
    list_bots,
    is_valid_bot,
)
from nanobot.models.bot_registry import (
    BotRegistry,
    get_bot_registry,
    list_available_bots,
)

# Re-export for backward compatibility
__all__ = [
    "RoleCard",
    "RoleCardDomain", 
    "BotCapabilities",
    "BUILTIN_BOTS",
    "get_role_card",
    "list_bots",
    "is_valid_bot",
    "BotRegistry",
    "get_bot_registry",
    "list_available_bots",
]
