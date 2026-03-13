"""CLI chat integration with MessageRouter.

This module provides the MessageRouter-based chat implementation for CLI.
It replaces the traditional AgentLoop with BotFleet + MessageRouter for
multi-bot support.

Usage:
    Set use_message_router: true in config to enable
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from loguru import logger

from nanofolks.agent.message_router import MessageRouter
from nanofolks.bots.fleet import BotFleet
from nanofolks.bus.events import MessageEnvelope
from nanofolks.bus.queue import MessageBus
from nanofolks.config.schema import Config
from nanofolks.providers.litellm_provider import LiteLLMProvider
from nanofolks.session.room_session_manager import RoomSessionManager

if TYPE_CHECKING:
    from rich.console import Console


class ChatWithMessageRouter:
    """CLI chat implementation using MessageRouter architecture.

    This class manages the BotFleet + MessageRouter lifecycle for CLI chat,
    providing multi-bot support with streaming responses.
    """

    def __init__(
        self,
        config: Config,
        room_id: str,
        console: "Console",
    ):
        """Initialize MessageRouter chat.

        Args:
            config: Configuration object
            room_id: Room ID to chat in
            console: Rich console for output
        """
        self.config = config
        self.room_id = room_id
        self.console = console

        # Core components
        self.bus: Optional[MessageBus] = None
        self.fleet: Optional[BotFleet] = None
        self.router: Optional[MessageRouter] = None
        self.session_manager: Optional[RoomSessionManager] = None

        self.logger = logger.bind(component="ChatWithMessageRouter")
        self._running = False
        self._streaming_content = ""

    async def initialize(self) -> bool:
        """Initialize all components for MessageRouter chat.

        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing MessageRouter chat...")

            # 1. Create MessageBus
            self.bus = MessageBus()

            # 2. Create LLM provider
            provider_config = self.config.get_provider()
            if not provider_config:
                self.console.print("[red]Error: No LLM provider configured[/red]")
                return False

            provider = LiteLLMProvider(
                default_model=self.config.agents.defaults.model,
                api_key=provider_config.api_key,
                api_base=provider_config.api_base,
            )

            # 3. Create RoomSessionManager
            self.session_manager = RoomSessionManager(Path(self.config.workspace_path))

            # 4. Create BotFleet with room-scoped bots
            self.fleet = BotFleet(
                workspace=Path(self.config.workspace_path),
                provider=provider,
                bus=self.bus,
                session_manager=self.session_manager,
                config=self.config.fleet,
            )

            # 5. Start fleet (but don't start bots yet - lazy start)
            await self.fleet.start()

            # 6. Create MessageRouter
            self.router = MessageRouter(
                bus=self.bus,
                fleet=self.fleet,
                room_manager=None,  # Can add if needed
            )

            # 7. Start MessageRouter in background
            self._router_task = asyncio.create_task(self.router.run())

            self._running = True
            self.logger.info("MessageRouter chat initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize MessageRouter chat: {e}")
            self.console.print(f"[red]Error initializing chat: {e}[/red]")
            return False

    async def start_room_bots(self, bot_names: Optional[list] = None) -> bool:
        """Start bots for the current room.

        Args:
            bot_names: List of bot names to start (defaults to fleet.auto_start_bots)

        Returns:
            True if bots started successfully
        """
        if not self.fleet:
            return False

        bots_to_start = bot_names or self.config.fleet.auto_start_bots

        self.console.print(
            f"[dim]Starting bots for room {self.room_id}: {', '.join(bots_to_start)}...[/dim]"
        )

        try:
            # Start all bots in parallel
            start_tasks = [
                self.fleet.start_bot(bot_name, room_id=self.room_id) for bot_name in bots_to_start
            ]

            await asyncio.gather(*start_tasks, return_exceptions=True)

            # Check which bots actually started
            active_bots = self.fleet.get_room_bots(self.room_id)
            self.logger.info(f"Started {len(active_bots)} bots for room {self.room_id}")

            return len(active_bots) > 0

        except Exception as e:
            self.logger.error(f"Error starting room bots: {e}")
            return False

    async def send_message(
        self,
        content: str,
        stream_callback: Optional[callable] = None,
    ) -> Optional[MessageEnvelope]:
        """Send a message and get response.

        Args:
            content: Message content
            stream_callback: Optional callback for streaming chunks

        Returns:
            Response MessageEnvelope or None
        """
        if not self.bus or not self._running:
            return None

        # Create message envelope
        msg = MessageEnvelope(
            channel="cli",
            chat_id=f"cli-{self.room_id}",
            content=content,
            room_id=self.room_id,
        )

        # Reset streaming content
        self._streaming_content = ""

        try:
            # Publish to bus (MessageRouter will pick it up)
            queued = await self.bus.publish_inbound(msg)

            if not queued:
                self.console.print("[yellow]System is busy. Please try again.[/yellow]")
                return None

            # Wait for response with timeout
            response = await asyncio.wait_for(
                self.bus.consume_outbound(),
                timeout=60.0,  # 60 second timeout
            )

            return response

        except asyncio.TimeoutError:
            self.console.print("[yellow]Response timeout. The bots are taking too long.[/yellow]")
            return None
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return None

    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up MessageRouter chat...")

        self._running = False

        # Stop router
        if self.router:
            await self.router.stop()

        if hasattr(self, "_router_task"):
            self._router_task.cancel()
            try:
                await self._router_task
            except asyncio.CancelledError:
                pass

        # Stop fleet
        if self.fleet:
            await self.fleet.stop()

        self.logger.info("MessageRouter chat cleaned up")


