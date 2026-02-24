"""Routine execution orchestration for user + team routines."""

from __future__ import annotations

from typing import Optional

from loguru import logger

from nanofolks.bus.events import MessageEnvelope
from nanofolks.routines.models import Routine
from nanofolks.utils.ids import room_to_session_id


class RoutineExecutor:
    """Executes routine jobs through a single, unified path."""

    def __init__(
        self,
        agent,
        bus,
        config,
        multi_manager=None,
    ) -> None:
        self._agent = agent
        self._bus = bus
        self._config = config
        self._multi_manager = multi_manager

    async def handle_job(self, job: Routine) -> str | None:
        """Execute a routine job.

        User routines are routed through the agent.
        Team routines ticks are routed to the bot routines service.
        """
        # Calibration jobs (system jobs, not user messages)
        if job.payload.routine == "calibration" or job.payload.message == "CALIBRATE_ROUTING":
            return await self._run_calibration(job)

        # Team routines tick (per-bot)
        if job.payload.routine == "team_routines" or job.payload.message == "TEAM_ROUTINES_TICK":
            return await self._run_team_routines_tick(job)

        # System routines (team/room/bot) - run through agent
        if job.payload.scope == "system":
            return await self._run_system_routine(job)

        # User routines - run through agent
        response = await self._run_user_routine(job)

        if job.payload.deliver and job.payload.to:
            await self._bus.publish_outbound(
                MessageEnvelope(
                    channel=job.payload.channel or "cli",
                    chat_id=job.payload.to,
                    content=response or "",
                    direction="outbound",
                )
            )
        return response

    async def _run_calibration(self, job: Routine) -> str | None:
        try:
            from nanofolks.agent.router.calibration import CalibrationManager

            calibration = CalibrationManager(
                patterns_file=self._config.workspace_path / "routing_patterns.json",
                analytics_file=self._config.workspace_path / "routing_stats.json",
                config=self._config.routing.auto_calibration.model_dump() if self._config.routing.auto_calibration else None,
            )
            if calibration.should_calibrate():
                results = calibration.calibrate()
                logger.info(f"Scheduled calibration completed: {results}")
                return (
                    f"Calibration completed: {results.get('patterns_added', 0)} patterns added, "
                    f"{results.get('patterns_removed', 0)} removed"
                )
            return "Calibration not needed yet (insufficient data or too soon)"
        except Exception as e:
            logger.error(f"Calibration job failed: {e}")
            return f"Calibration failed: {e}"

    async def _run_team_routines_tick(self, job: Routine) -> str | None:
        if not self._multi_manager:
            logger.warning("Team routines tick received but no team manager is configured")
            return None

        bot_name = job.payload.bot or job.payload.to
        if not bot_name:
            logger.warning("Team routines tick missing target bot")
            return None

        bot = self._multi_manager.get_bot(bot_name)
        if not bot:
            logger.warning(f"Team routines tick bot not found: {bot_name}")
            return None

        try:
            tick = await bot.trigger_team_routines_now(reason="scheduled")
            status = tick.status if tick else "unknown"
            return f"Team routines tick completed for {bot_name} ({status})"
        except Exception as e:
            logger.error(f"Team routines tick failed for {bot_name}: {e}")
            return f"Team routines tick failed for {bot_name}: {e}"

    async def _run_system_routine(self, job: Routine) -> str | None:
        metadata = job.payload.metadata or {}
        target_type = metadata.get("target_type")
        target_id = metadata.get("target_id")
        room_id = target_id if target_type == "room" else "general"
        return await self._agent.process_direct(
            job.payload.message,
            session_key=room_to_session_id(f"routine_{job.id}"),
            channel=job.payload.channel or "internal",
            chat_id=job.payload.to or "team",
            room_id=room_id,
        )

    async def _run_user_routine(self, job: Routine) -> str | None:
        return await self._agent.process_direct(
            job.payload.message,
            session_key=room_to_session_id(f"routine_{job.id}"),
            channel=job.payload.channel or "cli",
            chat_id=job.payload.to or "direct",
        )
