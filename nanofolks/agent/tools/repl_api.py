"""
REPL API Surfaces - API wrappers for REPL environment.

This module provides API classes that wrap nanofolks functionality
for use in the REPL environment. All APIs are room-scoped.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from nanofolks.agent.tools.registry import ToolRegistry
    from nanofolks.agent.bot_invoker import BotInvoker
    from nanofolks.agent.tools.repl_manager import REPLStateManager
    from nanofolks.memory.store import TurboMemoryStore
    from nanofolks.session.manager import RoomSessionManager


class ToolAPI:
    """
    Tools API for REPL.

    Provides access to all registered tools (web, file, shell, etc.)
    through a simple interface.

    Example:
        from tools import web, file, shell

        results = web.search("OpenClaw")
        content = file.read("~/project/README.md")
        output = shell.exec("ls -la")
    """

    def __init__(self, registry: "ToolRegistry", room_id: Optional[str] = None):
        """
        Initialize Tools API.

        Args:
            registry: Tool registry with all registered tools
            room_id: Room ID for room-scoped operations
        """
        self._registry = registry
        self._room_id = room_id

        # Create sub-modules for organization
        self.web = WebToolsAPI(registry)
        self.file = FileToolsAPI(registry)
        self.shell = ShellToolsAPI(registry)
        self.browser = BrowserToolsAPI(registry)
        self.mcp = MCPToolsAPI(registry)

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> str:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool
            params: Tool parameters

        Returns:
            Tool execution result
        """
        return await self._registry.execute(tool_name, params)

    def list_tools(self) -> List[str]:
        """List all available tools."""
        return self._registry.tool_names

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists."""
        return self._registry.has(name)

    def _run_async(self, coro):
        """Run async coroutine in executor (for sync access in REPL)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a new loop in a thread
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)


class WebToolsAPI:
    """Web-related tools (search, scrape, etc.) - sync version for REPL."""

    def __init__(self, registry: "ToolRegistry"):
        self._registry = registry

    def _run_sync(self, coro):
        """Run async coroutine synchronously."""
        import asyncio

        return asyncio.run(coro)

    def search(self, query: str, limit: int = 5) -> str:
        """Search the web (sync version for REPL)."""
        return self._run_sync(
            self._registry.execute(
                "web_search",
                {"query": query, "limit": limit},
            )
        )

    async def search_async(self, query: str, limit: int = 5) -> str:
        """Search the web (async version)."""
        return await self._registry.execute(
            "web_search",
            {"query": query, "limit": limit},
        )

    def scrape(self, url: str) -> str:
        """Scrape a webpage (sync version for REPL)."""
        return self._run_sync(self._registry.execute("scrape_url", {"url": url}))

    async def scrape_async(self, url: str) -> str:
        """Scrape a webpage (async version)."""
        return await self._registry.execute("scrape_url", {"url": url})

    def fetch(self, url: str) -> str:
        """Fetch URL content (alias for scrape)."""
        return self.scrape(url)


class FileToolsAPI:
    """File-related tools (read, write, list, etc.) - sync version for REPL."""

    def __init__(self, registry: "ToolRegistry"):
        self._registry = registry

    def _run_sync(self, coro):
        """Run async coroutine synchronously."""
        import asyncio

        return asyncio.run(coro)

    def read(self, path: str) -> str:
        """Read a file (sync version for REPL)."""
        return self._run_sync(self._registry.execute("read_file", {"path": path}))

    async def read_async(self, path: str) -> str:
        """Read a file (async version)."""
        return await self._registry.execute("read_file", {"path": path})

    def write(self, path: str, content: str) -> str:
        """Write to a file (sync version for REPL)."""
        return self._run_sync(
            self._registry.execute("write_file", {"path": path, "content": content})
        )

    async def write_async(self, path: str, content: str) -> str:
        """Write to a file (async version)."""
        return await self._registry.execute("write_file", {"path": path, "content": content})

    def list(self, path: str) -> str:
        """List directory contents (sync version for REPL)."""
        return self._run_sync(self._registry.execute("list_dir", {"path": path}))

    async def list_async(self, path: str) -> str:
        """List directory contents (async version)."""
        return await self._registry.execute("list_dir", {"path": path})

    def edit(self, path: str, edits: List[Dict[str, str]]) -> str:
        """Edit a file with multiple edits (sync version for REPL)."""
        return self._run_sync(self._registry.execute("edit_file", {"path": path, "edits": edits}))

    async def edit_async(self, path: str, edits: List[Dict[str, str]]) -> str:
        """Edit a file with multiple edits (async version)."""
        return await self._registry.execute("edit_file", {"path": path, "edits": edits})


