"""Reasoning configurations for bot implementations.

This module exports bot-specific Chain-of-Thought configurations.
"""

from nanofolks.reasoning.config import (
    AUDITOR_REASONING,
    BOT_REASONING_CONFIGS,
    CODER_REASONING,
    COORDINATOR_REASONING,
    CREATIVE_REASONING,
    DEFAULT_REASONING,
    RESEARCHER_REASONING,
    SOCIAL_REASONING,
    CoTLevel,
    ReasoningConfig,
    get_reasoning_config,
)

__all__ = [
    "ReasoningConfig",
    "CoTLevel",
    "RESEARCHER_REASONING",
    "CODER_REASONING",
    "SOCIAL_REASONING",
    "AUDITOR_REASONING",
    "CREATIVE_REASONING",
    "COORDINATOR_REASONING",
    "DEFAULT_REASONING",
    "get_reasoning_config",
    "BOT_REASONING_CONFIGS",
]
