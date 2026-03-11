"""RoomSessionManager: Manages sessions per room instead of per bot.

This module provides the RoomSessionManager class, which manages session
state on a per-room basis rather than per-bot. This allows multiple bots
to share the same conversation context within a room.

Key features:
- One session per room (shared by all bots in that room)
- Persistent conversation history across bot switches
- Room-level memory and context
- Thread-safe operations with async locks
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from nanofolks.config.loader import get_data_dir
from nanofolks.session.manager import Session


class RoomSession:
    """Session data for a room.

    This is similar to Session but optimized for room-centric usage
    with support for multiple bot participants.
    """

    def __init__(
        self,
        room_id: str,
        workspace: Path,
        participants: Optional[List[str]] = None,
    ):
        self.room_id = room_id
        self.workspace = workspace
        self.participants = participants or ["leader"]
        self.messages: List[Dict] = []
        self.metadata: Dict = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def key(self) -> str:
        """Session key for compatibility with regular Session.

        Returns:
            Room ID as the session key
        """
        return self.room_id

    def clear(self) -> None:
        """Clear all messages and metadata (compatibility with Session)."""
        self.messages = []
        self.metadata = {}
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str, bot_name: Optional[str] = None) -> None:
        """Add a message to the session.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            bot_name: Optional bot name for assistant messages
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if bot_name and role == "assistant":
            message["bot_name"] = bot_name

        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_history(self, max_messages: Optional[int] = None) -> List[Dict]:
        """Get conversation history.

        Args:
            max_messages: Maximum number of messages to return (None for all)

        Returns:
            List of message dicts
        """
        if max_messages:
            return self.messages[-max_messages:]
        return self.messages.copy()

    def get_last_messages(self, n: int = 10) -> List[Dict]:
        """Get last N messages.

        Args:
            n: Number of messages

        Returns:
            List of last N messages
        """
        return self.messages[-n:] if n < len(self.messages) else self.messages.copy()

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "room_id": self.room_id,
            "participants": self.participants,
            "messages": self.messages,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict, workspace: Path) -> "RoomSession":
        """Create RoomSession from dictionary."""
        session = cls(
            room_id=data["room_id"],
            workspace=workspace,
            participants=data.get("participants", ["leader"]),
        )
        session.messages = data.get("messages", [])
        session.metadata = data.get("metadata", {})
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        return session


