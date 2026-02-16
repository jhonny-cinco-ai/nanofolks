"""nanofolks Memory System

A lightweight, local-first memory system for the nanofolks AI assistant.
Provides semantic search, entity tracking, and knowledge graph capabilities.
"""

from nanofolks.memory.models import (
    Event,
    Entity,
    Edge,
    Fact,
    Topic,
    SummaryNode,
    Learning,
)
from nanofolks.memory.store import TurboMemoryStore
from nanofolks.memory.embeddings import (
    EmbeddingProvider,
    pack_embedding,
    unpack_embedding,
    cosine_similarity,
)
from nanofolks.memory.background import (
    ActivityTracker,
    BackgroundProcessor,
)
from nanofolks.memory.extraction import (
    Gliner2Extractor,
    ExtractionResult,
    extract_entities,
)
from nanofolks.memory.graph import (
    KnowledgeGraphManager,
    create_entity_resolver,
)
from nanofolks.memory.summaries import (
    SummaryTreeManager,
    create_summary_manager,
)
from nanofolks.memory.context import (
    ContextAssembler,
    ContextBudget,
    create_context_assembler,
)
from nanofolks.memory.retrieval import (
    MemoryRetrieval,
    create_retrieval,
)
from nanofolks.memory.learning import (
    LearningManager,
    FeedbackDetector,
    create_learning_manager,
)
from nanofolks.memory.preferences import (
    PreferencesAggregator,
    create_preferences_aggregator,
)
from nanofolks.memory.bot_memory import (
    BotMemory,
    SharedMemoryPool,
    CrossPollination,
    BotExpertise,
)

__all__ = [
    "Event",
    "Entity",
    "Edge",
    "Fact",
    "Topic",
    "SummaryNode",
    "Learning",
    "TurboMemoryStore",
    "EmbeddingProvider",
    "pack_embedding",
    "unpack_embedding",
    "cosine_similarity",
    "ActivityTracker",
    "BackgroundProcessor",
    "Gliner2Extractor",
    "ExtractionResult",
    "extract_entities",
    "KnowledgeGraphManager",
    "create_entity_resolver",
    "SummaryTreeManager",
    "create_summary_manager",
    "ContextAssembler",
    "ContextBudget",
    "create_context_assembler",
    "MemoryRetrieval",
    "create_retrieval",
    "LearningManager",
    "FeedbackDetector",
    "create_learning_manager",
    "PreferencesAggregator",
    "create_preferences_aggregator",
    "BotMemory",
    "SharedMemoryPool",
    "CrossPollination",
    "BotExpertise",
]
