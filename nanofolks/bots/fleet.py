"""BotFleet: Manages a fleet of independent bot instances.

This module provides the BotFleet class, which manages multiple independent
AgentLoop instances. Each bot in the fleet operates independently with its
own context, tools, and identity.

The BotFleet is responsible for:
- Starting and stopping bot instances
- Broadcasting messages to multiple bots in parallel
- Tracking bot health and availability
- Managing bot lifecycle
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from loguru import logger

from nanofolks.bus.events import MessageEnvelope
from nanofolks.bus.queue import MessageBus
from nanofolks.providers.base import LLMProvider

if TYPE_CHECKING:
    from nanofolks.agent.loop import AgentLoop
    from nanofolks.config.schema import FleetConfig
    from nanofolks.session.room_session_manager import RoomSessionManager


class BotFleet:
    """Manages all active bot instances.

    The BotFleet is the central manager for bot instances in the multi-bot
    architecture. It maintains a collection of AgentLoop instances, one per
    active bot, and provides methods for starting, stopping, and routing
    messages to these instances.

    Key responsibilities:
    - Start/stop bot instances on demand
    - Route messages to specific bots
    - Broadcast messages to multiple bots in parallel
    - Track bot health and status
    - Manage bot lifecycle and cleanup

    Attributes:
        workspace: Path to workspace directory
        provider: LLM provider for bot instances
        config: Fleet configuration
        bus: MessageBus for communication
        session_manager: RoomSessionManager for shared sessions
        bots: Dict mapping bot_name to AgentLoop instance
        _lock: Async lock for thread-safe operations
        _running: Whether the fleet is active
    """

    def __init__(
        self,
        workspace: Path,
        provider: LLMProvider,
        bus: MessageBus,
        session_manager: Optional["RoomSessionManager"] = None,
        config: Optional["FleetConfig"] = None,
    ):
        """Initialize the BotFleet.

        Args:
            workspace: Path to workspace directory
            provider: LLM provider for bot instances
            bus: MessageBus for sending/receiving messages
            session_manager: Optional RoomSessionManager for shared sessions
            config: Optional FleetConfig
        """
        self.workspace = workspace
        self.provider = provider
        self.bus = bus
        self.session_manager = session_manager
        self.config = config

        # Bot instances keyed by "room_id:bot_name" for room-scoped parallelism
        self.bots: Dict[str, "AgentLoop"] = {}

        # Track which bots are active per room
        self._room_bots: Dict[str, Set[str]] = {}  # room_id -> set of "room_id:bot_name"

        # Health tracking
        self._bot_health: Dict[str, Dict] = {}
        self._last_activity: Dict[str, float] = {}

        # Concurrency control
        self._lock = asyncio.Lock()
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None

        self.logger = logger.bind(component="BotFleet")
        self.logger.info(f"BotFleet initialized for workspace: {workspace}")

    async def start(self) -> None:
        """Start the fleet and health monitoring."""
        self._running = True

        # Start health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        self.logger.info("BotFleet started")

    async def stop(self) -> None:
        """Stop the fleet and all bot instances."""
        self._running = False

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Stop all bots
        async with self._lock:
            for bot_name in list(self.bots.keys()):
                await self._stop_bot_internal(bot_name)

        self.logger.info("BotFleet stopped")

    def _get_bot_key(self, bot_name: str, room_id: Optional[str] = None) -> str:
        """Get the storage key for a bot.

        For room-scoped parallelism, uses "room_id:bot_name" format.
        For global bots, uses just "bot_name".

        Args:
            bot_name: Name of the bot
            room_id: Optional room ID for room-scoped bots

        Returns:
            Storage key for the bot
        """
        if room_id:
            return f"{room_id}:{bot_name}"
        return bot_name

    async def start_bot(self, bot_name: str, room_id: Optional[str] = None) -> "AgentLoop":
        """Start a bot instance.

        If the bot is already running, returns the existing instance.
        Otherwise, creates and starts a new AgentLoop instance.

        Args:
            bot_name: Name of the bot to start
            room_id: Optional room ID for room-scoped bot instances.
                    If provided, creates a room-specific bot instance
                    for true parallelism between rooms.

        Returns:
            The AgentLoop instance

        Raises:
            ValueError: If bot_name is invalid
            RuntimeError: If bot cannot be started
        """
        bot_key = self._get_bot_key(bot_name, room_id)

        async with self._lock:
            # Check if already running
            if bot_key in self.bots:
                self.logger.debug(f"Bot '{bot_key}' already running")
                return self.bots[bot_key]

            self.logger.info(f"Starting bot: {bot_key}")

            try:
                # Import here to avoid circular dependencies
                from nanofolks.agent.loop import AgentLoop

                # Create bot configuration
                bot_config = self._create_bot_config(bot_name)

                # Create AgentLoop instance with room context
                bot = AgentLoop(
                    bot_name=bot_name,
                    bus=self.bus,
                    provider=self.provider,
                    workspace=self.workspace,
                    session_manager=self.session_manager,
                    **bot_config,
                )

                # Set room context if provided
                if room_id:
                    bot._current_room_id = room_id

                # Store and track
                self.bots[bot_key] = bot
                self._bot_health[bot_key] = {
                    "status": "starting",
                    "started_at": asyncio.get_event_loop().time(),
                    "errors": 0,
                }

                # Track per-room bots
                if room_id:
                    if room_id not in self._room_bots:
                        self._room_bots[room_id] = set()
                    self._room_bots[room_id].add(bot_key)

                # Record activity
                self._last_activity[bot_key] = asyncio.get_event_loop().time()

                self.logger.info(f"Bot '{bot_key}' started successfully")
                return bot

            except Exception as e:
                self.logger.error(f"Failed to start bot '{bot_key}': {e}")
                raise RuntimeError(f"Failed to start bot '{bot_key}': {e}")

    async def stop_bot(self, bot_name: str, room_id: Optional[str] = None) -> bool:
        """Stop a bot instance.

        Args:
            bot_name: Name of the bot to stop
            room_id: Optional room ID for room-scoped bots

        Returns:
            True if bot was stopped, False if not found
        """
        bot_key = self._get_bot_key(bot_name, room_id)
        async with self._lock:
            return await self._stop_bot_internal(bot_key)

    async def stop_room_bots(self, room_id: str) -> int:
        """Stop all bots for a specific room.

        Args:
            room_id: Room ID to stop bots for

        Returns:
            Number of bots stopped
        """
        async with self._lock:
            if room_id not in self._room_bots:
                return 0

            bot_keys = list(self._room_bots[room_id])
            stopped_count = 0

            for bot_key in bot_keys:
                if await self._stop_bot_internal(bot_key):
                    stopped_count += 1

            # Clean up room tracking
            del self._room_bots[room_id]

            self.logger.info(f"Stopped {stopped_count} bots for room {room_id}")
            return stopped_count

    async def _stop_bot_internal(self, bot_key: str) -> bool:
        """Internal method to stop a bot (must hold lock).

        Args:
            bot_key: Key of the bot to stop (can be "bot_name" or "room_id:bot_name")

        Returns:
            True if bot was stopped, False if not found
        """
        if bot_key not in self.bots:
            return False

        self.logger.info(f"Stopping bot: {bot_key}")

        try:
            bot = self.bots[bot_key]

            # Stop the bot
            if hasattr(bot, "stop"):
                await bot.stop()

            # Clean up room tracking if room-scoped
            if ":" in bot_key:
                room_id = bot_key.split(":")[0]
                if room_id in self._room_bots:
                    self._room_bots[room_id].discard(bot_key)

            # Clean up
            del self.bots[bot_key]
            if bot_key in self._bot_health:
                del self._bot_health[bot_key]
            if bot_key in self._last_activity:
                del self._last_activity[bot_key]

            self.logger.info(f"Bot '{bot_key}' stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping bot '{bot_key}': {e}")
            # Still remove from tracking
            self.bots.pop(bot_key, None)
            self._bot_health.pop(bot_key, None)
            self._last_activity.pop(bot_key, None)
            return False

    def get_active_bots(self) -> List[str]:
        """Get list of active bot keys.

        Returns:
            List of active bot keys (can be "bot_name" or "room_id:bot_name")
        """
        return list(self.bots.keys())

    def get_room_bots(self, room_id: str) -> List[str]:
        """Get list of active bot keys for a specific room.

        Args:
            room_id: Room ID to get bots for

        Returns:
            List of bot keys active in the room
        """
        return list(self._room_bots.get(room_id, set()))

    def is_bot_active(self, bot_name: str, room_id: Optional[str] = None) -> bool:
        """Check if a bot is currently active.

        Args:
            bot_name: Name of the bot to check
            room_id: Optional room ID for room-scoped bots

        Returns:
            True if bot is active, False otherwise
        """
        bot_key = self._get_bot_key(bot_name, room_id)
        return bot_key in self.bots

    def is_room_active(self, room_id: str) -> bool:
        """Check if a room has any active bots.

        Args:
            room_id: Room ID to check

        Returns:
            True if room has active bots, False otherwise
        """
        return room_id in self._room_bots and len(self._room_bots[room_id]) > 0

    async def get_or_create_room_bot(self, room_id: str, bot_name: str) -> "AgentLoop":
        """Get an existing room bot or create a new one.

        This is the primary method for room-scoped bot access.
        Ensures the bot exists for the room, creating it if needed.

        Args:
            room_id: Room ID
            bot_name: Name of the bot

        Returns:
            The AgentLoop instance for the room bot
        """
        bot_key = self._get_bot_key(bot_name, room_id)

        if bot_key in self.bots:
            return self.bots[bot_key]

        # Bot doesn't exist, create it
        return await self.start_bot(bot_name, room_id=room_id)

    async def send_proactive_message(
        self,
        room_id: str,
        bot_name: str,
        message: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Send a proactive message from a bot (e.g., after timeout).

        This is used by the proactive loop to send messages when a bot
        decides to proceed without user input.

        Args:
            room_id: Room ID to send to
            bot_name: Bot sending the message
            message: Message content
            metadata: Optional metadata about the proactive decision

        Returns:
            True if message was sent successfully
        """
        try:
            # Create message envelope
            proactive_msg = MessageEnvelope(
                channel="proactive",
                chat_id=room_id,
                content=message,
                bot_name=bot_name,
                room_id=room_id,
                metadata={
                    "is_proactive": True,
                    **(metadata or {}),
                },
            )

            # Publish to bus
            await self.bus.publish_outbound(proactive_msg)

            self.logger.info(f"Sent proactive message from {bot_name} in room {room_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send proactive message: {e}")
            return False

    async def broadcast_to_bots(
        self, bot_names: List[str], message: MessageEnvelope
    ) -> List[MessageEnvelope]:
        """Send message to multiple bots in parallel.

        This method broadcasts a message to multiple bots concurrently,
        collecting their responses. It's used for @all and @team mentions.

        Args:
            bot_names: List of bot names to broadcast to
            message: The message to broadcast

        Returns:
            List of responses (may contain exceptions for failed bots)
        """
        tasks = []
        task_to_bot = {}

        for bot_name in bot_names:
            if bot_name in self.bots:
                # Record activity
                self._last_activity[bot_name] = asyncio.get_event_loop().time()

                # Create task
                task = asyncio.create_task(self.bots[bot_name].process_message(message))
                tasks.append(task)
                task_to_bot[id(task)] = bot_name
            else:
                # Bot not active - add error response
                self.logger.warning(f"Cannot broadcast to inactive bot: {bot_name}")
                tasks.append(
                    asyncio.create_task(
                        self._create_error_response(bot_name, message, "Bot not active")
                    )
                )
                task_to_bot[id(tasks[-1])] = bot_name

        if not tasks:
            return []

        # Wait for all responses
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # Log error and create error response
                bot_name = task_to_bot.get(id(tasks[i]), "unknown")
                self.logger.error(f"Bot '{bot_name}' failed: {response}")
                error_response = await self._create_error_response(bot_name, message, str(response))
                processed_responses.append(error_response)
            else:
                processed_responses.append(response)

        return processed_responses

    async def broadcast_to_bots_streaming(self, bot_names: List[str], message: MessageEnvelope):
        """Send message to multiple bots and yield responses as they arrive.

        This is the streaming version of broadcast_to_bots. Instead of waiting
        for all bots to finish, it yields each response immediately when ready.
        This provides better UX for multi-bot discussions.

        Args:
            bot_names: List of bot names to broadcast to
            message: The message to broadcast

        Yields:
            MessageEnvelope responses as they arrive from each bot

        Example:
            async for response in fleet.broadcast_to_bots_streaming(bots, msg):
                print(f"{response.bot_name}: {response.content}")
        """
        tasks = {}

        for bot_name in bot_names:
            if bot_name in self.bots:
                # Record activity
                self._last_activity[bot_name] = asyncio.get_event_loop().time()

                # Create task
                task = asyncio.create_task(
                    self.bots[bot_name].process_message(message), name=f"bot_{bot_name}"
                )
                tasks[task] = bot_name
            else:
                # Bot not active - yield error immediately
                self.logger.warning(f"Cannot broadcast to inactive bot: {bot_name}")
                error_response = await self._create_error_response(
                    bot_name, message, "Bot not active"
                )
                yield error_response

        if not tasks:
            return

        # Wait for tasks as they complete (streaming)
        pending = set(tasks.keys())
        while pending:
            # Wait for the next task to complete
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                bot_name = tasks.get(task, "unknown")
                try:
                    response = task.result()
                    if isinstance(response, Exception):
                        # Handle exception result
                        self.logger.error(f"Bot '{bot_name}' failed: {response}")
                        error_response = await self._create_error_response(
                            bot_name, message, str(response)
                        )
                        yield error_response
                    else:
                        # Yield successful response
                        self.logger.debug(f"Bot '{bot_name}' responded (streaming)")
                        yield response
                except Exception as e:
                    # Handle task exception
                    self.logger.error(f"Bot '{bot_name}' task failed: {e}")
                    error_response = await self._create_error_response(bot_name, message, str(e))
                    yield error_response

    async def _create_error_response(
        self, bot_name: str, original_msg: MessageEnvelope, error: str
    ) -> MessageEnvelope:
        """Create an error response envelope.

        Args:
            bot_name: Name of the bot that failed
            original_msg: Original message
            error: Error message

        Returns:
            Error MessageEnvelope
        """
        return MessageEnvelope(
            channel=original_msg.channel,
            chat_id=original_msg.chat_id,
            content=f"❌ Bot '{bot_name}' failed: {error}",
            bot_name=bot_name,
            room_id=original_msg.room_id,
            metadata={"error": error, "bot_name": bot_name},
        )

    def get_bot_health(self, bot_name: str) -> Optional[Dict]:
        """Get health information for a bot.

        Args:
            bot_name: Name of the bot

        Returns:
            Health dict or None if bot not found
        """
        return self._bot_health.get(bot_name)

    def get_fleet_stats(self) -> Dict:
        """Get statistics about the fleet.

        Returns:
            Dictionary with fleet statistics
        """
        current_time = asyncio.get_event_loop().time()

        # Calculate activity times
        idle_times = {}
        for bot_name, last_activity in self._last_activity.items():
            idle_times[bot_name] = current_time - last_activity

        return {
            "running": self._running,
            "total_bots": len(self.bots),
            "active_bots": list(self.bots.keys()),
            "health_status": self._bot_health.copy(),
            "idle_times": idle_times,
        }

    async def cleanup_idle_bots(self, idle_timeout: float = 300.0) -> int:
        """Stop bots that have been idle for too long.

        Args:
            idle_timeout: Time in seconds before considering a bot idle

        Returns:
            Number of bots stopped
        """
        current_time = asyncio.get_event_loop().time()
        bots_to_stop = []

        for bot_name, last_activity in self._last_activity.items():
            if current_time - last_activity > idle_timeout:
                bots_to_stop.append(bot_name)

        stopped_count = 0
        for bot_name in bots_to_stop:
            self.logger.info(f"Stopping idle bot: {bot_name}")
            if await self.stop_bot(bot_name):
                stopped_count += 1

        if stopped_count > 0:
            self.logger.info(f"Stopped {stopped_count} idle bots")

        return stopped_count

    async def _health_check_loop(self) -> None:
        """Background task for health monitoring."""
        check_interval = 30.0  # Check every 30 seconds

        while self._running:
            try:
                await asyncio.sleep(check_interval)

                if not self._running:
                    break

                # Check bot health
                for bot_name, bot in list(self.bots.items()):
                    try:
                        # Check if bot is responsive (if bot has health check method)
                        if hasattr(bot, "check_health"):
                            is_healthy = await bot.check_health()
                            if not is_healthy:
                                self.logger.warning(f"Bot '{bot_name}' health check failed")
                                self._bot_health[bot_name]["status"] = "unhealthy"
                                self._bot_health[bot_name]["errors"] += 1
                    except Exception as e:
                        self.logger.error(f"Health check error for '{bot_name}': {e}")
                        self._bot_health[bot_name]["status"] = "error"
                        self._bot_health[bot_name]["errors"] += 1

                # Cleanup idle bots if configured
                if self.config and getattr(self.config, "cleanup_idle_bots", False):
                    await self.cleanup_idle_bots()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")

    def _create_bot_config(self, bot_name: str) -> Dict:
        """Create configuration dict for a bot instance.

        Args:
            bot_name: Name of the bot

        Returns:
            Configuration dictionary for AgentLoop
        """
        # Start with default config
        config = {
            "model": None,  # Use provider default
            "max_iterations": 20,
            "temperature": 0.7,
            "max_tokens": 4096,
            "brave_api_key": None,
            "restrict_to_workspace": False,
            "evolutionary": False,
        }

        # Apply fleet-wide config if available
        if self.config:
            # Override with fleet config
            if hasattr(self.config, "default_model"):
                config["model"] = self.config.default_model
            if hasattr(self.config, "temperature"):
                config["temperature"] = self.config.temperature
            if hasattr(self.config, "max_tokens"):
                config["max_tokens"] = self.config.max_tokens
            if hasattr(self.config, "max_iterations"):
                config["max_iterations"] = self.config.max_iterations

        return config


# Convenience function
def create_bot_fleet(
    workspace: Path,
    provider: LLMProvider,
    bus: MessageBus,
    session_manager: Optional["RoomSessionManager"] = None,
    config: Optional["FleetConfig"] = None,
) -> BotFleet:
    """Create a BotFleet instance.

    Args:
        workspace: Path to workspace directory
        provider: LLM provider for bot instances
        bus: MessageBus for communication
        session_manager: Optional RoomSessionManager
        config: Optional FleetConfig

    Returns:
        BotFleet instance
    """
    return BotFleet(workspace, provider, bus, session_manager, config)
