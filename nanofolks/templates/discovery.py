"""Template discovery for scanning and listing available themes."""

from pathlib import Path
from typing import List, Dict, Optional

from nanofolks.templates import SOUL_TEMPLATES_DIR, BOT_NAMES
from nanofolks.templates.parser import get_bot_metadata, parse_theme_description


def discover_themes() -> List[str]:
    """Discover all available themes by scanning template directories.
    
    Returns:
        List of theme names (directory names in templates/soul/)
    """
    themes = []
    if SOUL_TEMPLATES_DIR.exists():
        for item in SOUL_TEMPLATES_DIR.iterdir():
            if item.is_dir():
                themes.append(item.name)
    return sorted(themes)


def get_theme(theme_name: str) -> Optional[Dict]:
    """Get theme data by parsing template files.
    
    Args:
        theme_name: Name of the theme (directory name)
        
    Returns:
        Dictionary with theme data or None if theme not found
    """
    theme_dir = SOUL_TEMPLATES_DIR / theme_name
    if not theme_dir.exists():
        return None
    
    # Get description from leader or first available bot
    description = parse_theme_description(theme_name)
    
    # Build theme data
    theme_data = {
        "name": theme_name,
        "description": description,
        "bots": {}
    }
    
    # Get metadata for each bot
    for bot_name in BOT_NAMES:
        metadata = get_bot_metadata(bot_name, theme_name)
        if metadata:
            theme_data["bots"][bot_name] = metadata
    
    return theme_data


def list_themes() -> List[Dict]:
    """List all available themes with their metadata.
    
    Returns:
        List of theme dictionaries with name, display_name, description, emoji
    """
    themes = []
    
    for theme_name in discover_themes():
        theme_data = get_theme(theme_name)
        if theme_data:
            # Get emoji from leader bot
            leader_metadata = theme_data["bots"].get("leader")
            emoji = leader_metadata.emoji if leader_metadata else "👤"
            
            # Create display name from theme name
            display_name = theme_name.replace("_", " ").title()
            
            themes.append({
                "name": theme_name,
                "display_name": display_name,
                "description": theme_data["description"],
                "emoji": emoji
            })
    
    return themes


def get_bot_theming(bot_name: str, theme_name: str) -> Optional[Dict]:
    """Get theming for a specific bot in a theme.
    
    Args:
        bot_name: Bot role name (leader, researcher, coder, social, creative, auditor)
        theme_name: Theme name
        
    Returns:
        Dictionary with bot theming info or None
    """
    metadata = get_bot_metadata(bot_name, theme_name)
    if metadata:
        return metadata.to_dict()
    return None


def get_all_bots_theming(theme_name: str) -> Dict[str, Dict]:
    """Get theming for all bots in a theme.
    
    Args:
        theme_name: Theme name
        
    Returns:
        Dictionary mapping bot names to their theming
    """
    all_theming = {}
    for bot_name in BOT_NAMES:
        theming = get_bot_theming(bot_name, theme_name)
        if theming:
            all_theming[bot_name] = theming
    return all_theming
