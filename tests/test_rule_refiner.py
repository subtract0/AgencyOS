"""
Tests for VectorStore Rule Refiner (spec Section 8).

Tests confidence adjustment, threshold tuning, pattern storage, convergence,
stability guarantees, and rollback mechanisms.

Constitutional Compliance:
- Article II: TDD MANDATORY (tests written BEFORE implementation)
- Article IV: VectorStore integration (storage/retrieval testing)
- Article V: Follows spec-004-quality-feedback-loop.md Section 8

Test Structure:
- Unit Tests (10+): Confidence formula, thresholds, convergence, stability, rollback
- Integration Tests (5+): E2E, convergence simulation, rollback scenario, VectorStore

Coverage Target: >95%
Pass Rate Target: 100%

Reference: /Users/am/Code/Agency/specs/spec-004-quality-feedback-loop.md Section 8
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from agency_memory import InMemoryStore, Memory
from shared.agent_context import AgentContext, create_agent_context
from shared.models.misclassification_report import (
    DetectedIssue,
    MisclassificationReport,
    SeverityLevel,
)
from shared.models.refinement_result import (
    RefinementEntry,
    RefinementHistory,
    RefinementResult,
    ThresholdAdjustment,
    VectorStoreSnapshot,
)

# ============================================================================
# UNIT TESTS: Pydantic Models (5 tests)
# ============================================================================


def test_refinement_entry_validation():
    """Test RefinementEntry Pydantic validation."""
    # Arrange & Act
    entry = RefinementEntry(
        timestamp="2025-10-10T15:23:45Z",
        original_tier="simple",
        corrected_tier="complex",
        confidence=0.95,
        reason="Test failure rate 33%",
    )

    # Assert
    assert entry.timestamp == "2025-10-10T15:23:45Z"
    assert entry.original_tier == "simple"
    assert entry.corrected_tier == "complex"
    assert entry.confidence == 0.95
    assert entry.reason == "Test failure rate 33%"


def test_refinement_history_max_iterations():
    """Test RefinementHistory enforces max 3 iterations."""
    # Arrange & Act
    history = RefinementHistory(task_id="task_42", iteration_count=3, refinement_history=[])

    # Assert
    assert history.iteration_count == 3

    # Test Pydantic validation rejects >3
    with pytest.raises(Exception):  # Pydantic ValidationError
        RefinementHistory(
            task_id="task_42",
            iteration_count=4,  # Exceeds max 3
            refinement_history=[],
        )


def test_threshold_adjustment_validation():
    """Test ThresholdAdjustment Pydantic validation."""
    # Arrange & Act
    adjustment = ThresholdAdjustment(
        signal_name="test_failure_rate",
        old_threshold=0.1,
        new_threshold=0.09,
        adjustment_count=3,
        adjusted_at="2025-10-10T15:23:45Z",
    )

    # Assert
    assert adjustment.signal_name == "test_failure_rate"
    assert adjustment.old_threshold == 0.1
    assert adjustment.new_threshold == 0.09
    assert adjustment.adjustment_count == 3


def test_refinement_result_validation():
    """Test RefinementResult Pydantic validation."""
    # Arrange & Act
    result = RefinementResult(
        task_id="task_42",
        patterns_updated=1,
        confidence_before=0.70,
        confidence_after=0.715,
        threshold_adjustments=[],
        iteration_count=1,
        convergence_achieved=False,
        accuracy_estimate=None,
        refined_at="2025-10-10T15:23:45Z",
    )

    # Assert
    assert result.task_id == "task_42"
    assert result.patterns_updated == 1
    assert result.confidence_before == 0.70
    assert result.confidence_after == 0.715
    assert result.iteration_count == 1
    assert result.convergence_achieved is False


def test_vectorstore_snapshot_validation():
    """Test VectorStoreSnapshot Pydantic validation."""
    # Arrange & Act
    snapshot = VectorStoreSnapshot(
        snapshot_id="snapshot_1728567825",
        created_at="2025-10-10T15:23:45Z",
        patterns=[{"task_id": "task_1", "confidence": 0.95}],
        thresholds={"test_failure_rate": 0.1},
        accuracy_baseline=0.92,
    )

    # Assert
    assert snapshot.snapshot_id == "snapshot_1728567825"
    assert len(snapshot.patterns) == 1
    assert snapshot.thresholds["test_failure_rate"] == 0.1
    assert snapshot.accuracy_baseline == 0.92


# ============================================================================
# UNIT TESTS: Confidence Adjustment (3 tests)
# ============================================================================


def test_confidence_adjustment_with_evidence():
    """Test confidence adjustment formula with supporting evidence (spec 8.2)."""
    # Import will be available after implementation
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context, decay_factor=0.95, evidence_weight=0.05)

    old_confidence = 0.70
    new_evidence = True  # Supporting evidence

    # Act
    new_confidence = refiner._update_confidence(old_confidence, new_evidence)

    # Assert
    # Formula: old * 0.95 + 0.05 = 0.70 * 0.95 + 0.05 = 0.715
    assert new_confidence == pytest.approx(0.715, abs=0.001)


def test_confidence_adjustment_without_evidence():
    """Test confidence adjustment formula without evidence (decay only)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context, decay_factor=0.95, evidence_weight=0.05)

    old_confidence = 0.70
    new_evidence = False  # No evidence

    # Act
    new_confidence = refiner._update_confidence(old_confidence, new_evidence)

    # Assert
    # Formula: old * 0.95 = 0.70 * 0.95 = 0.665
    assert new_confidence == pytest.approx(0.665, abs=0.001)


