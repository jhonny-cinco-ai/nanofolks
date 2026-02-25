"""Context assembly for memory integration with the agent.

This module implements Phase 5 of the memory proposal:
- Token-budgeted context assembly from summaries
- Memory-aware system prompt generation
- Budget allocation across different memory sections
- Integration with agent context building

The context assembler takes pre-computed summaries and assembles them
into a context string that fits within the LLM's token budget.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from loguru import logger

from nanofolks.memory.models import Entity
from nanofolks.memory.policy import get_context_budget_overrides
from nanofolks.memory.store import TurboMemoryStore
from nanofolks.memory.summaries import SummaryTreeManager
from nanofolks.utils.ids import room_to_session_id


@dataclass
class ContextBudget:
    """Token budget allocation for different memory sections."""
    total: int = 4000  # Total token budget for memory context
    identity: int = 200  # Bot identity/persona
    state: int = 150  # Current conversation state
    knowledge: int = 500  # General knowledge from summaries
    channel: int = 300  # Channel-specific context
    entities: int = 400  # Entity summaries (per-entity)
    topics: int = 400  # Topic summaries
    preferences: int = 300  # User preferences
    learnings: int = 200  # Learned insights
    recent: int = 400  # Recent events

    def validate(self):
        """Ensure budget doesn't exceed total."""
        total_used = (
            self.identity + self.state + self.knowledge +
            self.channel + self.entities + self.topics +
            self.preferences + self.learnings + self.recent
        )
        if total_used > self.total:
            # Proportionally reduce each section
            ratio = self.total / total_used
            for key in ['identity', 'state', 'knowledge', 'channel',
                       'entities', 'topics', 'preferences', 'learnings', 'recent']:
                setattr(self, key, int(getattr(self, key) * ratio))


