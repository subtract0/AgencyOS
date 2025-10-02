"""
Comprehensive test suite for pattern_detector.

Tests pattern detection, confidence scoring, adaptive thresholds,
metadata bonuses, and pluggable detector architecture.

Constitutional Compliance:
- Article I: Complete test coverage before implementation
- Article II: 100% test success required
- TDD Mandate: Tests written before implementation
"""

import pytest
from typing import Dict, Any, List, Optional
from shared.pattern_detector import (
    PatternDetector,
    Pattern,
    PatternMatch,
    PatternType,
    PATTERN_HEURISTICS,
    BASE_CONFIDENCE,
)


class TestPatternDetectorBasics:
    """Test basic pattern detection functionality."""

    def test_detects_critical_error_pattern(self):
        """Should detect critical error with high confidence."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal error: ModuleNotFoundError in startup.py"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "critical_error"
        assert result.pattern_type == "failure"
        assert result.confidence >= 0.7
        assert "fatal" in result.keywords_matched
        assert "modulenotfounderror" in result.keywords_matched

    def test_detects_performance_regression(self):
        """Should detect performance regression pattern."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Test timeout exceeded limit: duration_s=15.2"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "performance_regression"
        assert result.pattern_type == "failure"
        assert "timeout" in result.keywords_matched
        assert "duration_s" in result.keywords_matched

    def test_detects_flaky_test(self):
        """Should detect flaky test pattern."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Test failed with AssertionError, sometimes passes (flaky)"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "flaky_test"
        assert result.pattern_type == "failure"
        assert "flaky" in result.keywords_matched

    def test_detects_constitutional_violation(self):
        """Should detect constitutional violation pattern."""
        # Arrange
        detector = PatternDetector(min_confidence=0.6)
        event = "Code uses Dict[Any, Any] with bypass flag, > 50 lines"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "constitutional_violation"
        assert result.pattern_type == "opportunity"
        assert "dict[any" in result.keywords_matched
        assert "bypass" in result.keywords_matched

    def test_detects_missing_tests(self):
        """Should detect missing tests pattern."""
        # Arrange
        detector = PatternDetector(min_confidence=0.6)
        event = "No tests found for module, coverage low at 0%"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "missing_tests"
        assert result.pattern_type == "opportunity"

    def test_detects_feature_request(self):
        """Should detect feature request user intent."""
        # Arrange
        detector = PatternDetector(min_confidence=0.5)
        event = "I need this feature, can we add auto-save functionality?"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "feature_request"
        assert result.pattern_type == "user_intent"
        assert "i need" in result.keywords_matched
        assert "can we add" in result.keywords_matched

    def test_returns_none_for_no_pattern_match(self):
        """Should return None when no pattern matches above threshold."""
        # Arrange
        detector = PatternDetector(min_confidence=0.9)
        event = "Normal log message with no issues"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is None

    def test_case_insensitive_matching(self):
        """Should match patterns case-insensitively."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "FATAL ERROR: CRASH IN MODULE"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "critical_error"


class TestMetadataBonus:
    """Test metadata bonus calculations."""

    def test_critical_error_metadata_bonus(self):
        """Should apply bonus for critical error metadata."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal error occurred"
        metadata = {"error_type": "ModuleNotFoundError"}

        # Act
        result = detector.detect(event, metadata)

        # Assert
        assert result is not None
        assert result.confidence > detector.detect(event).confidence

    def test_missing_tests_file_metadata_bonus(self):
        """Should apply bonus when file has no test in name."""
        # Arrange
        detector = PatternDetector(min_confidence=0.6)
        event = "No tests found"
        metadata = {"file": "src/utils.py"}

        # Act
        result = detector.detect(event, metadata)

        # Assert
        assert result is not None
        # Confidence should be higher with metadata
        base_result = detector.detect(event)
        assert result.confidence > base_result.confidence

    def test_priority_metadata_bonus(self):
        """Should apply bonus for CRITICAL priority."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Error in module"
        metadata = {"priority": "CRITICAL"}

        # Act
        result_with_priority = detector.detect(event, metadata)
        result_without = detector.detect(event)

        # Assert
        assert result_with_priority is not None
        if result_without:
            assert result_with_priority.confidence > result_without.confidence


