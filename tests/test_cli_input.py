import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from prompt_toolkit.formatted_text import HTML

from nanofolks.cli import commands


@pytest.fixture
def mock_prompt_session():
    """Mock the global prompt session."""
    mock_session = MagicMock()
    mock_session.prompt_async = AsyncMock()
    with patch("nanofolks.cli.commands._PROMPT_SESSION", mock_session):
        yield mock_session


@pytest.mark.asyncio
async def test_read_interactive_input_async_returns_input(mock_prompt_session):
    """Test that _read_interactive_input_async returns the user input from prompt_session."""
    mock_prompt_session.prompt_async.return_value = "hello world"

    result = await commands._read_interactive_input_async()

    assert result == "hello world"
    mock_prompt_session.prompt_async.assert_called_once()
    args, _ = mock_prompt_session.prompt_async.call_args
    assert isinstance(args[0], HTML)  # Verify HTML prompt is used


@pytest.mark.asyncio
async def test_read_interactive_input_async_handles_eof(mock_prompt_session):
    """Test that EOFError converts to KeyboardInterrupt."""
    mock_prompt_session.prompt_async.side_effect = EOFError()

    with pytest.raises(KeyboardInterrupt):
        await commands._read_interactive_input_async()


def test_init_prompt_session_creates_session():
    """Test that _init_prompt_session initializes the global session."""
    # Ensure global is None before test
    commands._PROMPT_SESSION = None

    with (
        patch("nanofolks.cli.commands.PromptSession") as MockSession,
        patch("nanofolks.cli.commands.FileHistory") as MockHistory,
        patch("pathlib.Path.home", return_value=MagicMock()),
    ):
        commands._init_prompt_session()

        assert commands._PROMPT_SESSION is not None
        MockSession.assert_called_once()
        MockHistory.assert_called_once()
        _, kwargs = MockSession.call_args
        assert kwargs["multiline"] is False
        assert kwargs["enable_open_in_editor"] is False


class _FakeRoomManager:
    def __init__(self):
        self.default_room = SimpleNamespace(id="general")
        self._rooms = {
            "general": SimpleNamespace(id="general"),
            "project-alpha": SimpleNamespace(id="project-alpha"),
        }

    def get_room(self, room_id: str):
        return self._rooms.get(room_id)


def test_parse_switch_target_accepts_bare_switch():
    assert commands._parse_switch_target("/switch") == ""


def test_parse_switch_target_accepts_switch_with_room():
    assert commands._parse_switch_target("/switch project-alpha") == "project-alpha"


def test_parse_switch_target_rejects_similar_prefix():
    assert commands._parse_switch_target("/switching") is None


def test_resolve_chat_room_and_session_normalizes_room_ids():
    manager = _FakeRoomManager()
    room, current_room, session_id = commands._resolve_chat_room_and_session(
        room="#general",
        session_id=None,
        room_manager=manager,
    )
    assert room == "general"
    assert current_room.id == "general"
    assert session_id == "room:general"


def test_resolve_chat_room_and_session_session_takes_precedence():
    manager = _FakeRoomManager()
    room, current_room, session_id = commands._resolve_chat_room_and_session(
        room="general",
        session_id="room:project-alpha",
        room_manager=manager,
    )
    assert room == "project-alpha"
    assert current_room.id == "project-alpha"
    assert session_id == "room:project-alpha"
