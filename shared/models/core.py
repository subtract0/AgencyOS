"""
Core system Pydantic models for type safety.
Replaces all Dict[str, Any] usage in core modules.
"""

from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from shared.type_definitions.json_value import JSONValue


class HealthStatus(BaseModel):
    """System health monitoring data."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Overall health status")
    healing_enabled: bool = Field(..., description="Whether self-healing is enabled")
    patterns_loaded: int = Field(..., description="Number of patterns loaded")
    telemetry_active: bool = Field(..., description="Whether telemetry is active")
    learning_loop_active: bool = Field(..., description="Whether learning loop is active")
    timestamp: datetime = Field(default_factory=datetime.now)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ErrorDetectionResult(BaseModel):
    """Result of error detection and fixing workflow."""

    model_config = ConfigDict(extra="forbid")

    errors_found: int = Field(0, description="Number of errors found")
    fixes_applied: int = Field(0, description="Number of fixes applied")
    success: bool = Field(True, description="Whether operation succeeded")
    details: list[str] = Field(default_factory=list)
    findings: list[JSONValue] = Field(default_factory=list)  # Structured Finding or JSONValue
    patches: list[JSONValue] = Field(default_factory=list)  # Structured Patch or JSONValue


class TelemetryEvent(BaseModel):
    """Core telemetry event structure."""

    model_config = ConfigDict(extra="forbid")

    event: str = Field(..., description="Event name")
    data: dict[str, JSONValue] = Field(default_factory=dict, description="Event data")
    level: str = Field("info", description="Event level")
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str | None = Field(None, description="Event source")


class TelemetryMetrics(BaseModel):
    """Telemetry metrics summary."""

    model_config = ConfigDict(extra="forbid")

    total_events: int = Field(0)
    events_by_level: dict[str, int] = Field(default_factory=dict)
    events_by_type: dict[str, int] = Field(default_factory=dict)
    error_rate: float = Field(0.0)
    warning_rate: float = Field(0.0)
    recent_errors: list[TelemetryEvent] = Field(default_factory=list)
    recent_warnings: list[TelemetryEvent] = Field(default_factory=list)


class LearningMetrics(BaseModel):
    """Learning system metrics."""

    model_config = ConfigDict(extra="forbid")

    patterns_learned: int = Field(0)
    successful_applications: int = Field(0)
    failed_applications: int = Field(0)
    learning_rate: float = Field(0.0)
    adaptation_score: float = Field(0.0)
    recent_learnings: list[str] = Field(default_factory=list)
    active_experiments: int = Field(0)


class EditOperation(BaseModel):
    """Unified edit operation details."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(..., description="Target file path")
    old_content: str = Field(..., description="Content to replace")
    new_content: str = Field(..., description="Replacement content")
    line_start: int | None = Field(None, description="Starting line number")
    line_end: int | None = Field(None, description="Ending line number")
    operation_type: str = Field("replace", description="Type of edit operation")
    validation_status: str | None = Field(None)


class EditResult(BaseModel):
    """Result of an edit operation."""

    model_config = ConfigDict(extra="forbid")

    success: bool = Field(...)
    file_path: str = Field(...)
    changes_made: int = Field(0)
    error: str | None = Field(None)
    backup_path: str | None = Field(None)
    validation_passed: bool = Field(True)


class PatternContext(BaseModel):
    """Context for pattern matching and application."""

    model_config = ConfigDict(extra="forbid")

    file_path: str | None = Field(None)
    error_type: str | None = Field(None)
    error_message: str | None = Field(None)
    line_number: int | None = Field(None)
    code_context: str | None = Field(None)
    metadata: dict[str, JSONValue] = Field(default_factory=dict)


class PatternStatistics(BaseModel):
    """Pattern usage statistics."""

    model_config = ConfigDict(extra="forbid")

    total_patterns: int = Field(0)
    active_patterns: int = Field(0)
    successful_applications: int = Field(0)
    failed_applications: int = Field(0)
    patterns_by_type: dict[str, int] = Field(default_factory=dict)
    success_rate: float = Field(0.0)
    most_used_patterns: list[str] = Field(default_factory=list)
    recently_added: list[str] = Field(default_factory=list)


