"""Room registry for true room-centric architecture.

This module implements the core room management system where rooms are
named entities (like 'general', 'project-website') that channels can join,
rather than sessions being tied to specific channels.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from loguru import logger


@dataclass
class RoomMember:
    """A member (user or channel) in a room."""
    id: str  # Unique member ID
    member_type: str  # 'user', 'channel', 'bot'
    channel: Optional[str] = None  # For channel members: telegram, discord, etc.
    chat_id: Optional[str] = None  # For channel members: chat ID
    joined_at: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Room:
    """A room where conversations and collaboration happen.
    
    Rooms are the primary entity in room-centric architecture.
    Channels join rooms to participate, not the other way around.
    """
    id: str  # Room ID (e.g., 'general', 'project-website')
    name: str  # Display name
    room_type: str  # 'open', 'project', 'direct', 'coordination'
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Members
    participants: List[str] = field(default_factory=list)  # Bot names
    members: List[RoomMember] = field(default_factory=list)  # All members
    
    # Context
    description: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def add_participant(self, bot_name: str) -> None:
        """Add a bot participant to the room."""
        if bot_name not in self.participants:
            self.participants.append(bot_name)
            self.updated_at = datetime.now()
    
    def remove_participant(self, bot_name: str) -> None:
        """Remove a bot participant from the room."""
        if bot_name in self.participants:
            self.participants.remove(bot_name)
            self.updated_at = datetime.now()
    
    def add_member(self, member: RoomMember) -> None:
        """Add a member (user or channel) to the room."""
        # Check if already exists
        existing = next((m for m in self.members if m.id == member.id), None)
        if existing:
            return
        self.members.append(member)
        self.updated_at = datetime.now()
    
    def remove_member(self, member_id: str) -> None:
        """Remove a member from the room."""
        self.members = [m for m in self.members if m.id != member_id]
        self.updated_at = datetime.now()
    
    def get_channel_mappings(self) -> List[Dict[str, str]]:
        """Get all channel mappings for this room."""
        return [
            {"channel": m.channel, "chat_id": m.chat_id}
            for m in self.members
            if m.member_type == "channel" and m.channel and m.chat_id
        ]
    
    def to_dict(self) -> dict:
        """Convert room to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "room_type": self.room_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "participants": self.participants,
            "members": [
                {
                    "id": m.id,
                    "member_type": m.member_type,
                    "channel": m.channel,
                    "chat_id": m.chat_id,
                    "joined_at": m.joined_at.isoformat(),
                    "metadata": m.metadata
                }
                for m in self.members
            ],
            "description": self.description,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Room":
        """Create room from dictionary."""
        room = cls(
            id=data["id"],
            name=data["name"],
            room_type=data["room_type"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            participants=data.get("participants", []),
            description=data.get("description", ""),
            metadata=data.get("metadata", {})
        )
        
        # Restore members
        for m_data in data.get("members", []):
            member = RoomMember(
                id=m_data["id"],
                member_type=m_data["member_type"],
                channel=m_data.get("channel"),
                chat_id=m_data.get("chat_id"),
                joined_at=datetime.fromisoformat(m_data["joined_at"]),
                metadata=m_data.get("metadata", {})
            )
            room.members.append(member)
        
        return room


class RoomRegistry:
    """Registry for managing rooms in the system.
    
    This is the core of room-centric architecture. Rooms exist as named
    entities independent of channels. Channels join rooms to participate.
    """
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.rooms_dir = workspace / ".nanofolks" / "rooms"
        self.rooms_dir.mkdir(parents=True, exist_ok=True)
        
        # Channel-to-room mapping
        self.channel_mappings: Dict[str, str] = {}  # "channel:chat_id" -> "room_id"
        
        # Cache
        self._rooms: Dict[str, Room] = {}
        self._load_channel_mappings()
    
    def _load_channel_mappings(self) -> None:
        """Load channel-to-room mappings from disk."""
        mapping_file = self.rooms_dir / "channel_mappings.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r') as f:
                    self.channel_mappings = json.load(f)
                logger.info(f"Loaded {len(self.channel_mappings)} channel mappings")
            except Exception as e:
                logger.warning(f"Failed to load channel mappings: {e}")
    
    def _save_channel_mappings(self) -> None:
        """Save channel-to-room mappings to disk."""
        mapping_file = self.rooms_dir / "channel_mappings.json"
        try:
            with open(mapping_file, 'w') as f:
                json.dump(self.channel_mappings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save channel mappings: {e}")
    
    def create_room(
        self,
        room_id: str,
        name: Optional[str] = None,
        room_type: str = "open",
        participants: Optional[List[str]] = None,
        description: str = ""
    ) -> Room:
        """Create a new room.
        
        Args:
            room_id: Unique room identifier (e.g., 'general', 'project-website')
            name: Display name (defaults to room_id)
            room_type: 'open', 'project', 'direct', 'coordination'
            participants: List of bot names to include
            description: Room description
            
        Returns:
            Created Room instance
        """
        # Check if room exists
        if self.get_room(room_id):
            raise ValueError(f"Room '{room_id}' already exists")
        
        # Create room
        room = Room(
            id=room_id,
            name=name or room_id,
            room_type=room_type,
            participants=participants or ["leader"],
            description=description
        )
        
        # Save room
        self._save_room(room)
        self._rooms[room_id] = room
        
        logger.info(f"Created room: {room_id} ({room_type})")
        return room
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Room instance or None if not found
        """
        # Check cache
        if room_id in self._rooms:
            return self._rooms[room_id]
        
        # Load from disk
        room_file = self.rooms_dir / f"{room_id}.json"
        if room_file.exists():
            try:
                with open(room_file, 'r') as f:
                    data = json.load(f)
                room = Room.from_dict(data)
                self._rooms[room_id] = room
                return room
            except Exception as e:
                logger.error(f"Failed to load room {room_id}: {e}")
        
        return None
    
    def get_or_create_room(self, room_id: str, **kwargs) -> Room:
        """Get existing room or create new one."""
        room = self.get_room(room_id)
        if room:
            return room
        return self.create_room(room_id, **kwargs)
    
    def _save_room(self, room: Room) -> None:
        """Save room to disk."""
        room_file = self.rooms_dir / f"{room.id}.json"
        try:
            with open(room_file, 'w') as f:
                json.dump(room.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save room {room.id}: {e}")
    
    def delete_room(self, room_id: str) -> bool:
        """Delete a room."""
        room_file = self.rooms_dir / f"{room_id}.json"
        
        if room_file.exists():
            room_file.unlink()
            
            # Remove from cache
            if room_id in self._rooms:
                del self._rooms[room_id]
            
            # Remove channel mappings
            channels_to_remove = [
                key for key, rid in self.channel_mappings.items()
                if rid == room_id
            ]
            for key in channels_to_remove:
                del self.channel_mappings[key]
            self._save_channel_mappings()
            
            logger.info(f"Deleted room: {room_id}")
            return True
        
        return False
    
    def list_rooms(self) -> List[Room]:
        """List all rooms."""
        rooms = []
        for room_file in self.rooms_dir.glob("*.json"):
            if room_file.name == "channel_mappings.json":
                continue
            room_id = room_file.stem
            room = self.get_room(room_id)
            if room:
                rooms.append(room)
        return rooms
    
    def join_channel_to_room(
        self,
        channel: str,
        chat_id: str,
        room_id: str
    ) -> bool:
        """Map a channel/chat to a room.
        
        This is how channels join the room-centric architecture.
        Messages from this channel/chat will be routed to the room.
        
        Args:
            channel: Channel type (telegram, discord, etc.)
            chat_id: Chat/channel identifier
            room_id: Room to join
            
        Returns:
            True if successful
        """
        # Verify room exists
        room = self.get_room(room_id)
        if not room:
            logger.error(f"Cannot join to non-existent room: {room_id}")
            return False
        
        # Create mapping key
        channel_key = f"{channel}:{chat_id}"
        
        # Add mapping
        self.channel_mappings[channel_key] = room_id
        self._save_channel_mappings()
        
        # Add channel as room member
        member = RoomMember(
            id=channel_key,
            member_type="channel",
            channel=channel,
            chat_id=chat_id
        )
        room.add_member(member)
        self._save_room(room)
        
        logger.info(f"Mapped {channel_key} -> room:{room_id}")
        return True
    
    def leave_channel_from_room(self, channel: str, chat_id: str) -> bool:
        """Remove a channel from its room."""
        channel_key = f"{channel}:{chat_id}"
        
        if channel_key in self.channel_mappings:
            room_id = self.channel_mappings[channel_key]
            del self.channel_mappings[channel_key]
            self._save_channel_mappings()
            
            # Remove from room members
            room = self.get_room(room_id)
            if room:
                room.remove_member(channel_key)
                self._save_room(room)
            
            logger.info(f"Removed mapping for {channel_key}")
            return True
        
        return False
    
    def get_room_for_channel(self, channel: str, chat_id: str) -> Optional[str]:
        """Get room ID for a channel/chat.
        
        Returns:
            Room ID or None if not mapped
        """
        channel_key = f"{channel}:{chat_id}"
        return self.channel_mappings.get(channel_key)
    
    def ensure_default_rooms(self) -> None:
        """Ensure default rooms exist (general, etc.)."""
        # Create general room if it doesn't exist
        if not self.get_room("general"):
            self.create_room(
                room_id="general",
                name="General",
                room_type="open",
                participants=["leader", "researcher", "creative", "coder", "social", "auditor"],
                description="General conversation room"
            )
            logger.info("Created default 'general' room")


def get_room_registry(workspace: Path) -> RoomRegistry:
    """Get RoomRegistry instance.
    
    Args:
        workspace: Workspace directory
        
    Returns:
        RoomRegistry instance
    """
    registry = RoomRegistry(workspace)
    registry.ensure_default_rooms()
    return registry
