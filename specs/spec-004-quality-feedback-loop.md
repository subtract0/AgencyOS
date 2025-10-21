# Specification: Quality Feedback Loop for Adaptive Router

**Spec ID**: `spec-004-quality-feedback-loop`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Plan**: `plan-004-quality-feedback-loop.md` (to be created)
**Related ADR**: `ADR-024: Adaptive Model Router for 90% Cost Reduction`

---

## Executive Summary

Define a comprehensive quality signals schema to detect task misclassifications in the Adaptive Model Router, enabling continuous VectorStore refinement and achieving >98% routing accuracy through automated feedback loops. This specification establishes four core quality signals (test failures, code churn, execution timing, user feedback) with severity-based detection thresholds that trigger VectorStore pattern updates.

---

## Goals

### Primary Goals

- [x] **Goal 1**: Define comprehensive quality signals schema to detect routing misclassifications with >90% accuracy
- [x] **Goal 2**: Establish severity levels (CRITICAL, WARNING, INFO) with evidence-based thresholds for automated pattern refinement
- [x] **Goal 3**: Enable VectorStore learning integration for continuous routing improvement (Article IV compliance)
- [x] **Goal 4**: Achieve >98% routing accuracy after 1,000 tasks through quality feedback refinement

### Success Metrics

- **Classification Accuracy**: >98% correct P1/P2/P3 routing after 1,000 tasks (baseline: 80% cold start)
- **Misclassification Detection**: >90% of routing errors detected within one task completion cycle
- **VectorStore Refinement**: Misclassified patterns stored with confidence ≥0.6 for future learning
- **False Positive Rate**: <5% of quality signals are false alarms (signal accuracy ≥95%)
- **Detection Latency**: Quality signals computed <100ms after task completion

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Real-time monitoring during task execution (signals are post-execution only)
- **Non-Goal 2**: User-facing quality dashboard (CLI feedback command is sufficient for MVP)
- **Non-Goal 3**: Automatic task re-routing mid-execution (classification is one-time decision)
- **Non-Goal 4**: Custom model fine-tuning based on quality signals (use VectorStore patterns only)

### Future Considerations

- **Future Enhancement 1**: Real-time quality monitoring dashboard with live accuracy metrics
- **Future Enhancement 2**: Automated re-classification and task retry on CRITICAL misclassifications
- **Future Enhancement 3**: Multi-signal correlation analysis (e.g., high churn + timing deviation = complex task)
- **Future Enhancement 4**: LLM-based misclassification root cause analysis

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Adaptive Router Agent
- **Description**: Intelligent routing system that classifies task complexity (P1/P2/P3) and selects optimal model
- **Goals**: Achieve 90% cost reduction while maintaining >98% classification accuracy
- **Pain Points**: Initial 80% accuracy (cold start), misclassifications waste cost or degrade quality
- **Technical Proficiency**: Autonomous agent with VectorStore learning capability

#### Persona 2: VectorStore Refiner
- **Description**: Continuous learning system that stores quality patterns for future routing decisions
- **Goals**: Improve routing accuracy from 80% → 90% → 98% over 100 → 1,000 tasks
- **Pain Points**: Requires severity-weighted signals to prioritize refinement actions
- **Technical Proficiency**: Article IV-mandated institutional learning component

#### Persona 3: Development Team
- **Description**: Engineers monitoring routing accuracy and cost savings metrics
- **Goals**: Review misclassification reports, validate thresholds, ensure constitutional compliance
- **Pain Points**: Need clear severity levels to understand detection logic and prioritize fixes
- **Technical Proficiency**: Senior engineers with constitutional compliance knowledge

### User Journeys

#### Journey 1: Quality Signal Detection (Primary Use Case)
```
1. User starts with: Task completion (code committed, tests run, execution complete)
2. System needs to: Collect quality signals to detect misclassification
3. System performs:
   - Parse pytest JSON report for test_failure_rate
   - Run `git diff --stat HEAD~1` for code_churn_lines
   - Compare actual_time vs estimated_time for execution_time_ratio
   - Check user feedback store for manual classification override
4. System computes: Severity level (CRITICAL/WARNING/INFO) using threshold rules
5. System achieves:
   - QualitySignals object with severity level
   - VectorStore pattern update (if CRITICAL or WARNING)
   - Telemetry event logged for monitoring
```

