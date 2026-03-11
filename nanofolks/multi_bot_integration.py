"""Multi-bot architecture integration module.

This module provides helper functions and examples for integrating the new
multi-bot fleet architecture into the existing nanofolks system.

Usage:
    from nanofolks.multi_bot_integration import (
        initialize_fleet_architecture,
        create_bot_fleet_with_orchestrator,
    )

    # Initialize with feature flags
    fleet, router = await initialize_fleet_architecture(config, workspace, provider)
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from loguru import logger

from nanofolks.bots.fleet import BotFleet
from nanofolks.bots.room_manager import get_room_manager
from nanofolks.bus.queue import MessageBus
from nanofolks.config.loader import load_config

if TYPE_CHECKING:
    from nanofolks.agent.message_router import MessageRouter
    from nanofolks.config.schema import Config
    from nanofolks.providers.base import LLMProvider
    from nanofolks.session.room_session_manager import RoomSessionManager


async def initialize_fleet_architecture(
    config: "Config",
    workspace: Path,
    provider: "LLMProvider",
    bus: Optional[MessageBus] = None,
) -> Tuple[BotFleet, "MessageRouter"]:
    """Initialize the complete multi-bot fleet architecture.

    This is the main entry point for setting up the new architecture.
    It creates all necessary components and starts the default bots.

    Args:
        config: Configuration object with features and fleet settings
        workspace: Path to workspace directory
        provider: LLM provider for bot instances
        bus: Optional MessageBus (creates new one if not provided)

    Returns:
        Tuple of (BotFleet, MessageRouter)

    Example:
        >>> config = load_config()
        >>> workspace = Path.home() / "nanofolks"
        >>> provider = create_provider(config)
        >>> fleet, router = await initialize_fleet_architecture(
        ...     config, workspace, provider
        ... )
        >>> await router.run()  # Start processing messages
    """
    from nanofolks.agent.message_router import MessageRouter
    from nanofolks.session.room_session_manager import RoomSessionManager

    logger.info("Initializing multi-bot fleet architecture...")

    # Create message bus if not provided
    if bus is None:
        bus = MessageBus()
        logger.debug("Created new MessageBus")

    # Create room session manager (shared across all bots)
    session_manager = RoomSessionManager(workspace)
    logger.debug("Created RoomSessionManager")

    # Create bot fleet
    fleet = BotFleet(
        workspace=workspace,
        provider=provider,
        bus=bus,
        session_manager=session_manager,
        config=config.fleet if hasattr(config, "fleet") else None,
    )

    # Start fleet
    await fleet.start()
    logger.info("BotFleet started")

    # Get room manager
    room_manager = get_room_manager()

    # Create message router
    router = MessageRouter(
        bus=bus,
        fleet=fleet,
        room_manager=room_manager,
    )
    logger.info("MessageRouter created")

    # Start default bots from config
    auto_start_bots = (
        getattr(config.fleet, "auto_start_bots", ["leader"])
        if hasattr(config, "fleet")
        else ["leader"]
    )

    for bot_name in auto_start_bots:
        try:
            await fleet.start_bot(bot_name)
            logger.info(f"Started bot: {bot_name}")
        except Exception as e:
            logger.error(f"Failed to start bot '{bot_name}': {e}")

    logger.info(
        f"Multi-bot architecture initialized with {len(fleet.get_active_bots())} active bots"
    )

    return fleet, router


async def create_bot_fleet_with_orchestrator(
    workspace: Path,
    provider: "LLMProvider",
    auto_start_bots: Optional[list] = None,
) -> Tuple[BotFleet, "MessageRouter"]:
    """Create a BotFleet and MessageRouter with default configuration.

    This is a simplified version that uses default configuration.
    For production use, prefer initialize_fleet_architecture() with proper config.

    Args:
        workspace: Path to workspace directory
        provider: LLM provider
        auto_start_bots: List of bots to auto-start (default: ["leader"])

    Returns:
        Tuple of (BotFleet, MessageRouter)
    """
    from nanofolks.agent.message_router import MessageRouter
    from nanofolks.session.room_session_manager import RoomSessionManager

    auto_start_bots = auto_start_bots or ["leader"]

    # Create components
    bus = MessageBus()
    session_manager = RoomSessionManager(workspace)

    fleet = BotFleet(
        workspace=workspace,
        provider=provider,
        bus=bus,
        session_manager=session_manager,
    )

    await fleet.start()

    # Start bots
    for bot_name in auto_start_bots:
        try:
            await fleet.start_bot(bot_name)
        except Exception as e:
            logger.error(f"Failed to start bot '{bot_name}': {e}")

    router = MessageRouter(
        bus=bus,
        fleet=fleet,
        room_manager=get_room_manager(),
    )

    return fleet, router


def should_use_fleet_architecture(config: "Config") -> bool:
    """Check if fleet architecture should be used based on feature flags.

    Args:
        config: Configuration object

    Returns:
        True if fleet architecture is enabled
    """
    if not hasattr(config, "features"):
        return False

    return getattr(config.features, "use_fleet_architecture", False)


def get_multi_bot_components(config: "Config") -> dict:
    """Get information about multi-bot components availability.

    Args:
        config: Configuration object

    Returns:
        Dict with component status
    """
    features = getattr(config, "features", None)

    return {
        "fleet_architecture_enabled": getattr(features, "use_fleet_architecture", False)
        if features
        else False,
        "room_sessions_enabled": getattr(features, "use_room_sessions", False)
        if features
        else False,
        "message_router_enabled": getattr(features, "use_message_router", False)
        if features
        else False,
        "bot_coordination_enabled": getattr(features, "use_bot_coordination", False)
        if features
        else False,
    }


async def shutdown_fleet_architecture(
    fleet: BotFleet,
    router: "MessageRouter",
    save_sessions: bool = True,
) -> None:
    """Gracefully shutdown the multi-bot fleet architecture.

    Args:
        fleet: BotFleet instance
        router: MessageRouter instance
        save_sessions: Whether to save sessions before shutdown
    """
    logger.info("Shutting down multi-bot fleet architecture...")

    # Stop router
    await router.stop()
    logger.debug("MessageRouter stopped")

    # Save sessions if requested
    if save_sessions and fleet.session_manager:
        try:
            count = await fleet.session_manager.save_all_sessions()
            logger.info(f"Saved {count} sessions before shutdown")
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")

    # Stop fleet (this stops all bots)
    await fleet.stop()
    logger.info("BotFleet stopped")

    logger.info("Multi-bot fleet architecture shutdown complete")


# Example usage in CLI/chat.py:
"""
# Example integration in cli/chat.py:

