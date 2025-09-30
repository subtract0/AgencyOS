"""
Pattern Detector for WITNESS Agent

Implements AUDITLEARN's pattern classification using local Qwen 1.5B model.
Analyzes telemetry/context events and classifies into failure/opportunity/user_intent.

Pattern Types:
- FAILURE: critical_error, performance_regression, flaky_test, integration_failure
- OPPORTUNITY: constitutional_violation, code_duplication, missing_tests, type_safety
- USER_INTENT: recurring_topic, feature_request, workflow_bottleneck, frustration_signal

Constitutional Compliance:
- Article I: Complete context before classification
- Article IV: Continuous learning with confidence tracking
"""

from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass
from datetime import datetime
import re


PatternType = Literal["failure", "opportunity", "user_intent"]


@dataclass
class PatternMatch:
    """Result of pattern detection."""
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
    Pattern detection engine for WITNESS agent.

    Uses keyword-based heuristics with confidence scoring for fast,
    local pattern classification without LLM inference.
    """

    def __init__(self, min_confidence: float = 0.7):
        """
        Initialize pattern detector.

        Args:
            min_confidence: Minimum confidence threshold for pattern matches
        """
        self.min_confidence = min_confidence
        self.pattern_history: Dict[str, int] = {}  # pattern_name -> count

    def detect(
        self,
        event_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[PatternMatch]:
        """
        Detect pattern in event text.

        Args:
            event_text: Text content to analyze (error message, log, user message)
            metadata: Optional metadata (file, line, source, etc.)

        Returns:
            PatternMatch if confidence >= min_confidence, else None
        """
        event_lower = event_text.lower()
        best_match: Optional[PatternMatch] = None
        best_confidence = 0.0

        # Try all pattern types and patterns
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

        # Apply adaptive threshold
        if best_match:
            adjusted_threshold = self._get_adaptive_threshold(best_match.pattern_name)
            if best_match.confidence >= adjusted_threshold:
                # Update history
                self.pattern_history[best_match.pattern_name] = \
                    self.pattern_history.get(best_match.pattern_name, 0) + 1
                return best_match

        return None

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
        keyword_score = 0.0
        matched_keywords: List[str] = []

        # Match keywords
        for keyword, weight in keywords.items():
            if keyword.lower() in event_lower:
                keyword_score += weight
                matched_keywords.append(keyword)

        # Metadata bonuses
        if metadata:
            keyword_score += self._metadata_bonus(pattern_type, pattern_name, metadata)

        # Calculate final confidence
        confidence = min(1.0, base_score + keyword_score)

        return PatternMatch(
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            confidence=confidence,
            keywords_matched=matched_keywords,
            base_score=base_score,
            keyword_score=keyword_score
        )

    def _metadata_bonus(
        self,
        pattern_type: PatternType,
        pattern_name: str,
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate bonus from metadata."""
        bonus = 0.0

        # Error type metadata
        if "error_type" in metadata:
            error_type = metadata["error_type"].lower()
            if pattern_name == "critical_error" and error_type in ["fatal", "modulenotfounderror"]:
                bonus += 0.1
            elif pattern_name == "flaky_test" and error_type == "assertionerror":
                bonus += 0.05

        # File extension
        if "file" in metadata:
            file_path = metadata["file"].lower()
            if pattern_name == "missing_tests" and "test" not in file_path:
                bonus += 0.05

        # Priority metadata
        if metadata.get("priority") == "CRITICAL":
            bonus += 0.05

        return bonus

    def _get_adaptive_threshold(self, pattern_name: str) -> float:
        """Get adaptive threshold based on pattern history."""
        if pattern_name not in ADAPTIVE_THRESHOLDS:
            return self.min_confidence

        config = ADAPTIVE_THRESHOLDS[pattern_name]
        occurrences = self.pattern_history.get(pattern_name, 0)

        if occurrences >= config["min_occurrences"]:
            # Reduce threshold after seeing pattern multiple times
            return max(0.6, self.min_confidence - config["threshold_reduction"])

        return self.min_confidence

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
            "most_common": sorted(
                self.pattern_history.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5] if self.pattern_history else []
        }

    def reset_history(self) -> None:
        """Reset pattern history (for new sessions)."""
        self.pattern_history.clear()
