"""User feedback CLI command for quality feedback loop.

Usage:
    agency feedback mark <task_id> --original_tier=simple --correct_tier=complex [--description="Fix bug"]
    agency feedback list [--limit=10]
    agency feedback clear <task_id>
    agency feedback milestone [--generate] [--history] [--reset]

Constitutional Compliance:
- Article II: Result pattern for error handling (no exceptions for control flow)
- Article IV: VectorStore integration (user feedback stored with confidence=1.0)
- Article V: Follows spec-004-quality-feedback-loop.md Section 7.1 Rule 4

Reference: /Users/am/Code/Agency/specs/spec-004-quality-feedback-loop.md Section 7.1
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC

from shared.models.misclassification_report import MisclassificationReport, DetectedIssue
from shared.models.quality_signals import SeverityLevel
from tools.quality_feedback.rule_refiner import RuleRefiner
from tools.quality_feedback.monitoring_service import MonitoringService
from shared.agent_context import create_agent_context
from shared.type_definitions.result import Result, Ok, Err

logger = logging.getLogger(__name__)


class FeedbackCommandError(Exception):
    """Raised when feedback command fails."""
    pass


class FeedbackCommand:
    """Handle user feedback for task misclassifications.

    Stores user feedback in:
    1. File-based store: ~/.agency/memories/feedback/{task_id}.json
    2. VectorStore: Via RuleRefiner for immediate pattern update

    User feedback has highest confidence (1.0) and triggers immediate refinement.

    Example:
        >>> cmd = FeedbackCommand()
        >>> result = cmd.mark_misclassified(
        ...     task_id="task_42",
        ...     original_tier="simple",
        ...     correct_tier="complex",
        ...     description="Fix critical bug"
        ... )
        >>> if result.is_ok():
        ...     print("Feedback stored and refinement triggered")
    """

    FEEDBACK_DIR = Path.home() / ".agency" / "memories" / "feedback"

    def __init__(self):
        """Initialize feedback command with VectorStore context."""
        self.context = create_agent_context(session_id="feedback_cli")
        self.refiner = RuleRefiner(self.context)
        self.FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

        logger.debug(f"FeedbackCommand initialized: {self.FEEDBACK_DIR}")

    def mark_misclassified(
        self,
        task_id: str,
        original_tier: str,
        correct_tier: str,
        description: Optional[str] = None
    ) -> Result[None, FeedbackCommandError]:
        """Mark task as misclassified with user feedback.

        Args:
            task_id: Task identifier
            original_tier: Tier task was routed to (simple/moderate/complex)
            correct_tier: Correct tier (user's judgment)
            description: Optional task description for VectorStore embedding

        Returns:
            Result[None, FeedbackCommandError]

        Constitutional Compliance:
            - Article II: Result pattern for error handling
            - Article IV: VectorStore update via RuleRefiner
            - Article V: Follows spec Section 7.1 Rule 4

        Example:
            >>> result = cmd.mark_misclassified(
            ...     task_id="task_42",
            ...     original_tier="simple",
            ...     correct_tier="complex"
            ... )
        """
        try:
            # Validate tier values
            valid_tiers = {"simple", "moderate", "complex"}
            if original_tier not in valid_tiers or correct_tier not in valid_tiers:
                return Err(FeedbackCommandError(
                    f"Invalid tier. Must be one of: {valid_tiers}"
                ))

            # Store user feedback in file (for SignalCollector retrieval)
            feedback_data = {
                "task_id": task_id,
                "original_tier": original_tier,
                "correct_tier": correct_tier,
                "feedback": "misclassified",
                "marked_at": datetime.now(UTC).isoformat()
            }

            feedback_file = self.FEEDBACK_DIR / f"{task_id}.json"
            with open(feedback_file, "w") as f:
                json.dump(feedback_data, f, indent=2)

            print(f"✅ User feedback stored: {feedback_file}")

            # Create misclassification report for immediate refinement
            report = MisclassificationReport(
                task_id=task_id,
                original_tier=original_tier,
                recommended_tier=correct_tier,
                detected_issues=[
                    DetectedIssue(
                        rule_name="user_feedback",
                        confidence=1.0,  # Highest confidence
                        severity=SeverityLevel.CRITICAL,
                        description="User explicitly flagged as misclassified",
                        signal_value=None
                    )
                ],
                aggregated_confidence=1.0,  # User feedback always 1.0
                is_misclassified=True,
                detected_at=datetime.now(UTC).isoformat()
            )

            # Trigger immediate refinement
            print(f"🔄 Triggering immediate VectorStore refinement...")
            refinement_result = self.refiner.refine(report, task_description=description)

            if refinement_result.is_err():
                error = refinement_result.unwrap_err()
                print(f"⚠️  Refinement failed: {error}")
                print(f"   Feedback stored, but VectorStore not updated")
                return Ok(None)  # Soft failure, feedback still saved

            refinement = refinement_result.unwrap()

            print(f"✅ Refinement complete:")
            print(f"   Task: {task_id}")
            print(f"   Classification: {original_tier} → {correct_tier}")

            # Handle confidence_before being None
            if refinement.confidence_before is not None:
                print(f"   Confidence: {refinement.confidence_before:.2f} → {refinement.confidence_after:.2f}")
            else:
                print(f"   Confidence: N/A → {refinement.confidence_after:.2f}")

            print(f"   Patterns updated: {refinement.patterns_updated}")
            print(f"   Iteration: {refinement.iteration_count}/3")

            # Show threshold adjustments if any
            if refinement.threshold_adjustments:
                print(f"   Threshold adjustments:")
                for adj in refinement.threshold_adjustments:
                    print(f"     - {adj.signal_name}: {adj.old_threshold:.2f} → {adj.new_threshold:.2f}")

            return Ok(None)

        except Exception as e:
            logger.error(f"Failed to mark feedback: {e}")
            return Err(FeedbackCommandError(f"Failed to mark feedback: {e}"))

    def list_feedback(self, limit: int = 10) -> Result[List[Dict[str, Any]], FeedbackCommandError]:
        """List recent user feedback entries.

        Args:
            limit: Max number of entries to return

        Returns:
            Result[List[Dict[str, Any]], FeedbackCommandError]

        Example:
            >>> result = cmd.list_feedback(limit=5)
            >>> if result.is_ok():
            ...     entries = result.unwrap()
            ...     for entry in entries:
            ...         print(entry["task_id"])
        """
        try:
            feedback_files = sorted(
                self.FEEDBACK_DIR.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:limit]

            entries = []
            for feedback_file in feedback_files:
                with open(feedback_file) as f:
                    data = json.load(f)
                    entries.append(data)

            return Ok(entries)

        except Exception as e:
            logger.error(f"Failed to list feedback: {e}")
            return Err(FeedbackCommandError(f"Failed to list feedback: {e}"))

    def clear_feedback(self, task_id: str) -> Result[None, FeedbackCommandError]:
        """Clear user feedback for a task.

        Args:
            task_id: Task identifier

        Returns:
            Result[None, FeedbackCommandError]

        Example:
            >>> result = cmd.clear_feedback(task_id="task_42")
        """
        try:
            feedback_file = self.FEEDBACK_DIR / f"{task_id}.json"

            if not feedback_file.exists():
                return Err(FeedbackCommandError(f"No feedback found for task {task_id}"))

            feedback_file.unlink()
            print(f"✅ Feedback cleared for task {task_id}")

            return Ok(None)

        except Exception as e:
            logger.error(f"Failed to clear feedback: {e}")
            return Err(FeedbackCommandError(f"Failed to clear feedback: {e}"))


def cmd_feedback_mark(args: argparse.Namespace) -> None:
    """Handle 'agency feedback mark' command.

    Args:
        args: Argparse namespace with task_id, original_tier, correct_tier, description
    """
    cmd = FeedbackCommand()

    result = cmd.mark_misclassified(
        task_id=args.task_id,
        original_tier=args.original_tier,
        correct_tier=args.correct_tier,
        description=args.description
    )

    if result.is_err():
        error = result.unwrap_err()
        print(f"❌ Error: {error}")
        exit(1)


def cmd_feedback_list(args: argparse.Namespace) -> None:
    """Handle 'agency feedback list' command.

    Args:
        args: Argparse namespace with limit
    """
    cmd = FeedbackCommand()

    result = cmd.list_feedback(limit=args.limit)

    if result.is_err():
        error = result.unwrap_err()
        print(f"❌ Error: {error}")
        exit(1)

    entries = result.unwrap()

    if not entries:
        print("No user feedback found.")
        return

    print(f"\nRecent user feedback ({len(entries)} entries):\n")
    for entry in entries:
        print(f"  Task: {entry['task_id']}")
        print(f"    Original tier: {entry['original_tier']}")
        print(f"    Correct tier: {entry['correct_tier']}")
        print(f"    Marked at: {entry['marked_at']}")
        print()


def cmd_feedback_clear(args: argparse.Namespace) -> None:
    """Handle 'agency feedback clear' command.

    Args:
        args: Argparse namespace with task_id
    """
    cmd = FeedbackCommand()

    result = cmd.clear_feedback(task_id=args.task_id)

    if result.is_err():
        error = result.unwrap_err()
        print(f"❌ Error: {error}")
        exit(1)


def cmd_feedback_milestone(args: argparse.Namespace) -> None:
    """Handle 'agency feedback milestone' command.

    Args:
        args: Argparse namespace with generate, history, reset flags
    """
    service = MonitoringService()

    # Show current status by default
    if not args.generate and not args.history and not args.reset:
        current_count = service.get_current_count()
        history = service.get_history()

        print(f"\n📊 Monitoring Status:")
        print(f"   Session ID: {service._counter.session_id}")
        print(f"   Current count: {current_count}")
        print(f"   Milestones reached: {len(history.milestones)}/4")
        print(f"   Complete: {'✅' if history.is_complete else '⏳'}")

        if history.milestones:
            latest = history.get_latest_milestone()
            print(f"\n   Latest milestone: #{latest.milestone_number} ({latest.task_threshold} tasks)")
            print(f"   Overall accuracy: {latest.metrics.overall_accuracy:.1%}")
            print(f"   Improving: {'✅' if latest.is_improving else '⚠️'}")

        if history.is_complete:
            print(f"\n   Final accuracy: {history.final_accuracy:.1%}")
            print(f"   Total improvement: +{history.accuracy_improvement:.1%}")

        # Show next milestone
        if current_count < 100:
            next_threshold = None
            for threshold in MonitoringService.MILESTONES:
                if current_count < threshold:
                    next_threshold = threshold
                    break
            if next_threshold:
                tasks_to_go = next_threshold - current_count
                print(f"\n   Next milestone: {next_threshold} tasks ({tasks_to_go} to go)")

        return

    # Generate milestone report manually
    if args.generate:
        milestone = service.generate_milestone_report(force=True)

        if milestone is None:
            print("⚠️  No milestone to generate (need at least 25 tasks)")
            return

        print(f"\n🎯 Milestone {milestone.milestone_number} Generated!")
        print(f"   Tasks: {milestone.tasks_processed}/{milestone.task_threshold}")
        print(f"   Overall Accuracy: {milestone.metrics.overall_accuracy:.1%}")
        print(f"   Interval Accuracy: {milestone.metrics.interval_accuracy:.1%}")
        print(f"   Improving: {'✅' if milestone.is_improving else '⚠️'}")

        if milestone.accuracy_delta is not None:
            print(f"   Accuracy delta: {milestone.accuracy_delta:+.1%}")

        print(f"\n   Dashboard: {milestone.dashboard_snapshot_path}")

        if milestone.top_misclassification_patterns:
            print(f"\n   Top Patterns:")
            for pattern in milestone.top_misclassification_patterns:
                print(f"      - {pattern}")

        if milestone.recommended_actions:
            print(f"\n   Recommendations:")
            for action in milestone.recommended_actions:
                print(f"      {action}")

        return

    # Show milestone history
    if args.history:
        history = service.get_history()

        print(f"\n📈 Milestone History:")
        print(f"   Session: {history.monitoring_session_id}")
        print(f"   Started: {history.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Milestones: {len(history.milestones)}/4\n")

        for milestone in history.milestones:
            print(f"   #{milestone.milestone_number} - {milestone.task_threshold} tasks")
            print(f"      Reached: {milestone.reached_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      Accuracy: {milestone.metrics.overall_accuracy:.1%}")
            print(f"      Interval: {milestone.metrics.interval_accuracy:.1%}")
            print(f"      Improving: {'✅' if milestone.is_improving else '⚠️'}")
            if milestone.accuracy_delta is not None:
                print(f"      Delta: {milestone.accuracy_delta:+.1%}")
            print()

        if history.is_complete:
            print(f"   ✅ Monitoring Complete!")
            print(f"   Final accuracy: {history.final_accuracy:.1%}")
            if history.accuracy_improvement:
                print(f"   Total improvement: +{history.accuracy_improvement:.1%}")

            progression = history.calculate_progression_rate()
            if progression:
                print(f"   Avg improvement/milestone: +{progression:.1%}")

        return

    # Reset monitoring (with confirmation)
    if args.reset:
        if not args.force:
            print("⚠️  WARNING: This will delete all milestone data and reset the counter.")
            response = input("Continue? [y/N]: ")
            if response.lower() != 'y':
                print("Reset cancelled.")
                return

        service.reset()
        print("✅ Monitoring service reset successfully.")
