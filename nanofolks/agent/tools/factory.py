"""Factory for creating bot-specific tool registries.

This module provides utilities to create tool registries for specialist bots
with appropriate permissions based on their SOUL.md/AGENTS.md configuration.
"""

from pathlib import Path
from typing import Any, Optional

from nanofolks.agent.tools import ToolRegistry
from nanofolks.agent.tools.permissions import (
    filter_registry,
    get_permissions_from_agents,
    get_permissions_from_soul,
    merge_permissions,
)
from nanofolks.config.schema import ExecToolConfig


def create_bot_registry(
    workspace: Path,
    bot_name: str,
    provider: Optional[Any] = None,
    bus: Optional[Any] = None,
    invoker: Optional[Any] = None,
    brave_api_key: Optional[str] = None,
    web_config: Optional[Any] = None,
    browser_config: Optional[Any] = None,
    exec_config: Optional[ExecToolConfig] = None,
    restrict_to_workspace: bool = False,
    base_registry: Optional[ToolRegistry] = None,
    evolutionary: bool = False,
    allowed_paths: Optional[list[str]] = None,
    protected_paths: Optional[list[str]] = None,
    content_store: Optional[Any] = None,
    cron_service: Optional[Any] = None,
    system_timezone: str = "UTC",
    memory_store: Optional[Any] = None,
    memory_retrieval: Optional[Any] = None,
    canceller: Optional[callable] = None,
    repl_manager: Optional[Any] = None,
    room_id: Optional[str] = None,
    nto_config: Optional[Any] = None,
) -> ToolRegistry:
    """Create a tool registry for a specialist bot.

    This function:
    1. Loads tool permissions from bot's SOUL.md/AGENTS.md
    2. Creates a base tool registry with standard tools
    3. Filters tools based on permissions

    Args:
        workspace: Path to workspace
        bot_name: Name of the bot
        provider: LLM provider
        bus: Message bus
        invoker: Bot invoker
        brave_api_key: API key for web search
        web_config: Configuration for web tools
        browser_config: Configuration for browser tool
        exec_config: Execution config for shell tool
        restrict_to_workspace: Whether to restrict file ops to workspace
        base_registry: Optional pre-created registry to filter
        evolutionary: Whether evolutionary mode is enabled
        allowed_paths: Allowed paths for evolutionary mode
        protected_paths: Protected paths for evolutionary mode
        content_store: Store for fetched content
        cron_service: Service for scheduled routines
        system_timezone: Timezone for routines
        memory_store: Memory store for context retrieval
        memory_retrieval: Memory retrieval system
        canceller: Callback to cancel room tasks
        repl_manager: REPL state manager for REPL tool
        room_id: Room ID for REPL tool
        nto_config: NTO configuration for token optimization

    Returns:
        Filtered ToolRegistry for the bot
    """
    # Get permissions
    soul_perms = get_permissions_from_soul(bot_name, workspace)
    agents_perms = get_permissions_from_agents(bot_name, workspace)
    permissions = merge_permissions(soul_perms, agents_perms)

    # If no special permissions, create default registry
    if not permissions.allowed_tools and not permissions.denied_tools:
        if base_registry:
            return base_registry
        return create_default_registry(
            workspace=workspace,
            provider=provider,
            bus=bus,
            invoker=invoker,
            brave_api_key=brave_api_key,
            web_config=web_config,
            browser_config=browser_config,
            exec_config=exec_config,
            restrict_to_workspace=restrict_to_workspace,
            evolutionary=evolutionary,
            allowed_paths=allowed_paths,
            protected_paths=protected_paths,
            content_store=content_store,
            cron_service=cron_service,
            system_timezone=system_timezone,
            memory_store=memory_store,
            memory_retrieval=memory_retrieval,
            canceller=canceller,
            repl_manager=repl_manager,
            room_id=room_id,
            nto_config=nto_config,
        )

    # Create base registry and filter
    base = base_registry or create_default_registry(
        workspace=workspace,
        provider=provider,
        bus=bus,
        invoker=invoker,
        brave_api_key=brave_api_key,
        web_config=web_config,
        browser_config=browser_config,
        exec_config=exec_config,
        restrict_to_workspace=restrict_to_workspace,
        evolutionary=evolutionary,
        allowed_paths=allowed_paths,
        protected_paths=protected_paths,
        content_store=content_store,
        cron_service=cron_service,
        system_timezone=system_timezone,
        memory_store=memory_store,
        memory_retrieval=memory_retrieval,
        canceller=canceller,
        repl_manager=repl_manager,
        room_id=room_id,
        nto_config=nto_config,
    )

    return filter_registry(base, permissions)


