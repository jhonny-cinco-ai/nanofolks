"""DEPRECATED: Old file-based memory system.

This module is deprecated and will be removed in a future version.
Use nanobot.memory.store.TurboMemoryStore instead.
"""

import warnings
from pathlib import Path

from nanobot.memory.store import TurboMemoryStore
from nanobot.config.loader import load_config

warnings.warn(
    "nanobot.agent.memory is deprecated. "
    "Use nanobot.memory.store.TurboMemoryStore instead.",
    DeprecationWarning,
    stacklevel=2
)


class MemoryStore:
    """
    DEPRECATED: Wrapper around TurboMemoryStore for backward compatibility.
    
    This class exists only for backward compatibility. New code should use
    TurboMemoryStore directly from nanobot.memory.store.
    """
    
    def __init__(self, workspace: Path):
        """Initialize with deprecation warning."""
        warnings.warn(
            "MemoryStore is deprecated. Use TurboMemoryStore instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        config = load_config()
        self._store = TurboMemoryStore(config.memory, workspace)
    
    def get_today_file(self) -> Path:
        """DEPRECATED: Get path to today's memory file."""
        raise NotImplementedError("This method is no longer supported. Use TurboMemoryStore.get_recent_events()")
    
    def read_today(self) -> str:
        """DEPRECATED: Read today's memory notes."""
        raise NotImplementedError("This method is no longer supported. Use TurboMemoryStore.get_recent_events()")
    
    def append_today(self, content: str) -> None:
        """DEPRECATED: Append content to today's memory notes."""
        raise NotImplementedError("This method is no longer supported. Use TurboMemoryStore.save_event()")
    
    def read_long_term(self) -> str:
        """DEPRECATED: Read long-term memory (MEMORY.md)."""
        raise NotImplementedError("This method is no longer supported. Use TurboMemoryStore.get_memory_context()")
    
    def write_long_term(self, content: str) -> None:
        """DEPRECATED: Write to long-term memory (MEMORY.md)."""
        raise NotImplementedError("This method is no longer supported. Use TurboMemoryStore.save_event()")
    
    def get_recent_memories(self, days: int = 7) -> str:
        """DEPRECATED: Get memories from the last N days."""
        raise NotImplementedError("This method is no longer supported. Use TurboMemoryStore.get_recent_events()")
    
    def list_memory_files(self) -> list[Path]:
        """DEPRECATED: List all memory files sorted by date (newest first)."""
        raise NotImplementedError("This method is no longer supported.")
    
    def get_memory_context(self) -> str:
        """Get memory context for the agent (delegates to TurboMemoryStore)."""
        return self._store.get_memory_context()
