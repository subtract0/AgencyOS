"""
Constitutional enforcement telemetry models.

Captures enforcement events for learning and pattern analysis.
Implements Article VII Phase 1: Constitutional Telemetry.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from shared.type_definitions.json import JSONValue


def _utc_now() -> datetime:
    """Helper for UTC timestamp generation."""
    return datetime.now(UTC)


class Article(str, Enum):
    """Constitutional articles."""

    ARTICLE_I = "I"
    ARTICLE_II = "II"
    ARTICLE_III = "III"
    ARTICLE_IV = "IV"
    ARTICLE_V = "V"
    ARTICLE_VII = "VII"  # For future meta-constitutional events


class EnforcementAction(str, Enum):
    """Actions taken during constitutional enforcement."""

    BLOCKED = "blocked"  # Operation prevented
    WARNING = "warning"  # Flagged but allowed
    AUTO_FIX = "auto_fix"  # Automatically remediated
    PASSED = "passed"  # Compliance verified


class EnforcementOutcome(str, Enum):
    """Outcome classification for enforcement events."""

    SUCCESS = "success"  # Correct enforcement
    FALSE_POSITIVE = "false_positive"  # Incorrect block
    FRICTION = "friction"  # Valid but high-cost enforcement
    OVERRIDE = "override"  # Rule bypassed (should be rare)


class ConstitutionalEvent(BaseModel):
    """
    Constitutional enforcement telemetry event.

    Captures every instance of constitutional rule application
    for learning and pattern analysis.
    """

    model_config = ConfigDict(extra="forbid")

    # Event identification
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(default_factory=_utc_now)

    # Constitutional context
    article: Article = Field(..., description="Constitutional article triggered")
    section: str | None = Field(None, description="Article section (e.g., '2.1')")
    rule_description: str = Field(..., description="Human-readable rule description")

    # Enforcement context
    context: dict[str, JSONValue] = Field(
        default_factory=dict, description="Contextual metadata about enforcement trigger"
    )
    # Context schema (flexible but documented):
    # {
    #   "branch": str,           # Git branch name
    #   "commit_hash": str,      # Git commit hash (if applicable)
    #   "agent_id": str,         # Agent triggering check
    #   "file_path": str,        # File being checked
    #   "operation": str,        # "commit", "merge", "pr_create", "check"
    #   "tool": str,             # Tool invoking check
    # }

    # Enforcement result
    action: EnforcementAction = Field(..., description="Action taken by enforcer")
    outcome: EnforcementOutcome = Field(
        EnforcementOutcome.SUCCESS, description="Outcome classification"
    )

    # Metadata
    severity: str = Field(
        "info", description="Severity level (info, warning, error, critical)"
    )
    error_message: str | None = Field(None, description="Error message if action=blocked")
    suggested_fix: str | None = Field(
        None, description="Suggested remediation if available"
    )
    metadata: dict[str, JSONValue] = Field(
        default_factory=dict, description="Additional metadata for analysis"
    )

    # Learning support
    tags: list[str] = Field(
        default_factory=list, description="Tags for categorization and search"
    )
    # Tags examples: ["constitutional", "article_i", "pre-commit", "agent:planner"]

    def to_jsonl(self) -> str:
        """Convert to JSONL format for logging."""
        return json.dumps(self.model_dump(mode="json"))

    def generate_tags(self) -> list[str]:
        """Generate standard tags for VectorStore indexing."""
        tags = [
            "constitutional",
            f"article_{self.article.value.lower()}",
            f"action_{self.action.value}",
            f"outcome_{self.outcome.value}",
        ]

        if self.context.get("agent_id"):
            tags.append(f"agent:{self.context['agent_id']}")

        if self.context.get("operation"):
            tags.append(f"operation:{self.context['operation']}")

        return tags + self.tags


class ComplianceMetrics(BaseModel):
    """Aggregated constitutional compliance metrics."""

    model_config = ConfigDict(extra="forbid")

    period_start: datetime
    period_end: datetime
    total_events: int = 0
    events_by_article: dict[str, int] = Field(default_factory=dict)
    events_by_action: dict[str, int] = Field(default_factory=dict)
    events_by_outcome: dict[str, int] = Field(default_factory=dict)
    compliance_rate: float = Field(0.0, ge=0.0, le=1.0)
    false_positive_rate: float = Field(0.0, ge=0.0, le=1.0)

    def calculate_rates(self) -> None:
        """Calculate compliance and false positive rates."""
        if self.total_events == 0:
            return

        success_count = self.events_by_outcome.get("success", 0)
        fp_count = self.events_by_outcome.get("false_positive", 0)

        self.compliance_rate = success_count / self.total_events
        self.false_positive_rate = fp_count / self.total_events
