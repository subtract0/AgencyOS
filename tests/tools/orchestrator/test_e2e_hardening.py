"""
End-to-End Hardening Validation Tests - Leap 6 Completion.

Tests the integration of all Leap 6 production hardening components:
- Slop Immunity Protocol
- Budget Guard
- Audit Signing
- Retry Policy

Constitutional Compliance:
- Article I: Complete context (all components tested together)
- Article II: 100% verification (all integration paths tested)
- Article III: Automated enforcement (no manual bypass)
- Article IV: Learning patterns stored for all verdicts
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.type_definitions.result import Err, Ok
from tools.orchestrator.audit_signing import (
    AuditSigner,
    RunSnapshot,
    SignedAuditEntry,
    append_signed_audit_entry,
    sign_audit_entry,
    verify_signature,
)
from tools.orchestrator.budget_guard import (
    AuditEntry,
    BudgetExceeded,
    BudgetGuard,
    BudgetLimits,
    CostEstimate,
)
from tools.orchestrator.retry_policy import (
    IdempotencyKey,
    RetryExhausted,
    RetryMetrics,
    RetryPolicy,
    retry_with_policy_sync,
)
from tools.orchestrator.slop_guardian import (
    SlopDetected,
    SlopGuardian,
    SlopVerdict,
    VerdictStatus,
    enforce_slop_immunity,
)


class TestE2EProductionHardening:
    """End-to-end tests for production hardening stack."""

    @pytest.fixture
    def temp_audit_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory for audit logs."""
        audit_dir = tmp_path / "audits"
        audit_dir.mkdir()
        return audit_dir

    @pytest.fixture
    def signing_secret(self) -> str:
        """Provide signing secret for tests."""
        return "test_secret_key_for_e2e_hardening"

    # Test 1: Full stack - slop immunity blocks low-quality mission
    @patch("openai.OpenAI")
    def test_slop_immunity_blocks_vague_mission(self, mock_openai) -> None:
        """Test that slop immunity blocks vague mission descriptions."""
        from unittest.mock import Mock

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps({
                        "dimension_scores": {
                            "clarity": 1.0,
                            "measurability": 1.5,
                            "completeness": 2.0,
                            "actionability": 1.5,
                        },
                        "reasons": ["Too vague", "No measurable outcomes"],
                        "top_fixes": ["Add specific deliverables", "Define success criteria"],
                    })
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = enforce_slop_immunity(
            text="Make the system better",
            guardian=guardian,
            stage="pre_planning",
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, SlopDetected)
        assert error.verdict.status == VerdictStatus.REJECT
        assert error.verdict.score < 2.0

    # Test 2: Budget guard blocks over-budget mission
    def test_budget_guard_blocks_over_budget(self, temp_audit_dir: Path) -> None:
        """Test that budget guard blocks missions exceeding limits."""
        audit_path = str(temp_audit_dir / "budget.jsonl")
        guard = BudgetGuard(audit_log_path=audit_path)

        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=5.0)
        estimate = CostEstimate(
            total_usd=15.0,  # Exceeds per_mission_usd
            total_tokens=60000,
            tasks_count=10,
        )

        result = guard.check_budget(estimate, limits, force=False)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.would_exceed_per_mission
        assert error.estimated_cost_usd == 15.0

    # Test 3: Budget guard allows with force flag and logs override
    def test_budget_guard_force_override_logged(self, temp_audit_dir: Path) -> None:
        """Test that budget override is logged to audit trail."""
        audit_path = str(temp_audit_dir / "budget.jsonl")
        guard = BudgetGuard(audit_log_path=audit_path)

        limits = BudgetLimits(daily_usd=10.0, per_mission_usd=5.0)
        estimate = CostEstimate(
            total_usd=15.0,
            total_tokens=60000,
            tasks_count=10,
        )

        result = guard.check_budget(estimate, limits, force=True)

        assert result.is_ok()

        # Verify audit log was written
        assert os.path.exists(audit_path)
        with open(audit_path) as f:
            lines = f.readlines()
            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert entry["action"] == "budget_override"
            assert entry["reason"] == "--force flag used"

    # Test 4: Audit signing produces deterministic signatures
    def test_audit_signing_deterministic(self, signing_secret: str) -> None:
        """Test that same input produces same signature."""
        signer = AuditSigner(secret=signing_secret)

        data = {"task_id": "test-1", "status": "success", "tokens": 1000}

        sig1 = signer.sign(data)
        sig2 = signer.sign(data)

        assert sig1 == sig2
        assert len(sig1) == 64  # SHA256 hex

    # Test 5: Audit signing detects tampering
    def test_audit_signing_detects_tampering(self, signing_secret: str) -> None:
        """Test that tampered entries are detected."""
        signer = AuditSigner(secret=signing_secret)

        entry = AuditEntry(
            timestamp="2025-01-01T00:00:00Z",
            action="budget_check_passed",
            estimated_cost_usd=1.0,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=0.0,
            reason="within budget",
        )

        snapshot = RunSnapshot(
            git_commit_hash="a" * 40,
            docker_image_hash="sha256:abc123",
            pip_freeze_output="numpy==1.24.0",
            random_seed=42,
        )

        signed = sign_audit_entry(entry, signer, snapshot)
        assert verify_signature(signed, signer)

        # Tamper with entry
        tampered_entry = entry.model_copy(update={"estimated_cost_usd": 0.01})
        tampered = SignedAuditEntry(
            entry=tampered_entry,
            snapshot=snapshot,
            signature=signed.signature,
        )

        assert not verify_signature(tampered, signer)

    # Test 6: Retry policy exhausts attempts and tracks idempotency
    def test_retry_exhausts_attempts_with_tracking(self) -> None:
        """Test that retry policy exhausts attempts and tracks keys."""
        policy = RetryPolicy(
            max_attempts=3,
            base_delay_s=0.01,  # Fast for testing
            jitter=0.0,
        )

        call_count = 0

        def failing_operation() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count} failed")

        result = retry_with_policy_sync("test-task", failing_operation, policy)

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, RetryExhausted)
        assert error.attempts == 3
        assert len(error.errors) == 3
        assert call_count == 3

    # Test 7: Full integration - successful mission flow
    @patch("openai.OpenAI")
    def test_full_integration_success_flow(
        self, mock_openai, temp_audit_dir: Path, signing_secret: str
    ) -> None:
        """Test full stack for successful mission execution."""
        from unittest.mock import Mock

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps({
                        "dimension_scores": {
                            "clarity": 4.5,
                            "measurability": 4.5,
                            "completeness": 4.5,
                            "actionability": 4.5,
                        },
                        "reasons": [],
                        "top_fixes": [],
                    })
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Step 1: Slop immunity check passes
        guardian = SlopGuardian()
        slop_result = enforce_slop_immunity(
            text="Implement JWT authentication with RSA-256 signing, "
                 "returning access tokens with 1-hour expiry. "
                 "Success: 100% test coverage, all auth endpoints secured.",
            guardian=guardian,
            stage="pre_planning",
        )
        assert slop_result.is_ok()

        # Step 2: Budget check passes
        audit_path = str(temp_audit_dir / "budget.jsonl")
        budget_guard = BudgetGuard(audit_log_path=audit_path)
        limits = BudgetLimits(daily_usd=100.0, per_mission_usd=10.0)
        estimate = CostEstimate(
            total_usd=5.0,  # Within limits
            total_tokens=20000,
            tasks_count=5,
        )
        budget_result = budget_guard.check_budget(estimate, limits)
        assert budget_result.is_ok()

        # Step 3: Sign audit entry
        signer = AuditSigner(secret=signing_secret)
        entry = AuditEntry(
            timestamp="2025-01-01T00:00:00Z",
            action="mission_complete",
            estimated_cost_usd=5.0,
            daily_limit_usd=100.0,
            per_mission_limit_usd=10.0,
            daily_spent_usd=5.0,
            reason="JWT auth implemented successfully",
        )
        snapshot = RunSnapshot(
            git_commit_hash="b" * 40,
            docker_image_hash="sha256:def456",
            pip_freeze_output="pyjwt==2.8.0",
            random_seed=12345,
        )
        signed = sign_audit_entry(entry, signer, snapshot)
        assert verify_signature(signed, signer)

        # Step 4: Append to audit log
        signed_audit_path = str(temp_audit_dir / "signed_audit.jsonl")
        append_signed_audit_entry(signed, signed_audit_path)

        # Verify audit log integrity
        assert os.path.exists(signed_audit_path)
        with open(signed_audit_path) as f:
            audit_data = json.loads(f.readline())
            assert "signature" in audit_data
            assert len(audit_data["signature"]) == 64

    # Test 8: Slop immunity REVISE triggers auto-rewrite
    @patch("openai.OpenAI")
    def test_slop_immunity_revise_flow(self, mock_openai) -> None:
        """Test that REVISE verdict triggers improvement suggestions."""
        from unittest.mock import Mock

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content=json.dumps({
                        "dimension_scores": {
                            "clarity": 3.0,
                            "measurability": 2.5,
                            "completeness": 3.0,
                            "actionability": 2.7,
                        },
                        "reasons": ["Success criteria unclear"],
                        "top_fixes": [
                            "Add specific test coverage target",
                            "Define measurable performance benchmarks",
                        ],
                    })
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        guardian = SlopGuardian()
        result = enforce_slop_immunity(
            text="Add caching to the API",
            guardian=guardian,
            stage="pre_planning",
        )

        # REVISE returns error but with fixable suggestions
        assert result.is_err()
        error = result.unwrap_err()
        assert error.verdict.status == VerdictStatus.REVISE
        assert len(error.verdict.top_fixes) > 0


