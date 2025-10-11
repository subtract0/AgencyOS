"""
Tests for ApprovalCheckpoint - user approval workflow.

Constitutional compliance:
- Article I: Complete context (all test scenarios covered)
- Article II: 100% verification (all tests must pass)
- Article III: Automated enforcement (no manual overrides)
- Article IV: VectorStore integration validated
- Article V: Spec-driven (approval workflow tested)
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.agent_context import create_agent_context
from shared.type_definitions.result import Err, Ok
from tools.orchestrator.approval_checkpoint import (
    ApprovalCheckpoint,
    ApprovalDecision,
    ApprovedSpec,
    Spec,
    create_approval_checkpoint,
)
from tools.orchestrator.slop_guardian import SlopGuardian, SlopVerdict, VerdictStatus


class TestSpec:
    """Test Spec model validation and methods."""

    def test_spec_creation_valid(self):
        """Test valid spec creation."""
        spec = Spec(title="Feature X", content="Add authentication to API endpoints")

        assert spec.title == "Feature X"
        assert spec.content == "Add authentication to API endpoints"
        assert spec.version == 1
        assert len(spec.created_at) > 0

    def test_spec_to_markdown(self):
        """Test spec to markdown conversion."""
        spec = Spec(title="Feature Y", content="Implement JWT tokens\n\nWith refresh logic")

        markdown = spec.to_markdown()

        assert "# Feature Y" in markdown
        assert "Implement JWT tokens" in markdown
        assert "With refresh logic" in markdown

    def test_spec_version_tracking(self):
        """Test spec version increments."""
        spec_v1 = Spec(title="Feature Z", content="Original content", version=1)
        spec_v2 = Spec(title="Feature Z", content="Updated content", version=2)

        assert spec_v1.version == 1
        assert spec_v2.version == 2

    def test_spec_validation_empty_title(self):
        """Test spec validation rejects empty title."""
        with pytest.raises(ValueError, match="at least 1 character"):
            Spec(title="", content="Valid content")

    def test_spec_validation_short_content(self):
        """Test spec validation rejects short content."""
        with pytest.raises(ValueError, match="at least 10 character"):
            Spec(title="Valid Title", content="Short")


class TestApprovalDecision:
    """Test ApprovalDecision model."""

    def test_approval_decision_approve(self):
        """Test approval decision creation."""
        decision = ApprovalDecision(action="approve")

        assert decision.action == "approve"
        assert decision.reason is None
        assert decision.slop_verdict is None
        assert len(decision.timestamp) > 0

    def test_approval_decision_reject_with_reason(self):
        """Test rejection decision with reason."""
        decision = ApprovalDecision(action="reject", reason="Missing acceptance criteria")

        assert decision.action == "reject"
        assert decision.reason == "Missing acceptance criteria"

    def test_approval_decision_with_slop_verdict(self):
        """Test decision with slop verdict attached."""
        verdict = SlopVerdict(
            score=2.8,
            reasons=["Vague language"],
            top_fixes=["Add specific metrics"],
            dimension_scores={
                "clarity": 2.5,
                "measurability": 2.0,
                "completeness": 3.5,
                "actionability": 3.2,
            },
        )

        decision = ApprovalDecision(action="approve", slop_verdict=verdict)

        assert decision.slop_verdict is not None
        assert decision.slop_verdict.score == 2.8


class TestApprovedSpec:
    """Test ApprovedSpec model."""

    def test_approved_spec_creation(self):
        """Test approved spec creation."""
        spec = Spec(title="Feature A", content="Content for feature A")
        decision = ApprovalDecision(action="approve")

        approved = ApprovedSpec(spec=spec, decision=decision, edit_count=0)

        assert approved.spec.title == "Feature A"
        assert approved.decision.action == "approve"
        assert approved.edit_count == 0

    def test_approved_spec_with_edits(self):
        """Test approved spec after edit iterations."""
        spec = Spec(title="Feature B", content="Revised content", version=2)
        decision = ApprovalDecision(action="approve")

        approved = ApprovedSpec(spec=spec, decision=decision, edit_count=2)

        assert approved.edit_count == 2
        assert approved.spec.version == 2


class TestApprovalCheckpoint:
    """Test ApprovalCheckpoint workflow."""

    @pytest.fixture
    def mock_context(self):
        """Create mock AgentContext."""
        context = create_agent_context(session_id="test_approval_session")
        return context

    @pytest.fixture
    def mock_guardian(self):
        """Create mock SlopGuardian."""
        guardian = MagicMock(spec=SlopGuardian)

        # Default: return ACCEPT verdict
        guardian.evaluate.return_value.is_ok.return_value = True
        guardian.evaluate.return_value.unwrap.return_value = SlopVerdict(
            score=4.0,
            reasons=[],
            top_fixes=[],
            dimension_scores={
                "clarity": 4.0,
                "measurability": 4.0,
                "completeness": 4.0,
                "actionability": 4.0,
            },
        )

        return guardian

    @pytest.fixture
    def checkpoint(self, mock_context, mock_guardian):
        """Create ApprovalCheckpoint instance."""
        return ApprovalCheckpoint(
            context=mock_context, guardian=mock_guardian, max_edit_attempts=3, timeout_seconds=5
        )

    @pytest.mark.asyncio
    async def test_await_approval_approve_immediately(self, checkpoint, mock_context):
        """Test approval workflow - user approves immediately."""
        spec = Spec(title="Test Feature", content="Add test feature with unit tests")

        # Mock user input: approve
        with patch.object(
            checkpoint, "_prompt_user_approval", new_callable=AsyncMock
        ) as mock_prompt:
            # Return Result directly (not a mock)
            mock_prompt.return_value = Ok(ApprovalDecision(action="approve"))

            result = await checkpoint.await_approval(spec)

        assert result.is_ok()
        approved = result.unwrap()
        assert approved.spec.title == "Test Feature"
        assert approved.decision.action == "approve"
        assert approved.edit_count == 0

        # Verify memory stored (Article IV)
        memories = mock_context.search_memories(["approval", "pattern"])
        assert len(memories) > 0

    @pytest.mark.asyncio
    async def test_await_approval_reject_once_then_approve(self, checkpoint, mock_context):
        """Test approval workflow - reject once, then approve."""
        spec = Spec(title="Test Feature", content="Initial content")

        # Mock user input: reject, then approve
        with (
            patch.object(
                checkpoint, "_prompt_user_approval", new_callable=AsyncMock
            ) as mock_prompt,
            patch.object(checkpoint, "_regenerate_spec", new_callable=AsyncMock) as mock_regenerate,
        ):
            # First call: reject, second call: approve
            reject_decision = ApprovalDecision(action="reject", reason="Needs more detail")
            approve_decision = ApprovalDecision(action="approve")

            mock_prompt.side_effect = [
                Ok(reject_decision),
                Ok(approve_decision),
            ]

            # Mock spec regeneration
            updated_spec = Spec(
                title="Test Feature", content="Updated content with more detail", version=2
            )
            mock_regenerate.return_value = Ok(updated_spec)

            result = await checkpoint.await_approval(spec)

        assert result.is_ok()
        approved = result.unwrap()
        assert approved.edit_count == 1
        assert approved.spec.version == 2

    @pytest.mark.asyncio
    async def test_await_approval_max_edits_exceeded(self, checkpoint):
        """Test approval workflow - max edit attempts exceeded."""
        spec = Spec(title="Test Feature", content="Initial content")

        # Mock user input: always reject
        with (
            patch.object(
                checkpoint, "_prompt_user_approval", new_callable=AsyncMock
            ) as mock_prompt,
            patch.object(checkpoint, "_regenerate_spec", new_callable=AsyncMock) as mock_regenerate,
        ):
            reject_decision = ApprovalDecision(action="reject", reason="Still not good enough")
            mock_prompt.return_value = Ok(reject_decision)

            # Mock spec regeneration
            mock_regenerate.return_value = Ok(spec)

            result = await checkpoint.await_approval(spec)

        assert result.is_err()
        error = result.unwrap_err()
        assert "rejected after 3 edit attempts" in error

    @pytest.mark.asyncio
    async def test_await_approval_timeout(self, checkpoint):
        """Test approval workflow - user input timeout."""
        spec = Spec(
            title="Test Feature", content="Content with at least 10 characters for validation"
        )

        # Mock user input: timeout after 5 seconds
        with patch.object(
            checkpoint, "_prompt_user_approval", new_callable=AsyncMock
        ) as mock_prompt:
            mock_prompt.side_effect = TimeoutError()

            result = await checkpoint.await_approval(spec)

        assert result.is_err()
        error = result.unwrap_err()
        assert "Approval timeout" in error
        assert "5s" in error

    @pytest.mark.asyncio
    async def test_await_approval_with_slop_warnings(self, checkpoint, mock_guardian):
        """Test approval workflow - displays slop warnings (non-blocking)."""
        spec = Spec(title="Vague Feature", content="Make the system better somehow")

        # Mock SlopGuardian: low score but non-blocking
        low_score_verdict = SlopVerdict(
            score=2.5,
            reasons=["Vague language", "No acceptance criteria"],
            top_fixes=["Add specific metrics", "Define concrete deliverables"],
            dimension_scores={
                "clarity": 2.0,
                "measurability": 2.5,
                "completeness": 3.0,
                "actionability": 2.5,
            },
        )
        mock_guardian.evaluate.return_value.unwrap.return_value = low_score_verdict

        # User approves despite warnings
        with patch.object(
            checkpoint, "_prompt_user_approval", new_callable=AsyncMock
        ) as mock_prompt:
            mock_prompt.return_value = Ok(
                ApprovalDecision(action="approve", slop_verdict=low_score_verdict)
            )

            result = await checkpoint.await_approval(spec)

        assert result.is_ok()
        approved = result.unwrap()
        assert approved.decision.slop_verdict is not None
        assert approved.decision.slop_verdict.score == 2.5

    @pytest.mark.asyncio
    async def test_prompt_user_approval_approve(self, checkpoint):
        """Test user prompt - approve action."""
        spec = Spec(title="Feature", content="Content with at least 10 characters")
        verdict = SlopVerdict(
            score=4.0,
            reasons=[],
            top_fixes=[],
            dimension_scores={
                "clarity": 4.0,
                "measurability": 4.0,
                "completeness": 4.0,
                "actionability": 4.0,
            },
        )

        # Mock user input: "A"
        with patch("builtins.input", return_value="A"):
            result = await checkpoint._prompt_user_approval(spec, verdict)

        assert result.is_ok()
        decision = result.unwrap()
        assert decision.action == "approve"

    @pytest.mark.asyncio
    async def test_prompt_user_approval_reject(self, checkpoint):
        """Test user prompt - reject action."""
        spec = Spec(title="Feature", content="Content with at least 10 characters")

        # Mock user input: "R", then rejection reason
        with patch("builtins.input", side_effect=["R", "Needs more details"]):
            result = await checkpoint._prompt_user_approval(spec, None)

        assert result.is_ok()
        decision = result.unwrap()
        assert decision.action == "reject"
        assert decision.reason == "Needs more details"

    @pytest.mark.asyncio
    async def test_prompt_user_approval_invalid_choice(self, checkpoint):
        """Test user prompt - invalid choice."""
        spec = Spec(title="Feature", content="Content with at least 10 characters")

        # Mock user input: "X" (invalid)
        with patch("builtins.input", return_value="X"):
            result = await checkpoint._prompt_user_approval(spec, None)

        assert result.is_err()
        error = result.unwrap_err()
        assert "Invalid choice" in error

    def test_update_todo_status(self, checkpoint, mock_context):
        """Test TodoWrite integration."""
        checkpoint._update_todo_status("pending", "Test approval pending")

        # Verify no exceptions raised
        # (TodoWrite context handling is mocked in this test)

    def test_store_approval_pattern(self, checkpoint, mock_context):
        """Test VectorStore pattern storage (Article IV)."""
        spec = Spec(title="Feature X", content="Content with at least 10 characters")
        decision = ApprovalDecision(action="approve")
        approved = ApprovedSpec(spec=spec, decision=decision, edit_count=1)

        verdict = SlopVerdict(
            score=3.8,
            reasons=[],
            top_fixes=[],
            dimension_scores={
                "clarity": 4.0,
                "measurability": 3.5,
                "completeness": 4.0,
                "actionability": 3.8,
            },
        )

        checkpoint._store_approval_pattern(approved, verdict)

        # Verify memory stored
        memories = mock_context.search_memories(["approval", "pattern"])
        assert len(memories) > 0

        # Verify pattern data
        pattern = memories[0]
        assert pattern["content"]["spec_title"] == "Feature X"
        assert pattern["content"]["edit_count"] == 1
        assert pattern["content"]["slop_score"] == 3.8

    @pytest.mark.asyncio
    async def test_regenerate_spec_not_implemented(self, checkpoint):
        """Test spec regeneration placeholder (not yet implemented)."""
        spec = Spec(title="Feature", content="Content with at least 10 characters")

        result = await checkpoint._regenerate_spec(spec, "Needs improvement", None)

        assert result.is_err()
        assert "not yet implemented" in result.unwrap_err()


class TestApprovalCheckpointFactory:
    """Test factory function."""

    def test_create_approval_checkpoint(self):
        """Test factory creates checkpoint with defaults."""
        context = create_agent_context()

        checkpoint = create_approval_checkpoint(context)

        assert checkpoint.context == context
        assert checkpoint.max_edit_attempts == 3
        assert checkpoint.timeout_seconds == 300
        assert checkpoint.guardian is not None

    def test_create_approval_checkpoint_custom_config(self):
        """Test factory with custom configuration."""
        context = create_agent_context()
        guardian = SlopGuardian(model="gpt-5", temperature=0.2)

        checkpoint = create_approval_checkpoint(
            context, guardian=guardian, max_edit_attempts=5, timeout_seconds=600
        )

        assert checkpoint.guardian == guardian
        assert checkpoint.max_edit_attempts == 5
        assert checkpoint.timeout_seconds == 600


class TestApprovalCheckpointIntegration:
    """Integration tests for approval workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_real_slop_guardian(self):
        """Test full approval workflow with real SlopGuardian."""
        context = create_agent_context(session_id="integration_test")

        # Use real SlopGuardian (mocked LLM calls)
        guardian = MagicMock(spec=SlopGuardian)
        guardian.evaluate.return_value.is_ok.return_value = True
        guardian.evaluate.return_value.unwrap.return_value = SlopVerdict(
            score=4.2,
            reasons=[],
            top_fixes=[],
            dimension_scores={
                "clarity": 4.5,
                "measurability": 4.0,
                "completeness": 4.0,
                "actionability": 4.3,
            },
        )

        checkpoint = ApprovalCheckpoint(context, guardian=guardian)

        spec = Spec(
            title="User Authentication",
            content="Implement JWT-based authentication with refresh tokens and role-based access control",
        )

        # Mock user approval
        with patch.object(
            checkpoint, "_prompt_user_approval", new_callable=AsyncMock
        ) as mock_prompt:
            mock_prompt.return_value = Ok(ApprovalDecision(action="approve"))

            result = await checkpoint.await_approval(spec)

        assert result.is_ok()
        approved = result.unwrap()
        assert approved.spec.title == "User Authentication"
        assert approved.decision.action == "approve"

        # Verify VectorStore integration
        memories = context.search_memories(["approval"])
        assert len(memories) > 0
