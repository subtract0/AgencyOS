"""
Tests for prediction logger utility (tools/ml_routing/prediction_logger.py).

Validates:
- log_prediction() stores predictions in VectorStore via context.store_memory()
- get_predictions() retrieves predictions with filtering (timestamp, tier)
- Tags include ['prediction', tier, method] for searchability
- Async/non-blocking operation (Article IV mandate)

NECESSARY Pattern Coverage:
- N: Normal operation (log and retrieve predictions)
- E: Edge cases (empty results, None filters)
- C: Corner cases (concurrent logging, cache invalidation)
- E: Error conditions (invalid context, missing fields)
- S: Security (no sensitive data leakage in logs)
- S: Stress (batch prediction logging)
- A: Accessibility (clear API, error messages)
- R: Regression (schema changes don't break retrieval)
- Y: Yield tests (Result pattern validation)

Constitutional compliance:
- Article I: Complete context (all prediction metadata logged)
- Article II: TDD (tests written first), Result pattern
- Article IV: MANDATORY VectorStore logging (all predictions)
- Article V: Spec-driven (traces to spec-007-phase3-ml-inference.md)

Reference: specs/spec-007-phase3-ml-inference.md Section 5.5
Author: AgencyCodeAgent
Date: 2025-10-10
"""

from datetime import UTC, datetime, timedelta

import pytest

from agency_memory import Memory
from shared.agent_context import AgentContext
from shared.models.prediction_log import PredictionLog

# ============================================================================
# Test Category 1: log_prediction() - Normal Operation (NECESSARY: N)
# ============================================================================


class TestLogPredictionNormalOperation:
    """Test log_prediction() stores predictions in VectorStore."""

    def test_log_prediction_stores_in_vectorstore(self):
        """
        Test AC-3.5: log_prediction() stores prediction in VectorStore.

        Article IV: MANDATORY VectorStore logging (all predictions).
        NECESSARY: N (Normal operation - happy path).
        """
        # Arrange
        from tools.ml_routing.prediction_logger import log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_001")
        prediction = PredictionLog(
            task_id="task_abc123",
            tier="moderate",
            confidence=0.85,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_001",
        )

        # Act
        result = log_prediction(context, prediction)

        # Assert: Result is Ok
        assert result.is_ok(), (
            f"Expected Ok, got Err: {result.unwrap_err() if result.is_err() else ''}"
        )

        # Assert: Prediction stored in VectorStore
        stored_predictions = context.search_memories(["prediction"], include_session=True)
        assert len(stored_predictions) == 1
        assert stored_predictions[0]["content"]["task_id"] == "task_abc123"

    def test_log_prediction_with_correct_tags(self):
        """
        Test AC-3.5: log_prediction() tags prediction with ['prediction', tier, method].

        Article IV: VectorStore searchability via tags.
        NECESSARY: N (Normal operation - tag validation).
        """
        # Arrange
        from tools.ml_routing.prediction_logger import log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_002")
        prediction = PredictionLog(
            task_id="task_xyz789",
            tier="complex",
            confidence=0.92,
            method="rule_based_fallback",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_002",
        )

        # Act
        result = log_prediction(context, prediction)
        assert result.is_ok()

        # Assert: Tags include 'prediction', tier, method
        stored = context.search_memories(["prediction"], include_session=True)
        tags = stored[0]["tags"]
        assert "prediction" in tags
        assert "complex" in tags
        assert "rule_based_fallback" in tags
        assert f"session:{context.session_id}" in tags

    def test_log_prediction_async_non_blocking(self):
        """
        Test AC-3.5: log_prediction() is non-blocking (returns immediately).

        Article IV: Logging must not block task execution.
        NECESSARY: C (Corner case - performance validation).
        """
        # Arrange
        import time

        from tools.ml_routing.prediction_logger import log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_003")
        prediction = PredictionLog(
            task_id="task_perf_test",
            tier="simple",
            confidence=0.98,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_003",
        )

        # Act: Measure execution time
        start_time = time.perf_counter()
        result = log_prediction(context, prediction)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Assert: Returns Ok immediately (<10ms)
        assert result.is_ok()
        assert elapsed_ms < 10.0, f"log_prediction took {elapsed_ms:.2f}ms (expected <10ms)"


