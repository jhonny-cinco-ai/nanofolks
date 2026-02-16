"""Message bus module for decoupled channel-agent communication."""

from nanofolks.bus.events import InboundMessage, OutboundMessage
from nanofolks.bus.queue import MessageBus

__all__ = ["MessageBus", "InboundMessage", "OutboundMessage"]
