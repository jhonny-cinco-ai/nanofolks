"""Example: SmartDiscuss with LLM-based urgency evaluation.

This example demonstrates how SmartDispatch uses the local Apple Intelligence
model (or any configured LLM) to evaluate which bots should respond.
"""

import asyncio
from pathlib import Path

from nanofolks.bots.smart_dispatch import SmartDispatch
from nanofolks.bots.room_manager import RoomManager
from nanofolks.providers.factory import create_provider
from nanofolks.config.loader import load_config


async def example_smart_discuss_with_llm():
    """Example: User asks about design canvas - which bots should respond?"""

    # Setup
    config = load_config()
    workspace = Path.home() / "nanofolks"
    provider = create_provider(config)  # This could be Apple Intelligence, Ollama, etc.

    room_manager = RoomManager(workspace)

    # Create a room with multiple bots
    room = room_manager.create_room(
        room_id="design-project",
        participants=["leader", "creative", "coder", "researcher", "auditor"],
    )

    # Create SmartDispatch with LLM
    smart_dispatch = SmartDispatch(
        room_manager=room_manager,
        llm_provider=provider,  # ← Uses local Apple LLM!
        speak_threshold=0.5,
        use_llm=True,
    )

    # Example 1: Nuanced design question
    print("=" * 60)
    print("Example 1: Nuanced Design Question")
    print("=" * 60)

    message = "I'm trying to understand how color theory works, what could be best option for our design canvas app"

    print(f"\nUser: {message}\n")
    print("SmartDispatch evaluating with LLM...\n")

    result = await smart_dispatch.dispatch_smart_discuss(
        message=message,
        room_id="design-project",
    )

    print(f"Selected bots: {result.primary_bot}", end="")
    if result.secondary_bots:
        print(f" + {', '.join(result.secondary_bots)}")
    else:
        print()
    print(f"Reason: {result.reason}\n")

    # Expected LLM evaluation:
    # creative: 0.90 - "Color theory and design expertise essential"
    # coder: 0.75 - "Canvas implementation needs technical knowledge"
    # researcher: 0.60 - "Could research user preferences"
    # leader: 0.50 - "Strategic input valuable"
    # auditor: 0.20 - "Accessibility review not immediately needed"

    # Example 2: Technical architecture question
    print("\n" + "=" * 60)
    print("Example 2: Technical Architecture Question")
    print("=" * 60)

    message2 = "Should we use PostgreSQL or MongoDB for our user data storage?"

    print(f"\nUser: {message2}\n")
    print("SmartDispatch evaluating with LLM...\n")

    result2 = await smart_dispatch.dispatch_smart_discuss(
        message=message2,
        room_id="design-project",
    )

    print(f"Selected bots: {result2.primary_bot}", end="")
    if result2.secondary_bots:
        print(f" + {', '.join(result2.secondary_bots)}")
    else:
        print()
    print(f"Reason: {result2.reason}\n")

    # Expected LLM evaluation:
    # coder: 0.95 - "Database choice is technical implementation"
    # researcher: 0.70 - "Could analyze data structure requirements"
    # leader: 0.60 - "Strategic technology decision"
    # creative: 0.20 - "Not relevant to design"
    # auditor: 0.40 - "Data security considerations"

    # Example 3: Security question
    print("\n" + "=" * 60)
    print("Example 3: Security Question")
    print("=" * 60)

    message3 = "We're thinking of letting users upload files to the canvas. Any concerns?"

    print(f"\nUser: {message3}\n")
    print("SmartDispatch evaluating with LLM...\n")

    result3 = await smart_dispatch.dispatch_smart_discuss(
        message=message3,
        room_id="design-project",
    )

    print(f"Selected bots: {result3.primary_bot}", end="")
    if result3.secondary_bots:
        print(f" + {', '.join(result3.secondary_bots)}")
    else:
        print()
    print(f"Reason: {result3.reason}\n")

    # Expected LLM evaluation:
    # auditor: 0.95 - "File uploads have major security implications"
    # coder: 0.80 - "Implementation needs security considerations"
    # leader: 0.70 - "Risk assessment needed"
    # creative: 0.30 - "UX impact minimal"
    # researcher: 0.40 - "User behavior research could help"


async def example_comparison():
    """Compare LLM-based vs Rule-based evaluation."""

    config = load_config()
    workspace = Path.home() / "nanofolks"
    provider = create_provider(config)

    room_manager = RoomManager(workspace)
    room = room_manager.create_room(
        room_id="test",
        participants=["leader", "creative", "coder", "researcher"],
    )

    message = "How should we implement collaborative editing in the canvas?"

    print("=" * 60)
    print("Comparison: LLM vs Rule-Based")
    print("=" * 60)
    print(f"\nMessage: {message}\n")

    # LLM-based
    print("--- LLM-Based Evaluation ---")
    llm_dispatch = SmartDispatch(
        room_manager=room_manager,
        llm_provider=provider,
        speak_threshold=0.5,
        use_llm=True,
    )

    llm_result = await llm_dispatch.dispatch_smart_discuss(message, "test")
    print(f"Selected: {llm_result.primary_bot}", end="")
    if llm_result.secondary_bots:
        print(f" + {', '.join(llm_result.secondary_bots)}")
    print(f"Reason: {llm_result.reason}\n")

    # Rule-based
    print("--- Rule-Based Evaluation ---")
    rule_dispatch = SmartDispatch(
        room_manager=room_manager,
        llm_provider=None,  # No LLM
        speak_threshold=0.5,
        use_llm=False,
    )

    rule_result = await rule_dispatch.dispatch_smart_discuss(message, "test")
    print(f"Selected: {rule_result.primary_bot}", end="")
    if rule_result.secondary_bots:
        print(f" + {', '.join(rule_result.secondary_bots)}")
    print(f"Reason: {rule_result.reason}\n")

    print("Key Differences:")
    print("- LLM understands 'collaborative editing' implies real-time tech (coder)")
    print("- LLM understands 'canvas' implies design (creative)")
    print("- Rule-based only matches keywords 'canvas' → creative")
    print("- Rule-based misses 'collaborative' and 'editing' nuances")


if __name__ == "__main__":
    print("SmartDispatch with LLM Examples")
    print("=" * 60)
    print()

    # Run examples
    asyncio.run(example_smart_discuss_with_llm())

    print("\n" + "=" * 60)
    print()

    asyncio.run(example_comparison())
