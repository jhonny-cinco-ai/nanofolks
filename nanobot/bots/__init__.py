"""Bot system for multi-agent orchestration."""

from .base import SpecialistBot
from .definitions import (
    NANOBOT_ROLE,
    RESEARCHER_ROLE,
    CODER_ROLE,
    SOCIAL_ROLE,
    CREATIVE_ROLE,
    AUDITOR_ROLE,
)
from .implementations import (
    NanobotLeader,
    ResearcherBot,
    CoderBot,
    SocialBot,
    CreativeBot,
    AuditorBot,
)

# Heartbeat configurations and checks
from .heartbeat_configs import (
    RESEARCHER_CONFIG,
    CODER_CONFIG,
    SOCIAL_CONFIG,
    AUDITOR_CONFIG,
    CREATIVE_CONFIG,
    COORDINATOR_CONFIG,
    DEFAULT_CONFIGS,
    get_bot_heartbeat_config,
    get_all_heartbeat_configs,
    load_config_from_file,
    save_heartbeat_config,
    merge_config,
)

# Import check modules to ensure registration
from .checks import (
    researcher_checks,
    coder_checks,
    social_checks,
    auditor_checks,
    creative_checks,
    coordinator_checks,
)

__all__ = [
    # Base classes
    "SpecialistBot",
    # Role definitions
    "NANOBOT_ROLE",
    "RESEARCHER_ROLE",
    "CODER_ROLE",
    "SOCIAL_ROLE",
    "CREATIVE_ROLE",
    "AUDITOR_ROLE",
    # Bot implementations
    "NanobotLeader",
    "ResearcherBot",
    "CoderBot",
    "SocialBot",
    "CreativeBot",
    "AuditorBot",
    # Heartbeat configs
    "RESEARCHER_CONFIG",
    "CODER_CONFIG",
    "SOCIAL_CONFIG",
    "AUDITOR_CONFIG",
    "CREATIVE_CONFIG",
    "COORDINATOR_CONFIG",
    "DEFAULT_CONFIGS",
    # Config functions
    "get_bot_heartbeat_config",
    "get_all_heartbeat_configs",
    "load_config_from_file",
    "save_heartbeat_config",
    "merge_config",
    # Check modules (imported for side effects)
    "researcher_checks",
    "coder_checks",
    "social_checks",
    "auditor_checks",
    "creative_checks",
    "coordinator_checks",
]