async def chat_with_message_router(
    config: Config,
    room: str,
    console: "Console",
    message: Optional[str] = None,
    markdown: bool = True,
) -> bool:
    """Run chat using MessageRouter architecture.

    This is the main entry point for MessageRouter-based CLI chat.

    Args:
        config: Configuration object
        room: Room ID to chat in
        console: Rich console for output
        message: Optional single message to send (non-interactive mode)
        markdown: Whether to render markdown

    Returns:
        True if chat completed successfully
    """
    chat = ChatWithMessageRouter(config, room, console)

    # Initialize
    if not await chat.initialize():
        return False

    try:
        # Start room bots
        if not await chat.start_room_bots():
            console.print("[red]Failed to start bots. Falling back to standard mode.[/red]")
            return False

        # Display "Lobby" for the default room, otherwise show the room name
        display_room = "Lobby" if room == "general" else room
        console.print(
            f"[green]✓[/green] Connected to [bold cyan]#{display_room}[/bold cyan] with MessageRouter"
        )

        if message:
            # Single message mode
            response = await chat.send_message(message)
            if response:
                from nanofolks.cli.commands import _print_agent_response

                _print_agent_response(
                    response.content,
                    render_markdown=markdown,
                    room_id=response.room_id or room,
                    bot_name=response.bot_name,
                )
            return True
        else:
            # Interactive mode
            console.print("\n[dim]Type your message (or /exit to quit):[/dim]\n")

            while True:
                try:
                    # Get user input
                    from nanofolks.cli.commands import (
                        _init_prompt_session,
                        _read_interactive_input_async,
                    )

                    _init_prompt_session()
                    user_input = await _read_interactive_input_async(room)

                    if not user_input.strip():
                        continue

                    if user_input.strip() in ["/exit", "/quit", "exit", "quit"]:
                        console.print("\nGoodbye!")
                        break

                    # Send message
                    console.print()  # Newline before response
                    response = await chat.send_message(user_input)

                    if response and response.content:
                        from nanofolks.cli.commands import _print_agent_response

                        _print_agent_response(
                            response.content,
                            render_markdown=markdown,
                            room_id=response.room_id or room,
                            bot_name=response.bot_name,
                        )
                        console.print()  # Newline after response

                except KeyboardInterrupt:
                    console.print("\nGoodbye!")
                    break
                except EOFError:
                    console.print("\nGoodbye!")
                    break

            return True

    finally:
        await chat.cleanup()


# Export main function
__all__ = ["chat_with_message_router", "ChatWithMessageRouter"]
