"""ProactiveBotLoop: Timeout-based proactive decision making for multi-bot system.

This module implements a proactive clarification system where:
1. Bot asks clarifying question when request is ambiguous
2. Waits for user response (default: 10 seconds)
3. If no response, proactively decides how to proceed
4. Integrates with TurboMemory for learning from decisions

Usage:
    proactive_loop = ProactiveBotLoop(fleet_manager, turbo_memory)
    await proactive_loop.handle_clarification_state(room_id, bot_name, question)
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger


class ProactiveActionType(Enum):
    """Types of proactive actions when timeout occurs."""

    PROCEED_WITH_INTENT = "proceed_with_intent"  # Execute best guess
    OFFER_OPTIONS = "offer_options"  # Present multiple choices
    ASK_DIFFERENT_QUESTION = "ask_different_question"  # Try alternate question
    DEFER_TO_LEADER = "defer_to_leader"  # Escalate to leader bot
    PROVIDE_CONTEXT = "provide_context"  # Show context without acting


@dataclass
class IntentHypothesis:
    """A possible interpretation of user intent."""

    intent: str
    confidence: float  # 0.0-1.0
    reasoning: str
    suggested_action: Optional[str] = None


@dataclass
class ProactiveAction:
    """Action to take when proactive timeout triggers."""

    action_type: ProactiveActionType
    confidence: float
    message: str
    options: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClarificationState:
    """State tracking for clarification requests."""

    room_id: str
    bot_name: str
    original_request: str
    clarifying_question: str
    timestamp: float
    possible_intents: List[IntentHypothesis]
    context_hash: str
    timeout_seconds: float = 10.0
    confidence_threshold: float = 0.7
    proactive_enabled: bool = True

    def is_expired(self) -> bool:
        """Check if clarification has timed out."""
        return time.time() - self.timestamp > self.timeout_seconds

    def time_remaining(self) -> float:
        """Get remaining time before timeout."""
        remaining = self.timeout_seconds - (time.time() - self.timestamp)
        return max(0.0, remaining)


@dataclass
class ProactiveLearning:
    """Learning data from proactive decisions."""

    room_id: str
    bot_name: str
    original_request: str
    clarifying_question: str
    selected_action: ProactiveActionType
    confidence: float
    user_corrected: Optional[bool] = None
    user_follow_up: Optional[str] = None
    success: Optional[bool] = None
    timestamp: float = field(default_factory=time.time)


class ProactiveDecisionEngine:
    """Engine for making proactive decisions when user doesn't respond.

    Uses confidence scoring and historical patterns to decide:
    - Whether to proceed with best guess
    - Whether to offer options
    - Whether to escalate to leader
    """

    def __init__(
        self,
        turbo_memory=None,
        high_threshold: float = 0.8,
        medium_threshold: float = 0.5,
        low_threshold: float = 0.3,
        config=None,
    ):
        """Initialize the decision engine.

        Args:
            turbo_memory: Optional TurboMemory for historical context
            high_threshold: Threshold for proceeding with intent (default: 0.8)
            medium_threshold: Threshold for offering options (default: 0.5)
            low_threshold: Threshold for alternate question (default: 0.3)
            config: Optional configuration with bot_thresholds
        """
        self.turbo_memory = turbo_memory
        self.HIGH_CONFIDENCE = high_threshold
        self.MEDIUM_CONFIDENCE = medium_threshold
        self.LOW_CONFIDENCE = low_threshold
        self.config = config
        self.logger = logger.bind(component="ProactiveDecisionEngine")

    async def decide_on_timeout(
        self,
        state: ClarificationState,
        room_history: List[Dict[str, Any]],
    ) -> ProactiveAction:
        """Decide what to do when clarification times out.

        Args:
            state: Current clarification state
            room_history: Recent room message history

        Returns:
            ProactiveAction with decision
        """
        self.logger.info(f"Making proactive decision for {state.bot_name} in room {state.room_id}")

        # Score confidence of possible intents
        scored_intents = await self._score_intents(state, room_history)

        if not scored_intents:
            # No clear intents - defer to leader
            return ProactiveAction(
                action_type=ProactiveActionType.DEFER_TO_LEADER,
                confidence=0.0,
                message=f"I'm not sure what you need. Let me get {state.bot_name}'s leader to help.",
            )

        # Get highest confidence intent
        best_intent = scored_intents[0]

        # Decision logic based on confidence
        if best_intent.confidence >= self.HIGH_CONFIDENCE:
            # High confidence - proceed with best guess
            return await self._create_proceed_action(state, best_intent)

        elif best_intent.confidence >= self.MEDIUM_CONFIDENCE:
            # Medium confidence - offer top 2-3 options
            return await self._create_options_action(state, scored_intents[:3])

        elif best_intent.confidence >= self.LOW_CONFIDENCE:
            # Low confidence - try different question
            return await self._create_alternate_question_action(state, best_intent)

        else:
            # Very low confidence - defer to leader
            return ProactiveAction(
                action_type=ProactiveActionType.DEFER_TO_LEADER,
                confidence=best_intent.confidence,
                message="I'm having trouble understanding what you need. Let me get help.",
                metadata={"best_intent": best_intent.intent},
            )

    async def _score_intents(
        self,
        state: ClarificationState,
        room_history: List[Dict[str, Any]],
    ) -> List[IntentHypothesis]:
        """Score possible intents based on context and history.

        Returns:
            List of scored intents (sorted by confidence, highest first)
        """
        scored = []

        for intent in state.possible_intents:
            # Base confidence from intent hypothesis
            confidence = intent.confidence

            # Boost based on historical success
            historical_boost = await self._get_historical_boost(
                state.room_id, state.bot_name, intent.intent
            )
            confidence = min(1.0, confidence + historical_boost)

            # Boost based on context similarity
            context_boost = self._calculate_context_boost(intent, room_history)
            confidence = min(1.0, confidence + context_boost)

            # Adjust based on bot personality
            personality_adjustment = self._get_personality_adjustment(state.bot_name, intent.intent)
            confidence = max(0.0, min(1.0, confidence + personality_adjustment))

            scored.append(
                IntentHypothesis(
                    intent=intent.intent,
                    confidence=confidence,
                    reasoning=intent.reasoning,
                    suggested_action=intent.suggested_action,
                )
            )

        # Sort by confidence (highest first)
        scored.sort(key=lambda x: x.confidence, reverse=True)

        return scored

    async def _get_historical_boost(
        self,
        room_id: str,
        bot_name: str,
        intent: str,
    ) -> float:
        """Get confidence boost based on historical success patterns.

        Returns:
            Boost value (-0.1 to +0.2)
        """
        if not self.turbo_memory:
            return 0.0

        try:
            # Query turbo memory for similar past decisions
            learnings = await self.turbo_memory.get_learnings(
                bot_name=bot_name, intent_type=intent, limit=5
            )

            if not learnings:
                return 0.0

            # Calculate success rate
            successful = sum(1 for l in learnings if l.get("success", False))
            success_rate = successful / len(learnings)

            # Boost based on success rate
            if success_rate > 0.8:
                return 0.15  # Strong boost for high success
            elif success_rate > 0.5:
                return 0.05  # Small boost for moderate success
            elif success_rate < 0.3:
                return -0.1  # Penalty for low success

            return 0.0

        except Exception as e:
            self.logger.warning(f"Error getting historical boost: {e}")
            return 0.0

    def _calculate_context_boost(
        self,
        intent: IntentHypothesis,
        room_history: List[Dict[str, Any]],
    ) -> float:
        """Calculate boost based on conversation context similarity."""
        if not room_history:
            return 0.0

        boost = 0.0

        # Check recent messages for context clues
        recent_messages = room_history[-5:]  # Last 5 messages

        for msg in recent_messages:
            content = msg.get("content", "").lower()

            # Boost if message contains intent keywords
            intent_keywords = intent.intent.lower().split()
            matches = sum(1 for kw in intent_keywords if kw in content)

            if matches > 0:
                boost += 0.02 * matches

        return min(0.1, boost)  # Cap at 0.1

    def _get_personality_adjustment(
        self,
        bot_name: str,
        intent: str,
    ) -> float:
        """Adjust confidence based on bot personality.

        Different bots have different thresholds for proactive behavior.
        Also checks for bot-specific overrides in config.
        """
        # Bot personality profiles
        profiles = {
            "leader": {"proactive_threshold": 0.6, "cautious": False},
            "coder": {"proactive_threshold": 0.7, "cautious": True},
            "creative": {"proactive_threshold": 0.5, "cautious": False},
            "researcher": {"proactive_threshold": 0.75, "cautious": True},
            "social": {"proactive_threshold": 0.4, "cautious": False},
            "auditor": {"proactive_threshold": 0.85, "cautious": True},
        }

        profile = profiles.get(bot_name, {"proactive_threshold": 0.6, "cautious": False})

        # Check for config override
        if hasattr(self, "config") and self.config and hasattr(self.config, "bot_thresholds"):
            if bot_name in self.config.bot_thresholds:
                # If bot has custom threshold, adjust based on it
                custom_threshold = self.config.bot_thresholds[bot_name]
                if custom_threshold > profile["proactive_threshold"]:
                    # Higher threshold = more cautious
                    return -0.15
                else:
                    # Lower threshold = more proactive
                    return 0.1

        if profile["cautious"]:
            # Cautious bots are less likely to proceed proactively
            return -0.1
        else:
            # Confident bots are more likely to proceed
            return 0.05

    async def _create_proceed_action(
        self,
        state: ClarificationState,
        intent: IntentHypothesis,
    ) -> ProactiveAction:
        """Create action to proceed with best intent."""
        message = self._generate_proceed_message(state.bot_name, intent)

        return ProactiveAction(
            action_type=ProactiveActionType.PROCEED_WITH_INTENT,
            confidence=intent.confidence,
            message=message,
            metadata={
                "selected_intent": intent.intent,
                "original_question": state.clarifying_question,
            },
        )

    async def _create_options_action(
        self,
        state: ClarificationState,
        intents: List[IntentHypothesis],
    ) -> ProactiveAction:
        """Create action offering multiple options."""
        options = []
        for i, intent in enumerate(intents[:3], 1):
            options.append(
                {
                    "number": i,
                    "description": intent.intent,
                    "confidence": f"{intent.confidence:.0%}",
                    "action": intent.suggested_action or f"Proceed with {intent.intent}",
                }
            )

        message = f"I found a few possibilities:\n\n"
        for opt in options:
            message += f"{opt['number']}. {opt['description']} ({opt['confidence']})\n"
        message += f"\nWhich one did you mean? Or just tell me what you'd like."

        return ProactiveAction(
            action_type=ProactiveActionType.OFFER_OPTIONS,
            confidence=intents[0].confidence if intents else 0.0,
            message=message,
            options=options,
            metadata={
                "num_options": len(options),
                "top_confidence": intents[0].confidence if intents else 0.0,
            },
        )

    async def _create_alternate_question_action(
        self,
        state: ClarificationState,
        intent: IntentHypothesis,
    ) -> ProactiveAction:
        """Create action with alternate clarifying question."""
        # Generate alternate question based on best intent
        alternate_question = self._generate_alternate_question(state.original_request, intent)

        return ProactiveAction(
            action_type=ProactiveActionType.ASK_DIFFERENT_QUESTION,
            confidence=intent.confidence,
            message=alternate_question,
            metadata={
                "previous_question": state.clarifying_question,
                "best_intent": intent.intent,
            },
        )

    def _generate_proceed_message(
        self,
        bot_name: str,
        intent: IntentHypothesis,
    ) -> str:
        """Generate message for proceeding with intent."""
        templates = [
            f"I'll proceed with {intent.intent}. Let me work on that...",
            f"I understand you want me to {intent.intent}. Starting now...",
            f"Got it - I'll {intent.intent}. Here's what I'm doing...",
            f"Taking action on {intent.intent}. Here's my approach...",
        ]

        # Select based on bot personality
        import random

        return random.choice(templates)

    def _generate_alternate_question(
        self,
        original_request: str,
        intent: IntentHypothesis,
    ) -> str:
        """Generate an alternate clarifying question."""
        templates = [
            f"To help you with {intent.intent}, could you specify which aspect?",
            f"When you mentioned '{original_request}', were you referring to {intent.intent}?",
            f"I want to make sure I understand - are you asking about {intent.intent}?",
        ]

        import random

        return random.choice(templates)


class TimeoutManager:
    """Manages non-blocking timeouts for clarification states.

    Handles multiple concurrent timeouts across different rooms/bots.
    """

    def __init__(self):
        self.logger = logger.bind(component="TimeoutManager")
        self._active_timeouts: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, Callable] = {}

    def start_timeout(
        self,
        timeout_id: str,
        timeout_seconds: float,
        on_timeout: Callable,
    ) -> None:
        """Start a non-blocking timeout.

        Args:
            timeout_id: Unique identifier for this timeout
            timeout_seconds: Seconds to wait
            on_timeout: Callback function when timeout triggers
        """
        # Cancel any existing timeout with this ID
        self.cancel_timeout(timeout_id)

        # Store callback
        self._callbacks[timeout_id] = on_timeout

        # Create timeout task
        task = asyncio.create_task(
            self._timeout_worker(timeout_id, timeout_seconds), name=f"timeout_{timeout_id}"
        )

        self._active_timeouts[timeout_id] = task

        self.logger.debug(f"Started timeout {timeout_id} ({timeout_seconds}s)")

    async def _timeout_worker(self, timeout_id: str, seconds: float) -> None:
        """Worker that waits and triggers callback."""
        try:
            await asyncio.sleep(seconds)

            # Timeout triggered
            callback = self._callbacks.pop(timeout_id, None)
            self._active_timeouts.pop(timeout_id, None)

            if callback:
                self.logger.info(f"Timeout {timeout_id} triggered")

                # Handle both sync and async callbacks
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()

        except asyncio.CancelledError:
            self.logger.debug(f"Timeout {timeout_id} cancelled")
        except Exception as e:
            self.logger.error(f"Error in timeout {timeout_id}: {e}")

    def cancel_timeout(self, timeout_id: str) -> bool:
        """Cancel an active timeout.

        Returns:
            True if timeout was cancelled, False if not found
        """
        task = self._active_timeouts.pop(timeout_id, None)
        if task:
            task.cancel()
            self._callbacks.pop(timeout_id, None)
            self.logger.debug(f"Cancelled timeout {timeout_id}")
            return True
        return False

    def has_active_timeout(self, timeout_id: str) -> bool:
        """Check if a timeout is active."""
        return timeout_id in self._active_timeouts

    def get_active_timeouts(self) -> Set[str]:
        """Get all active timeout IDs."""
        return set(self._active_timeouts.keys())

    async def shutdown(self):
        """Cancel all active timeouts."""
        self.logger.info(f"Shutting down, cancelling {len(self._active_timeouts)} timeouts")

        for timeout_id in list(self._active_timeouts.keys()):
            self.cancel_timeout(timeout_id)

        # Wait briefly for cancellations to complete
        if self._active_timeouts:
            await asyncio.sleep(0.1)


class ProactiveBotLoop:
    """Main proactive loop for handling clarification timeouts.

    Coordinates between:
    - Clarification requests from bots
    - Timeout management
    - Proactive decision making
    - TurboMemory learning integration
    """

    DEFAULT_TIMEOUT = 10.0  # seconds

    def __init__(
        self,
        fleet_manager=None,
        turbo_memory=None,
        timeout_seconds: float = DEFAULT_TIMEOUT,
        proactive_enabled: bool = True,
        config=None,
    ):
        """Initialize the proactive bot loop.

        Args:
            fleet_manager: Fleet manager for bot coordination
            turbo_memory: TurboMemory for learning integration
            timeout_seconds: Default timeout for clarification (default: 10s)
            proactive_enabled: Whether proactive mode is enabled (default: True)
            config: Optional ProactiveConfig for advanced settings
        """
        self.fleet_manager = fleet_manager
        self.turbo_memory = turbo_memory
        self.config = config

        # Use config values if provided, otherwise use defaults
        if config:
            self.timeout_seconds = config.timeout_seconds
            self.proactive_enabled = config.enabled
            # Configure decision engine with thresholds from config
            self.decision_engine = ProactiveDecisionEngine(
                turbo_memory=turbo_memory,
                high_threshold=config.high_confidence_threshold,
                medium_threshold=config.medium_confidence_threshold,
                low_threshold=config.low_confidence_threshold,
            )
        else:
            self.timeout_seconds = timeout_seconds
            self.proactive_enabled = proactive_enabled
            self.decision_engine = ProactiveDecisionEngine(turbo_memory)

        self.timeout_manager = TimeoutManager()

        # Track clarification states by (room_id, bot_name)
        self._clarification_states: Dict[str, ClarificationState] = {}

        self.logger = logger.bind(component="ProactiveBotLoop")

        if self.proactive_enabled:
            self.logger.info(f"ProactiveBotLoop initialized (timeout: {self.timeout_seconds}s)")
        else:
            self.logger.info("ProactiveBotLoop initialized (disabled)")

    async def register_clarification(
        self,
        room_id: str,
        bot_name: str,
        original_request: str,
        clarifying_question: str,
        possible_intents: List[IntentHypothesis],
        context_hash: Optional[str] = None,
    ) -> None:
        """Register a new clarification request and start timeout.

        Args:
            room_id: Room ID
            bot_name: Bot asking the question
            original_request: User's original request
            clarifying_question: Question being asked
            possible_intents: List of possible intent interpretations
            context_hash: Hash of conversation context (for detecting changes)
        """
        if not self.proactive_enabled:
            self.logger.debug("Proactive mode disabled, not registering clarification")
            return

        state_key = f"{room_id}:{bot_name}"

        # Cancel any existing clarification from this bot in this room
        if state_key in self._clarification_states:
            self.timeout_manager.cancel_timeout(state_key)
            self.logger.debug(f"Cancelled previous clarification for {state_key}")

        # Create new state
        state = ClarificationState(
            room_id=room_id,
            bot_name=bot_name,
            original_request=original_request,
            clarifying_question=clarifying_question,
            timestamp=time.time(),
            possible_intents=possible_intents,
            context_hash=context_hash or self._compute_context_hash(room_id),
            timeout_seconds=self.timeout_seconds,
            proactive_enabled=True,
        )

        self._clarification_states[state_key] = state

        # Start timeout
        self.timeout_manager.start_timeout(
            timeout_id=state_key,
            timeout_seconds=self.timeout_seconds,
            on_timeout=lambda: asyncio.create_task(self._handle_timeout(state_key)),
        )

        self.logger.info(
            f"Registered clarification for {bot_name} in room {room_id} "
            f"({self.timeout_seconds}s timeout)"
        )

    async def check_user_response(
        self,
        room_id: str,
        user_message: str,
    ) -> Optional[str]:
        """Check if user message is a response to a pending clarification.

        Returns:
            Bot name if this is a response to their clarification, None otherwise
        """
        # Check all active clarifications in this room
        for state_key, state in self._clarification_states.items():
            if state.room_id == room_id:
                # Check if message addresses this bot
                if self._is_response_to_bot(user_message, state.bot_name):
                    # Cancel timeout and remove state
                    self.timeout_manager.cancel_timeout(state_key)
                    self._clarification_states.pop(state_key, None)

                    self.logger.info(
                        f"User responded to {state.bot_name}'s clarification in room {room_id}"
                    )

                    # Record learning (user responded, not proactive)
                    await self._record_learning(state, user_responded=True)

                    return state.bot_name

        return None

    async def _handle_timeout(self, state_key: str) -> None:
        """Handle timeout - make proactive decision."""
        state = self._clarification_states.pop(state_key, None)
        if not state:
            return

        self.logger.info(f"Timeout triggered for {state.bot_name} in room {state.room_id}")

        # Get room history for context
        room_history = await self._get_room_history(state.room_id)

        # Make proactive decision
        action = await self.decision_engine.decide_on_timeout(state, room_history)

        # Execute action
        await self._execute_action(state, action)

        # Record learning
        await self._record_learning(state, user_responded=False, action=action)

    async def _execute_action(
        self,
        state: ClarificationState,
        action: ProactiveAction,
    ) -> None:
        """Execute the proactive action."""
        self.logger.info(
            f"Executing proactive action: {action.action_type.value} "
            f"(confidence: {action.confidence:.2f})"
        )

        if self.fleet_manager:
            # Send proactive message through fleet manager
            await self.fleet_manager.send_proactive_message(
                room_id=state.room_id,
                bot_name=state.bot_name,
                message=action.message,
                metadata={
                    "action_type": action.action_type.value,
                    "confidence": action.confidence,
                    **action.metadata,
                },
            )
        else:
            self.logger.warning("No fleet manager available to send proactive message")

    async def _record_learning(
        self,
        state: ClarificationState,
        user_responded: bool,
        action: Optional[ProactiveAction] = None,
    ) -> None:
        """Record learning data to TurboMemory."""
        if not self.turbo_memory:
            return

        learning = ProactiveLearning(
            room_id=state.room_id,
            bot_name=state.bot_name,
            original_request=state.original_request,
            clarifying_question=state.clarifying_question,
            selected_action=action.action_type
            if action
            else ProactiveActionType.PROCEED_WITH_INTENT,
            confidence=action.confidence if action else 1.0,
            user_corrected=None,  # Will be updated if user corrects later
            timestamp=time.time(),
        )

        try:
            await self.turbo_memory.add_proactive_learning(
                bot_name=learning.bot_name,
                original_request=learning.original_request,
                clarifying_question=learning.clarifying_question,
                selected_action=learning.selected_action.value,
                confidence=learning.confidence,
                user_responded=user_responded,
                metadata={
                    "room_id": learning.room_id,
                    "timestamp": learning.timestamp,
                },
            )

            self.logger.debug(f"Recorded proactive learning for {state.bot_name}")

        except Exception as e:
            self.logger.warning(f"Failed to record learning: {e}")

    async def update_learning_feedback(
        self,
        room_id: str,
        bot_name: str,
        was_correct: bool,
        user_follow_up: Optional[str] = None,
    ) -> None:
        """Update learning with user feedback on proactive decision.

        Args:
            room_id: Room ID
            bot_name: Bot that made proactive decision
            was_correct: Whether the proactive decision was correct
            user_follow_up: User's follow-up message (if any)
        """
        if not self.turbo_memory:
            return

        try:
            await self.turbo_memory.update_proactive_feedback(
                room_id=room_id,
                bot_name=bot_name,
                was_correct=was_correct,
                user_follow_up=user_follow_up,
            )

            self.logger.info(f"Updated learning for {bot_name}: correct={was_correct}")

        except Exception as e:
            self.logger.warning(f"Failed to update learning feedback: {e}")

    def _is_response_to_bot(self, message: str, bot_name: str) -> bool:
        """Check if user message is responding to a specific bot."""
        message_lower = message.lower()

        # Check for direct mention
        if f"@{bot_name}" in message_lower:
            return True

        # Check if message is likely a response (not a new request)
        # Simple heuristic: short messages are often responses
        if len(message.split()) <= 5:
            return True

        return False

    def _compute_context_hash(self, room_id: str) -> str:
        """Compute a hash of current room context."""
        import hashlib

        return hashlib.md5(f"{room_id}:{time.time()}".encode()).hexdigest()[:8]

    async def _get_room_history(self, room_id: str) -> List[Dict[str, Any]]:
        """Get room message history."""
        if self.fleet_manager and hasattr(self.fleet_manager, "get_room_history"):
            return await self.fleet_manager.get_room_history(room_id)
        return []

    def get_active_clarifications(self) -> List[ClarificationState]:
        """Get all active clarification states."""
        return list(self._clarification_states.values())

    def is_clarification_pending(self, room_id: str, bot_name: str) -> bool:
        """Check if a bot has a pending clarification in a room."""
        state_key = f"{room_id}:{bot_name}"
        return state_key in self._clarification_states

    async def shutdown(self):
        """Shutdown the proactive loop."""
        self.logger.info("Shutting down ProactiveBotLoop")
        await self.timeout_manager.shutdown()
        self._clarification_states.clear()
