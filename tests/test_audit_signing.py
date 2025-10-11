"""
Tests for audit signing and reproducibility snapshots.

Constitutional Compliance:
- Article I: Complete context (all reproducibility data captured)
- Article II: 100% verification (signature tamper detection)
- ADR-008: Strict typing (Pydantic models)
- ADR-010: Result pattern for error handling
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import pytest

from tools.orchestrator.audit_signing import (
    AuditSigner,
    RunSnapshot,
    SignedAuditEntry,
    sign_audit_entry,
    verify_signature,
)


class TestRunSnapshot:
    """Test RunSnapshot model for reproducibility data."""

    def test_run_snapshot_captures_all_fields(self):
        """Test RunSnapshot captures git hash, docker hash, pip freeze, seed."""
        git_hash = "a" * 40  # Valid 40-char SHA1
        snapshot = RunSnapshot(
            git_commit_hash=git_hash,
            docker_image_hash="sha256:fedcba987654",
            pip_freeze_output="numpy==1.24.0\npandas==2.0.0",
            random_seed=42,
        )

        assert snapshot.git_commit_hash == git_hash
        assert snapshot.docker_image_hash == "sha256:fedcba987654"
        assert snapshot.pip_freeze_output == "numpy==1.24.0\npandas==2.0.0"
        assert snapshot.random_seed == 42

    def test_run_snapshot_validates_git_hash_length(self):
        """Test RunSnapshot validates git commit hash length (40 chars SHA1)."""
        # Valid 40-char hash
        snapshot = RunSnapshot(
            git_commit_hash="a" * 40,
            docker_image_hash="sha256:test",
            pip_freeze_output="",
            random_seed=0,
        )
        assert len(snapshot.git_commit_hash) == 40

        # Invalid short hash
        with pytest.raises(ValueError, match="Git commit hash must be 40 characters"):
            RunSnapshot(
                git_commit_hash="short",
                docker_image_hash="sha256:test",
                pip_freeze_output="",
                random_seed=0,
            )

    def test_run_snapshot_validates_docker_hash_format(self):
        """Test RunSnapshot validates docker hash starts with sha256:."""
        # Valid format
        snapshot = RunSnapshot(
            git_commit_hash="a" * 40,
            docker_image_hash="sha256:abc123",
            pip_freeze_output="",
            random_seed=0,
        )
        assert snapshot.docker_image_hash.startswith("sha256:")

        # Invalid format
        with pytest.raises(ValueError, match="Docker image hash must start with 'sha256:'"):
            RunSnapshot(
                git_commit_hash="a" * 40,
                docker_image_hash="invalid:abc123",
                pip_freeze_output="",
                random_seed=0,
            )

    def test_run_snapshot_allows_empty_pip_freeze(self):
        """Test RunSnapshot allows empty pip freeze output."""
        snapshot = RunSnapshot(
            git_commit_hash="a" * 40,
            docker_image_hash="sha256:test",
            pip_freeze_output="",
            random_seed=0,
        )
        assert snapshot.pip_freeze_output == ""

    def test_run_snapshot_validates_seed_non_negative(self):
        """Test RunSnapshot validates random seed is non-negative."""
        # Valid seed
        snapshot = RunSnapshot(
            git_commit_hash="a" * 40,
            docker_image_hash="sha256:test",
            pip_freeze_output="",
            random_seed=0,
        )
        assert snapshot.random_seed == 0

        # Invalid negative seed
        with pytest.raises(ValueError, match="Random seed must be non-negative"):
            RunSnapshot(
                git_commit_hash="a" * 40,
                docker_image_hash="sha256:test",
                pip_freeze_output="",
                random_seed=-1,
            )


class TestAuditSigner:
    """Test AuditSigner for deterministic SHA256 signing."""

    def test_signer_initializes_with_secret(self):
        """Test AuditSigner initializes with secret key."""
        signer = AuditSigner(secret="test_secret")
        assert signer.secret == "test_secret"

    def test_signer_loads_secret_from_env(self):
        """Test AuditSigner loads secret from AUDIT_SIGNING_SECRET env var."""
        os.environ["AUDIT_SIGNING_SECRET"] = "env_secret"
        try:
            signer = AuditSigner()
            assert signer.secret == "env_secret"
        finally:
            del os.environ["AUDIT_SIGNING_SECRET"]

    def test_signer_raises_on_missing_secret(self):
        """Test AuditSigner raises error when secret is missing."""
        # Ensure env var not set
        if "AUDIT_SIGNING_SECRET" in os.environ:
            del os.environ["AUDIT_SIGNING_SECRET"]

        with pytest.raises(ValueError, match="Audit signing secret not configured"):
            AuditSigner()

    def test_sign_creates_deterministic_sha256(self):
        """Test sign() creates deterministic SHA256 signature (same input = same sig)."""
        signer = AuditSigner(secret="test_secret")
        data = {"key": "value", "number": 123}

        # Sign twice - should be identical
        sig1 = signer.sign(data)
        sig2 = signer.sign(data)

        assert sig1 == sig2
        assert len(sig1) == 64  # SHA256 hex digest is 64 chars

    def test_sign_different_data_produces_different_signature(self):
        """Test different data produces different signatures."""
        signer = AuditSigner(secret="test_secret")

        sig1 = signer.sign({"key": "value1"})
        sig2 = signer.sign({"key": "value2"})

        assert sig1 != sig2

    def test_sign_different_secret_produces_different_signature(self):
        """Test different secrets produce different signatures for same data."""
        data = {"key": "value"}

        signer1 = AuditSigner(secret="secret1")
        signer2 = AuditSigner(secret="secret2")

        sig1 = signer1.sign(data)
        sig2 = signer2.sign(data)

        assert sig1 != sig2

    def test_verify_returns_true_for_valid_signature(self):
        """Test verify() returns True for valid signature."""
        signer = AuditSigner(secret="test_secret")
        data = {"key": "value"}

        signature = signer.sign(data)
        result = signer.verify(data, signature)

        assert result is True

    def test_verify_returns_false_for_tampered_data(self):
        """Test verify() returns False when data is tampered."""
        signer = AuditSigner(secret="test_secret")
        data = {"key": "value"}

        signature = signer.sign(data)

        # Tamper with data
        tampered_data = {"key": "tampered"}
        result = signer.verify(tampered_data, signature)

        assert result is False

    def test_verify_returns_false_for_invalid_signature(self):
        """Test verify() returns False for invalid signature."""
        signer = AuditSigner(secret="test_secret")
        data = {"key": "value"}

        result = signer.verify(data, "invalid_signature_12345")

        assert result is False


class TestSignAuditEntry:
    """Test sign_audit_entry() function."""

    def test_sign_audit_entry_adds_signature_field(self):
        """Test sign_audit_entry() adds signature field to entry."""
        from tools.orchestrator.budget_guard import AuditEntry

        entry = AuditEntry(
            timestamp="2025-10-11T12:00:00Z",
            action="test_action",
            estimated_cost_usd=1.5,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=2.0,
            reason="test reason",
            user="test_user",
        )

        signer = AuditSigner(secret="test_secret")
        signed_entry = sign_audit_entry(entry, signer)

        assert isinstance(signed_entry, SignedAuditEntry)
        assert signed_entry.entry == entry
        assert signed_entry.signature is not None
        assert len(signed_entry.signature) == 64  # SHA256 hex

    def test_sign_audit_entry_with_snapshot(self):
        """Test sign_audit_entry() with RunSnapshot."""
        from tools.orchestrator.budget_guard import AuditEntry

        entry = AuditEntry(
            timestamp="2025-10-11T12:00:00Z",
            action="test_action",
            estimated_cost_usd=1.5,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=2.0,
            reason="test reason",
        )

        snapshot = RunSnapshot(
            git_commit_hash="a" * 40,
            docker_image_hash="sha256:test",
            pip_freeze_output="numpy==1.24.0",
            random_seed=42,
        )

        signer = AuditSigner(secret="test_secret")
        signed_entry = sign_audit_entry(entry, signer, snapshot)

        assert signed_entry.snapshot == snapshot
        assert signed_entry.signature is not None

    def test_signed_entry_serializes_to_json(self):
        """Test SignedAuditEntry serializes to valid JSON."""
        from tools.orchestrator.budget_guard import AuditEntry

        entry = AuditEntry(
            timestamp="2025-10-11T12:00:00Z",
            action="test_action",
            estimated_cost_usd=1.5,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=2.0,
            reason="test",
        )

        signer = AuditSigner(secret="test_secret")
        signed_entry = sign_audit_entry(entry, signer)

        # Serialize to JSON
        json_str = json.dumps(signed_entry.model_dump())
        parsed = json.loads(json_str)

        assert "entry" in parsed
        assert "signature" in parsed
        assert parsed["signature"] == signed_entry.signature


class TestVerifySignature:
    """Test verify_signature() function."""

    def test_verify_signature_returns_true_for_valid(self):
        """Test verify_signature() returns True for valid signed entry."""
        from tools.orchestrator.budget_guard import AuditEntry

        entry = AuditEntry(
            timestamp="2025-10-11T12:00:00Z",
            action="test_action",
            estimated_cost_usd=1.5,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=2.0,
            reason="test",
        )

        signer = AuditSigner(secret="test_secret")
        signed_entry = sign_audit_entry(entry, signer)

        result = verify_signature(signed_entry, signer)
        assert result is True

    def test_verify_signature_returns_false_for_tampered_entry(self):
        """Test verify_signature() returns False when entry is tampered."""
        from tools.orchestrator.budget_guard import AuditEntry

        entry = AuditEntry(
            timestamp="2025-10-11T12:00:00Z",
            action="test_action",
            estimated_cost_usd=1.5,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=2.0,
            reason="test",
        )

        signer = AuditSigner(secret="test_secret")
        signed_entry = sign_audit_entry(entry, signer)

        # Tamper with entry
        tampered_entry = AuditEntry(
            timestamp="2025-10-11T12:00:00Z",
            action="tampered_action",  # Changed
            estimated_cost_usd=1.5,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=2.0,
            reason="test",
        )
        signed_entry.entry = tampered_entry

        result = verify_signature(signed_entry, signer)
        assert result is False

    def test_verify_signature_with_snapshot(self):
        """Test verify_signature() with RunSnapshot."""
        from tools.orchestrator.budget_guard import AuditEntry

        entry = AuditEntry(
            timestamp="2025-10-11T12:00:00Z",
            action="test_action",
            estimated_cost_usd=1.5,
            daily_limit_usd=10.0,
            per_mission_limit_usd=5.0,
            daily_spent_usd=2.0,
            reason="test",
        )

        snapshot = RunSnapshot(
            git_commit_hash="a" * 40,
            docker_image_hash="sha256:test",
            pip_freeze_output="numpy==1.24.0",
            random_seed=42,
        )

        signer = AuditSigner(secret="test_secret")
        signed_entry = sign_audit_entry(entry, signer, snapshot)

        result = verify_signature(signed_entry, signer)
        assert result is True


class TestAppendOnlyAuditLog:
    """Test append-only JSONL audit log writer."""

    def test_append_signed_entry_to_jsonl(self):
        """Test appending SignedAuditEntry to JSONL log."""
        from tools.orchestrator.budget_guard import AuditEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            entry = AuditEntry(
                timestamp="2025-10-11T12:00:00Z",
                action="test_action",
                estimated_cost_usd=1.5,
                daily_limit_usd=10.0,
                per_mission_limit_usd=5.0,
                daily_spent_usd=2.0,
                reason="test",
            )

            signer = AuditSigner(secret="test_secret")
            signed_entry = sign_audit_entry(entry, signer)

            # Write to log
            from tools.orchestrator.audit_signing import append_signed_audit_entry

            append_signed_audit_entry(signed_entry, str(log_path))

            # Verify file exists and content
            assert log_path.exists()
            content = log_path.read_text()
            assert len(content.strip().split("\n")) == 1

            # Parse and verify
            line = content.strip()
            parsed = json.loads(line)
            assert "entry" in parsed
            assert "signature" in parsed

    def test_append_multiple_entries(self):
        """Test appending multiple entries creates separate lines."""
        from tools.orchestrator.budget_guard import AuditEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            signer = AuditSigner(secret="test_secret")

            # Append 3 entries
            for i in range(3):
                entry = AuditEntry(
                    timestamp=f"2025-10-11T12:0{i}:00Z",
                    action=f"action_{i}",
                    estimated_cost_usd=float(i),
                    daily_limit_usd=10.0,
                    per_mission_limit_usd=5.0,
                    daily_spent_usd=0.0,
                    reason=f"test_{i}",
                )

                signed_entry = sign_audit_entry(entry, signer)

                from tools.orchestrator.audit_signing import append_signed_audit_entry

                append_signed_audit_entry(signed_entry, str(log_path))

            # Verify 3 lines
            content = log_path.read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 3

            # Verify each line is valid JSON
            for line in lines:
                parsed = json.loads(line)
                assert "entry" in parsed
                assert "signature" in parsed

    def test_append_preserves_existing_entries(self):
        """Test appending preserves existing entries (append-only)."""
        from tools.orchestrator.budget_guard import AuditEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"

            # Write initial entry manually
            initial_data = {"entry": {"test": "data"}, "signature": "abc123"}
            log_path.write_text(json.dumps(initial_data) + "\n")

            # Append new signed entry
            entry = AuditEntry(
                timestamp="2025-10-11T12:00:00Z",
                action="new_action",
                estimated_cost_usd=1.0,
                daily_limit_usd=10.0,
                per_mission_limit_usd=5.0,
                daily_spent_usd=0.0,
                reason="test",
            )

            signer = AuditSigner(secret="test_secret")
            signed_entry = sign_audit_entry(entry, signer)

            from tools.orchestrator.audit_signing import append_signed_audit_entry

            append_signed_audit_entry(signed_entry, str(log_path))

            # Verify both entries exist
            content = log_path.read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 2

            # First line unchanged
            assert json.loads(lines[0]) == initial_data

            # Second line is new entry
            parsed = json.loads(lines[1])
            assert parsed["entry"]["action"] == "new_action"
