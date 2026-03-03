"""
REPL Tool - Programmable Python environment tool.

This tool provides a single entry point for the agent to execute
arbitrary Python code with access to tools, bots, memory, and skills.

Based on Witan Labs REPL Tool pattern:
https://github.com/witanlabs/research-log/blob/main/06-repl-tool.md
"""

from typing import Any, Dict, Optional

from loguru import logger

from nanofolks.agent.tools.base import Tool
from nanofolks.agent.tools.repl_manager import REPLStateManager


class REPLTool(Tool):
    """
    Single tool with persistent Python environment.

    The REPL tool allows the agent to execute arbitrary Python code
    with access to a rich API surface (tools, bots, memory, skills).
    State persists across calls within the same room.

    Key features:
    - Single tool instead of many discrete tools
    - State persistence (variables survive across calls)
    - Room-scoped isolation
    - Sandboxed execution

    Example usage in agent:
        # Execute Python code
        result = await repl.execute(code='''
            from tools import web
            from memory import store

            url = web.search("OpenClaw")[0].url
            html = web.scrape(url)
            store("openclaw_html", html)
            print(f"Saved {len(html)} chars")
        ''')

    Security:
    - Code runs in RestrictedPython sandbox
    - No filesystem/network access
    - 90-second timeout
    - 20K character output limit
    """

    @property
    def name(self) -> str:
        """Tool name."""
        return "repl"

    @property
    def description(self) -> str:
        """Tool description."""
        return """Execute arbitrary Python code with access to tools, bots, memory, and skills.

This is a programmable environment where you can:
- Execute multi-step operations in a single call
- Compose tools, bots, and memory operations
- Store intermediate results in variables
- Use loops, conditionals, and functions

Available APIs:
- tools: Tool API (tools.web.search(), tools.file.read(), etc.)
- bots: Bot API (bots.invoke(), bots.invoke_many(), bots.list_bots(), bots.has_bot())
- memory: Memory API (memory.search(), memory.store(), memory.recent())
- skills: Skills API (skills.load(), skills.compose(), skills.run())
- session: Session API (session.history(), session.context())

State persists across calls in the same room.

Management Actions (use action parameter):
- list_variables: Show current variables in REPL state
- reset: Clear all variables, start fresh
- get_history: Show recent execution history
- get_stats: Show REPL statistics
- save_snapshot: Save current state for later
- restore_snapshot: Restore from saved snapshot

Example:
    # Invoke specialist bot
    from bots import coordinator
    result = coordinator.invoke("researcher", "Find info on OpenClaw")
    print(result)

    # Multi-step research
    from tools import web
    from memory import store
    
    url = web.search("OpenClaw")[0].url
    html = web.scrape(url)
    store("openclaw_research", html)
    print(f"Saved {len(html)} chars from {url}")

Security: 90s timeout, 20K char output limit, no filesystem/network access."""

    @property
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Can use tools, bots, memory, skills, and session APIs.",
                },
                "action": {
                    "type": "string",
                    "enum": [
                        "list_variables",
                        "reset",
                        "get_history",
                        "get_stats",
                        "save_snapshot",
                        "restore_snapshot",
                    ],
                    "description": "REPL management action (alternative to code)",
                },
                "room_id": {
                    "type": "string",
                    "description": "Room ID (uses default if not provided)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Limit for history/stats actions (default: 10)",
                },
                "snapshot": {
                    "type": "object",
                    "description": "Snapshot data for restore_snapshot action",
                },
            },
        }

    def __init__(
        self,
        repl_manager: REPLStateManager,
        room_id: Optional[str] = None,
    ):
        """
        Initialize REPL tool.

        Args:
            repl_manager: REPL state manager (provides room-scoped state)
            room_id: Default room ID (can be overridden in execute)
        """
        self._repl_manager = repl_manager
        self._default_room_id = room_id

        logger.debug(f"REPLTool initialized with default room: {room_id}")

    async def execute(self, **kwargs: Any) -> str:
        """
        Execute Python code or REPL management actions in the environment.

        Args:
            code: Python code to execute
            action: Optional action (list_variables, reset, get_history, get_stats, save_snapshot, restore_snapshot)
            room_id: Optional room ID (uses default if not provided)
            limit: Limit for history/stats actions
            snapshot: Snapshot data for restore_snapshot action

        Returns:
            Execution result as string
        """
        action = kwargs.get("action")
        code = kwargs.get("code", "")
        room_id = kwargs.get("room_id") or self._default_room_id
        limit = kwargs.get("limit", 10)
        snapshot = kwargs.get("snapshot")

        if not room_id:
            return "Error: No room ID available"

        state = self._repl_manager.get_state(room_id)

        if action:
            return await self._handle_action(action, state, limit, snapshot)

        if not code:
            return "Error: No code provided"

        logger.info(f"REPLTool: Executing {len(code)} chars in room {room_id}")
        result = await state.execute(code)

        return result

    async def _handle_action(
        self,
        action: str,
        state: Any,
        limit: int = 10,
        snapshot: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Handle REPL management actions."""
        import json

        if action == "list_variables":
            variables = state.list_variables()
            if not variables:
                return "No variables in REPL state"
            lines = [f"{name}: {vtype}" for name, vtype in sorted(variables.items())]
            return "Variables:\n" + "\n".join(lines)

        elif action == "reset":
            state.reset()
            return "REPL state reset successfully"

        elif action == "get_history":
            history = state.get_history(limit)
            if not history:
                return "No execution history"
            lines = []
            for i, h in enumerate(history):
                status = "✓" if h.success else "✗"
                lines.append(f"{i + 1}. {status} ({h.execution_time_ms}ms): {h.output[:50]}...")
            return "History:\n" + "\n".join(lines)

        elif action == "get_stats":
            stats = state.get_stats()
            lines = [f"{k}: {v}" for k, v in stats.items()]
            return "Stats:\n" + "\n".join(lines)

        elif action == "save_snapshot":
            snap = state.save_snapshot()
            return f"Snapshot saved: {len(snap.get('variables', {}))} variables"

        elif action == "restore_snapshot":
            if not snapshot:
                return "Error: No snapshot provided"
            success = state.restore_snapshot(snapshot)
            return "Snapshot restored" if success else "Failed to restore snapshot"

        return f"Unknown action: {action}"

    def validate_params(self, params: Dict[str, Any]) -> list[str]:
        """
        Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if "code" not in params:
            errors.append("Missing required parameter: code")
        elif not isinstance(params["code"], str):
            errors.append("Parameter 'code' must be a string")
        elif not params["code"].strip():
            errors.append("Parameter 'code' cannot be empty")

        return errors

    def to_schema(self) -> Dict[str, Any]:
        """
        Generate OpenAI function schema for this tool.

        Returns:
            OpenAI function definition
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def __repr__(self) -> str:
        return f"REPLTool(default_room={self._default_room_id!r})"


def create_repl_tool(
    room_id: str,
    tools_registry: Optional[Any] = None,
    bot_invoker: Optional[Any] = None,
    memory_store: Optional[Any] = None,
    session_manager: Optional[Any] = None,
    sandbox_timeout: float = 90.0,
    sandbox_max_output_chars: int = 20000,
) -> REPLTool:
    """
    Factory function to create a REPL tool with all dependencies.

    This is a convenience function for creating a fully-configured REPL tool.

    Args:
        room_id: Default room ID
        tools_registry: Tool registry
        bot_invoker: BotInvoker for invoking specialist bots
        memory_store: Memory store
        session_manager: Session manager
        sandbox_timeout: Sandbox timeout in seconds
        sandbox_max_output_chars: Maximum output characters

    Returns:
        Configured REPLTool instance
    """
    from nanofolks.agent.tools.repl_api import create_api_instances
    from nanofolks.agent.tools.repl_manager import REPLStateManager

    # Create API factory
    def api_factory(rid: str) -> Dict[str, Any]:
        return create_api_instances(
            room_id=rid,
            tools_registry=tools_registry,
            bot_invoker=bot_invoker,
            memory_store=memory_store,
            session_manager=session_manager,
        )

    # Create manager
    manager = REPLStateManager(
        api_factory=api_factory,
        sandbox_timeout=sandbox_timeout,
        sandbox_max_output_chars=sandbox_max_output_chars,
    )

    # Create tool
    return REPLTool(repl_manager=manager, room_id=room_id)
