"""Invoke tool for delegating tasks to specialist bots.

This tool allows the main agent (nanofolks) to delegate tasks to specialist bots
(researcher, coder, social, creative, auditor). The bot works in the background
and reports results back when complete. The main agent continues immediately.

This is always async - no waiting for results.
"""

from typing import TYPE_CHECKING, Any

from nanofolks.agent.tools.base import Tool

if TYPE_CHECKING:
    from nanofolks.agent.bot_invoker import BotInvoker


class InvokeTool(Tool):
    """
    Tool to invoke specialist bots for specific tasks.

    Use this when a task requires expertise from a specific bot domain:
    - researcher: Research, analysis, information gathering
    - coder: Code implementation, debugging, technical solutions
    - social: Community engagement, communication
    - creative: Creative brainstorming, design, content
    - auditor: Quality review, validation, compliance

    The bot works in the background and reports back when complete.
    """

    def __init__(self, invoker: "BotInvoker"):
        self._invoker = invoker
        self._context: str | None = None
        self._origin_channel: str = "cli"
        self._origin_chat_id: str = "direct"
        self._origin_room_id: str | None = None

    def set_context(self, channel: str, chat_id: str, room_id: str | None = None) -> None:
        """Set conversation context for invocations."""
        self._origin_channel = channel
        self._origin_chat_id = chat_id
        self._origin_room_id = room_id

    @property
    def name(self) -> str:
        return "invoke"

    @property
    def description(self) -> str:
        return (
            "Invoke a specialist bot to handle a task in your domain of expertise. "
            "Use this when you need help from a specific team member. "
            "Available bots: researcher, coder, social, creative, auditor. "
            "The bot will work in background and report results when ready."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "bot": {
                    "type": "string",
                    "description": "Bot to invoke: researcher, coder, social, creative, or auditor",
                    "enum": ["researcher", "coder", "social", "creative", "auditor"],
                },
                "task": {
                    "type": "string",
                    "description": "Task description for the bot",
                },
            },
            "required": ["bot", "task"],
        }

    async def execute(
        self,
        bot: str,
        task: str,
        **kwargs: Any,
    ) -> str:
        """
        Invoke a specialist bot to handle a task.

        The bot works in the background and reports results when complete.
        """
        result = await self._invoker.invoke(
            bot_name=bot,
            task=task,
            context=self._context,
            origin_channel=self._origin_channel,
            origin_chat_id=self._origin_chat_id,
            origin_room_id=self._origin_room_id,
        )

        return result

    def list_available_bots(self) -> dict:
        """List all bots that can be invoked."""
        return self._invoker.list_available_bots()
