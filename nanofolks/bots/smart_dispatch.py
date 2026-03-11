"""SmartDispatch: Intelligent bot selection for group chat with urgency scoring.

This module provides the SmartDispatch system which enables a group chat
environment where:
1. ALL room participants evaluate their urgency to respond
2. Only bots with high urgency (> threshold) actually speak
3. Responses are in micro-turns (1-3 sentences)
4. Creates a natural "group discussion" flow

Usage:
    smart_dispatch = SmartDispatch(room_manager, provider)
    result = await smart_dispatch.dispatch_smart_discuss(message, room_id)
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional

from loguru import logger

from nanofolks.bots.dispatch import DispatchResult, DispatchTarget
from nanofolks.bots.room_manager import RoomManager


@dataclass
class BotUrgency:
    """Urgency assessment for a single bot."""

    bot_name: str
    urgency_score: float  # 0.0 to 1.0
    should_speak: bool
    reasoning: str  # Why this bot should/shouldn't speak


class SmartDispatch:
    """Smart group discussion dispatcher with urgency-based selection.

    Two-phase architecture:
    Phase 1: All bots evaluate urgency (cheap, parallel)
    Phase 2: High-urgency bots generate short responses

    Example:
        User: "@discuss How does color theory work for our canvas app?"

        Phase 1 - Urgency Check:
        creative: 0.95 (design expertise)
        coder: 0.85 (canvas implementation)
        researcher: 0.60 (user research)
        leader: 0.50 (coordination)
        auditor: 0.20 (not relevant)
        social: 0.10 (not relevant)

        Phase 2 - Only bots with urgency >= 0.5 respond:
        creative: "Color theory is fundamental..."
        coder: "For canvas implementation, we need..."
        researcher: "Studies show users prefer..."
        leader: "Let's prioritize this feature..."
    """

    # Default thresholds
    SPEAK_THRESHOLD = 0.5  # Speak if urgency >= this
    HIGH_URGENCY = 0.8
    MEDIUM_URGENCY = 0.5

    def __init__(
        self,
        room_manager: RoomManager,
        llm_provider=None,
        speak_threshold: float = 0.5,
        use_llm: bool = True,
    ):
        """Initialize SmartDispatch.

        Args:
            room_manager: Room manager for room operations
            llm_provider: LLM provider for urgency evaluation (uses rule-based if None)
            speak_threshold: Minimum urgency score to speak (0.0-1.0)
            use_llm: Whether to use LLM for urgency evaluation (if provider available)
        """
        self.room_manager = room_manager
        self.llm_provider = llm_provider
        self.speak_threshold = speak_threshold
        self.use_llm = use_llm and llm_provider is not None

        self.logger = logger.bind(component="SmartDispatch")

        if self.use_llm:
            self.logger.info("SmartDispatch using LLM-based urgency evaluation")
        else:
            self.logger.info("SmartDispatch using rule-based urgency evaluation")

    async def dispatch_smart_discuss(
        self,
        message: str,
        room_id: str,
    ) -> DispatchResult:
        """Execute smart group discussion dispatch.

        Two-phase process:
        1. All room bots evaluate urgency in parallel
        2. High-urgency bots are selected to respond

        Args:
            message: User's message (with @discuss trigger removed)
            room_id: Room ID

        Returns:
            DispatchResult with selected bots ordered by urgency
        """
        self.logger.info(f"SmartDiscuss triggered in room {room_id}")

        # Get room and participants
        room = self.room_manager.get_room(room_id)
        if not room:
            self.logger.warning(f"Room {room_id} not found, defaulting to leader")
            return DispatchResult(
                target=DispatchTarget.SMART_DISCUSS,
                primary_bot="leader",
                secondary_bots=[],
                room_id=room_id,
                reason="Room not found",
            )

        participants = room.participants
        if not participants:
            participants = ["leader"]

        self.logger.info(f"Evaluating urgency for {len(participants)} bots")

        # Phase 1: Evaluate urgency for all bots
        if self.use_llm and self.llm_provider:
            # Use single LLM call to evaluate all bots (more efficient)
            urgency_results = await self._evaluate_all_bots_with_llm(message, participants)
        else:
            # Use rule-based evaluation (parallel, no LLM cost)
            urgency_tasks = [
                self._evaluate_urgency_rule_based(message, bot_name) for bot_name in participants
            ]
            urgency_results = await asyncio.gather(*urgency_tasks)

        # Phase 2: Select bots that should speak
        selected_bots = [result for result in urgency_results if result.should_speak]

        # Sort by urgency (highest first)
        selected_bots.sort(key=lambda x: x.urgency_score, reverse=True)

        if not selected_bots:
            # No bots want to speak - fallback to leader
            self.logger.info("No bots selected, falling back to leader")
            return DispatchResult(
                target=DispatchTarget.SMART_DISCUSS,
                primary_bot="leader",
                secondary_bots=[],
                room_id=room_id,
                reason="No bots exceeded urgency threshold",
            )

        # Build dispatch result
        primary = selected_bots[0].bot_name
        secondary = [b.bot_name for b in selected_bots[1:]]

        self.logger.info(
            f"Selected {len(selected_bots)} bots: {', '.join(b.bot_name for b in selected_bots)}"
        )

        # Log urgency scores for debugging
        for bot in selected_bots:
            self.logger.debug(f"  {bot.bot_name}: {bot.urgency_score:.2f} - {bot.reasoning}")

        return DispatchResult(
            target=DispatchTarget.SMART_DISCUSS,
            primary_bot=primary,
            secondary_bots=secondary,
            room_id=room_id,
            reason=self._format_reason(selected_bots),
        )

    async def _evaluate_all_bots_with_llm(
        self,
        message: str,
        bot_names: List[str],
    ) -> List[BotUrgency]:
        """Evaluate all bots' urgency in a single LLM call.

        This is more efficient than calling the LLM for each bot separately.
        Uses the local Apple Intelligence model or whatever LLM is configured.

        Args:
            message: User message
            bot_names: List of bot names to evaluate

        Returns:
            List of BotUrgency assessments
        """
        if not self.llm_provider:
            # Fallback to rule-based
            tasks = [self._evaluate_urgency_rule_based(message, name) for name in bot_names]
            return await asyncio.gather(*tasks)

        # Create bot context for prompt
        bot_contexts = []
        for bot_name in bot_names:
            role_desc = self._get_bot_role_description(bot_name)
            bot_contexts.append(f"{bot_name}: {role_desc}")

        prompt = f"""You are evaluating which team members should respond to a user question.