class ToolCall(BaseModel):
    """Tool invocation details."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(...)
    parameters: dict[str, JSONValue] = Field(default_factory=dict)
    result: JSONValue | None = Field(None)
    success: bool = Field(True)
    error: str | None = Field(None)
    duration_ms: int | None = Field(None)


class HealingAttempt(BaseModel):
    """Self-healing attempt record."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(default_factory=datetime.now)
    attempt_id: str = Field(...)
    error_type: str = Field(...)
    fix_applied: bool = Field(False)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    initial_error: str | None = Field(None)
    final_state: str | None = Field(None)
    success: bool = Field(False)
    reason: str | None = Field(None)


class SystemConfiguration(BaseModel):
    """Core system configuration."""

    model_config = ConfigDict(extra="forbid")

    healing_enabled: bool = Field(True)
    telemetry_enabled: bool = Field(True)
    learning_enabled: bool = Field(True)
    pattern_persistence: bool = Field(False)
    max_healing_attempts: int = Field(3)
    telemetry_buffer_size: int = Field(1000)
    pattern_cache_size: int = Field(100)
    debug_mode: bool = Field(False)


# Hook system type models


class HookParameters(BaseModel):
    """Safe tool parameters for hook systems."""

    model_config = ConfigDict(extra="forbid")

    parameters: dict[str, JSONValue] = Field(default_factory=dict)
    sensitive_keys_redacted: list[str] = Field(default_factory=list)
    extraction_status: str = Field("success")


class AgentInfo(BaseModel):
    """Agent information for hook operations."""

    model_config = ConfigDict(extra="forbid")

    agent_type: str = Field(..., description="Type/class of the agent")
    agent_name: str | None = Field(None, description="Agent name if available")
    agent_id: str | None = Field(None, description="Unique agent identifier")


class ToolInfo(BaseModel):
    """Tool information for hook operations."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., description="Name of the tool")
    parameters: HookParameters = Field(default_factory=lambda: HookParameters())
    result_size: int = Field(0, description="Size of tool result in characters")


class SessionEvent(BaseModel):
    """Session lifecycle event data."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str = Field(..., description="ISO timestamp")
    agent_info: AgentInfo = Field(..., description="Agent involved in the event")
    context_id: str = Field("unknown", description="Context identifier")
    session_duration: str | None = Field(None, description="Duration string")
    output_summary: str | None = Field(None, description="Truncated output summary")


class HandoffEvent(BaseModel):
    """Agent handoff event data."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str = Field(..., description="ISO timestamp")
    target_agent: str = Field(..., description="Agent receiving handoff")
    source_agent: str = Field(..., description="Agent initiating handoff")


class ToolEvent(BaseModel):
    """Tool execution event data."""

    model_config = ConfigDict(extra="forbid")

    timestamp: str = Field(..., description="ISO timestamp")
    agent_info: AgentInfo = Field(..., description="Agent executing the tool")
    tool_info: ToolInfo = Field(..., description="Tool information")


class ToolResultEvent(ToolEvent):
    """Tool execution result event data."""

    result: str = Field(..., description="Truncated tool result")


class ToolErrorEvent(ToolEvent):
    """Tool execution error event data."""

    error: str = Field(..., description="Error message")


class CodeBundleInfo(BaseModel):
    """Code bundle attachment information."""

    model_config = ConfigDict(extra="forbid")

    bundle_path: str = Field(..., description="Path to the created bundle")
    session_id: str | None = Field(None, description="Session identifier")
    timestamp: str = Field(..., description="Creation timestamp")
    content_size: int = Field(0, description="Size of bundled content")


class FileSnapshot(BaseModel):
    """File snapshot information."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., description="Relative path from repo root")
    snapshot_path: str = Field(..., description="Path to snapshot file")
    size_bytes: int = Field(0, description="File size in bytes")


class SnapshotManifest(BaseModel):
    """Manifest for file snapshots."""

    model_config = ConfigDict(extra="forbid")

    files: list[FileSnapshot] = Field(default_factory=list)
    timestamp: str = Field(..., description="Snapshot creation time")
    base_path: str = Field(..., description="Base directory for snapshots")


# Hook system typed interfaces


@runtime_checkable
class ToolProtocol(Protocol):
    """Protocol for tool objects used in hook systems."""

    name: str
    parameters: dict[str, object] | None

    def run(self, *args, **kwargs) -> str:
        """Execute the tool and return result."""
        ...


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol for agent objects used in hook systems."""

    name: str | None


@runtime_checkable
class RunContextProtocol(Protocol):
    """Protocol for run context objects used in hook systems."""

    context: dict[str, object]
    id: str | None

    def get(self, key: str, default=None) -> JSONValue:
        """Get value from context."""
        ...

    def set(self, key: str, value: JSONValue) -> None:
        """Set value in context."""
        ...
