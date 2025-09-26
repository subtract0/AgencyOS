"""
Learning and pattern analysis Pydantic models for Agency OS.
Replaces Dict[str, Any] in learning consolidation and pattern analysis.
"""

from datetime import datetime
from typing import Dict, List, Optional
from shared.type_definitions.json import JSONValue
from pydantic import BaseModel, Field, field_validator, ConfigDict


class LearningMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Individual learning metric."""
    name: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ContentTypeBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Breakdown of content types in memories."""
    text: int = 0
    error: int = 0
    success: int = 0
    command: int = 0
    url: int = 0
    long_text: int = 0
    code: int = 0
    empty: int = 0
    other: int = 0

    def total(self) -> int:
        """Calculate total content items."""
        return sum(self.model_dump().values())

    def get_dominant_type(self) -> str:
        """Get the most common content type."""
        counts = self.model_dump()
        return max(counts, key=counts.get) if counts else "empty"


class TimeDistribution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Time-based distribution patterns."""
    hourly: Dict[int, int] = Field(default_factory=dict)
    daily: Dict[str, int] = Field(default_factory=dict)
    peak_hour: Optional[int] = None
    peak_day: Optional[str] = None

    @field_validator('hourly')
    def validate_hourly(cls, v: Dict[int, int]) -> Dict[int, int]:
        """Ensure hour keys are valid (0-23)."""
        for hour in v.keys():
            if not 0 <= hour <= 23:
                raise ValueError(f'Invalid hour: {hour}')
        return v


class PatternAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Pattern analysis results."""
    content_types: ContentTypeBreakdown = Field(default_factory=ContentTypeBreakdown)
    time_distribution: TimeDistribution = Field(default_factory=TimeDistribution)
    common_sequences: List[List[str]] = Field(default_factory=list)
    anomalies_detected: int = 0
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)

    def has_patterns(self) -> bool:
        """Check if any patterns were detected."""
        return (
            self.content_types.total() > 0 or
            bool(self.time_distribution.hourly) or
            bool(self.common_sequences)
        )


class LearningInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Individual learning insight."""
    category: str
    description: str
    importance: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    supporting_data: Dict[str, JSONValue] = Field(default_factory=dict)


class LearningConsolidation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """
    Consolidated learning results.
    Replaces Dict[str, Any] returned from consolidate_learnings().
    """
    summary: str
    total_memories: int = Field(0, ge=0)
    unique_tags: int = Field(0, ge=0)
    avg_tags_per_memory: float = Field(0.0, ge=0.0)
    tag_frequencies: Dict[str, int] = Field(default_factory=dict)
    top_tags: List[Dict[str, JSONValue]] = Field(default_factory=list)
    patterns: PatternAnalysis = Field(default_factory=PatternAnalysis)
    insights: List[LearningInsight] = Field(default_factory=list)
    metrics: Dict[str, LearningMetric] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = None
    agent_id: Optional[str] = None

    @field_validator('tag_frequencies')
    def validate_tag_frequencies(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Ensure all frequencies are non-negative."""
        for tag, freq in v.items():
            if freq < 0:
                raise ValueError(f'Negative frequency for tag {tag}')
        return v

    def get_top_tags(self, n: int = 10) -> List[tuple[str, int]]:
        """Get the N most frequent tags."""
        return sorted(
            self.tag_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(mode='json')

    def has_insights(self) -> bool:
        """Check if any insights were generated."""
        return len(self.insights) > 0

    def get_critical_insights(self) -> List[LearningInsight]:
        """Get only critical importance insights."""
        return [i for i in self.insights if i.importance == "critical"]