class ShellToolsAPI:
    """Shell execution tools - sync version for REPL."""

    def __init__(self, registry: "ToolRegistry"):
        self._registry = registry

    def _run_sync(self, coro):
        """Run async coroutine synchronously."""
        import asyncio

        return asyncio.run(coro)

    def exec(self, command: str, timeout: int = 30) -> str:
        """Execute a shell command (sync version for REPL)."""
        return self._run_sync(
            self._registry.execute("shell", {"command": command, "timeout": timeout})
        )

    async def exec_async(self, command: str, timeout: int = 30) -> str:
        """Execute a shell command (async version)."""
        return await self._registry.execute("shell", {"command": command, "timeout": timeout})

    def run(self, command: str) -> str:
        """Run a shell command (alias for exec)."""
        return self.exec(command)


class BrowserToolsAPI:
    """Browser automation tools - sync version for REPL."""

    def __init__(self, registry: "ToolRegistry"):
        self._registry = registry

    def _run_sync(self, coro):
        """Run async coroutine synchronously."""
        import asyncio

        return asyncio.run(coro)

    def open(self, url: str) -> str:
        """Open URL in browser (sync version for REPL)."""
        return self._run_sync(self._registry.execute("browser_navigate", {"url": url}))

    async def open_async(self, url: str) -> str:
        """Open URL in browser (async version)."""
        return await self._registry.execute("browser_navigate", {"url": url})

    def click(self, selector: str) -> str:
        """Click element (sync version for REPL)."""
        return self._run_sync(self._registry.execute("browser_click", {"selector": selector}))

    async def click_async(self, selector: str) -> str:
        """Click element (async version)."""
        return await self._registry.execute("browser_click", {"selector": selector})

    def type_text(self, selector: str, text: str) -> str:
        """Type text into element (sync version for REPL)."""
        return self._run_sync(
            self._registry.execute("browser_type", {"selector": selector, "text": text})
        )

    async def type_text_async(self, selector: str, text: str) -> str:
        """Type text into element (async version)."""
        return await self._registry.execute("browser_type", {"selector": selector, "text": text})

    def screenshot(self) -> str:
        """Take screenshot (sync version for REPL)."""
        return self._run_sync(self._registry.execute("browser_screenshot", {}))

    async def screenshot_async(self) -> str:
        """Take screenshot (async version)."""
        return await self._registry.execute("browser_screenshot", {})