class TestAdaptiveThresholds:
    """Test adaptive threshold functionality."""

    def test_threshold_reduction_after_occurrences(self):
        """Should reduce threshold after min_occurrences reached."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal crash occurred"

        # Act - Trigger critical_error multiple times
        for _ in range(3):
            detector.detect(event)

        # Assert - Next detection should have lower threshold
        threshold = detector._get_adaptive_threshold("critical_error")
        assert threshold < detector.min_confidence

    def test_constitutional_violation_no_threshold_reduction(self):
        """Should NOT reduce threshold for constitutional violations."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Dict[Any, Any] detected"

        # Act
        detector.detect(event)

        # Assert - Threshold should remain same (reduction=0.0)
        threshold = detector._get_adaptive_threshold("constitutional_violation")
        assert threshold == detector.min_confidence

    def test_pattern_history_tracking(self):
        """Should track pattern occurrence history."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        events = [
            "Fatal crash",
            "Fatal error",
            "Crash occurred",
        ]

        # Act
        for event in events:
            detector.detect(event)

        # Assert
        assert detector.pattern_history.get("critical_error", 0) > 0


class TestPatternStats:
    """Test pattern statistics functionality."""

    def test_get_pattern_stats_empty(self):
        """Should return empty stats for new detector."""
        # Arrange
        detector = PatternDetector()

        # Act
        stats = detector.get_pattern_stats()

        # Assert
        assert stats["total_detections"] == 0
        assert stats["unique_patterns"] == 0
        assert stats["pattern_counts"] == {}
        assert stats["most_common"] == []

    def test_get_pattern_stats_with_detections(self):
        """Should return accurate stats after detections."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        events = [
            "Fatal crash",
            "Fatal error",
            "Test timeout",
            "Fatal crash again",
        ]

        # Act
        for event in events:
            detector.detect(event)

        stats = detector.get_pattern_stats()

        # Assert
        assert stats["total_detections"] > 0
        assert stats["unique_patterns"] > 0
        assert len(stats["most_common"]) > 0
        # critical_error should be most common (3 occurrences)
        assert stats["most_common"][0][0] == "critical_error"

    def test_reset_history(self):
        """Should clear pattern history on reset."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        detector.detect("Fatal crash")

        # Act
        detector.reset_history()

        # Assert
        assert len(detector.pattern_history) == 0
        stats = detector.get_pattern_stats()
        assert stats["total_detections"] == 0


class TestConfidenceCalculation:
    """Test confidence score calculations."""

    def test_confidence_combines_base_and_keyword_scores(self):
        """Should combine base confidence with keyword scores."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal crash with traceback"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        # Confidence is min(1.0, base + keyword) so check capped value
        assert result.confidence == min(1.0, result.base_score + result.keyword_score)
        assert result.base_score == BASE_CONFIDENCE["failure"]
        assert result.keyword_score > 0

    def test_confidence_capped_at_1_0(self):
        """Should cap confidence at 1.0 maximum."""
        # Arrange
        detector = PatternDetector(min_confidence=0.5)
        # Event with many high-weight keywords
        event = "Fatal crash with exception traceback and SystemExit"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.confidence <= 1.0

    def test_best_match_wins(self):
        """Should return pattern with highest confidence."""
        # Arrange
        detector = PatternDetector(min_confidence=0.5)
        # Event that could match multiple patterns
        event = "API error 500: timeout exceeded"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        # Should pick the best match based on confidence


class TestCustomMinConfidence:
    """Test custom minimum confidence thresholds."""

    def test_respects_custom_min_confidence(self):
        """Should only return matches above custom threshold."""
        # Arrange
        high_threshold = PatternDetector(min_confidence=0.9)
        low_threshold = PatternDetector(min_confidence=0.5)
        event = "Test failed sometimes"

        # Act
        high_result = high_threshold.detect(event)
        low_result = low_threshold.detect(event)

        # Assert
        # High threshold might miss it, low threshold should catch it
        assert low_result is not None
        if high_result is None:
            assert low_result.confidence < 0.9

    def test_default_min_confidence_is_0_7(self):
        """Should use 0.7 as default min_confidence."""
        # Arrange & Act
        detector = PatternDetector()

        # Assert
        assert detector.min_confidence == 0.7


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_event_text(self):
        """Should handle empty event text gracefully."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)

        # Act
        result = detector.detect("")

        # Assert
        assert result is None

    def test_very_long_event_text(self):
        """Should handle very long event text."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal error " * 1000

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "critical_error"

    def test_special_characters_in_event(self):
        """Should handle special characters in event text."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal error: <script>alert('xss')</script>"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "critical_error"

    def test_none_metadata(self):
        """Should handle None metadata gracefully."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal crash"

        # Act
        result = detector.detect(event, metadata=None)

        # Assert
        assert result is not None

    def test_empty_metadata(self):
        """Should handle empty metadata dict."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal crash"

        # Act
        result = detector.detect(event, metadata={})

        # Assert
        assert result is not None


class TestAllPatternTypes:
    """Test that all pattern types are detectable."""

    def test_all_failure_patterns_detectable(self):
        """Should detect all failure pattern types."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        failure_events = {
            "critical_error": "Fatal ModuleNotFoundError crash",
            "performance_regression": "Timeout exceeded limit, slow performance",
            "flaky_test": "Test failed with AssertionError, flaky behavior",
            "integration_failure": "API error 500, connection refused to Firebase",
        }

        # Act & Assert
        for expected_pattern, event in failure_events.items():
            result = detector.detect(event)
            assert result is not None, f"Failed to detect {expected_pattern}"
            assert result.pattern_name == expected_pattern
            assert result.pattern_type == "failure"

    def test_all_opportunity_patterns_detectable(self):
        """Should detect all opportunity pattern types."""
        # Arrange
        detector = PatternDetector(min_confidence=0.6)
        opportunity_events = {
            "constitutional_violation": "Dict[Any used with no-verify bypass",
            "code_duplication": "Similar code detected, DRY violation with copy-paste",
            "missing_tests": "No tests found, 0% coverage, untested code",
            "type_safety": "Untyped variable with Any type, missing type hints",
        }

        # Act & Assert
        for expected_pattern, event in opportunity_events.items():
            result = detector.detect(event)
            assert result is not None, f"Failed to detect {expected_pattern}"
            assert result.pattern_name == expected_pattern
            assert result.pattern_type == "opportunity"

    def test_all_user_intent_patterns_detectable(self):
        """Should detect all user_intent pattern types."""
        # Arrange
        detector = PatternDetector(min_confidence=0.5)
        intent_events = {
            "recurring_topic": "Topic mentioned >3x, repeated again, frequently discussed",
            "feature_request": "I need this feature, can we add new feature please",
            "workflow_bottleneck": "This is tedious, I always manually do repetitive task",
            "frustration_signal": "Why doesn't this work? Confused and frustrated",
        }

        # Act & Assert
        for expected_pattern, event in intent_events.items():
            result = detector.detect(event)
            assert result is not None, f"Failed to detect {expected_pattern}"
            assert result.pattern_name == expected_pattern
            assert result.pattern_type == "user_intent"


