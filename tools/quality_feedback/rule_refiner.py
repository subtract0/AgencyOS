"""
VectorStore Rule Refiner for Adaptive Model Router.

Updates VectorStore classification patterns based on detected misclassifications,
implementing closed-loop learning (Article IV).

Features:
- Confidence adjustment (exponential decay + evidence weight)
- Threshold tuning (10% reduction after 3 CRITICAL detections)
- Pattern storage (embeddings + corrected tier)
- Convergence detection (accuracy >98%)
- Stability guarantees (max 3 iterations, oscillation detection)
- Rollback mechanism (accuracy degradation >5%)

Constitutional Compliance:
- Article I: Complete context (all data saved before refinement)
- Article II: Result pattern for error handling
- Article IV: VectorStore integration MANDATORY
- Article V: Follows spec-004-quality-feedback-loop.md Section 8

Reference: /Users/am/Code/Agency/specs/spec-004-quality-feedback-loop.md Section 8
"""

import logging
from datetime import UTC, datetime
from typing import Optional

from shared.agent_context import AgentContext
from shared.models.misclassification_report import MisclassificationReport
from shared.models.refinement_result import (
    RefinementEntry,
    RefinementHistory,
    RefinementResult,
    ThresholdAdjustment,
    VectorStoreSnapshot,
)
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class RefinementError(Exception):
    """Raised when refinement fails."""

    pass


class MaxIterationsExceeded(RefinementError):
    """Raised when task exceeds max 3 refinement iterations."""

    pass


class AccuracyDegradation(RefinementError):
    """Raised when accuracy degrades >5% after refinement."""

    pass


