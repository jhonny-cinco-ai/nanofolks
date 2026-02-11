"""nanobot Memory System

A lightweight, local-first memory system for the nanobot AI assistant.
Provides semantic search, entity tracking, and knowledge graph capabilities.
"""

from nanobot.memory.models import (
    Event,
    Entity,
    Edge,
    Fact,
    Topic,
    SummaryNode,
    Learning,
)
from nanobot.memory.store import MemoryStore
from nanobot.memory.embeddings import (
    EmbeddingProvider,
    pack_embedding,
    unpack_embedding,
    cosine_similarity,
)
from nanobot.memory.background import (
    ActivityTracker,
    BackgroundProcessor,
)
from nanobot.memory.extraction import (
    Gliner2Extractor,
    ExtractionResult,
    extract_entities,
)
from nanobot.memory.graph import (
    KnowledgeGraphManager,
    create_entity_resolver,
)

__all__ = [
    "Event",
    "Entity",
    "Edge",
    "Fact",
    "Topic",
    "SummaryNode",
    "Learning",
    "MemoryStore",
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
]
