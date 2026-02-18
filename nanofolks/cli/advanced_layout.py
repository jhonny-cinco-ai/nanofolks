"""Advanced terminal layout for Phase 3 of CLI UX improvements.

Provides:
- Rich Layout-based side-by-side display
- Terminal resize detection and handling
- Live sidebar updates
- Smooth transitions and animations
"""

import shutil
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

console = Console()


class AdvancedLayout:
    """Manages Rich Layout-based terminal layout with sidebar."""

    def __init__(self, min_width: int = 80):
        """Initialize advanced layout.

        Args:
            min_width: Minimum terminal width required
        """
        self.min_width = min_width
        self.width = self._get_terminal_width()
        self.height = self._get_terminal_height()
        self.sidebar_width = max(20, int(self.width * 0.25))  # 25% width, min 20
        self.chat_width = self.width - self.sidebar_width - 2  # Account for borders
        self._resize_callbacks: List[Callable] = []
        self._monitoring = False

    def _get_terminal_width(self) -> int:
        """Get current terminal width."""
        return shutil.get_terminal_size().columns

    def _get_terminal_height(self) -> int:
        """Get current terminal height."""
        return shutil.get_terminal_size().lines

    def can_use_layout(self) -> bool:
        """Check if terminal is wide enough for layout."""
        return self._get_terminal_width() >= self.min_width

    def on_resize(self, callback: Callable) -> None:
        """Register callback for resize events.

        Args:
            callback: Function to call when terminal resizes
        """
        self._resize_callbacks.append(callback)

    def start_monitoring(self) -> None:
        """Start monitoring for terminal resize events."""
        if self._monitoring:
            return

        self._monitoring = True

        def monitor():
            last_width = self.width
            last_height = self.height

            while self._monitoring:
                time.sleep(0.5)  # Check every 500ms
                new_width = self._get_terminal_width()
                new_height = self._get_terminal_height()

                if new_width != last_width or new_height != last_height:
                    self.width = new_width
                    self.height = new_height
                    self.sidebar_width = max(20, int(self.width * 0.25))
                    self.chat_width = self.width - self.sidebar_width - 2

                    # Trigger callbacks
                    for callback in self._resize_callbacks:
                        try:
                            callback()
                        except Exception:
                            pass

                    last_width = new_width
                    last_height = new_height

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def stop_monitoring(self) -> None:
        """Stop monitoring for resize events."""
        self._monitoring = False

    def create_layout(self) -> Layout:
        """Create Rich Layout for side-by-side display.

        Returns:
            Rich Layout with main chat area and sidebar
        """
        layout = Layout()

        # Split into chat area (70%) and sidebar (30%)
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        # Split body into chat (70%) and sidebar (30%)
        layout["body"].split_row(
            Layout(name="chat"),
            Layout(name="sidebar", size=self.sidebar_width)
        )

        return layout

    def render_header(self, room_id: str, team_count: int, bot_emojis: str = "") -> RenderableType:
        """Render header with room status.

        Args:
            room_id: Current room ID
            team_count: Number of team members
            bot_emojis: Emoji string of team

        Returns:
            Renderable header
        """
        status = f"[bold cyan]#{room_id}[/bold cyan] • "
        status += f"[dim]Team:[/dim] [green]{team_count}[/green]"
        if bot_emojis:
            status += f" {bot_emojis}"

        return Panel(
            status,
            title="[bold cyan]🤖 nanofolks[/bold cyan]",
            expand=False
        )

    def render_footer(self, prompt_text: str = "") -> RenderableType:
        """Render footer with prompt.

        Args:
            prompt_text: Optional custom prompt text

        Returns:
            Renderable footer
        """
        if not prompt_text:
            prompt_text = "[#general] You: "

        return Panel(
            prompt_text,
            expand=False
        )

    def render_sidebar(
        self,
        team_roster: str,
        room_list: str
    ) -> RenderableType:
        """Render sidebar with team and rooms.

        Args:
            team_roster: Team roster display
            room_list: Room list display

        Returns:
            Renderable sidebar
        """
        # Combine roster and room list in sidebar
        content = f"{team_roster}\n\n{room_list}"

        return Panel(
            content,
            title="[bold cyan]📊 Dashboard[/bold cyan]",
            expand=True
        )

    def render_chat_area(
        self,
        chat_content: str,
        show_border: bool = True
    ) -> RenderableType:
        """Render main chat area.

        Args:
            chat_content: Chat messages to display
            show_border: Whether to show border panel

        Returns:
            Renderable chat area
        """
        if show_border:
            return Panel(
                chat_content,
                title="[bold cyan]💬 Chat[/bold cyan]",
                expand=True
            )
        else:
            return Text(chat_content)


