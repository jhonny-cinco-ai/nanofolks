"""
REPL State - Room-scoped Python environment state.

This module manages the persistent state for a single room's REPL environment.
State persists across tool calls within the same room.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from nanofolks.agent.tools.repl_sandbox import (
    RestrictedPythonSandbox,
    REPLError,
    REPLTimeoutError,
)


@dataclass
class REPLExecutionResult:
    """Result of a REPL execution."""

    success: bool
    output: str
    error: Optional[str] = None
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class REPLState:
    """
    REPL state for a single room.

    This class manages:
    - Persistent Python globals (survive across calls)
    - Sandboxed code execution
    - Room-scoped isolation
    - Execution history

    The state is room-scoped, meaning:
    - All channels in a room share the same REPL state
    - Variables persist across calls within the same room
    - State is cleared when room is archived

    Example:
        state = REPLState(room_id="project-alpha", sandbox=...)

        # Execute code (variables persist)
        result = await state.execute("x = 10")
        result = await state.execute("print(x * 2)")  # Prints: 20

        # Inspect state
        variables = state.list_variables()  # {'x': 'int'}
    """

    def __init__(
        self,
        room_id: str,
        sandbox: RestrictedPythonSandbox,
        api_instances: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize REPL state for a room.

        Args:
            room_id: Room identifier (e.g., "project-alpha")
            sandbox: RestrictedPythonSandbox instance
            api_instances: Optional pre-created API instances (tools, bots, memory, etc.)
        """
        self.room_id = room_id
        self.sandbox = sandbox
        self.call_count = 0
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()

        # Execution history (last N executions)
        self._history: List[REPLExecutionResult] = []
        self._max_history = 50

        # Track API instance keys (for reset)
        self._api_keys: set = set()

        # Persistent globals (survive across calls)
        # These are shared by all channels in this room
        self.globals: Dict[str, Any] = {}

        # Initialize with safe builtins
        self.globals["__builtins__"] = sandbox._create_safe_builtins()

        # Add API instances if provided
        if api_instances:
            self.globals.update(api_instances)
            self._api_keys = set(api_instances.keys())

        logger.debug(f"REPL state initialized for room: {room_id}")

    async def execute(self, code: str) -> str:
        """
        Execute Python code in this room's REPL.

        Args:
            code: Python code to execute

        Returns:
            Execution result as string
        """
        import time

        self.call_count += 1
        self.last_accessed = datetime.now()

        logger.debug(
            f"Executing REPL code in room {self.room_id} "
            f"(call #{self.call_count}, {len(code)} chars)"
        )

        start_time = time.time()
        result: Optional[REPLExecutionResult] = None

        try:
            output = await self.sandbox.execute_async(
                code=code,
                globals_dict=self.globals,
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            result = REPLExecutionResult(
                success=True,
                output=output,
                execution_time_ms=execution_time_ms,
            )

            logger.debug(
                f"REPL execution complete in room {self.room_id}: "
                f"{len(output)} chars output, {execution_time_ms}ms"
            )

            return output

        except REPLTimeoutError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result = REPLExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
            logger.warning(f"REPL timeout in room {self.room_id}: {e}")
            return f"Error: {e}"

        except REPLError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result = REPLExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )
            logger.error(f"REPL error in room {self.room_id}: {e}")
            return f"Error: {e}"

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result = REPLExecutionResult(
                success=False,
                output="",
                error=f"{type(e).__name__}: {str(e)}",
                execution_time_ms=execution_time_ms,
            )
            logger.error(f"Unexpected REPL error in room {self.room_id}: {e}")
            return f"Error: {type(e).__name__}: {str(e)}"

        finally:
            # Add to history
            if result:
                self._history.append(result)
                # Trim history if needed
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history :]

    def reset(self) -> None:
        """
        Reset REPL state (clear all variables).

        This is useful for debugging or when the agent gets into a bad state.
        API instances are preserved.
        """
        logger.info(f"Resetting REPL state for room: {self.room_id}")

        # Preserve only API instances
        api_instances = {k: v for k, v in self.globals.items() if k in self._api_keys}

        # Reset globals
        self.globals = {}
        self.globals["__builtins__"] = self.sandbox._create_safe_builtins()

        # Restore API instances
        self.globals.update(api_instances)

        # Reset counters
        self.call_count = 0
        self._history = []
        self.last_accessed = datetime.now()

    def list_variables(self) -> Dict[str, str]:
        """
        List current REPL variables (for debugging).

        Returns:
            Dict of variable name → type name
        """
        return {
            name: type(value).__name__
            for name, value in self.globals.items()
            if not name.startswith("_")
        }

    def get_variable(self, name: str) -> Optional[Any]:
        """
        Get a specific variable value.

        Args:
            name: Variable name

        Returns:
            Variable value or None if not found
        """
        return self.globals.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a specific variable value (for testing).

        Args:
            name: Variable name
            value: Variable value
        """
        self.globals[name] = value
        logger.debug(f"Set variable '{name}' in room {self.room_id}")

    def delete_variable(self, name: str) -> bool:
        """
        Delete a variable from the REPL state.

        Args:
            name: Variable name

        Returns:
            True if variable was deleted, False if not found
        """
        if name in self.globals and not name.startswith("_"):
            del self.globals[name]
            logger.debug(f"Deleted variable '{name}' in room {self.room_id}")
            return True
        return False

    def get_history(self, limit: int = 10) -> List[REPLExecutionResult]:
        """
        Get execution history.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of execution results (most recent first)
        """
        return list(reversed(self._history[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get REPL state statistics.

        Returns:
            Dict with statistics
        """
        return {
            "room_id": self.room_id,
            "call_count": self.call_count,
            "variable_count": len(self.list_variables()),
            "history_size": len(self._history),
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
        }

    def __repr__(self) -> str:
        return (
            f"REPLState(room_id={self.room_id!r}, "
            f"calls={self.call_count}, "
            f"variables={len(self.list_variables())})"
        )