class TestPatternMatchDataclass:
    """Test PatternMatch dataclass structure."""

    def test_pattern_match_has_required_fields(self):
        """Should have all required fields in PatternMatch."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal crash"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert hasattr(result, "pattern_type")
        assert hasattr(result, "pattern_name")
        assert hasattr(result, "confidence")
        assert hasattr(result, "keywords_matched")
        assert hasattr(result, "base_score")
        assert hasattr(result, "keyword_score")

    def test_keywords_matched_is_list(self):
        """Should return list of matched keywords."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)
        event = "Fatal crash with exception"

        # Act
        result = detector.detect(event)

        # Assert
        assert result is not None
        assert isinstance(result.keywords_matched, list)
        assert len(result.keywords_matched) > 0
        assert all(isinstance(k, str) for k in result.keywords_matched)


class TestPydanticPattern:
    """Test Pydantic Pattern model."""

    def test_pattern_model_validation(self):
        """Should validate Pattern model fields."""
        # Arrange & Act
        pattern = Pattern(
            pattern_id="test_001",
            pattern_type="failure",
            pattern_name="critical_error",
            description="Test pattern",
            confidence=0.85,
            occurrences=3,
            examples=[{"event": "Fatal crash"}],
            metadata={"source": "test"}
        )

        # Assert
        assert pattern.pattern_id == "test_001"
        assert pattern.pattern_type == "failure"
        assert pattern.confidence == 0.85
        assert pattern.occurrences == 3

    def test_pattern_confidence_validation_rejects_invalid(self):
        """Should reject confidence outside 0-1 range."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            Pattern(
                pattern_id="test",
                pattern_type="failure",
                pattern_name="error",
                description="test",
                confidence=1.5  # Invalid
            )


class TestCustomDetectors:
    """Test custom detector registration."""

    def test_register_custom_detector(self):
        """Should register custom detector function."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)

        def custom_detector(text: str, metadata: Optional[Dict]) -> Optional[PatternMatch]:
            if "custom_pattern" in text:
                return PatternMatch(
                    pattern_type="failure",
                    pattern_name="custom_error",
                    confidence=0.9,
                    keywords_matched=["custom_pattern"],
                    base_score=0.7,
                    keyword_score=0.2
                )
            return None

        # Act
        detector.register_detector("custom", custom_detector)

        # Assert
        assert "custom" in detector.custom_detectors

    def test_detect_with_custom_detector(self):
        """Should use custom detector in detection."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)

        def custom_detector(text: str, metadata: Optional[Dict]) -> Optional[PatternMatch]:
            if "special_keyword" in text.lower():
                return PatternMatch(
                    pattern_type="failure",
                    pattern_name="special_error",
                    confidence=0.95,
                    keywords_matched=["special_keyword"],
                    base_score=0.8,
                    keyword_score=0.15
                )
            return None

        detector.register_detector("special", custom_detector)
        event = "Event with special_keyword detected"

        # Act
        result = detector.detect_with_custom(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "special_error"
        assert result.confidence == 0.95

    def test_custom_detector_wins_over_builtin(self):
        """Should prefer custom detector with higher confidence."""
        # Arrange
        detector = PatternDetector(min_confidence=0.7)

        def high_confidence_custom(text: str, metadata: Optional[Dict]) -> Optional[PatternMatch]:
            return PatternMatch(
                pattern_type="opportunity",
                pattern_name="custom_high",
                confidence=0.99,
                keywords_matched=["fatal"],
                base_score=0.9,
                keyword_score=0.09
            )

        detector.register_detector("high_custom", high_confidence_custom)
        event = "Fatal error"  # Would match built-in but custom has higher confidence

        # Act
        result = detector.detect_with_custom(event)

        # Assert
        assert result is not None
        assert result.pattern_name == "custom_high"
        assert result.confidence == 0.99