async def run_chat_with_fleet(config, workspace, provider):
    # Check if fleet architecture is enabled
    if should_use_fleet_architecture(config):
        # Initialize new architecture
        fleet, router = await initialize_fleet_architecture(
            config, workspace, provider
        )
        
        try:
            # Run the router
            await router.run()
        finally:
            # Cleanup
            await shutdown_fleet_architecture(fleet, router)
    else:
        # Use legacy single-bot architecture
        agent = AgentLoop(
            bot_name="leader",
            bus=MessageBus(),
            provider=provider,
            workspace=workspace,
            ...
        )
        await agent.run()
"""

# Example message handling:
"""
# Example of how messages flow through the new architecture:

# 1. User sends message: "@all what do you think?"
# 2. Message goes to bus
# 3. MessageRouter picks up message
# 4. BotDispatch determines MULTI_BOT target
# 5. MessageRouter broadcasts to all bots via BotFleet
# 6. Each bot processes independently
# 7. Responses collected and combined by ResponseCombiner
# 8. Combined response sent back to user

# Example code:
async def handle_user_message(user_input: str, room_id: str):
    msg = MessageEnvelope(
        content=user_input,
        room_id=room_id,
        channel="cli",
    )
    
    # Route through new architecture
    response = await router.route_message(msg)
    
    # Display response
    print(response.content)
"""
