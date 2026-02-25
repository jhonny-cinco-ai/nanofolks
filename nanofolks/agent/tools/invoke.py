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
        self._memory_store = None

    def set_context(self, channel: str, chat_id: str, room_id: str | None = None) -> None:
        """Set conversation context for invocations."""
        self._origin_channel = channel
        self._origin_chat_id = chat_id
        self._origin_room_id = room_id

    def set_memory_store(self, memory_store) -> None:
        """Attach a memory store for logging task events."""
        self._memory_store = memory_store

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
        room_task_id = None
        if self._origin_room_id:
            try:
                from nanofolks.bots.room_manager import get_room_manager

                manager = get_room_manager()
                room = manager.get_room(self._origin_room_id)
                if room:
                    room_task = room.add_task(
                        title=task,
                        owner=bot,
                        status="in_progress",
                        metadata={
                            "source": "invoke",
                            "invoked_by": "leader",
                            "subtasks": [],
                        },
                    )
                    room_task.add_handoff("leader", bot, reason="Leader assigned task")
                    manager._save_room(room)
                    room_task_id = room_task.id
                    self._log_task_event(self._origin_room_id, "add", room_task, reason="Leader assigned task")
            except Exception:
                room_task_id = None

        result = await self._invoker.invoke(
            bot_role=bot,
            task=task,
            context=self._context,
            origin_channel=self._origin_channel,
            origin_chat_id=self._origin_chat_id,
            origin_room_id=self._origin_room_id,
            room_task_id=room_task_id,
        )

        return result

    def _log_task_event(self, room_id: str | None, action: str, task: Any, reason: str | None = None) -> None:
        if not self._memory_store or not room_id:
            return
        try:
            import uuid
            from datetime import datetime

            from nanofolks.memory.models import Event
            from nanofolks.utils.ids import room_to_session_id

            metadata = {
                "task_id": task.id,
                "action": action,
                "owner": task.owner,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date,
            }
            if reason:
                metadata["reason"] = reason

            content = (
                f"Task {action}: {task.title} "
                f"(owner: {task.owner}, status: {task.status})"
            )

            event = Event(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                channel="internal",
                direction="internal",
                event_type="task",
                content=content,
                session_key=room_to_session_id(room_id),
                metadata=metadata,
            )
            self._memory_store.save_event(event)
        except Exception:
            return

    def list_available_bots(self) -> dict:
        """List all bots that can be invoked."""
        return self._invoker.list_available_bots()
