"""Bot invocation system for delegating tasks to specialist bots.

This module provides synchronous bot invocation where the main agent (nanobot)
can delegate tasks to specialist bots and wait for their responses.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from nanobot.agent.work_log import LogLevel
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider
from nanobot.agent.context import ContextBuilder
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirTool
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.web import WebSearchTool, WebFetchTool
from nanobot.security.sanitizer import SecretSanitizer
from nanobot.config.schema import ExecToolConfig
from nanobot.session.manager import SessionManager


# Available specialist bots that can be invoked
AVAILABLE_BOTS = {
    "researcher": {
        "domain": "research",
        "description": "Deep research, analysis, and information gathering",
        "default_name": "Navigator",
    },
    "coder": {
        "domain": "development", 
        "description": "Code implementation, debugging, and technical solutions",
        "default_name": "Gunner",
    },
    "social": {
        "domain": "community",
        "description": "Community engagement, communication, and user relations",
        "default_name": "Lookout",
    },
    "creative": {
        "domain": "design",
        "description": "Creative brainstorming, design, and content creation",
        "default_name": "Artist",
    },
    "auditor": {
        "domain": "quality",
        "description": "Quality review, validation, and compliance checking",
        "default_name": "Quartermaster",
    },
}


class BotInvoker:
    """
    Manages synchronous bot invocations.
    
    Allows the main agent (nanobot) to delegate tasks to specialist bots
    and wait for their responses. Each bot has its own processing context
    with its SOUL.md personality.
    """
    
    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        bus: MessageBus,
        work_log_manager: Any = None,
        model: str | None = None,
        brave_api_key: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
        restrict_to_workspace: bool = False,
        evolutionary: bool = False,
        allowed_paths: list[str] | None = None,
        protected_paths: list[str] | None = None,
    ):
        self.provider = provider
        self.workspace = workspace
        self.bus = bus
        self.model = model or provider.get_default_model()
        self.brave_api_key = brave_api_key
        self.exec_config = exec_config or ExecToolConfig()
        self.restrict_to_workspace = restrict_to_workspace
        self.evolutionary = evolutionary
        self.protected_paths = protected_paths or []
        self.allowed_paths = allowed_paths or []
        
        # Initialize secret sanitizer
        self.sanitizer = SecretSanitizer()
        
        # Work log manager for multi-bot tracking
        self.work_log_manager = work_log_manager
        
        # Active invocations
        self._active_invocations: dict[str, asyncio.Task[None]] = {}
        self._pending_results: dict[str, asyncio.Future[str]] = {}
    
    async def invoke(
        self,
        bot_name: str,
        task: str,
        context: Optional[str] = None,
        session_id: str = "invoke:default",
    ) -> str:
        """
        Invoke a specialist bot to handle a task.
        
        Args:
            bot_name: Name of bot to invoke (researcher, coder, social, creative, auditor)
            task: Task description for the bot
            context: Additional context from the main conversation
            session_id: Session ID for this invocation
            
        Returns:
            Bot's response to the task
        """
        if bot_name not in AVAILABLE_BOTS:
            return f"Error: Unknown bot '{bot_name}'. Available bots: {', '.join(AVAILABLE_BOTS.keys())}"
        
        if bot_name == "nanobot":
            return "Error: Cannot invoke nanobot (Leader) - use @nanobot directly"
        
        invocation_id = str(uuid.uuid4())[:8]
        
        # Create future to wait for result
        loop = asyncio.get_event_loop()
        result_future: asyncio.Future[str] = loop.create_future()
        self._pending_results[invocation_id] = result_future
        
        logger.info(f"Invoking {bot_name} (id: {invocation_id}): {task[:50]}...")
        
        # Log the bot invocation request
        self._log_invocation_request(bot_name, task, context)
        
        # Create the invocation task
        task_handle = asyncio.create_task(
            self._process_invocation(
                invocation_id=invocation_id,
                bot_name=bot_name,
                task=task,
                context=context,
                session_id=session_id,
                result_future=result_future,
            )
        )
        self._active_invocations[invocation_id] = task_handle
        
        try:
            # Wait for result with timeout (5 minutes)
            result = await asyncio.wait_for(result_future, timeout=300.0)
            logger.info(f"Invocation {invocation_id} completed: {result[:100]}...")
            
            # Log the bot's response
            self._log_invocation_response(bot_name, task, result)
            
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Invocation {invocation_id} timed out")
            self._log_invocation_error(bot_name, task, "timeout")
            return f"Error: Bot '{bot_name}' timed out after 5 minutes"
        except Exception as e:
            logger.error(f"Invocation {invocation_id} failed: {e}")
            self._log_invocation_error(bot_name, task, str(e))
            return f"Error: Bot '{bot_name}' failed: {str(e)}"
            return f"Error: Bot '{bot_name}' failed: {str(e)}"
        finally:
            # Cleanup
            self._active_invocations.pop(invocation_id, None)
            self._pending_results.pop(invocation_id, None)
    
    async def _process_invocation(
        self,
        invocation_id: str,
        bot_name: str,
        task: str,
        context: Optional[str],
        session_id: str,
        result_future: asyncio.Future[str],
    ) -> None:
        """Process a bot invocation."""
        try:
            # Build system prompt for this bot
            system_prompt = await self._build_bot_system_prompt(bot_name, task)
            
            # Build user message
            user_message = task
            if context:
                user_message = f"Context from Leader:\n{context}\n\n---\n\nTask:\n{task}"
            
            # Process through LLM (simplified - just use main model for now)
            response = await self._call_bot_llm(bot_name, system_prompt, user_message, session_id)
            
            # Set result
            if not result_future.done():
                result_future.set_result(response)
                
        except Exception as e:
            logger.error(f"Invocation {invocation_id} error: {e}")
            if not result_future.done():
                result_future.set_exception(e)
    
    async def _build_bot_system_prompt(self, bot_name: str, task: str) -> str:
        """Build system prompt for the invoked bot."""
        from nanobot.soul import SoulManager
        
        # Get bot's SOUL.md if exists
        soul_manager = SoulManager(self.workspace)
        soul_content = soul_manager.get_bot_soul(bot_name)
        
        # Build system prompt
        bot_info = AVAILABLE_BOTS[bot_name]
        
        if soul_content:
            system_prompt = soul_content
        else:
            # Fallback to basic role
            system_prompt = f"""You are @{bot_name} ({bot_info['default_name']}), a specialist bot.