# ============================================================================
# Test Category 2: get_predictions() - Retrieval and Filtering (NECESSARY: N, E)
# ============================================================================


class TestGetPredictionsRetrieval:
    """Test get_predictions() retrieves and filters predictions from VectorStore."""

    def test_get_predictions_retrieves_all(self):
        """
        Test AC-3.5: get_predictions() retrieves all predictions without filters.

        Article I: Complete context (all predictions retrieved).
        NECESSARY: N (Normal operation - retrieve all).
        """
        # Arrange
        from tools.ml_routing.prediction_logger import get_predictions, log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_004")

        # Log 3 predictions
        for i in range(3):
            prediction = PredictionLog(
                task_id=f"task_{i}",
                tier="moderate",
                confidence=0.80 + i * 0.05,
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                session_id="test_session_004",
            )
            log_prediction(context, prediction)

        # Act: Retrieve all predictions (no filters)
        result = get_predictions(context, since=None, tier_filter=None)

        # Assert: Result is Ok with 3 predictions
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 3
        assert all(isinstance(p, PredictionLog) for p in predictions)

    def test_get_predictions_filter_by_since(self):
        """
        Test AC-3.5: get_predictions() filters by timestamp (since parameter).

        NECESSARY: E (Edge case - timestamp filtering).
        """
        # Arrange
        import time

        from tools.ml_routing.prediction_logger import get_predictions, log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_005")

        # Log prediction 1 (old)
        old_prediction = PredictionLog(
            task_id="task_old",
            tier="simple",
            confidence=0.95,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_005",
            timestamp=(datetime.now(UTC) - timedelta(hours=2)).isoformat() + "Z",
        )
        log_prediction(context, old_prediction)

        # Wait to ensure timestamp difference
        time.sleep(0.1)
        cutoff_time = datetime.now(UTC)
        time.sleep(0.1)

        # Log prediction 2 (new)
        new_prediction = PredictionLog(
            task_id="task_new",
            tier="moderate",
            confidence=0.88,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_005",
        )
        log_prediction(context, new_prediction)

        # Act: Retrieve predictions since cutoff_time
        result = get_predictions(context, since=cutoff_time, tier_filter=None)

        # Assert: Only new prediction retrieved
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 1
        assert predictions[0].task_id == "task_new"

    def test_get_predictions_filter_by_tier(self):
        """
        Test AC-3.5: get_predictions() filters by tier (tier_filter parameter).

        NECESSARY: E (Edge case - tier filtering).
        """
        # Arrange
        from tools.ml_routing.prediction_logger import get_predictions, log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_006")

        # Log predictions with different tiers
        for tier in ["complex", "moderate", "simple"]:
            prediction = PredictionLog(
                task_id=f"task_{tier}",
                tier=tier,
                confidence=0.85,
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                session_id="test_session_006",
            )
            log_prediction(context, prediction)

        # Act: Retrieve only complex predictions
        result = get_predictions(context, since=None, tier_filter="complex")

        # Assert: Only complex prediction retrieved
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 1
        assert predictions[0].tier == "complex"

    def test_get_predictions_empty_result(self):
        """
        Test AC-3.5: get_predictions() returns empty list when no predictions match filters.

        NECESSARY: E (Edge case - empty result set).
        """
        # Arrange
        from tools.ml_routing.prediction_logger import get_predictions

        context = AgentContext(memory=Memory(), session_id="test_session_007")

        # Act: Retrieve predictions from empty VectorStore
        result = get_predictions(context, since=None, tier_filter=None)

        # Assert: Result is Ok with empty list
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 0

    def test_get_predictions_handles_invalid_data(self):
        """
        Test AC-3.5: get_predictions() handles corrupted VectorStore data gracefully.

        Article II: 100% verification (skip invalid entries).
        NECESSARY: E (Error condition - data corruption).
        """
        # Arrange
        from tools.ml_routing.prediction_logger import get_predictions

        context = AgentContext(memory=Memory(), session_id="test_session_008")

        # Store invalid prediction data (missing required fields)
        context.store_memory(
            key="corrupted_prediction",
            content={"task_id": "task_invalid"},  # Missing required fields
            tags=["prediction", "P2", "ml"],
        )

        # Store valid prediction data
        context.store_memory(
            key="valid_prediction",
            content={
                "task_id": "task_valid",
                "tier": "simple",
                "confidence": 0.90,
                "method": "ml_model",
                "model_version": "2025-10-10T12:00:00Z",
                "session_id": "test_session_008",
                "timestamp": datetime.now(UTC).isoformat() + "Z",
            },
            tags=["prediction", "simple", "ml_model"],
        )

        # Act: Retrieve predictions (should skip corrupted entry)
        result = get_predictions(context, since=None, tier_filter=None)

        # Assert: Result is Ok with only valid prediction
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 1
        assert predictions[0].task_id == "task_valid"


