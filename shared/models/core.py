"""
Core system Pydantic models for type safety.
Replaces all Dict[str, Any] usage in core modules.
"""

from datetime import datetime
from typing import Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from shared.types.json import JSONValue


class HealthStatus(BaseModel):
    """System health monitoring data."""
    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Overall health status")
    healing_enabled: bool = Field(..., description="Whether self-healing is enabled")
    patterns_loaded: int = Field(..., description="Number of patterns loaded")
    telemetry_active: bool = Field(..., description="Whether telemetry is active")
    learning_loop_active: bool = Field(..., description="Whether learning loop is active")
    timestamp: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ErrorDetectionResult(BaseModel):
    """Result of error detection and fixing workflow."""
    model_config = ConfigDict(extra="forbid")

    errors_found: int = Field(0, description="Number of errors found")
    fixes_applied: int = Field(0, description="Number of fixes applied")
    success: bool = Field(True, description="Whether operation succeeded")
    details: List[str] = Field(default_factory=list)
    findings: List[JSONValue] = Field(default_factory=list)  # Structured Finding or JSONValue
    patches: List[JSONValue] = Field(default_factory=list)  # Structured Patch or JSONValue


class TelemetryEvent(BaseModel):
    """Core telemetry event structure."""
    model_config = ConfigDict(extra="forbid")

    event: str = Field(..., description="Event name")
    data: dict[str, JSONValue] = Field(default_factory=dict, description="Event data")
    level: str = Field("info", description="Event level")
    timestamp: datetime = Field(default_factory=datetime.now)
    source: Optional[str] = Field(None, description="Event source")


class TelemetryMetrics(BaseModel):
    """Telemetry metrics summary."""
    model_config = ConfigDict(extra="forbid")

    total_events: int = Field(0)
    events_by_level: dict[str, int] = Field(default_factory=dict)
    events_by_type: dict[str, int] = Field(default_factory=dict)
    error_rate: float = Field(0.0)
    warning_rate: float = Field(0.0)
    recent_errors: List[TelemetryEvent] = Field(default_factory=list)
    recent_warnings: List[TelemetryEvent] = Field(default_factory=list)


class LearningMetrics(BaseModel):
    """Learning system metrics."""
    model_config = ConfigDict(extra="forbid")

    patterns_learned: int = Field(0)
    successful_applications: int = Field(0)
    failed_applications: int = Field(0)
    learning_rate: float = Field(0.0)
    adaptation_score: float = Field(0.0)
    recent_learnings: List[str] = Field(default_factory=list)
    active_experiments: int = Field(0)


class EditOperation(BaseModel):
    """Unified edit operation details."""
    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(..., description="Target file path")
    old_content: str = Field(..., description="Content to replace")
    new_content: str = Field(..., description="Replacement content")
    line_start: Optional[int] = Field(None, description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    operation_type: str = Field("replace", description="Type of edit operation")
    validation_status: Optional[str] = Field(None)


class EditResult(BaseModel):
    """Result of an edit operation."""
    model_config = ConfigDict(extra="forbid")

    success: bool = Field(...)
    file_path: str = Field(...)
    changes_made: int = Field(0)
    error: Optional[str] = Field(None)
    backup_path: Optional[str] = Field(None)
    validation_passed: bool = Field(True)


class PatternContext(BaseModel):
    """Context for pattern matching and application."""
    model_config = ConfigDict(extra="forbid")

    file_path: Optional[str] = Field(None)
    error_type: Optional[str] = Field(None)
    error_message: Optional[str] = Field(None)
    line_number: Optional[int] = Field(None)
    code_context: Optional[str] = Field(None)
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
    most_used_patterns: List[str] = Field(default_factory=list)
    recently_added: List[str] = Field(default_factory=list)


class ToolCall(BaseModel):
    """Tool invocation details."""
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(...)
    parameters: dict[str, JSONValue] = Field(default_factory=dict)
    result: Optional[JSONValue] = Field(None)
    success: bool = Field(True)
    error: Optional[str] = Field(None)
    duration_ms: Optional[int] = Field(None)


class HealingAttempt(BaseModel):
    """Self-healing attempt record."""
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime = Field(default_factory=datetime.now)
    attempt_id: str = Field(...)
    error_type: str = Field(...)
    fix_applied: bool = Field(False)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    initial_error: Optional[str] = Field(None)
    final_state: Optional[str] = Field(None)
    success: bool = Field(False)
    reason: Optional[str] = Field(None)


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