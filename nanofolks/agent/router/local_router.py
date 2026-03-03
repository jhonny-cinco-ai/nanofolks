"""Local Apple Foundation Model router for experimental routing."""

import json
from typing import Any, Optional

from loguru import logger

from .models import RoutingDecision, RoutingTier


LOCAL_UNIFIED_PROMPT = """Classify the user's message for a multi-agent AI system:

1. INTENT:
- build: creating or developing something new
- explore: brainstorming, monetization, or business ideas
- advice: how-to questions, recommendations, or help
- research: finding information, learning about a topic
- task: specific actions like writing, summarizing, or analyzing
- chat: general conversation, greetings, or follow-up questions

2. TIER (Complexity):
- SIMPLE: quick facts, greetings, thanks, simple questions
- MEDIUM: explanations, searches, simple tasks
- CODING: code writing, debugging, implementations
- COMPLEX: multi-step tasks, architecture, complex debugging
- REASONING: proofs, logic, math

Respond with only JSON:
{{"intent": "build|explore|advice|research|task|chat", "tier": "SIMPLE|MEDIUM|CODING|COMPLEX|REASONING", "confidence": 0.0-1.0, "reasoning": "..."}}

Message: {content}
"""


class LocalRouter:
    """
    Experimental local Apple Foundation Model router.

    Uses Apple's on-device Foundation Models (via python-apple-fm-sdk)
    for classification when available. Falls back gracefully if unavailable.
    """

    def __init__(
        self,
        fallback_to_api: bool = True,
    ):
        self.fallback_to_api = fallback_to_api
        self._model = None
        self._available = None
        self._last_content = None
        self._last_result = None
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Apple Foundation Model is available."""
        try:
            import apple_fm_sdk as fm

            model = fm.SystemLanguageModel()
            is_available, reason = model.is_available()
            if is_available:
                self._model = model
                self._available = True
                logger.info("Apple Foundation Model is available for local routing")
            else:
                self._available = False
                logger.warning(f"Apple Foundation Model not available: {reason}")
        except ImportError:
            self._available = False
            logger.warning("apple-fm-sdk not installed, local routing unavailable")
        except Exception as e:
            self._available = False
            logger.warning(f"Failed to initialize Apple Foundation Model: {e}")

    async def warmup(self) -> None:
        """Pre-warm the local model to eliminate cold start delay on first use."""
        if not self.is_available():
            return

        try:
            import apple_fm_sdk as fm

            prompt = LOCAL_UNIFIED_PROMPT.format(content="hello")
            session = fm.LanguageModelSession()
            response = await session.respond(prompt)
            logger.info("Local model warmed up and ready")
        except Exception as e:
            logger.warning(f"Failed to warm up local model: {e}")

    async def classify_unified(
        self,
        content: str,
    ) -> Optional[dict[str, Any]]:
        """
        Run unified classification (Intent + Tier) using local model.
        Caches result to avoid redundant on-device inference.
        """
        if not self.is_available():
            return None

        # Check cache
        if content == self._last_content and self._last_result:
            return self._last_result

        try:
            import apple_fm_sdk as fm

            prompt = LOCAL_UNIFIED_PROMPT.format(content=content)

            session = fm.LanguageModelSession()
            response = await session.respond(prompt)
            logger.debug(f"Local unified classification raw response: {response}")

            result = self._parse_json_robust(response)

            # 1. Parse Intent
            raw_intent = result.get("intent")
            valid_intents = ["build", "explore", "advice", "research", "task", "chat"]
            cleaned_intent = None
            if raw_intent:
                cleaned_intent = str(raw_intent).lower()
                if "|" in cleaned_intent:
                    cleaned_intent = cleaned_intent.split("|")[0].strip()
                if cleaned_intent not in valid_intents:
                    cleaned_intent = None
            if not cleaned_intent:
                for valid in valid_intents:
                    if valid in response.lower():
                        cleaned_intent = valid
                        break
            if not cleaned_intent:
                cleaned_intent = "chat"

            # 2. Parse Tier
            raw_tier = result.get("tier")
            valid_tiers = ["SIMPLE", "MEDIUM", "CODING", "COMPLEX", "REASONING"]
            cleaned_tier = None
            if raw_tier:
                cleaned_tier = str(raw_tier).upper()
                if "|" in cleaned_tier:
                    cleaned_tier = cleaned_tier.split("|")[0].strip()
                if cleaned_tier not in valid_tiers:
                    cleaned_tier = None
            if not cleaned_tier:
                for valid in valid_tiers:
                    if f'"{valid}"' in response.upper() or f"'{valid}'" in response.upper():
                        cleaned_tier = valid
                        break
            if not cleaned_tier:
                cleaned_tier = "MEDIUM"

            unified_result = {
                "intent": cleaned_intent,
                "tier": cleaned_tier,
                "confidence": result.get("confidence", 0.7),
                "reasoning": result.get("reasoning", "Unified local classification"),
                "needs_tools": cleaned_tier not in ["SIMPLE"],
                "model": "apple-on-device",
            }

            self._last_content = content
            self._last_result = unified_result
            return unified_result

        except Exception as e:
            logger.error(f"Local unified classification failed: {e}")
            return None

    def is_available(self) -> bool:
        """Check if local model is available."""
        return self._available is True

    async def classify_intent(
        self,
        content: str,
    ) -> Optional[dict[str, Any]]:
        """Backwards compatibility for intent-only classification."""
        return await self.classify_unified(content)

    def _parse_json_robust(self, response: str) -> dict[str, Any]:
        """Generic robust JSON parser for local model responses."""
        content = response.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(content)
            if not isinstance(result, dict):
                return {}

            # Clean keys
            return {k.strip().strip('"').strip("'"): v for k, v in result.items()}
        except Exception:
            return {}

    async def classify(
        self,
        content: str,
    ) -> Optional[RoutingDecision]:
        """
        Classify content using local Apple Foundation Model (Unified check).
        """
        unified = await self.classify_unified(content)
        if not unified:
            return None

        return RoutingDecision(
            tier=RoutingTier(unified["tier"].lower()),
            model="apple-on-device",
            confidence=unified["confidence"],
            layer="local",
            reasoning=unified["reasoning"],
            estimated_tokens=self._estimate_tokens(content),
            needs_tools=unified["needs_tools"],
            metadata={"local_model": "apple-foundation", "unified": True},
        )

    def _fallback_parse(self, response: str) -> dict[str, Any]:
        """Fallback parsing when JSON is not valid (case-insensitive)."""
        response_lower = response.lower()
        if "simple" in response_lower:
            tier = "SIMPLE"
        elif "coding" in response_lower or "code" in response_lower:
            tier = "CODING"
        elif "complex" in response_lower:
            tier = "COMPLEX"
        elif "reasoning" in response_lower or "proof" in response_lower:
            tier = "REASONING"
        else:
            tier = "MEDIUM"

        return {
            "tier": tier,
            "confidence": 0.6,
            "reasoning": "Parsed from non-JSON response",
            "needs_tools": tier != "SIMPLE",
        }

    def _estimate_tokens(self, content: str) -> int:
        """Rough token estimation."""
        return len(content.split()) * 4 // 3