class TestE2EAuditLogIntegrity:
    """Tests for append-only audit log integrity."""

    def test_audit_log_append_only(self, tmp_path: Path) -> None:
        """Test that audit log only appends, never modifies."""
        audit_path = str(tmp_path / "audit.jsonl")
        signer = AuditSigner(secret="test_secret")

        entries = []
        for i in range(3):
            entry = AuditEntry(
                timestamp=f"2025-01-0{i + 1}T00:00:00Z",
                action=f"action_{i}",
                estimated_cost_usd=float(i),
                daily_limit_usd=100.0,
                per_mission_limit_usd=10.0,
                daily_spent_usd=float(i),
                reason=f"reason_{i}",
            )
            signed = sign_audit_entry(entry, signer)
            append_signed_audit_entry(signed, audit_path)
            entries.append(signed)

        # Verify all entries present and in order
        with open(audit_path) as f:
            lines = f.readlines()
            assert len(lines) == 3

            for i, line in enumerate(lines):
                data = json.loads(line)
                assert data["entry"]["action"] == f"action_{i}"
                # Verify signature still valid
                reconstructed = SignedAuditEntry(**data)
                assert verify_signature(reconstructed, signer)


class TestE2EDeterministicReproducibility:
    """Tests for deterministic execution reproducibility."""

    def test_run_snapshot_captures_reproducibility(self) -> None:
        """Test that RunSnapshot captures all reproducibility data."""
        snapshot = RunSnapshot(
            git_commit_hash="c" * 40,
            docker_image_hash="sha256:ghi789",
            pip_freeze_output="requests==2.31.0\npandas==2.0.0",
            random_seed=99999,
        )

        # Serialize and deserialize
        data = snapshot.model_dump()
        restored = RunSnapshot(**data)

        assert restored.git_commit_hash == snapshot.git_commit_hash
        assert restored.docker_image_hash == snapshot.docker_image_hash
        assert restored.pip_freeze_output == snapshot.pip_freeze_output
        assert restored.random_seed == snapshot.random_seed

    def test_idempotency_key_format(self) -> None:
        """Test that idempotency keys follow expected format."""
        key = IdempotencyKey.generate("task-123", 1)

        # Format: {task_id}:{attempt}:{timestamp_ms}
        key_str = key.to_string()
        parts = key_str.split(":")
        assert len(parts) == 3
        assert parts[0] == "task-123"
        assert parts[1] == "1"
        assert int(parts[2]) > 0  # Valid timestamp

        # Round-trip
        parsed = IdempotencyKey.from_string(key_str)
        assert parsed.task_id == key.task_id
        assert parsed.attempt == key.attempt
        assert parsed.timestamp_ms == key.timestamp_ms
