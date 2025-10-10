"""
Tests for User Feedback CLI Command.

Tests the feedback CLI command implementation for quality feedback loop
(spec-004-quality-feedback-loop.md Section 7.1 Rule 4: User Feedback Override).

Constitutional Compliance:
- Article II: TDD MANDATORY - tests written FIRST before implementation
- Article IV: VectorStore integration (user feedback stored with confidence=1.0)
- Article V: Follows spec Section 7.1 (Rule 4)

Test Categories:
- Unit Tests: FeedbackCommand methods (10+ tests)
- Integration Tests: E2E workflow (3+ tests)
- Error Handling Tests: Invalid inputs, failures
- CLI Tests: Argparse integration

Reference: /Users/am/Code/Agency/specs/spec-004-quality-feedback-loop.md Section 7.1
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from shared.models.misclassification_report import DetectedIssue, MisclassificationReport
from shared.models.quality_signals import SeverityLevel
from shared.models.refinement_result import RefinementResult
from shared.type_definitions.result import Err, Ok
from tools.agency_cli.feedback_command import (
    FeedbackCommand,
    FeedbackCommandError,
    cmd_feedback_clear,
    cmd_feedback_list,
    cmd_feedback_mark,
)

# ============================================================================
# UNIT TESTS (10+ tests required)
# ============================================================================

class TestFeedbackCommandUnit:
    """Unit tests for FeedbackCommand class."""

    @pytest.fixture
    def temp_feedback_dir(self, tmp_path):
        """Create temporary feedback directory."""
        feedback_dir = tmp_path / ".agency" / "memories" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        # Patch FEEDBACK_DIR class attribute
        with patch.object(FeedbackCommand, 'FEEDBACK_DIR', feedback_dir):
            yield feedback_dir

    @pytest.fixture
    def mock_context(self):
        """Create mock AgentContext."""
        context = Mock()
        context.session_id = "test_feedback_session"
        context.store_memory = Mock()
        context.search_memories = Mock(return_value=[])
        return context

    @pytest.fixture
    def mock_refiner(self):
        """Create mock RuleRefiner."""
        refiner = Mock()

        # Mock successful refinement
        refinement = RefinementResult(
            task_id="task_42",
            patterns_updated=1,
            confidence_before=0.6,
            confidence_after=0.62,
            threshold_adjustments=[],
            iteration_count=1,
            convergence_achieved=False,
            accuracy_estimate=None,
            refined_at=datetime.now(UTC).isoformat()
        )

        refiner.refine = Mock(return_value=Ok(refinement))
        return refiner

    @pytest.fixture
    def feedback_command(self, temp_feedback_dir, mock_context, mock_refiner):
        """Create FeedbackCommand instance with mocks."""
        with patch('tools.agency_cli.feedback_command.create_agent_context', return_value=mock_context), \
             patch('tools.agency_cli.feedback_command.RuleRefiner', return_value=mock_refiner):
            cmd = FeedbackCommand()
            cmd.context = mock_context
            cmd.refiner = mock_refiner
            return cmd

    # Test 1: Valid tiers → feedback file created
    def test_mark_misclassified_valid_tiers_creates_file(
        self, feedback_command, temp_feedback_dir
    ):
        """Test mark_misclassified with valid tiers creates feedback file."""
        result = feedback_command.mark_misclassified(
            task_id="task_42",
            original_tier="simple",
            correct_tier="complex",
            description="Fix critical bug"
        )

        assert result.is_ok()

        # Check feedback file created
        feedback_file = temp_feedback_dir / "task_42.json"
        assert feedback_file.exists()

        # Validate file content
        with open(feedback_file) as f:
            data = json.load(f)

        assert data["task_id"] == "task_42"
        assert data["original_tier"] == "simple"
        assert data["correct_tier"] == "complex"
        assert data["feedback"] == "misclassified"
        assert "marked_at" in data

    # Test 2: Invalid tier → error returned
    def test_mark_misclassified_invalid_tier_returns_error(self, feedback_command):
        """Test mark_misclassified with invalid tier returns error."""
        result = feedback_command.mark_misclassified(
            task_id="task_42",
            original_tier="invalid_tier",  # Invalid
            correct_tier="complex",
            description="Fix bug"
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid tier" in str(error)

    # Test 3: Triggers refinement → RuleRefiner called
    def test_mark_misclassified_triggers_refinement(
        self, feedback_command, mock_refiner
    ):
        """Test mark_misclassified triggers immediate refinement."""
        result = feedback_command.mark_misclassified(
            task_id="task_42",
            original_tier="simple",
            correct_tier="complex",
            description="Fix bug"
        )

        assert result.is_ok()

        # Verify RuleRefiner.refine was called
        assert mock_refiner.refine.called
        call_args = mock_refiner.refine.call_args

        # Extract MisclassificationReport from call
        report = call_args[0][0]
        assert isinstance(report, MisclassificationReport)
        assert report.task_id == "task_42"
        assert report.original_tier == "simple"
        assert report.recommended_tier == "complex"
        assert report.aggregated_confidence == 1.0  # User feedback = 1.0
        assert report.is_misclassified is True

        # Verify CRITICAL severity with confidence 1.0
        issues = report.detected_issues
        assert len(issues) == 1
        assert issues[0].rule_name == "user_feedback"
        assert issues[0].confidence == 1.0
        assert issues[0].severity == SeverityLevel.CRITICAL

    # Test 4: List feedback → returns 5 most recent
    def test_list_feedback_returns_recent_entries(
        self, feedback_command, temp_feedback_dir
    ):
        """Test list_feedback returns most recent entries."""
        # Create 5 feedback files
        for i in range(5):
            feedback_file = temp_feedback_dir / f"task_{i}.json"
            data = {
                "task_id": f"task_{i}",
                "original_tier": "simple",
                "correct_tier": "complex",
                "feedback": "misclassified",
                "marked_at": datetime.now(UTC).isoformat()
            }
            with open(feedback_file, "w") as f:
                json.dump(data, f)

        result = feedback_command.list_feedback(limit=3)

        assert result.is_ok()
        entries = result.unwrap()
        assert len(entries) == 3  # Limited to 3

    # Test 5: Empty directory → returns empty list
    def test_list_feedback_empty_directory_returns_empty(
        self, feedback_command, temp_feedback_dir
    ):
        """Test list_feedback with empty directory returns empty list."""
        result = feedback_command.list_feedback(limit=10)

        assert result.is_ok()
        entries = result.unwrap()
        assert len(entries) == 0

    # Test 6: Clear feedback → file deleted
    def test_clear_feedback_deletes_file(
        self, feedback_command, temp_feedback_dir
    ):
        """Test clear_feedback deletes existing feedback file."""
        # Create feedback file
        feedback_file = temp_feedback_dir / "task_42.json"
        data = {
            "task_id": "task_42",
            "original_tier": "simple",
            "correct_tier": "complex",
            "feedback": "misclassified",
            "marked_at": datetime.now(UTC).isoformat()
        }
        with open(feedback_file, "w") as f:
            json.dump(data, f)

        assert feedback_file.exists()

        result = feedback_command.clear_feedback(task_id="task_42")

        assert result.is_ok()
        assert not feedback_file.exists()

    # Test 7: Clear non-existent → error returned
    def test_clear_feedback_non_existent_returns_error(self, feedback_command):
        """Test clear_feedback for non-existent task returns error."""
        result = feedback_command.clear_feedback(task_id="nonexistent")

        assert result.is_err()
        error = result.unwrap_err()
        assert "No feedback found" in str(error)

    # Test 8: User feedback stored with confidence=1.0
    def test_user_feedback_has_highest_confidence(
        self, feedback_command, mock_refiner
    ):
        """Test user feedback creates CRITICAL issue with confidence=1.0."""
        feedback_command.mark_misclassified(
            task_id="task_42",
            original_tier="simple",
            correct_tier="complex",
            description="Fix bug"
        )

        # Extract MisclassificationReport from refiner call
        call_args = mock_refiner.refine.call_args
        report = call_args[0][0]

        # Verify highest confidence
        assert report.aggregated_confidence == 1.0
        assert report.detected_issues[0].confidence == 1.0

    # Test 9: User feedback creates CRITICAL severity
    def test_user_feedback_creates_critical_severity(
        self, feedback_command, mock_refiner
    ):
        """Test user feedback creates CRITICAL severity issue."""
        feedback_command.mark_misclassified(
            task_id="task_42",
            original_tier="simple",
            correct_tier="complex",
            description="Fix bug"
        )

        # Extract MisclassificationReport
        call_args = mock_refiner.refine.call_args
        report = call_args[0][0]

        # Verify CRITICAL severity
        assert report.detected_issues[0].severity == SeverityLevel.CRITICAL

    # Test 10: Refinement result shows confidence update
    def test_refinement_result_shows_confidence_update(
        self, feedback_command, mock_refiner, capsys
    ):
        """Test refinement result displays confidence update."""
        feedback_command.mark_misclassified(
            task_id="task_42",
            original_tier="simple",
            correct_tier="complex",
            description="Fix bug"
        )

        # Verify refiner was called
        assert mock_refiner.refine.called

        # Check output contains confidence info
        captured = capsys.readouterr()
        assert "Confidence:" in captured.out
        assert "0.62" in captured.out  # confidence_after from mock

    # Test 11: Refinement failure → soft failure (feedback still saved)
    def test_refinement_failure_saves_feedback(
        self, feedback_command, mock_refiner, temp_feedback_dir
    ):
        """Test refinement failure doesn't prevent feedback storage."""
        # Mock refinement failure
        mock_refiner.refine = Mock(return_value=Err("Refinement failed"))

        result = feedback_command.mark_misclassified(
            task_id="task_42",
            original_tier="simple",
            correct_tier="complex",
            description="Fix bug"
        )

        # Should still succeed (soft failure)
        assert result.is_ok()

        # Feedback file should still be created
        feedback_file = temp_feedback_dir / "task_42.json"
        assert feedback_file.exists()

    # Test 12: No description provided → refinement skipped gracefully
    def test_no_description_skips_refinement(
        self, feedback_command, mock_refiner, temp_feedback_dir
    ):
        """Test missing description doesn't crash, refinement uses None."""
        result = feedback_command.mark_misclassified(
            task_id="task_42",
            original_tier="simple",
            correct_tier="complex",
            description=None  # No description
        )

        assert result.is_ok()

        # Verify refinement was called with None description
        call_args = mock_refiner.refine.call_args
        assert call_args[1]["task_description"] is None