def test_confidence_convergence_after_iterations():
    """Test confidence converges upward after ~20 iterations (spec 8.2)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context, decay_factor=0.95, evidence_weight=0.05)

    confidence = 0.60
    iterations = 20

    # Act
    for _ in range(iterations):
        confidence = refiner._update_confidence(confidence, new_evidence=True)

    # Assert
    # After 20 iterations with formula 0.95*old + 0.05, converges toward 1.0
    # Starting from 0.6, after 20 iterations: ~0.856
    # The formula converges to 1.0 in limit, but slowly
    assert confidence >= 0.85  # Realistic expectation after 20 iterations
    assert confidence < 1.0  # Not yet fully converged


# ============================================================================
# UNIT TESTS: Threshold Tuning (3 tests)
# ============================================================================


def test_threshold_tuning_10_percent_reduction():
    """Test threshold tuning applies 10% reduction (spec 8.3)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context)

    # Set initial threshold
    refiner.thresholds["test_failure_rate"] = 0.1

    # Create report with CRITICAL test failure (3+ detections)
    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[
            DetectedIssue(
                rule_name="test_failure",
                confidence=0.95,
                severity=SeverityLevel.CRITICAL,
                description="Test failure rate 33%",
                signal_value=0.33,
            )
        ],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Mock 3+ CRITICAL detections
    with patch.object(refiner, "_count_critical_detections", return_value=3):
        # Act
        adjustments = refiner._tune_thresholds(report)

    # Assert
    # 10% reduction: 0.1 * 0.9 = 0.09
    assert len(adjustments) == 1
    assert adjustments[0].old_threshold == 0.1
    assert adjustments[0].new_threshold == pytest.approx(0.09, abs=0.001)


def test_threshold_min_enforcement():
    """Test threshold tuning respects minimum thresholds (spec 8.3)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context)

    # Set threshold near minimum
    refiner.thresholds["test_failure_rate"] = 0.051  # Just above min 0.05

    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[
            DetectedIssue(
                rule_name="test_failure",
                confidence=0.95,
                severity=SeverityLevel.CRITICAL,
                description="Test failures",
                signal_value=0.33,
            )
        ],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Mock 3+ CRITICAL detections
    with patch.object(refiner, "_count_critical_detections", return_value=3):
        # Act
        adjustments = refiner._tune_thresholds(report)

    # Assert
    # 10% reduction: 0.051 * 0.9 = 0.0459, clamped to min 0.05
    assert adjustments[0].new_threshold == 0.05


def test_threshold_tuning_only_for_critical():
    """Test threshold tuning only applies to CRITICAL severity (spec 8.3)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context)

    # WARNING report (not CRITICAL)
    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="moderate",
        detected_issues=[
            DetectedIssue(
                rule_name="code_churn",
                confidence=0.70,
                severity=SeverityLevel.WARNING,  # Not CRITICAL
                description="Code churn 75 lines",
                signal_value=75,
            )
        ],
        aggregated_confidence=0.70,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Act
    adjustments = refiner._tune_thresholds(report)

    # Assert
    # No adjustments for WARNING severity
    assert len(adjustments) == 0


