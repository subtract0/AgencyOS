"""
Memory-related Pydantic models for Agency OS.
Replaces Dict[str, Any] with concrete typed models.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.type_definitions.json_value import JSONValue


class MemoryPriority(str, Enum):
    """Priority levels for memory records."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Structured metadata for memory records."""
    agent_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    tool_name: str | None = None
    error_type: str | None = None
    success_rate: float | None = None
    execution_time_ms: int | None = None
    additional: dict[str, JSONValue] = Field(default_factory=dict)

    @field_validator("success_rate")
    def validate_success_rate(cls, v: float | None) -> float | None:
        if v is not None and not (0 <= v <= 1):
            raise ValueError("success_rate must be between 0 and 1")
        return v


class MemoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Core memory record model replacing Dict[str, Any]."""
    key: str = Field(..., description="Unique identifier for the memory")
    content: JSONValue = Field(
        ..., description="The actual content to store as JSON-compatible value"
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the memory was created"
    )
    priority: MemoryPriority = Field(default=MemoryPriority.MEDIUM, description="Priority level")
    metadata: MemoryMetadata = Field(
        default_factory=MemoryMetadata, description="Structured metadata"
    )
    ttl_seconds: int | None = Field(None, description="Time to live in seconds")
    embedding: list[float] | None = Field(
        None, description="Vector embedding for semantic search"
    )

    @field_validator("content", mode="before")
    def validate_json_compatible(cls, v: JSONValue) -> JSONValue:
        """Ensure content is JSON-compatible (strict validation).

        Validates against all non-JSON types: sets, bytes, custom classes,
        functions, lambdas, circular references, etc.
        """
        import json
        try:
            # Comprehensive JSON compatibility test
            json.dumps(v)
            return v
        except (TypeError, ValueError, OverflowError) as e:
            raise TypeError(
                f"Content must be JSON-compatible. "
                f"Invalid type: {type(v).__name__}. Error: {e}"
            )

    @field_validator("tags")
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Ensure tags are unique and non-empty while preserving order."""
        seen = set()
        result = []
        for tag in v:
            if tag and tag.strip() and tag not in seen:
                seen.add(tag)
                result.append(tag)
        return result

    @field_validator("ttl_seconds")
    def validate_ttl(cls, v: int | None) -> int | None:
        """Ensure TTL is positive if set."""
        if v is not None and v <= 0:
            raise ValueError("ttl_seconds must be positive")
        return v

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(mode="json")

    def is_expired(self) -> bool:
        """Check if the memory has expired based on TTL."""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds


class MemorySearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Result from memory search operations."""
    records: list[MemoryRecord] = Field(default_factory=list)
    total_count: int = Field(0, description="Total matching records")
    search_query: dict[str, JSONValue] = Field(default_factory=dict)
    execution_time_ms: float = Field(0.0)
    relevance_scores: dict[str, float] | None = None

    def get_by_key(self, key: str) -> MemoryRecord | None:
        """Get a specific record by key."""
        for record in self.records:
            if record.key == key:
                return record
        return None

    def filter_by_priority(self, min_priority: MemoryPriority) -> list[MemoryRecord]:
        """Filter records by minimum priority."""
        priority_order = {
            MemoryPriority.LOW: 0,
            MemoryPriority.MEDIUM: 1,
            MemoryPriority.HIGH: 2,
            MemoryPriority.CRITICAL: 3,
        }
        min_level = priority_order[min_priority]
        return [r for r in self.records if priority_order[r.priority] >= min_level]