# ============================================================================
# INTEGRATION TESTS (3+ tests required)
# ============================================================================

class TestFeedbackCommandIntegration:
    """Integration tests for E2E workflow."""

    @pytest.fixture
    def temp_feedback_dir(self, tmp_path):
        """Create temporary feedback directory."""
        feedback_dir = tmp_path / ".agency" / "memories" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(FeedbackCommand, 'FEEDBACK_DIR', feedback_dir):
            yield feedback_dir

    # Integration Test 1: E2E mark → list → clear workflow
    def test_e2e_mark_list_clear_workflow(self, temp_feedback_dir):
        """Test complete E2E workflow: mark → list → clear."""
        with patch('tools.agency_cli.feedback_command.create_agent_context') as mock_ctx, \
             patch('tools.agency_cli.feedback_command.RuleRefiner') as mock_refiner_cls:

            # Setup mocks
            mock_context = Mock()
            mock_context.session_id = "test"
            mock_ctx.return_value = mock_context

            mock_refiner = Mock()
            refinement = RefinementResult(
                task_id="task_42",
                patterns_updated=1,
                confidence_before=0.6,
                confidence_after=0.62,
                threshold_adjustments=[],
                iteration_count=1,
                convergence_achieved=False,
                accuracy_estimate=None,
                refined_at=datetime.now(UTC).isoformat()
            )
            mock_refiner.refine = Mock(return_value=Ok(refinement))
            mock_refiner_cls.return_value = mock_refiner

            cmd = FeedbackCommand()

            # Step 1: Mark as misclassified
            mark_result = cmd.mark_misclassified(
                task_id="task_42",
                original_tier="simple",
                correct_tier="complex",
                description="Fix bug"
            )
            assert mark_result.is_ok()

            # Step 2: List feedback (should show 1 entry)
            list_result = cmd.list_feedback(limit=10)
            assert list_result.is_ok()
            entries = list_result.unwrap()
            assert len(entries) == 1
            assert entries[0]["task_id"] == "task_42"

            # Step 3: Clear feedback
            clear_result = cmd.clear_feedback(task_id="task_42")
            assert clear_result.is_ok()

            # Step 4: List again (should be empty)
            list_result_2 = cmd.list_feedback(limit=10)
            assert list_result_2.is_ok()
            entries_2 = list_result_2.unwrap()
            assert len(entries_2) == 0

    # Integration Test 2: E2E mark → VectorStore pattern updated
    def test_e2e_mark_updates_vectorstore(self, temp_feedback_dir):
        """Test mark triggers VectorStore pattern update."""
        with patch('tools.agency_cli.feedback_command.create_agent_context') as mock_ctx, \
             patch('tools.agency_cli.feedback_command.RuleRefiner') as mock_refiner_cls:

            # Setup mocks
            mock_context = Mock()
            mock_context.session_id = "test"
            mock_context.store_memory = Mock()
            mock_ctx.return_value = mock_context

            mock_refiner = Mock()
            refinement = RefinementResult(
                task_id="task_42",
                patterns_updated=1,
                confidence_before=0.6,
                confidence_after=0.62,
                threshold_adjustments=[],
                iteration_count=1,
                convergence_achieved=False,
                accuracy_estimate=None,
                refined_at=datetime.now(UTC).isoformat()
            )
            mock_refiner.refine = Mock(return_value=Ok(refinement))
            mock_refiner_cls.return_value = mock_refiner

            cmd = FeedbackCommand()

            # Mark as misclassified
            cmd.mark_misclassified(
                task_id="task_42",
                original_tier="simple",
                correct_tier="complex",
                description="Fix critical bug"
            )

            # Verify RuleRefiner.refine was called (which updates VectorStore)
            assert mock_refiner.refine.called

    # Integration Test 3: E2E immediate refinement applied
    def test_e2e_immediate_refinement_applied(self, temp_feedback_dir, capsys):
        """Test immediate refinement is triggered (no wait for next execution)."""
        with patch('tools.agency_cli.feedback_command.create_agent_context') as mock_ctx, \
             patch('tools.agency_cli.feedback_command.RuleRefiner') as mock_refiner_cls:

            # Setup mocks
            mock_context = Mock()
            mock_context.session_id = "test"
            mock_ctx.return_value = mock_context

            mock_refiner = Mock()
            refinement = RefinementResult(
                task_id="task_42",
                patterns_updated=1,
                confidence_before=None,  # No prior pattern
                confidence_after=0.62,
                threshold_adjustments=[],
                iteration_count=1,
                convergence_achieved=False,
                accuracy_estimate=None,
                refined_at=datetime.now(UTC).isoformat()
            )
            mock_refiner.refine = Mock(return_value=Ok(refinement))
            mock_refiner_cls.return_value = mock_refiner

            cmd = FeedbackCommand()

            # Mark and capture output
            cmd.mark_misclassified(
                task_id="task_42",
                original_tier="simple",
                correct_tier="complex",
                description="Fix bug"
            )

            # Verify immediate refinement message
            captured = capsys.readouterr()
            assert "Triggering immediate VectorStore refinement" in captured.out
            assert "Refinement complete" in captured.out