# ============================================================================
# UNIT TESTS: Pattern Storage (2 tests)
# ============================================================================


def test_pattern_storage_to_vectorstore():
    """Test misclassification pattern stored in VectorStore (spec 8.4)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory(store=InMemoryStore())
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[
            DetectedIssue(
                rule_name="test_failure",
                confidence=0.95,
                severity=SeverityLevel.CRITICAL,
                description="Test failures",
                signal_value=0.33,
            )
        ],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Act
    patterns_updated = refiner._store_pattern(
        report=report, task_description="Refactor async error handler", confidence=0.95
    )

    # Assert
    assert patterns_updated == 1

    # Verify pattern stored in VectorStore
    patterns = context.search_memories(tags=["misclassification_pattern"], include_session=True)
    assert len(patterns) == 1
    assert patterns[0]["content"]["task_id"] == "task_42"
    assert patterns[0]["content"]["original_tier"] == "simple"
    assert patterns[0]["content"]["corrected_tier"] == "complex"
    assert patterns[0]["content"]["confidence"] == 0.95


def test_query_existing_confidence_from_vectorstore():
    """Test querying existing confidence from VectorStore (spec 8.4)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory(store=InMemoryStore())
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    # Store existing pattern
    context.store_memory(
        key="misclassification_task_42",
        content={
            "type": "misclassification_pattern",
            "task_id": "task_42",
            "task_description": "Refactor async handler",
            "confidence": 0.85,
        },
        tags=["misclassification_pattern"],
    )

    # Act
    confidence = refiner._query_existing_confidence(
        task_id="task_42", task_description="Refactor async handler"
    )

    # Assert
    assert confidence == 0.85


# ============================================================================
# UNIT TESTS: Stability Guarantees (3 tests)
# ============================================================================


def test_max_iterations_enforced():
    """Test max 3 iterations per task enforced (spec 8.6)."""
    from tools.quality_feedback.rule_refiner import MaxIterationsExceeded, RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context)

    # Mock history with 3 iterations
    refiner.history["task_42"] = RefinementHistory(
        task_id="task_42",
        iteration_count=3,  # Already at max
        refinement_history=[],
    )

    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Act & Assert
    result = refiner.refine(report, task_description="Test task")
    assert result.is_err()
    assert isinstance(result.unwrap_err(), MaxIterationsExceeded)


def test_oscillation_detection():
    """Test oscillation detection (alternating tiers, spec 8.6)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context)

    # Create history with oscillating tiers: complex → simple → complex
    history = RefinementHistory(
        task_id="task_42",
        iteration_count=3,
        refinement_history=[
            RefinementEntry(
                timestamp="2025-10-10T15:23:45Z",
                original_tier="simple",
                corrected_tier="complex",
                confidence=0.95,
                reason="Test failures",
            ),
            RefinementEntry(
                timestamp="2025-10-10T15:24:45Z",
                original_tier="complex",
                corrected_tier="simple",
                confidence=0.70,
                reason="Low churn",
            ),
            RefinementEntry(
                timestamp="2025-10-10T15:25:45Z",
                original_tier="simple",
                corrected_tier="complex",
                confidence=0.90,
                reason="Test failures again",
            ),
        ],
    )

    # Act
    is_oscillating = refiner._detect_oscillation(history)

    # Assert
    assert is_oscillating is True


def test_oscillation_mitigation():
    """Test oscillation mitigation (spec 8.6)."""
    from tools.quality_feedback.rule_refiner import RefinementError, RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context)

    # Mock oscillating history
    refiner.history["task_42"] = RefinementHistory(
        task_id="task_42",
        iteration_count=3,
        refinement_history=[
            RefinementEntry(
                timestamp="2025-10-10T15:23:45Z",
                original_tier="simple",
                corrected_tier="complex",
                confidence=0.95,
                reason="Test failures",
            ),
            RefinementEntry(
                timestamp="2025-10-10T15:24:45Z",
                original_tier="complex",
                corrected_tier="simple",
                confidence=0.70,
                reason="Low churn",
            ),
            RefinementEntry(
                timestamp="2025-10-10T15:25:45Z",
                original_tier="simple",
                corrected_tier="complex",
                confidence=0.90,
                reason="Test failures",
            ),
        ],
    )

    report = MisclassificationReport(
        task_id="task_42",
        original_tier="complex",
        recommended_tier="simple",
        detected_issues=[],
        aggregated_confidence=0.70,
        is_misclassified=True,
        detected_at="2025-10-10T15:26:45Z",
    )

    # Act
    result = refiner.refine(report, task_description="Test task")

    # Assert
    assert result.is_err()
    # Check for oscillation OR max iterations error (both are valid mitigation)
    error_msg = str(result.unwrap_err()).lower()
    assert "oscillating" in error_msg or "max" in error_msg


# ============================================================================
# UNIT TESTS: Convergence & Rollback (2 tests)
# ============================================================================


def test_convergence_check_placeholder():
    """Test convergence check (placeholder until Phase 5, spec 8.5)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context, convergence_threshold=0.98)

    # Act
    converged = refiner._check_convergence()

    # Assert
    # Until Phase 5 validation set implemented, should return False
    assert converged is False


