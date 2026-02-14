"""Invoke tool for delegating tasks to specialist bots.

This tool allows the main agent (nanobot) to synchronously invoke
specialist bots (researcher, coder, social, creative, auditor) and
wait for their responses.
"""

from typing import Any, TYPE_CHECKING

from nanobot.agent.tools.base import Tool

if TYPE_CHECKING:
    from nanobot.agent.bot_invoker import BotInvoker


class InvokeTool(Tool):
    """
    Tool to invoke specialist bots for specific tasks.
    
    Use this when a task requires expertise from a specific bot domain:
    - researcher: Research, analysis, information gathering
    - coder: Code implementation, debugging, technical solutions
    - social: Community engagement, communication
    - creative: Creative brainstorming, design, content
    - auditor: Quality review, validation, compliance
    
    The invoked bot will process the task and return its response.
    """
    
    def __init__(self, invoker: "BotInvoker"):
        self._invoker = invoker
        self._context: str | None = None
    
    def set_context(self, context: str) -> None:
        """Set conversation context for invocations."""
        self._context = context
    
    @property
    def name(self) -> str:
        return "invoke"
    
    @property
    def description(self) -> str:
        return (
            "Invoke a specialist bot to handle a task in your domain of expertise. "
            "Use this when you need help from a specific team member. "
            "The bot will process the task and return its response. "
            "Available bots: researcher, coder, social, creative, auditor."
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
    
    async def execute(self, bot: str, task: str, **kwargs: Any) -> str:
        """
        Invoke a specialist bot to handle a task.
        
        Args:
            bot: Bot name to invoke
            task: Task description
            
        Returns:
            Bot's response to the task
        """
        result = await self._invoker.invoke(
            bot_name=bot,
            task=task,
            context=self._context,
        )
        
        # Format result nicely
        bot_info = self._invoker.get_bot_info(bot)
        bot_title = bot_info.get("default_name", bot) if bot_info else bot
        
        return f"@{bot} ({bot_title}) response:\n\n{result}"
    
    def list_available_bots(self) -> dict:
        """List all bots that can be invoked."""
        return self._invoker.list_available_bots()