# ============================================================================
# CLI INTEGRATION TESTS (argparse)
# ============================================================================

class TestFeedbackCLI:
    """Test CLI command handlers."""

    @pytest.fixture
    def temp_feedback_dir(self, tmp_path):
        """Create temporary feedback directory."""
        feedback_dir = tmp_path / ".agency" / "memories" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(FeedbackCommand, 'FEEDBACK_DIR', feedback_dir):
            yield feedback_dir

    def test_cmd_feedback_mark_success(self, temp_feedback_dir, capsys):
        """Test cmd_feedback_mark CLI handler with valid args."""
        with patch('tools.agency_cli.feedback_command.create_agent_context') as mock_ctx, \
             patch('tools.agency_cli.feedback_command.RuleRefiner') as mock_refiner_cls:

            # Setup mocks
            mock_context = Mock()
            mock_context.session_id = "test"
            mock_ctx.return_value = mock_context

            mock_refiner = Mock()
            refinement = RefinementResult(
                task_id="task_42",
                patterns_updated=1,
                confidence_before=0.6,
                confidence_after=0.62,
                threshold_adjustments=[],
                iteration_count=1,
                convergence_achieved=False,
                accuracy_estimate=None,
                refined_at=datetime.now(UTC).isoformat()
            )
            mock_refiner.refine = Mock(return_value=Ok(refinement))
            mock_refiner_cls.return_value = mock_refiner

            # Create mock args
            args = Mock()
            args.task_id = "task_42"
            args.original_tier = "simple"
            args.correct_tier = "complex"
            args.description = "Fix bug"

            # Execute CLI command
            cmd_feedback_mark(args)

            # Should complete without error
            captured = capsys.readouterr()
            assert "User feedback stored" in captured.out

    def test_cmd_feedback_mark_failure_exits(self, temp_feedback_dir):
        """Test cmd_feedback_mark exits with code 1 on error."""
        with patch('tools.agency_cli.feedback_command.create_agent_context') as mock_ctx, \
             patch('tools.agency_cli.feedback_command.RuleRefiner') as mock_refiner_cls:

            mock_context = Mock()
            mock_ctx.return_value = mock_context
            mock_refiner_cls.return_value = Mock()

            # Create args with invalid tier
            args = Mock()
            args.task_id = "task_42"
            args.original_tier = "invalid"
            args.correct_tier = "complex"
            args.description = None

            # Should exit with code 1
            with pytest.raises(SystemExit) as exc_info:
                cmd_feedback_mark(args)

            assert exc_info.value.code == 1

    def test_cmd_feedback_list_displays_entries(self, temp_feedback_dir, capsys):
        """Test cmd_feedback_list displays feedback entries."""
        # Create feedback file
        feedback_file = temp_feedback_dir / "task_42.json"
        data = {
            "task_id": "task_42",
            "original_tier": "simple",
            "correct_tier": "complex",
            "feedback": "misclassified",
            "marked_at": "2025-10-10T12:00:00Z"
        }
        with open(feedback_file, "w") as f:
            json.dump(data, f)

        with patch('tools.agency_cli.feedback_command.create_agent_context'), \
             patch('tools.agency_cli.feedback_command.RuleRefiner'):

            args = Mock()
            args.limit = 10

            cmd_feedback_list(args)

            captured = capsys.readouterr()
            assert "task_42" in captured.out
            assert "simple" in captured.out
            assert "complex" in captured.out

    def test_cmd_feedback_clear_success(self, temp_feedback_dir, capsys):
        """Test cmd_feedback_clear deletes feedback."""
        # Create feedback file
        feedback_file = temp_feedback_dir / "task_42.json"
        data = {
            "task_id": "task_42",
            "original_tier": "simple",
            "correct_tier": "complex",
            "feedback": "misclassified",
            "marked_at": "2025-10-10T12:00:00Z"
        }
        with open(feedback_file, "w") as f:
            json.dump(data, f)

        with patch('tools.agency_cli.feedback_command.create_agent_context'), \
             patch('tools.agency_cli.feedback_command.RuleRefiner'):

            args = Mock()
            args.task_id = "task_42"

            cmd_feedback_clear(args)

            captured = capsys.readouterr()
            assert "Feedback cleared" in captured.out
            assert not feedback_file.exists()


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestFeedbackCommandErrors:
    """Test error handling scenarios."""

    @pytest.fixture
    def temp_feedback_dir(self, tmp_path):
        """Create temporary feedback directory."""
        feedback_dir = tmp_path / ".agency" / "memories" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(FeedbackCommand, 'FEEDBACK_DIR', feedback_dir):
            yield feedback_dir

    def test_invalid_original_tier(self, temp_feedback_dir):
        """Test invalid original_tier parameter."""
        with patch('tools.agency_cli.feedback_command.create_agent_context'), \
             patch('tools.agency_cli.feedback_command.RuleRefiner'):

            cmd = FeedbackCommand()

            result = cmd.mark_misclassified(
                task_id="task_42",
                original_tier="invalid",
                correct_tier="complex",
                description="Fix bug"
            )

            assert result.is_err()
            assert "Invalid tier" in str(result.unwrap_err())

    def test_invalid_correct_tier(self, temp_feedback_dir):
        """Test invalid correct_tier parameter."""
        with patch('tools.agency_cli.feedback_command.create_agent_context'), \
             patch('tools.agency_cli.feedback_command.RuleRefiner'):

            cmd = FeedbackCommand()

            result = cmd.mark_misclassified(
                task_id="task_42",
                original_tier="simple",
                correct_tier="invalid",
                description="Fix bug"
            )

            assert result.is_err()
            assert "Invalid tier" in str(result.unwrap_err())

    def test_exception_during_refinement(self, temp_feedback_dir):
        """Test exception during refinement is handled gracefully."""
        with patch('tools.agency_cli.feedback_command.create_agent_context') as mock_ctx, \
             patch('tools.agency_cli.feedback_command.RuleRefiner') as mock_refiner_cls:

            mock_context = Mock()
            mock_ctx.return_value = mock_context

            # Mock refiner that raises exception
            mock_refiner = Mock()
            mock_refiner.refine = Mock(side_effect=Exception("VectorStore failure"))
            mock_refiner_cls.return_value = mock_refiner

            cmd = FeedbackCommand()

            # Should not crash, feedback still saved (soft failure)
            result = cmd.mark_misclassified(
                task_id="task_42",
                original_tier="simple",
                correct_tier="complex",
                description="Fix bug"
            )

            # Feedback file should exist despite exception
            feedback_file = temp_feedback_dir / "task_42.json"
            assert feedback_file.exists()