class LayoutManager:
    """Manages layout lifecycle and updates."""

    def __init__(self):
        """Initialize layout manager."""
        self.advanced_layout = AdvancedLayout()
        self.layout: Optional[Layout] = None
        self.live_display: Optional[Live] = None
        self._is_running = False

    def start(self) -> None:
        """Start advanced layout mode."""
        if not self.advanced_layout.can_use_layout():
            console.print("[yellow]Terminal too narrow for advanced layout. "
                        "Using simple mode.[/yellow]")
            return

        self._is_running = True
        self.layout = self.advanced_layout.create_layout()
        self.advanced_layout.start_monitoring()

    def stop(self) -> None:
        """Stop advanced layout mode."""
        self._is_running = False
        self.advanced_layout.stop_monitoring()
        if self.live_display:
            self.live_display.stop()

    def update(
        self,
        header: Optional[RenderableType] = None,
        chat: Optional[RenderableType] = None,
        sidebar: Optional[RenderableType] = None,
        footer: Optional[RenderableType] = None
    ) -> None:
        """Update layout sections.

        Args:
            header: New header content
            chat: New chat area content
            sidebar: New sidebar content
            footer: New footer content
        """
        if not self._is_running or not self.layout:
            return

        if header:
            self.layout["header"].update(header)
        if chat:
            self.layout["chat"].update(chat)
        if sidebar:
            self.layout["sidebar"].update(sidebar)
        if footer:
            self.layout["footer"].update(footer)


class SidebarManager:
    """Manages sidebar content updates."""

    def __init__(self):
        """Initialize sidebar manager."""
        self.team_roster_content = ""
        self.room_list_content = ""
        self._update_timestamp = datetime.now()

    def update_team_roster(self, content: str) -> None:
        """Update team roster display.

        Args:
            content: New roster content
        """
        self.team_roster_content = content
        self._update_timestamp = datetime.now()

    def update_room_list(self, content: str) -> None:
        """Update room list display.

        Args:
            content: New room list content
        """
        self.room_list_content = content
        self._update_timestamp = datetime.now()

    def get_content(self) -> str:
        """Get combined sidebar content.

        Returns:
            Combined sidebar content
        """
        return f"{self.team_roster_content}\n{self.room_list_content}"

    def get_last_update(self) -> datetime:
        """Get timestamp of last update.

        Returns:
            Last update datetime
        """
        return self._update_timestamp


class TransitionEffect:
    """Smooth transition effects."""

    @staticmethod
    def fade_in(content: str, steps: int = 3) -> None:
        """Fade in content with gradual display.

        Args:
            content: Content to fade in
            steps: Number of fade steps
        """
        # Simple fade effect using opacity/dimming
        for step in range(steps):
            opacity = (step + 1) / steps
            dim = "[dim]" if opacity < 0.7 else ""
            undim = "[/dim]" if opacity < 0.7 else ""
            console.print(f"{dim}{content}{undim}")
            if step < steps - 1:
                time.sleep(0.1)

    @staticmethod
    def slide_in(content: str, direction: str = "left", duration: float = 0.3) -> None:
        """Slide in content.

        Args:
            content: Content to slide
            direction: Direction of slide (left, right, up, down)
            duration: Animation duration in seconds
        """
        # Simple slide effect
        console.print(content)
        time.sleep(duration)

    @staticmethod
    def highlight(text: str, duration: float = 0.5) -> None:
        """Highlight text with brief animation.

        Args:
            text: Text to highlight
            duration: Animation duration
        """
        console.print(f"[bold green]{text}[/bold green]")
        time.sleep(duration * 0.5)
        console.print(f"{text}")


class ResponsiveLayout:
    """Handles layout responsiveness based on terminal size."""

    @staticmethod
    def get_layout_mode(width: int) -> str:
        """Determine layout mode based on terminal width.

        Args:
            width: Terminal width

        Returns:
            Layout mode: "full" (advanced), "compact", or "minimal"
        """
        if width >= 120:
            return "full"
        elif width >= 80:
            return "compact"
        else:
            return "minimal"

    @staticmethod
    def render_for_mode(mode: str, content: Dict[str, str]) -> str:
        """Render content appropriate for layout mode.

        Args:
            mode: Layout mode
            content: Dict with content keys

        Returns:
            Formatted content for mode
        """
        if mode == "full":
            # All content displayed side-by-side
            return content.get("full", "")
        elif mode == "compact":
            # Stacked layout
            return f"{content.get('header', '')}\n{content.get('chat', '')}\n{content.get('sidebar', '')}"
        else:
            # Minimal - just chat
            return content.get("chat", "")


# Export public API
__all__ = [
    "AdvancedLayout",
    "LayoutManager",
    "SidebarManager",
    "TransitionEffect",
    "ResponsiveLayout",
]
