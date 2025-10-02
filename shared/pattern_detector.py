"""
Generic Pattern Detector - Extracted from Trinity Protocol

A keyword-based heuristic pattern detection engine with confidence scoring,
adaptive thresholds, and pluggable detector architecture.

Pattern Types:
- FAILURE: critical_error, performance_regression, flaky_test, integration_failure
- OPPORTUNITY: constitutional_violation, code_duplication, missing_tests, type_safety
- USER_INTENT: recurring_topic, feature_request, workflow_bottleneck, frustration_signal

Constitutional Compliance:
- Article I: Complete context before classification
- Article IV: Continuous learning with confidence tracking
- TDD Mandate: Comprehensive test coverage
- Type Safety: Strict Pydantic models (no Dict[Any, Any])
- Functions <50 lines
"""

from typing import Dict, Any, List, Optional, Literal, Callable
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass
from datetime import datetime
import re


# Type definitions
PatternType = Literal["failure", "opportunity", "user_intent"]


# Pydantic models
class Pattern(BaseModel):
    """Detected pattern result."""
    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_type: PatternType = Field(..., description="Type of pattern")
    pattern_name: str = Field(..., description="Specific pattern name")
    description: str = Field(..., description="Pattern description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    occurrences: int = Field(default=1, ge=1, description="Number of occurrences")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Example instances")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator("confidence")
    def confidence_in_range(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


@dataclass
class PatternMatch:
    """Result of pattern detection (internal use)."""
    pattern_type: PatternType
    pattern_name: str
    confidence: float
    keywords_matched: List[str]
    base_score: float
    keyword_score: float


# Pattern heuristics with keyword weights
PATTERN_HEURISTICS: Dict[PatternType, Dict[str, Dict[str, float]]] = {
    "failure": {
        "critical_error": {
            "fatal": 0.25,
            "crash": 0.25,
            "modulenotfounderror": 0.25,
            "importerror": 0.20,
            "systemexit": 0.20,
            "exception": 0.10,
            "traceback": 0.10
        },
        "performance_regression": {
            "timeout": 0.25,
            "duration_s": 0.15,
            "exceeded limit": 0.20,
            "slow": 0.15,
            "performance": 0.15,
            "regression": 0.20
        },
        "flaky_test": {
            "test failed": 0.20,
            "assertionerror": 0.15,
            "intermittent": 0.20,
            "sometimes passes": 0.20,
            "flaky": 0.25,
            "non-deterministic": 0.15
        },
        "integration_failure": {
            "api error": 0.20,
            "connection refused": 0.25,
            "firebase": 0.15,
            "openai": 0.15,
            "401": 0.20,
            "403": 0.20,
            "500": 0.20,
            "503": 0.15
        }
    },
    "opportunity": {
        "constitutional_violation": {
            "dict[any": 0.30,
            "no-verify": 0.25,
            "> 50 lines": 0.20,
            "bypass": 0.25,
            "skip test": 0.25,
            "# type: ignore": 0.15,
            "try/catch": 0.10
        },
        "code_duplication": {
            "similar code": 0.25,
            "repeated logic": 0.25,
            "copy-paste": 0.20,
            "dry violation": 0.25,
            "duplicate": 0.20,
            "repetition": 0.15
        },
        "missing_tests": {
            "no tests": 0.30,
            "untested": 0.25,
            "coverage low": 0.20,
            "0% coverage": 0.30,
            "missing test": 0.25,
            "test gap": 0.20
        },
        "type_safety": {
            "any": 0.20,
            "untyped": 0.20,
            "missing type hints": 0.25,
            "# type: ignore": 0.20,
            "no type": 0.15,
            "type error": 0.20
        }
    },
    "user_intent": {
        "recurring_topic": {
            "repeated": 0.30,
            "again": 0.15,
            "mentioned >3x": 0.30,
            "keeps coming up": 0.25,
            "frequently": 0.20
        },
        "feature_request": {
            "i need": 0.25,
            "can we add": 0.25,
            "please implement": 0.25,
            "would like": 0.20,
            "feature request": 0.30,
            "new feature": 0.25
        },
        "workflow_bottleneck": {
            "i always manually": 0.25,
            "this is tedious": 0.25,
            "repetitive task": 0.25,
            "slow process": 0.20,
            "time-consuming": 0.20,
            "automate": 0.20
        },
        "frustration_signal": {
            "why doesn't": 0.20,
            "this should work": 0.20,
            "confused": 0.20,
            "unclear": 0.15,
            "broken": 0.15,
            "not working": 0.15,
            "frustrated": 0.25
        }
    }
}


# Base confidence scores per pattern type
BASE_CONFIDENCE: Dict[PatternType, float] = {
    "failure": 0.7,
    "opportunity": 0.6,
    "user_intent": 0.5
}


# Adaptive threshold adjustments
ADAPTIVE_THRESHOLDS = {
    "critical_error": {"min_occurrences": 3, "threshold_reduction": 0.1},
    "flaky_test": {"min_occurrences": 2, "threshold_reduction": 0.15},
    "constitutional_violation": {"min_occurrences": 1, "threshold_reduction": 0.0}
}


class PatternDetector:
    """
    Generic pattern detection engine.

    Uses keyword-based heuristics with confidence scoring for fast,
    local pattern classification without LLM inference.

    Features:
    - Confidence-based pattern matching
    - Adaptive thresholds based on history
    - Metadata bonus calculations
    - Pluggable custom detector architecture
    - Pattern statistics tracking
    """

    def __init__(self, min_confidence: float = 0.7):
        """
        Initialize pattern detector.

        Args:
            min_confidence: Minimum confidence threshold for pattern matches
        """
        self.min_confidence = min_confidence
        self.pattern_history: Dict[str, int] = {}
        self.custom_detectors: Dict[str, Callable] = {}

    def detect(
        self,
        event_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[PatternMatch]:
        """
        Detect pattern in event text.

        Args:
            event_text: Text content to analyze
            metadata: Optional metadata for bonus scoring

        Returns:
            PatternMatch if confidence >= min_confidence, else None
        """
        # Validate input
        if not event_text or not event_text.strip():
            return None

        event_lower = event_text.lower()
        best_match = self._find_best_match(event_lower, metadata)

        if best_match:
            return self._apply_adaptive_threshold(best_match)

        return None

    def _find_best_match(
        self,
        event_lower: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Optional[PatternMatch]:
        """Find best matching pattern."""
        best_match: Optional[PatternMatch] = None
        best_confidence = 0.0

        for pattern_type in PATTERN_HEURISTICS:
            for pattern_name, keywords in PATTERN_HEURISTICS[pattern_type].items():
                match = self._calculate_match(
                    pattern_type,
                    pattern_name,
                    event_lower,
                    keywords,
                    metadata
                )

                if match.confidence > best_confidence:
                    best_match = match
                    best_confidence = match.confidence

        return best_match

    def _calculate_match(
        self,
        pattern_type: PatternType,
        pattern_name: str,
        event_lower: str,
        keywords: Dict[str, float],
        metadata: Optional[Dict[str, Any]]
    ) -> PatternMatch:
        """Calculate pattern match confidence."""
        base_score = BASE_CONFIDENCE[pattern_type]
        keyword_score = self._calculate_keyword_score(
            event_lower, keywords
        )
        matched_keywords = self._get_matched_keywords(
            event_lower, keywords
        )

        if metadata:
            keyword_score += self._metadata_bonus(
                pattern_type, pattern_name, metadata
            )

        confidence = min(1.0, base_score + keyword_score)

        return PatternMatch(
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            confidence=confidence,
            keywords_matched=matched_keywords,
            base_score=base_score,
            keyword_score=keyword_score
        )

    def _calculate_keyword_score(
        self,
        event_lower: str,
        keywords: Dict[str, float]
    ) -> float:
        """Calculate keyword match score."""
        score = 0.0
        for keyword, weight in keywords.items():
            if keyword.lower() in event_lower:
                score += weight
        return score

    def _get_matched_keywords(
        self,
        event_lower: str,
        keywords: Dict[str, float]
    ) -> List[str]:
        """Get list of matched keywords."""
        matched = []
        for keyword in keywords.keys():
            if keyword.lower() in event_lower:
                matched.append(keyword)
        return matched

    def _metadata_bonus(
        self,
        pattern_type: PatternType,
        pattern_name: str,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate bonus from metadata."""
        bonus = 0.0

        bonus += self._error_type_bonus(pattern_name, metadata)
        bonus += self._file_extension_bonus(pattern_name, metadata)
        bonus += self._priority_bonus(metadata)

        return bonus

    def _error_type_bonus(
        self,
        pattern_name: str,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate error type bonus."""
        if "error_type" not in metadata:
            return 0.0

        error_type = metadata["error_type"].lower()
        if pattern_name == "critical_error":
            if error_type in ["fatal", "modulenotfounderror"]:
                return 0.1
        elif pattern_name == "flaky_test":
            if error_type == "assertionerror":
                return 0.05

        return 0.0

    def _file_extension_bonus(
        self,
        pattern_name: str,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate file extension bonus."""
        if "file" not in metadata:
            return 0.0

        file_path = metadata["file"].lower()
        if pattern_name == "missing_tests" and "test" not in file_path:
            return 0.05

        return 0.0

    def _priority_bonus(self, metadata: Dict[str, Any]) -> float:
        """Calculate priority bonus."""
        if metadata.get("priority") == "CRITICAL":
            return 0.05
        return 0.0

    def _apply_adaptive_threshold(
        self,
        match: PatternMatch
    ) -> Optional[PatternMatch]:
        """Apply adaptive threshold and update history."""
        threshold = self._get_adaptive_threshold(match.pattern_name)

        if match.confidence >= threshold:
            self._update_history(match.pattern_name)
            return match

        return None

    def _get_adaptive_threshold(self, pattern_name: str) -> float:
        """Get adaptive threshold based on pattern history."""
        if pattern_name not in ADAPTIVE_THRESHOLDS:
            return self.min_confidence

        config = ADAPTIVE_THRESHOLDS[pattern_name]
        occurrences = self.pattern_history.get(pattern_name, 0)

        if occurrences >= config["min_occurrences"]:
            reduction = config["threshold_reduction"]
            return max(0.6, self.min_confidence - reduction)

        return self.min_confidence

    def _update_history(self, pattern_name: str) -> None:
        """Update pattern occurrence history."""
        current = self.pattern_history.get(pattern_name, 0)
        self.pattern_history[pattern_name] = current + 1

    def get_pattern_stats(self) -> Dict[str, Any]:
        """
        Get statistics about detected patterns.

        Returns:
            Dict with pattern counts and frequencies
        """
        total = sum(self.pattern_history.values())

        return {
            "total_detections": total,
            "unique_patterns": len(self.pattern_history),
            "pattern_counts": dict(self.pattern_history),
            "most_common": self._get_most_common(5)
        }

    def _get_most_common(self, limit: int) -> List[tuple]:
        """Get most common patterns."""
        if not self.pattern_history:
            return []

        return sorted(
            self.pattern_history.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def reset_history(self) -> None:
        """Reset pattern history (for new sessions)."""
        self.pattern_history.clear()

    def register_detector(
        self,
        name: str,
        detector_func: Callable[[str, Optional[Dict]], Optional[PatternMatch]]
    ) -> None:
        """
        Register custom pattern detector.

        Args:
            name: Unique detector name
            detector_func: Function(event_text, metadata) -> Optional[PatternMatch]
        """
        self.custom_detectors[name] = detector_func

    def detect_with_custom(
        self,
        event_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[PatternMatch]:
        """
        Detect using both built-in and custom detectors.

        Args:
            event_text: Text to analyze
            metadata: Optional metadata

        Returns:
            Best match from all detectors
        """
        # Try built-in detection first
        best_match = self.detect(event_text, metadata)
        best_confidence = best_match.confidence if best_match else 0.0

        # Try custom detectors
        for custom_func in self.custom_detectors.values():
            match = custom_func(event_text, metadata)
            if match and match.confidence > best_confidence:
                best_match = match
                best_confidence = match.confidence

        return best_match
