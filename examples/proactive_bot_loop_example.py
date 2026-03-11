"""Example: Using the ProactiveBotLoop for smart clarification handling.

This example demonstrates how the proactive bot system works:
1. Bot asks clarifying question
2. System waits 10 seconds
3. If no response, proactively decides what to do
4. Decision is based on confidence scoring and historical patterns
"""

import asyncio
from nanofolks.bots.proactive_loop import (
    ProactiveBotLoop,
    IntentHypothesis,
    ProactiveActionType,
)


async def example_proactive_flow():
    """Demonstrate the proactive clarification flow."""

    print("=" * 70)
    print("ProactiveBotLoop Example")
    print("=" * 70)

    # Initialize the proactive loop
    proactive_loop = ProactiveBotLoop(
        timeout_seconds=10.0,  # 10 second timeout
        proactive_enabled=True,
    )

    # Example 1: High confidence scenario
    print("\n📝 Example 1: User asks 'fix the bug'")
    print("-" * 70)

    original_request = "fix the bug"
    clarifying_question = "Which bug are you referring to?"

    # Define possible intents with confidence scores
    possible_intents = [
        IntentHypothesis(
            intent="fix_login_bug",
            confidence=0.85,
            reasoning="User mentioned 'bug' and there's an open login issue (#42)",
            suggested_action="Fix the login authentication bug",
        ),
        IntentHypothesis(
            intent="fix_ui_bug",
            confidence=0.40,
            reasoning="Could be a UI bug, but less likely based on context",
            suggested_action="Fix UI rendering issue",
        ),
    ]

    # Register the clarification
    await proactive_loop.register_clarification(
        room_id="example_room",
        bot_name="coder",
        original_request=original_request,
        clarifying_question=clarifying_question,
        possible_intents=possible_intents,
    )

    print(f"Bot (coder): {clarifying_question}")
    print(f"[System: Waiting 10 seconds for user response...]")
    print(f"[System: Possible intents identified:]")
    for intent in possible_intents:
        print(f"  - {intent.intent}: {intent.confidence:.0%} confidence")

    print(f"\n[After 10 seconds, no response received]")
    print(f"[System: Making proactive decision...]")
    print(f"[Result: PROCEED_WITH_INTENT (confidence: 85%)]")
    print(f"Bot (coder): I'll proceed with fixing the login bug. Let me work on that...")

    # Example 2: Medium confidence scenario
    print("\n\n📝 Example 2: User asks 'update the design'")
    print("-" * 70)

    original_request = "update the design"
    clarifying_question = "Which design file should I update?"

    possible_intents = [
        IntentHypothesis(
            intent="update_homepage_design",
            confidence=0.65,
            reasoning="Homepage design was recently discussed",
            suggested_action="Update homepage mockup",
        ),
        IntentHypothesis(
            intent="update_mobile_design",
            confidence=0.55,
            reasoning="Mobile responsive design needs work",
            suggested_action="Update mobile layout",
        ),
        IntentHypothesis(
            intent="update_logo",
            confidence=0.35,
            reasoning="Less likely based on recent context",
            suggested_action="Update brand logo",
        ),
    ]

    await proactive_loop.register_clarification(
        room_id="example_room_2",
        bot_name="creative",
        original_request=original_request,
        clarifying_question=clarifying_question,
        possible_intents=possible_intents,
    )

    print(f"Bot (creative): {clarifying_question}")
    print(f"[System: Waiting 10 seconds...]")
    print(f"[System: Multiple possible intents with similar confidence]")

    print(f"\n[After 10 seconds, no response received]")
    print(f"[System: Making proactive decision...]")
    print(f"[Result: OFFER_OPTIONS]")
    print(f"Bot (creative): I found a few possibilities:\n")
    print(f"  1. Update homepage mockup (65%)")
    print(f"  2. Update mobile layout (55%)")
    print(f"  3. Update brand logo (35%)\n")
    print(f"Which one did you mean? Or just tell me what you'd like.")

    # Example 3: Low confidence scenario
    print("\n\n📝 Example 3: User asks 'help'")
    print("-" * 70)

    original_request = "help"
    clarifying_question = "What do you need help with?"

    possible_intents = [
        IntentHypothesis(
            intent="technical_help",
            confidence=0.25,
            reasoning="Could be technical, but very vague",
            suggested_action="Provide technical assistance",
        ),
        IntentHypothesis(
            intent="general_help",
            confidence=0.20,
            reasoning="Request is too vague to determine",
            suggested_action="Ask for more details",
        ),
    ]

    await proactive_loop.register_clarification(
        room_id="example_room_3",
        bot_name="leader",
        original_request=original_request,
        clarifying_question=clarifying_question,
        possible_intents=possible_intents,
    )

    print(f"Bot (leader): {clarifying_question}")
    print(f"[System: Waiting 10 seconds...]")
    print(f"[System: Low confidence on all intents - request is very vague]")

    print(f"\n[After 10 seconds, no response received]")
    print(f"[System: Making proactive decision...]")
    print(f"[Result: DEFER_TO_LEADER / Ask different question]")
    print(
        f"Bot (leader): To help you best, could you tell me more specifically what you're working on?"
    )
    print(f"             For example: 'I need help fixing a bug' or 'Help me design the homepage'")

    # Show configuration options
    print("\n\n⚙️  Configuration Options")
    print("-" * 70)
    print("""
You can configure the proactive behavior in your config:

[fleet.proactive]
enabled = true
timeout_seconds = 10.0
high_confidence_threshold = 0.8
medium_confidence_threshold = 0.5
low_confidence_threshold = 0.3
enable_learning = true

# Bot-specific overrides
[fleet.proactive.bot_thresholds]
auditor = 0.9    # Auditor is more cautious
creative = 0.4   # Creative is more proactive
""")

    # Show how user response cancels timeout
    print("\n\n✅ User Response Flow")
    print("-" * 70)
    print("""
If user responds within 10 seconds:

User: "fix the bug"
Bot (coder): "Which bug are you referring to?"
User: "the login one"  ← [Response received within timeout]
[System: Cancels proactive timeout]
Bot (coder): "Got it, I'll fix the login bug!"

The system tracks:
- Whether user responded (for learning)
- What action was taken (if proactive)
- User feedback on proactive decisions (success/failure)
""")

    await proactive_loop.shutdown()
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(example_proactive_flow())
