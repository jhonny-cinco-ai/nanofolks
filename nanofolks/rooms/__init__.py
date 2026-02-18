"""Room-centric architecture module.

This module provides true room-centric architecture where rooms are
named entities that channels join, rather than sessions being tied
to specific channels.
"""

from nanofolks.rooms.registry import RoomRegistry, Room, RoomMember, get_room_registry

__all__ = [
    "RoomRegistry",
    "Room",
    "RoomMember",
    "get_room_registry",
]