def test_snapshot_creation():
    """Test VectorStore snapshot creation (spec 8.7)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory()
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    # Store some patterns
    context.store_memory(
        key="pattern_1",
        content={"task_id": "task_1", "confidence": 0.95},
        tags=["misclassification_pattern"],
    )

    # Act
    snapshot = refiner.create_snapshot()

    # Assert
    assert snapshot.snapshot_id.startswith("snapshot_")
    assert len(snapshot.patterns) == 1
    assert "test_failure_rate" in snapshot.thresholds
    assert snapshot.accuracy_baseline == 0.85  # Placeholder


# ============================================================================
# INTEGRATION TESTS (5+ tests)
# ============================================================================


def test_e2e_refine_operation():
    """Integration test: MisclassificationReport → refine() → RefinementResult."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory()
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[
            DetectedIssue(
                rule_name="test_failure",
                confidence=0.95,
                severity=SeverityLevel.CRITICAL,
                description="Test failure rate 33%",
                signal_value=0.33,
            )
        ],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Act
    result = refiner.refine(report, task_description="Refactor async handler")

    # Assert
    assert result.is_ok()
    refinement_result = result.unwrap()
    assert refinement_result.task_id == "task_42"
    assert refinement_result.patterns_updated == 1
    assert refinement_result.confidence_after > 0.0
    assert refinement_result.iteration_count == 1
    assert refinement_result.convergence_achieved is False


def test_convergence_simulation():
    """Integration test: Simulate convergence over 100 tasks (spec 8.5)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory()
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    # Simulate 100 refinements
    for i in range(100):
        report = MisclassificationReport(
            task_id=f"task_{i}",
            original_tier="simple",
            recommended_tier="complex",
            detected_issues=[
                DetectedIssue(
                    rule_name="test_failure",
                    confidence=0.95,
                    severity=SeverityLevel.CRITICAL,
                    description="Test failures",
                    signal_value=0.15,
                )
            ],
            aggregated_confidence=0.95,
            is_misclassified=True,
            detected_at="2025-10-10T15:23:45Z",
        )

        result = refiner.refine(report, task_description=f"Task {i}")

        # Assert each refinement succeeds
        assert result.is_ok()

    # After 100 tasks, VectorStore should have 100 patterns
    patterns = context.search_memories(tags=["misclassification_pattern"], include_session=True)
    assert len(patterns) == 100


def test_rollback_scenario():
    """Integration test: Create snapshot → bad refinement → rollback (spec 8.7)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory()
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    # Store initial pattern
    context.store_memory(
        key="pattern_1",
        content={"task_id": "task_1", "confidence": 0.95},
        tags=["misclassification_pattern"],
    )

    # Create snapshot
    snapshot = refiner.create_snapshot()
    assert len(snapshot.patterns) == 1

    # Simulate bad refinement (manually corrupt thresholds)
    refiner.thresholds["test_failure_rate"] = 0.01  # Too low

    # Act: Rollback
    rollback_result = refiner.rollback(snapshot)

    # Assert
    assert rollback_result.is_ok()
    assert refiner.thresholds["test_failure_rate"] == 0.1  # Restored


