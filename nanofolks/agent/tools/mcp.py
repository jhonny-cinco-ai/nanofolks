"""MCP client: connects to MCP servers and wraps their tools as native nanofolks tools."""

from contextlib import AsyncExitStack
from typing import Any

from loguru import logger

from nanofolks.agent.tools.base import Tool
from nanofolks.agent.tools.registry import ToolRegistry


class MCPToolWrapper(Tool):
    """Wraps a single MCP server tool as a nanofolks Tool."""

    def __init__(self, session, server_name: str, tool_def):
        self._session = session
        self._original_name = tool_def.name
        self._name = f"mcp_{server_name}_{tool_def.name}"
        self._description = tool_def.description or tool_def.name
        self._parameters = tool_def.inputSchema or {"type": "object", "properties": {}}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    async def execute(self, **kwargs: Any) -> str:
        from mcp import types

        result = await self._session.call_tool(self._original_name, arguments=kwargs)
        parts = []
        for block in result.content:
            if isinstance(block, types.TextContent):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return "\n".join(parts) or "(no output)"


def _resolve_env_for_mcp(env: dict[str, str] | None) -> dict[str, str] | None:
    """Resolve symbolic references in MCP env vars.

    Allows using {{symbolic_ref}} syntax in env var values which are
    resolved from KeyVault at connection time.

    Example:
        {"OPENAI_API_KEY": "{{openai_key}}"} -> {"OPENAI_API_KEY": "sk-actual-key..."}
    """
    if not env:
        return None

    from nanofolks.security.symbolic_converter import get_symbolic_converter
    converter = get_symbolic_converter()

    resolved = {}
    for key, value in env.items():
        if converter.is_symbolic_ref(value):
            actual_value = converter.resolve(value)
            if actual_value:
                logger.info(f"MCP: resolved {key} from KeyVault")
                resolved[key] = actual_value
            else:
                logger.warning(f"MCP: failed to resolve {key} ({value}), keeping original")
                resolved[key] = value
        else:
            resolved[key] = value

    return resolved if resolved else None


async def connect_mcp_servers(
    mcp_servers: dict, registry: ToolRegistry, stack: AsyncExitStack
) -> None:
    """Connect to configured MCP servers and register their tools."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    for name, cfg in mcp_servers.items():
        try:
            if cfg.command:
                resolved_env = _resolve_env_for_mcp(cfg.env)
                params = StdioServerParameters(
                    command=cfg.command, args=cfg.args, env=resolved_env
                )
                read, write = await stack.enter_async_context(stdio_client(params))
            elif cfg.url:
                from mcp.client.streamable_http import streamable_http_client

                read, write, _ = await stack.enter_async_context(
                    streamable_http_client(cfg.url)
                )
            else:
                logger.warning(
                    f"MCP server '{name}': no command or url configured, skipping"
                )
                continue

            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            tools = await session.list_tools()
            for tool_def in tools.tools:
                wrapper = MCPToolWrapper(session, name, tool_def)
                registry.register(wrapper)
                logger.debug(
                    f"MCP: registered tool '{wrapper.name}' from server '{name}'"
                )

            logger.info(
                f"MCP server '{name}': connected, {len(tools.tools)} tools registered"
            )
        except Exception as e:
            logger.error(f"MCP server '{name}': failed to connect: {e}")
