"""Heartbeat checks for all bot types.

This module exports all domain-specific heartbeat checks.
Importing these modules automatically registers the checks
with the global check registry.

Example:
    from nanofolks.bots.checks import researcher_checks, coder_checks
    # Checks are now registered and can be used by BotHeartbeatService
"""

# Import all check modules to ensure registration
# The act of importing registers the checks via @register_check decorator
from . import researcher_checks
from . import coder_checks
from . import social_checks
from . import auditor_checks
from . import creative_checks
from . import coordinator_checks

__all__ = [
    "researcher_checks",
    "coder_checks",
    "social_checks",
    "auditor_checks",
    "creative_checks",
    "coordinator_checks",
]