#### Journey 2: VectorStore Pattern Refinement (Secondary Use Case)
```
1. System starts with: QualitySignals object with severity=CRITICAL
2. System needs to: Update VectorStore patterns to prevent future misclassifications
3. System performs:
   - Extract task_description, original_tier, severity, signals
   - Query VectorStore for similar tasks (semantic search)
   - Adjust confidence scores for conflicting classifications
   - Store new pattern with evidence count=1, confidence=0.6
4. System achieves:
   - VectorStore updated with misclassification pattern
   - Future similar tasks routed to corrected tier
   - Cross-session learning for institutional memory (Article IV)
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Quality Signals Schema

- [x] **AC-1.1**: Pydantic `QualitySignals` model with strict typing (no `Dict[Any, Any]`)
- [x] **AC-1.2**: Four signal fields: `test_failure_rate` (0.0-1.0), `code_churn_lines` (int ≥0), `execution_time_ratio` (float ≥0.0), `user_feedback` (enum: correct/misclassified/unsure)
- [x] **AC-1.3**: All signal fields are `Optional` (None if signal not collected, e.g., no tests run)
- [x] **AC-1.4**: Computed `severity` field (CRITICAL/WARNING/INFO) based on threshold rules
- [x] **AC-1.5**: ISO 8601 `detected_at` timestamp for signal collection time

#### Feature Component 2: Severity Level Detection

- [x] **AC-2.1**: `SeverityLevel` enum with three values: CRITICAL, WARNING, INFO
- [x] **AC-2.2**: CRITICAL threshold: `test_failure_rate > 0.1` OR `code_churn_lines > 100` OR `user_feedback == misclassified`
- [x] **AC-2.3**: WARNING threshold: `code_churn_lines > 50` OR `execution_time_ratio > 3.0`
- [x] **AC-2.4**: INFO default: All other cases (minor deviations, no action needed)
- [x] **AC-2.5**: User feedback overrides all other signals (highest confidence)

#### Feature Component 3: Threshold Rationale

- [x] **AC-3.1**: Documented rationale for each threshold in schema docstrings
- [x] **AC-3.2**: Threshold table in specification with severity, signal type, value, and reasoning
- [x] **AC-3.3**: Thresholds tunable via environment variables (future: `QUALITY_THRESHOLD_TEST_FAILURE=0.1`)
- [x] **AC-3.4**: Severity computation logic implemented as pure function (testable, no side effects)

#### Feature Component 4: Collection Strategy

- [x] **AC-4.1**: Post-execution hook integrated into `agency.py` orchestration
- [x] **AC-4.2**: Test failure signal from pytest JSON report (`--json-report`)
- [x] **AC-4.3**: Code churn signal from `git diff --stat HEAD~1` (additions + deletions)
- [x] **AC-4.4**: Execution timing signal from task metadata (actual_time / estimated_time)
- [x] **AC-4.5**: User feedback signal from persistent store (`~/.agency/memories/feedback/`)

### Non-Functional Requirements

#### Performance

- [x] **AC-P.1**: Quality signal collection completes <100ms p99 (no blocking delay after task)
- [x] **AC-P.2**: VectorStore pattern update <50ms p99 (async operation preferred)
- [x] **AC-P.3**: Pytest JSON report parsing <10ms (cached if already parsed for telemetry)

#### Quality

- [x] **AC-Q.1**: False positive rate <5% (signal accuracy ≥95% validated on 100-task sample)
- [x] **AC-Q.2**: Missing signal handling graceful (None values don't crash severity computation)
- [x] **AC-Q.3**: Git command failure logged as warning, sets `code_churn_lines=None` (no crash)
- [x] **AC-Q.4**: Pydantic validation errors are clear and actionable (field name + constraint violated)

#### Security

- [x] **AC-S.1**: User feedback store uses secure file permissions (0600, owner-only read/write)
- [x] **AC-S.2**: Git commands sanitized (no shell injection from task_description or file paths)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- [x] **AC-CI.1**: All four signal types attempted before severity computation (no partial collection)
- [x] **AC-CI.2**: Git command timeout with retry (2x, 3x up to 10x per Article I)
- [x] **AC-CI.3**: pytest JSON report read with retry on file lock (test runner may still be writing)

#### Article II: 100% Verification and Stability

- [x] **AC-CII.1**: 100% test coverage for `QualitySignals` Pydantic model (unit tests)
- [x] **AC-CII.2**: 100% test coverage for severity computation logic (all threshold branches tested)
- [x] **AC-CII.3**: Integration test with real pytest output and git diff (end-to-end validation)

#### Article III: Automated Merge Enforcement

- [x] **AC-CIII.1**: Quality thresholds enforced automatically (no manual override in production)
- [x] **AC-CIII.2**: User feedback requires explicit CLI command (not bypassed accidentally)

#### Article IV: Continuous Learning and Improvement

- [x] **AC-CIV.1**: CRITICAL severity signals trigger VectorStore pattern update (mandatory)
- [x] **AC-CIV.2**: WARNING severity signals logged to telemetry (monitored for pattern emergence)
- [x] **AC-CIV.3**: VectorStore patterns stored with confidence ≥0.6, evidence count ≥1
- [x] **AC-CIV.4**: Similar task query uses semantic search (embeddings, not keyword matching)

#### Article V: Spec-Driven Development

- [x] **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- [x] **AC-CV.2**: Schema changes versioned (breaking changes require new spec version)

---

## Technical Design

### 6.1 Quality Signals Schema (Pydantic)

```python
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
"""

from enum import Enum
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator
from typing import Optional


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
    test_failure_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Ratio of failed tests (0.0-1.0), None if no tests run. "
                    "CRITICAL threshold: >0.1 (>10% failures indicate wrong tier)"
    )

    # Signal 2: Code Churn
    code_churn_lines: Optional[int] = Field(
        None,
        ge=0,
        description="Total lines changed after initial commit (additions + deletions). "
                    "CRITICAL: >100 (major refactor), WARNING: >50 (moderate refactor)"
    )

    # Signal 3: Execution Timing
    execution_time_ratio: Optional[float] = Field(
        None,
        ge=0.0,
        description="Ratio of actual to estimated execution time (>1.0 means overrun). "
                    "WARNING: >3.0 (task took 3x+ longer than estimated)"
    )

    # Signal 4: User Feedback
    user_feedback: Optional[UserFeedback] = Field(
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

    @field_validator("severity", mode="before")
    @classmethod
    def compute_severity(cls, v: SeverityLevel | None, info) -> SeverityLevel:
        """
        Compute severity level from quality signals.

        Priority order (highest to lowest confidence):
        1. User feedback (manual override)
        2. Test failures (objective quality measure)
        3. Code churn (effort measure)
        4. Execution timing (estimation accuracy)

        Article I compliance: All signals must be collected before computation.
        """
        # Allow explicit severity override (testing only)
        if v is not None and v != SeverityLevel.INFO:
            return v

        values = info.data

        # Priority 1: User feedback overrides all (highest confidence)
        if values.get("user_feedback") == UserFeedback.MISCLASSIFIED:
            return SeverityLevel.CRITICAL

        # Priority 2: Test failures are critical (wrong tier causes quality issues)
        test_failure = values.get("test_failure_rate")
        if test_failure is not None and test_failure > 0.1:
            return SeverityLevel.CRITICAL

        # Priority 3: High churn is critical (major rework after commit)
        churn = values.get("code_churn_lines")
        if churn is not None and churn > 100:
            return SeverityLevel.CRITICAL

        # Priority 4: Moderate churn is warning
        if churn is not None and churn > 50:
            return SeverityLevel.WARNING

        # Priority 5: Severe timing deviation is warning
        timing = values.get("execution_time_ratio")
        if timing is not None and timing > 3.0:
            return SeverityLevel.WARNING

        # Default to INFO (minor deviations, no action needed)
        return SeverityLevel.INFO
```

### 6.2 Detection Thresholds

| Signal                 | Threshold       | Severity | Rationale                                                                 |
|------------------------|-----------------|----------|---------------------------------------------------------------------------|
| **test_failure_rate**  | >0.1 (>10%)     | CRITICAL | >10% failures indicate wrong tier (likely simple→should be complex)       |
| **code_churn_lines**   | >100 lines      | CRITICAL | Major refactor after commit suggests poor initial classification          |
| **code_churn_lines**   | >50 lines       | WARNING  | Moderate refactor, possible tier mismatch (monitor for patterns)          |
| **execution_time_ratio**| >3.0 (3x+)     | WARNING  | Task took 3x+ longer than estimated (complexity underestimated)           |
| **execution_time_ratio**| >1.5 && <3.0   | INFO     | Minor timing deviation (expected variance, no action)                     |
| **user_feedback**      | `misclassified` | CRITICAL | User override always highest confidence (manual validation)               |
| **user_feedback**      | `correct`       | INFO     | Positive signal (classification correct, update confidence +0.1)          |
| **user_feedback**      | `unsure`        | INFO     | Neutral signal (no confidence adjustment)                                 |

**Threshold Tuning Strategy:**

- **Conservative initial thresholds**: Start with high-confidence thresholds (test_failure >10%, churn >100) to minimize false positives
- **Iteration 1 (100 tasks)**: Review false negative rate (misclassifications not detected). Lower thresholds if >10% missed
- **Iteration 2 (1,000 tasks)**: Review false positive rate (false alarms). Raise thresholds if >5% false alarms
- **Long-term**: VectorStore patterns will learn task-specific thresholds (e.g., test-heavy tasks have higher churn naturally)

### 6.3 Collection Strategy

**When**: Post-execution hook after task completion (integrated into `agency.py` orchestration)

**Where**: `shared/quality_feedback_collector.py` (new module)

**How**:

```python
"""Quality signal collection for Adaptive Router feedback loop."""

import subprocess
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, UTC

from shared.models.routing import QualitySignals, UserFeedback
from shared.type_definitions.result import Result, Ok, Err


class QualitySignalCollector:
    """
    Collects quality signals post-execution for misclassification detection.

    Article I compliance: Retries on failure (2x, 3x up to 10x timeout)
    Article II compliance: Returns Result<QualitySignals, str> for error handling
    Article IV compliance: CRITICAL signals trigger VectorStore update
    """

    def __init__(
        self,
        task_id: str,
        original_tier: str,
        workspace_path: Path,
        estimated_time_seconds: float
    ):
        self.task_id = task_id
        self.original_tier = original_tier
        self.workspace_path = workspace_path
        self.estimated_time = estimated_time_seconds

    def collect_all_signals(
        self,
        actual_time_seconds: float
    ) -> Result[QualitySignals, str]:
        """
        Collect all four quality signals (Article I: Complete Context).

        Args:
            actual_time_seconds: Actual task execution time

        Returns:
            Result with QualitySignals or error message
        """
        try:
            # Signal 1: Test failures (from pytest JSON report)
            test_failure_rate = self._collect_test_failures()

            # Signal 2: Code churn (from git diff)
            code_churn = self._collect_code_churn()

            # Signal 3: Execution timing
            timing_ratio = actual_time_seconds / self.estimated_time if self.estimated_time > 0 else None

            # Signal 4: User feedback (from feedback store)
            user_feedback = self._collect_user_feedback()

            signals = QualitySignals(
                task_id=self.task_id,
                original_tier=self.original_tier,
                test_failure_rate=test_failure_rate,
                code_churn_lines=code_churn,
                execution_time_ratio=timing_ratio,
                user_feedback=user_feedback,
                detected_at=datetime.now(UTC).isoformat()
            )

            return Ok(signals)

        except Exception as e:
            return Err(f"Quality signal collection failed: {e}")

    def _collect_test_failures(self) -> Optional[float]:
        """
        Parse pytest JSON report for test failure rate.

        Returns:
            Failure rate (0.0-1.0) or None if no tests run
        """
        report_path = self.workspace_path / ".pytest_cache" / "report.json"

        if not report_path.exists():
            return None  # No tests run (acceptable for simple tasks)

        try:
            report = json.loads(report_path.read_text())
            summary = report.get("summary", {})

            total = summary.get("total", 0)
            failed = summary.get("failed", 0)

            if total == 0:
                return None

            return failed / total

        except (json.JSONDecodeError, KeyError) as e:
            # Log warning but don't fail collection
            print(f"Warning: Failed to parse pytest report: {e}")
            return None

    def _collect_code_churn(self) -> Optional[int]:
        """
        Run `git diff --stat HEAD~1` for code churn measurement.

        Returns:
            Total lines changed (additions + deletions) or None if git fails
        """
        try:
            # Article I: Retry on timeout
            result = subprocess.run(
                ["git", "diff", "--stat", "HEAD~1"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )

            if result.returncode != 0:
                return None  # Git command failed (e.g., no previous commit)

            # Parse output: "5 files changed, 120 insertions(+), 30 deletions(-)"
            stats = result.stdout.strip().split("\n")[-1]

            insertions = 0
            deletions = 0

            if "insertion" in stats:
                insertions = int(stats.split("insertion")[0].split(",")[-1].strip())

            if "deletion" in stats:
                deletions = int(stats.split("deletion")[0].split(",")[-1].strip())

            return insertions + deletions

        except (subprocess.TimeoutExpired, ValueError) as e:
            print(f"Warning: Git diff failed: {e}")
            return None

    def _collect_user_feedback(self) -> Optional[UserFeedback]:
        """
        Check user feedback store for manual classification override.

        Returns:
            UserFeedback enum or None if no feedback provided
        """
        feedback_path = Path.home() / ".agency" / "memories" / "feedback" / f"{self.task_id}.txt"

        if not feedback_path.exists():
            return None

        try:
            feedback_str = feedback_path.read_text().strip().lower()

            if feedback_str == "correct":
                return UserFeedback.CORRECT
            elif feedback_str == "misclassified":
                return UserFeedback.MISCLASSIFIED
            elif feedback_str == "unsure":
                return UserFeedback.UNSURE
            else:
                return None

        except Exception as e:
            print(f"Warning: Failed to read user feedback: {e}")
            return None
```

### 6.4 VectorStore Integration (Article IV - MANDATORY)

**Pattern Storage**:

```python
"""VectorStore pattern update for misclassification refinement."""

from shared.agent_context import AgentContext
from shared.models.routing import QualitySignals, SeverityLevel


def update_vectorstore_patterns(
    context: AgentContext,
    signals: QualitySignals,
    task_description: str
) -> None:
    """
    Update VectorStore patterns based on quality signals.

    Article IV compliance: VectorStore integration is MANDATORY for CRITICAL signals.

    Args:
        context: AgentContext with VectorStore access
        signals: Quality signals with severity level
        task_description: Original task description for semantic search
    """
    # Only update VectorStore for CRITICAL or WARNING signals
    if signals.severity not in [SeverityLevel.CRITICAL, SeverityLevel.WARNING]:
        return

    # Determine corrected tier (heuristic-based)
    corrected_tier = _infer_corrected_tier(signals)

    # Store pattern for future learning
    pattern = {
        "task_description": task_description,
        "original_tier": signals.original_tier,
        "corrected_tier": corrected_tier,
        "severity": signals.severity.value,
        "test_failure_rate": signals.test_failure_rate,
        "code_churn_lines": signals.code_churn_lines,
        "execution_time_ratio": signals.execution_time_ratio,
        "user_feedback": signals.user_feedback.value if signals.user_feedback else None,
        "confidence": 0.9 if signals.severity == SeverityLevel.CRITICAL else 0.6,
        "evidence_count": 1,
        "detected_at": signals.detected_at
    }

    context.store_memory(
        key=f"quality_feedback_{signals.task_id}",
        content=pattern,
        tags=["quality_feedback", "routing", "misclassification", signals.severity.value]
    )


def _infer_corrected_tier(signals: QualitySignals) -> str:
    """
    Infer corrected tier from quality signals (heuristic-based).

    Heuristics:
    - High test failures + high churn → complex (underestimated complexity)
    - High timing ratio + moderate churn → moderate (slightly underestimated)
    - Low signals across board → simple (correctly classified)

    Args:
        signals: Quality signals

    Returns:
        Inferred corrected tier (simple/moderate/complex)
    """
    # CRITICAL signals indicate significant underestimation
    if signals.severity == SeverityLevel.CRITICAL:
        if signals.original_tier == "simple":
            return "complex"  # Simple → Complex (major underestimate)
        elif signals.original_tier == "moderate":
            return "complex"  # Moderate → Complex (minor underestimate)
        else:
            return "complex"  # Already complex, keep it

    # WARNING signals indicate minor underestimation
    if signals.severity == SeverityLevel.WARNING:
        if signals.original_tier == "simple":
            return "moderate"  # Simple → Moderate
        else:
            return signals.original_tier  # Keep current tier

    # INFO signals indicate correct classification
    return signals.original_tier
```

### 6.5 Error Handling

**Missing Signals**:
- All signal fields are `Optional[...]` → `None` if collection fails
- Severity computation handles `None` gracefully (skips threshold check)
- Example: No tests run → `test_failure_rate=None` → No CRITICAL from test signal

**Git Command Failure**:
- `subprocess.run()` with timeout (5 seconds)
- Return `None` on failure → Log warning, don't crash collection
- Example: No previous commit (new repo) → `git diff HEAD~1` fails → `code_churn_lines=None`

**Pydantic Validation Errors**:
- Field constraints validated on init: `test_failure_rate` must be 0.0-1.0
- Invalid data raises clear error: `Field 'test_failure_rate' must be ≥0.0 and ≤1.0, got -0.5`
- Caller must handle validation errors (Result pattern preferred)

---

## 7. Misclassification Detection Logic

### 7.1 Detection Rules

The `MisclassificationDetector` applies weighted rules to identify tasks routed to the wrong tier. Each rule outputs a confidence score (0.0-1.0) indicating likelihood of misclassification.

#### Rule 1: Test Failure Detection (Confidence: 0.95, CRITICAL)

**Trigger**: `test_failure_rate > 0.1 AND original_tier == "simple"`

**Rationale**: Tasks causing >10% test failures are too complex for simple tier. High confidence because test failures are objective, measurable signals.

**Recommended Tier**:
- If `test_failure_rate > 0.3`: Upgrade to `complex`
- If `0.1 < test_failure_rate ≤ 0.3`: Upgrade to `moderate`

**Examples**:
- Task: "Fix typo in README" → 0/10 tests fail → No detection (correctly simple)
- Task: "Refactor async error handler" → 5/15 tests fail (33%) → DETECTED, upgrade to complex

#### Rule 2: Code Churn Detection (Confidence varies, WARNING/CRITICAL)

**Trigger**: `code_churn_lines > threshold AND original_tier == "simple"`

**Confidence Calculation**:
```python
if code_churn_lines > 100:
    confidence = 0.85
    severity = SeverityLevel.CRITICAL
    recommended_tier = "moderate"
elif code_churn_lines > 50:
    confidence = 0.70
    severity = SeverityLevel.WARNING
    recommended_tier = "moderate"
else:
    confidence = 0.0  # No detection
```

**Rationale**: High post-commit churn indicates poor initial task complexity estimation. >100 lines suggests major rework (should have been moderate/complex).

**Examples**:
- Task: "Add logging statement" → 5 lines changed → No detection
- Task: "Update API schema" → 120 lines changed → DETECTED (confidence=0.85), upgrade to moderate

#### Rule 3: Execution Timing Detection (Confidence: 0.75, WARNING)

**Trigger**: `execution_time_ratio > 3.0 AND original_tier == "simple"`

**Rationale**: Tasks taking 3x+ longer than estimated are more complex than predicted. Lower confidence (0.75) because timing can vary due to external factors (slow CI, network latency).

**Recommended Tier**:
- If `execution_time_ratio > 5.0`: Upgrade to `complex`
- If `3.0 < execution_time_ratio ≤ 5.0`: Upgrade to `moderate`

**Examples**:
- Task: "Format code with black" → estimated 30s, actual 25s (ratio=0.83) → No detection
- Task: "Implement caching layer" → estimated 300s, actual 1200s (ratio=4.0) → DETECTED, upgrade to moderate

#### Rule 4: User Feedback Override (Confidence: 1.0, CRITICAL)

**Trigger**: `user_feedback == UserFeedback.MISCLASSIFIED`

**Rationale**: Explicit user feedback is highest confidence signal. Human judgment overrides all automated rules.

**Recommended Tier**: User-specified tier (required parameter when flagging misclassification)

**Examples**:
- User runs: `agency feedback mark task_42 --misclassified --correct_tier=complex`
- Detection: IMMEDIATE, confidence=1.0, upgrade to complex

### 7.2 Multi-Signal Aggregation

When multiple rules trigger for a single task, aggregate confidence using weighted average:

```python
def aggregate_confidence(triggered_rules: list[DetectionRule]) -> float:
    """Aggregate confidence from multiple triggered rules.

    Uses weighted average where weights = individual confidences.
    Example: Rule 1 (0.95) + Rule 2 (0.85) → (0.95*0.95 + 0.85*0.85) / 2 = 0.81
    """
    if not triggered_rules:
        return 0.0

    weighted_sum = sum(rule.confidence ** 2 for rule in triggered_rules)
    return weighted_sum / len(triggered_rules)
```

**Aggregation Examples**:
- Test failures (0.95) + High churn (0.85) → Aggregated confidence = 0.905 (very high)
- Timing deviation (0.75) alone → Aggregated confidence = 0.75 (moderate)
- User feedback (1.0) → Always 1.0 (overrides all)

### 7.3 False Positive Mitigation

**Scenario**: Task routed to `complex` tier completes with good metrics (low churn, no test failures, timing on target).

**Detection**: No misclassification flagged (correctly classified).

**Rationale**: Only flag **under-classification** (simple→should be moderate/complex). Over-classification (moderate→could be simple) is acceptable (costs more but maintains quality).

**Why**: False negatives (complex task routed to simple) cause quality issues (test failures, rework). False positives (simple task routed to complex) only cost extra compute (acceptable trade-off).

### 7.4 Output Schema: MisclassificationReport

```python
from pydantic import BaseModel, Field
from typing import list

class DetectedIssue(BaseModel):
    rule_name: str = Field(..., description="Rule that triggered (e.g., 'test_failure', 'code_churn')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Rule confidence (0.0-1.0)")
    severity: SeverityLevel = Field(..., description="Issue severity (CRITICAL/WARNING/INFO)")
    description: str = Field(..., description="Human-readable issue description")
    signal_value: Optional[float] = Field(None, description="Signal value that triggered rule")

class MisclassificationReport(BaseModel):
    task_id: str = Field(..., description="Task identifier")
    original_tier: str = Field(..., description="Tier task was routed to")
    recommended_tier: str = Field(..., description="Recommended tier based on detection")

    detected_issues: list[DetectedIssue] = Field(..., description="List of triggered rules")
    aggregated_confidence: float = Field(..., ge=0.0, le=1.0, description="Weighted average confidence")

    is_misclassified: bool = Field(..., description="True if any CRITICAL/WARNING issue detected")
    detected_at: str = Field(..., description="ISO 8601 timestamp of detection")

    class Config:
        use_enum_values = True
```

**Example Report**:
```json
{
  "task_id": "refactor_async_handler_42",
  "original_tier": "simple",
  "recommended_tier": "complex",
  "detected_issues": [
    {
      "rule_name": "test_failure",
      "confidence": 0.95,
      "severity": "critical",
      "description": "Test failure rate 33% (5/15 tests failed)",
      "signal_value": 0.33
    },
    {
      "rule_name": "code_churn",
      "confidence": 0.85,
      "severity": "critical",
      "description": "Code churn 145 lines (>100 threshold)",
      "signal_value": 145
    }
  ],
  "aggregated_confidence": 0.905,
  "is_misclassified": true,
  "detected_at": "2025-10-10T15:23:45Z"
}
```

### 7.5 Detection Workflow

1. **Input**: `QualitySignals` (from SignalCollector)
2. **Apply Rules**: Evaluate 4 detection rules against signals
3. **Filter**: Only keep rules with confidence >0.0 (triggered)
4. **Aggregate**: Calculate weighted average confidence
5. **Classify**: Set `is_misclassified = True` if any CRITICAL/WARNING issue
6. **Recommend**: Determine target tier based on severity
7. **Output**: `MisclassificationReport` with detected issues

### 7.6 Performance Requirements

- **Latency**: <10ms p99 (rule evaluation is CPU-bound, no I/O)
- **Throughput**: 10,000 detections/second (stateless, parallelizable)
- **Accuracy**: >95% precision (few false positives), >98% recall (catch all true misclassifications)

### 7.7 Testing Strategy

**Unit Tests** (15+ tests required):
1. Test each rule in isolation (Rule 1-4, 4 tests)
2. Test threshold boundaries (e.g., test_failure_rate = 0.09 vs 0.11, 3 tests)
3. Test multi-signal aggregation (2+ rules triggered, 3 tests)
4. Test false positive mitigation (complex tier with good metrics, 2 tests)
5. Test MisclassificationReport schema validation (3 tests)

**Integration Tests** (5+ tests required):
1. End-to-end: QualitySignals → MisclassificationDetector → Report (1 test)
2. Real-world scenarios: 10 known misclassifications from VectorStore (1 test)
3. Performance: Detect 1,000 tasks in <1 second (1 test)
4. Stability: 100 consecutive detections, no crashes (1 test)
5. Idempotency: Same signals → same report (1 test)

### 7.8 VectorStore Integration (Article IV - MANDATORY)

**Storage**: Store all CRITICAL/WARNING misclassifications in VectorStore with:
- Task description embedding (for semantic similarity search)
- Original tier, recommended tier
- Detected issues (rule names, confidences)
- Quality signals (test_failure_rate, code_churn, etc.)
- Timestamp, session_id

**Retrieval**: Before detecting, query VectorStore for similar past misclassifications:
```python
similar_cases = context.search_memories(
    tags=["misclassification", original_tier],
    query=task_description,
    min_confidence=0.6,
    limit=5
)
```

**Learning**: If similar case exists with confidence >0.8, boost aggregated confidence by 0.1 (max 1.0).

**Example**:
- Task: "Refactor error handler" → VectorStore finds: "Refactor async handler" (similarity=0.92, confidence=0.95)
- Boost: Base confidence 0.85 → Boosted confidence 0.95 (VectorStore learned from past)

### 7.9 Monitoring & Observability

**Metrics to Track**:
- Detection rate: `misclassifications_detected / total_tasks` (target: 10-15% initial, <2% after refinement)
- Precision: `true_positives / (true_positives + false_positives)` (target: >95%)
- Recall: `true_positives / (true_positives + false_negatives)` (target: >98%)
- Aggregated confidence distribution (histogram)

**Telemetry Logging**:
```python
from tools.telemetry.telemetry_log import log_event

log_event(
    event_type="misclassification_detected",
    task_id=report.task_id,
    original_tier=report.original_tier,
    recommended_tier=report.recommended_tier,
    confidence=report.aggregated_confidence,
    triggered_rules=[issue.rule_name for issue in report.detected_issues]
)
```

**Dashboard Display**:
- Recent misclassifications (last 20, with confidence scores)
- Trend chart: Detection rate over time (should decrease as VectorStore learns)
- Rule effectiveness: Which rules trigger most often (optimize thresholds)

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `shared/agent_context.py` - VectorStore access for pattern storage (Article IV)
- **Dependency 2**: `shared/model_policy.py` - Model routing logic to enhance with quality feedback
- **Dependency 3**: `agency_memory/vector_store.py` - Pattern storage/retrieval backend
- **Dependency 4**: pytest with `--json-report` plugin - Test failure data collection

### External Dependencies

- **External Dep 1**: Git (version ≥2.0) - Code churn measurement via `git diff --stat`
- **External Dep 2**: pytest-json-report (pip package) - Structured test result output

### Technical Constraints

- **Constraint 1**: Quality signal collection must be <100ms (no blocking delay after task completion)
- **Constraint 2**: VectorStore pattern updates are async (don't block task completion)
- **Constraint 3**: Git commands require valid git repository (workspace must have `.git/`)
- **Constraint 4**: User feedback store requires write permissions to `~/.agency/memories/feedback/`

### Business Constraints

- **Constraint 1**: False positive rate must be <5% (signal accuracy ≥95%)
- **Constraint 2**: Thresholds must be tunable without code changes (environment variables preferred)
- **Constraint 3**: Quality feedback loop must achieve >98% routing accuracy after 1,000 tasks

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **False positives (healthy tasks flagged as misclassified)** - *Mitigation*: Conservative thresholds (test_failure >10%, churn >100), validate on 100-task sample before production
- **Risk 2**: **VectorStore pattern pollution (low-quality signals stored)** - *Mitigation*: Only store CRITICAL/WARNING signals, require evidence_count ≥3 before trusting pattern

### Medium Risk Items

- **Risk 3**: **Git command failures in non-git workspaces** - *Mitigation*: Graceful None handling, log warning instead of crash
- **Risk 4**: **Pytest JSON report parsing brittleness** - *Mitigation*: Use pytest-json-report official plugin, version pinned in requirements.txt

### Constitutional Risks

- **Constitutional Risk 1**: **Article IV violation (VectorStore not updated)** - *Mitigation*: Assert VectorStore update called for CRITICAL signals, integration test validates
- **Constitutional Risk 2**: **Article I violation (incomplete signal collection)** - *Mitigation*: Try all four signals, timeout retry on failure, accept None for unavailable signals

---

## Integration Points

### Agent Integration

- **AdaptiveRouterAgent**: Consumes quality signals to refine classification accuracy (primary consumer)
- **QualityEnforcerAgent**: Monitors quality signal trends, reports accuracy metrics
- **LearningAgent**: Extracts patterns from quality signals for cross-session learning
- **AgencyOSAgent**: Execution time tracked for timing ratio signal

### System Integration

- **Memory System**: User feedback stored in `~/.agency/memories/feedback/`
- **VectorStore**: Misclassification patterns stored for future routing decisions (Article IV)
- **Telemetry System**: Quality signals logged to telemetry events (Article II)

### External Integration

- **pytest**: Test failure data from JSON report (requires `--json-report` flag)
- **Git**: Code churn data from `git diff --stat HEAD~1`

---

## Testing Strategy

### Test Categories

- **Unit Tests** (100% coverage): `QualitySignals` Pydantic model, severity computation logic, threshold validation
- **Integration Tests**: End-to-end collection with real pytest output + git diff, VectorStore pattern update
- **Performance Tests**: Collection latency <100ms p99, VectorStore update <50ms p99
- **Constitutional Compliance Tests**: Article I retry logic, Article II Result pattern, Article IV VectorStore update

### Test Data Requirements

- **Test Data 1**: Sample pytest JSON reports (0% failures, 50% failures, 100% failures)
- **Test Data 2**: Sample git diff outputs (0 lines, 50 lines, 100 lines, 200 lines)
- **Test Data 3**: Sample user feedback files (correct, misclassified, unsure)

### Test Environment Requirements

- **Environment 1**: Git repository with commit history (for git diff testing)
- **Environment 2**: pytest with json-report plugin installed
- **Environment 3**: Writable `~/.agency/memories/feedback/` directory

---

## Implementation Phases

### Phase 1: Schema Definition (Week 1, Day 1-2)

- **Scope**: Pydantic models (`QualitySignals`, `SeverityLevel`, `UserFeedback`)
- **Deliverables**:
  - `shared/models/routing.py` with QualitySignals schema
  - Unit tests for Pydantic validation
  - Severity computation logic with threshold tests
- **Success Criteria**: 100% test pass, mypy type checking clean

### Phase 2: Collection Implementation (Week 1, Day 3-4)

- **Scope**: `QualitySignalCollector` class with four signal collection methods
- **Deliverables**:
  - `shared/quality_feedback_collector.py`
  - Integration with pytest JSON report and git diff
  - Unit tests for each collection method
- **Success Criteria**: Collection latency <100ms p99, graceful error handling

### Phase 3: VectorStore Integration (Week 1, Day 5)

- **Scope**: Pattern storage for CRITICAL/WARNING signals (Article IV)
- **Deliverables**:
  - `update_vectorstore_patterns()` function
  - Corrected tier inference heuristics
  - Integration tests with real VectorStore
- **Success Criteria**: CRITICAL signals stored with confidence ≥0.6

### Phase 4: Production Validation (Week 2)

- **Scope**: A/B testing on 100 tasks, threshold tuning
- **Deliverables**:
  - False positive rate <5% validation
  - Accuracy improvement measurement (80% → 90%)
  - Telemetry dashboard integration
- **Success Criteria**: >90% routing accuracy after 100 tasks

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: PlannerAgent, AdaptiveRouterAgent, QualityEnforcerAgent
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), LearningAgent (VectorStore integration)

### Review Criteria

- [x] **Completeness**: All four quality signals defined with clear thresholds
- [x] **Clarity**: Schema is Pydantic-typed with no `Dict[Any, Any]`
- [x] **Feasibility**: Collection strategy uses existing tools (pytest, git)
- [x] **Constitutional Compliance**: Article I (complete context), Article II (verification), Article IV (VectorStore)
- [x] **Quality Standards**: False positive rate <5%, accuracy >98% after 1,000 tasks

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **Constitutional Compliance**: Pending QualityEnforcer validation
- [ ] **Final Approval**: Pending after Phase 1 implementation

---

## Appendices

### Appendix A: Glossary

- **Quality Signal**: Observable metric indicating potential task misclassification (test failures, code churn, timing, user feedback)
- **Severity Level**: Classification of signal importance (CRITICAL, WARNING, INFO)
- **Code Churn**: Total lines changed (additions + deletions) after initial commit
- **Execution Time Ratio**: Actual task time / estimated time (>1.0 means overrun)
- **VectorStore Pattern**: Learned classification pattern stored for future routing decisions

### Appendix B: References

- **ADR-024**: Adaptive Model Router for 90% Cost Reduction
- **ADR-004**: Continuous Learning and Improvement (VectorStore integration mandate)
- **Article IV**: Constitutional requirement for VectorStore learning

### Appendix C: Related Documents

- **Spec**: `specs/adaptive_model_router_spec.md` (parent specification)
- **Plan**: `plan-004-quality-feedback-loop.md` (to be created after spec approval)
- **ADR**: `docs/adr/ADR-024-adaptive-model-router.md`

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification with four signals                                |
| 1.1     | 2025-10-10 | PlannerAgent   | Added Section 7: Misclassification Detection Logic (4 rules, schemas) |
| 1.2     | 2025-10-10 | PlannerAgent   | Added Section 8: VectorStore Rule Refinement (convergence, stability) |

---

## 8. VectorStore Rule Refinement (Learning Layer)

### 8.1 Overview

The `RuleRefiner` updates VectorStore classification patterns based on detected misclassifications, implementing closed-loop learning (Article IV). The system:
1. Stores misclassified task embeddings with corrected tier labels
2. Adjusts confidence scores using decay formula
3. Tunes detection thresholds to reduce false negatives
4. Enforces stability guarantees (max 3 iterations per task)
5. Rolls back changes if accuracy degrades

**Goal**: Improve adaptive router accuracy from ~85% baseline to >98% after 1,000 tasks.

### 8.2 Confidence Adjustment Formula

When a misclassification is detected, update the confidence score of related patterns in VectorStore using exponential decay with evidence accumulation:

```python
def update_confidence(
    old_confidence: float,
    new_evidence: bool,
    decay_factor: float = 0.95,
    evidence_weight: float = 0.05
) -> float:
    """Update confidence score with decay and evidence accumulation.

    Args:
        old_confidence: Existing confidence score (0.0-1.0)
        new_evidence: Whether new evidence supports pattern (True/False)
        decay_factor: Decay rate for old confidence (0.95 = 5% decay)
        evidence_weight: Weight per evidence occurrence (0.05 = 5%)

    Returns:
        Updated confidence score (0.0-1.0)

    Examples:
        >>> update_confidence(0.70, True)  # Supporting evidence
        0.715  # 0.70 * 0.95 + 0.05 = 0.715

        >>> update_confidence(0.70, False)  # Contradicting evidence
        0.665  # 0.70 * 0.95 (no evidence weight added)
    """
    decayed = old_confidence * decay_factor
    if new_evidence:
        return min(1.0, decayed + evidence_weight)
    return max(0.0, decayed)
```

**Rationale**: Exponential decay prevents stale patterns from dominating, while evidence weight ensures recent observations influence classification.

**Convergence**: After ~20 correct classifications, confidence converges to 0.95+ (assuming no contradicting evidence).

### 8.3 Threshold Tuning Strategy

When CRITICAL misclassifications are detected (test failures, high churn), adjust detection thresholds to reduce false negatives:

#### **Threshold Adjustments**

| Signal | Original Threshold | Adjusted Threshold | Condition |
|--------|-------------------|-------------------|-----------|
| test_failure_rate | >0.1 | >0.08 | After 3+ CRITICAL test failure detections |
| code_churn_lines | >100 | >90 | After 3+ CRITICAL churn detections |
| execution_time_ratio | >3.0 | >2.7 | After 3+ WARNING timing detections |

**Formula**: `new_threshold = original_threshold * 0.9` (10% reduction)

**Rationale**: Lower thresholds make detector more sensitive, catching borderline cases that previously slipped through (false negatives).

**Safeguard**: Min threshold values to prevent over-sensitivity:
- test_failure_rate: min 0.05 (5%)
- code_churn_lines: min 50 lines
- execution_time_ratio: min 2.0x

**Example**:
```python
# Initial state: test_failure_rate threshold = 0.1
# 3 CRITICAL test failure detections occur
# Tuning: 0.1 * 0.9 = 0.09 (new threshold)
# Result: Detector now catches 9% test failure rate (previously missed)
```

### 8.4 Pattern Update Strategy (VectorStore Storage)

When a misclassification is detected, store the corrected pattern in VectorStore:

#### **Storage Schema**

```python
{
    "type": "misclassification_pattern",
    "task_id": "refactor_async_handler_42",
    "task_description": "Refactor async error handler with retry logic",
    "task_embedding": [0.23, -0.45, ...],  # 1536-dim vector from text-embedding-3-small

    # Classification metadata
    "original_tier": "simple",
    "corrected_tier": "complex",
    "confidence": 0.95,

    # Detection metadata
    "detected_issues": [
        {"rule_name": "test_failure", "confidence": 0.95, "signal_value": 0.33}
    ],
    "aggregated_confidence": 0.95,

    # Learning metadata
    "iteration_count": 1,  # How many times this pattern has been refined
    "created_at": "2025-10-10T15:23:45Z",
    "last_updated_at": "2025-10-10T15:23:45Z",
    "session_id": "session_leap4_1728567825"
}
```

#### **Retrieval for Future Tasks**

When classifying a new task, query VectorStore for similar misclassification patterns:

```python
# Compute task embedding
task_embedding = openai.embeddings.create(
    model="text-embedding-3-small",
    input=task_description
).data[0].embedding

# Query VectorStore for similar patterns
similar_patterns = vector_store.similarity_search(
    embedding=task_embedding,
    filter={"type": "misclassification_pattern"},
    k=5,  # Top 5 similar patterns
    min_confidence=0.6
)

# If high similarity (cosine_similarity >0.85), use corrected tier
if similar_patterns and similar_patterns[0]["similarity"] > 0.85:
    recommended_tier = similar_patterns[0]["corrected_tier"]
    confidence = similar_patterns[0]["confidence"]
    return classification_override(recommended_tier, confidence)
```

**Embedding Model**: `text-embedding-3-small` (1536 dimensions, $0.02/1M tokens, fast)

**Similarity Threshold**: 0.85 cosine similarity (high confidence that tasks are similar)

### 8.5 Convergence Criteria

Refinement stops when routing accuracy reaches target or improvement plateaus:

#### **Success Criteria** (Stop refinement, system converged):
1. **Accuracy Target Met**: Routing accuracy >98% on 100-task validation set
2. **Improvement Plateau**: Accuracy improves <0.5% over last 100 tasks
3. **False Negative Elimination**: Complex tasks routed to simple tier <2%

#### **Failure Criteria** (Continue refinement):
1. Accuracy <98% after 1,000 tasks
2. Accuracy improving >0.5% per 100 tasks (still learning)
3. False negatives >2%

**Validation Set**: 100 tasks with known ground truth tier labels (manually labeled or from high-confidence historical data).

**Measurement**:
```python
def calculate_accuracy(validation_set: List[Task]) -> float:
    correct = sum(
        1 for task in validation_set
        if task.predicted_tier == task.ground_truth_tier
    )
    return correct / len(validation_set)

# Example:
# Iteration 1: 85% accuracy (85/100 correct)
# Iteration 2: 91% accuracy (91/100 correct) → +6%, continue
# Iteration 3: 92% accuracy (92/100 correct) → +1%, continue
# Iteration 4: 98.5% accuracy (98.5/100 correct) → CONVERGED, stop
```

### 8.6 Stability Guarantees (Prevent Oscillation)

**Problem**: Repeated refinements on the same task can cause oscillation (simple→complex→simple→...).

**Solution**: Enforce max 3 refinement iterations per task.

#### **Iteration Tracking**

```python
class RefinementHistory(BaseModel):
    task_id: str
    iteration_count: int = 0
    refinement_history: List[RefinementEntry] = Field(default_factory=list)

class RefinementEntry(BaseModel):
    timestamp: str
    original_tier: str
    corrected_tier: str
    confidence: float
    reason: str

# Example:
history = RefinementHistory(task_id="refactor_async_handler_42")
history.iteration_count = 1
history.refinement_history.append(RefinementEntry(
    timestamp="2025-10-10T15:23:45Z",
    original_tier="simple",
    corrected_tier="complex",
    confidence=0.95,
    reason="Test failure rate 33% (CRITICAL)"
))

# On 4th refinement attempt:
if history.iteration_count >= 3:
    raise MaxIterationsExceeded(
        f"Task {task_id} reached max 3 refinement iterations. "
        "Possible labeling ambiguity or model instability."
    )
```

**Oscillation Detection**:
```python
def detect_oscillation(history: RefinementHistory) -> bool:
    """Detect if task is oscillating between tiers."""
    if len(history.refinement_history) < 3:
        return False

    # Check if last 3 refinements alternate tiers
    last_3_tiers = [entry.corrected_tier for entry in history.refinement_history[-3:]]

    # Example: ["complex", "simple", "complex"] → oscillation detected
    return len(set(last_3_tiers)) == 2 and last_3_tiers[0] != last_3_tiers[1]
```

**Mitigation**: If oscillation detected, use majority vote from last 5 classifications and freeze task (no further refinement).

### 8.7 Rollback Mechanism

If accuracy degrades after refinement, restore previous VectorStore state:

#### **Accuracy Degradation Detection**

```python
def check_degradation(
    previous_accuracy: float,
    current_accuracy: float,
    threshold: float = 0.05
) -> bool:
    """Check if accuracy degraded by >5%."""
    return (previous_accuracy - current_accuracy) > threshold

# Example:
# Previous: 92% accuracy
# Current: 86% accuracy
# Degradation: 92% - 86% = 6% > 5% threshold → ROLLBACK
```

#### **VectorStore Snapshot & Restore**

```python
class VectorStoreSnapshot(BaseModel):
    snapshot_id: str
    created_at: str
    patterns: List[dict]  # All misclassification patterns
    thresholds: dict  # Detection thresholds
    accuracy_baseline: float

def create_snapshot(vector_store: VectorStore) -> VectorStoreSnapshot:
    """Create snapshot before refinement."""
    return VectorStoreSnapshot(
        snapshot_id=f"snapshot_{int(time.time())}",
        created_at=datetime.utcnow().isoformat(),
        patterns=vector_store.get_all_patterns(type="misclassification_pattern"),
        thresholds=get_current_thresholds(),
        accuracy_baseline=calculate_accuracy(validation_set)
    )

def rollback(snapshot: VectorStoreSnapshot, vector_store: VectorStore):
    """Restore VectorStore to previous state."""
    vector_store.clear_patterns(type="misclassification_pattern")

    for pattern in snapshot.patterns:
        vector_store.store_pattern(pattern)

    restore_thresholds(snapshot.thresholds)

    log_event("vectorstore_rollback", {
        "snapshot_id": snapshot.snapshot_id,
        "reason": "accuracy_degradation",
        "previous_accuracy": snapshot.accuracy_baseline
    })
```

**Rollback Trigger**: After each refinement batch (100 tasks), compare accuracy. If degraded >5%, rollback immediately.

### 8.8 Implementation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  RuleRefiner                                                │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ Confidence     │  │ Threshold      │  │ Pattern      │ │
│  │ Adjustment     │  │ Tuning         │  │ Storage      │ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
│           │                  │                    │        │
│           └──────────────────┴────────────────────┘        │
│                              │                             │
│                    ┌─────────▼─────────┐                   │
│                    │ VectorStore       │                   │
│                    │ (Misclassification│                   │
│                    │  Patterns)        │                   │
│                    └───────────────────┘                   │
│                              │                             │
│                    ┌─────────▼─────────┐                   │
│                    │ Convergence Check │                   │
│                    │ (Accuracy >98%?)  │                   │
│                    └───────────────────┘                   │
│                              │                             │
│               ┌──────────────┴──────────────┐              │
│               │ Yes                         │ No           │
│         ┌─────▼─────┐               ┌──────▼──────┐       │
│         │ Stop      │               │ Continue    │       │
│         │ Refinement│               │ Learning    │       │
│         └───────────┘               └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 8.9 Performance Requirements

- **Latency**: <50ms p99 for pattern storage (includes embedding generation + VectorStore write)
- **Throughput**: 1,000 refinements/second (batched writes to VectorStore)
- **Storage**: ~1KB per pattern (1,000 patterns = 1MB, 10,000 patterns = 10MB)

### 8.10 Testing Strategy

**Unit Tests** (10+ tests required):
1. Test confidence adjustment formula (decay + evidence weight)
2. Test threshold tuning (10% reduction after 3 detections)
3. Test pattern storage schema validation
4. Test retrieval similarity threshold (0.85 cosine similarity)
5. Test convergence detection (accuracy >98%)
6. Test max iteration enforcement (4th attempt raises error)
7. Test oscillation detection (alternating tiers)
8. Test rollback mechanism (accuracy degradation >5%)
9. Test snapshot creation and restore
10. Test graceful degradation (VectorStore query failure)

**Integration Tests** (5+ tests required):
1. E2E: MisclassificationReport → refine() → VectorStore updated
2. Convergence simulation: 1,000 tasks → accuracy 85% → 98%
3. Stability test: 100 refinements on same task → max 3 iterations enforced
4. Rollback scenario: Inject bad refinements → accuracy drops → rollback restores
5. Real-world data: Apply refinement to 100 historical misclassifications

### 8.11 Monitoring & Observability

**Metrics to Track**:
- Refinement rate: `refinements_applied / total_tasks` (target: 10% initial, <2% after convergence)
- Confidence distribution: Histogram of pattern confidences (target: mean >0.85)
- Accuracy improvement: `(current_accuracy - baseline_accuracy)` (target: +13% from 85% to 98%)
- Rollback frequency: `rollbacks / refinement_batches` (target: <1%)

**Telemetry Logging**:
```python
log_event("vectorstore_refinement", {
    "task_id": task_id,
    "original_tier": original_tier,
    "corrected_tier": corrected_tier,
    "confidence_before": old_confidence,
    "confidence_after": new_confidence,
    "iteration_count": iteration_count,
    "thresholds_adjusted": threshold_changes
})
```

### 8.12 Constitutional Compliance

**Article IV Enforcement** (MANDATORY):
- VectorStore integration is constitutionally required (no disable flags)
- All CRITICAL/WARNING misclassifications MUST be stored
- Agents MUST query learnings before classification
- Pattern accumulation enables cross-session learning

**Validation**:
```python
# Assert VectorStore enabled (Article IV)
assert os.getenv("USE_ENHANCED_MEMORY") == "true", \
    "Article IV: VectorStore integration is mandatory"

# Assert CRITICAL misclassifications stored
if report.is_misclassified and report.aggregated_confidence > 0.8:
    assert vector_store.contains(report.task_id), \
        "Article IV: CRITICAL misclassifications must be stored"
```

---

*"Quality is not an act, it is a habit. Measurement is not surveillance, it is learning."* - Quality Feedback Loop Principle
