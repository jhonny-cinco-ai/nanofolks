"""Team profile aggregation utilities.

Builds a single read-only profile per bot by combining:
- Team templates (SOUL + IDENTITY)
- Workspace overrides (SOUL + IDENTITY + AGENTS)
- Role cards (ROLE.md/YAML or built-in)
- Reasoning configuration
- Tool permissions
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from nanofolks.agent.tools.permissions import (
    ToolPermissions,
    merge_permissions,
    parse_tool_permissions,
)
from nanofolks.models.role_card import BUILTIN_ROLES, RoleCard, get_role_card
from nanofolks.reasoning.config import ReasoningConfig, get_reasoning_config
from nanofolks.templates import (
    BOT_NAMES,
    get_agents_template,
    get_identity_template_for_bot,
    get_soul_template_for_bot,
    get_bot_team_profile as get_template_team_profile,
)
from nanofolks.templates.parser import parse_identity_file, parse_soul_file


@dataclass(frozen=True)
class TeamProfile:
    """Aggregated, read-only team profile for a bot."""

    bot_role: str
    team_name: str
    bot_name: str
    bot_title: str
    emoji: str
    personality: str
    greeting: str
    voice: str
    role_card: Optional[RoleCard]
    reasoning: ReasoningConfig
    permissions: ToolPermissions
    sources: Dict[str, str]
    soul_content: Optional[str] = None
    identity_content: Optional[str] = None
    agents_content: Optional[str] = None

    def display_name(self) -> str:
        """Preferred display name for the bot."""
        return self.bot_name or self.bot_title or self.bot_role

    def to_dict(self) -> Dict[str, object]:
        """Convert to a dictionary for compatibility with legacy callers."""
        return {
            "bot_role": self.bot_role,
            "team_name": self.team_name,
            "bot_name": self.bot_name,
            "bot_title": self.bot_title,
            "emoji": self.emoji,
            "personality": self.personality,
            "greeting": self.greeting,
            "voice": self.voice,
            "role_card": self.role_card,
            "reasoning": self.reasoning,
            "permissions": self.permissions,
            "sources": self.sources,
            "soul_content": self.soul_content,
            "identity_content": self.identity_content,
            "agents_content": self.agents_content,
        }

    def get(self, key: str, default: object = None) -> object:
        """Compatibility accessor for legacy dict-style usage."""
        return self.to_dict().get(key, default)


def _read_workspace_file(workspace_path: Optional[Path], bot_role: str, filename: str) -> Optional[str]:
    if not workspace_path:
        return None

    file_path = Path(workspace_path) / "bots" / bot_role / filename
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return None


def _normalize_metadata(metadata: Dict[str, str]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}

    if metadata.get("name"):
        normalized["bot_name"] = metadata["name"]
    if metadata.get("title"):
        normalized["bot_title"] = metadata["title"]
    elif metadata.get("short_title"):
        normalized["bot_title"] = metadata["short_title"]

    if metadata.get("emoji"):
        normalized["emoji"] = metadata["emoji"]
    if metadata.get("personality"):
        normalized["personality"] = metadata["personality"]
    if metadata.get("greeting"):
        normalized["greeting"] = metadata["greeting"]
    if metadata.get("voice_directive"):
        normalized["voice"] = metadata["voice_directive"]
    if metadata.get("voice"):
        normalized["voice"] = metadata["voice"]

    return normalized


def _merge_profile(base: Dict[str, str], override: Dict[str, str]) -> Dict[str, str]:
    merged = dict(base)
    for key, value in override.items():
        if value is not None and value != "":
            merged[key] = value
    return merged


def _permissions_from_markdown(content: Optional[str]) -> ToolPermissions:
    if not content:
        return ToolPermissions()
    return parse_tool_permissions(content)


def _role_card_source(bot_role: str, workspace_path: Optional[Path]) -> str:
    if not workspace_path:
        return "builtin"

    workspace_path = Path(workspace_path)
    role_md = workspace_path / "bots" / bot_role / "ROLE.md"
    if role_md.exists():
        return "workspace"

    workspace_yaml = workspace_path / ".nanofolks" / "role_cards" / f"{bot_role}.yaml"
    if workspace_yaml.exists():
        return "workspace"

    global_yaml = Path.home() / ".config" / "nanofolks" / "role_cards" / f"{bot_role}.yaml"
    if global_yaml.exists():
        return "global"

    return "builtin"


def get_bot_team_profile(
    bot_role: str,
    team_name: str,
    workspace_path: Optional[Path] = None,
) -> TeamProfile:
    """Build an aggregated team profile for a bot.

    Args:
        bot_role: Bot identifier (leader, researcher, coder, etc.)
        team_name: Team name
        workspace_path: Optional workspace path for overrides

    Returns:
        TeamProfile instance
    """
    template_profile = get_template_team_profile(bot_role, team_name) or {}

    template_soul = get_soul_template_for_bot(bot_role, team=team_name)
    template_identity = get_identity_template_for_bot(bot_role, team=team_name)
    template_agents = get_agents_template(bot_role)

    workspace_soul = _read_workspace_file(workspace_path, bot_role, "SOUL.md")
    workspace_identity = _read_workspace_file(workspace_path, bot_role, "IDENTITY.md")
    workspace_agents = _read_workspace_file(workspace_path, bot_role, "AGENTS.md")

    sources = {
        "soul": "workspace" if workspace_soul else ("template" if template_soul else "missing"),
        "identity": "workspace" if workspace_identity else ("template" if template_identity else "missing"),
        "agents": "workspace" if workspace_agents else ("template" if template_agents else "missing"),
    }

    base_metadata: Dict[str, str] = dict(template_profile)

    # Workspace overrides from IDENTITY + SOUL
    workspace_metadata: Dict[str, str] = {}
    if workspace_identity:
        workspace_metadata.update(parse_identity_file(workspace_identity))
    if workspace_soul:
        workspace_metadata.update(parse_soul_file(workspace_soul))

    normalized_workspace = _normalize_metadata(workspace_metadata)
    merged = _merge_profile(base_metadata, normalized_workspace)

    if workspace_path:
        role_card = get_role_card(bot_role, workspace_path)
        role_source = _role_card_source(bot_role, workspace_path)
    else:
        role_card = BUILTIN_ROLES.get(bot_role)
        role_source = "builtin"
    sources["role_card"] = role_source

    bot_title = merged.get("bot_title") or (role_card.title if role_card else "") or bot_role.title()
    bot_name = merged.get("bot_name") or bot_title or bot_role
    emoji = merged.get("emoji") or "👤"
    personality = merged.get("personality") or ""
    greeting = merged.get("greeting") or ""
    voice = merged.get("voice") or ""

    # Permissions (template + workspace)
    permissions = merge_permissions(
        _permissions_from_markdown(template_soul),
        _permissions_from_markdown(template_agents),
        _permissions_from_markdown(workspace_soul),
        _permissions_from_markdown(workspace_agents),
    )

    reasoning = get_reasoning_config(bot_role)

    return TeamProfile(
        bot_role=bot_role,
        team_name=team_name,
        bot_name=bot_name,
        bot_title=bot_title,
        emoji=emoji,
        personality=personality,
        greeting=greeting,
        voice=voice,
        role_card=role_card or BUILTIN_ROLES.get(bot_role),
        reasoning=reasoning,
        permissions=permissions,
        sources=sources,
        soul_content=workspace_soul or template_soul,
        identity_content=workspace_identity or template_identity,
        agents_content=workspace_agents or template_agents,
    )


def get_all_bot_team_profiles(
    team_name: str,
    workspace_path: Optional[Path] = None,
) -> Dict[str, TeamProfile]:
    """Get aggregated team profiles for all bots in a team."""
    profiles: Dict[str, TeamProfile] = {}
    for bot_role in BOT_NAMES:
        profiles[bot_role] = get_bot_team_profile(bot_role, team_name, workspace_path)
    return profiles
