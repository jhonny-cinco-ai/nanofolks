"""Room data model for multi-agent orchestration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RoomType(Enum):
    """Types of rooms in the system."""

    OPEN = "open"  # #general - all bots, casual chat
    PROJECT = "project"  # #project-x - specific team, deadline-driven
    DIRECT = "direct"  # DM @bot - 1-on-1 focused discussion
    COORDINATION = "coordination"  # leader manages when user away


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
class Message:
    """A message in a room."""

    sender: str  # Bot name or "user"
    content: str  # Message content
    timestamp: datetime  # When sent
    room_id: str  # Which room
    attachments: List[str] = field(default_factory=list)  # File paths


@dataclass
class SharedContext:
    """Shared memory for a room (all bots see this)."""

    events: List[Dict[str, Any]] = field(default_factory=list)
    """What happened (timestamped)"""

    entities: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    """Knowledge graph: people, orgs, concepts"""

    facts: List[Dict[str, Any]] = field(default_factory=list)
    """Verified truths with confidence scores"""

    artifact_chain: List[Dict[str, Any]] = field(default_factory=list)
    """Structured handoffs between bots"""


@dataclass
class Room:
    """A room for crew collaboration."""

    id: str  # "general", "project-alpha", "dm-researcher"
    name: str = ""  # Display name (e.g., "General", "Project Website")
    type: RoomType = RoomType.OPEN  # OPEN, PROJECT, DIRECT, COORDINATION
    room_type: str = "open"  # String form for compatibility

    # Participants (bots)
    participants: List[str] = field(default_factory=list)  # ["leader", "researcher"]

    # Members (users and channels)
    members: List[RoomMember] = field(default_factory=list)

    # Metadata
    owner: str = "user"  # "user" or bot name if coordination mode
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Memory
    shared_context: SharedContext = field(default_factory=SharedContext)
    history: List[Message] = field(default_factory=list)
    summary: str = ""

    # Behavior
    auto_archive: bool = False
    archive_after_days: int = 30
    coordinator_mode: bool = False
    escalation_threshold: str = "medium"  # "low", "medium", "high"

    # Metadata
    deadline: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set defaults after initialization."""
        if not self.name:
            self.name = self.id
        if not self.room_type and self.type:
            self.room_type = self.type.value

    def add_member(self, member: RoomMember) -> None:
        """Add a member to the room.

        Args:
            member: RoomMember to add
        """
        existing = [m for m in self.members if m.id == member.id]
        if not existing:
            self.members.append(member)
            self.updated_at = datetime.now()

    def remove_member(self, member_id: str) -> bool:
        """Remove a member from the room.

        Args:
            member_id: Member ID to remove

        Returns:
            True if removed, False if not found
        """
        for i, m in enumerate(self.members):
            if m.id == member_id:
                self.members.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def get_member(self, member_id: str) -> Optional[RoomMember]:
        """Get a member by ID.

        Args:
            member_id: Member ID to find

        Returns:
            RoomMember or None if not found
        """
        for m in self.members:
            if m.id == member_id:
                return m
        return None

    def add_message(self, sender: str, content: str) -> Message:
        """Add a message to room history.

        Args:
            sender: Bot name or "user"
            content: Message content

        Returns:
            Created Message object
        """
        msg = Message(
            sender=sender,
            content=content,
            timestamp=datetime.now(),
            room_id=self.id,
        )
        self.history.append(msg)
        return msg

    def add_participant(self, bot_name: str) -> None:
        """Add bot to room.

        Args:
            bot_name: Name of bot to add
        """
        if bot_name not in self.participants:
            self.participants.append(bot_name)

    def remove_participant(self, bot_name: str) -> None:
        """Remove bot from room.

        Args:
            bot_name: Name of bot to remove
        """
        if bot_name in self.participants:
            self.participants.remove(bot_name)

    def has_participant(self, bot_name: str) -> bool:
        """Check if bot is in room.

        Args:
            bot_name: Name of bot to check

        Returns:
            True if bot is participant
        """
        return bot_name in self.participants

    def is_active(self) -> bool:
        """Check if room should be archived.

        Returns:
            True if room is still active
        """
        if not self.history:
            return False

        last_activity = self.history[-1].timestamp
        days_inactive = (datetime.now() - last_activity).days
        return days_inactive < self.archive_after_days

    def get_last_message(self) -> Optional[Message]:
        """Get the most recent message in room.

        Returns:
            Last message or None if no messages
        """
        return self.history[-1] if self.history else None

    def get_participant_messages(self, bot_name: str) -> List[Message]:
        """Get all messages from specific participant.

        Args:
            bot_name: Name of bot

        Returns:
            List of messages from that bot
        """
        return [msg for msg in self.history if msg.sender == bot_name]

    def add_fact(
        self, subject: str, predicate: str, obj: str, confidence: float = 1.0
    ) -> None:
        """Add fact to shared memory.

        Args:
            subject: Subject of fact
            predicate: Relationship
            obj: Object of fact
            confidence: Confidence score (0.0-1.0)
        """
        fact = {
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }
        self.shared_context.facts.append(fact)

    def add_entity(self, entity_id: str, entity_data: Dict[str, Any]) -> None:
        """Add entity to knowledge graph.

        Args:
            entity_id: Unique entity identifier
            entity_data: Entity information
        """
        self.shared_context.entities[entity_id] = entity_data

    def add_event(self, content: str, source: str, **kwargs: Any) -> None:
        """Add event to shared history.

        Args:
            content: What happened
            source: Where event came from
            **kwargs: Additional event data
        """
        event = {
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.shared_context.events.append(event)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize room to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value if isinstance(self.type, RoomType) else self.type,
            "room_type": self.room_type,
            "participants": self.participants,
            "members": [
                {
                    "id": m.id,
                    "member_type": m.member_type,
                    "channel": m.channel,
                    "chat_id": m.chat_id,
                    "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                    "metadata": m.metadata,
                }
                for m in self.members
            ],
            "owner": self.owner,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "summary": self.summary,
            "auto_archive": self.auto_archive,
            "archive_after_days": self.archive_after_days,
            "coordinator_mode": self.coordinator_mode,
            "escalation_threshold": self.escalation_threshold,
            "deadline": self.deadline,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Room":
        """Deserialize room from dictionary."""
        members = []
        for m_data in data.get("members", []):
            members.append(RoomMember(
                id=m_data["id"],
                member_type=m_data["member_type"],
                channel=m_data.get("channel"),
                chat_id=m_data.get("chat_id"),
                joined_at=datetime.fromisoformat(m_data["joined_at"]) if m_data.get("joined_at") else datetime.now(),
                metadata=m_data.get("metadata", {}),
            ))

        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            type=RoomType(data.get("type", data.get("room_type", "open"))),
            room_type=data.get("room_type", data.get("type", "open")),
            participants=data.get("participants", []),
            members=members,
            owner=data.get("owner", "user"),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            summary=data.get("summary", ""),
            auto_archive=data.get("auto_archive", False),
            archive_after_days=data.get("archive_after_days", 30),
            coordinator_mode=data.get("coordinator_mode", False),
            escalation_threshold=data.get("escalation_threshold", "medium"),
            deadline=data.get("deadline"),
            metadata=data.get("metadata", {}),
        )
