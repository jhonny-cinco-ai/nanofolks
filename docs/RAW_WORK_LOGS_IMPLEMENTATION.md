# Raw Work Logs Implementation

**Document Version:** 1.0  
**Last Updated:** February 12, 2026  
**Status:** Draft - Ready for Review  
**Author:** AI Implementation Team  

## Executive Summary

Based on [VoxYZ research](https://www.voxyz.space/insights/agent-work-logs-beat-polish-trust), this document outlines the implementation of **Raw Work Logs** for nanobot - a transparency feature that shows users the agent's real-time thinking, decision points, corrections, and uncertainty rather than polished final outputs.

**Core Principle:** Users trust AI agents more when they see messy, real-time work logs instead of clean summaries. Raw transparency beats perfection for building confidence.

**Expected Benefits:**
- Increased user trust through verifiable reasoning
- Easier debugging of agent behavior
- Faster identification of errors before they compound
- Reduced "learned helplessness" - users understand *why* decisions were made

---

## Problem Statement

### Current State
- nanobot presents clean, polished outputs
- Users cannot verify reasoning chains
- Errors hidden until they compound
- Smart routing and memory decisions are opaque
- Security scan results shown, but agent reasoning hidden

### User Pain Points
1. **Black Box Effect:** "How did the agent decide to use that skill?"
2. **Hidden Errors:** Mistakes only visible in final output
3. **Overconfidence:** Agent appears certain when it's not
4. **No Learning:** Users can't spot-check reasoning

### Desired State
- Agent shows decision points and reasoning
- Uncertainty exposed with confidence scores
- Corrections and revisions visible
- Process transparency for high-stakes decisions

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Add work logging infrastructure

#### 1.1 WorkLog Data Model
```python
# nanobot/agent/work_log.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from enum import Enum

class LogLevel(Enum):
    INFO = "info"      # Normal operation
    THINKING = "thinking"  # Reasoning steps
    DECISION = "decision"  # Choice made
    CORRECTION = "correction"  # Mistake fixed
    UNCERTAINTY = "uncertainty"  # Low confidence
    WARNING = "warning"  # Issue encountered
    ERROR = "error"      # Failure

@dataclass
class WorkLogEntry:
    timestamp: datetime
    level: LogLevel
    step: int           # Sequential step number
    category: str       # "memory", "tool", "routing", "security", etc.
    message: str        # Human-readable description
    details: dict = field(default_factory=dict)  # Structured data
    confidence: Optional[float] = None  # 0.0-1.0 for uncertainty
    duration_ms: Optional[int] = None  # How long this step took
    
    # Tool execution fields (for agent-to-agent handoffs)
    tool_name: Optional[str] = None          # e.g., "scan_skill"
    tool_input: Optional[dict] = None        # Structured input parameters
    tool_output: Optional[Any] = None        # Structured result (JSON-serializable)
    tool_status: Optional[str] = None        # "success", "error", "timeout"
    tool_error: Optional[str] = None         # Error message if failed
    
    def is_tool_entry(self) -> bool:
        """Check if this entry represents a tool execution."""
        return self.tool_name is not None
    
    def to_artifact(self) -> dict:
        """Convert to structured artifact for agent consumption."""
        return {
            "step": self.step,
            "category": self.category,
            "tool": self.tool_name,
            "input": self.tool_input,
            "output": self.tool_output,
            "status": self.tool_status,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass  
class WorkLog:
    session_id: str
    query: str          # Original user query
    start_time: datetime
    end_time: Optional[datetime] = None
    entries: list[WorkLogEntry] = field(default_factory=list)
    final_output: Optional[str] = None
    
    def add_entry(self, level: LogLevel, category: str, message: str, 
                  details: dict = None, confidence: float = None):
        """Add a work log entry."""
        entry = WorkLogEntry(
            timestamp=datetime.now(),
            level=level,
            step=len(self.entries) + 1,
            category=category,
            message=message,
            details=details or {},
            confidence=confidence
        )
        self.entries.append(entry)
        return entry
```

#### 1.2 WorkLogManager
```python
# nanobot/agent/work_log_manager.py

class WorkLogManager:
    """Manages work logs for agent sessions."""
    
    def __init__(self, enabled: bool = True, storage: str = "sqlite"):
        self.enabled = enabled
        self.storage = storage  # "sqlite", "memory", "file"
        self.current_log: Optional[WorkLog] = None
        
    def start_session(self, session_id: str, query: str) -> WorkLog:
        """Start a new work log session."""
        self.current_log = WorkLog(
            session_id=session_id,
            query=query,
            start_time=datetime.now()
        )
        return self.current_log
    
    def log(self, level: LogLevel, category: str, message: str, 
            details: dict = None, confidence: float = None):
        """Add entry to current log."""
        if not self.enabled or not self.current_log:
            return
        self.current_log.add_entry(level, category, message, details, confidence)
    
    def end_session(self, final_output: str):
        """End current session and save log."""
        if self.current_log:
            self.current_log.end_time = datetime.now()
            self.current_log.final_output = final_output
            self._save_log(self.current_log)
    
    def get_formatted_log(self, mode: str = "summary") -> str:
        """Get formatted log for display.
        
        Modes:
        - "summary": Just high-level steps
        - "detailed": All entries with details
        - "debug": Full technical details
        """
        if not self.current_log:
            return "No work log available"
        
        if mode == "summary":
            return self._format_summary()
        elif mode == "detailed":
            return self._format_detailed()
        elif mode == "debug":
            return self._format_debug()
        else:
            return self._format_summary()
```

#### 1.3 Integration Points
- Hook into `AgentLoop` - log at key decision points
- Hook into `ContextBuilder` - log memory assembly
- Hook into `MemoryRetrieval` - log search decisions
- Hook into tool execution - log tool selection
- Hook into `SkillsLoader` - log skill verification

#### 1.4 Configuration
```json
{
  "work_logs": {
    "enabled": true,
    "storage": "sqlite",  # "sqlite", "memory", "file", "none"
    "retention_days": 30,
    "log_levels": ["info", "thinking", "decision", "correction", "uncertainty", "warning", "error"],
    "categories": ["memory", "tool", "routing", "security", "skill", "context", "general"],
    "show_in_response": false,  # Include in normal responses
    "progressive_disclosure": true,  # Allow user to expand
    "default_mode": "summary",  # "summary", "detailed", "debug"
    "confidence_threshold": 0.7  # Flag decisions below this
  }
}
```

---

### Phase 2: Core Logging (Week 2-3)
**Goal:** Add logging to all major decision points

#### 2.1 Agent Loop Logging
```python
# In nanobot/agent/loop.py

class AgentLoop:
    def __init__(self, ...):
        self.work_log = WorkLogManager(enabled=config.work_logs.enabled)
    
    async def _process_chat_message(self, message: str, ...):
        # Start work log session
        self.work_log.start_session(session_id, message)
        
        try:
            # Log message received
            self.work_log.log(
                level=LogLevel.INFO,
                category="general",
                message=f"Processing user message: {message[:100]}..."
            )
            
            # Log memory retrieval
            self.work_log.log(
                level=LogLevel.THINKING,
                category="memory",
                message="Retrieving relevant context from memory",
                details={"query": message, "limit": 10}
            )
            
            # Build context with detailed logging
            context = self._build_context_with_logging(message)
            
            # Log routing decision
            self.work_log.log(
                level=LogLevel.DECISION,
                category="routing",
                message=f"Classified as {tier} tier",
                details={
                    "tier": tier,
                    "model": model,
                    "confidence": confidence,
                    "alternatives": alternatives
                },
                confidence=confidence
            )
            
            # Execute with logging
            result = await self._execute_with_logging(context)
            
            # Log completion
            self.work_log.end_session(result)
            
            # Return based on mode
            if self.config.work_logs.show_in_response:
                return self._format_response_with_log(result)
            else:
                return result
                
        except Exception as e:
            self.work_log.log(
                level=LogLevel.ERROR,
                category="general",
                message=f"Error processing message: {str(e)}"
            )
            self.work_log.end_session(f"Error: {str(e)}")
            raise
```

#### 2.2 Context Builder Logging
```python
# In nanobot/agent/context.py

def _build_context_with_logging(self, query: str) -> str:
    """Build context with work logging."""
    
    # Log identity loading
    self.work_log.log(
        level=LogLevel.INFO,
        category="context",
        message="Loading agent identity"
    )
    
    # Log memory context retrieval
    self.work_log.log(
        level=LogLevel.THINKING,
        category="memory",
        message="Querying memory for relevant context",
        details={"query_embedding": "BAAI/bge-small-en-v1.5"}
    )
    
    memory = self.memory.get_memory_context()
    
    if memory:
        self.work_log.log(
            level=LogLevel.INFO,
            category="memory",
            message=f"Retrieved {len(memory)} characters of memory context"
        )
    else:
        self.work_log.log(
            level=LogLevel.WARNING,
            category="memory",
            message="No relevant memory context found"
        )
    
    # Log skills loading
    self.work_log.log(
        level=LogLevel.THINKING,
        category="skill",
        message="Loading available skills",
        details={"skill_count": len(skills)}
    )
    
    for skill in skills:
        self.work_log.log(
            level=LogLevel.INFO,
            category="skill",
            message=f"Skill loaded: {skill['name']} ({skill.get('verified', 'unknown')})"
        )
    
    return context
```

#### 2.3 Smart Routing Logging
```python
# In nanobot/agent/stages/routing_stage.py

async def execute(self, context: Context) -> Context:
    """Execute routing with work logging."""
    
    # Log classification start
    self.work_log.log(
        level=LogLevel.THINKING,
        category="routing",
        message="Starting message classification"
    )
    
    # Get classification
    result = await self.classifier.classify(context.message)
    
    # Log decision
    self.work_log.log(
        level=LogLevel.DECISION,
        category="routing",
        message=f"Classified as {result.tier} tier ({result.model})",
        details={
            "tier": result.tier,
            "model": result.model,
            "confidence": result.confidence,
            "patterns_matched": result.patterns,
            "alternatives": result.alternatives
        },
        confidence=result.confidence
    )
    
    # Log if low confidence
    if result.confidence < self.config.work_logs.confidence_threshold:
        self.work_log.log(
            level=LogLevel.UNCERTAINTY,
            category="routing",
            message=f"Low confidence ({result.confidence:.0%}) - consider manual review",
            confidence=result.confidence
        )
    
    return context.with_routing(result)
```

#### 2.4 Tool Execution Logging with Artifacts
```python
# In nanobot/agent/tools/base.py or tool implementations

async def execute_with_logging(self, *args, **kwargs):
    """
    Execute tool with comprehensive logging.
    
    Captures both human-readable descriptions and structured artifacts
    for agent-to-agent handoffs.
    """
    
    start_time = time.time()
    
    # Create tool execution entry with structured input
    entry = self.work_log.add_entry(
        level=LogLevel.DECISION,
        category="tool",
        message=f"Executing {self.name}",
        tool_name=self.name,
        tool_input={
            "args": args,
            "kwargs": {k: str(v)[:500] for k, v in kwargs.items()},  # Truncate large values
            "timestamp": datetime.now().isoformat()
        }
    )
    
    try:
        result = await self._execute(*args, **kwargs)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Serialize result for structured output
        tool_output = self._serialize_for_artifact(result)
        
        # Update entry with structured output
        entry.tool_output = tool_output
        entry.tool_status = "success"
        entry.duration_ms = duration_ms
        
        # Human-readable summary
        entry.message = f"✓ {self.name} completed in {duration_ms}ms"
        entry.details = {
            "result_type": type(result).__name__,
            "result_summary": str(result)[:200],
            "duration_ms": duration_ms,
            "output_size_bytes": len(json.dumps(tool_output))
        }
        
        return result
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Update entry with error information
        entry.tool_status = "error"
        entry.tool_error = str(e)
        entry.duration_ms = duration_ms
        entry.level = LogLevel.ERROR
        entry.message = f"✗ {self.name} failed: {str(e)[:200]}"
        entry.details = {
            "error_type": type(e).__name__,
            "error_message": str(e)[:500],
            "duration_ms": duration_ms
        }
        
        raise

    def _serialize_for_artifact(self, result: Any) -> dict:
        """Convert tool result to structured artifact format."""
        if isinstance(result, (dict, list)):
            return result
        elif hasattr(result, 'to_dict'):
            return result.to_dict()
        elif hasattr(result, '__dict__'):
            return {k: v for k, v in result.__dict__.items() if not k.startswith('_')}
        else:
            return {"_value": str(result), "_type": type(result).__name__}
```

#### 2.5 Example: Security Tool Logging

Real-world example of `scan_skill` tool logging:

**Human-Readable Output:**
```
⚠️ Security scan flagged 1 issue (risk: 15/100)

Findings:
- [HIGH] persistence_mechanism: Uses cron scheduling
  This may be a false positive for scheduled bookmark digests
```

**Structured Artifact (for next agent):**
```json
{
  "tool": "scan_skill",
  "input": {"skill_path": "./x-bookmarks", "strict": false},
  "output": {
    "skill_name": "x-bookmarks",
    "risk_score": 15,
    "passed": false,
    "status": "rejected",
    "findings": [
      {
        "severity": "high",
        "category": "persistence_mechanism",
        "confidence": 0.85,
        "line": 8,
        "code": "scheduled bookmark digests via cron",
        "remediation": "Verify this is legitimate scheduled task usage"
      }
    ],
    "critical_count": 0,
    "high_count": 1,
    "medium_count": 0,
    "low_count": 0
  },
  "status": "success",
  "duration_ms": 342,
  "next_actions": ["manual_review", "approve_if_trusted"]
}
```

**Next Agent Can:**
- See risk score: 15/100 (low-medium)
- Understand finding is cron-related
- Know manual approval is recommended
- Access full structured data without parsing text

#### 2.6 Tool Artifact Schema Standards

**Tool Input Schema (all tools):**
```python
{
  "args": [...],                 # Positional arguments (serialized)
  "kwargs": {...},              # Keyword arguments (truncated if large)
  "timestamp": "ISO8601",       # Execution start time
  "caller": "agent-id",         # Which agent/tool called this
  "context": {...}              # Execution context
}
```

**Tool Output Schema (all tools):**
```python
{
  "_raw": {...},                # Original result (if serializable)
  "_type": "class_name",        # Result type for deserialization
  "_summary": "...",            # Human-readable summary
  "status": "success|error",    # Execution status
  "error": "...",              # Error message (if failed)
  "metadata": {...}            # Tool-specific metadata
}
```

---

### Phase 2.5: Multi-Agent Artifact Handoffs (Optional Enhancement)
**Goal:** Enable work logs as structured artifacts for agent-to-agent communication

Based on [VoxYZ research on artifact handoffs](https://www.voxyz.space/insights/agents-need-artifact-handoffs-not-chat-reports):

#### Why Artifacts Beat Chat for Multi-Agent Workflows

**Problem with Chat Reports:**
```
Agent A: "I analyzed the data and found 3 issues..."
Agent B: Must parse natural language → Extract data → Act
```

**Solution: Structured Artifacts:**
```python
{
  "analysis_id": "uuid",
  "issues": [
    {"severity": "high", "category": "performance", "metric": 0.15},
    {"severity": "medium", "category": "security", "metric": 0.03}
  ],
  "next_actions": ["optimize_query", "add_index"]
}
```

#### WorkLog as Agent Artifact

```python
# nanobot/agent/work_log.py

@dataclass
class WorkLog:
    # ... existing fields ...
    
    # Artifact metadata for multi-agent handoffs
    artifact_schema: str = "work-log-v1"  # Version for compatibility
    producer_agent: str = "main"          # Agent that created this log
    consumer_agent: Optional[str] = None   # Agent that should consume it
    workflow_id: Optional[str] = None    # Parent workflow identifier
    
    def to_agent_artifact(self) -> dict:
        """
        Convert work log to structured artifact for next agent.
        
        Next agent can directly consume this without parsing text.
        """
        return {
            "schema": self.artifact_schema,
            "workflow_id": self.workflow_id,
            "query": self.query,
            "decisions": [
                {
                    "step": e.step,
                    "category": e.category,
                    "tool": e.tool_name,
                    "input": e.tool_input,
                    "output": e.tool_output,
                    "status": e.tool_status,
                    "confidence": e.confidence,
                    "duration_ms": e.duration_ms,
                    "error": e.tool_error
                }
                for e in self.entries
                if e.is_tool_entry()  # Only tool executions (structured data)
            ],
            "summary": {
                "total_steps": len(self.entries),
                "tool_calls": len([e for e in self.entries if e.is_tool_entry()]),
                "errors": len([e for e in self.entries if e.level == LogLevel.ERROR]),
                "total_duration_ms": sum(e.duration_ms or 0 for e in self.entries),
                "final_output": self.final_output[:500]
            },
            "recommendations": self._extract_next_actions()
        }
    
    def _extract_next_actions(self) -> list[str]:
        """Extract suggested next actions from work log."""
        actions = []
        
        # Look for explicit next_actions in tool outputs
        for entry in self.entries:
            if entry.tool_output and isinstance(entry.tool_output, dict):
                if "next_actions" in entry.tool_output:
                    actions.extend(entry.tool_output["next_actions"])
        
        # Infer from errors
        errors = [e for e in self.entries if e.level == LogLevel.ERROR]
        if errors:
            actions.append("review_errors")
        
        # Infer from low confidence
        low_conf = [e for e in self.entries 
                   if e.confidence and e.confidence < 0.7]
        if low_conf:
            actions.append("verify_low_confidence_decisions")
        
        return actions
```

#### Artifact Storage for Multi-Agent Workflows

```python
# nanobot/agent/artifact_store.py

class AgentArtifactStore:
    """Store and retrieve artifacts for agent-to-agent handoffs."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path / ".nanobot" / "artifacts"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_artifact(self, artifact: dict, producer: str, consumer: Optional[str] = None) -> str:
        """Save artifact and return artifact ID."""
        artifact_id = str(uuid.uuid4())
        artifact_path = self.storage_path / f"{artifact_id}.json"
        
        artifact["_meta"] = {
            "id": artifact_id,
            "producer": producer,
            "consumer": consumer,
            "created_at": datetime.now().isoformat(),
            "schema": artifact.get("schema", "unknown")
        }
        
        artifact_path.write_text(json.dumps(artifact, indent=2))
        return artifact_id
    
    def get_artifact(self, artifact_id: str) -> Optional[dict]:
        """Retrieve artifact by ID."""
        artifact_path = self.storage_path / f"{artifact_id}.json"
        if artifact_path.exists():
            return json.loads(artifact_path.read_text())
        return None
    
    def list_artifacts_for_consumer(self, consumer: str) -> list[dict]:
        """List all artifacts waiting for a specific consumer agent."""
        artifacts = []
        for artifact_file in self.storage_path.glob("*.json"):
            data = json.loads(artifact_file.read_text())
            if data.get("_meta", {}).get("consumer") == consumer:
                artifacts.append(data)
        return sorted(artifacts, key=lambda x: x["_meta"]["created_at"])
```

#### Example: Multi-Agent Bookmark Analysis Workflow

```python
# Agent A: Fetch and analyze bookmarks
async def analyze_bookmarks():
    work_log = WorkLogManager().start_session("analyze_bookmarks", "Check my X bookmarks")
    
    # Step 1: Fetch bookmarks
    bookmarks = await exec_tool("bird", {"command": "bookmarks", "count": 50})
    work_log.add_entry(
        tool_name="bird",
        tool_input={"command": "bookmarks", "count": 50},
        tool_output={"count": len(bookmarks), "categories": categorize(bookmarks)},
        tool_status="success",
        duration_ms=1200
    )
    
    # Step 2: Categorize
    categories = categorize_bookmarks(bookmarks)
    work_log.add_entry(
        tool_name="categorize",
        tool_input={"items": len(bookmarks)},
        tool_output={
            "categories": categories,
            "ai_ml_count": categories.get("AI/ML", 0),
            "productivity_count": categories.get("Productivity", 0)
        },
        tool_status="success"
    )
    
    # Convert to artifact for Agent B
    artifact = work_log.to_agent_artifact()
    artifact["next_actions"] = ["summarize_top_categories", "suggest_actions"]
    
    # Save for Agent B
    artifact_id = artifact_store.save_artifact(
        artifact, 
        producer="bookmark_analyzer",
        consumer="action_suggester"
    )
    
    return f"Analysis complete. See artifact {artifact_id} for details."

# Agent B: Read artifact and suggest actions
async def suggest_actions(artifact_id: str):
    artifact = artifact_store.get_artifact(artifact_id)
    
    # Directly access structured data - no parsing!
    ai_ml_count = artifact["decisions"][1]["output"]["ai_ml_count"]
    
    if ai_ml_count > 5:
        return f"You have {ai_ml_count} AI bookmarks. Want me to create a summary report?"
```

**Benefits:**
- No natural language parsing between agents
- Clear data lineage and audit trail
- Structured error handling
- Next action recommendations
- Versioned schemas for compatibility

---

### Phase 3: CLI Integration (Week 3)
**Goal:** Add user-facing commands to view work logs

#### 3.1 New CLI Commands
```python
# In nanobot/cli/commands.py

@app.command("explain")
def explain_last_decision(
    session_id: Optional[str] = typer.Option(None, help="Session ID to explain"),
    mode: str = typer.Option("detailed", help="Explanation mode: summary, detailed, debug"),
):
    """
    Show how the agent made its last decision.
    
    Examples:
        nanobot explain                    # Explain last interaction
        nanobot explain --mode summary     # Brief explanation
        nanobot explain --mode debug       # Full technical details
    """
    from nanobot.agent.work_log_manager import WorkLogManager
    
    manager = WorkLogManager()
    
    if session_id:
        log = manager.get_log(session_id)
    else:
        log = manager.get_last_log()
    
    if not log:
        console.print("[yellow]No work log found. Interact with the agent first.[/yellow]")
        return
    
    console.print(manager.get_formatted_log(mode))


@app.command("how")
def how_did_you_decide(
    query: str = typer.Argument(..., help="What to explain (e.g., 'routing', 'memory search')"),
):
    """
    Ask how a specific decision was made.
    
    Examples:
        nanobot how "why did you choose Claude"
        nanobot how "what memories did you use"
    """
    # Search work logs for relevant entries
    # Return natural language explanation
    pass
```

#### 3.2 Agent Integration
Add to system prompt:
```markdown
## Work Log Transparency

When asked "how did you decide" or "why did you choose":
1. Reference the work log for that interaction
2. Explain the reasoning chain
3. Show confidence levels
4. Admit uncertainty when present

Example:
User: "Why did you use that skill?"
You: "I scanned 5 available skills. 'github-manager' matched your request 
('push to repo') with 94% confidence based on tool patterns. 
Alternative 'git-cli' was 67% confident."
```

---

### Phase 4: Progressive UI (Week 4)
**Goal:** Implement progressive disclosure UI

#### 4.1 Response Formatting
```python
def format_response_with_log(self, result: str, log: WorkLog) -> str:
    """Format response with optional work log."""
    
    if self.config.work_logs.show_in_response:
        # Full log included
        return f"""
{result}

---

<details>
<summary>🔍 How I decided this</summary>

{log.get_formatted_log("detailed")}
</details>
"""
    else:
        # Just the result, with a hint
        return f"""{result}

💡 Tip: Use `nanobot explain` to see how I made this decision."""
```

#### 4.2 Interactive Mode
In chat interface:
```
User: Check my bookmarks
Agent: [Processes...]

📚 I found 12 bookmarks. Here's a summary:
- 5 about AI/ML
- 3 about productivity
- 4 uncategorized

[See how I decided →] [Ask follow-up →]

User clicks "See how I decided"
Agent shows work log with:
✓ Loaded x-bookmarks skill (verified)
✓ Executed bird CLI to fetch bookmarks  
⚠ 4 bookmarks without clear categories
✓ Categorized 8/12 with 91% confidence
```

---

## Technical Specifications

### Storage Options

#### Option A: SQLite (Recommended)
```sql
CREATE TABLE work_logs (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    query TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    final_output TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE work_log_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_log_id TEXT,
    step INTEGER,
    timestamp TIMESTAMP,
    level TEXT,
    category TEXT,
    message TEXT,
    details_json TEXT,
    confidence REAL,
    duration_ms INTEGER,
    FOREIGN KEY (work_log_id) REFERENCES work_logs(id)
);
```

**Pros:** Persistent, queryable, scalable  
**Cons:** Slight performance overhead

#### Option B: In-Memory
```python
work_logs: dict[str, WorkLog] = {}  # session_id -> WorkLog
```

**Pros:** Fast, no I/O  
**Cons:** Lost on restart, memory usage

#### Option C: JSON Files
```python
# workspace/.nanobot/work-logs/{session_id}.json
```

**Pros:** Human-readable, easy to inspect  
**Cons:** Slower queries, file system overhead

**Recommendation:** SQLite for production, in-memory for testing.

### Performance Considerations

1. **Async Logging:** Don't block agent loop
   ```python
   asyncio.create_task(self._async_log(...))
   ```

2. **Sampling:** Only log 10% of "info" level in production
   ```python
   if level == LogLevel.INFO and random.random() > 0.1:
       return  # Skip
   ```

3. **Truncation:** Limit large fields
   ```python
   details["result"] = str(result)[:500]  # Truncate
   ```

4. **Retention:** Auto-delete old logs
   ```python
   DELETE FROM work_logs WHERE created_at < date('now', '-30 days');
   ```

### Privacy & Security

1. **PII Masking:** Automatically redact sensitive data
   ```python
   message = mask_secrets(message)  # Use existing sanitizer
   ```

2. **Access Control:** Logs only accessible to workspace owner
   ```python
   # Check user_id matches session owner
   ```

3. **Opt-out:** Users can disable logging entirely
   ```json
   {"work_logs": {"enabled": false}}
   ```

---

## Testing Strategy

### Unit Tests
```python
def test_work_log_creation():
    log = WorkLog(session_id="test", query="hello")
    log.add_entry(LogLevel.INFO, "test", "message")
    assert len(log.entries) == 1

def test_low_confidence_flagging():
    log = WorkLog(session_id="test", query="hello")
    log.add_entry(LogLevel.DECISION, "routing", "test", confidence=0.5)
    # Should be flagged as uncertainty
    assert log.entries[0].level == LogLevel.UNCERTAINTY

def test_formatted_output():
    log = WorkLog(session_id="test", query="hello")
    log.add_entry(LogLevel.INFO, "test", "step 1")
    log.add_entry(LogLevel.DECISION, "test", "step 2")
    
    formatted = log.get_formatted_log("summary")
    assert "step 1" in formatted
    assert "step 2" in formatted
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_agent_loop_logging():
    agent = AgentLoop(..., work_logs_enabled=True)
    
    result = await agent.process("test message")
    
    # Verify log was created
    log = agent.work_log.current_log
    assert log is not None
    assert len(log.entries) > 0
    
    # Verify specific entries
    routing_entries = [e for e in log.entries if e.category == "routing"]
    assert len(routing_entries) > 0
```

---

## Rollout Plan

### Week 1: Infrastructure
- [ ] Create `WorkLog` and `WorkLogEntry` data classes
- [ ] Implement `WorkLogManager` with storage backends
- [ ] Add configuration to `config/schema.py`
- [ ] Unit tests for work log classes

### Week 2: Core Integration
- [ ] Hook into `AgentLoop` - start/end sessions
- [ ] Add logging to `ContextBuilder`
- [ ] Add logging to `Smart Routing`
- [ ] Add logging to tool execution
- [ ] Integration tests

### Week 3: CLI & API
- [ ] Add `explain` CLI command
- [ ] Add `how` CLI command
- [ ] Add work log tools to agent (meta-cognition)
- [ ] Documentation updates

### Week 4: UI & Polish
- [ ] Implement progressive disclosure UI
- [ ] Add `--verbose` flag to agent
- [ ] Performance optimization (async, sampling)
- [ ] Privacy review (PII masking)
- [ ] Final testing & release

---

## Success Metrics

1. **Adoption:** % of users who run `nanobot explain` at least once
2. **Trust:** User survey - "I understand how nanobot makes decisions" (1-5)
3. **Debugging:** Average time to diagnose agent issues (before vs after)
4. **Error Detection:** # of errors caught by users reviewing work logs

Target: 80% of users report increased understanding after viewing work logs.

---

## Open Questions

1. Should work logs be shared between users (anonymized) for research?
2. How long should logs be retained by default?
3. Should we allow exporting work logs for debugging?
4. Should there be a "silent mode" for API calls that skips logging entirely?

---

## Related Documentation

- [MEMORY_IMPLEMENTATION_STATUS.md](MEMORY_IMPLEMENTATION_STATUS.md) - Memory system architecture
- [Smart Routing Documentation](ROUTING.md) - Routing decision logic
- [Security Scanner](docs/SECURITY.md) - Skill verification (future doc)
- [VoxYZ Research](https://www.voxyz.space/insights/agent-work-logs-beat-polish-trust) - Original article

---

**Next Steps:**
1. Review this document with the team
2. Create GitHub issues for each phase
3. Assign developers to Week 1 tasks
4. Schedule weekly check-ins during implementation