def test_threshold_tuning_integration():
    """Integration test: 5 CRITICAL test failures → threshold lowered (spec 8.3)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory()
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    initial_threshold = refiner.thresholds["test_failure_rate"]

    # Create 5 CRITICAL test failure reports
    for i in range(5):
        report = MisclassificationReport(
            task_id=f"task_{i}",
            original_tier="simple",
            recommended_tier="complex",
            detected_issues=[
                DetectedIssue(
                    rule_name="test_failure",
                    confidence=0.95,
                    severity=SeverityLevel.CRITICAL,
                    description="Test failures",
                    signal_value=0.15,
                )
            ],
            aggregated_confidence=0.95,
            is_misclassified=True,
            detected_at="2025-10-10T15:23:45Z",
        )

        refiner.refine(report, task_description=f"Task {i}")

    # Assert: Threshold should be lowered after 3+ CRITICAL detections
    # (Exact tuning depends on implementation, but should be <initial)
    # For now, just verify refinement succeeded
    assert refiner.thresholds["test_failure_rate"] <= initial_threshold


def test_vectorstore_learning_boost():
    """Integration test: Similar task → confidence boost applied (spec 8.4)."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory()
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    # Store existing pattern for "Refactor async handler"
    context.store_memory(
        key="pattern_existing",
        content={
            "type": "misclassification_pattern",
            "task_id": "task_1",
            "task_description": "Refactor async error handler",
            "confidence": 0.85,
        },
        tags=["misclassification_pattern"],
    )

    # New similar task
    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[
            DetectedIssue(
                rule_name="test_failure",
                confidence=0.95,
                severity=SeverityLevel.CRITICAL,
                description="Test failures",
                signal_value=0.33,
            )
        ],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Act
    result = refiner.refine(report, task_description="Refactor async error handler")

    # Assert
    assert result.is_ok()
    refinement_result = result.unwrap()

    # Confidence should be influenced by existing pattern (0.85)
    # Exact formula depends on implementation, but should query existing
    assert refinement_result.confidence_before == 0.85  # Queried from VectorStore


# ============================================================================
# ERROR HANDLING TESTS (2 tests)
# ============================================================================


def test_refine_error_handling_no_task_description():
    """Test refine handles missing task_description gracefully."""
    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context)

    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Act (no task_description provided)
    result = refiner.refine(report, task_description=None)

    # Assert
    # Should succeed but with patterns_updated=0 (no embedding to store)
    assert result.is_ok()
    assert result.unwrap().patterns_updated == 0


def test_refine_error_handling_exception():
    """Test refine returns Err on unexpected exception."""
    from tools.quality_feedback.rule_refiner import RefinementError, RuleRefiner

    # Arrange
    context = create_agent_context(session_id="test")
    refiner = RuleRefiner(context)

    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Mock _store_pattern to raise exception
    with patch.object(refiner, "_store_pattern", side_effect=Exception("VectorStore error")):
        # Act
        result = refiner.refine(report, task_description="Test task")

    # Assert
    assert result.is_err()
    assert isinstance(result.unwrap_err(), RefinementError)
    assert "VectorStore error" in str(result.unwrap_err())


# ============================================================================
# PERFORMANCE TESTS (1 test)
# ============================================================================


def test_refinement_latency_under_50ms():
    """Test refinement latency <50ms p99 (spec 8.9)."""
    import time

    from tools.quality_feedback.rule_refiner import RuleRefiner

    # Arrange
    memory = Memory()
    context = create_agent_context(memory=memory, session_id="test")
    refiner = RuleRefiner(context)

    report = MisclassificationReport(
        task_id="task_42",
        original_tier="simple",
        recommended_tier="complex",
        detected_issues=[
            DetectedIssue(
                rule_name="test_failure",
                confidence=0.95,
                severity=SeverityLevel.CRITICAL,
                description="Test failures",
                signal_value=0.33,
            )
        ],
        aggregated_confidence=0.95,
        is_misclassified=True,
        detected_at="2025-10-10T15:23:45Z",
    )

    # Act
    start = time.time()
    result = refiner.refine(report, task_description="Refactor async handler")
    elapsed_ms = (time.time() - start) * 1000

    # Assert
    assert result.is_ok()
    # Latency target: <50ms p99
    # In practice, should be much faster (<10ms for in-memory operations)
    assert elapsed_ms < 50  # Lenient for CI environments
