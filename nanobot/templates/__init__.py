"""Bot template files for multi-agent system."""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "bots"

BOT_NAMES = ["nanobot", "researcher", "coder", "social", "creative", "auditor"]


def get_agents_template(bot_name: str) -> str | None:
    """Get AGENTS.md template for a bot.
    
    Args:
        bot_name: Name of the bot
        
    Returns:
        Template content or None if not found
    """
    template_file = TEMPLATES_DIR / f"{bot_name}_AGENTS.md"
    if template_file.exists():
        return template_file.read_text(encoding="utf-8")
    return None


def get_all_agents_templates() -> dict[str, str]:
    """Get all AGENTS.md templates.
    
    Returns:
        Dict mapping bot_name to template content
    """
    templates = {}
    for bot_name in BOT_NAMES:
        content = get_agents_template(bot_name)
        if content:
            templates[bot_name] = content
    return templates