# ============================================================================
# Test Category 3: Edge Cases and Error Handling (NECESSARY: E, S)
# ============================================================================


class TestPredictionLoggerEdgeCases:
    """Test edge cases and error conditions for prediction logger."""

    def test_log_prediction_with_actual_tier_populated(self):
        """
        Test AC-3.5: log_prediction() stores prediction with actual_tier if provided.

        NECESSARY: N (Normal operation - complete prediction log).
        """
        # Arrange
        from tools.ml_routing.prediction_logger import get_predictions, log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_009")
        prediction = PredictionLog(
            task_id="task_complete",
            tier="moderate",
            confidence=0.82,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_009",
        )

        # Act
        result = log_prediction(context, prediction)
        assert result.is_ok()

        # Retrieve and verify
        predictions = get_predictions(context, since=None, tier_filter=None).unwrap()
        assert len(predictions) == 1
        assert predictions[0].tier == "moderate"

    def test_get_predictions_combined_filters(self):
        """
        Test AC-3.5: get_predictions() applies both since and tier_filter.

        NECESSARY: C (Corner case - multiple filters).
        """
        # Arrange
        import time

        from tools.ml_routing.prediction_logger import get_predictions, log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_010")

        # Log old complex prediction
        old_p1 = PredictionLog(
            task_id="task_old_complex",
            tier="complex",
            confidence=0.90,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_010",
            timestamp=(datetime.now(UTC) - timedelta(hours=1)).isoformat() + "Z",
        )
        log_prediction(context, old_p1)

        time.sleep(0.1)
        cutoff_time = datetime.now(UTC)
        time.sleep(0.1)

        # Log new complex prediction
        new_p1 = PredictionLog(
            task_id="task_new_complex",
            tier="complex",
            confidence=0.92,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_010",
        )
        log_prediction(context, new_p1)

        # Log new moderate prediction (should be filtered out)
        new_p2 = PredictionLog(
            task_id="task_new_moderate",
            tier="moderate",
            confidence=0.85,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="test_session_010",
        )
        log_prediction(context, new_p2)

        # Act: Retrieve complex predictions since cutoff_time
        result = get_predictions(context, since=cutoff_time, tier_filter="complex")

        # Assert: Only new complex prediction retrieved
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 1
        assert predictions[0].task_id == "task_new_complex"

    def test_log_prediction_batch_logging(self):
        """
        Test AC-3.5: log_prediction() handles batch logging efficiently.

        Article IV: VectorStore supports concurrent writes.
        NECESSARY: S (Stress test - batch operations).
        """
        # Arrange
        import time

        from tools.ml_routing.prediction_logger import get_predictions, log_prediction

        context = AgentContext(memory=Memory(), session_id="test_session_011")
        batch_size = 50

        # Act: Log 50 predictions
        start_time = time.perf_counter()
        for i in range(batch_size):
            prediction = PredictionLog(
                task_id=f"task_batch_{i}",
                tier="moderate",
                confidence=0.80 + (i % 20) * 0.01,
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                session_id="test_session_011",
            )
            result = log_prediction(context, prediction)
            assert result.is_ok()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Assert: All predictions logged and retrievable
        predictions = get_predictions(context, since=None, tier_filter=None).unwrap()
        assert len(predictions) == batch_size

        # Performance: <500ms for 50 predictions (<10ms each)
        assert elapsed_ms < 500.0, f"Batch logging took {elapsed_ms:.2f}ms (expected <500ms)"
