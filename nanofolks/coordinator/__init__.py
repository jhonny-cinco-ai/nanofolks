"""Coordinator module for multi-agent orchestration.

Provides inter-bot communication, task delegation, and team coordination.
"""

from nanofolks.coordinator.models import (
    BotMessage,
    MessageType,
    Task,
    TaskStatus,
    TaskPriority,
    TaskDependency,
    ConversationContext,
    CoordinationEvent,
)
from nanofolks.coordinator.bus import InterBotBus
from nanofolks.coordinator.coordinator_bot import CoordinatorBot
from nanofolks.coordinator.store import CoordinatorStore
from nanofolks.coordinator.autonomous import AutonomousBotTeam, BotCollaborator
from nanofolks.coordinator.decisions import (
    BotPosition,
    Decision,
    Disagreement,
    DecisionMaker,
    DisputeResolver,
    VotingStrategy,
    DisagreementType,
)
from nanofolks.coordinator.audit import (
    AuditTrail,
    AuditEvent,
    AuditEventType,
    AuditEventSeverity,
    DecisionAuditRecord,
)
from nanofolks.coordinator.explanation import (
    ExplanationEngine,
    Explanation,
)
from nanofolks.coordinator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CallMetrics,
    CircuitBreakerOpen,
    RetryStrategy,
    LoadBalancer,
)

__all__ = [
    "BotMessage",
    "MessageType",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskDependency",
    "ConversationContext",
    "CoordinationEvent",
    "InterBotBus",
    "CoordinatorBot",
    "CoordinatorStore",
    "AutonomousBotTeam",
    "BotCollaborator",
    "BotPosition",
    "Decision",
    "Disagreement",
    "DecisionMaker",
    "DisputeResolver",
    "VotingStrategy",
    "DisagreementType",
    "AuditTrail",
    "AuditEvent",
    "AuditEventType",
    "AuditEventSeverity",
    "DecisionAuditRecord",
    "ExplanationEngine",
    "Explanation",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "CallMetrics",
    "CircuitBreakerOpen",
    "RetryStrategy",
    "LoadBalancer",
]
