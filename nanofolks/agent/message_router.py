"""MessageRouter: Routes messages to bots without being a bot itself.

This module provides the MessageRouter class, which is the central routing
component in the multi-bot architecture. It receives messages from the bus,
determines which bot(s) should handle them, and routes accordingly.

Unlike the current AgentLoop, the MessageRouter has no bot identity of its own.
It is purely a routing layer that coordinates multiple independent bot instances.
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from loguru import logger

from nanofolks.bots.dispatch import BotDispatch, DispatchResult, DispatchTarget
from nanofolks.bots.room_manager import RoomManager, get_room_manager
from nanofolks.bus.events import MessageEnvelope
from nanofolks.bus.queue import MessageBus

if TYPE_CHECKING:
    from nanofolks.agent.loop import AgentLoop


class MessageRouter:
    """Routes messages to appropriate bot(s) without being a bot itself.

    The MessageRouter is the central routing component in the multi-bot architecture.
    It receives messages from the bus, uses BotDispatch to determine which bot(s)
    should handle the message, and routes to those bots.

    Key responsibilities:
    - Receive messages from the message bus
    - Determine dispatch strategy using BotDispatch
    - Route to single bot or broadcast to multiple bots
    - Combine responses when multiple bots respond
    - Manage room context
    - Coordinate bot fleet (via BotFleet)

    Attributes:
        fleet: BotFleet instance managing all bot instances
        room_manager: RoomManager for room operations
        bus: MessageBus for sending/receiving messages
        dispatch: BotDispatch for routing decisions
        response_combiner: ResponseCombiner for formatting multi-bot responses
        _running: Whether the router loop is running
        _current_room_id: Currently active room for routing context
    """

    def __init__(
        self,
        bus: MessageBus,
        fleet: "BotFleet",
        room_manager: Optional[RoomManager] = None,
    ):
        """Initialize the MessageRouter.

        Args:
            bus: MessageBus for sending/receiving messages
            fleet: BotFleet managing all bot instances
            room_manager: Optional RoomManager (uses singleton if not provided)
        """
        self.bus = bus
        self.fleet = fleet
        self.room_manager = room_manager or get_room_manager()
        self.dispatch = BotDispatch(room_manager=self.room_manager)

        # Import ResponseCombiner here to avoid circular imports
        from nanofolks.agent.response_combiner import ResponseCombiner

        self.response_combiner = ResponseCombiner()

        self._running = False
        self._current_room_id = "general"

        # Initialize proactive bot loop (enabled by default)
        from nanofolks.bots.proactive_loop import ProactiveBotLoop

        self.proactive_loop = ProactiveBotLoop(
            fleet_manager=fleet,
            turbo_memory=None,  # Will be set later if available
            timeout_seconds=10.0,
            proactive_enabled=True,
        )

        self.logger = logger.bind(component="MessageRouter")
        self.logger.info("MessageRouter initialized")

    async def run(self) -> None:
        """Run the router loop, processing messages from the bus.

        This is the main entry point for the router. It continuously
        consumes messages from the bus and routes them to appropriate bots.
        """
        self._running = True
        self.logger.info("MessageRouter started - listening for messages")

        while self._running:
            try:
                # Wait for next message (with timeout to allow clean shutdown)
                msg = await asyncio.wait_for(self.bus.consume_inbound(), timeout=1.0)

                if msg is None:
                    continue

                # Process the message
                try:
                    response = await self.route_message(msg)
                    if response:
                        await self.bus.publish_outbound(response)
                        self.logger.debug(f"Published response from {response.bot_name}")
                except Exception as e:
                    self.logger.error(f"Error routing message: {e}")
                    # Send error response
                    error_response = MessageEnvelope(
                        channel=msg.channel,
                        chat_id=msg.chat_id,
                        content=f"❌ I encountered an error: {str(e)}",
                        bot_name="system",
                        room_id=msg.room_id or self._current_room_id,
                    )
                    await self.bus.publish_outbound(error_response)

            except asyncio.TimeoutError:
                # Normal timeout - just continue
                continue
            except Exception as e:
                self.logger.error(f"Error in router loop: {e}")
                await asyncio.sleep(0.1)

    async def stop(self) -> None:
        """Stop the router loop."""
        self._running = False
        self.logger.info("MessageRouter stopped")

    async def route_message(self, msg: MessageEnvelope) -> Optional[MessageEnvelope]:
        """Route message to appropriate bot(s).

        This is the core routing method. It:
        1. Determines the dispatch strategy using BotDispatch
        2. Routes to single bot or multiple bots
        3. Combines responses if needed

        Args:
            msg: The incoming message to route

        Returns:
            Response MessageEnvelope, or None if no response needed
        """
        # Update current room context
        self._current_room_id = msg.room_id or self._current_room_id

        # Check if this is a response to a pending clarification
        responding_bot = await self.proactive_loop.check_user_response(
            room_id=self._current_room_id,
            user_message=msg.content,
        )

        if responding_bot:
            self.logger.info(f"User responding to {responding_bot}'s clarification")

        self.logger.info(
            f"Routing message in room '{self._current_room_id}': {msg.content[:50]}..."
        )

        # Get room context
        room = None
        if self.room_manager and self._current_room_id:
            room = self.room_manager.get_room(self._current_room_id)

        # Determine dispatch strategy
        dispatch_result = self.dispatch.dispatch_message(
            message=msg.content,
            room=room,
            is_dm=msg.is_dm if hasattr(msg, "is_dm") else False,
            dm_target=msg.dm_target if hasattr(msg, "dm_target") else None,
        )

        self.logger.info(
            f"Dispatch decision: {dispatch_result.target.value} -> {dispatch_result.primary_bot}"
        )

        # Route based on dispatch mode
        if dispatch_result.target == DispatchTarget.DIRECT_BOT:
            return await self._route_to_single_bot(msg, dispatch_result)

        elif dispatch_result.target in [DispatchTarget.MULTI_BOT, DispatchTarget.TEAM_CONTEXT]:
            return await self._route_to_multiple_bots(msg, dispatch_result)

        elif dispatch_result.target == DispatchTarget.SMART_DISCUSS:
            # Use SmartDispatch for intelligent bot selection
            return await self._route_smart_discuss(msg, dispatch_result)

        elif dispatch_result.target == DispatchTarget.LEADER_FIRST:
            return await self._route_through_leader(msg, dispatch_result)

        elif dispatch_result.target == DispatchTarget.DM:
            return await self._route_to_dm(msg, dispatch_result)

        else:
            # Unknown dispatch target - default to leader
            self.logger.warning(
                f"Unknown dispatch target: {dispatch_result.target}, defaulting to leader"
            )
            return await self._route_through_leader(msg, dispatch_result)

    async def _route_to_single_bot(
        self, msg: MessageEnvelope, dispatch_result: DispatchResult
    ) -> MessageEnvelope:
        """Route message to a single bot.

        Args:
            msg: The incoming message
            dispatch_result: Dispatch decision

        Returns:
            Bot response
        """
        bot_name = dispatch_result.primary_bot
        room_id = msg.room_id or self._current_room_id

        # Use room-scoped bot for true parallelism
        bot_key = self.fleet._get_bot_key(bot_name, room_id)

        # Ensure bot is running (room-scoped)
        if bot_key not in self.fleet.get_active_bots():
            self.logger.info(f"Bot '{bot_key}' not active, attempting to start")
            try:
                await self.fleet.start_bot(bot_name, room_id=room_id)
            except Exception as e:
                self.logger.error(f"Failed to start bot '{bot_key}': {e}")
                return MessageEnvelope(
                    content=f"❌ Bot '{bot_name}' is not available",
                    bot_name="system",
                    room_id=msg.room_id,
                    metadata={"error": "bot_not_available", "bot_name": bot_name},
                )

        # Route to the room-scoped bot
        try:
            response = await self.fleet.bots[bot_key].process_message(msg)

            # Check if this is a clarifying question and register with proactive loop
            await self._check_and_register_clarification(
                room_id=msg.room_id or self._current_room_id,
                bot_name=bot_name,
                original_request=msg.content,
                response=response,
            )

            return response
        except Exception as e:
            self.logger.error(f"Error from bot '{bot_name}': {e}")
            return MessageEnvelope(
                content=f"❌ Bot '{bot_name}' encountered an error: {str(e)}",
                bot_name=bot_name,
                room_id=msg.room_id,
                metadata={"error": str(e)},
            )

    async def _route_to_multiple_bots(
        self, msg: MessageEnvelope, dispatch_result: DispatchResult
    ) -> MessageEnvelope:
        """Route message to multiple bots in parallel.

        Args:
            msg: The incoming message
            dispatch_result: Dispatch decision

        Returns:
            Combined response from all bots
        """
        # Get all bots to respond (primary + secondary)
        room_id = msg.room_id or self._current_room_id
        all_bots = [dispatch_result.primary_bot] + dispatch_result.secondary_bots

        # Remove duplicates while preserving order
        seen = set()
        unique_bot_names = []
        for bot in all_bots:
            if bot and bot not in seen:
                seen.add(bot)
                unique_bot_names.append(bot)

        self.logger.info(
            f"Broadcasting to {len(unique_bot_names)} bots in room {room_id}: {', '.join(unique_bot_names)}"
        )

        # Ensure all room-scoped bots are running
        active_bot_keys = []
        for bot_name in unique_bot_names:
            bot_key = self.fleet._get_bot_key(bot_name, room_id)
            if bot_key not in self.fleet.get_active_bots():
                try:
                    await self.fleet.start_bot(bot_name, room_id=room_id)
                except Exception as e:
                    self.logger.warning(f"Could not start bot '{bot_key}': {e}")
            if bot_key in self.fleet.get_active_bots():
                active_bot_keys.append(bot_key)

        # Broadcast to all active room-scoped bots
        active_bots = [
            b for b in unique_bot_names if self.fleet._get_bot_key(b, room_id) in active_bot_keys
        ]

        if not active_bots:
            return MessageEnvelope(
                content="❌ No bots are available to respond",
                bot_name="system",
                room_id=msg.room_id,
                metadata={"error": "no_bots_available"},
            )

        try:
            responses = await self.fleet.broadcast_to_bots(active_bots, msg)

            # Combine responses
            combined = self.response_combiner.combine(responses, dispatch_result.target)

            # Add metadata about which bots were asked vs responded
            combined.metadata = combined.metadata or {}
            combined.metadata["asked_bots"] = unique_bot_names
            combined.metadata["active_bots"] = active_bots

            return combined

        except Exception as e:
            self.logger.error(f"Error in multi-bot routing: {e}")
            return MessageEnvelope(
                content=f"❌ Error coordinating bots: {str(e)}",
                bot_name="system",
                room_id=msg.room_id,
                metadata={"error": str(e)},
            )

    async def _route_through_leader(
        self, msg: MessageEnvelope, dispatch_result: DispatchResult
    ) -> MessageEnvelope:
        """Route message through leader bot (Leader-First mode).

        In Leader-First mode, the leader bot coordinates the response.
        The leader may invoke other bots via tools or coordination.

        Args:
            msg: The incoming message
            dispatch_result: Dispatch decision

        Returns:
            Leader response
        """
        # This is essentially the same as _route_to_single_bot but with logging
        self.logger.info("Routing through leader (Leader-First mode)")
        return await self._route_to_single_bot(msg, dispatch_result)

    async def _route_to_dm(
        self, msg: MessageEnvelope, dispatch_result: DispatchResult
    ) -> MessageEnvelope:
        """Route direct message to specific bot.

        DM mode bypasses leader and goes directly to the target bot.

        Args:
            msg: The incoming message
            dispatch_result: Dispatch decision

        Returns:
            Bot response
        """
        self.logger.info(f"Routing DM to bot '{dispatch_result.primary_bot}'")
        return await self._route_to_single_bot(msg, dispatch_result)

    async def _route_smart_discuss(
        self, msg: MessageEnvelope, dispatch_result: DispatchResult
    ) -> MessageEnvelope:
        """Route message using SmartDispatch for intelligent bot selection.

        Two-phase process:
        1. All room bots evaluate urgency in parallel
        2. Only high-urgency bots respond (in micro-turns)

        Args:
            msg: The incoming message
            dispatch_result: Initial dispatch decision (may be overridden by SmartDispatch)

        Returns:
            Combined response from selected bots
        """
        from nanofolks.bots.smart_dispatch import SmartDispatch

        self.logger.info("SmartDiscuss mode - evaluating bot urgency with LLM")

        # Remove @discuss trigger from message for processing
        clean_message = msg.content.replace("@discuss", "").strip()

        # Get LLM provider from fleet
        llm_provider = None
        if hasattr(self.fleet, "provider"):
            llm_provider = self.fleet.provider

        if llm_provider:
            self.logger.debug("Using LLM-based urgency evaluation")
        else:
            self.logger.warning("No LLM provider available, using rule-based evaluation")

        # Get active bots from fleet for SmartDispatch
        active_bots = self.fleet.get_active_bots() if self.fleet else ["leader"]
        self.logger.debug(
            f"SmartDispatch will evaluate {len(active_bots)} active bots: {active_bots}"
        )

        # Create SmartDispatch instance with LLM provider
        smart_dispatch = SmartDispatch(
            room_manager=self.room_manager,
            llm_provider=llm_provider,
            speak_threshold=0.5,
            use_llm=llm_provider is not None,
        )

        # Run SmartDispatch to select bots based on urgency
        smart_result = await smart_dispatch.dispatch_smart_discuss(
            message=clean_message,
            room_id=msg.room_id or self._current_room_id,
            available_bots=active_bots,  # Pass active bots from fleet
        )

        # Log selection results
        self.logger.info(
            f"SmartDispatch selected {len(smart_result.secondary_bots) + 1} bots: "
            f"{smart_result.primary_bot}"
            + (
                f" + {', '.join(smart_result.secondary_bots)}"
                if smart_result.secondary_bots
                else ""
            )
        )

        # Use the smart dispatch result instead of original
        # Ensure all selected room-scoped bots are running
        all_selected = [smart_result.primary_bot] + smart_result.secondary_bots
        room_id = msg.room_id or self._current_room_id
        active_bot_keys = []

        for bot_name in all_selected:
            bot_key = self.fleet._get_bot_key(bot_name, room_id)
            if bot_key not in self.fleet.get_active_bots():
                try:
                    await self.fleet.start_bot(bot_name, room_id=room_id)
                except Exception as e:
                    self.logger.warning(f"Could not start bot '{bot_key}': {e}")
            if bot_key in self.fleet.get_active_bots():
                active_bot_keys.append(bot_key)

        # Filter to only active bots
        active_bots = [
            b for b in all_selected if self.fleet._get_bot_key(b, room_id) in active_bot_keys
        ]

        if not active_bots:
            return MessageEnvelope(
                content="❌ No bots are available for discussion",
                bot_name="system",
                room_id=msg.room_id,
                metadata={"error": "no_bots_available"},
            )

        # Broadcast to selected room-scoped bots with streaming
        try:
            # Create message without @discuss for bot processing
            msg_for_bots = MessageEnvelope(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=clean_message,
                bot_name=msg.bot_name,
                room_id=msg.room_id,
                metadata={
                    **(msg.metadata or {}),
                    "smart_discuss": True,
                    "dispatch_mode": "smart_discuss",
                },
            )

            # Use streaming for multi-bot discussions
            # This yields responses as they arrive instead of waiting for all
            responses = []
            first_response_received = False
            async for response in self.fleet.broadcast_to_bots_streaming(
                active_bot_keys, msg_for_bots
            ):
                # Publish each response immediately for streaming UX
                await self.bus.publish_outbound(response)
                self.logger.info(f"Streamed response from {response.bot_name}")
                responses.append(response)

                # Cancel any pending proactive when bots respond
                # (new context means the clarification is answered)
                if not first_response_received:
                    first_response_received = True
                    room_id = msg.room_id or self._current_room_id
                    if self.proactive_loop.is_clarification_pending(room_id, response.bot_name):
                        await self.proactive_loop.cancel_room_proactive(
                            room_id, reason=f"Bot {response.bot_name} responded"
                        )

            # Combine responses using ResponseCombiner (for metadata/logging)
            combined = self.response_combiner.combine(
                responses,
                DispatchTarget.SMART_DISCUSS,
            )

            # Add metadata about the smart selection
            combined.metadata = combined.metadata or {}
            combined.metadata["smart_discuss"] = True
            combined.metadata["asked_bots"] = all_selected
            combined.metadata["active_bots"] = active_bots
            combined.metadata["dispatch_reason"] = smart_result.reason
            combined.metadata["streaming"] = True
            combined.metadata["response_count"] = len(responses)

            return combined

        except Exception as e:
            self.logger.error(f"Error in SmartDiscuss routing: {e}")
            return MessageEnvelope(
                content=f"❌ Error in smart discussion: {str(e)}",
                bot_name="system",
                room_id=msg.room_id,
                metadata={"error": str(e)},
            )

    def get_current_room_id(self) -> str:
        """Get the currently active room ID.

        Returns:
            Current room ID
        """
        return self._current_room_id

    def set_current_room(self, room_id: str) -> None:
        """Set the current room for routing context.

        Args:
            room_id: Room ID to set as current
        """
        self._current_room_id = room_id
        self.logger.debug(f"Current room set to: {room_id}")

    def get_stats(self) -> Dict:
        """Get router statistics.

        Returns:
            Dictionary with router stats
        """
        return {
            "running": self._running,
            "current_room_id": self._current_room_id,
            "active_bots": self.fleet.get_active_bots() if self.fleet else [],
            "bot_count": len(self.fleet.get_active_bots()) if self.fleet else 0,
            "active_clarifications": len(self.proactive_loop.get_active_clarifications()),
        }

    async def _check_and_register_clarification(
        self,
        room_id: str,
        bot_name: str,
        original_request: str,
        response: MessageEnvelope,
    ) -> None:
        """Check if bot response is a clarifying question and register with proactive loop.

        Args:
            room_id: Room ID
            bot_name: Bot that responded
            original_request: User's original request
            response: Bot's response message
        """
        from nanofolks.bots.proactive_loop import IntentHypothesis

        content = response.content if hasattr(response, "content") else str(response)

        # Heuristic: Check if response contains a question mark and seems to be asking for clarification
        is_clarifying = self._is_clarifying_question(content)

        if is_clarifying:
            self.logger.info(f"Detected clarifying question from {bot_name} in room {room_id}")

            # Generate possible intent hypotheses based on original request
            possible_intents = self._generate_intent_hypotheses(original_request, bot_name)

            # Register with proactive loop
            # Pass metadata from response to detect @discuss mode
            metadata = response.metadata if hasattr(response, "metadata") else {}
            await self.proactive_loop.register_clarification(
                room_id=room_id,
                bot_name=bot_name,
                original_request=original_request,
                clarifying_question=content,
                possible_intents=possible_intents,
                metadata=metadata,
            )

    def _is_clarifying_question(self, content: str) -> bool:
        """Check if content is a clarifying question.

        Heuristics:
        - Contains question mark
        - Asks for specification (which, what, how, where)
        - Doesn't provide a solution or answer
        """
        content_lower = content.lower()

        # Must have a question mark
        if "?" not in content:
            return False

        # Check for clarification indicators
        clarification_indicators = [
            "which",
            "what",
            "how would you like",
            "could you specify",
            "can you clarify",
            "do you mean",
            "are you referring to",
            "would you prefer",
        ]

        has_indicator = any(ind in content_lower for ind in clarification_indicators)

        # Check it's not just a rhetorical question at the end of a long answer
        sentences = content.split(".")
        last_sentence = sentences[-1] if sentences else content

        # If question is at the very end and preceded by substantial content, it might be rhetorical
        if len(content) > 200 and "?" in last_sentence and not has_indicator:
            return False

        return has_indicator

    def _generate_intent_hypotheses(
        self,
        original_request: str,
        bot_name: str,
    ) -> List[IntentHypothesis]:
        """Generate possible intent interpretations.

        Args:
            original_request: User's request
            bot_name: Bot that will handle the request

        Returns:
            List of intent hypotheses with confidence scores
        """
        from nanofolks.bots.proactive_loop import IntentHypothesis

        # Get bot-specific keywords
        domain_keywords = self._get_bot_keywords(bot_name)

        # Analyze request for possible intents
        request_lower = original_request.lower()

        hypotheses = []

        # Check for action keywords
        action_keywords = {
            "create": ["create", "make", "build", "generate", "new"],
            "update": ["update", "change", "modify", "edit", "fix"],
            "delete": ["delete", "remove", "clean", "clear"],
            "analyze": ["analyze", "check", "review", "audit", "inspect"],
            "implement": ["implement", "add", "integrate", "setup", "configure"],
        }

        detected_action = None
        for action, keywords in action_keywords.items():
            if any(kw in request_lower for kw in keywords):
                detected_action = action
                break

        # Generate hypotheses based on detected action and bot domain
        if detected_action:
            # High confidence: specific action in bot's domain
            confidence = 0.75
            if any(kw in request_lower for kw in domain_keywords[:5]):
                confidence = 0.85

            hypotheses.append(
                IntentHypothesis(
                    intent=f"{detected_action}_{bot_name}_task",
                    confidence=confidence,
                    reasoning=f"Detected '{detected_action}' action in {bot_name}'s domain",
                    suggested_action=f"Proceed with {detected_action} using best practices",
                )
            )

        # Medium confidence: general request in bot's domain
        domain_match = sum(1 for kw in domain_keywords if kw in request_lower)
        if domain_match >= 2:
            hypotheses.append(
                IntentHypothesis(
                    intent=f"general_{bot_name}_assistance",
                    confidence=0.6,
                    reasoning=f"Multiple domain keywords match ({domain_match} matches)",
                    suggested_action=f"Provide general {bot_name} assistance",
                )
            )

        # Low confidence: vague request
        if len(original_request.split()) <= 3:
            hypotheses.append(
                IntentHypothesis(
                    intent="vague_request_needs_clarification",
                    confidence=0.3,
                    reasoning="Request is too vague",
                    suggested_action="Ask for more details",
                )
            )

        # Always add a fallback
        hypotheses.append(
            IntentHypothesis(
                intent=f"{bot_name}_best_effort",
                confidence=0.4,
                reasoning="Make best effort based on available context",
                suggested_action="Attempt to help with available information",
            )
        )

        return hypotheses

    def _get_bot_keywords(self, bot_name: str) -> List[str]:
        """Get domain keywords for a bot."""
        keywords = {
            "leader": ["plan", "strategy", "coordinate", "manage", "decision", "team"],
            "coder": ["code", "implement", "build", "technical", "api", "database", "bug"],
            "researcher": ["research", "analyze", "data", "market", "study", "insight"],
            "creative": ["design", "visual", "color", "ui", "ux", "brand", "mockup"],
            "social": ["social", "marketing", "audience", "content", "community"],
            "auditor": ["audit", "security", "compliance", "review", "quality"],
        }
        return keywords.get(bot_name, [])


class MessageRouterConfig:
    """Configuration for the MessageRouter.

    Attributes:
        default_routing: Default routing strategy
        max_parallel_bots: Maximum number of bots to invoke in parallel
        response_timeout: Timeout for bot responses (seconds)
        enable_leader_first: Whether Leader-First mode is enabled
    """

    def __init__(
        self,
        default_routing: str = "leader_first",
        max_parallel_bots: int = 6,
        response_timeout: int = 30,
        enable_leader_first: bool = True,
    ):
        self.default_routing = default_routing
        self.max_parallel_bots = max_parallel_bots
        self.response_timeout = response_timeout
        self.enable_leader_first = enable_leader_first


# Convenience function
def create_message_router(
    bus: MessageBus,
    fleet: "BotFleet",
    room_manager: Optional[RoomManager] = None,
) -> MessageRouter:
    """Create a MessageRouter instance.

    Args:
        bus: MessageBus for sending/receiving messages
        fleet: BotFleet managing all bot instances
        room_manager: Optional RoomManager

    Returns:
        MessageRouter instance
    """
    return MessageRouter(bus, fleet, room_manager)
