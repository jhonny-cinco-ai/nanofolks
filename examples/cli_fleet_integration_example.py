"""Example CLI integration with multi-bot fleet architecture.

This file demonstrates how to integrate the new multi-bot fleet architecture
into the existing CLI. This is an example/reference implementation.

To use in production, adapt this code into nanofolks/cli/chat.py
"""

import asyncio
from pathlib import Path

from loguru import logger

from nanofolks.multi_bot_integration import (
    initialize_fleet_architecture,
    shutdown_fleet_architecture,
    should_use_fleet_architecture,
)


async def run_chat_with_fleet_architecture(config, workspace, provider):
    """Run chat using the new multi-bot fleet architecture.

    This is the new entry point that uses the fleet architecture instead
    of the legacy single-bot AgentLoop.

    Args:
        config: Configuration object
        workspace: Path to workspace
        provider: LLM provider
    """
    logger.info("Starting chat with multi-bot fleet architecture")

    # Initialize fleet and router
    fleet, router = await initialize_fleet_architecture(
        config=config,
        workspace=workspace,
        provider=provider,
    )

    try:
        # Start the router in a background task
        router_task = asyncio.create_task(router.run())

        # Run the CLI interaction loop
        await run_cli_loop(router)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        # Graceful shutdown
        logger.info("Shutting down...")
        router_task.cancel()
        try:
            await router_task
        except asyncio.CancelledError:
            pass

        await shutdown_fleet_architecture(fleet, router, save_sessions=True)


async def run_cli_loop(router):
    """Run the CLI interaction loop.

    Args:
        router: MessageRouter instance
    """
    print("🤖 nanofolks Multi-Bot Chat")
    print("Type 'exit' or 'quit' to exit")
    print("Use @botname to message a specific bot")
    print("Use @all to message all bots")
    print("Use @team to message relevant bots\n")

    current_room = "general"

    while True:
        try:
            # Get user input
            user_input = input(f"[{current_room}] > ").strip()

            if not user_input:
                continue

            # Check for exit
            if user_input.lower() in ["exit", "quit", "/exit", "/quit"]:
                print("Goodbye! 👋")
                break

            # Check for room switch command
            if user_input.startswith("/room "):
                new_room = user_input[6:].strip()
                current_room = new_room
                router.set_current_room(new_room)
                print(f"Switched to room: {new_room}")
                continue

            # Check for fleet stats command
            if user_input == "/status":
                stats = router.get_stats()
                print(f"\n📊 Fleet Status:")
                print(f"  Active bots: {stats['bot_count']}")
                print(f"  Bots: {', '.join(stats['active_bots'])}")
                print(f"  Current room: {stats['current_room_id']}")
                print()
                continue

            # Create message envelope
            from nanofolks.bus.events import MessageEnvelope

            msg = MessageEnvelope(
                content=user_input,
                room_id=current_room,
                channel="cli",
                chat_id="cli-session",
            )

            # Route message through fleet
            print("Thinking...")
            response = await router.route_message(msg)

            if response:
                # Print response
                print(f"\n{response.content}\n")

                # Show which bots responded (if multi-bot)
                if response.metadata and response.metadata.get("multi_bot"):
                    bots = response.metadata.get("responding_bots", [])
                    print(f"💬 Responded: {', '.join(bots)}\n")
            else:
                print("No response received\n")

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit\n")
            continue
        except Exception as e:
            logger.error(f"Error in CLI loop: {e}")
            print(f"❌ Error: {e}\n")


async def run_legacy_chat(config, workspace, provider):
    """Run chat using legacy single-bot architecture.

    This maintains backward compatibility with the existing system.

    Args:
        config: Configuration object
        workspace: Path to workspace
        provider: LLM provider
    """
    from nanofolks.agent.loop import AgentLoop
    from nanofolks.bus.queue import MessageBus

    logger.info("Starting chat with legacy single-bot architecture")

    bus = MessageBus()

    agent = AgentLoop(
        bot_name="leader",
        bus=bus,
        provider=provider,
        workspace=workspace,
        model=config.agents.defaults.model,
        temperature=config.agents.defaults.temperature,
        max_tokens=config.agents.defaults.max_tokens,
        brave_api_key=config.tools.web_search.brave_api_key,
        exec_config=config.tools.exec,
        evolutionary=config.agents.defaults.evolutionary,
        restrict_to_workspace=config.agents.defaults.restrict_to_workspace,
        routing_config=config.routing,
        memory_config=config.memory,
        mcp_servers=config.tools.mcp_servers,
        bot_mcp_servers=config.agents.mcp_servers,
        sidekick_config=getattr(config.tools, "sidekick", None),
        web_config=getattr(config.tools, "web", None),
        browser_config=getattr(config.tools, "browser", None),
        document_config=getattr(config.tools, "document", None),
    )

    # Run the agent
    await agent.run()


async def main():
    """Main entry point with architecture selection."""
    from nanofolks.config.loader import load_config
    from nanofolks.providers.factory import create_provider

    # Load configuration
    config = load_config()
    workspace = config.workspace_path

    # Create provider
    provider = create_provider(config)

    # Check which architecture to use
    if should_use_fleet_architecture(config):
        # Use new multi-bot fleet architecture
        await run_chat_with_fleet_architecture(config, workspace, provider)
    else:
        # Use legacy single-bot architecture
        await run_legacy_chat(config, workspace, provider)


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