# ============================================================================
# COVERAGE TESTS (ensure >95%)
# ============================================================================

class TestFeedbackCommandCoverage:
    """Additional tests to ensure >95% coverage."""

    @pytest.fixture
    def temp_feedback_dir(self, tmp_path):
        """Create temporary feedback directory."""
        feedback_dir = tmp_path / ".agency" / "memories" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(FeedbackCommand, 'FEEDBACK_DIR', feedback_dir):
            yield feedback_dir

    def test_feedback_directory_created_if_missing(self, tmp_path):
        """Test FEEDBACK_DIR is created if it doesn't exist."""
        feedback_dir = tmp_path / ".agency" / "memories" / "feedback"

        # Ensure directory doesn't exist
        assert not feedback_dir.exists()

        with patch.object(FeedbackCommand, 'FEEDBACK_DIR', feedback_dir), \
             patch('tools.agency_cli.feedback_command.create_agent_context'), \
             patch('tools.agency_cli.feedback_command.RuleRefiner'):

            cmd = FeedbackCommand()

            # Directory should be created
            assert feedback_dir.exists()

    def test_list_feedback_empty_message(self, temp_feedback_dir, capsys):
        """Test list_feedback displays message when no entries found."""
        with patch('tools.agency_cli.feedback_command.create_agent_context'), \
             patch('tools.agency_cli.feedback_command.RuleRefiner'):

            args = Mock()
            args.limit = 10

            cmd_feedback_list(args)

            captured = capsys.readouterr()
            assert "No user feedback found" in captured.out

    def test_threshold_adjustments_displayed(self, temp_feedback_dir, capsys):
        """Test threshold adjustments are displayed in output."""
        from shared.models.refinement_result import ThresholdAdjustment

        with patch('tools.agency_cli.feedback_command.create_agent_context') as mock_ctx, \
             patch('tools.agency_cli.feedback_command.RuleRefiner') as mock_refiner_cls:

            mock_context = Mock()
            mock_ctx.return_value = mock_context

            mock_refiner = Mock()

            # Mock refinement with threshold adjustments
            threshold_adj = ThresholdAdjustment(
                signal_name="test_failure_rate",
                old_threshold=0.1,
                new_threshold=0.09,
                adjustment_count=3,
                adjusted_at=datetime.now(UTC).isoformat()
            )

            refinement = RefinementResult(
                task_id="task_42",
                patterns_updated=1,
                confidence_before=0.6,
                confidence_after=0.62,
                threshold_adjustments=[threshold_adj],
                iteration_count=1,
                convergence_achieved=False,
                accuracy_estimate=None,
                refined_at=datetime.now(UTC).isoformat()
            )

            mock_refiner.refine = Mock(return_value=Ok(refinement))
            mock_refiner_cls.return_value = mock_refiner

            cmd = FeedbackCommand()

            cmd.mark_misclassified(
                task_id="task_42",
                original_tier="simple",
                correct_tier="complex",
                description="Fix bug"
            )

            captured = capsys.readouterr()
            assert "Threshold adjustments" in captured.out
            assert "test_failure_rate" in captured.out
            assert "0.10" in captured.out
            assert "0.09" in captured.out
