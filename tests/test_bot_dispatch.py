"""Tests for Bot Dispatch system."""

import pytest
from nanobot.bots.dispatch import BotDispatch, DispatchTarget
from nanobot.models.room import Room, RoomType


@pytest.fixture
def dispatch():
    """Create BotDispatch instance."""
    return BotDispatch()


@pytest.fixture
def sample_room():
    """Create sample room with participants."""
    room = Room(
        id="test-project",
        type=RoomType.PROJECT,
        participants=["nanobot", "coder", "creative"]
    )
    return room


class TestLeaderFirstDispatch:
    """Test Leader-First dispatch logic."""

    def test_default_room_message_goes_to_leader(self, dispatch, sample_room):
        """Default messages in workspace go to Leader first."""
        result = dispatch.dispatch_message(
            message="Create a landing page",
            room=sample_room,
            is_dm=False
        )
        
        assert result.target == DispatchTarget.LEADER_FIRST
        assert result.primary_bot == "nanobot"
        assert "coder" in result.secondary_bots
        assert "creative" in result.secondary_bots
        assert result.room_id == "test-project"
    
    def test_leader_alone_in_workspace(self, dispatch):
        """Leader-only workspace works correctly."""
        room = Room(
            id="leader-only",
            type=RoomType.OPEN,
            participants=["nanobot"]
        )
        
        result = dispatch.dispatch_message(
            message="Hello",
            room=room,
            is_dm=False
        )
        
        assert result.primary_bot == "nanobot"
        assert result.secondary_bots == []  # No other bots


class TestDirectMentionDispatch:
    """Test bypassing leader with direct mentions."""
    
    def test_mention_coder_bypasses_leader(self, dispatch, sample_room):
        """@Coder goes directly to Coder, bypassing Leader."""
        result = dispatch.dispatch_message(
            message="@Coder help me with this bug",
            room=sample_room,
            is_dm=False
        )
        
        assert result.target == DispatchTarget.DIRECT_BOT
        assert result.primary_bot == "coder"
        assert result.secondary_bots == []  # Only coder
    
    def test_mention_researcher_bypasses_leader(self, dispatch, sample_room):
        """@Researcher goes directly to Researcher."""
        result = dispatch.dispatch_message(
            message="@Researcher find me some data",
            room=sample_room,
            is_dm=False
        )
        
        assert result.primary_bot == "researcher"
    
    def test_mention_all_includes_all_participants(self, dispatch, sample_room):
        """@all includes all workspace participants."""
        result = dispatch.dispatch_message(
            message="@all meeting in 5 minutes",
            room=sample_room,
            is_dm=False
        )
        
        assert result.primary_bot == "nanobot"  # Leader coordinates
        assert "coder" in result.secondary_bots
        assert "creative" in result.secondary_bots
    
    def test_mention_case_insensitive(self, dispatch, sample_room):
        """Mentions are case-insensitive."""
        result = dispatch.dispatch_message(
            message="@CODER @coder @Coder",
            room=sample_room,
            is_dm=False
        )
        
        assert result.primary_bot == "coder"


class TestDirectMessageDispatch:
    """Test DM routing (bypasses leader)."""
    
    def test_dm_to_coder_bypasses_leader(self, dispatch):
        """DM to Coder goes directly to Coder."""
        result = dispatch.dispatch_message(
            message="Help me code",
            is_dm=True,
            dm_target="coder"
        )
        
        assert result.target == DispatchTarget.DM
        assert result.primary_bot == "coder"
        assert result.secondary_bots == []
        assert result.room_id is None  # No workspace in DM
    
    def test_dm_to_leader_still_works(self, dispatch):
        """DM to Leader works normally."""
        result = dispatch.dispatch_message(
            message="What's the plan?",
            is_dm=True,
            dm_target="nanobot"
        )
        
        assert result.target == DispatchTarget.DM
        assert result.primary_bot == "nanobot"


class TestWorkspaceCreationDetection:
    """Test detecting workspace creation requests."""
    
    def test_detect_create_workspace(self, dispatch):
        """Detect 'create workspace' patterns."""
        should_create, name, project_type = dispatch.should_leader_create_workspace(
            "Create a workspace for the website"
        )
        
        assert should_create is True
        assert "website" in name.lower()
        assert project_type == "web"
    
    def test_detect_new_project(self, dispatch):
        """Detect 'new project' patterns."""
        should_create, name, project_type = dispatch.should_leader_create_workspace(
            "New project: mobile app"
        )
        
        assert should_create is True
        assert "mobile app" in name.lower()
        assert project_type == "mobile"
    
    def test_no_workspace_creation(self, dispatch):
        """Normal messages don't trigger workspace creation."""
        should_create, name, project_type = dispatch.should_leader_create_workspace(
            "What's the weather today?"
        )
        
        assert should_create is False
        assert name is None


class TestBotSuggestions:
    """Test bot suggestions for project types."""
    
    def test_web_project_suggests_coder_and_creative(self, dispatch):
        """Web projects need Coder and Creative."""
        bots = dispatch.suggest_bots_for_project("web")
        
        assert "nanobot" in bots
        assert "coder" in bots
        assert "creative" in bots
    
    def test_research_project_suggests_researcher(self, dispatch):
        """Research projects need Researcher."""
        bots = dispatch.suggest_bots_for_project("research")
        
        assert "nanobot" in bots
        assert "researcher" in bots
    
    def test_marketing_project_suggests_social_and_creative(self, dispatch):
        """Marketing projects need Social and Creative."""
        bots = dispatch.suggest_bots_for_project("marketing")
        
        assert "nanobot" in bots
        assert "social" in bots
        assert "creative" in bots
    
    def test_audit_project_suggests_auditor(self, dispatch):
        """Audit projects need Auditor."""
        bots = dispatch.suggest_bots_for_project("audit")
        
        assert "nanobot" in bots
        assert "auditor" in bots


class TestMentionExtraction:
    """Test mention extraction from messages."""
    
    def test_extract_coder_mention(self, dispatch):
        """Extract @Coder mention."""
        bot = dispatch._extract_mention("Hey @Coder help me")
        assert bot == "coder"
    
    def test_extract_all_mention(self, dispatch):
        """Extract @all mention."""
        bot = dispatch._extract_mention("Hello @all")
        assert bot == "all"
    
    def test_no_mention_returns_none(self, dispatch):
        """No mention returns None."""
        bot = dispatch._extract_mention("Just a normal message")
        assert bot is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