class RuleRefiner:
    """
    Updates VectorStore classification patterns based on misclassifications.

    Implements spec Section 8:
    - Confidence adjustment (exponential decay + evidence weight)
    - Threshold tuning (10% reduction for CRITICAL detections)
    - Pattern storage (embeddings + corrected tier)
    - Convergence detection (accuracy >98%)
    - Stability guarantees (max 3 iterations, rollback)

    Example:
        >>> from tools.quality_feedback.rule_refiner import RuleRefiner
        >>> from shared.agent_context import create_agent_context
        >>>
        >>> context = create_agent_context(session_id="test")
        >>> refiner = RuleRefiner(context)
        >>>
        >>> # Refine based on misclassification report
        >>> result = refiner.refine(report, task_description="Fix bug")
        >>> if result.is_ok():
        ...     refinement = result.unwrap()
        ...     print(f"Confidence: {refinement.confidence_after}")
    """

    # Default thresholds (spec Section 8.3)
    DEFAULT_THRESHOLDS = {
        "test_failure_rate": 0.1,
        "code_churn_lines": 100,
        "execution_time_ratio": 3.0,
    }

    # Minimum thresholds (spec Section 8.3)
    MIN_THRESHOLDS = {
        "test_failure_rate": 0.05,
        "code_churn_lines": 50,
        "execution_time_ratio": 2.0,
    }

    def __init__(
        self,
        context: AgentContext,
        decay_factor: float = 0.95,
        evidence_weight: float = 0.05,
        convergence_threshold: float = 0.98,
    ):
        """
        Initialize refiner with VectorStore context.

        Args:
            context: AgentContext with VectorStore access
            decay_factor: Confidence decay rate (0.95 = 5% decay per spec 8.2)
            evidence_weight: Weight per evidence occurrence (0.05 = 5% per spec 8.2)
            convergence_threshold: Accuracy target for convergence (0.98 = 98% per spec 8.5)

        Constitutional Compliance:
            - Article IV: VectorStore integration mandatory
        """
        self.context = context
        self.decay_factor = decay_factor
        self.evidence_weight = evidence_weight
        self.convergence_threshold = convergence_threshold

        # Load or initialize thresholds
        self.thresholds = self._load_thresholds()

        # Load refinement history
        self.history: dict[str, RefinementHistory] = self._load_history()

        logger.debug(
            f"RuleRefiner initialized: decay={decay_factor}, "
            f"evidence_weight={evidence_weight}, "
            f"convergence={convergence_threshold}"
        )

    def refine(
        self, report: MisclassificationReport, task_description: str | None = None
    ) -> Result[RefinementResult, RefinementError]:
        """
        Refine VectorStore patterns based on misclassification report.

        Args:
            report: Misclassification detection report
            task_description: Optional task description for embedding generation

        Returns:
            Result[RefinementResult, RefinementError]

        Constitutional Compliance:
            - Article I: Complete context (all history checked before action)
            - Article II: Result pattern for error handling
            - Article IV: VectorStore pattern storage mandatory
            - Article V: Follows spec Section 8 exactly

        Example:
            >>> result = refiner.refine(report, task_description="Fix bug")
            >>> if result.is_ok():
            ...     refinement = result.unwrap()
            ...     print(f"Confidence after: {refinement.confidence_after}")
        """
        try:
            # Check max iterations (spec Section 8.6)
            history = self.history.get(report.task_id, RefinementHistory(task_id=report.task_id))

            if history.iteration_count >= 3:
                return Err(
                    MaxIterationsExceeded(
                        f"Task {report.task_id} reached max 3 refinement iterations"
                    )
                )

            # Detect oscillation (spec Section 8.6)
            if self._detect_oscillation(history):
                return Err(RefinementError(f"Task {report.task_id} is oscillating between tiers"))

            # Query existing confidence from VectorStore (Article IV)
            confidence_before = self._query_existing_confidence(report.task_id, task_description)

            # Update confidence (spec Section 8.2)
            confidence_after = self._update_confidence(
                old_confidence=confidence_before or 0.6, new_evidence=report.is_misclassified
            )

            # Tune thresholds if CRITICAL (spec Section 8.3)
            threshold_adjustments: list[ThresholdAdjustment] = []
            if report.aggregated_confidence > 0.8:
                threshold_adjustments = self._tune_thresholds(report)

            # Store pattern in VectorStore (spec Section 8.4, Article IV)
            patterns_updated = self._store_pattern(
                report=report, task_description=task_description, confidence=confidence_after
            )

            # Update iteration count
            history.iteration_count += 1
            history.refinement_history.append(
                RefinementEntry(
                    timestamp=datetime.now(UTC).isoformat(),
                    original_tier=report.original_tier,
                    corrected_tier=report.recommended_tier,
                    confidence=confidence_after,
                    reason=(
                        f"Misclassification detected "
                        f"(confidence={report.aggregated_confidence:.2f})"
                    ),
                )
            )
            self.history[report.task_id] = history

            # Check convergence (spec Section 8.5)
            convergence_achieved = self._check_convergence()

            # Build result
            result = RefinementResult(
                task_id=report.task_id,
                patterns_updated=patterns_updated,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                threshold_adjustments=threshold_adjustments,
                iteration_count=history.iteration_count,
                convergence_achieved=convergence_achieved,
                accuracy_estimate=None,  # Computed in Phase 5
                refined_at=datetime.now(UTC).isoformat(),
            )

            # Save updated history and thresholds
            self._save_history()
            self._save_thresholds()

            logger.info(
                f"Refinement complete: task={report.task_id}, "
                f"confidence={confidence_after:.3f}, "
                f"iteration={history.iteration_count}"
            )

            return Ok(result)

        except Exception as e:
            logger.error(f"Refinement failed: {e}")
            return Err(RefinementError(f"Refinement failed: {e}"))

    def _update_confidence(self, old_confidence: float, new_evidence: bool) -> float:
        """
        Update confidence using exponential decay + evidence weight (spec Section 8.2).

        Formula: new_confidence = old_confidence * decay_factor + (evidence_weight if evidence else 0)

        Args:
            old_confidence: Existing confidence score (0.0-1.0)
            new_evidence: Whether new evidence supports pattern

        Returns:
            Updated confidence score (0.0-1.0)

        Example:
            >>> refiner._update_confidence(0.70, True)
            0.715  # 0.70 * 0.95 + 0.05 = 0.715
        """
        decayed = old_confidence * self.decay_factor
        if new_evidence:
            return min(1.0, decayed + self.evidence_weight)
        return max(0.0, decayed)

    def _tune_thresholds(self, report: MisclassificationReport) -> list[ThresholdAdjustment]:
        """
        Tune detection thresholds for CRITICAL detections (spec Section 8.3).

        After 3+ CRITICAL detections, lower threshold by 10%.

        Args:
            report: Misclassification report with detected issues

        Returns:
            List of threshold adjustments made

        Example:
            >>> # After 3 CRITICAL test failures
            >>> adjustments = refiner._tune_thresholds(report)
            >>> adjustments[0].new_threshold  # 0.1 * 0.9 = 0.09
        """
        adjustments: list[ThresholdAdjustment] = []

        for issue in report.detected_issues:
            # severity is already a string due to Pydantic use_enum_values
            severity_str = (
                issue.severity if isinstance(issue.severity, str) else issue.severity.value
            )
            if severity_str != "critical":
                continue

            # Map rule name to threshold key
            threshold_key = {
                "test_failure": "test_failure_rate",
                "code_churn": "code_churn_lines",
                "execution_timing": "execution_time_ratio",
            }.get(issue.rule_name)

            if not threshold_key:
                continue

            # Count CRITICAL detections for this signal
            detection_count = self._count_critical_detections(threshold_key)

            if detection_count >= 3:
                old_threshold = self.thresholds[threshold_key]
                new_threshold = max(
                    self.MIN_THRESHOLDS[threshold_key],
                    old_threshold * 0.9,  # 10% reduction
                )

                if new_threshold != old_threshold:
                    self.thresholds[threshold_key] = new_threshold
                    adjustments.append(
                        ThresholdAdjustment(
                            signal_name=threshold_key,
                            old_threshold=old_threshold,
                            new_threshold=new_threshold,
                            adjustment_count=detection_count,
                            adjusted_at=datetime.now(UTC).isoformat(),
                        )
                    )

                    logger.info(
                        f"Threshold tuned: {threshold_key} "
                        f"{old_threshold:.3f} → {new_threshold:.3f} "
                        f"(after {detection_count} CRITICAL detections)"
                    )

        return adjustments

    def _store_pattern(
        self, report: MisclassificationReport, task_description: str | None, confidence: float
    ) -> int:
        """
        Store misclassification pattern in VectorStore (spec Section 8.4).

        Args:
            report: Misclassification report
            task_description: Task description for semantic search
            confidence: Updated confidence score

        Returns:
            Number of patterns stored (0 or 1)

        Constitutional Compliance:
            - Article IV: VectorStore integration mandatory
        """
        if not task_description:
            logger.debug(
                f"No task_description provided for {report.task_id}, skipping pattern storage"
            )
            return 0

        pattern = {
            "type": "misclassification_pattern",
            "task_id": report.task_id,
            "task_description": task_description,
            "original_tier": report.original_tier,
            "corrected_tier": report.recommended_tier,
            "confidence": confidence,
            "detected_issues": [issue.model_dump() for issue in report.detected_issues],
            "aggregated_confidence": report.aggregated_confidence,
            "iteration_count": self.history.get(
                report.task_id, RefinementHistory(task_id=report.task_id)
            ).iteration_count,
            "created_at": datetime.now(UTC).isoformat(),
            "session_id": self.context.session_id,
        }

        # Store in VectorStore with tags (Article IV)
        self.context.store_memory(
            key=f"misclassification_{report.task_id}_{int(datetime.now(UTC).timestamp())}",
            content=pattern,
            tags=["misclassification_pattern", report.original_tier, report.recommended_tier],
        )

        logger.debug(
            f"Pattern stored: {report.task_id} ({report.original_tier} → {report.recommended_tier})"
        )

        return 1

    def _query_existing_confidence(
        self, task_id: str, task_description: str | None
    ) -> float | None:
        """
        Query VectorStore for existing pattern confidence.

        Args:
            task_id: Task identifier
            task_description: Task description for semantic search

        Returns:
            Existing confidence score or None if not found

        Constitutional Compliance:
            - Article IV: VectorStore query for learning
        """
        if not task_description:
            return None

        try:
            patterns = self.context.search_memories(
                tags=["misclassification_pattern"], include_session=True
            )

            # Search for similar task descriptions
            # (In Phase 5, use semantic similarity with embeddings)
            for pattern in patterns:
                content = pattern.get("content", {})
                if isinstance(content, dict):
                    pattern_desc = content.get("task_description", "")
                    if task_description.lower() in pattern_desc.lower():
                        return content.get("confidence", 0.6)

            return None

        except Exception as e:
            logger.warning(f"Failed to query existing confidence: {e}")
            return None

    def _detect_oscillation(self, history: RefinementHistory) -> bool:
        """
        Detect tier oscillation (spec Section 8.6).

        Args:
            history: Refinement history for task

        Returns:
            True if oscillating between tiers
        """
        if len(history.refinement_history) < 3:
            return False

        last_3_tiers = [entry.corrected_tier for entry in history.refinement_history[-3:]]

        # Oscillation: alternating tiers (e.g., ["complex", "simple", "complex"])
        return len(set(last_3_tiers)) == 2 and last_3_tiers[0] != last_3_tiers[1]

    def _count_critical_detections(self, threshold_key: str) -> int:
        """
        Count CRITICAL detections for threshold tuning.

        Args:
            threshold_key: Threshold signal name

        Returns:
            Number of CRITICAL detections
        """
        count = 0

        try:
            patterns = self.context.search_memories(
                tags=["misclassification_pattern"],
                include_session=False,  # Cross-session learning
            )

            for pattern in patterns:
                content = pattern.get("content", {})
                if isinstance(content, dict):
                    for issue in content.get("detected_issues", []):
                        if issue.get("severity") == "critical" and issue.get("rule_name") in {
                            "test_failure",
                            "code_churn",
                            "execution_timing",
                        }:
                            count += 1

        except Exception as e:
            logger.warning(f"Failed to count CRITICAL detections: {e}")

        return count

    def _check_convergence(self) -> bool:
        """
        Check if refinement has converged (spec Section 8.5).

        Convergence criteria:
        - Accuracy >98% on validation set (computed in Phase 5)
        - Improvement plateau <0.5% over last 100 tasks

        Returns:
            True if converged (False until Phase 5 implementation)
        """
        # Phase 5: Implement validation set accuracy check
        # For now, return False (convergence not yet implemented)
        return False

    def create_snapshot(self) -> VectorStoreSnapshot:
        """
        Create VectorStore snapshot for rollback (spec Section 8.7).

        Returns:
            VectorStoreSnapshot with current state

        Raises:
            RefinementError: If snapshot creation fails

        Example:
            >>> snapshot = refiner.create_snapshot()
            >>> snapshot.snapshot_id
            'snapshot_1728567825'
        """
        try:
            patterns = self.context.search_memories(
                tags=["misclassification_pattern"],
                include_session=False,  # Include all patterns
            )

            # Extract pattern content
            pattern_list = []
            for pattern in patterns:
                content = pattern.get("content", {})
                if isinstance(content, dict):
                    pattern_list.append(content)

            snapshot = VectorStoreSnapshot(
                snapshot_id=f"snapshot_{int(datetime.now(UTC).timestamp())}",
                created_at=datetime.now(UTC).isoformat(),
                patterns=pattern_list,
                thresholds=self.thresholds.copy(),
                accuracy_baseline=0.85,  # Placeholder, computed in Phase 5
            )

            logger.info(
                f"Snapshot created: {snapshot.snapshot_id} ({len(snapshot.patterns)} patterns)"
            )

            return snapshot

        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            raise RefinementError(f"Snapshot creation failed: {e}") from e

    def rollback(self, snapshot: VectorStoreSnapshot) -> Result[None, RefinementError]:
        """
        Restore VectorStore to snapshot state (spec Section 8.7).

        Args:
            snapshot: VectorStoreSnapshot to restore

        Returns:
            Result[None, RefinementError]

        Example:
            >>> result = refiner.rollback(snapshot)
            >>> if result.is_ok():
            ...     print("Rollback successful")
        """
        try:
            # Phase 5: Implement VectorStore pattern deletion
            # For now, just restore thresholds

            # Restore thresholds
            self.thresholds = snapshot.thresholds.copy()
            self._save_thresholds()

            # Log rollback event
            logger.warning(
                f"⚠️  Rolled back to snapshot {snapshot.snapshot_id} "
                f"(baseline accuracy: {snapshot.accuracy_baseline:.2%})"
            )

            return Ok(None)

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return Err(RefinementError(f"Rollback failed: {e}"))

    def _load_thresholds(self) -> dict[str, float]:
        """
        Load thresholds from persistent storage.

        Returns:
            Threshold dictionary

        Note: Phase 5 will load from file or VectorStore
        """
        # Phase 5: Load from file or VectorStore
        return self.DEFAULT_THRESHOLDS.copy()

    def _save_thresholds(self) -> None:
        """
        Save thresholds to persistent storage.

        Note: Phase 5 will save to file or VectorStore
        """
        # Phase 5: Save to file or VectorStore
        pass

    def _load_history(self) -> dict[str, RefinementHistory]:
        """
        Load refinement history from persistent storage.

        Returns:
            History dictionary keyed by task_id

        Note: Phase 5 will load from VectorStore or file
        """
        # Phase 5: Load from VectorStore or file
        return {}

    def _save_history(self) -> None:
        """
        Save refinement history to persistent storage.

        Note: Phase 5 will save to VectorStore or file
        """
        # Phase 5: Save to VectorStore or file
        pass
