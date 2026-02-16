"""Utilities for reading user profile from USER.md."""

import re
from pathlib import Path
from loguru import logger


def get_user_timezone(workspace: Path) -> str:
    """
    Extract timezone from workspace/USER.md.
    
    Looks for "Timezone:" in the USER.md file and extracts the value.
    Falls back to "UTC" if not found or file doesn't exist.
    
    Args:
        workspace: Path to workspace directory
    
    Returns:
        Timezone string (e.g., "America/New_York", "UTC")
    """
    user_file = workspace / "USER.md"
    
    if not user_file.exists():
        logger.debug(f"USER.md not found at {user_file}, using default timezone UTC")
        return "UTC"
    
    try:
        content = user_file.read_text()
        
        # Look for "Timezone: <value>" pattern (case-insensitive)
        # Handles:
        # - Timezone: America/New_York
        # - Timezone: UTC
        # - timezone: Asia/Tokyo
        match = re.search(r'(?:timezone|Timezone):\s*(\S+)', content, re.IGNORECASE)
        
        if match:
            tz = match.group(1).strip()
            logger.debug(f"Read timezone from USER.md: {tz}")
            return tz
        else:
            logger.debug("Timezone not found in USER.md, using default UTC")
            return "UTC"
            
    except Exception as e:
        logger.warning(f"Failed to read timezone from USER.md: {e}, using default UTC")
        return "UTC"


def set_user_timezone(workspace: Path, timezone: str) -> bool:
    """
    Update timezone in workspace/USER.md.
    
    Args:
        workspace: Path to workspace directory
        timezone: Timezone string (e.g., "America/New_York")
    
    Returns:
        True if successful, False otherwise
    """
    user_file = workspace / "USER.md"
    
    if not user_file.exists():
        logger.warning(f"USER.md not found at {user_file}, cannot set timezone")
        return False
    
    try:
        content = user_file.read_text()
        
        # Replace existing timezone or add it
        if re.search(r'(?:timezone|Timezone):\s*\S+', content, re.IGNORECASE):
            # Replace existing
            new_content = re.sub(
                r'(?:timezone|Timezone):\s*\S+',
                f'Timezone: {timezone}',
                content,
                flags=re.IGNORECASE
            )
        else:
            # Add new timezone line in Preferences section
            new_content = re.sub(
                r'(## Preferences\s*\n)',
                f'## Preferences\n\n- Timezone: {timezone}\n',
                content
            )
        
        user_file.write_text(new_content)
        logger.info(f"Updated timezone in USER.md to: {timezone}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update timezone in USER.md: {e}")
        return False
