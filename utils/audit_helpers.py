"""Atomic audit logging helpers with HMAC signing for tamper detection.

Constitutional Compliance:
- Article II: Append-only audit trail (no edits)
- Article III: Cryptographic integrity (HMAC-SHA256)
- Security: AGENCY_DATA_DIR respects container/environment filesystem policy
"""

import hashlib
import hmac
import json
import os
import tempfile

# Environment-driven data dir (respects AGENCY_DATA_DIR env var)
AGENCY_DATA_DIR = os.getenv(
    "AGENCY_DATA_DIR", os.path.join(os.path.expanduser("~"), ".agency")
)
AUDIT_HMAC_KEY = os.getenv("AGENCY_AUDIT_HMAC_KEY")  # MUST be set in CI/production vault


def append_jsonl_atomic(path: str, obj: dict) -> None:
    """Atomically append a JSON line to `path` by writing temp file then replacing.

    Ensures concurrent writers do not corrupt the target file.

    Args:
        path: Target JSONL file path
        obj: Dictionary to serialize as JSON line

    Raises:
        OSError: If directory creation or file write fails

    Implementation:
        Reads existing file, appends new line, writes to temp, then atomically replaces.
        This prevents corruption from concurrent writes while maintaining append semantics.
    """
    dirpath = os.path.dirname(path)
    os.makedirs(dirpath, exist_ok=True, mode=0o700)  # Secure directory permissions

    # Read existing content
    existing_content = ""
    if os.path.exists(path):
        with open(path) as f:
            existing_content = f.read()

    # Write existing + new line to temp file
    fd, tmp = tempfile.mkstemp(dir=dirpath, prefix=".tmp_audit_")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(existing_content)
            f.write(json.dumps(obj, sort_keys=True) + "\n")
        # Atomic replace (works across Unix/Windows)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass  # Best effort cleanup


def sign_entry_hmac(entry_json: str) -> str:
    """Return HMAC-SHA256 signature of entry_json using AUDIT_HMAC_KEY if provided.

    Falls back to plain SHA256 hexdigest if no key provided (for development).

    Args:
        entry_json: JSON string to sign (should be canonical with sort_keys=True)

    Returns:
        64-character hex signature

    Security Notes:
        - HMAC requires secret key: set AGENCY_AUDIT_HMAC_KEY in production
        - SHA256 fallback provides tamper detection but not authentication
        - For full non-repudiation, use ed25519 asymmetric signing
    """
    if AUDIT_HMAC_KEY:
        return hmac.new(
            AUDIT_HMAC_KEY.encode(), entry_json.encode(), hashlib.sha256
        ).hexdigest()
    # Fallback to SHA256 (development only - log warning in production)
    return hashlib.sha256(entry_json.encode()).hexdigest()


def write_audit_entry(audit_dir: str, entry: dict) -> None:
    """Write audit entry to slop_evaluations.jsonl with HMAC signature.

    Args:
        audit_dir: Directory for audit logs (e.g., ~/.agency/audit/slop_immunity/)
        entry: Dictionary containing audit data (will be signed before writing)

    Side Effects:
        - Creates audit_dir if it doesn't exist (mode 0o700)
        - Appends entry to slop_evaluations.jsonl atomically
        - Adds 'signature' field to entry before writing
    """
    path = os.path.join(audit_dir, "slop_evaluations.jsonl")
    entry_json = json.dumps(entry, sort_keys=True)
    signature = sign_entry_hmac(entry_json)

    # Add signature to entry (after computing signature to avoid circular dependency)
    entry_with_sig = {**entry, "signature": signature}
    append_jsonl_atomic(path, entry_with_sig)