class RoomSessionManager:
    """Manages sessions per room, not per bot.

    The RoomSessionManager provides a centralized way to manage conversation
    sessions on a per-room basis. All bots in the same room share the same
    session, enabling proper context sharing and persistence.

    Attributes:
        workspace: Path to workspace directory
        sessions_dir: Directory for session persistence
        room_sessions: Dict mapping room_id to RoomSession
        _lock: Async lock for thread-safe operations
    """

    def __init__(self, workspace: Path):
        """Initialize the RoomSessionManager.

        Args:
            workspace: Path to workspace directory
        """
        self.workspace = workspace
        self.data_dir = get_data_dir()
        self.sessions_dir = self.data_dir / "room_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache of room sessions
        self.room_sessions: Dict[str, RoomSession] = {}

        # Thread safety
        self._lock = asyncio.Lock()

        self.logger = logger.bind(component="RoomSessionManager")
        self.logger.info(f"RoomSessionManager initialized: {self.sessions_dir}")

    async def get_session(self, room_id: str) -> RoomSession:
        """Get session for a room (shared by all bots in room).

        If the session doesn't exist in memory, attempts to load from disk.
        If not on disk, creates a new session.

        Args:
            room_id: Room identifier

        Returns:
            RoomSession instance
        """
        async with self._lock:
            # Check memory cache
            if room_id in self.room_sessions:
                return self.room_sessions[room_id]

            # Try to load from disk
            session = await self._load_session(room_id)
            if session:
                self.room_sessions[room_id] = session
                self.logger.debug(f"Loaded session for room: {room_id}")
                return session

            # Create new session
            session = RoomSession(
                room_id=room_id,
                workspace=self.workspace,
            )
            self.room_sessions[room_id] = session
            self.logger.info(f"Created new session for room: {room_id}")

            # Persist immediately
            await self._save_session_internal(room_id, session)

            return session

    def get_or_create(self, room_id: str) -> RoomSession:
        """Synchronous wrapper for get_or_create compatibility with AgentLoop.

        This method provides a synchronous interface that matches SessionManager
        for backward compatibility. It runs the async get_session in the event loop.

        Args:
            room_id: Room identifier (used as session key)

        Returns:
            RoomSession instance
        """
        import asyncio

        try:
            # Try to get the running event loop
            loop = asyncio.get_running_loop()
            # If we're already in an async context, create a task
            if loop.is_running():
                # This is a hack for compatibility - in practice this should be async
                # For now, return a new session synchronously
                if room_id not in self.room_sessions:
                    # Create synchronously (will be saved on first async save)
                    self.room_sessions[room_id] = RoomSession(
                        room_id=room_id,
                        workspace=self.workspace,
                    )
                return self.room_sessions[room_id]
        except RuntimeError:
            # No event loop running, create one
            pass

        # Run async method synchronously
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule in running loop and return immediately
                # The session will be loaded/created on first async access
                if room_id not in self.room_sessions:
                    self.room_sessions[room_id] = RoomSession(
                        room_id=room_id,
                        workspace=self.workspace,
                    )
                return self.room_sessions[room_id]
            else:
                return loop.run_until_complete(self.get_session(room_id))
        except Exception:
            # Fallback: create new session
            if room_id not in self.room_sessions:
                self.room_sessions[room_id] = RoomSession(
                    room_id=room_id,
                    workspace=self.workspace,
                )
            return self.room_sessions[room_id]

    def save(self, session: RoomSession) -> None:
        """Synchronously save session to memory (async save to disk happens automatically).

        Args:
            session: RoomSession instance to save
        """
        if session and hasattr(session, "room_id"):
            self.room_sessions[session.room_id] = session
            # Schedule async save
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule background save
                    asyncio.create_task(self.save_session(session.room_id))
            except Exception:
                pass  # Ignore errors in synchronous context

    async def save_session(self, room_id: str) -> bool:
        """Persist session to disk.

        Args:
            room_id: Room identifier

        Returns:
            True if saved successfully
        """
        async with self._lock:
            if room_id not in self.room_sessions:
                self.logger.warning(f"Cannot save: session not found for room: {room_id}")
                return False

            return await self._save_session_internal(room_id, self.room_sessions[room_id])

    async def _save_session_internal(self, room_id: str, session: RoomSession) -> bool:
        """Internal save method (must hold lock).

        Args:
            room_id: Room identifier
            session: Session to save

        Returns:
            True if saved successfully
        """
        try:
            session_file = self.sessions_dir / f"{room_id}.json"
            session_data = session.to_dict()

            # Write atomically
            temp_file = session_file.with_suffix(".tmp")
            temp_file.write_text(json.dumps(session_data, indent=2, default=str))
            temp_file.replace(session_file)

            self.logger.debug(f"Saved session for room: {room_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save session for room {room_id}: {e}")
            return False

    async def _load_session(self, room_id: str) -> Optional[RoomSession]:
        """Load session from disk.

        Args:
            room_id: Room identifier

        Returns:
            RoomSession or None if not found
        """
        try:
            session_file = self.sessions_dir / f"{room_id}.json"
            if not session_file.exists():
                return None

            data = json.loads(session_file.read_text())
            return RoomSession.from_dict(data, self.workspace)

        except Exception as e:
            self.logger.error(f"Failed to load session for room {room_id}: {e}")
            return None

    async def add_participant(self, room_id: str, bot_name: str) -> bool:
        """Add a bot participant to a room session.

        Args:
            room_id: Room identifier
            bot_name: Bot name to add

        Returns:
            True if added (or already present)
        """
        async with self._lock:
            session = await self.get_session(room_id)

            if bot_name not in session.participants:
                session.participants.append(bot_name)
                await self._save_session_internal(room_id, session)
                self.logger.info(f"Added {bot_name} to room {room_id}")

            return True

    async def remove_participant(self, room_id: str, bot_name: str) -> bool:
        """Remove a bot participant from a room session.

        Args:
            room_id: Room identifier
            bot_name: Bot name to remove

        Returns:
            True if removed (or not present)
        """
        async with self._lock:
            session = await self.get_session(room_id)

            if bot_name in session.participants:
                session.participants.remove(bot_name)
                await self._save_session_internal(room_id, session)
                self.logger.info(f"Removed {bot_name} from room {room_id}")

            return True

    async def get_participants(self, room_id: str) -> List[str]:
        """Get list of bot participants in a room.

        Args:
            room_id: Room identifier

        Returns:
            List of bot names
        """
        session = await self.get_session(room_id)
        return session.participants.copy()

    async def clear_session(self, room_id: str) -> bool:
        """Clear a room session (delete all messages).

        Args:
            room_id: Room identifier

        Returns:
            True if cleared
        """
        async with self._lock:
            if room_id in self.room_sessions:
                self.room_sessions[room_id].messages = []
                self.room_sessions[room_id].metadata = {}
                await self._save_session_internal(room_id, self.room_sessions[room_id])
                self.logger.info(f"Cleared session for room: {room_id}")

            # Also delete from disk
            session_file = self.sessions_dir / f"{room_id}.json"
            if session_file.exists():
                session_file.unlink()

            return True

    async def delete_session(self, room_id: str) -> bool:
        """Delete a room session completely.

        Args:
            room_id: Room identifier

        Returns:
            True if deleted
        """
        async with self._lock:
            # Remove from memory
            if room_id in self.room_sessions:
                del self.room_sessions[room_id]

            # Remove from disk
            session_file = self.sessions_dir / f"{room_id}.json"
            if session_file.exists():
                session_file.unlink()

            self.logger.info(f"Deleted session for room: {room_id}")
            return True

    async def list_rooms(self) -> List[str]:
        """List all rooms with sessions.

        Returns:
            List of room IDs
        """
        rooms = set(self.room_sessions.keys())

        # Also check disk
        if self.sessions_dir.exists():
            for session_file in self.sessions_dir.glob("*.json"):
                room_id = session_file.stem
                rooms.add(room_id)

        return sorted(list(rooms))

    async def get_session_stats(self, room_id: str) -> Optional[Dict]:
        """Get statistics for a room session.

        Args:
            room_id: Room identifier

        Returns:
            Stats dict or None if not found
        """
        session = await self.get_session(room_id)
        if not session:
            return None

        return {
            "room_id": room_id,
            "message_count": len(session.messages),
            "participants": session.participants,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }

    async def save_all_sessions(self) -> int:
        """Save all in-memory sessions to disk.

        Returns:
            Number of sessions saved
        """
        async with self._lock:
            count = 0
            for room_id, session in self.room_sessions.items():
                if await self._save_session_internal(room_id, session):
                    count += 1

            self.logger.info(f"Saved {count} sessions to disk")
            return count

    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Delete sessions older than specified days.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of sessions deleted
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)
        deleted = 0

        async with self._lock:
            # Check disk sessions
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    data = json.loads(session_file.read_text())
                    updated_at = datetime.fromisoformat(data["updated_at"])

                    if updated_at < cutoff:
                        room_id = session_file.stem

                        # Remove from memory if present
                        if room_id in self.room_sessions:
                            del self.room_sessions[room_id]

                        # Delete file
                        session_file.unlink()
                        deleted += 1
                        self.logger.debug(f"Deleted old session: {room_id}")

                except Exception as e:
                    self.logger.warning(f"Error checking session file {session_file}: {e}")

        if deleted > 0:
            self.logger.info(f"Cleaned up {deleted} old sessions")

        return deleted


# Convenience function
def create_room_session_manager(workspace: Path) -> RoomSessionManager:
    """Create a RoomSessionManager instance.

    Args:
        workspace: Path to workspace directory

    Returns:
        RoomSessionManager instance
    """
    return RoomSessionManager(workspace)
