"""Heartbeat control tool for managing bot heartbeats via chat.

This tool allows the coordinator (leader bot) to enable, disable, start, stop,
and check status of specialist bot heartbeats through conversation.
"""

import asyncio
from typing import Any

from nanofolks.agent.tools.base import Tool


class HeartbeatControlTool(Tool):
    """
    Control heartbeat services for specialist bots.
    
    Use this to manage which bots have active background heartbeat services:
    - Enable/disable: Turns heartbeat on/off (persists across restarts)
    - Start/stop: Starts/stops the currently running heartbeat service
    
    Available bots: researcher, coder, social, creative, auditor
    Coordinator (leader) always has heartbeat enabled.
    """

    @property
    def name(self) -> str:
        return "heartbeat_control"

    @property
    def description(self) -> str:
        return (
            "Control heartbeat services for specialist bots. "
            "Use this to activate background tasks for bots or check their status. "
            "Available bots: researcher, coder, social, creative, auditor. "
            "Actions: enable, disable, start, stop, status, list"
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["enable", "disable", "start", "stop", "status", "list"],
                },
                "bot": {
                    "type": "string",
                    "description": "Bot name (researcher, coder, social, creative, auditor). Required for all actions except 'list'",
                    "enum": ["researcher", "coder", "social", "creative", "auditor"],
                },
            },
            "required": ["action"],
        }

    async def execute(
        self,
        action: str,
        bot: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute heartbeat control action."""
        from nanofolks.cli.heartbeat_commands import get_heartbeat_manager

        manager = get_heartbeat_manager()

        if manager is None:
            return "Error: Heartbeat manager not initialized. The bot team is not running."

        if action == "list":
            return await self._list_bots(manager)

        if not bot:
            return "Error: Bot name is required for this action."

        bot = bot.lower()

        if action == "enable":
            return await self._enable_heartbeat(manager, bot)
        elif action == "disable":
            return await self._disable_heartbeat(manager, bot)
        elif action == "start":
            return await self._start_heartbeat(manager, bot)
        elif action == "stop":
            return await self._stop_heartbeat(manager, bot)
        elif action == "status":
            return await self._get_status(manager, bot)
        else:
            return f"Unknown action: {action}"

    async def _list_bots(self, manager) -> str:
        """List all bots and their heartbeat status."""
        lines = ["Available bots and their heartbeat status:\n"]

        for bot_name, bot in manager._bots.items():
            status = bot.get_heartbeat_status()
            enabled = status.get("enabled", "unknown")
            running = status.get("running", False)

            enabled_str = "enabled" if enabled else "disabled"
            running_str = "running" if running else "stopped"

            lines.append(f"- @{bot_name}: {enabled_str}, {running_str}")

        return "\n".join(lines)

    async def _enable_heartbeat(self, manager, bot_name: str) -> str:
        """Enable heartbeat config for a bot."""
        bot = manager.get_bot(bot_name)
        if not bot:
            return f"Error: Bot '{bot_name}' not found."

        if bot._heartbeat_config is None:
            return f"Error: Bot '{bot_name}' has no heartbeat configuration."

        if bot._heartbeat_config.enabled:
            return f"@{bot_name}'s heartbeat is already enabled."

        bot._heartbeat_config.enabled = True

        try:
            await bot.start_heartbeat()
            return f"✅ Enabled and started heartbeat for @{bot_name}"
        except Exception as e:
            return f"✅ Enabled @{bot_name}'s heartbeat config, but failed to start: {e}"

    async def _disable_heartbeat(self, manager, bot_name: str) -> str:
        """Disable heartbeat config for a bot."""
        bot = manager.get_bot(bot_name)
        if not bot:
            return f"Error: Bot '{bot_name}' not found."

        if bot._heartbeat_config is None:
            return f"Error: Bot '{bot_name}' has no heartbeat configuration."

        if not bot._heartbeat_config.enabled:
            return f"@{bot_name}'s heartbeat is already disabled."

        if bot.is_heartbeat_running:
            bot.stop_heartbeat()

        bot._heartbeat_config.enabled = False

        return f"✅ Disabled heartbeat for @{bot_name}"

    async def _start_heartbeat(self, manager, bot_name: str) -> str:
        """Start heartbeat for a bot."""
        bot = manager.get_bot(bot_name)
        if not bot:
            return f"Error: Bot '{bot_name}' not found."

        if bot.is_heartbeat_running:
            return f"@{bot_name}'s heartbeat is already running."

        if bot._heartbeat_config and not bot._heartbeat_config.enabled:
            bot._heartbeat_config.enabled = True

        try:
            await bot.start_heartbeat()
            return f"✅ Started heartbeat for @{bot_name}"
        except Exception as e:
            return f"Error starting @{bot_name}'s heartbeat: {e}"

    async def _stop_heartbeat(self, manager, bot_name: str) -> str:
        """Stop heartbeat for a bot."""
        bot = manager.get_bot(bot_name)
        if not bot:
            return f"Error: Bot '{bot_name}' not found."

        if not bot.is_heartbeat_running:
            return f"@{bot_name}'s heartbeat is not running."

        bot.stop_heartbeat()
        return f"✅ Stopped heartbeat for @{bot_name}"

    async def _get_status(self, manager, bot_name: str) -> str:
        """Get heartbeat status for a Bot."""
        bot = manager.get_bot(bot_name)
        if not bot:
            return f"Error: Bot '{bot_name}' not found."

        status = bot.get_heartbeat_status()

        enabled = bot._heartbeat_config.enabled if bot._heartbeat_config else False
        running = status.get("running", False)
        interval_min = status.get("interval_min", "unknown")
        checks_count = status.get("checks_count", 0)

        history = status.get("history", {})
        total_ticks = history.get("total_ticks", 0)
        success_rate = history.get("success_rate", "N/A")

        lines = [
            f"@{bot_name} Heartbeat Status:",
            f"  Enabled: {'Yes' if enabled else 'No'}",
            f"  Running: {'Yes' if running else 'No'}",
            f"  Interval: {interval_min} minutes" if isinstance(interval_min, int) else f"  Interval: {interval_min}",
            f"  Checks: {checks_count}",
            f"  Total ticks: {total_ticks}",
            f"  Success rate: {success_rate}" if isinstance(success_rate, str) else f"  Success rate: {success_rate:.1%}",
        ]

        return "\n".join(lines)
