"""
Approval Checkpoint - User approval gate for specifications.

Implements Article V (Spec-Driven Development) approval workflow with:
1. Interactive user prompt (approve/reject/edit)
2. Edit loop with max 3 attempts
3. 5-minute timeout with graceful degradation
4. SlopGuardian integration (non-blocking warnings)
5. TodoWrite status tracking
6. VectorStore learning (Article IV)

Constitutional compliance:
- Article I: Complete context before execution (approval + slop verdict)
- Article II: 100% verification (Pydantic validation)
- Article III: Automated enforcement (slop warnings audited)
- Article IV: VectorStore integration (approval patterns stored)
- Article V: Spec-driven (user approval gate)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result
from tools.orchestrator.slop_guardian import SlopGuardian, SlopVerdict, log_slop_evaluation
from tools.todo_write import TodoItem, TodoWrite

logger = logging.getLogger(__name__)


class Spec(BaseModel):
    """
    Specification model for approval workflow.

    Fields:
        title: Specification title
        content: Full specification content (markdown)
        created_at: ISO 8601 timestamp of creation
        version: Spec version for edit tracking
    """

    title: str = Field(..., min_length=1, description="Specification title")
    content: str = Field(..., min_length=10, description="Full specification content (markdown)")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 timestamp of creation",
    )
    version: int = Field(default=1, ge=1, description="Spec version for edit tracking")

    def to_markdown(self) -> str:
        """Convert spec to markdown format for display/evaluation."""
        return f"# {self.title}\n\n{self.content}"


class ApprovalDecision(BaseModel):
    """
    User approval decision with metadata.

    Fields:
        action: User action (approve/reject/edit)
        reason: Optional reason for rejection
        slop_verdict: Optional slop guardian verdict
        timestamp: ISO 8601 timestamp of decision
    """

    action: Literal["approve", "reject", "edit"] = Field(..., description="User decision")
    reason: str | None = Field(None, description="Optional reason for rejection")
    slop_verdict: SlopVerdict | None = Field(None, description="Slop guardian verdict")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 timestamp of decision",
    )


class ApprovedSpec(BaseModel):
    """
    Approved specification with metadata.

    Fields:
        spec: Approved specification
        decision: Approval decision metadata
        edit_count: Number of edit iterations (0-3)
    """

    spec: Spec = Field(..., description="Approved specification")
    decision: ApprovalDecision = Field(..., description="Approval decision metadata")
    edit_count: int = Field(default=0, ge=0, le=3, description="Number of edit iterations")


class ApprovalCheckpoint:
    """
    Interactive approval checkpoint for specifications.

    Implements user approval workflow with:
    - Interactive prompt (approve/reject/edit)
    - Edit loop with Planner agent (max 3 attempts)
    - 5-minute timeout with graceful error
    - SlopGuardian integration (non-blocking warnings)
    - TodoWrite status tracking
    - VectorStore learning (Article IV)

    Example:
        >>> context = create_agent_context()
        >>> checkpoint = ApprovalCheckpoint(context)
        >>> spec = Spec(title="Feature X", content="Add authentication...")
        >>> result = await checkpoint.await_approval(spec)
        >>> if result.is_ok():
        ...     approved = result.unwrap()
        ...     print(f"Approved: {approved.spec.title}")
    """

    def __init__(
        self,
        context: AgentContext,
        guardian: SlopGuardian | None = None,
        max_edit_attempts: int = 3,
        timeout_seconds: int = 300,
    ):
        """
        Initialize approval checkpoint.

        Args:
            context: AgentContext for memory/learning integration
            guardian: Optional SlopGuardian instance (creates default if None)
            max_edit_attempts: Maximum edit loop iterations (default: 3)
            timeout_seconds: User input timeout in seconds (default: 300 = 5 min)
        """
        self.context = context
        self.guardian = guardian or SlopGuardian(model="gpt-5", temperature=0.3)
        self.max_edit_attempts = max_edit_attempts
        self.timeout_seconds = timeout_seconds

    async def await_approval(self, spec: Spec) -> Result[ApprovedSpec, str]:
        """
        Await user approval with interactive prompt and edit loop.

        Workflow:
        1. Evaluate spec with SlopGuardian (non-blocking)
        2. Display approval prompt with slop warnings
        3. If reject: call Planner agent to re-generate (max 3 attempts)
        4. If approve: return ApprovedSpec with metadata
        5. Track status with TodoWrite (pending → approved/rejected)
        6. Store approval pattern to VectorStore (Article IV)

        Args:
            spec: Specification to approve

        Returns:
            Result with ApprovedSpec or error message

        Constitutional Compliance:
            - Article I: Complete context (spec + slop verdict)
            - Article IV: VectorStore learning (approval patterns)
            - Article V: Spec-driven (user approval gate)
        """
        # Update TodoWrite: approval checkpoint pending
        self._update_todo_status("pending", f"Awaiting approval: {spec.title}")

        edit_count = 0
        current_spec = spec

        while edit_count <= self.max_edit_attempts:
            # Step 1: Evaluate with SlopGuardian (non-blocking)
            slop_result = self.guardian.evaluate(current_spec.to_markdown())

            slop_verdict = None
            if slop_result.is_ok():
                slop_verdict = slop_result.unwrap()

                # Log slop evaluation (Article III: audit trail)
                log_slop_evaluation(
                    slop_verdict,
                    current_spec.to_markdown(),
                    stage="spec_approval",
                    attempt=edit_count,
                    task_id=current_spec.title,
                )
            else:
                logger.warning(f"Slop evaluation failed: {slop_result.unwrap_err()}")

            # Step 2: Display approval prompt with slop warnings
            try:
                decision_result = await asyncio.wait_for(
                    self._prompt_user_approval(current_spec, slop_verdict),
                    timeout=self.timeout_seconds,
                )

                if decision_result.is_err():
                    return decision_result

                decision = decision_result.unwrap()

            except TimeoutError:
                # Graceful timeout handling
                self._update_todo_status("rejected", f"Timeout: {spec.title}")
                return Err(f"Approval timeout after {self.timeout_seconds}s (no user response)")

            # Step 3: Handle user decision
            if decision.action == "approve":
                # Success path: return approved spec
                approved = ApprovedSpec(spec=current_spec, decision=decision, edit_count=edit_count)

                # Update TodoWrite: approved
                self._update_todo_status("completed", f"Approved: {current_spec.title}")

                # Store approval pattern to VectorStore (Article IV)
                self._store_approval_pattern(approved, slop_verdict)

                return Ok(approved)

            elif decision.action == "reject":
                # Edit loop: call Planner agent to re-generate
                if edit_count >= self.max_edit_attempts:
                    # Exhausted attempts
                    self._update_todo_status("rejected", f"Max edits reached: {current_spec.title}")
                    return Err(
                        f"Approval rejected after {self.max_edit_attempts} edit attempts. "
                        f"Reason: {decision.reason or 'No reason provided'}"
                    )

                # Re-generate spec with Planner agent
                rewrite_result = await self._regenerate_spec(
                    current_spec, decision.reason, slop_verdict
                )

                if rewrite_result.is_err():
                    return rewrite_result

                current_spec = rewrite_result.unwrap()
                edit_count += 1

                # Update TodoWrite: edit iteration
                self._update_todo_status(
                    "in_progress",
                    f"Edit {edit_count}/{self.max_edit_attempts}: {current_spec.title}",
                )

            elif decision.action == "edit":
                # Allow manual edit (placeholder - requires external editor integration)
                return Err(
                    "Manual edit not yet implemented. Use 'reject' to trigger re-generation."
                )

        # Should never reach here (fallthrough after max attempts)
        return Err(f"Approval failed after {self.max_edit_attempts} attempts")

    async def _prompt_user_approval(
        self, spec: Spec, slop_verdict: SlopVerdict | None
    ) -> Result[ApprovalDecision, str]:
        """
        Display interactive approval prompt with slop warnings.

        Args:
            spec: Specification to display
            slop_verdict: Optional slop guardian verdict

        Returns:
            Result with ApprovalDecision or error message
        """
        # Build prompt with spec content
        prompt_lines = [
            "=" * 80,
            f"📋 SPECIFICATION APPROVAL REQUIRED: {spec.title}",
            "=" * 80,
            "",
            spec.to_markdown(),
            "",
        ]

        # Add slop warnings (non-blocking, informational only)
        if slop_verdict:
            prompt_lines.extend(
                [
                    "⚠️  SLOP GUARDIAN ANALYSIS:",
                    f"   Score: {slop_verdict.score}/5.0 ({slop_verdict.status.upper()})",
                    "",
                ]
            )

            if slop_verdict.reasons:
                prompt_lines.append("   Quality Issues:")
                for reason in slop_verdict.reasons:
                    prompt_lines.append(f"     • {reason}")
                prompt_lines.append("")

            if slop_verdict.top_fixes:
                prompt_lines.append("   Suggested Improvements:")
                for fix in slop_verdict.top_fixes:
                    prompt_lines.append(f"     • {fix}")
                prompt_lines.append("")

            prompt_lines.append(
                "   Note: Warnings are informational only. You can approve despite low score."
            )
            prompt_lines.append("")

        # Add action prompt
        prompt_lines.extend(
            [
                "=" * 80,
                "ACTION REQUIRED:",
                "  [A]pprove - Proceed with this specification",
                "  [R]eject  - Request re-generation with improvements",
                "  [E]dit    - Manual edit (not yet implemented)",
                "",
                "Enter your choice (A/R/E):",
            ]
        )

        print("\n".join(prompt_lines))

        # Get user input (async-safe)
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input, "> ")

        # Parse decision
        choice = user_input.strip().upper()

        if choice in ("A", "APPROVE"):
            return Ok(ApprovalDecision(action="approve", slop_verdict=slop_verdict))

        elif choice in ("R", "REJECT"):
            # Request rejection reason
            print("\nReason for rejection (optional):")
            reason = await loop.run_in_executor(None, input, "> ")
            return Ok(
                ApprovalDecision(
                    action="reject", reason=reason.strip() or None, slop_verdict=slop_verdict
                )
            )

        elif choice in ("E", "EDIT"):
            return Ok(ApprovalDecision(action="edit", slop_verdict=slop_verdict))

        else:
            return Err(f"Invalid choice: {choice}. Expected A/R/E.")

    async def _regenerate_spec(
        self, original_spec: Spec, rejection_reason: str | None, slop_verdict: SlopVerdict | None
    ) -> Result[Spec, str]:
        """
        Regenerate specification using Planner agent.

        Args:
            original_spec: Original specification
            rejection_reason: User's rejection reason
            slop_verdict: Slop guardian verdict (for fix suggestions)

        Returns:
            Result with regenerated Spec or error message

        Note: This is a placeholder. Full implementation requires:
        - Planner agent invocation
        - Spec re-generation with feedback
        - Constitutional validation
        """
        # TODO: Implement Planner agent invocation
        # For now, return error to indicate unimplemented feature
        return Err(
            "Spec re-generation not yet implemented. "
            "This requires Planner agent integration for spec rewriting."
        )

    def _update_todo_status(self, status: str, task_description: str) -> None:
        """
        Update TodoWrite with checkpoint status.

        Args:
            status: Todo status (pending/in_progress/completed/rejected)
            task_description: Task description for display
        """
        try:
            # Map status to TodoWrite format
            todo_status_map = {
                "pending": "pending",
                "in_progress": "in_progress",
                "completed": "completed",
                "rejected": "completed",  # Mark as completed to remove from active list
            }

            todo_status = todo_status_map.get(status, "pending")

            # Create TodoWrite tool instance
            todo_tool = TodoWrite(
                todos=[
                    TodoItem(
                        task=task_description,
                        status=todo_status,  # type: ignore
                        priority="high",
                    )
                ]
            )

            # Set context and run
            todo_tool.context = self.context  # type: ignore
            result = todo_tool.run()

            logger.debug(f"TodoWrite updated: {result}")

        except Exception as e:
            logger.warning(f"TodoWrite update failed: {e}")

    def _store_approval_pattern(
        self, approved: ApprovedSpec, slop_verdict: SlopVerdict | None
    ) -> None:
        """
        Store approval pattern to VectorStore (Article IV).

        Args:
            approved: Approved specification with metadata
            slop_verdict: Slop guardian verdict
        """
        try:
            pattern_data = {
                "spec_title": approved.spec.title,
                "spec_version": approved.spec.version,
                "edit_count": approved.edit_count,
                "slop_score": slop_verdict.score if slop_verdict else None,
                "slop_status": slop_verdict.status if slop_verdict else None,
                "approved_despite_warnings": (
                    slop_verdict.status != "accept" if slop_verdict else False
                ),
                "decision_timestamp": approved.decision.timestamp,
                "confidence": 0.8,  # Base confidence for approval patterns
            }

            self.context.store_memory(
                f"approval_pattern_{approved.spec.title}_{datetime.now(UTC).timestamp()}",
                pattern_data,
                tags=["approval", "checkpoint", "spec", "pattern"],
            )

            logger.info(
                f"Approval pattern stored: {approved.spec.title} "
                f"(edits: {approved.edit_count}, slop: {pattern_data['slop_score']})"
            )

        except Exception as e:
            logger.warning(f"Failed to store approval pattern: {e}")


# Convenience factory function
def create_approval_checkpoint(
    context: AgentContext,
    guardian: SlopGuardian | None = None,
    max_edit_attempts: int = 3,
    timeout_seconds: int = 300,
) -> ApprovalCheckpoint:
    """
    Factory function to create ApprovalCheckpoint instance.

    Args:
        context: AgentContext for memory/learning integration
        guardian: Optional SlopGuardian instance
        max_edit_attempts: Maximum edit loop iterations (default: 3)
        timeout_seconds: User input timeout in seconds (default: 300)

    Returns:
        Configured ApprovalCheckpoint instance
    """
    return ApprovalCheckpoint(
        context=context,
        guardian=guardian,
        max_edit_attempts=max_edit_attempts,
        timeout_seconds=timeout_seconds,
    )