class ContextAssembler:
    """
    Assembles memory context for the agent from pre-computed summaries.

    This class takes the hierarchical summaries and assembles them into
    a context string that fits within the token budget. It prioritizes
    the most relevant information based on the current conversation.
    """

    def __init__(
        self,
        store: TurboMemoryStore,
        summary_manager: SummaryTreeManager,
        budget: Optional[ContextBudget] = None,
    ):
        """
        Initialize the context assembler.

        Args:
            store: TurboMemoryStore for database access
            summary_manager: SummaryTreeManager for summary access
            budget: Token budget allocation (uses default if None)
        """
        self.store = store
        self.summary_manager = summary_manager
        self.budget = budget or ContextBudget()
        self.budget.validate()

        logger.info(f"ContextAssembler initialized (budget: {self.budget.total} tokens)")

    def assemble_context(
        self,
        room_id: str,
        channel: str = None,
        entity_ids: list[str] = None,
        recent_event_ids: list[str] = None,
        include_preferences: bool = True,
        query: str | None = None,
    ) -> str:
        """
        Assemble memory context from summaries.

        Args:
            room_id: Current room (room-centric)
            channel: Current conversation channel (optional, for reference only)
            entity_ids: Entity IDs mentioned in current conversation
            recent_event_ids: Recent event IDs to include
            include_preferences: Whether to include user preferences

        Returns:
            Assembled context string
        """
        budget = self._budget_for_room(room_id)
        sections = []
        remaining_budget = budget.total

        # Section 1: Identity (always include)
        identity_context = self._get_identity_context()
        if identity_context:
            sections.append(("IDENTITY", identity_context, budget.identity))
            remaining_budget -= budget.identity

        # Section 2: Room Context (room-centric)
        room_context = self._get_room_context(room_id)
        if room_context:
            sections.append(("ROOM", room_context, budget.channel))
            remaining_budget -= budget.channel

        # Section 3: Entity Context (prioritized by relevance)
        if entity_ids:
            entity_context = self._get_entity_context(
                entity_ids=entity_ids,
                query=query,
                max_tokens=budget.entities,
            )
            if entity_context:
                sections.append(("ENTITIES", entity_context, budget.entities))
                remaining_budget -= budget.entities

        # Section 4: User Preferences (if enabled)
        if include_preferences:
            prefs_context = self._get_preferences_context()
            if prefs_context:
                sections.append(("PREFERENCES", prefs_context, budget.preferences))
                remaining_budget -= budget.preferences

        # Section 5: Recent Events
        recent_context = self._get_recent_context(
            event_ids=recent_event_ids,
            room_id=room_id,
            query=query,
            entity_ids=entity_ids,
            max_tokens=budget.recent,
        )
        if recent_context:
            sections.append(("RECENT", recent_context, budget.recent))
            remaining_budget -= budget.recent

        # Section 6: Knowledge (general summaries)
        if remaining_budget > 0:
            knowledge_context = self._get_knowledge_context(
                max_tokens=min(remaining_budget, budget.knowledge)
            )
            if knowledge_context:
                sections.append(("KNOWLEDGE", knowledge_context, len(knowledge_context) // 4))

        # Assemble final context
        return self._format_sections(sections)

    def _get_identity_context(self) -> str:
        """Get bot identity context."""
        return """You are nanofolks, an AI assistant with persistent memory.
You have access to a knowledge graph of entities, relationships, and facts from past conversations.
Use this context to provide personalized and informed responses."""

    def _get_room_context(self, room_id: str) -> str:
        """Get room-specific context from summary tree.

        Args:
            room_id: Room ID (room-centric)
        """
        room_node = self.store.get_summary_node(room_to_session_id(room_id))
        if room_node and room_node.summary:
            return f"Room: {room_id}\n{room_node.summary}"
        return ""

    def _get_entity_context(
        self,
        entity_ids: list[str],
        query: str | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Get context for specific entities (relevance-scored)."""
        if not entity_ids:
            return ""

        query_terms = self._tokenize_query(query)
        scored_items: list[tuple[float, str]] = []

        for entity_id in entity_ids:
            entity = self.store.get_entity(entity_id)
            if not entity:
                continue

            # Get entity summary from tree (preferred)
            entity_node = self.store.get_summary_node(f"entity:{entity_id}")
            if entity_node and entity_node.summary:
                text = entity_node.summary
            else:
                text = f"{entity.name} ({entity.entity_type})"

            score = float(entity.event_count or 0)
            score *= self._recency_boost(entity.last_seen)
            score += self._match_boost(text, query_terms) + self._match_boost(entity.name, query_terms)

            scored_items.append((score, text))

        return self._join_scored(scored_items, max_tokens)

    def _get_preferences_context(self) -> str:
        """Get user preferences context."""
        prefs_node = self.store.get_summary_node("user_preferences")
        if prefs_node and prefs_node.summary:
            return prefs_node.summary
        return ""

    def _get_recent_context(
        self,
        event_ids: list[str] | None,
        room_id: str,
        query: str | None = None,
        entity_ids: list[str] | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Get context from recent events (relevance-scored)."""
        query_terms = self._tokenize_query(query)
        entity_names: list[str] = []
        if entity_ids:
            for entity_id in entity_ids:
                entity = self.store.get_entity(entity_id)
                if entity:
                    entity_names.append(entity.name.lower())

        events: list = []
        if event_ids:
            for event_id in event_ids:
                event = self.store.get_event(event_id)
                if event:
                    events.append(event)
        else:
            session_key = room_to_session_id(room_id)
            events = self.store.get_events_for_session(session_key, limit=50)

        scored_items: list[tuple[float, str]] = []
        for event in events:
            content = event.content or ""
            score = self._recency_boost(event.timestamp)
            score += self._match_boost(content, query_terms)
            for name in entity_names:
                if name and name in content.lower():
                    score += 1.0
            snippet = content[:160]
            if snippet:
                scored_items.append((score, f"- {snippet}"))

        if not scored_items:
            return ""

        joined = self._join_scored(scored_items, max_tokens)
        if joined:
            return "Recent conversation:\n" + joined
        return ""

    def _join_scored(
        self,
        scored_items: Iterable[tuple[float, str]],
        max_tokens: int | None,
    ) -> str:
        if not scored_items:
            return ""
        items = sorted(scored_items, key=lambda x: x[0], reverse=True)
        if not max_tokens:
            return "\n\n".join([text for _, text in items])

        remaining = max_tokens
        selected: list[str] = []
        for _, text in items:
            cost = self._estimate_tokens(text)
            if cost > remaining:
                continue
            selected.append(text)
            remaining -= cost
            if remaining <= 0:
                break
        return "\n\n".join(selected)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    @staticmethod
    def _tokenize_query(query: str | None) -> list[str]:
        if not query:
            return []
        return [term for term in query.lower().split() if len(term) > 2]

    @staticmethod
    def _match_boost(text: str, query_terms: list[str]) -> float:
        if not text or not query_terms:
            return 0.0
        text_lower = text.lower()
        return sum(1.0 for term in query_terms if term in text_lower)

    @staticmethod
    def _recency_boost(ts) -> float:
        if not ts:
            return 1.0
        try:
            days = max(0.0, (datetime.now() - ts).total_seconds() / 86400.0)
        except Exception:
            return 1.0
        if days <= 1:
            return 3.0
        if days <= 7:
            return 2.0
        if days <= 30:
            return 1.2
        return 1.0

    def _get_knowledge_context(self, max_tokens: int) -> str:
        """Get general knowledge from summary tree."""
        # Get root summary
        root = self.store.get_summary_node("root")
        if root and root.summary:
            # Simple token estimation
            max_chars = max_tokens * 4
            if len(root.summary) > max_chars:
                return root.summary[:max_chars] + "..."
            return root.summary
        return ""

    def _format_sections(self, sections: list[tuple]) -> str:
        """Format sections into final context string."""
        parts = []

        for name, content, budget in sections:
            if content:
                parts.append(f"--- {name} ---")
                parts.append(content)
                parts.append("")  # Empty line between sections

        return "\n".join(parts).strip()

    def _budget_for_room(self, room_id: str) -> ContextBudget:
        """Apply per-room budget overrides if available."""
        overrides = get_context_budget_overrides(self.store.workspace, room_id)
        if not overrides:
            return self.budget
        data = {**self.budget.__dict__}
        data.update({k: v for k, v in overrides.items() if k in data})
        budget = ContextBudget(**data)
        budget.validate()
        return budget

    def get_relevant_entities(
        self,
        query: str,
        channel: str = None,
        room_id: str = None,
        limit: int = 5,
    ) -> list[Entity]:
        """
        Find entities relevant to the current query.

        Args:
            query: Current user query
            channel: Current channel (for filtering)
            room_id: Current room (preferred for filtering)
            limit: Max entities to return

        Returns:
            List of relevant entities
        """
        # Get entities mentioned in recent events from this channel
        if room_id:
            session_key = room_to_session_id(room_id)
            recent_entities = self.store.get_entities_for_session(session_key, limit=limit * 2)
        elif channel:
            recent_entities = self.store.get_entities_for_channel(channel, limit=limit * 2)
        else:
            # Get most frequently mentioned entities
            recent_entities = self.store.get_entities_by_type("person", limit=limit * 2)

        # Score by recency and frequency
        scored = []
        for entity in recent_entities:
            score = entity.event_count
            if entity.last_seen:
                # Boost recently seen entities
                from datetime import datetime
                days_since = (datetime.now() - entity.last_seen).days
                if days_since < 7:
                    score *= 2  # Double score for recent mentions

            scored.append((entity, score))

        # Sort by score and return top
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:limit]]


def create_context_assembler(
    store: TurboMemoryStore,
    summary_manager: SummaryTreeManager,
    budget: Optional[ContextBudget] = None,
) -> ContextAssembler:
    """
    Factory function to create a ContextAssembler.

    Args:
        store: TurboMemoryStore instance
        summary_manager: SummaryTreeManager instance
        budget: Optional custom budget

    Returns:
        ContextAssembler instance
    """
    return ContextAssembler(store, summary_manager, budget)
