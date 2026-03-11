"""BotCoordinationChannel: Real-time bot-to-bot communication.

This module provides the BotCoordinationChannel class, which enables bots
to communicate with each other in real-time, share insights, request help,
and coordinate task execution.

Key features:
- Broadcast insights to relevant bots
- Persistent DM room history for coordination
- Real-time notifications via message bus
- Task coordination and help requests
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from loguru import logger

from nanofolks.bots.room_manager import RoomManager, get_room_manager
from nanofolks.bus.events import MessageEnvelope
from nanofolks.bus.queue import MessageBus


class InsightType(str, Enum):
    """Types of insights that can be shared between bots."""

    DISCOVERY = "discovery"
    SECURITY = "security"
    BUG = "bug"
    OPTIMIZATION = "optimization"
    QUESTION = "question"
    ANSWER = "answer"
    TASK_UPDATE = "task_update"
    HELP_REQUEST = "help_request"


class CoordinationMessage:
    """A coordination message between bots."""

    def __init__(
        self,
        from_bot: str,
        to_bot: str,
        content: str,
        insight_type: InsightType = InsightType.DISCOVERY,
        context: Optional[Dict] = None,
        reply_to: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.from_bot = from_bot
        self.to_bot = to_bot
        self.content = content
        self.insight_type = insight_type
        self.context = context or {}
        self.reply_to = reply_to
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "from_bot": self.from_bot,
            "to_bot": self.to_bot,
            "content": self.content,
            "insight_type": self.insight_type.value,
            "context": self.context,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp.isoformat(),
        }


class BotCoordinationChannel:
    """Real-time bot-to-bot communication channel.

    The BotCoordinationChannel enables bots to communicate with each other,
    share insights, and coordinate activities. It uses DM rooms for persistent
    history and the message bus for real-time notifications.

    Attributes:
        room_manager: RoomManager for DM room operations
        bus: MessageBus for real-time notifications
        _handlers: Dict of message handlers for different insight types
    """

    def __init__(
        self,
        room_manager: Optional[RoomManager] = None,
        bus: Optional[MessageBus] = None,
    ):
        """Initialize the BotCoordinationChannel.

        Args:
            room_manager: Optional RoomManager (uses singleton if not provided)
            bus: Optional MessageBus
        """
        self.room_manager = room_manager or get_room_manager()
        self.bus = bus

        # Message handlers for different insight types
        self._handlers: Dict[InsightType, List] = {}

        self.logger = logger.bind(component="BotCoordinationChannel")
        self.logger.info("BotCoordinationChannel initialized")

    async def broadcast_insight(
        self,
        from_bot: str,
        insight: str,
        relevant_bots: List[str],
        insight_type: InsightType = InsightType.DISCOVERY,
        context: Optional[Dict] = None,
    ) -> List[str]:
        """Broadcast an insight to relevant bots.

        Args:
            from_bot: Name of the bot sharing the insight
            insight: The insight content
            relevant_bots: List of bot names to notify
            insight_type: Type of insight
            context: Optional context information

        Returns:
            List of message IDs sent
        """
        message_ids = []

        for to_bot in relevant_bots:
            if to_bot == from_bot:
                continue

            try:
                # Create coordination message
                coord_msg = CoordinationMessage(
                    from_bot=from_bot,
                    to_bot=to_bot,
                    content=insight,
                    insight_type=insight_type,
                    context=context,
                )

                # Log to DM room for persistence
                dm_room = self.room_manager.get_or_create_dm_room([from_bot, to_bot])

                message_id = self.room_manager.log_dm_message(
                    sender_bot=from_bot,
                    recipient_bot=to_bot,
                    content=insight,
                    message_type=insight_type.value,
                    context={
                        **(context or {}),
                        "coordination_id": coord_msg.id,
                        "timestamp": coord_msg.timestamp.isoformat(),
                    },
                )
                message_ids.append(message_id)

                # Send real-time notification via bus
                if self.bus:
                    await self.bus.publish_outbound(
                        MessageEnvelope(
                            channel="internal",
                            chat_id=f"dm-{from_bot}-{to_bot}",
                            content=insight,
                            bot_name=from_bot,
                            metadata={
                                "type": "coordination",
                                "insight_type": insight_type.value,
                                "coordination_id": coord_msg.id,
                                "to_bot": to_bot,
                            },
                        )
                    )

                self.logger.debug(f"Insight from {from_bot} to {to_bot}: {insight[:50]}...")

            except Exception as e:
                self.logger.error(f"Failed to send insight to {to_bot}: {e}")

        if message_ids:
            self.logger.info(f"Broadcast insight from {from_bot} to {len(message_ids)} bots")

        return message_ids

    async def request_help(
        self,
        from_bot: str,
        help_request: str,
        relevant_bots: List[str],
        urgency: str = "normal",
        context: Optional[Dict] = None,
    ) -> List[str]:
        """Request help from other bots.

        Args:
            from_bot: Name of the bot requesting help
            help_request: Description of help needed
            relevant_bots: List of bots to ask for help
            urgency: Urgency level (low, normal, high, critical)
            context: Optional context

        Returns:
            List of message IDs sent
        """
        full_context = {
            **(context or {}),
            "urgency": urgency,
            "request_type": "help",
        }

        # Add urgency prefix
        urgency_prefix = {
            "critical": "🚨 CRITICAL: ",
            "high": "⚠️ HIGH: ",
            "normal": "❓ ",
            "low": "💭 ",
        }.get(urgency, "")

        formatted_request = f"{urgency_prefix}{from_bot} needs help: {help_request}"

        return await self.broadcast_insight(
            from_bot=from_bot,
            insight=formatted_request,
            relevant_bots=relevant_bots,
            insight_type=InsightType.HELP_REQUEST,
            context=full_context,
        )

    async def share_discovery(
        self,
        from_bot: str,
        discovery: str,
        relevant_bots: List[str],
        importance: str = "normal",
        context: Optional[Dict] = None,
    ) -> List[str]:
        """Share a discovery with other bots.

        Args:
            from_bot: Name of the bot making the discovery
            discovery: Description of the discovery
            relevant_bots: List of bots to notify
            importance: Importance level (low, normal, high)
            context: Optional context

        Returns:
            List of message IDs sent
        """
        full_context = {
            **(context or {}),
            "importance": importance,
            "discovery_type": "finding",
        }

        # Add importance prefix
        importance_prefix = {
            "high": "🔍 IMPORTANT DISCOVERY: ",
            "normal": "🔍 Discovery: ",
            "low": "💡 Noted: ",
        }.get(importance, "")

        formatted_discovery = f"{importance_prefix}{discovery}"

        return await self.broadcast_insight(
            from_bot=from_bot,
            insight=formatted_discovery,
            relevant_bots=relevant_bots,
            insight_type=InsightType.DISCOVERY,
            context=full_context,
        )

    async def report_security_issue(
        self,
        from_bot: str,
        issue: str,
        severity: str,
        relevant_bots: List[str],
        context: Optional[Dict] = None,
    ) -> List[str]:
        """Report a security issue to relevant bots.

        Args:
            from_bot: Name of the bot reporting the issue
            issue: Description of the security issue
            severity: Severity level (low, medium, high, critical)
            relevant_bots: List of bots to notify (should include auditor)
            context: Optional context

        Returns:
            List of message IDs sent
        """
        full_context = {
            **(context or {}),
            "severity": severity,
            "issue_type": "security",
        }

        # Add severity prefix
        severity_prefix = {
            "critical": "🚨 SECURITY CRITICAL: ",
            "high": "⚠️ Security Issue: ",
            "medium": "🔒 Security Note: ",
            "low": "🔒 Security: ",
        }.get(severity, "")

        formatted_issue = f"{severity_prefix}{issue}"

        return await self.broadcast_insight(
            from_bot=from_bot,
            insight=formatted_issue,
            relevant_bots=relevant_bots,
            insight_type=InsightType.SECURITY,
            context=full_context,
        )

    async def report_bug(
        self,
        from_bot: str,
        bug_description: str,
        relevant_bots: List[str],
        context: Optional[Dict] = None,
    ) -> List[str]:
        """Report a bug to relevant bots.

        Args:
            from_bot: Name of the bot reporting the bug
            bug_description: Description of the bug
            relevant_bots: List of bots to notify
            context: Optional context

        Returns:
            List of message IDs sent
        """
        formatted_bug = f"🐛 Bug found: {bug_description}"

        return await self.broadcast_insight(
            from_bot=from_bot,
            insight=formatted_bug,
            relevant_bots=relevant_bots,
            insight_type=InsightType.BUG,
            context=context,
        )

    async def send_task_update(
        self,
        from_bot: str,
        task_id: str,
        status: str,
        relevant_bots: List[str],
        details: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> List[str]:
        """Send a task update to relevant bots.

        Args:
            from_bot: Name of the bot sending the update
            task_id: Task identifier
            status: Task status (started, in_progress, completed, failed)
            relevant_bots: List of bots to notify
            details: Optional details
            context: Optional context

        Returns:
            List of message IDs sent
        """
        full_context = {
            **(context or {}),
            "task_id": task_id,
            "status": status,
        }

        # Format update
        status_emoji = {
            "started": "🚀",
            "in_progress": "⏳",
            "completed": "✅",
            "failed": "❌",
        }.get(status, "📋")

        update = f"{status_emoji} Task {task_id}: {status}"
        if details:
            update += f" - {details}"

        return await self.broadcast_insight(
            from_bot=from_bot,
            insight=update,
            relevant_bots=relevant_bots,
            insight_type=InsightType.TASK_UPDATE,
            context=full_context,
        )

    async def ask_question(
        self,
        from_bot: str,
        question: str,
        to_bot: str,
        context: Optional[Dict] = None,
    ) -> str:
        """Ask a specific question to another bot.

        Args:
            from_bot: Name of the bot asking
            question: The question
            to_bot: Name of the bot being asked
            context: Optional context

        Returns:
            Message ID
        """
        formatted_question = f"❓ {question}"

        message_ids = await self.broadcast_insight(
            from_bot=from_bot,
            insight=formatted_question,
            relevant_bots=[to_bot],
            insight_type=InsightType.QUESTION,
            context=context,
        )

        return message_ids[0] if message_ids else ""

    async def reply_to_question(
        self,
        from_bot: str,
        answer: str,
        to_bot: str,
        question_message_id: str,
        context: Optional[Dict] = None,
    ) -> str:
        """Reply to a question from another bot.

        Args:
            from_bot: Name of the bot answering
            answer: The answer
            to_bot: Name of the bot who asked
            question_message_id: ID of the question message
            context: Optional context

        Returns:
            Message ID
        """
        formatted_answer = f"✅ {answer}"

        full_context = {
            **(context or {}),
            "reply_to": question_message_id,
            "answer_type": "response",
        }

        message_ids = await self.broadcast_insight(
            from_bot=from_bot,
            insight=formatted_answer,
            relevant_bots=[to_bot],
            insight_type=InsightType.ANSWER,
            context=full_context,
        )

        return message_ids[0] if message_ids else ""

    def get_coordination_history(
        self,
        bot1: str,
        bot2: str,
        limit: int = 50,
    ) -> List[Dict]:
        """Get coordination history between two bots.

        Args:
            bot1: First bot name
            bot2: Second bot name
            limit: Maximum number of messages to return

        Returns:
            List of coordination messages
        """
        try:
            dm_room = self.room_manager.get_or_create_dm_room([bot1, bot2])

            # Get messages from DM room
            messages = dm_room.get_messages(limit=limit)

            # Filter to coordination messages only
            coordination_messages = [
                msg for msg in messages if msg.metadata.get("type") == "coordination"
            ]

            return coordination_messages

        except Exception as e:
            self.logger.error(f"Error getting coordination history: {e}")
            return []

    def register_handler(
        self,
        insight_type: InsightType,
        handler,
    ) -> None:
        """Register a handler for a specific insight type.

        Args:
            insight_type: Type of insight to handle
            handler: Async function to handle messages
        """
        if insight_type not in self._handlers:
            self._handlers[insight_type] = []

        self._handlers[insight_type].append(handler)
        self.logger.debug(f"Registered handler for {insight_type.value}")

    async def process_incoming_coordination(
        self,
        message: MessageEnvelope,
    ) -> None:
        """Process an incoming coordination message.

        Args:
            message: Incoming coordination message
        """
        metadata = message.metadata or {}

        if metadata.get("type") != "coordination":
            return

        insight_type_str = metadata.get("insight_type", "discovery")

        try:
            insight_type = InsightType(insight_type_str)
        except ValueError:
            self.logger.warning(f"Unknown insight type: {insight_type_str}")
            return

        # Call registered handlers
        handlers = self._handlers.get(insight_type, [])

        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Handler error for {insight_type.value}: {e}")


# Convenience function
def create_coordination_channel(
    room_manager: Optional[RoomManager] = None,
    bus: Optional[MessageBus] = None,
) -> BotCoordinationChannel:
    """Create a BotCoordinationChannel instance.

    Args:
        room_manager: Optional RoomManager
        bus: Optional MessageBus

    Returns:
        BotCoordinationChannel instance
    """
    return BotCoordinationChannel(room_manager, bus)
