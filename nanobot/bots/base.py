"""Base class for all specialist bots with heartbeat support."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from loguru import logger

from nanobot.models.role_card import RoleCard
from nanobot.models.workspace import Workspace


class SpecialistBot(ABC):
    """Abstract base class for all bot implementations with autonomous heartbeat.
    
    Each bot runs its own independent heartbeat with:
    - Role-specific periodic checks
    - Domain-optimized intervals
    - Autonomous task execution
    - Self-managed state
    """

    def __init__(self, role_card: RoleCard, bus=None, workspace_id: Optional[str] = None):
        """Initialize a bot with a role card.
        
        Args:
            role_card: Role card defining bot's personality and constraints
            bus: InterBotBus for communication with coordinator
            workspace_id: Workspace context ID
        """
        self.role_card = role_card
        self.bus = bus
        self.workspace_id = workspace_id
        self.private_memory: Dict[str, Any] = {
            "learnings": [],  # Lessons learned by this bot
            "expertise_domains": [],  # Domains where bot is competent
            "mistakes": [],  # Errors and how they were recovered
            "confidence": 0.7,  # Self-assessed competence (0.0-1.0)
            "created_at": datetime.now().isoformat(),
            "heartbeat_history": [],  # History of heartbeat executions
        }
        
        # Heartbeat service (initialized lazily)
        self._heartbeat = None
        self._heartbeat_config = None

    @property
    def name(self) -> str:
        """Get bot name."""
        return self.role_card.bot_name

    @property
    def domain(self) -> str:
        """Get bot domain."""
        return self.role_card.domain.value

    @property
    def title(self) -> str:
        """Get bot title."""
        return self.role_card.title

    def can_perform_action(self, action: str) -> tuple[bool, Optional[str]]:
        """Validate if bot can perform an action (check hard bans).
        
        Args:
            action: Action description
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        return self.role_card.validate_action(action)

    def get_greeting(self, workspace: Optional[Workspace] = None) -> str:
        """Get bot's greeting for a workspace.
        
        Args:
            workspace: Workspace context (optional)
            
        Returns:
            Greeting message
        """
        return self.role_card.greeting

    def record_learning(self, lesson: str, confidence: float = 0.7) -> None:
        """Record a private learning.
        
        Args:
            lesson: What was learned
            confidence: How confident in this learning (0.0-1.0)
        """
        self.private_memory["learnings"].append({
            "lesson": lesson,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        })

    def record_mistake(self, error: str, recovery: str, lesson: Optional[str] = None) -> None:
        """Record a mistake and how it was recovered.
        
        Args:
            error: What went wrong
            recovery: How the error was fixed
            lesson: Optional lesson learned
        """
        record = {
            "error": error,
            "recovery": recovery,
            "timestamp": datetime.now().isoformat(),
        }
        if lesson:
            record["lesson"] = lesson
        
        self.private_memory["mistakes"].append(record)

    def add_expertise(self, domain: str) -> None:
        """Add a domain to bot's expertise.
        
        Args:
            domain: Domain name
        """
        if domain not in self.private_memory["expertise_domains"]:
            self.private_memory["expertise_domains"].append(domain)

    def update_confidence(self, delta: float) -> None:
        """Update bot's confidence level.
        
        Args:
            delta: Change in confidence (-1.0 to 1.0)
        """
        current = self.private_memory["confidence"]
        new_confidence = max(0.0, min(1.0, current + delta))
        self.private_memory["confidence"] = new_confidence

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of bot's status and learnings.
        
        Returns:
            Summary dictionary
        """
        return {
            "name": self.name,
            "domain": self.domain,
            "title": self.title,
            "learnings_count": len(self.private_memory["learnings"]),
            "mistakes_count": len(self.private_memory["mistakes"]),
            "expertise_domains": self.private_memory["expertise_domains"],
            "confidence": self.private_memory["confidence"],
            "created_at": self.private_memory["created_at"],
            "heartbeat_running": self.is_heartbeat_running,
        }

    # ==================================================================
    # Heartbeat Methods
    # ==================================================================

    def initialize_heartbeat(
        self,
        config=None,
        on_tick_complete: Optional[Callable] = None,
        on_check_complete: Optional[Callable] = None
    ) -> None:
        """Initialize bot's autonomous heartbeat.
        
        Args:
            config: Heartbeat configuration (uses default if None)
            on_tick_complete: Callback when tick completes
            on_check_complete: Callback when individual check completes
        """
        if config is None:
            # Load default config for this bot type
            from nanobot.bots.heartbeat_configs import get_bot_heartbeat_config
            config = get_bot_heartbeat_config(self.role_card.bot_name)
        
        self._heartbeat_config = config
        
        # Import here to avoid circular imports
        from nanobot.heartbeat.bot_heartbeat import BotHeartbeatService
        
        # Wrap callbacks to include bot context
        def tick_callback(tick):
            self._on_heartbeat_tick_complete(tick)
            if on_tick_complete:
                on_tick_complete(tick)
        
        def check_callback(result):
            self._on_check_complete(result)
            if on_check_complete:
                on_check_complete(result)
        
        self._heartbeat = BotHeartbeatService(
            bot_instance=self,
            config=config,
            on_tick_complete=tick_callback,
            on_check_complete=check_callback
        )
        
        logger.info(
            f"[{self.role_card.bot_name}] Heartbeat initialized: "
            f"{config.interval_s}s interval, {len(config.checks)} checks"
        )

    async def start_heartbeat(self) -> None:
        """Start bot's independent heartbeat."""
        if self._heartbeat is None:
            # Auto-initialize with defaults
            self.initialize_heartbeat()
        
        if self._heartbeat:
            await self._heartbeat.start()

    def stop_heartbeat(self) -> None:
        """Stop bot's heartbeat."""
        if self._heartbeat:
            self._heartbeat.stop()

    @property
    def is_heartbeat_running(self) -> bool:
        """Check if heartbeat is currently running."""
        return self._heartbeat is not None and self._heartbeat.is_running

    def get_heartbeat_status(self) -> Dict[str, Any]:
        """Get current heartbeat status."""
        if self._heartbeat:
            return self._heartbeat.get_status()
        return {"running": False, "bot_name": self.role_card.bot_name}

    async def trigger_heartbeat_now(self, reason: str = "manual"):
        """Manually trigger a heartbeat tick.
        
        Args:
            reason: Why heartbeat is being triggered
            
        Returns:
            HeartbeatTick result
        """
        if self._heartbeat is None:
            self.initialize_heartbeat()
        
        if self._heartbeat is not None:
            return await self._heartbeat.trigger_now(reason)
        return None

    def _on_heartbeat_tick_complete(self, tick) -> None:
        """Internal handler for tick completion.
        
        Records to bot's private memory and logs learning.
        """
        # Record to private memory
        tick_summary = {
            "tick_id": tick.tick_id,
            "timestamp": tick.started_at.isoformat(),
            "status": tick.status,
            "success_rate": tick.get_success_rate(),
            "failed_checks": [r.check_name for r in tick.get_failed_checks()],
        }
        
        self.private_memory["heartbeat_history"].append(tick_summary)
        
        # Trim history if too long
        max_history = tick.config.retain_history_count if tick.config else 100
        if len(self.private_memory["heartbeat_history"]) > max_history:
            self.private_memory["heartbeat_history"] = self.private_memory["heartbeat_history"][-max_history:]
        
        # Record learning
        success_rate = tick.get_success_rate()
        if success_rate >= 0.9:
            self.record_learning(
                lesson=f"Heartbeat tick {tick.tick_id} completed with {success_rate:.0%} success",
                confidence=0.9
            )
        elif success_rate < 0.5:
            self.record_mistake(
                error=f"Heartbeat tick {tick.tick_id} had low success rate: {success_rate:.0%}",
                recovery="Review failed checks and adjust configuration"
            )

    def _on_check_complete(self, result) -> None:
        """Internal handler for check completion."""
        # Log check completion
        if result.success:
            logger.debug(
                f"[{self.role_card.bot_name}] Check '{result.check_name}' completed successfully"
            )
        else:
            logger.warning(
                f"[{self.role_card.bot_name}] Check '{result.check_name}' failed: {result.error}"
            )

    # ==================================================================
    # Communication with Coordinator
    # ==================================================================

    async def notify_coordinator(
        self,
        message: str,
        priority: str = "normal",
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Notify coordinator of heartbeat finding.
        
        Args:
            message: Notification message
            priority: Priority level (low/normal/high/critical)
            data: Additional data to include
            
        Returns:
            True if notification sent successfully
        """
        if self.bus is None:
            logger.warning(f"[{self.role_card.bot_name}] No bus available for notification")
            return False
        
        try:
            # Create notification payload
            notification = {
                "sender": self.role_card.bot_name,
                "recipient": "coordinator",
                "type": "notification",
                "message": message,
                "priority": priority,
                "data": data or {},
                "source": "heartbeat",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send via bus if available
            if hasattr(self.bus, 'send_message'):
                self.bus.send_message(notification)
            
            logger.info(f"[{self.role_card.bot_name}] Notified coordinator: {message}")
            return True
            
        except Exception as e:
            logger.error(f"[{self.role_card.bot_name}] Failed to notify coordinator: {e}")
            return False

    async def escalate_to_coordinator(
        self,
        message: str,
        priority: str = "high",
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Escalate issue to coordinator for human attention.
        
        Args:
            message: Escalation message
            priority: Priority level
            data: Supporting data
            
        Returns:
            True if escalation sent successfully
        """
        return await self.notify_coordinator(
            message=f"[ESCALATION] {message}",
            priority=priority,
            data=data
        )

    @abstractmethod
    async def process_message(self, message: str, workspace: Workspace) -> str:
        """Process a message and generate response.
        
        This is the main interaction method for the bot.
        
        Args:
            message: User or system message
            workspace: Workspace context
            
        Returns:
            Bot's response message
        """
        pass

    @abstractmethod
    async def execute_task(self, task: str, workspace: Workspace) -> Dict[str, Any]:
        """Execute a specific task.
        
        This is for structured task execution (not conversational).
        
        Args:
            task: Task description
            workspace: Workspace context
            
        Returns:
            Task result dictionary
        """
        pass
