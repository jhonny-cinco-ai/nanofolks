"""Room-centric architecture module.

This module provides room-centric architecture where rooms are
named entities that channels join, rather than sessions being tied
to specific channels.
"""

from nanofolks.bots.room_manager import RoomManager, get_room_manager
from nanofolks.models.room import Room, RoomMember, RoomType

__all__ = [
    "RoomManager",
    "get_room_manager",
    "Room",
    "RoomMember",
    "RoomType",
]