class MCPToolsAPI:
    """
    MCP (Model Context Protocol) tools API for REPL.

    Provides access to MCP server tools. MCP tools are registered with
    names starting with "mcp_" (e.g., mcp_github_search).

    Example:
        from tools import mcp

        # List available MCP tools
        mcp_tools = mcp.list()

        # Check if an MCP tool is available
        if mcp.has("github_search"):
            result = mcp.call("github_search", query="openclaw")
    """

    def __init__(self, registry: "ToolRegistry"):
        self._registry = registry

    def list(self) -> List[str]:
        """List all available MCP tools (tools starting with mcp_)."""
        return [name for name in self._registry.tool_names if name.startswith("mcp_")]

    def has(self, tool_name: str) -> bool:
        """Check if an MCP tool is available.

        Args:
            tool_name: Tool name without mcp_ prefix (e.g., "github_search")
                       or with prefix (e.g., "mcp_github_search")
        """
        # Normalize name
        if not tool_name.startswith("mcp_"):
            tool_name = f"mcp_{tool_name}"
        return self._registry.has(tool_name)

    async def call(self, tool_name: str, **kwargs: Any) -> str:
        """Call an MCP tool by name.

        Args:
            tool_name: Tool name (with or without mcp_ prefix)
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        # Normalize name
        if not tool_name.startswith("mcp_"):
            tool_name = f"mcp_{tool_name}"
        return await self._registry.execute(tool_name, kwargs)

    async def connect(self, server_name: str) -> str:
        """Connect to an MCP server.

        Note: This triggers the connection process but the tool may not
        be immediately available. Check with mcp.list() after calling.

        Args:
            server_name: Name of the MCP server to connect to

        Returns:
            Connection status message
        """
        return await self._registry.execute("connect_mcp_server", {"server_name": server_name})


class BotAPI:
    """
    Bot coordination API for REPL.

    Provides access to multi-bot coordination (invoke, list, has).
    Uses BotInvoker to delegate tasks to specialist bots.

    Example:
        from bots import coordinator

        result = coordinator.invoke("researcher", "Find info on OpenClaw")
        bots = coordinator.list_bots()
    """

    def __init__(self, invoker: "BotInvoker", room_id: Optional[str] = None):
        """
        Initialize Bot API.

        Args:
            invoker: BotInvoker instance for invoking specialist bots
            room_id: Room ID for room-scoped operations
        """
        self._invoker = invoker
        self._room_id = room_id

    async def invoke(
        self,
        bot_name: str,
        task: str,
        context: Optional[str] = None,
    ) -> str:
        """
        Invoke a specialist bot to handle a task.

        The bot works in the background and reports results back when complete.
        This is always async - the main agent continues immediately.

        Args:
            bot_name: Name of the bot (e.g., "researcher", "coder", "social", "creative", "auditor")
            task: Task description for the bot
            context: Additional context from the main conversation

        Returns:
            Confirmation message that the bot was invoked
        """
        logger.debug(f"REPL BotAPI: Invoking {bot_name}")
        return await self._invoker.invoke(
            bot_role=bot_name,
            task=task,
            context=context,
            origin_channel="repl",
            origin_chat_id="repl",
            origin_room_id=self._room_id,
        )

    async def invoke_many(
        self,
        bots: List[str],
        task: str,
        context: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Invoke multiple specialist bots in parallel.

        Args:
            bots: List of bot names to invoke
            task: Task description for the bots
            context: Additional context

        Returns:
            Dict of bot_name → invocation confirmation
        """
        import asyncio

        logger.debug(f"REPL BotAPI: Invoking {len(bots)} bots")

        async def invoke_one(bot: str) -> tuple[str, str]:
            result = await self.invoke(bot, task, context)
            return bot, result

        results = await asyncio.gather(*[invoke_one(b) for b in bots])
        return dict(results)

    def list_bots(self) -> List[str]:
        """List available bots."""
        from nanofolks.agent.bot_invoker import AVAILABLE_BOTS

        return list(AVAILABLE_BOTS.keys())

    def has_bot(self, name: str) -> bool:
        """Check if a bot exists."""
        from nanofolks.agent.bot_invoker import AVAILABLE_BOTS

        return name in AVAILABLE_BOTS


