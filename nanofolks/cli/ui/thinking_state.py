"""State management for thinking display preferences.

This module tracks user preferences for the thinking display,
including whether it should be expanded or collapsed per message.

Supports:
- Persisting expanded/collapsed state per message
- Session-wide preferences
- Configurable defaults
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class ThinkingDisplayMode(Enum):
    """Modes for thinking display."""
    ALWAYS_COLLAPSED = "always_collapsed"
    ALWAYS_EXPANDED = "always_expanded"
    REMEMBER_STATE = "remember_state"
    USER_CHOICE = "user_choice"


@dataclass
class ThinkingDisplayState:
    """Tracks state for a single message's thinking display."""
    message_index: int
    expanded: bool = False
    visited: int = 0  # How many times user has toggled

    def increment_visits(self) -> None:
        """Record that user visited this thinking display."""
        self.visited += 1


class ThinkingStateTracker:
    """Manages thinking display state across messages.

    Tracks:
    - Whether each message's thinking display is expanded/collapsed
    - User preference history
    - Session-wide defaults
    """

    def __init__(
        self,
        mode: ThinkingDisplayMode = ThinkingDisplayMode.REMEMBER_STATE,
        default_expanded: bool = False,
    ):
        """Initialize state tracker.

        Args:
            mode: How to handle state persistence
            default_expanded: Default state for new messages
        """
        self.mode = mode
        self.default_expanded = default_expanded
        self.states: Dict[int, ThinkingDisplayState] = {}
        self.global_preference: Optional[bool] = None

    def should_be_expanded(self, message_index: int) -> bool:
        """Determine if thinking display should be expanded for this message.

        Args:
            message_index: Index of the message

        Returns:
            True if should be expanded, False if collapsed
        """
        if self.mode == ThinkingDisplayMode.ALWAYS_EXPANDED:
            return True
        elif self.mode == ThinkingDisplayMode.ALWAYS_COLLAPSED:
            return False
        elif self.mode == ThinkingDisplayMode.REMEMBER_STATE:
            # Return remembered state, or default if not seen
            if message_index in self.states:
                return self.states[message_index].expanded
            return self.default_expanded
        else:  # USER_CHOICE
            # Use global preference if set, otherwise default
            if self.global_preference is not None:
                return self.global_preference
            return self.default_expanded

    def record_state(self, message_index: int, expanded: bool) -> None:
        """Record the state of a thinking display after user interaction.

        Args:
            message_index: Index of the message
            expanded: Whether display was expanded
        """
        if message_index not in self.states:
            self.states[message_index] = ThinkingDisplayState(message_index)

        state = self.states[message_index]
        state.expanded = expanded
        state.increment_visits()

        # Update global preference based on mode
        if self.mode == ThinkingDisplayMode.USER_CHOICE:
            self.global_preference = expanded

    def get_state(self, message_index: int) -> Optional[ThinkingDisplayState]:
        """Get stored state for a message.

        Args:
            message_index: Index of the message

        Returns:
            State object if exists, None otherwise
        """
        return self.states.get(message_index)

    def get_all_states(self) -> Dict[int, ThinkingDisplayState]:
        """Get all stored states.

        Returns:
            Dictionary of all states
        """
        return self.states.copy()

    def reset_message_state(self, message_index: int) -> None:
        """Reset state for a specific message.

        Args:
            message_index: Index of the message
        """
        if message_index in self.states:
            del self.states[message_index]

    def reset_all(self) -> None:
        """Reset all state tracking."""
        self.states.clear()
        self.global_preference = None

    def set_mode(self, mode: ThinkingDisplayMode) -> None:
        """Change the state tracking mode.

        Args:
            mode: New mode to use
        """
        self.mode = mode

    def get_stats(self) -> Dict[str, any]:
        """Get statistics about state tracking.

        Returns:
            Dictionary with stats
        """
        total_messages = len(self.states)
        expanded_count = sum(1 for s in self.states.values() if s.expanded)
        total_visits = sum(s.visited for s in self.states.values())

        return {
            "total_messages": total_messages,
            "expanded_count": expanded_count,
            "collapsed_count": total_messages - expanded_count,
            "total_visits": total_visits,
            "average_visits": total_visits / total_messages if total_messages > 0 else 0,
            "current_mode": self.mode.value,
            "global_preference": self.global_preference,
        }


class SessionThinkingPreferences:
    """Manages session-wide thinking display preferences.

    Stores user preferences that persist across messages in a session.
    """

    def __init__(self):
        """Initialize preferences."""
        self.show_thinking = True  # Show thinking display at all
        self.use_colors = True  # Use colored output
        self.show_stats = True  # Show statistics in expanded view
        self.auto_expand_on_errors = True  # Auto-expand if there were errors
        self.max_summary_length = 80  # Max length before truncation

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary.

        Returns:
            Dictionary of preferences
        """
        return {
            "show_thinking": self.show_thinking,
            "use_colors": self.use_colors,
            "show_stats": self.show_stats,
            "auto_expand_on_errors": self.auto_expand_on_errors,
            "max_summary_length": self.max_summary_length,
        }

    def from_dict(self, data: Dict[str, any]) -> None:
        """Load from dictionary.

        Args:
            data: Dictionary of preferences
        """
        if "show_thinking" in data:
            self.show_thinking = data["show_thinking"]
        if "use_colors" in data:
            self.use_colors = data["use_colors"]
        if "show_stats" in data:
            self.show_stats = data["show_stats"]
        if "auto_expand_on_errors" in data:
            self.auto_expand_on_errors = data["auto_expand_on_errors"]
        if "max_summary_length" in data:
            self.max_summary_length = data["max_summary_length"]
