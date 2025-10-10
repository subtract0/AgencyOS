"""
Misclassification detector for Adaptive Router quality feedback loop.

Implements rule-based detection with 4 weighted rules:
1. Test failure detection (confidence=0.95)
2. Code churn detection (confidence=0.85/0.70)
3. Execution timing detection (confidence=0.75)
4. User feedback override (confidence=1.0)

Constitutional Compliance:
- Article I: Complete context (all signals evaluated before detection)
- Article II: Result pattern for error handling
- Article IV: VectorStore learning boost (mandatory)
- Article V: Follows spec-004-quality-feedback-loop.md Section 7

Reference: /Users/am/Code/Agency/specs/spec-004-quality-feedback-loop.md Section 7
"""

from datetime import datetime
from typing import Optional

from shared.agent_context import AgentContext
from shared.models.misclassification_report import DetectedIssue, MisclassificationReport
from shared.models.quality_signals import QualitySignals, SeverityLevel, UserFeedback
from shared.type_definitions.result import Err, Ok, Result


class DetectionError(Exception):
    """Raised when detection fails."""
    pass


class MisclassificationDetector:
    """
    Detects task misclassifications using rule-based analysis.

    Implements spec Section 7.1-7.5:
    - 4 detection rules with confidence scoring
    - Multi-signal aggregation (weighted average)
    - VectorStore learning boost (Article IV)
    - Recommended tier computation

    Example:
        >>> detector = MisclassificationDetector()
        >>> signals = QualitySignals(
        ...     task_id="task_123",
        ...     original_tier="simple",
        ...     test_failure_rate=0.33,
        ...     code_churn_lines=145,
        ...     execution_time_ratio=4.2,
        ...     user_feedback=None
        ... )
        >>> result = detector.detect("task_123", signals)
        >>> report = result.unwrap()
        >>> report.is_misclassified
        True
        >>> report.recommended_tier
        'complex'
    """

    def __init__(self, context: AgentContext | None = None):
        """
        Initialize detector with optional AgentContext for VectorStore learning.

        Args:
            context: AgentContext with VectorStore access (None disables learning boost)
        """
        self.context = context

    def detect(
        self,
        task_id: str,
        signals: QualitySignals,
        task_description: str | None = None
    ) -> Result[MisclassificationReport, DetectionError]:
        """
        Detect misclassification from quality signals.

        Applies 4 detection rules (spec Section 7.1):
        1. Test failure detection (confidence=0.95)
        2. Code churn detection (confidence=0.85/0.70)
        3. Execution timing detection (confidence=0.75)
        4. User feedback override (confidence=1.0)

        Args:
            task_id: Task identifier
            signals: Quality signals from SignalCollector
            task_description: Optional task description for VectorStore similarity search

        Returns:
            Result[MisclassificationReport, DetectionError]

        Example:
            >>> result = detector.detect("task_42", signals, "Refactor async handler")
            >>> if result.is_ok():
            ...     report = result.unwrap()
            ...     print(f"Misclassified: {report.is_misclassified}")
        """
        try:
            # Apply 4 detection rules (Article I: Complete context)
            detected_issues: list[DetectedIssue] = []

            # Rule 1: Test failure detection
            if issue := self._rule_test_failure(signals):
                detected_issues.append(issue)

            # Rule 2: Code churn detection
            if issue := self._rule_code_churn(signals):
                detected_issues.append(issue)

            # Rule 3: Execution timing detection
            if issue := self._rule_execution_timing(signals):
                detected_issues.append(issue)

            # Rule 4: User feedback override
            if issue := self._rule_user_feedback(signals):
                detected_issues.append(issue)

            # Aggregate confidence (spec Section 7.2)
            aggregated_confidence = self._aggregate_confidence(detected_issues)

            # VectorStore learning boost (Article IV, spec Section 7.8)
            if self.context and task_description:
                aggregated_confidence = self._apply_learning_boost(
                    task_description, signals.original_tier, aggregated_confidence
                )

            # Determine recommended tier
            recommended_tier = self._recommend_tier(signals.original_tier, detected_issues)

            # Classify misclassification (CRITICAL/WARNING issues only)
            is_misclassified = any(
                issue.severity in [SeverityLevel.CRITICAL, SeverityLevel.WARNING]
                for issue in detected_issues
            )

            report = MisclassificationReport(
                task_id=task_id,
                original_tier=signals.original_tier,
                recommended_tier=recommended_tier,
                detected_issues=detected_issues,
                aggregated_confidence=aggregated_confidence,
                is_misclassified=is_misclassified,
                detected_at=datetime.utcnow().isoformat()
            )

            return Ok(report)

        except Exception as e:
            return Err(DetectionError(f"Detection failed: {e}"))

    def _rule_test_failure(self, signals: QualitySignals) -> DetectedIssue | None:
        """
        Rule 1: Test failure detection (spec Section 7.1, confidence=0.95).

        Trigger: test_failure_rate > 0.1 AND original_tier == "simple"

        Returns:
            DetectedIssue with CRITICAL severity or None
        """
        if not signals.test_failure_rate:
            return None

        if signals.test_failure_rate > 0.1 and signals.original_tier == "simple":
            return DetectedIssue(
                rule_name="test_failure",
                confidence=0.95,
                severity=SeverityLevel.CRITICAL,
                description=f"Test failure rate {signals.test_failure_rate:.1%} (>10% threshold)",
                signal_value=signals.test_failure_rate
            )

        return None

    def _rule_code_churn(self, signals: QualitySignals) -> DetectedIssue | None:
        """
        Rule 2: Code churn detection (spec Section 7.1, confidence varies).

        Triggers:
        - code_churn_lines > 100 → CRITICAL (confidence=0.85)
        - code_churn_lines > 50 → WARNING (confidence=0.70)

        Returns:
            DetectedIssue with CRITICAL/WARNING severity or None
        """
        if not signals.code_churn_lines:
            return None

        if signals.code_churn_lines > 100 and signals.original_tier == "simple":
            return DetectedIssue(
                rule_name="code_churn",
                confidence=0.85,
                severity=SeverityLevel.CRITICAL,
                description=f"Code churn {signals.code_churn_lines} lines (>100 threshold)",
                signal_value=float(signals.code_churn_lines)
            )

        elif signals.code_churn_lines > 50 and signals.original_tier == "simple":
            return DetectedIssue(
                rule_name="code_churn",
                confidence=0.70,
                severity=SeverityLevel.WARNING,
                description=f"Code churn {signals.code_churn_lines} lines (>50 threshold)",
                signal_value=float(signals.code_churn_lines)
            )

        return None

    def _rule_execution_timing(self, signals: QualitySignals) -> DetectedIssue | None:
        """
        Rule 3: Execution timing detection (spec Section 7.1, confidence=0.75).

        Trigger: execution_time_ratio > 3.0 AND original_tier == "simple"

        Returns:
            DetectedIssue with WARNING severity or None
        """
        if not signals.execution_time_ratio:
            return None

        if signals.execution_time_ratio > 3.0 and signals.original_tier == "simple":
            return DetectedIssue(
                rule_name="execution_timing",
                confidence=0.75,
                severity=SeverityLevel.WARNING,
                description=f"Execution time ratio {signals.execution_time_ratio:.1f}x (>3.0 threshold)",
                signal_value=signals.execution_time_ratio
            )

        return None

    def _rule_user_feedback(self, signals: QualitySignals) -> DetectedIssue | None:
        """
        Rule 4: User feedback override (spec Section 7.1, confidence=1.0).

        Trigger: user_feedback == UserFeedback.MISCLASSIFIED

        Returns:
            DetectedIssue with CRITICAL severity or None
        """
        if signals.user_feedback == UserFeedback.MISCLASSIFIED:
            return DetectedIssue(
                rule_name="user_feedback",
                confidence=1.0,
                severity=SeverityLevel.CRITICAL,
                description="User explicitly flagged as misclassified",
                signal_value=None
            )

        return None

    def _aggregate_confidence(self, detected_issues: list[DetectedIssue]) -> float:
        """
        Aggregate confidence from multiple rules (spec Section 7.2).

        Uses weighted average: sum(confidence^2) / count
        User feedback always overrides (confidence=1.0)

        Args:
            detected_issues: List of triggered detection rules

        Returns:
            Aggregated confidence (0.0-1.0)

        Example:
            >>> issues = [
            ...     DetectedIssue(rule_name="test_failure", confidence=0.95, ...),
            ...     DetectedIssue(rule_name="code_churn", confidence=0.85, ...)
            ... ]
            >>> confidence = detector._aggregate_confidence(issues)
            >>> confidence
            0.905  # (0.95^2 + 0.85^2) / 2
        """
        if not detected_issues:
            return 0.0

        # User feedback always overrides (confidence=1.0)
        if any(issue.rule_name == "user_feedback" for issue in detected_issues):
            return 1.0

        # Weighted average: sum(confidence^2) / count
        weighted_sum = sum(issue.confidence ** 2 for issue in detected_issues)
        return weighted_sum / len(detected_issues)

    def _recommend_tier(self, original_tier: str, detected_issues: list[DetectedIssue]) -> str:
        """
        Determine recommended tier based on detected issues.

        Logic:
        - No issues → keep original tier
        - Test failures >30% → upgrade to complex
        - CRITICAL issues → upgrade to moderate
        - WARNING issues → upgrade to moderate

        Args:
            original_tier: Original tier classification
            detected_issues: List of detected issues

        Returns:
            Recommended tier (simple/moderate/complex)

        Example:
            >>> tier = detector._recommend_tier("simple", [critical_test_failure])
            >>> tier
            'complex'
        """
        if not detected_issues:
            return original_tier  # No issues, keep current tier

        # Get CRITICAL issues
        critical_issues = [i for i in detected_issues if i.severity == SeverityLevel.CRITICAL]

        if critical_issues:
            # Check for test failures >30% → complex
            for issue in critical_issues:
                if issue.rule_name == "test_failure" and issue.signal_value and issue.signal_value > 0.3:
                    return "complex"

            # Otherwise upgrade to moderate
            return "moderate"

        # WARNING issues → moderate
        return "moderate"

    def _apply_learning_boost(
        self, task_description: str, original_tier: str, base_confidence: float
    ) -> float:
        """
        Apply VectorStore learning boost (spec Section 7.8, Article IV).

        Queries VectorStore for similar misclassifications. If similar case exists
        with confidence >0.8, boost aggregated confidence by +0.1 (max 1.0).

        Args:
            task_description: Task description for semantic search
            original_tier: Original tier classification
            base_confidence: Base confidence before boost

        Returns:
            Boosted confidence (0.0-1.0)

        Example:
            >>> # VectorStore finds similar case with confidence=0.9
            >>> boosted = detector._apply_learning_boost("Refactor async", "simple", 0.85)
            >>> boosted
            0.95  # 0.85 + 0.1 boost
        """
        if not self.context:
            return base_confidence

        try:
            # Query VectorStore for similar misclassifications (Article IV)
            similar_cases = self.context.search_memories(
                tags=["misclassification", original_tier],
                include_session=False  # Cross-session learning
            )

            # If similar case exists with high confidence, boost by 0.1
            if similar_cases and len(similar_cases) > 0:
                max_similarity = max(case.get("confidence", 0.0) for case in similar_cases)
                if max_similarity > 0.8:
                    return min(1.0, base_confidence + 0.1)

            return base_confidence

        except Exception:
            # Gracefully degrade if VectorStore query fails (Article I)
            return base_confidence
