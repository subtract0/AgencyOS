"""
Quality feedback loop for Adaptive Model Router.

Detects task misclassifications via four quality signals:
1. Test failure rate (0.0-1.0)
2. Code churn (lines changed after commit)
3. Execution timing deviation (actual/expected)
4. User feedback (manual classification override)

Constitutional compliance:
- Article I: Complete context (all signals collected before severity)
- Article II: 100% verification (strict Pydantic validation)
- Article IV: VectorStore integration (CRITICAL signals stored)
- Article V: Spec-driven (follows spec-004-quality-feedback-loop.md)

Reference: specs/spec-004-quality-feedback-loop.md Section 6.1
"""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SeverityLevel(str, Enum):
    """
    Severity level for quality signal detection.

    CRITICAL: Causes test failures or major quality degradation (immediate action)
    WARNING: High churn or timing deviation (monitor for patterns)
    INFO: Minor deviations (no action needed)
    """
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class UserFeedback(str, Enum):
    """
    User classification feedback (manual override).

    CORRECT: Task routed to correct tier (positive signal)
    MISCLASSIFIED: Task routed to wrong tier (negative signal, highest confidence)
    UNSURE: User uncertain about classification (neutral signal)
    """
    CORRECT = "correct"
    MISCLASSIFIED = "misclassified"
    UNSURE = "unsure"


class QualitySignals(BaseModel):
    """
    Quality signals for task misclassification detection.

    Collects four signals post-execution:
    1. test_failure_rate: Ratio of failed tests (0.0-1.0)
    2. code_churn_lines: Total lines changed after initial commit
    3. execution_time_ratio: Actual execution time / estimated time
    4. user_feedback: Manual classification override (optional)

    Severity computed from threshold rules:
    - CRITICAL: test_failure_rate >0.1 OR code_churn >100 OR user_feedback=misclassified
    - WARNING: code_churn >50 OR execution_time_ratio >3.0
    - INFO: All other cases (default)

    Example:
        >>> signals = QualitySignals(
        ...     task_id="task_123",
        ...     original_tier="simple",
        ...     test_failure_rate=0.15,  # 15% tests failed
        ...     code_churn_lines=120,    # 120 lines changed after commit
        ...     execution_time_ratio=4.2, # Took 4.2x longer than estimated
        ...     detected_at=datetime.now(UTC).isoformat()
        ... )
        >>> signals.severity
        SeverityLevel.CRITICAL  # test_failure_rate >0.1 AND code_churn >100
    """

    # Task metadata
    task_id: str = Field(
        ...,
        description="Unique task identifier (same as routing decision task_id)"
    )
    original_tier: str = Field(
        ...,
        description="Tier task was routed to (simple/moderate/complex)",
        pattern="^(simple|moderate|complex)$"
    )

    # Signal 1: Test Failures
    test_failure_rate: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Ratio of failed tests (0.0-1.0), None if no tests run. "
                    "CRITICAL threshold: >0.1 (>10% failures indicate wrong tier)"
    )

    # Signal 2: Code Churn
    code_churn_lines: int | None = Field(
        None,
        ge=0,
        description="Total lines changed after initial commit (additions + deletions). "
                    "CRITICAL: >100 (major refactor), WARNING: >50 (moderate refactor)"
    )

    # Signal 3: Execution Timing
    execution_time_ratio: float | None = Field(
        None,
        ge=0.0,
        description="Ratio of actual to estimated execution time (>1.0 means overrun). "
                    "WARNING: >3.0 (task took 3x+ longer than estimated)"
    )

    # Signal 4: User Feedback
    user_feedback: UserFeedback | None = Field(
        None,
        description="Explicit user classification feedback (manual override). "
                    "CRITICAL if misclassified (highest confidence signal)"
    )

    # Computed Fields
    severity: SeverityLevel = Field(
        default=SeverityLevel.INFO,
        description="Computed severity based on threshold rules (auto-computed on init)"
    )

    detected_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 timestamp of signal collection (UTC)"
    )

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "original_tier": "simple",
                "test_failure_rate": 0.12,
                "code_churn_lines": 85,
                "execution_time_ratio": 2.3,
                "user_feedback": None,
                "severity": "critical",
                "detected_at": "2025-10-10T12:34:56.789Z"
            }
        }

    @model_validator(mode="after")
    def compute_severity_after_validation(self) -> "QualitySignals":
        """
        Compute severity level from quality signals.

        Priority order (highest to lowest confidence):
        1. User feedback (manual override)
        2. Test failures (objective quality measure)
        3. Code churn (effort measure)
        4. Execution timing (estimation accuracy)

        Article I compliance: All signals must be collected before computation.

        Returns:
            Self with computed severity level
        """
        # Priority 1: User feedback overrides all (highest confidence)
        if self.user_feedback == UserFeedback.MISCLASSIFIED:
            self.severity = SeverityLevel.CRITICAL
            return self

        # Priority 2: Test failures are critical (wrong tier causes quality issues)
        if self.test_failure_rate is not None and self.test_failure_rate > 0.1:
            self.severity = SeverityLevel.CRITICAL
            return self

        # Priority 3: High churn is critical (major rework after commit)
        if self.code_churn_lines is not None and self.code_churn_lines > 100:
            self.severity = SeverityLevel.CRITICAL
            return self

        # Priority 4: Moderate churn is warning
        if self.code_churn_lines is not None and self.code_churn_lines > 50:
            self.severity = SeverityLevel.WARNING
            return self

        # Priority 5: Severe timing deviation is warning
        if self.execution_time_ratio is not None and self.execution_time_ratio > 3.0:
            self.severity = SeverityLevel.WARNING
            return self

        # Default to INFO (minor deviations, no action needed)
        self.severity = SeverityLevel.INFO
        return self
