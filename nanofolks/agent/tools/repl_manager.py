"""
REPL State Manager - Room-scoped REPL environment management.

This module manages REPL states for multiple rooms, providing room-scoped
isolation and lifecycle management.
"""

from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from nanofolks.agent.tools.repl_sandbox import RestrictedPythonSandbox
from nanofolks.agent.tools.repl_state import REPLState


class REPLStateManager:
    """
    Manage REPL state per room.

    REPL state is room-scoped, not user-scoped or channel-scoped.
    This means all channels in a room share the same REPL environment.

    Key features:
    - Room-scoped state isolation
    - Lazy initialization (state created on first access)
    - Automatic cleanup when room is archived
    - Factory pattern for API instances

    Example:
        manager = REPLStateManager(api_factory=create_api_instances)

        # Get state for a room (creates if needed)
        state = manager.get_state("project-alpha")

        # Execute code
        result = await state.execute("print('Hello')")

        # Clear state when room is archived
        manager.clear_state("project-alpha")
    """

    def __init__(
        self,
        api_factory: Optional[Callable[[str], Dict[str, Any]]] = None,
        sandbox_timeout: float = 90.0,
        sandbox_max_output_chars: int = 20000,
    ):
        """
        Initialize REPL State Manager.

        Args:
            api_factory: Optional factory function to create API instances
                        Signature: (room_id: str) -> Dict[str, Any]
            sandbox_timeout: Timeout for sandbox execution (seconds)
            sandbox_max_output_chars: Maximum output characters before truncation
        """
        # Map: room_id → REPLState
        self._states: Dict[str, REPLState] = {}

        # API factory (creates tools, bots, memory APIs for each room)
        self._api_factory = api_factory

        # Sandbox configuration
        self._sandbox_timeout = sandbox_timeout
        self._sandbox_max_output_chars = sandbox_max_output_chars

        logger.info("REPL State Manager initialized")

    def _create_sandbox(self) -> RestrictedPythonSandbox:
        """
        Create a new sandbox instance.

        Returns:
            RestrictedPythonSandbox instance
        """
        return RestrictedPythonSandbox(
            timeout=self._sandbox_timeout,
            max_output_chars=self._sandbox_max_output_chars,
        )

    def _create_api_instances(self, room_id: str) -> Dict[str, Any]:
        """
        Create API instances for a room.

        Args:
            room_id: Room identifier

        Returns:
            Dict of API instances (tools, bots, memory, etc.)
        """
        if self._api_factory:
            return self._api_factory(room_id)
        return {}

    def get_state(self, room_id: str) -> REPLState:
        """
        Get or create REPL state for a room.

        This method implements lazy initialization - state is only
        created when first accessed.

        Args:
            room_id: Room identifier (e.g., "project-alpha")

        Returns:
            REPLState instance for this room
        """
        if room_id not in self._states:
            logger.info(f"Creating new REPL state for room: {room_id}")

            # Create sandbox
            sandbox = self._create_sandbox()

            # Create API instances for this room
            api_instances = self._create_api_instances(room_id)

            # Create state
            self._states[room_id] = REPLState(
                room_id=room_id,
                sandbox=sandbox,
                api_instances=api_instances,
            )

        return self._states[room_id]

    def has_state(self, room_id: str) -> bool:
        """
        Check if a room has REPL state.

        Args:
            room_id: Room identifier

        Returns:
            True if state exists, False otherwise
        """
        return room_id in self._states

    def clear_state(self, room_id: str) -> bool:
        """
        Clear REPL state when room is archived.

        This is called when a room is deleted or archived to
        free up memory and prevent stale state.

        Args:
            room_id: Room identifier to clear

        Returns:
            True if state was cleared, False if it didn't exist
        """
        if room_id in self._states:
            logger.info(f"Clearing REPL state for room: {room_id}")
            del self._states[room_id]
            return True
        return False

    def reset_state(self, room_id: str) -> bool:
        """
        Reset REPL state for a room (clear variables, keep state).

        This is useful when the agent gets into a bad state but
        you don't want to delete the entire state object.

        Args:
            room_id: Room identifier

        Returns:
            True if state was reset, False if it didn't exist
        """
        if room_id in self._states:
            logger.info(f"Resetting REPL state for room: {room_id}")
            self._states[room_id].reset()
            return True
        return False

    def list_rooms(self) -> List[str]:
        """
        List all rooms with active REPL state.

        Returns:
            List of room IDs
        """
        return list(self._states.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        Get REPL state manager statistics.

        Returns:
            Dict with statistics
        """
        total_calls = sum(state.call_count for state in self._states.values())
        total_variables = sum(len(state.list_variables()) for state in self._states.values())

        return {
            "active_rooms": len(self._states),
            "room_ids": self.list_rooms(),
            "total_calls": total_calls,
            "total_variables": total_variables,
            "sandbox_timeout": self._sandbox_timeout,
            "sandbox_max_output_chars": self._sandbox_max_output_chars,
        }

    def get_room_stats(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific room.

        Args:
            room_id: Room identifier

        Returns:
            Dict with room statistics or None if room doesn't exist
        """
        if room_id in self._states:
            return self._states[room_id].get_stats()
        return None

    def clear_all(self) -> int:
        """
        Clear all REPL states.

        This is useful for testing or when shutting down.

        Returns:
            Number of states cleared
        """
        count = len(self._states)
        logger.info(f"Clearing all REPL states ({count} rooms)")
        self._states.clear()
        return count

    def cleanup_inactive(self, max_age_seconds: int = 3600) -> int:
        """
        Cleanup states that haven't been accessed recently.

        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)

        Returns:
            Number of states cleaned up
        """
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        to_remove = []

        for room_id, state in self._states.items():
            if state.last_accessed < cutoff:
                to_remove.append(room_id)

        for room_id in to_remove:
            logger.info(f"Cleaning up inactive REPL state: {room_id}")
            del self._states[room_id]

        return len(to_remove)

    def __len__(self) -> int:
        """Return number of active rooms."""
        return len(self._states)

    def __contains__(self, room_id: str) -> bool:
        """Check if a room has REPL state."""
        return room_id in self._states

    def __repr__(self) -> str:
        return f"REPLStateManager(rooms={len(self._states)})"
