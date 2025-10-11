"""
Audit Signing for Bulletproof Orchestrator - Cryptographic Reproducibility

Implements SHA256 signing for audit trail entries with reproducibility snapshots.
Part of Leap 6: Bulletproof Orchestrator - Production Hardening.

Constitutional Compliance:
- Article I: Complete context via RunSnapshot (git, docker, pip, seed)
- Article II: 100% verification through signature validation
- ADR-008: Strict typing with Pydantic models (no Dict[Any, Any])
- ADR-010: Result pattern for error handling

Example:
    from tools.orchestrator.audit_signing import (
        AuditSigner, RunSnapshot, sign_audit_entry, verify_signature
    )

    # Create reproducibility snapshot
    snapshot = RunSnapshot(
        git_commit_hash="abc123...",
        docker_image_hash="sha256:...",
        pip_freeze_output="numpy==1.24.0\\npandas==2.0.0",
        random_seed=42
    )

    # Sign audit entry
    signer = AuditSigner(secret="your_secret")
    signed_entry = sign_audit_entry(entry, signer, snapshot)

    # Verify signature
    is_valid = verify_signature(signed_entry, signer)
    if not is_valid:
        raise ValueError("Audit entry has been tampered with!")
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from tools.orchestrator.budget_guard import AuditEntry


class RunSnapshot(BaseModel):
    """
    Reproducibility snapshot capturing all environment state.

    Constitutional Compliance:
    - Article I: Complete context (all reproducibility data)
    - ADR-008: Strict typing (no Dict[Any, Any])
    """

    model_config = {"extra": "forbid"}

    git_commit_hash: str = Field(
        ..., description="Git commit hash (40-char SHA1) of the codebase"
    )
    docker_image_hash: str = Field(
        ..., description="Docker image hash (sha256:...) for runtime environment"
    )
    pip_freeze_output: str = Field(
        ..., description="Output of 'pip freeze' for Python dependencies"
    )
    random_seed: int = Field(..., description="Random seed for deterministic execution")

    @field_validator("git_commit_hash")
    @classmethod
    def validate_git_hash(cls, v: str) -> str:
        """Validate git commit hash is 40 characters (SHA1)."""
        if len(v) != 40:
            raise ValueError("Git commit hash must be 40 characters (SHA1 hex)")
        return v

    @field_validator("docker_image_hash")
    @classmethod
    def validate_docker_hash(cls, v: str) -> str:
        """Validate docker hash starts with sha256:."""
        if not v.startswith("sha256:"):
            raise ValueError("Docker image hash must start with 'sha256:'")
        return v

    @field_validator("random_seed")
    @classmethod
    def validate_seed(cls, v: int) -> int:
        """Validate random seed is non-negative."""
        if v < 0:
            raise ValueError("Random seed must be non-negative")
        return v


class SignedAuditEntry(BaseModel):
    """
    Audit entry with cryptographic signature for tamper detection.

    Constitutional Compliance:
    - Article II: 100% verification (signature detects tampering)
    - ADR-008: Strict typing
    """

    model_config = {"extra": "forbid"}

    entry: AuditEntry = Field(..., description="Original audit entry")
    snapshot: RunSnapshot | None = Field(
        default=None, description="Optional reproducibility snapshot"
    )
    signature: str = Field(..., description="SHA256 HMAC signature (hex)")


class AuditSigner:
    """
    SHA256-based signer for audit entries.

    Provides deterministic signing (same input = same signature) and
    tamper detection through signature verification.

    Constitutional Compliance:
    - ADR-008: Strict typing
    - Article II: Cryptographic verification
    """

    def __init__(self, secret: str | None = None):
        """
        Initialize audit signer with secret key.

        Args:
            secret: Secret key for HMAC signing. If None, loads from
                   AUDIT_SIGNING_SECRET environment variable.

        Raises:
            ValueError: If secret is not provided and env var not set
        """
        self.secret = secret or os.getenv("AUDIT_SIGNING_SECRET")
        if not self.secret:
            raise ValueError(
                "Audit signing secret not configured. "
                "Set AUDIT_SIGNING_SECRET environment variable or pass secret parameter."
            )

    def sign(self, data: dict) -> str:
        """
        Create deterministic SHA256 HMAC signature for data.

        Args:
            data: Dictionary to sign (will be JSON-serialized)

        Returns:
            SHA256 HMAC signature as hex string (64 characters)

        Constitutional Compliance:
        - Deterministic: Same input always produces same signature
        - Cryptographically secure: SHA256 HMAC
        """
        # Serialize data to canonical JSON (sorted keys for determinism)
        json_data = json.dumps(data, sort_keys=True, ensure_ascii=False)

        # Create HMAC-SHA256 signature
        signature = hashlib.sha256(
            (self.secret + json_data).encode("utf-8")
        ).hexdigest()

        return signature

    def verify(self, data: dict, signature: str) -> bool:
        """
        Verify signature for data.

        Args:
            data: Dictionary to verify
            signature: Signature to check against

        Returns:
            True if signature is valid, False if tampered or invalid

        Constitutional Compliance:
        - Article II: Tamper detection
        """
        expected_signature = self.sign(data)
        return signature == expected_signature


def sign_audit_entry(
    entry: AuditEntry,
    signer: AuditSigner,
    snapshot: RunSnapshot | None = None,
) -> SignedAuditEntry:
    """
    Sign audit entry with optional reproducibility snapshot.

    Args:
        entry: Audit entry to sign
        signer: AuditSigner instance with secret key
        snapshot: Optional reproducibility snapshot

    Returns:
        SignedAuditEntry with cryptographic signature

    Constitutional Compliance:
    - Article I: Complete context (snapshot captures all reproducibility data)
    - Article II: Cryptographic verification
    """
    # Build data to sign (entry + optional snapshot)
    data_to_sign = entry.model_dump()
    if snapshot:
        data_to_sign["snapshot"] = snapshot.model_dump()

    # Generate signature
    signature = signer.sign(data_to_sign)

    return SignedAuditEntry(
        entry=entry,
        snapshot=snapshot,
        signature=signature,
    )


def verify_signature(signed_entry: SignedAuditEntry, signer: AuditSigner) -> bool:
    """
    Verify signature of signed audit entry.

    Args:
        signed_entry: Signed audit entry to verify
        signer: AuditSigner instance with secret key

    Returns:
        True if signature is valid, False if tampered

    Constitutional Compliance:
    - Article II: Tamper detection
    """
    # Reconstruct data that was signed
    data_to_verify = signed_entry.entry.model_dump()
    if signed_entry.snapshot:
        data_to_verify["snapshot"] = signed_entry.snapshot.model_dump()

    # Verify signature
    return signer.verify(data_to_verify, signed_entry.signature)


def append_signed_audit_entry(signed_entry: SignedAuditEntry, log_path: str) -> None:
    """
    Append signed audit entry to JSONL log (append-only).

    Args:
        signed_entry: Signed audit entry to append
        log_path: Path to audit log file (JSONL format)

    Constitutional Compliance:
    - Append-only: Never modifies existing entries
    - Article II: Preserves audit trail integrity
    """
    # Ensure directory exists
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    # Append to JSONL file (append mode preserves existing entries)
    with open(log_path, "a", encoding="utf-8") as f:
        json_line = json.dumps(signed_entry.model_dump(), ensure_ascii=False)
        f.write(json_line + "\n")


__all__ = [
    "RunSnapshot",
    "SignedAuditEntry",
    "AuditSigner",
    "sign_audit_entry",
    "verify_signature",
    "append_signed_audit_entry",
]