class REPLToolsAPI:
    """
    REPL management API for introspection and control.

    Example:
        from repl import list_variables, reset, get_history, get_stats

        vars = list_variables()
        reset()
        history = get_history()
        stats = get_stats()
    """

    def __init__(
        self,
        repl_manager: "REPLStateManager",
        room_id: Optional[str] = None,
    ):
        """
        Initialize REPL Tools API.

        Args:
            repl_manager: REPL state manager
            room_id: Room ID for room-scoped operations
        """
        self._repl_manager = repl_manager
        self._room_id = room_id

    def _get_state(self):
        """Get REPL state for current room."""
        room_id = self._room_id or "general"
        return self._repl_manager.get_state(room_id)

    def list_variables(self) -> Dict[str, str]:
        """List current variables in REPL state."""
        return self._get_state().list_variables()

    def reset(self) -> str:
        """Reset REPL state (clear all variables)."""
        self._get_state().reset()
        return "REPL state reset"

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history."""
        return [
            {
                "success": h.success,
                "output": h.output,
                "error": h.error,
                "execution_time_ms": h.execution_time_ms,
            }
            for h in self._get_state().get_history(limit)
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get REPL statistics."""
        return self._get_state().get_stats()

    def save_snapshot(self) -> Dict[str, Any]:
        """Save current REPL state as snapshot."""
        return self._get_state().save_snapshot()

    def restore_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Restore REPL state from snapshot."""
        success = self._get_state().restore_snapshot(snapshot)
        return "Restored" if success else "Failed"


class MemoryAPI:
    """
    Memory API for REPL (room-scoped).

    All memory operations are automatically scoped to the current room.

    Example:
        from memory import search, store, recent

        results = search("project X", limit=5)
        store("important_key", {"data": "value"}, tags=["important"])
        recent_items = recent(days=7)
    """

    def __init__(
        self,
        memory_store: Optional["TurboMemoryStore"] = None,
        room_id: Optional[str] = None,
    ):
        """
        Initialize Memory API.

        Args:
            memory_store: Memory store instance
            room_id: Room ID for room-scoped operations
        """
        self._store = memory_store
        self._room_id = room_id

    async def search(
        self,
        query: str,
        limit: int = 10,
        room_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search memory.

        Args:
            query: Search query
            limit: Maximum results
            room_id: Override room ID (optional)

        Returns:
            List of matching memories
        """
        if not self._store:
            return [{"error": "Memory store not available"}]

        effective_room = room_id or self._room_id
        logger.debug(f"REPL MemoryAPI: Searching for '{query}' in room {effective_room}")

        return await self._store.search(
            query=query,
            room_id=effective_room,
            limit=limit,
        )

    async def store(
        self,
        key: str,
        value: Any,
        tags: Optional[List[str]] = None,
        room_id: Optional[str] = None,
    ) -> str:
        """
        Store in memory.

        Args:
            key: Storage key
            value: Value to store
            tags: Optional tags
            room_id: Override room ID (optional)

        Returns:
            Success message
        """
        if not self._store:
            return "Error: Memory store not available"

        effective_room = room_id or self._room_id
        logger.debug(f"REPL MemoryAPI: Storing '{key}' in room {effective_room}")

        await self._store.store(
            key=key,
            value=value,
            tags=tags or [],
            room_id=effective_room,
        )
        return f"Stored: {key}"

    async def load(
        self,
        key: str,
        room_id: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Load from memory.

        Args:
            key: Storage key
            room_id: Override room ID (optional)

        Returns:
            Stored value or None
        """
        if not self._store:
            return None

        effective_room = room_id or self._room_id
        logger.debug(f"REPL MemoryAPI: Loading '{key}' from room {effective_room}")

        return await self._store.load(
            key=key,
            room_id=effective_room,
        )

    async def recent(
        self,
        days: int = 7,
        room_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent memories.

        Args:
            days: Number of days to look back
            room_id: Override room ID (optional)

        Returns:
            List of recent memories
        """
        if not self._store:
            return []

        effective_room = room_id or self._room_id
        logger.debug(f"REPL MemoryAPI: Getting recent memories from room {effective_room}")

        return await self._store.get_recent(
            days=days,
            room_id=effective_room,
        )

    async def associate(
        self,
        key: str,
        tags: List[str],
        room_id: Optional[str] = None,
    ) -> str:
        """
        Associate memory with tags.

        Args:
            key: Storage key
            tags: Tags to associate
            room_id: Override room ID (optional)

        Returns:
            Success message
        """
        if not self._store:
            return "Error: Memory store not available"

        effective_room = room_id or self._room_id
        await self._store.associate_tags(
            key=key,
            tags=tags,
            room_id=effective_room,
        )
        return f"Associated: {key} with {tags}"


class SessionAPI:
    """
    Session API for REPL (room-scoped).

    Access current session context and history.

    Example:
        from session import history, context

        recent = history(limit=10)
        ctx = context()
    """

    def __init__(
        self,
        session_manager: Optional["RoomSessionManager"] = None,
        room_id: Optional[str] = None,
    ):
        """
        Initialize Session API.

        Args:
            session_manager: Session manager instance
            room_id: Room ID for room-scoped operations
        """
        self._session_manager = session_manager
        self._room_id = room_id

    async def history(
        self,
        limit: int = 10,
        room_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent session history.

        Args:
            limit: Maximum messages
            room_id: Override room ID (optional)

        Returns:
            List of recent messages
        """
        if not self._session_manager:
            return []

        effective_room = room_id or self._room_id
        logger.debug(f"REPL SessionAPI: Getting history for room {effective_room}")

        session = self._session_manager.get_session(effective_room)
        if session:
            return session.get_history(max_messages=limit)
        return []

    async def context(
        self,
        room_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get current session context.

        Args:
            room_id: Override room ID (optional)

        Returns:
            Session context or None
        """
        if not self._session_manager:
            return None

        effective_room = room_id or self._room_id
        logger.debug(f"REPL SessionAPI: Getting context for room {effective_room}")

        session = self._session_manager.get_session(effective_room)
        if session:
            return session.get_context()
        return None


class SkillsAPI:
    """
    Skills API for REPL.

    Access and compose skills.

    Example:
        from skills import load, compose, run

        load("web-research")
        workflow = compose(["web-research", "summarize"])
        result = run(workflow, "Research OpenClaw")
    """

    def __init__(self, room_id: Optional[str] = None):
        """
        Initialize Skills API.

        Args:
            room_id: Room ID for room-scoped operations
        """
        self._room_id = room_id
        self._loaded_skills: Dict[str, Any] = {}

    def load(self, skill_name: str) -> str:
        """
        Load a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            Success message
        """
        # TODO: Implement skill loading
        logger.debug(f"REPL SkillsAPI: Loading skill '{skill_name}'")
        self._loaded_skills[skill_name] = True
        return f"Loaded: {skill_name}"

    def compose(self, skills: List[str]) -> str:
        """
        Compose multiple skills.

        Args:
            skills: List of skill names

        Returns:
            Workflow ID
        """
        # TODO: Implement skill composition
        logger.debug(f"REPL SkillsAPI: Composing {len(skills)} skills")
        return f"workflow-{len(skills)}"

    async def run(self, workflow: str, input_data: Any) -> str:
        """
        Run a workflow.

        Args:
            workflow: Workflow ID
            input_data: Input data

        Returns:
            Workflow result
        """
        # TODO: Implement workflow execution
        logger.debug(f"REPL SkillsAPI: Running workflow '{workflow}'")
        return f"Result for: {input_data}"

    def list_skills(self) -> List[str]:
        """List loaded skills."""
        return list(self._loaded_skills.keys())


def create_api_instances(
    room_id: str,
    tools_registry: Optional["ToolRegistry"] = None,
    bot_invoker: Optional["BotInvoker"] = None,
    memory_store: Optional["TurboMemoryStore"] = None,
    session_manager: Optional["RoomSessionManager"] = None,
    repl_manager: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Create API instances for a room.

    This is a factory function used by REPLStateManager.

    Args:
        room_id: Room identifier
        tools_registry: Tool registry
        bot_invoker: BotInvoker for invoking specialist bots
        memory_store: Memory store
        session_manager: Session manager
        repl_manager: REPL state manager

    Returns:
        Dict of API instances
    """
    instances = {}

    if tools_registry:
        instances["tools"] = ToolAPI(tools_registry, room_id)

    if bot_invoker:
        instances["bots"] = BotAPI(bot_invoker, room_id)

    if memory_store:
        instances["memory"] = MemoryAPI(memory_store, room_id)

    if session_manager:
        instances["session"] = SessionAPI(session_manager, room_id)

    if repl_manager:
        instances["repl"] = REPLToolsAPI(repl_manager, room_id)

    # Always create skills API
    instances["skills"] = SkillsAPI(room_id)

    return instances