Domain: {bot_info['domain']}
Role: {bot_info['description']}

You are a specialist focused on {bot_info['domain']} tasks. 
Provide helpful, expert responses in your domain."""
        
        # Add task context
        system_prompt += f"""

You were invoked by the Leader (nanobot) to help with a task.
Focus only on your domain expertise and provide a helpful response.
"""
        
        return system_prompt
    
    async def _call_bot_llm(
        self,
        bot_name: str,
        system_prompt: str,
        user_message: str,
        session_id: str,
    ) -> str:
        """Call LLM with bot's context."""
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        # Call LLM
        response = await self.provider.chat(
            model=self.model,
            messages=messages,
            max_tokens=4000,
        )
        
        return response.content
    
    def list_available_bots(self) -> dict:
        """List all bots that can be invoked."""
        return AVAILABLE_BOTS.copy()
    
    def get_bot_info(self, bot_name: str) -> Optional[dict]:
        """Get information about a specific bot."""
        return AVAILABLE_BOTS.get(bot_name)
    
    def _log_invocation_request(
        self,
        bot_name: str,
        task: str,
        context: Optional[str] = None,
    ) -> None:
        """Log a bot invocation request using work_log_manager."""
        if not self.work_log_manager:
            return
        
        try:
            # Log as a bot message with mention
            self.work_log_manager.log_bot_message(
                bot_name="nanobot",
                message=f"Invoking @{bot_name} with task: {task[:200]}...",
                mentions=[f"@{bot_name}"]
            )
            
            # Log as a handoff (bot-to-bot transfer)
            self.work_log_manager.log(
                level=LogLevel.HANDOFF,
                category="bot_invocation",
                message=f"Delegating task to @{bot_name}",
                details={
                    "target_bot": bot_name,
                    "task": task[:500],
                    "context": context[:500] if context else None,
                },
                triggered_by="nanobot"
            )
        except Exception as e:
            logger.warning(f"Failed to log invocation request: {e}")
    
    def _log_invocation_response(
        self,
        bot_name: str,
        task: str,
        response: str,
    ) -> None:
        """Log a bot's response to an invocation."""
        if not self.work_log_manager:
            return
        
        try:
            # Log the bot's response
            self.work_log_manager.log_bot_message(
                bot_name=bot_name,
                message=f"Response to task: {task[:100]}...\n\n{response[:1000]}...",
                mentions=[f"@{bot_name}"]
            )
            
            # Log completion
            self.work_log_manager.log(
                level=LogLevel.INFO,
                category="bot_invocation",
                message=f"@{bot_name} completed the task",
                details={
                    "target_bot": bot_name,
                    "task": task[:500],
                    "response_length": len(response),
                },
                triggered_by=f"@{bot_name}"
            )
        except Exception as e:
            logger.warning(f"Failed to log invocation response: {e}")
    
    def _log_invocation_error(
        self,
        bot_name: str,
        task: str,
        error: str,
    ) -> None:
        """Log an error during bot invocation."""
        if not self.work_log_manager:
            return
        
        try:
            self.work_log_manager.log(
                level=LogLevel.ERROR,
                category="bot_invocation",
                message=f"@{bot_name} invocation failed: {error}",
                details={
                    "target_bot": bot_name,
                    "task": task[:500],
                    "error": error,
                },
                triggered_by="nanobot"
            )
        except Exception as e:
            logger.warning(f"Failed to log invocation error: {e}")
