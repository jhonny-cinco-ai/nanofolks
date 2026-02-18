"""Room management with default General room.

Automatically creates and manages rooms, including a default
"General" room that exists on first run with Leader ready to go.
"""

import json
import secrets
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from loguru import logger

from nanofolks.config.loader import get_data_dir
from nanofolks.models.room import Room, RoomType


class RoomManager:
    """Manages all rooms with automatic default creation.
    
    Supports room-centric architecture where channels can join rooms
    for cross-platform conversation continuity.
    """
    
    # Default room that always exists
    DEFAULT_ROOM_ID = "general"
    DEFAULT_ROOM_NAME = "General"
    
    def __init__(self):
        """Initialize room manager."""
        self.config_dir = get_data_dir()
        self.rooms_dir = self.config_dir / "rooms"
        self.rooms_dir.mkdir(parents=True, exist_ok=True)
        
        self._rooms: Dict[str, Room] = {}
        
        # Channel-to-room mapping for room-centric architecture
        # Key: "channel:chat_id" (e.g., "telegram:123456"), Value: "room_id"
        self._channel_mappings: Dict[str, str] = {}
        self._mappings_file = self.rooms_dir / "channel_mappings.json"
        self._load_channel_mappings()
        
        self._load_or_create_default()
    
    def _load_or_create_default(self) -> None:
        """Load existing rooms or create default General room."""
        # Try to load existing rooms
        room_files = list(self.rooms_dir.glob("*.json"))
        
        if room_files:
            # Load all existing rooms
            for room_file in room_files:
                try:
                    room_data = json.loads(room_file.read_text())
                    room = self._room_from_dict(room_data)
                    self._rooms[room.id] = room
                    logger.debug(f"Loaded room: {room.id}")
                except Exception as e:
                    logger.warning(f"Failed to load room {room_file}: {e}")
        
        # Ensure General room exists
        if self.DEFAULT_ROOM_ID not in self._rooms:
            self._create_default_room()
    
    def _create_default_room(self) -> None:
        """Create the default General room with Leader."""
        general = Room(
            id=self.DEFAULT_ROOM_ID,
            type=RoomType.OPEN,
            participants=["leader"],  # Only Leader initially
            owner="user",
            created_at=datetime.now(),
        )
        
        self._rooms[self.DEFAULT_ROOM_ID] = general
        self._save_room(general)
        
        logger.info(f"Created default '{self.DEFAULT_ROOM_NAME}' room with Leader")
    
    def _save_room(self, room: Room) -> None:
        """Save room to disk."""
        room_file = self.rooms_dir / f"{room.id}.json"
        room_data = self._room_to_dict(room)
        room_file.write_text(json.dumps(room_data, indent=2, default=str))
    
    def _room_to_dict(self, room: Room) -> dict:
        """Convert room to dictionary."""
        return {
            "id": room.id,
            "type": room.type.value,
            "participants": room.participants,
            "owner": room.owner,
            "created_at": room.created_at.isoformat(),
            "summary": room.summary,
            "auto_archive": room.auto_archive,
            "coordinator_mode": room.coordinator_mode,
        }
    
    def _room_from_dict(self, data: dict) -> Room:
        """Create room from dictionary."""
        return Room(
            id=data["id"],
            type=RoomType(data["type"]),
            participants=data.get("participants", []),
            owner=data.get("owner", "user"),
            created_at=datetime.fromisoformat(data["created_at"]),
            summary=data.get("summary", ""),
            auto_archive=data.get("auto_archive", False),
            coordinator_mode=data.get("coordinator_mode", False),
        )
    
    @property
    def default_room(self) -> Room:
        """Get the default General room.
        
        Returns:
            General room (always exists)
        """
        return self._rooms[self.DEFAULT_ROOM_ID]
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Room or None if not found
        """
        return self._rooms.get(room_id)

    def _generate_short_id(self) -> str:
        """Generate a unique 8-character alphanumeric short ID.
        
        Returns:
            8-char alphanumeric string
        """
        chars = "abcdefghijkmnpqrstuvwxyz23456789"
        return "".join(secrets.choice(chars) for _ in range(8))
    
    def _generate_unique_room_id(self, base_name: str) -> str:
        """Generate a unique room ID with short_id prefix.
        
        Args:
            base_name: Base name for the room (e.g., "website", "marketing-campaign")
            
        Returns:
            Unique room ID in format: short_id-base_name_slug
        """
        slug = base_name.lower().replace(" ", "-").replace("_", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        
        max_attempts = 10
        for _ in range(max_attempts):
            short_id = self._generate_short_id()
            room_id = f"{short_id}-{slug}"
            if room_id not in self._rooms:
                return room_id
        
        raise RuntimeError(f"Could not generate unique room ID after {max_attempts} attempts")
    
    def create_room(
        self,
        name: str,
        room_type: RoomType = RoomType.PROJECT,
        participants: Optional[List[str]] = None,
        use_short_id: bool = True,
    ) -> Room:
        """Create a new room.
        
        Args:
            name: Room name (becomes ID)
            room_type: Type of room
            participants: Initial bot participants (defaults to ["leader"])
            use_short_id: If True, prepend unique 8-char short_id to room_id
            
        Returns:
            Created room
        """
        if use_short_id:
            room_id = self._generate_unique_room_id(name)
        else:
            room_id = name.lower().replace(" ", "-").replace("_", "-")
        
        if room_id in self._rooms:
            raise ValueError(f"Room '{name}' already exists")
        
        if participants is None:
            participants = ["leader"]
        
        room = Room(
            id=room_id,
            type=room_type,
            participants=participants,
            owner="user",
            created_at=datetime.now(),
        )
        
        self._rooms[room_id] = room
        self._save_room(room)
        
        logger.info(f"Created room '{name}' with ID '{room_id}' and {len(participants)} bots")
        return room
    
    def invite_bot(self, room_id: str, bot_name: str) -> bool:
        """Invite a bot to a room.
        
        Args:
            room_id: Target room
            bot_name: Bot to invite
            
        Returns:
            True if invited, False if already present
        """
        room = self._rooms.get(room_id)
        if not room:
            logger.error(f"Room '{room_id}' not found")
            return False
        
        if bot_name in room.participants:
            logger.debug(f"Bot '{bot_name}' already in room '{room_id}'")
            return False
        
        room.add_participant(bot_name)
        self._save_room(room)
        
        logger.info(f"Invited '{bot_name}' to room '{room_id}'")
        return True
    
    def create_project_room(
        self,
        name: str,
        bots: Optional[List[str]] = None,
    ) -> Room:
        """Create a new project room and invite bots.
        
        This is a convenience method that creates a project room with
        a unique short_id-prefixed ID and invites the specified bots.
        
        Args:
            name: Room name/description (e.g., "website", "marketing-campaign")
            bots: List of bot names to invite (defaults to ["leader"])
            
        Returns:
            Created room with bots invited
        """
        if bots is None:
            bots = ["leader"]
        elif "leader" not in bots:
            bots = ["leader"] + bots
        
        room = self.create_room(
            name=name,
            room_type=RoomType.PROJECT,
            participants=bots,
            use_short_id=True,
        )
        
        logger.info(f"Created project room '{name}' with bots: {bots}")
        return room
    
    def remove_bot(self, room_id: str, bot_name: str) -> bool:
        """Remove a bot from a room.
        
        Args:
            room_id: Target room
            bot_name: Bot to remove
            
        Returns:
            True if removed, False if not present or room not found
        """
        room = self._rooms.get(room_id)
        if not room:
            return False
        
        if bot_name not in room.participants:
            return False
        
        # Don't remove the last bot (keep at least Leader)
        if len(room.participants) <= 1:
            logger.warning(f"Cannot remove last bot from room '{room_id}'")
            return False
        
        room.remove_participant(bot_name)
        self._save_room(room)
        
        logger.info(f"Removed '{bot_name}' from room '{room_id}'")
        return True
    
    def list_rooms(self) -> List[dict]:
        """List all rooms.
        
        Returns:
            List of room summaries
        """
        return [
            {
                "id": room.id,
                "type": room.type.value,
                "participants": room.participants,
                "participant_count": len(room.participants),
                "is_default": room.id == self.DEFAULT_ROOM_ID,
            }
            for room in self._rooms.values()
        ]
    
    def get_room_participants(self, room_id: str) -> List[str]:
        """Get list of bots in a room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            List of bot names (empty if room not found)
        """
        room = self._rooms.get(room_id)
        if room:
            return room.participants.copy()
        return []
    
    # ========================================================================
    # Room-Centric Architecture: Channel-to-Room Mapping
    # ========================================================================
    
    def _load_channel_mappings(self) -> None:
        """Load channel-to-room mappings from disk."""
        if self._mappings_file.exists():
            try:
                with open(self._mappings_file, 'r') as f:
                    self._channel_mappings = json.load(f)
                logger.debug(f"Loaded {len(self._channel_mappings)} channel mappings")
            except Exception as e:
                logger.warning(f"Failed to load channel mappings: {e}")
                self._channel_mappings = {}
    
    def _save_channel_mappings(self) -> None:
        """Save channel-to-room mappings to disk."""
        try:
            with open(self._mappings_file, 'w') as f:
                json.dump(self._channel_mappings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save channel mappings: {e}")
    
    def join_channel_to_room(self, channel: str, chat_id: str, room_id: str) -> bool:
        """Map a channel/chat to a room (room-centric architecture).
        
        This allows messages from this channel to be routed to the room,
        enabling cross-platform conversation continuity.
        
        Args:
            channel: Channel type (telegram, discord, slack, etc.)
            chat_id: Chat/channel identifier
            room_id: Room to join
            
        Returns:
            True if successful
        """
        # Verify room exists
        if room_id not in self._rooms:
            logger.error(f"Cannot join to non-existent room: {room_id}")
            return False
        
        # Create mapping key
        channel_key = f"{channel}:{chat_id}"
        
        # Add mapping
        self._channel_mappings[channel_key] = room_id
        self._save_channel_mappings()
        
        logger.info(f"Mapped {channel_key} -> room:{room_id}")
        return True
    
    def leave_channel_from_room(self, channel: str, chat_id: str) -> bool:
        """Remove a channel from its room.
        
        Args:
            channel: Channel type
            chat_id: Chat identifier
            
        Returns:
            True if removed, False if not mapped
        """
        channel_key = f"{channel}:{chat_id}"
        
        if channel_key in self._channel_mappings:
            room_id = self._channel_mappings[channel_key]
            del self._channel_mappings[channel_key]
            self._save_channel_mappings()
            
            logger.info(f"Removed mapping for {channel_key} (was in room:{room_id})")
            return True
        
        return False
    
    def get_room_for_channel(self, channel: str, chat_id: str) -> Optional[str]:
        """Get room ID for a channel/chat.
        
        Args:
            channel: Channel type
            chat_id: Chat identifier
            
        Returns:
            Room ID or None if not mapped
        """
        channel_key = f"{channel}:{chat_id}"
        return self._channel_mappings.get(channel_key)
    
    def get_channel_mappings_for_room(self, room_id: str) -> List[Dict[str, str]]:
        """Get all channel mappings for a room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            List of {channel, chat_id} dicts
        """
        mappings = []
        for channel_key, rid in self._channel_mappings.items():
            if rid == room_id:
                parts = channel_key.split(":", 1)
                if len(parts) == 2:
                    mappings.append({
                        "channel": parts[0],
                        "chat_id": parts[1]
                    })
        return mappings
    
    def auto_join_to_general(self, channel: str, chat_id: str) -> str:
        """Auto-join a channel to the general room if not mapped.
        
        Args:
            channel: Channel type
            chat_id: Chat identifier
            
        Returns:
            Room ID (general or existing mapping)
        """
        existing = self.get_room_for_channel(channel, chat_id)
        if existing:
            return existing
        
        # Auto-join to general
        self.join_channel_to_room(channel, chat_id, self.DEFAULT_ROOM_ID)
        logger.info(f"Auto-joined {channel}:{chat_id} to room:general")
        return self.DEFAULT_ROOM_ID


# Global instance
_room_manager: Optional[RoomManager] = None


def get_room_manager() -> RoomManager:
    """Get the global room manager.
    
    Returns:
        RoomManager instance (creates if needed)
    """
    global _room_manager
    if _room_manager is None:
        _room_manager = RoomManager()
    return _room_manager


def reset_room_manager() -> None:
    """Reset the global room manager (forces reload)."""
    global _room_manager
    _room_manager = None
