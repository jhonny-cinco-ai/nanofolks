"""Channel manager for coordinating chat channels."""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from nanofolks.bus.queue import MessageBus
from nanofolks.channels.base import BaseChannel
from nanofolks.config.schema import Config


class ChannelManager:
    """
    Manages chat channels and coordinates message routing.

    Responsibilities:
    - Initialize enabled channels (Telegram, WhatsApp, etc.)
    - Start/stop channels
    - Route outbound messages
    """

    def __init__(self, config: Config, bus: MessageBus):
        self.config = config
        self.bus = bus
        self.channels: dict[str, BaseChannel] = {}
        self._dispatch_task: asyncio.Task | None = None

        self._init_channels()

    def _init_channels(self) -> None:
        """Initialize channels based on config."""

        # Telegram channel
        if self.config.channels.telegram.enabled:
            try:
                from nanofolks.channels.telegram import TelegramChannel
                self.channels["telegram"] = TelegramChannel(
                    self.config.channels.telegram,
                    self.bus,
                    groq_api_key=self.config.providers.groq.api_key,
                )
                logger.info("Telegram channel enabled")
            except ImportError as e:
                logger.warning(f"Telegram channel not available: {e}")

        # WhatsApp channel
        if self.config.channels.whatsapp.enabled:
            try:
                from nanofolks.channels.whatsapp import WhatsAppChannel
                self.channels["whatsapp"] = WhatsAppChannel(
                    self.config.channels.whatsapp, self.bus
                )
                logger.info("WhatsApp channel enabled")
            except ImportError as e:
                logger.warning(f"WhatsApp channel not available: {e}")

        # Discord channel
        if self.config.channels.discord.enabled:
            try:
                from nanofolks.channels.discord import DiscordChannel
                self.channels["discord"] = DiscordChannel(
                    self.config.channels.discord, self.bus
                )
                logger.info("Discord channel enabled")
            except ImportError as e:
                logger.warning(f"Discord channel not available: {e}")

        # Email channel
        if self.config.channels.email.enabled:
            try:
                from nanofolks.channels.email import EmailChannel
                self.channels["email"] = EmailChannel(
                    self.config.channels.email, self.bus
                )
                logger.info("Email channel enabled")
            except ImportError as e:
                logger.warning(f"Email channel not available: {e}")

        # Slack channel
        if self.config.channels.slack.enabled:
            try:
                from nanofolks.channels.slack import SlackChannel
                self.channels["slack"] = SlackChannel(
                    self.config.channels.slack, self.bus
                )
                logger.info("Slack channel enabled")
            except ImportError as e:
                logger.warning(f"Slack channel not available: {e}")

    async def _start_channel(self, name: str, channel: BaseChannel) -> None:
        """Start a channel and log any exceptions."""
        try:
            await channel.start()
        except Exception as e:
            logger.error(f"Failed to start channel {name}: {e}")

    async def start_all(self) -> None:
        """Start all channels and the outbound dispatcher."""
        if not self.channels:
            logger.warning("No channels enabled")
            return

        # Start outbound dispatcher
        self._dispatch_task = asyncio.create_task(self._dispatch_outbound())

        # Start channels
        tasks = []
        for name, channel in self.channels.items():
            logger.info(f"Starting {name} channel...")
            tasks.append(asyncio.create_task(self._start_channel(name, channel)))

        # Wait for all to complete (they should run forever)
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_all(self) -> None:
        """Stop all channels and the dispatcher."""
        logger.info("Stopping all channels...")

        # Stop dispatcher
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass

        # Stop all channels
        for name, channel in self.channels.items():
            try:
                await channel.stop()
                logger.info(f"Stopped {name} channel")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")

    async def _dispatch_outbound(self) -> None:
        """Dispatch outbound messages to the appropriate channel.

        After sending to the primary (originating) channel, this also fans out
        to every other channel that is mapped to the same room via the
        RoomManager.  This implements the cross-channel broadcast that was
        previously stubbed in MessageBus.set_room_manager().

        Fan-out is skipped when:
          - msg.room_id is None (no room context on the message)
          - Only one channel mapping exists for that room
          - A sibling channel driver is not loaded / enabled
        """
        logger.info("Outbound dispatcher started")

        while True:
            try:
                msg = await asyncio.wait_for(
                    self.bus.consume_outbound(),
                    timeout=1.0
                )

                # ── Primary delivery ──────────────────────────────────────────
                primary_channel = self.channels.get(msg.channel)
                if primary_channel:
                    try:
                        await primary_channel.send(msg)
                    except Exception as e:
                        logger.error(f"Error sending to {msg.channel}: {e}")
                else:
                    logger.warning(f"Unknown channel: {msg.channel}")

                # ── Cross-channel broadcast ───────────────────────────────────
                # Only attempt when the message carries a room_id and we have a
                # room manager to look up sibling channels.
                room_mgr = getattr(self.bus, "_room_manager", None)
                if msg.room_id and room_mgr:
                    try:
                        sibling_mappings = room_mgr.get_channel_mappings_for_room(
                            msg.room_id
                        )
                        for mapping in sibling_mappings:
                            sib_channel = mapping.get("channel")
                            sib_chat_id = mapping.get("chat_id")
                            # Skip the originating channel (already sent above)
                            if sib_channel == msg.channel and sib_chat_id == msg.chat_id:
                                continue
                            driver = self.channels.get(sib_channel)
                            if not driver:
                                continue
                            # Build a copy of the message aimed at the sibling
                            import dataclasses
                            broadcast_msg = dataclasses.replace(
                                msg,
                                channel=sib_channel,
                                chat_id=sib_chat_id,
                            )
                            asyncio.create_task(
                                self._send_broadcast(driver, broadcast_msg)
                            )
                    except Exception as e:
                        logger.warning(f"Cross-channel broadcast error: {e}")

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def _send_broadcast(self, channel, msg) -> None:
        """Send a broadcast copy to a sibling channel (fire-and-forget helper)."""
        try:
            await channel.send(msg)
            logger.debug(
                f"Broadcast delivered to {msg.channel}:{msg.chat_id} "
                f"(room:{msg.room_id})"
            )
        except Exception as e:
            logger.warning(f"Broadcast to {msg.channel} failed: {e}")

    def get_channel(self, name: str) -> BaseChannel | None:
        """Get a channel by name."""
        return self.channels.get(name)

    def get_status(self) -> dict[str, Any]:
        """Get status of all channels."""
        return {
            name: {
                "enabled": True,
                "running": channel.is_running
            }
            for name, channel in self.channels.items()
        }

    @property
    def enabled_channels(self) -> list[str]:
        """Get list of enabled channel names."""
        return list(self.channels.keys())