def create_default_registry(
    workspace: Path,
    provider: Optional[Any] = None,
    bus: Optional[Any] = None,
    invoker: Optional[Any] = None,
    brave_api_key: Optional[str] = None,
    web_config: Optional[Any] = None,
    browser_config: Optional[Any] = None,
    exec_config: Optional[ExecToolConfig] = None,
    restrict_to_workspace: bool = False,
    evolutionary: bool = False,
    allowed_paths: Optional[list[str]] = None,
    protected_paths: Optional[list[str]] = None,
    content_store: Optional[Any] = None,
    cron_service: Optional[Any] = None,
    system_timezone: str = "UTC",
    memory_store: Optional[Any] = None,
    memory_retrieval: Optional[Any] = None,
    canceller: Optional[callable] = None,
    repl_manager: Optional[Any] = None,
    room_id: Optional[str] = None,
    nto_config: Optional[Any] = None,
) -> ToolRegistry:
    """Create a default tool registry with all standard tools.

    Args:
        workspace: Path to workspace
        provider: LLM provider
        bus: Message bus for message tool
        invoker: Bot invoker for delegation
        brave_api_key: API key for web search
        web_config: Configuration for web tools
        browser_config: Configuration for browser tool
        exec_config: Execution config for shell tool
        restrict_to_workspace: Whether to restrict file ops to workspace
        evolutionary: Whether evolutionary mode is enabled
        allowed_paths: Allowed paths for evolutionary mode
        protected_paths: Protected paths for evolutionary mode
        content_store: Store for fetched content
        cron_service: Service for scheduled routines
        system_timezone: Timezone for routines
        memory_store: Memory store for context retrieval
        memory_retrieval: Memory retrieval system
        canceller: Callback to cancel room tasks
        repl_manager: REPL state manager for REPL tool
        room_id: Room ID for REPL tool
        nto_config: NTO configuration for token optimization

    Returns:
        ToolRegistry with default tools
    """
    registry = ToolRegistry()

    # Import tools
    from nanofolks.agent.tools.filesystem import (
        EditFileTool,
        ListDirTool,
        ReadFileTool,
        WriteFileTool,
    )
    from nanofolks.agent.tools.shell import ExecTool
    from nanofolks.agent.tools.room_tasks import RoomTaskTool
    from nanofolks.agent.tools.web import WebFetchTool, WebSearchTool
    from nanofolks.agent.tools.browser import AgentBrowserTool
    from nanofolks.agent.tools.message import MessageTool
    from nanofolks.agent.tools.update_config import UpdateConfigTool
    from nanofolks.agent.tools.routines import RoutinesTool

    # File tools
    default_protected = [str(Path.home() / ".nanofolks" / "config.json")]
    all_protected = list(set((protected_paths or []) + default_protected))
    protected_dirs = [Path(p).expanduser().resolve() for p in all_protected]

    if evolutionary and allowed_paths:
        allowed_dirs = [Path(p).expanduser().resolve() for p in allowed_paths]
        registry.register(ReadFileTool(allowed_paths=allowed_dirs, protected_paths=protected_dirs))
        registry.register(WriteFileTool(allowed_paths=allowed_dirs, protected_paths=protected_dirs))
        registry.register(EditFileTool(allowed_paths=allowed_dirs, protected_paths=protected_dirs))
        registry.register(ListDirTool(allowed_paths=allowed_dirs, protected_paths=protected_dirs))

        registry.register(
            ExecTool(
                working_dir=str(workspace),
                timeout=exec_config.timeout if exec_config else 60,
                allowed_paths=allowed_paths,
            )
        )
    else:
        allowed_dir = workspace if restrict_to_workspace else None
        registry.register(ReadFileTool(allowed_dir=allowed_dir, protected_paths=protected_dirs))
        registry.register(WriteFileTool(allowed_dir=allowed_dir, protected_paths=protected_dirs))
        registry.register(EditFileTool(allowed_dir=allowed_dir, protected_paths=protected_dirs))
        registry.register(ListDirTool(allowed_dir=allowed_dir, protected_paths=protected_dirs))

        registry.register(
            ExecTool(
                working_dir=str(workspace),
                timeout=exec_config.timeout if exec_config else 60,
                restrict_to_workspace=restrict_to_workspace,
            )
        )

    # Web tools
    registry.register(WebSearchTool(api_key=brave_api_key, nto_config=nto_config))
    registry.register(
        WebFetchTool(
            scrapling_enabled=bool(getattr(web_config, "scrapling_enabled", False)),
            scrapling_min_chars=int(getattr(web_config, "scrapling_min_chars", 800)),
            scrapling_mode=str(getattr(web_config, "scrapling_mode", "auto")),
            content_store=content_store,
            nto_config=nto_config,
        )
    )

    # Markdown conversion
    from nanofolks.agent.tools.markdown_convert import MarkdownNewTool

    registry.register(MarkdownNewTool())

    # Content access tool
    from nanofolks.agent.tools.content import ReadFetchedContentTool

    registry.register(ReadFetchedContentTool(content_store=content_store))

    # Browser tool
    if getattr(browser_config, "enabled", False):
        registry.register(
            AgentBrowserTool(
                binary=getattr(browser_config, "binary", "agent-browser"),
                allowlist=getattr(browser_config, "allowlist", []),
            )
        )

    # Message tool - enabled for legitimate communication
    if bus:
        registry.register(MessageTool(send_callback=bus.publish_outbound))

    # Invoke tool - enabled for bot delegation when appropriate
    if invoker:
        from nanofolks.agent.tools.invoke import InvokeTool

        registry.register(InvokeTool(invoker=invoker))

    # Room task tool - DISABLED (was causing infinite task loops)
    # room_task_tool = RoomTaskTool()
    # if canceller:
    #     room_task_tool.set_canceller(canceller)
    # registry.register(room_task_tool)

    # Config update - enabled for legitimate configuration changes
    registry.register(UpdateConfigTool())

    # Memory tools
    if memory_store and memory_retrieval:
        from nanofolks.agent.tools.memory import create_memory_tools

        memory_tools = create_memory_tools(memory_store, memory_retrieval, nto_config=nto_config)
        for tool in memory_tools:
            registry.register(tool)

    # Security tools - enabled but with anti-panic guardrails in prompts
    from nanofolks.agent.tools.security import create_security_tools

    security_tools = create_security_tools()
    for tool in security_tools:
        registry.register(tool)

    # REPL tool (programmable Python environment) - enabled for coding tasks
    if repl_manager is not None and room_id:
        from nanofolks.agent.tools.repl import REPLTool

        registry.register(REPLTool(repl_manager=repl_manager, room_id=room_id))

    return registry

    return registry


def get_tool_definitions_for_bot(
    workspace: Path,
    bot_name: str,
    base_definitions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Get filtered tool definitions for a bot based on permissions.

    Args:
        workspace: Path to workspace
        bot_name: Name of the bot
        base_definitions: Full list of tool definitions

    Returns:
        Filtered list of tool definitions
    """
    soul_perms = get_permissions_from_soul(bot_name, workspace)
    agents_perms = get_permissions_from_agents(bot_name, workspace)
    permissions = merge_permissions(soul_perms, agents_perms)

    if not permissions.allowed_tools and not permissions.denied_tools:
        return base_definitions

    filtered = []
    for tool_def in base_definitions:
        tool_name = tool_def.get("function", {}).get("name", "")
        if permissions.is_allowed(tool_name):
            # Apply custom description if present
            custom_desc = permissions.get_custom_description(tool_name)
            if custom_desc:
                tool_def = {
                    "type": "function",
                    "function": {
                        **tool_def.get("function", {}),
                        "description": custom_desc,
                    },
                }
            filtered.append(tool_def)

    return filtered
