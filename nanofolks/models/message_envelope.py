"""Unified message envelope for routing across the system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from nanofolks.utils.ids import normalize_room_id, new_trace_id, session_key_for_message

MessageDirection = Literal["inbound", "outbound"]
MessageRole = Literal["user", "bot", "system"]

SYSTEM_PRIORITY = 0
BOT_PRIORITY = 3
USER_PRIORITY = 5
DEFAULT_PRIORITY = USER_PRIORITY


@dataclass
class MessageEnvelope:
    """Single message shape for broker, bus, channels, and tools."""

    channel: str  # telegram, discord, slack, whatsapp, cli, gui
    chat_id: str  # Chat/channel identifier
    content: str  # Message text
    priority: int = DEFAULT_PRIORITY  # Lower = higher priority
    direction: MessageDirection = "inbound"
    sender_id: str | None = None  # User identifier (inbound)
    sender_role: MessageRole | None = None  # user, bot, system
    bot_name: str | None = None  # Bot name if sender is a bot
    reply_to: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    media: list[str] = field(default_factory=list)  # Media URLs
    metadata: dict[str, Any] = field(default_factory=dict)  # Channel-specific data
    room_id: str | None = None  # Room ID if part of room-centric routing
    trace_id: str | None = None

    @property
    def session_key(self) -> str:
        """Unique key for session identification (room-centric format)."""
        return session_key_for_message(self.room_id, self.channel, self.chat_id)

    def set_room(self, room_id: str) -> None:
        """Set the room for this message (room-centric routing)."""
        self.room_id = normalize_room_id(room_id)

    def ensure_trace_id(self) -> None:
        """Ensure a trace id is set for end-to-end tracking."""
        if not self.trace_id:
            self.trace_id = new_trace_id()

    def ensure_sender_role(self, default_role: MessageRole) -> None:
        """Ensure sender_role is set to a default if missing."""
        if not self.sender_role:
            self.sender_role = default_role

    def ensure_priority(self) -> None:
        """Ensure priority is set and aligned with sender_role."""
        if self.priority is None:
            self.priority = DEFAULT_PRIORITY
        if self.priority == DEFAULT_PRIORITY and self.sender_role:
            if self.sender_role == "system":
                self.priority = SYSTEM_PRIORITY
            elif self.sender_role == "bot":
                self.priority = BOT_PRIORITY
            elif self.sender_role == "user":
                self.priority = USER_PRIORITY

    def apply_defaults(self, default_role: MessageRole) -> None:
        """Apply default sender_role, trace_id, and priority if missing."""
        self.ensure_sender_role(default_role)
        self.ensure_trace_id()
        self.ensure_priority()

    def to_dict(self) -> dict[str, Any]:
        """Serialize envelope to a JSON-safe dict."""
        return {
            "channel": self.channel,
            "chat_id": self.chat_id,
            "content": self.content,
            "priority": self.priority,
            "direction": self.direction,
            "sender_id": self.sender_id,
            "sender_role": self.sender_role,
            "bot_name": self.bot_name,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp.isoformat(),
            "media": list(self.media),
            "metadata": dict(self.metadata),
            "room_id": self.room_id,
            "trace_id": self.trace_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageEnvelope":
        """Deserialize from a JSON-safe dict."""
        ts = data.get("timestamp")
        timestamp = datetime.fromisoformat(ts) if isinstance(ts, str) else datetime.now()
        return cls(
            channel=data.get("channel", ""),
            chat_id=data.get("chat_id", ""),
            content=data.get("content", ""),
            priority=int(data.get("priority", DEFAULT_PRIORITY)),
            direction=data.get("direction", "inbound"),
            sender_id=data.get("sender_id"),
            sender_role=data.get("sender_role"),
            bot_name=data.get("bot_name"),
            reply_to=data.get("reply_to"),
            timestamp=timestamp,
            media=data.get("media", []) or [],
            metadata=data.get("metadata", {}) or {},
            room_id=data.get("room_id"),
            trace_id=data.get("trace_id"),
        )
