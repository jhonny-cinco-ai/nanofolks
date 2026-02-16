"""Collapsible thinking display component for chat flow.

This module provides the ThinkingDisplay component that renders bot thinking
in a collapsible format in the chat flow.

Features:
- Collapsible/expandable state management
- Rich rendering with colors and icons
- Multi-bot support with filtering
- Configurable display options
"""

from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.style import Style

from nanofolks.agent.work_log import WorkLog
from nanofolks.cli.ui.thinking_summary import ThinkingSummaryBuilder


class ThinkingDisplay:
    """Manages display and state of collapsible thinking section.
    
    Renders bot thinking/reasoning in an expandable/collapsible format
    that users can toggle with a keypress.
    
    Attributes:
        log: The work log being displayed
        expanded: Whether the thinking section is currently expanded
        summary: One-line summary of thinking
        details: Detailed lines for expanded view
        bot_name: Optional bot name for filtering (multi-agent)
        use_colors: Whether to use colors in output
        show_stats: Whether to show statistics in expanded view
    """
    
    # Colors for different elements
    COLORS = {
        "header": "dim cyan",
        "summary": "blue",
        "step": "white",
        "decision": "yellow",
        "tool": "green",
        "correction": "magenta",
        "error": "red",
        "divider": "dim",
    }
    
    def __init__(
        self,
        work_log: WorkLog,
        bot_name: Optional[str] = None,
        use_colors: bool = True,
        show_stats: bool = True,
    ):
        """Initialize the thinking display.
        
        Args:
            work_log: The work log to display
            bot_name: Optional bot name to filter entries
            use_colors: Whether to use colors in output
            show_stats: Whether to show statistics in expanded view
        """
        self.log = work_log
        self.bot_name = bot_name
        self.expanded = False
        self.use_colors = use_colors
        self.show_stats = show_stats
        
        # Generate summary and details
        self.summary = ThinkingSummaryBuilder.generate_summary(work_log)
        self.details = ThinkingSummaryBuilder.generate_details(work_log, bot_name)
    
    def render(self) -> str:
        """Render the appropriate view (collapsed or expanded).
        
        Returns:
            String representation ready for printing
        """
        if self.expanded:
            return self.render_expanded()
        else:
            return self.render_collapsed()
    
    def render_collapsed(self) -> str:
        """Render single-line collapsed view.
        
        Output format:
            💭 Thinking: <summary> [SPACE to expand]
        
        Returns:
            Collapsed view string
        """
        if self.use_colors:
            text = Text()
            text.append("💭 ", style="cyan")
            text.append("Thinking: ", style=self.COLORS["summary"])
            text.append(self.summary, style="white")
            text.append(" [SPACE to expand]", style="dim")
            # Return the rendered text as string for compatibility
            return str(text)
        else:
            return f"💭 Thinking: {self.summary} [SPACE to expand]"
    
    def render_expanded(self) -> str:
        """Render multi-line expanded view.
        
        Output format:
            💭 Thinking [↓] <bot filter if applicable>
               Step 1 🎯 Decision: ...
               Step 2 🔧 Tool: ...
               ...
            [Statistics if enabled]
            [Press any key to continue...]
        
        Returns:
            Expanded view string
        """
        lines = []
        
        # Build header
        if self.use_colors:
            header = Text()
            header.append("💭 ", style="cyan")
            header.append("Thinking ", style=self.COLORS["header"])
            header.append("[↓]", style="dim cyan")
            if self.bot_name:
                header.append(f" (@{self.bot_name})", style="dim magenta")
            lines.append(str(header))
        else:
            header = "💭 Thinking [↓]"
            if self.bot_name:
                header += f" (@{self.bot_name})"
            lines.append(header)
        
        # Add detail lines with indentation
        for detail in self.details:
            lines.append(f"   {detail}")
        
        # Add statistics if enabled
        if self.show_stats:
            stats = self.get_stats()
            lines.append("")
            stats_line = f"   [{stats['total_steps']} steps • {stats['decisions']} decisions • {stats['tools']} tools]"
            if self.use_colors:
                lines.append(f"[dim]{stats_line}[/dim]")
            else:
                lines.append(stats_line)
        
        # Add footer
        lines.append("")
        if self.use_colors:
            lines.append("[dim][Press any key to continue...][/dim]")
        else:
            lines.append("[Press any key to continue...]")
        
        return "\n".join(lines)
    
    def toggle(self) -> None:
        """Toggle between expanded and collapsed state."""
        self.expanded = not self.expanded
    
    def expand(self) -> None:
        """Expand the thinking display."""
        self.expanded = True
    
    def collapse(self) -> None:
        """Collapse the thinking display."""
        self.expanded = False
    
    def get_stats(self) -> dict:
        """Get statistics about the thinking process.
        
        Returns:
            Dictionary with thinking stats
        """
        return ThinkingSummaryBuilder.get_summary_stats(self.log)
    
    def get_line_count(self) -> int:
        """Get number of lines when expanded.
        
        Returns:
            Number of lines the expanded view will take
        """
        # Header + details + blank line + footer
        return 3 + len(self.details)


def create_thinking_display(work_log: WorkLog, 
                           bot_name: Optional[str] = None) -> ThinkingDisplay:
    """Factory function to create a thinking display.
    
    Args:
        work_log: The work log to display
        bot_name: Optional bot name for filtering
        
    Returns:
        Initialized ThinkingDisplay instance
    """
    return ThinkingDisplay(work_log, bot_name)
