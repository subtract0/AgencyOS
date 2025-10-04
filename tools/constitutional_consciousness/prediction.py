#!/usr/bin/env python3
"""
Constitutional Consciousness - Prediction Engine (Day 3).

Uses VectorStore queries and pattern analysis to predict future violations.

Constitutional Compliance:
- Article I: Complete context from VectorStore queries
- Article IV: Continuous learning via pattern history
- Article V: Implements spec from consciousness-launch.md
"""

from datetime import UTC, datetime
from typing import Any

from agency_memory import create_enhanced_memory_store
from tools.constitutional_consciousness.models import (
    ConstitutionalPattern,
    ViolationPrediction,
)


class PredictionEngine:
    """
    Predicts future constitutional violations using historical patterns.

    Uses VectorStore to query similar patterns and calculate recurrence probability.
    """

    def __init__(self, enable_vectorstore: bool = True):
        """Initialize prediction engine."""
        self.enable_vectorstore = enable_vectorstore

        if self.enable_vectorstore:
            self.vector_store = create_enhanced_memory_store(
                embedding_provider="openai"
            )
        else:
            self.vector_store = None

    def predict_violations(
        self,
        patterns: list[ConstitutionalPattern],
        lookback_days: int = 7,
    ) -> list[ViolationPrediction]:
        """
        Predict future violations based on historical patterns.

        Args:
            patterns: Current detected patterns
            lookback_days: Days to look back for trend analysis

        Returns:
            List of ViolationPrediction objects
        """
        if not patterns:
            return []

        predictions = []

        for pattern in patterns:
            # Query VectorStore for historical context
            similar_patterns = self._query_similar_patterns(pattern) if self.vector_store else []

            # Calculate recurrence probability
            probability = self._calculate_probability(pattern, similar_patterns)

            # Estimate expected occurrences
            expected_count = self._estimate_occurrences(pattern, lookback_days)

            # Generate recommended action
            action = self._recommend_action(pattern, probability)

            # Calculate confidence based on evidence
            confidence = min(
                pattern.confidence * (1 + len(similar_patterns) * 0.1),
                0.95
            )

            prediction = ViolationPrediction(
                pattern_id=pattern.pattern_id,
                probability=probability,
                expected_occurrences=expected_count,
                time_period="7_days",
                recommended_action=action,
                confidence=confidence,
            )

            predictions.append(prediction)

        # Sort by probability (highest first)
        predictions.sort(key=lambda p: p.probability, reverse=True)

        return predictions

    def _query_similar_patterns(self, pattern: ConstitutionalPattern) -> list[dict[str, Any]]:
        """Query VectorStore for similar historical patterns."""
        if not self.vector_store:
            return []

        # Build semantic query
        query = (
            f"{pattern.function_name} violates "
            f"{', '.join(pattern.articles_violated)} "
            f"with {pattern.trend.lower()} trend"
        )

        # Search with tags
        results = self.vector_store.combined_search(
            tags=["constitutional", "pattern", pattern.trend.lower()],
            query=query,
            top_k=5,
        )

        return results

    def _calculate_probability(
        self,
        pattern: ConstitutionalPattern,
        similar_patterns: list[dict[str, Any]]
    ) -> float:
        """
        Calculate probability of recurrence.

        Factors:
        - Pattern trend (INCREASING = higher probability)
        - Frequency (more occurrences = higher probability)
        - Similar patterns (more history = higher probability)
        """
        base_prob = pattern.confidence

        # Trend boost
        trend_multiplier = {
            "INCREASING": 1.3,
            "STABLE": 1.0,
            "DECREASING": 0.7,
        }.get(pattern.trend, 1.0)

        # Frequency boost (normalize to 0-1 scale)
        freq_boost = min(pattern.frequency / 100.0, 0.3)

        # Historical evidence boost
        history_boost = len(similar_patterns) * 0.05

        probability = min(
            base_prob * trend_multiplier + freq_boost + history_boost,
            0.95  # Cap at 95%
        )

        return round(probability, 2)

    def _estimate_occurrences(
        self,
        pattern: ConstitutionalPattern,
        lookback_days: int
    ) -> int:
        """
        Estimate expected violations in next 7 days.

        Uses simple heuristic:
        - If INCREASING: expect 20% more than recent average
        - If STABLE: expect same as recent average
        - If DECREASING: expect 20% less
        """
        # Average per day in lookback period
        daily_avg = pattern.frequency / lookback_days

        # Trend adjustment
        trend_factor = {
            "INCREASING": 1.2,
            "STABLE": 1.0,
            "DECREASING": 0.8,
        }.get(pattern.trend, 1.0)

        expected_7d = int(daily_avg * 7 * trend_factor)

        return max(expected_7d, 1)  # At least 1

    def _recommend_action(
        self,
        pattern: ConstitutionalPattern,
        probability: float
    ) -> str:
        """Generate recommended action based on pattern and probability."""
        if probability > 0.85:
            action = f"URGENT: Apply fix immediately - {pattern.fix_suggestion}"
        elif probability > 0.70:
            action = f"HIGH PRIORITY: Schedule fix this week - {pattern.fix_suggestion}"
        elif probability > 0.50:
            action = f"MEDIUM: Monitor and plan fix - {pattern.fix_suggestion}"
        else:
            action = f"LOW: Track for trends - {pattern.fix_suggestion}"

        return action

    def generate_prediction_report(
        self,
        predictions: list[ViolationPrediction]
    ) -> str:
        """Generate human-readable prediction report."""
        if not predictions:
            return "No predictions generated (no patterns detected)."

        report_lines = []
        report_lines.append("\n" + "=" * 80)
        report_lines.append("CONSTITUTIONAL CONSCIOUSNESS - VIOLATION PREDICTIONS")
        report_lines.append("=" * 80)
        report_lines.append(f"\nTimestamp: {datetime.now(UTC).isoformat()}")
        report_lines.append(f"Predictions: {len(predictions)}")

        for i, pred in enumerate(predictions, 1):
            report_lines.append(f"\n{i}. Pattern: {pred.pattern_id}")
            report_lines.append(f"   Probability of Recurrence: {pred.probability:.0%}")
            report_lines.append(f"   Expected Violations ({pred.time_period.replace('_', ' ')}): {pred.expected_occurrences}")
            report_lines.append(f"   Confidence: {pred.confidence:.0%}")
            report_lines.append(f"   Action: {pred.recommended_action}")

        report_lines.append("\n" + "=" * 80 + "\n")

        return "\n".join(report_lines)
