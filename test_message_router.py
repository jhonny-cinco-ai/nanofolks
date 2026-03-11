#!/usr/bin/env python3
"""Test script for MessageRouter + BotFleet integration.

This script tests the multi-bot architecture by:
1. Initializing BotFleet with multiple bots
2. Starting MessageRouter
3. Sending messages and verifying routing
4. Testing @discuss and other multi-bot features
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from nanofolks.multi_bot_integration import initialize_fleet_architecture
from nanofolks.bus.queue import MessageBus
from nanofolks.bus.events import MessageEnvelope
from nanofolks.config.loader import load_config
from loguru import logger


async def test_message_router():
    """Test the MessageRouter and BotFleet integration."""

    print("=" * 70)
    print("MessageRouter + BotFleet Test")
    print("=" * 70)

    # Load config
    config = load_config()
    print(f"\n✓ Config loaded")
    print(f"  Workspace: {config.workspace_path}")
    print(f"  Model: {config.agents.defaults.model}")

    # Initialize MessageBus
    bus = MessageBus()
    print(f"\n✓ MessageBus initialized")

    # Create LLM provider
    from nanofolks.providers.litellm_provider import LiteLLMProvider

    provider_config = config.get_provider()
    if not provider_config:
        print("✗ No provider configured. Please check your config.")
        return False

    provider = LiteLLMProvider(
        default_model=config.agents.defaults.model,
        api_key=provider_config.api_key,
        api_base=provider_config.api_base,
    )
    print(f"✓ LLM provider created: {config.agents.defaults.model}")

    # Initialize BotFleet + MessageRouter
    print(f"\n→ Initializing BotFleet and MessageRouter...")
    try:
        fleet, router = await initialize_fleet_architecture(
            bus=bus,
            provider=provider,
            workspace=config.workspace_path,
            config=config,
        )
        print(f"✓ BotFleet + MessageRouter initialized")
        print(f"  Auto-start bots: {config.fleet.auto_start_bots}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Start the fleet
    print(f"\n→ Starting BotFleet...")
    try:
        await fleet.start()
        print(f"✓ BotFleet started")
        print(f"  Active bots: {fleet.get_active_bots()}")
    except Exception as e:
        print(f"✗ Failed to start fleet: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Start MessageRouter in background
    print(f"\n→ Starting MessageRouter...")
    router_task = asyncio.create_task(router.run())
    print(f"✓ MessageRouter started (listening)")

    # Give it a moment to start
    await asyncio.sleep(0.5)

    # Test 1: Simple message to leader
    print(f"\n{'=' * 70}")
    print("Test 1: Simple message to leader bot")
    print(f"{'=' * 70}")

    test_msg = MessageEnvelope(
        channel="cli",
        chat_id="test",
        content="Hello, what can you help me with?",
        room_id="general",
        bot_name="user",
    )

    print(f"\nUser: {test_msg.content}")
    print(f"→ Sending to MessageRouter...")

    # Send message
    await bus.publish_inbound(test_msg)

    # Wait for response (with timeout)
    print(f"→ Waiting for response (30s timeout)...")
    try:
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=30.0)
        print(f"\n✓ Response received!")
        print(f"  Bot: {response.bot_name}")
        print(f"  Content: {response.content[:200]}...")
    except asyncio.TimeoutError:
        print(f"\n✗ Timeout waiting for response")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Message with @discuss
    print(f"\n{'=' * 70}")
    print("Test 2: @discuss trigger (multi-bot discussion)")
    print(f"{'=' * 70}")

    discuss_msg = MessageEnvelope(
        channel="cli",
        chat_id="test",
        content="@discuss What do you all think about the new architecture?",
        room_id="general",
        bot_name="user",
    )

    print(f"\nUser: {discuss_msg.content}")
    print(f"→ Sending to MessageRouter...")

    await bus.publish_inbound(discuss_msg)

    # Collect multiple responses (SmartDiscuss might trigger multiple bots)
    # With streaming, responses arrive as each bot finishes processing
    print(f"→ Waiting for streaming responses (45s total timeout)...")
    print(f"  (Responses will appear as each bot replies)\n")
    responses = []
    start_time = asyncio.get_event_loop().time()
    total_timeout = 45.0  # Total time to wait for all responses

    try:
        # Wait for first response (this takes longest due to LLM evaluation)
        first_response_timeout = 20.0
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=first_response_timeout)
        responses.append(response)
        print(f"  💬 {response.bot_name}: {response.content[:200]}...")
        print(f"     (First response received, waiting for more...)\n")

        # Collect additional responses with shorter timeouts
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining = total_timeout - elapsed

            if remaining <= 0:
                break

            # Short timeout for subsequent responses
            try:
                response = await asyncio.wait_for(
                    bus.consume_outbound(), timeout=min(3.0, remaining)
                )
                responses.append(response)
                print(f"  💬 {response.bot_name}: {response.content[:200]}...")
            except asyncio.TimeoutError:
                # No more responses coming
                break

        print(
            f"\n✓ Collected {len(responses)} response(s) from {len(set(r.bot_name for r in responses))} bot(s)"
        )

    except asyncio.TimeoutError:
        if responses:
            print(f"\n✓ Collected {len(responses)} response(s) (timeout waiting for more)")
        else:
            print(f"\n✗ No responses received (timeout waiting for first response)")
            return False

    # Test 3: Direct bot mention
    print(f"\n{'=' * 70}")
    print("Test 3: Direct bot mention (@coder)")
    print(f"{'=' * 70}")

    if "coder" in fleet.get_active_bots():
        direct_msg = MessageEnvelope(
            channel="cli",
            chat_id="test",
            content="@coder Help me refactor this function",
            room_id="general",
            bot_name="user",
        )

        print(f"\nUser: {direct_msg.content}")
        print(f"→ Sending to MessageRouter...")

        await bus.publish_inbound(direct_msg)

        print(f"→ Waiting for response (10s timeout)...")
        try:
            response = await asyncio.wait_for(bus.consume_outbound(), timeout=10.0)
            print(f"\n✓ Response received!")
            print(f"  Bot: {response.bot_name}")
            print(f"  Content: {response.content[:200]}...")
        except asyncio.TimeoutError:
            print(f"\n✗ Timeout waiting for response")
    else:
        print(f"\n⚠ Skipping (coder bot not active)")

    # Test 4: Proactive loop
    print(f"\n{'=' * 70}")
    print("Test 4: Proactive clarification (if triggered)")
    print(f"{'=' * 70}")

    vague_msg = MessageEnvelope(
        channel="cli",
        chat_id="test",
        content="Fix it",
        room_id="general",
        bot_name="user",
    )

    print(f"\nUser: {vague_msg.content}")
    print(f"→ Sending to MessageRouter...")

    await bus.publish_inbound(vague_msg)

    print(f"→ Waiting for response...")
    try:
        response = await asyncio.wait_for(bus.consume_outbound(), timeout=10.0)
        print(f"\n✓ Response received!")
        print(f"  Bot: {response.bot_name}")
        print(f"  Content: {response.content[:200]}...")

        # Check if it's a clarifying question
        if "?" in response.content:
            print(f"\n⚠ Bot asked a clarifying question")
            print(f"→ Waiting 12 seconds to test proactive loop...")
            await asyncio.sleep(12)

            # Check if proactive message was sent (wait up to 2 seconds)
            try:
                proactive = await asyncio.wait_for(bus.consume_outbound(), timeout=2.0)
                print(f"\n✓ Proactive message received!")
                print(f"  Bot: {proactive.bot_name}")
                print(f"  Content: {proactive.content[:200]}...")
            except asyncio.TimeoutError:
                print(f"\n⚠ No proactive message (might be expected)")
    except asyncio.TimeoutError:
        print(f"\n✗ Timeout waiting for response")

    # Cleanup
    print(f"\n{'=' * 70}")
    print("Cleanup")
    print(f"{'=' * 70}")

    print(f"\n→ Stopping MessageRouter...")
    await router.stop()
    router_task.cancel()
    try:
        await router_task
    except asyncio.CancelledError:
        pass
    print(f"✓ MessageRouter stopped")

    print(f"\n→ Stopping BotFleet...")
    await fleet.stop()
    print(f"✓ BotFleet stopped")

    print(f"\n{'=' * 70}")
    print("Test Complete!")
    print(f"{'=' * 70}")

    return True


async def main():
    """Main entry point."""
    logger.remove()  # Remove default logger
    logger.add(sys.stderr, level="INFO")  # Add simple console output

    try:
        success = await test_message_router()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
