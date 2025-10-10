"""
Misclassification detection report models.

Pydantic models for MisclassificationDetector output (spec Section 7.4).

Models:
- DetectedIssue: Single detection rule result
- MisclassificationReport: Complete detection report with aggregated confidence

Constitutional Compliance:
- Article II: Strict typing (no Dict[Any, Any])
- Article V: Follows spec-004-quality-feedback-loop.md Section 7.4

Reference: /Users/am/Code/Agency/specs/spec-004-quality-feedback-loop.md Section 7.4
"""

from pydantic import BaseModel, Field

from shared.models.quality_signals import SeverityLevel


class DetectedIssue(BaseModel):
    """
    Single detection rule result.

    Represents one triggered detection rule with confidence and severity.

    Attributes:
        rule_name: Rule that triggered (e.g., 'test_failure', 'code_churn')
        confidence: Rule confidence score (0.0-1.0)
        severity: Issue severity level (CRITICAL/WARNING/INFO)
        description: Human-readable issue description
        signal_value: Signal value that triggered rule (None for user_feedback)

    Example:
        >>> issue = DetectedIssue(
        ...     rule_name="test_failure",
        ...     confidence=0.95,
        ...     severity=SeverityLevel.CRITICAL,
        ...     description="Test failure rate 33% (5/15 tests failed)",
        ...     signal_value=0.33
        ... )
        >>> issue.confidence
        0.95
    """

    rule_name: str = Field(
        ...,
        description="Rule that triggered (e.g., 'test_failure', 'code_churn', 'execution_timing', 'user_feedback')",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Rule confidence score (0.0-1.0). Higher confidence indicates stronger evidence of misclassification.",
    )

    severity: SeverityLevel = Field(..., description="Issue severity level (CRITICAL/WARNING/INFO)")

    description: str = Field(
        ...,
        description="Human-readable issue description with context (e.g., 'Test failure rate 33%')",
    )

    signal_value: float | None = Field(
        None,
        description="Signal value that triggered rule (e.g., 0.33 for test_failure_rate). None for user_feedback.",
    )

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "rule_name": "test_failure",
                "confidence": 0.95,
                "severity": "critical",
                "description": "Test failure rate 33% (5/15 tests failed)",
                "signal_value": 0.33,
            }
        }


class MisclassificationReport(BaseModel):
    """
    Complete misclassification detection report.

    Aggregates multiple detection rules and recommends corrected tier.

    Attributes:
        task_id: Task identifier
        original_tier: Tier task was routed to (simple/moderate/complex)
        recommended_tier: Recommended tier based on detection
        detected_issues: List of triggered detection rules
        aggregated_confidence: Weighted average confidence from all rules
        is_misclassified: True if any CRITICAL/WARNING issue detected
        detected_at: ISO 8601 timestamp of detection

    Example:
        >>> report = MisclassificationReport(
        ...     task_id="refactor_async_handler_42",
        ...     original_tier="simple",
        ...     recommended_tier="complex",
        ...     detected_issues=[
        ...         DetectedIssue(
        ...             rule_name="test_failure",
        ...             confidence=0.95,
        ...             severity=SeverityLevel.CRITICAL,
        ...             description="Test failure rate 33%",
        ...             signal_value=0.33
        ...         ),
        ...         DetectedIssue(
        ...             rule_name="code_churn",
        ...             confidence=0.85,
        ...             severity=SeverityLevel.CRITICAL,
        ...             description="Code churn 145 lines",
        ...             signal_value=145
        ...         )
        ...     ],
        ...     aggregated_confidence=0.905,
        ...     is_misclassified=True,
        ...     detected_at="2025-10-10T15:23:45Z"
        ... )
        >>> report.is_misclassified
        True
    """

    task_id: str = Field(..., description="Task identifier (same as QualitySignals.task_id)")

    original_tier: str = Field(
        ...,
        description="Tier task was routed to (simple/moderate/complex)",
        pattern="^(simple|moderate|complex)$",
    )

    recommended_tier: str = Field(
        ...,
        description="Recommended tier based on detection (simple/moderate/complex)",
        pattern="^(simple|moderate|complex)$",
    )

    detected_issues: list[DetectedIssue] = Field(
        ..., description="List of triggered detection rules with confidence and severity"
    )

    aggregated_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted average confidence from all triggered rules. "
        "Formula: sum(confidence^2) / count. User feedback always returns 1.0.",
    )

    is_misclassified: bool = Field(
        ...,
        description="True if any CRITICAL or WARNING issue detected. "
        "False if all issues are INFO or no issues detected.",
    )

    detected_at: str = Field(..., description="ISO 8601 timestamp of detection (UTC)")

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "task_id": "refactor_async_handler_42",
                "original_tier": "simple",
                "recommended_tier": "complex",
                "detected_issues": [
                    {
                        "rule_name": "test_failure",
                        "confidence": 0.95,
                        "severity": "critical",
                        "description": "Test failure rate 33% (5/15 tests failed)",
                        "signal_value": 0.33,
                    },
                    {
                        "rule_name": "code_churn",
                        "confidence": 0.85,
                        "severity": "critical",
                        "description": "Code churn 145 lines (>100 threshold)",
                        "signal_value": 145,
                    },
                ],
                "aggregated_confidence": 0.905,
                "is_misclassified": True,
                "detected_at": "2025-10-10T15:23:45Z",
            }
        }
