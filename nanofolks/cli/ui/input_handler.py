"""Async input handling for CLI interactions.

This module provides utilities for non-blocking keyboard input
to support interactive thinking display toggling.

Supports:
- SPACE: Toggle thinking display
- ESC: Exit thinking view
- Ctrl+C: Graceful interrupt
- Any other key: Continue
"""

import asyncio
import sys
from typing import Optional, Literal


async def async_input(prompt: str = "", timeout: Optional[float] = None) -> Optional[str]:
    """Read a line of input asynchronously.
    
    Args:
        prompt: Optional prompt to display
        timeout: Optional timeout in seconds
        
    Returns:
        The input string, or None if timeout
    """
    if prompt:
        print(prompt, end="", flush=True)
    
    loop = asyncio.get_event_loop()
    
    # Use executor to run blocking input in thread pool
    try:
        if timeout:
            line = await asyncio.wait_for(
                loop.run_in_executor(None, sys.stdin.readline),
                timeout=timeout
            )
        else:
            line = await loop.run_in_executor(None, sys.stdin.readline)
        
        return line.rstrip("\n")
    except asyncio.TimeoutError:
        return None


async def async_get_key(timeout: Optional[float] = None) -> Optional[str]:
    """Read a single keypress asynchronously.
    
    Attempts to read a single character without waiting for Enter.
    Falls back to regular input on systems where it's not supported.
    
    Args:
        timeout: Optional timeout in seconds
        
    Returns:
        The key pressed, or None if timeout
    """
    import platform
    
    system = platform.system()
    
    if system == "Windows":
        return await _windows_getch(timeout)
    else:
        return await _unix_getch(timeout)


async def _unix_getch(timeout: Optional[float] = None) -> Optional[str]:
    """Unix/Linux/macOS single key input.
    
    Args:
        timeout: Optional timeout in seconds
        
    Returns:
        The key pressed, or None if timeout
    """
    import tty
    import termios
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        tty.setraw(fd)
        
        loop = asyncio.get_event_loop()
        
        try:
            if timeout:
                key = await asyncio.wait_for(
                    loop.run_in_executor(None, sys.stdin.read, 1),
                    timeout=timeout
                )
            else:
                key = await loop.run_in_executor(None, sys.stdin.read, 1)
            
            return key if key else None
        except asyncio.TimeoutError:
            return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


async def _windows_getch(timeout: Optional[float] = None) -> Optional[str]:
    """Windows single key input.
    
    Args:
        timeout: Optional timeout in seconds
        
    Returns:
        The key pressed, or None if timeout
    """
    try:
        import msvcrt
        
        loop = asyncio.get_event_loop()
        
        # Windows doesn't have good async key reading, fall back to blocking
        try:
            if timeout:
                key = await asyncio.wait_for(
                    loop.run_in_executor(None, msvcrt.getch),
                    timeout=timeout
                )
            else:
                key = await loop.run_in_executor(None, msvcrt.getch)
            
            return key.decode("utf-8") if isinstance(key, bytes) else key
        except asyncio.TimeoutError:
            return None
    except ImportError:
        # Fall back to regular input on Windows if msvcrt unavailable
        return await async_input(timeout=timeout)


async def wait_for_key(message: str = "Press any key to continue...") -> str:
    """Wait for user to press any key, with optional message.
    
    Args:
        message: Message to display while waiting
        
    Returns:
        The key that was pressed
    """
    if message:
        print(message)
    
    key = await async_get_key()
    return key if key else ""


def is_escape_key(key: str) -> bool:
    """Check if the key pressed is ESC.
    
    Args:
        key: The key character
        
    Returns:
        True if key is ESC (ASCII 27)
    """
    return key == "\x1b" or key == "\033"


def is_ctrl_c(key: str) -> bool:
    """Check if the key pressed is Ctrl+C.
    
    Args:
        key: The key character
        
    Returns:
        True if key is Ctrl+C (ASCII 3)
    """
    return key == "\x03"


class ThinkingInputHandler:
    """Manages keyboard input for thinking display interaction.
    
    Handles:
    - SPACE: Toggle expanded/collapsed
    - ESC: Exit thinking view
    - Ctrl+C: Graceful interrupt
    - Any other key: Continue to next prompt
    """
    
    def __init__(self):
        """Initialize input handler."""
        self.last_action: Optional[str] = None
    
    async def get_thinking_action(
        self, timeout: Optional[float] = None
    ) -> Literal["toggle", "exit", "interrupt", "continue"]:
        """Get user's action for thinking display.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            One of: "toggle", "exit", "interrupt", "continue"
        """
        try:
            key = await async_get_key(timeout)
            
            if not key:
                # Timeout - treat as continue
                self.last_action = "continue"
                return "continue"
            
            if key == " ":  # Space bar
                self.last_action = "toggle"
                return "toggle"
            elif is_escape_key(key):  # ESC
                self.last_action = "exit"
                return "exit"
            elif is_ctrl_c(key):  # Ctrl+C
                self.last_action = "interrupt"
                return "interrupt"
            else:
                # Any other key
                self.last_action = "continue"
                return "continue"
        except Exception as e:
            # On error, treat as continue
            return "continue"
    
    def get_last_action(self) -> Optional[str]:
        """Get the last action taken by the user.
        
        Returns:
            The last action, or None if none yet
        """
        return self.last_action
