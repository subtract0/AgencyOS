"""
Audit Signing Example - Cryptographic Reproducibility for Orchestrator

Demonstrates SHA256 signing, reproducibility snapshots, and tamper detection
for Leap 6: Bulletproof Orchestrator.

Constitutional Compliance:
- Article I: Complete context via RunSnapshot
- Article II: 100% verification via signatures
- ADR-008: Strict typing (Pydantic models)

Usage:
    python tools/orchestrator/audit_signing_example.py
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from tools.orchestrator.audit_signing import (
    AuditSigner,
    RunSnapshot,
    append_signed_audit_entry,
    sign_audit_entry,
    verify_signature,
)
from tools.orchestrator.budget_guard import AuditEntry


def capture_reproducibility_snapshot() -> RunSnapshot:
    """
    Capture current environment state for reproducibility.

    Returns:
        RunSnapshot with git hash, docker hash, pip freeze, seed

    Constitutional Compliance:
    - Article I: Complete context (all reproducibility data)
    """
    # Get git commit hash
    git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

    # Get docker image hash (if available)
    try:
        docker_hash = subprocess.check_output(
            ["docker", "images", "-q", "agency:latest"],
            text=True,
        ).strip()
        if docker_hash:
            docker_hash = f"sha256:{docker_hash}"
        else:
            docker_hash = "sha256:none"
    except (subprocess.CalledProcessError, FileNotFoundError):
        docker_hash = "sha256:none"

    # Get pip freeze output
    pip_freeze = subprocess.check_output(["pip", "freeze"], text=True).strip()

    # Get random seed from environment (or default)
    random_seed = int(os.getenv("RANDOM_SEED", "42"))

    return RunSnapshot(
        git_commit_hash=git_hash,
        docker_image_hash=docker_hash,
        pip_freeze_output=pip_freeze,
        random_seed=random_seed,
    )


def main() -> None:
    """Run audit signing example."""
    print("=== Audit Signing Example for Leap 6 ===\n")

    # 1. Set signing secret (in production, use secure env var)
    os.environ["AUDIT_SIGNING_SECRET"] = "production_secret_key_12345"
    signer = AuditSigner()
    print("✅ AuditSigner initialized with secret from env\n")

    # 2. Capture reproducibility snapshot
    print("📸 Capturing reproducibility snapshot...")
    snapshot = capture_reproducibility_snapshot()
    print(f"   Git commit: {snapshot.git_commit_hash[:8]}...")
    print(f"   Docker image: {snapshot.docker_image_hash[:30]}...")
    print(f"   Pip packages: {len(snapshot.pip_freeze_output.split())} packages")
    print(f"   Random seed: {snapshot.random_seed}\n")

    # 3. Create audit entry (from budget guard)
    entry = AuditEntry(
        timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        action="orchestrator_execution",
        estimated_cost_usd=2.5,
        daily_limit_usd=10.0,
        per_mission_limit_usd=5.0,
        daily_spent_usd=3.5,
        reason="Task graph execution with budget check",
        user=os.getenv("USER", "system"),
    )
    print("📝 Audit entry created:")
    print(f"   Action: {entry.action}")
    print(f"   Cost: ${entry.estimated_cost_usd}")
    print(f"   Daily spend: ${entry.daily_spent_usd}/${entry.daily_limit_usd}\n")

    # 4. Sign entry with snapshot
    print("🔐 Signing audit entry...")
    signed_entry = sign_audit_entry(entry, signer, snapshot)
    print(f"   Signature: {signed_entry.signature[:32]}... (64 chars)\n")

    # 5. Verify signature
    print("✅ Verifying signature...")
    is_valid = verify_signature(signed_entry, signer)
    print(f"   Valid: {is_valid}\n")

    # 6. Demonstrate tamper detection
    print("🔍 Testing tamper detection...")
    original_cost = signed_entry.entry.estimated_cost_usd
    signed_entry.entry.estimated_cost_usd = 999.0
    is_valid_after_tamper = verify_signature(signed_entry, signer)
    print(f"   After tampering cost: Valid={is_valid_after_tamper}")
    print(f"   ❌ Tampering detected: {not is_valid_after_tamper}\n")

    # Restore for next step
    signed_entry.entry.estimated_cost_usd = original_cost

    # 7. Write to append-only audit log
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit_signed.jsonl"

        # Recreate signed entry (untampered)
        signed_entry_clean = sign_audit_entry(entry, signer, snapshot)

        print("📁 Writing to append-only audit log...")
        append_signed_audit_entry(signed_entry_clean, str(log_path))
        print(f"   Path: {log_path}")
        print(f"   Size: {log_path.stat().st_size} bytes")

        # Read back and verify
        content = log_path.read_text()
        print(f"   Entries: {len(content.strip().split(chr(10)))}")
        print("   ✅ JSONL format preserved\n")

    # 8. Summary
    print("=== Implementation Features ===")
    print("✅ Deterministic SHA256 HMAC signing (same input = same signature)")
    print("✅ RunSnapshot captures: git hash, docker hash, pip freeze, random seed")
    print("✅ Signature verification detects any tampering")
    print("✅ Append-only JSONL audit log preserves integrity")
    print("✅ Constitutional compliance: Articles I, II + ADR-008\n")

    print("=== Production Usage ===")
    print("1. Set AUDIT_SIGNING_SECRET in environment (secure storage)")
    print("2. Capture RunSnapshot before orchestrator execution")
    print("3. Sign all budget guard entries with snapshot")
    print("4. Verify signatures on audit log replay")
    print("5. Detect tampering via signature mismatch\n")

    print("🚀 Leap 6: Bulletproof Orchestrator - Audit Signing Complete!")


if __name__ == "__main__":
    main()
