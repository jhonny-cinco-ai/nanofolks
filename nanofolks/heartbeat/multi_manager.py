"""Manager for coordinating multiple bot heartbeats.

This module provides centralized management of heartbeats across
all bots in the team. It handles:
- Starting/stopping all bot heartbeats
- Monitoring team health
- Coordinating cross-bot tasks
- Aggregating metrics

Usage:
    from nanofolks.heartbeat.multi_manager import MultiHeartbeatManager
    
    manager = MultiHeartbeatManager(bus=interbot_bus)
    
    # Register bots
    for bot in [researcher, coder, social, creative, auditor, leader]:
        manager.register_bot(bot)
    
    # Start all heartbeats
    await manager.start_all()
    
    # Get team health
    health = manager.get_team_health()
    
    # Stop all
    manager.stop_all()
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger

from nanofolks.bots.base import SpecialistBot


@dataclass
class CrossBotCheck:
    """A check that requires coordination across multiple bots."""
    name: str
    description: str
    participating_bots: List[str]
    coordinator_check: str  # Check that runs on coordinator
    dependencies: List[str] = field(default_factory=list)  # Checks that must complete first


@dataclass
class TeamHealthReport:
    """Comprehensive health report for the bot team."""
    timestamp: str
    total_bots: int
    running_bots: int
    overall_success_rate: float
    total_ticks_all_bots: int
    failed_ticks_all_bots: int
    bots: Dict[str, Any]
    alerts: List[str] = field(default_factory=list)


class MultiHeartbeatManager:
    """Manages heartbeats across all bots in the team.
    
    Responsibilities:
    - Start/stop all bot heartbeats
    - Coordinate cross-bot checks
    - Monitor overall team health
    - Aggregate heartbeat metrics
    - Handle bot failures and recovery
    
    Example:
        manager = MultiHeartbeatManager(bus=bus)
        
        # Register bots
        for bot in team:
            manager.register_bot(bot)
        
        # Start all
        await manager.start_all()
        
        # Check health
        health = manager.get_team_health()
        print(f"Team success rate: {health['overall_success_rate']:.1f}%")
        
        # Stop all
        manager.stop_all()
    """
    
    def __init__(self, bus=None):
        """Initialize the multi-heartbeat manager.
        
        Args:
            bus: InterBotBus for cross-bot communication (optional)
        """
        self.bus = bus
        
        # Bot registry
        self._bots: Dict[str, SpecialistBot] = {}
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
        # Cross-bot coordination
        self._cross_bot_checks: Dict[str, CrossBotCheck] = {}
        
        # State
        self._running = False
        self._coordinator_check_task: Optional[asyncio.Task] = None
        self._team_health_task: Optional[asyncio.Task] = None
        
        # Health monitoring
        self._health_check_interval_s = 300  # 5 minutes
        self._alerts: List[str] = []
    
    def register_bot(self, bot: SpecialistBot) -> None:
        """Register a bot for heartbeat management.
        
        Args:
            bot: Bot instance to register
            
        Example:
            researcher = ResearcherBot()
            manager.register_bot(researcher)
        """
        bot_name = bot.role_card.bot_name
        
        if bot_name in self._bots:
            logger.warning(f"[MultiHeartbeatManager] Bot {bot_name} already registered, replacing")
        
        self._bots[bot_name] = bot
        logger.info(f"[MultiHeartbeatManager] Registered bot: {bot_name}")
    
    def unregister_bot(self, bot_name: str) -> bool:
        """Unregister a bot and stop its heartbeat.
        
        Args:
            bot_name: Name of bot to unregister
            
        Returns:
            True if unregistered successfully
            
        Example:
            manager.unregister_bot("researcher")
        """
        if bot_name not in self._bots:
            logger.warning(f"[MultiHeartbeatManager] Bot {bot_name} not registered")
            return False
        
        # Stop heartbeat if running
        bot = self._bots[bot_name]
        try:
            bot.stop_heartbeat()
        except Exception as e:
            logger.error(f"[MultiHeartbeatManager] Error stopping {bot_name} heartbeat: {e}")
        
        # Cancel task if exists
        if bot_name in self._heartbeat_tasks:
            self._heartbeat_tasks[bot_name].cancel()
            del self._heartbeat_tasks[bot_name]
        
        del self._bots[bot_name]
        logger.info(f"[MultiHeartbeatManager] Unregistered bot: {bot_name}")
        return True
    
    async def start_all(self) -> None:
        """Start heartbeats for all registered bots.
        
        This starts each bot's independent heartbeat service.
        Coordinator bot runs with 30min interval, specialists with 60min.
        
        Example:
            await manager.start_all()
        """
        self._running = True
        
        logger.info(f"[MultiHeartbeatManager] Starting heartbeats for {len(self._bots)} bots")
        
        # Start each bot's heartbeat
        for bot_name, bot in self._bots.items():
            try:
                await bot.start_heartbeat()
                
                interval = bot._heartbeat_config.interval_s if bot._heartbeat_config else 3600
                checks_count = len(bot._heartbeat_config.checks) if bot._heartbeat_config else 0
                
                logger.info(
                    f"[MultiHeartbeatManager] Started {bot_name} heartbeat: "
                    f"{interval}s interval, {checks_count} checks"
                )
                
            except Exception as e:
                logger.error(f"[MultiHeartbeatManager] Failed to start {bot_name} heartbeat: {e}")
        
        # Start team health monitoring
        self._team_health_task = asyncio.create_task(
            self._monitor_team_health(),
            name="team_health_monitor"
        )
        
        logger.info("[MultiHeartbeatManager] All heartbeats started")
    
    def stop_all(self) -> None:
        """Stop all bot heartbeats.
        
        This gracefully stops all running heartbeats and cancels
        any pending coordination tasks.
        
        Example:
            manager.stop_all()
        """
        self._running = False
        
        logger.info(f"[MultiHeartbeatManager] Stopping heartbeats for {len(self._bots)} bots")
        
        # Stop each bot
        for bot_name, bot in self._bots.items():
            try:
                bot.stop_heartbeat()
                logger.debug(f"[MultiHeartbeatManager] Stopped {bot_name} heartbeat")
            except Exception as e:
                logger.error(f"[MultiHeartbeatManager] Error stopping {bot_name}: {e}")
        
        # Cancel health monitoring task
        if self._team_health_task:
            self._team_health_task.cancel()
            self._team_health_task = None
        
        # Cancel coordinator task
        if self._coordinator_check_task:
            self._coordinator_check_task.cancel()
            self._coordinator_check_task = None
        
        # Cancel any pending heartbeat tasks
        for task in self._heartbeat_tasks.values():
            task.cancel()
        self._heartbeat_tasks.clear()
        
        logger.info("[MultiHeartbeatManager] All heartbeats stopped")
    
    async def _monitor_team_health(self) -> None:
        """Monitor team health periodically.
        
        Runs every 5 minutes to check overall team health and
        generate alerts if issues are detected.
        """
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval_s)
                
                if not self._running:
                    break
                
                health = self.get_team_health()
                
                # Check for issues
                alerts = []
                
                if health.overall_success_rate < 80:
                    alerts.append(f"Low team success rate: {health.overall_success_rate:.1f}%")
                
                non_running = health.total_bots - health.running_bots
                if non_running > 0:
                    alerts.append(f"{non_running} bots not running")
                
                # Log alerts
                for alert in alerts:
                    logger.warning(f"[MultiHeartbeatManager] ALERT: {alert}")
                
                self._alerts = alerts
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[MultiHeartbeatManager] Health monitoring error: {e}")
    
    def get_team_health(self) -> TeamHealthReport:
        """Get overall health status of all bot heartbeats.
        
        Returns comprehensive health report with per-bot and aggregate metrics.
        
        Returns:
            TeamHealthReport with health metrics
            
        Example:
            health = manager.get_team_health()
            print(f"Success rate: {health.overall_success_rate:.1f}%")
            print(f"Running bots: {health.running_bots}/{health.total_bots}")
        """
        bot_statuses = {}
        
        for bot_name, bot in self._bots.items():
            try:
                status = bot.get_heartbeat_status()
                
                # Add bot-specific info
                status["bot_name"] = bot_name
                status["domain"] = bot.domain
                status["title"] = bot.title
                
                bot_statuses[bot_name] = status
            except Exception as e:
                logger.error(f"[MultiHeartbeatManager] Error getting status for {bot_name}: {e}")
                bot_statuses[bot_name] = {
                    "bot_name": bot_name,
                    "error": str(e),
                    "running": False
                }
        
        # Calculate aggregate metrics from heartbeat history
        total_ticks = 0
        failed_ticks = 0
        
        for bot in self._bots.values():
            history = bot.private_memory.get("heartbeat_history", [])
            total_ticks += len(history)
            failed_ticks += sum(
                1 for tick in history 
                if tick.get("status") in ["failed", "timeout"]
            )
        
        overall_success_rate = (
            ((total_ticks - failed_ticks) / total_ticks * 100)
            if total_ticks > 0 else 100.0
        )
        
        running_count = sum(
            1 for s in bot_statuses.values() 
            if s.get("running", False)
        )
        
        return TeamHealthReport(
            timestamp=datetime.now().isoformat(),
            total_bots=len(self._bots),
            running_bots=running_count,
            overall_success_rate=overall_success_rate,
            total_ticks_all_bots=total_ticks,
            failed_ticks_all_bots=failed_ticks,
            bots=bot_statuses,
            alerts=self._alerts.copy()
        )
    
    def get_team_health_dict(self) -> Dict[str, Any]:
        """Get team health as a dictionary (for JSON serialization).
        
        Returns:
            Dict with health information
        """
        report = self.get_team_health()
        return {
            "timestamp": report.timestamp,
            "total_bots": report.total_bots,
            "running_bots": report.running_bots,
            "overall_success_rate": report.overall_success_rate,
            "total_ticks_all_bots": report.total_ticks_all_bots,
            "failed_ticks_all_bots": report.failed_ticks_all_bots,
            "bots": report.bots,
            "alerts": report.alerts
        }
    
    async def trigger_team_heartbeat(self, reason: str = "manual") -> Dict[str, Any]:
        """Manually trigger heartbeat on all bots.
        
        This forces an immediate heartbeat tick on all registered bots,
        regardless of their scheduled intervals.
        
        Args:
            reason: Why heartbeat is being triggered
            
        Returns:
            Results from all bots
            
        Example:
            results = await manager.trigger_team_heartbeat("system_check")
            for bot_name, tick in results.items():
                print(f"{bot_name}: {tick.status}")
        """
        results = {}
        
        logger.info(f"[MultiHeartbeatManager] Triggering team heartbeat: {reason}")
        
        for bot_name, bot in self._bots.items():
            try:
                tick = await bot.trigger_heartbeat_now(reason)
                results[bot_name] = {
                    "success": True,
                    "tick_id": tick.tick_id if tick else None,
                    "status": tick.status if tick else "unknown"
                }
                logger.debug(f"[MultiHeartbeatManager] Triggered {bot_name} heartbeat")
            except Exception as e:
                results[bot_name] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"[MultiHeartbeatManager] Failed to trigger {bot_name}: {e}")
        
        return results
    
    def get_registered_bots(self) -> List[str]:
        """Get list of registered bot names.
        
        Returns:
            List of bot names
        """
        return list(self._bots.keys())
    
    def is_running(self) -> bool:
        """Check if manager is running.
        
        Returns:
            True if manager is active
        """
        return self._running
    
    def register_cross_bot_check(self, check: CrossBotCheck) -> None:
        """Register a check that requires cross-bot coordination.
        
        Args:
            check: CrossBotCheck definition
        """
        self._cross_bot_checks[check.name] = check
        logger.info(f"[MultiHeartbeatManager] Registered cross-bot check: {check.name}")
    
    def get_bot(self, bot_name: str) -> Optional[SpecialistBot]:
        """Get a registered bot by name.
        
        Args:
            bot_name: Name of bot to retrieve
            
        Returns:
            Bot instance or None if not found
        """
        return self._bots.get(bot_name)
    
    def __len__(self) -> int:
        """Return number of registered bots."""
        return len(self._bots)
    
    def __contains__(self, bot_name: str) -> bool:
        """Check if a bot is registered."""
        return bot_name in self._bots


__all__ = [
    "MultiHeartbeatManager",
    "CrossBotCheck",
    "TeamHealthReport",
]