User Question: "{message}"

Available team members and their expertise:
{chr(10).join(f"- {ctx}" for ctx in bot_contexts)}

For each team member, rate their urgency to respond on a scale of 0.0 to 1.0:
- 0.0-0.3: Not relevant to their expertise
- 0.4-0.6: Somewhat relevant, could contribute
- 0.7-0.9: Highly relevant, should definitely respond
- 1.0: Critical expertise needed

Consider:
1. Direct expertise match (e.g., design questions → creative bot)
2. Indirect relevance (e.g., "canvas app" needs both design AND code)
3. Contextual needs (e.g., strategic questions → leader, research questions → researcher)
4. Nuanced understanding (e.g., "design canvas" implies both creative AND coder)

Respond ONLY in this format (one line per bot):
creative: 0.85 - Design expertise needed for canvas UI
coder: 0.80 - Canvas implementation requires technical knowledge
leader: 0.50 - Strategic coordination valuable
researcher: 0.40 - User research could inform decisions
auditor: 0.20 - Security review not immediately needed
social: 0.10 - Marketing not relevant to technical question"""

        try:
            # Call LLM
            response = await self.llm_provider.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at routing questions to the right team members. Be precise and concise.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=500,
            )

            # Parse response
            assessments = self._parse_llm_urgency_response(response.content, bot_names)

            self.logger.info(f"LLM evaluated {len(assessments)} bots")
            return assessments

        except Exception as e:
            self.logger.error(f"LLM urgency evaluation failed: {e}. Falling back to rule-based.")
            # Fallback to rule-based
            tasks = [self._evaluate_urgency_rule_based(message, name) for name in bot_names]
            return await asyncio.gather(*tasks)

    def _get_bot_role_description(self, bot_name: str) -> str:
        """Get a brief role description for LLM context."""
        descriptions = {
            "leader": "Strategic coordinator, manages team direction and decisions",
            "coder": "Technical implementation, architecture, code, APIs, databases",
            "researcher": "Data analysis, user research, market research, insights",
            "creative": "Design, visuals, UX, branding, color, typography, aesthetics",
            "social": "Marketing, audience, community, engagement, content strategy",
            "auditor": "Security, compliance, quality, accessibility, ethics, review",
        }
        return descriptions.get(bot_name, "General team member")

    def _parse_llm_urgency_response(self, response: str, bot_names: List[str]) -> List[BotUrgency]:
        """Parse LLM urgency response into BotUrgency objects."""
        assessments = []
        response_lower = response.lower()

        for line in response.strip().split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue

            try:
                # Parse format: "botname: 0.85 - reasoning"
                parts = line.split(":", 1)
                if len(parts) != 2:
                    continue

                bot_name = parts[0].strip()
                if bot_name not in bot_names:
                    continue

                rest = parts[1].strip()

                # Extract score
                if "-" in rest:
                    score_part = rest.split("-")[0].strip()
                    reasoning = rest.split("-", 1)[1].strip()
                else:
                    score_part = rest
                    reasoning = "LLM evaluation"

                urgency_score = float(score_part)
                urgency_score = max(0.0, min(1.0, urgency_score))  # Clamp to 0-1

                should_speak = urgency_score >= self.speak_threshold

                assessments.append(
                    BotUrgency(
                        bot_name=bot_name,
                        urgency_score=urgency_score,
                        should_speak=should_speak,
                        reasoning=reasoning,
                    )
                )

            except (ValueError, IndexError) as e:
                self.logger.warning(f"Could not parse urgency line: {line}. Error: {e}")
                continue

        # Add any missing bots with low urgency
        assessed_bots = {a.bot_name for a in assessments}
        for bot_name in bot_names:
            if bot_name not in assessed_bots:
                assessments.append(
                    BotUrgency(
                        bot_name=bot_name,
                        urgency_score=0.2,
                        should_speak=False,
                        reasoning="Not assessed by LLM",
                    )
                )

        return assessments

    async def _evaluate_urgency_rule_based(
        self,
        message: str,
        bot_name: str,
    ) -> BotUrgency:
        """Evaluate a single bot's urgency using rule-based scoring.

        Fallback method when LLM is not available.
        Fast but less nuanced than LLM evaluation.

        Args:
            message: User message
            bot_name: Bot to evaluate

        Returns:
            BotUrgency assessment
        """
        # Get domain keywords for this bot
        domain_keywords = self._get_bot_keywords(bot_name)

        # Count keyword matches
        message_lower = message.lower()
        matches = sum(1 for kw in domain_keywords if kw in message_lower)

        # Base urgency on matches
        if matches == 0:
            # Check for general relevance
            base_urgency = 0.2  # Low baseline for all bots
            reasoning = f"No specific {bot_name} expertise needed"
        elif matches >= 3:
            base_urgency = min(0.95, 0.6 + (matches * 0.1))
            reasoning = f"Strong {bot_name} relevance ({matches} matches)"
        elif matches >= 1:
            base_urgency = min(0.75, 0.4 + (matches * 0.1))
            reasoning = f"Moderate {bot_name} relevance ({matches} matches)"
        else:
            base_urgency = 0.2
            reasoning = f"Weak {bot_name} relevance"

        # Adjust based on bot role
        urgency_score = self._adjust_urgency_by_role(bot_name, base_urgency, message)

        # Determine if should speak
        should_speak = urgency_score >= self.speak_threshold

        return BotUrgency(
            bot_name=bot_name,
            urgency_score=urgency_score,
            should_speak=should_speak,
            reasoning=reasoning,
        )

    def _get_bot_keywords(self, bot_name: str) -> List[str]:
        """Get domain keywords for a bot.

        These define what topics each bot is expert in.
        """
        keywords = {
            "leader": [
                "plan",
                "strategy",
                "coordinate",
                "manage",
                "decision",
                "team",
                "direction",
                "vision",
                "organize",
                "prioritize",
                "project",
                "timeline",
                "roadmap",
                "scope",
                "goal",
                "objective",
            ],
            "coder": [
                "code",
                "program",
                "implement",
                "develop",
                "build",
                "create",
                "api",
                "database",
                "backend",
                "frontend",
                "architecture",
                "function",
                "class",
                "module",
                "library",
                "framework",
                "python",
                "javascript",
                "typescript",
                "react",
                "vue",
                "node",
                "bug",
                "fix",
                "debug",
                "test",
                "deploy",
                "devops",
                "technical",
                "engineering",
                "performance",
                "optimization",
                "canvas",
                "drawing",
                "graphics",
                "rendering",
            ],
            "researcher": [
                "research",
                "analyze",
                "study",
                "investigate",
                "explore",
                "data",
                "metrics",
                "statistics",
                "survey",
                "report",
                "market",
                "competitor",
                "trend",
                "industry",
                "benchmark",
                "user research",
                "interview",
                "insight",
                "finding",
                "evaluation",
                "assessment",
                "comparison",
                "review",
            ],
            "creative": [
                "design",
                "visual",
                "color",
                "palette",
                "theme",
                "style",
                "brand",
                "logo",
                "typography",
                "layout",
                "composition",
                "ui",
                "ux",
                "interface",
                "experience",
                "aesthetic",
                "look",
                "mockup",
                "prototype",
                "wireframe",
                "sketch",
                "concept",
                "art",
                "creative",
                "inspiration",
                "mood",
                "vibe",
                "canvas",
                "drawing",
                "illustration",
                "graphics",
            ],
            "social": [
                "social",
                "marketing",
                "audience",
                "community",
                "engagement",
                "viral",
                "content",
                "post",
                "share",
                "promote",
                "campaign",
                "brand awareness",
                "reach",
                "follower",
                "influencer",
                "communication",
                "messaging",
                "copy",
                "tone",
                "voice",
            ],
            "auditor": [
                "audit",
                "security",
                "compliance",
                "policy",
                "regulation",
                "review",
                "quality",
                "standard",
                "guideline",
                "requirement",
                "test",
                "validate",
                "verify",
                "check",
                "inspect",
                "scan",
                "vulnerability",
                "risk",
                "threat",
                "privacy",
                "gdpr",
                "accessibility",
                "a11y",
                "wcag",
                "ethics",
                "bias",
            ],
        }

        return keywords.get(bot_name, [])

    def _adjust_urgency_by_role(
        self,
        bot_name: str,
        base_urgency: float,
        message: str,
    ) -> float:
        """Adjust urgency based on bot's role and message context."""
        message_lower = message.lower()

        # Leader gets boost for coordination questions
        if bot_name == "leader":
            if any(word in message_lower for word in ["team", "plan", "next steps", "coordinate"]):
                return min(0.95, base_urgency + 0.3)

        # Creative gets boost for design/visual questions
        if bot_name == "creative":
            if any(word in message_lower for word in ["design", "color", "visual", "look", "feel"]):
                return min(0.95, base_urgency + 0.25)

        # Coder gets boost for technical questions
        if bot_name == "coder":
            if any(word in message_lower for word in ["implement", "code", "build", "technical"]):
                return min(0.95, base_urgency + 0.25)

        # Auditor gets boost for security/compliance questions
        if bot_name == "auditor":
            if any(word in message_lower for word in ["security", "privacy", "compliance", "risk"]):
                return min(0.95, base_urgency + 0.3)

        return base_urgency

    def _format_reason(self, selected_bots: List[BotUrgency]) -> str:
        """Format reason string for dispatch result."""
        if not selected_bots:
            return "No bots selected"

        bot_list = ", ".join(b.bot_name for b in selected_bots[:3])
        if len(selected_bots) > 3:
            bot_list += f" (+{len(selected_bots) - 3} more)"

        return f"SmartDiscuss: {bot_list} (urgency >= {self.speak_threshold})"


# Convenience function
async def smart_dispatch_discuss(
    message: str,
    room_id: str,
    room_manager: RoomManager,
    llm_provider,
    speak_threshold: float = 0.5,
) -> DispatchResult:
    """Convenience function for smart discuss dispatch.

    Args:
        message: User message (with @discuss removed)
        room_id: Room ID
        room_manager: Room manager
        llm_provider: LLM provider
        speak_threshold: Minimum urgency to speak

    Returns:
        DispatchResult with selected bots
    """
    dispatcher = SmartDispatch(room_manager, llm_provider, speak_threshold)
    return await dispatcher.dispatch_smart_discuss(message, room_id)
