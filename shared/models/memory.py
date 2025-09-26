"""
Memory-related Pydantic models for Agency OS.
Replaces Dict[str, Any] with concrete typed models.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from shared.types.json import JSONValue
from pydantic import BaseModel, Field, field_validator, ConfigDict


class MemoryPriority(str, Enum):
    """Priority levels for memory records."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Structured metadata for memory records."""
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    tool_name: Optional[str] = None
    error_type: Optional[str] = None
    success_rate: Optional[float] = None
    execution_time_ms: Optional[int] = None
    additional: Dict[str, JSONValue] = Field(default_factory=dict)

    @field_validator('success_rate')
    def validate_success_rate(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0 <= v <= 1):
            raise ValueError('success_rate must be between 0 and 1')
        return v


class MemoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Core memory record model replacing Dict[str, Any]."""
    key: str = Field(..., description="Unique identifier for the memory")
    content: JSONValue = Field(..., description="The actual content to store as JSON-compatible value")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the memory was created")
    priority: MemoryPriority = Field(default=MemoryPriority.MEDIUM, description="Priority level")
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata, description="Structured metadata")
    ttl_seconds: Optional[int] = Field(None, description="Time to live in seconds")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding for semantic search")


    @field_validator('tags')
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Ensure tags are unique and non-empty while preserving order."""
        seen = set()
        result = []
        for tag in v:
            if tag and tag.strip() and tag not in seen:
                seen.add(tag)
                result.append(tag)
        return result

    @field_validator('ttl_seconds')
    def validate_ttl(cls, v: Optional[int]) -> Optional[int]:
        """Ensure TTL is positive if set."""
        if v is not None and v <= 0:
            raise ValueError('ttl_seconds must be positive')
        return v

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(mode='json')

    def is_expired(self) -> bool:
        """Check if the memory has expired based on TTL."""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds


class MemorySearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Result from memory search operations."""
    records: List[MemoryRecord] = Field(default_factory=list)
    total_count: int = Field(0, description="Total matching records")
    search_query: Dict[str, JSONValue] = Field(default_factory=dict)
    execution_time_ms: float = Field(0.0)
    relevance_scores: Optional[Dict[str, float]] = None

    def get_by_key(self, key: str) -> Optional[MemoryRecord]:
        """Get a specific record by key."""
        for record in self.records:
            if record.key == key:
                return record
        return None

    def filter_by_priority(self, min_priority: MemoryPriority) -> List[MemoryRecord]:
        """Filter records by minimum priority."""
        priority_order = {
            MemoryPriority.LOW: 0,
            MemoryPriority.MEDIUM: 1,
            MemoryPriority.HIGH: 2,
            MemoryPriority.CRITICAL: 3
        }
        min_level = priority_order[min_priority]
        return [
            r for r in self.records
            if priority_order[r.priority] >= min_level
        ]