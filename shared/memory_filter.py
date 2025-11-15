"""
PII redaction filter for memory storage.

Mission 1.5 of Metaproductivity 2.0 - Privacy protection.

This module provides functions to redact personally identifiable information (PII)
from text before storing it in memory systems (EnhancedMemoryStore, VectorStore, etc.).

Constitutional Compliance:
- Article IV: Protects user privacy in learning systems
- GDPR/CCPA alignment: Prevents accidental PII storage

Usage:
    from shared.memory_filter import redact

    text = "Contact john@example.com or call 123-456-7890"
    safe_text = redact(text)
    # Result: "Contact [EMAIL_REDACTED] or call [PHONE_REDACTED]"
"""

import re


# PII Regex Patterns
# Optimized for high precision (minimize false positives) while maintaining recall

# Email: Standard RFC 5322 simplified pattern
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

# Phone: US format (10 digits with optional separators)
# Matches: 123-456-7890, 123.456.7890, 1234567890
PHONE_PATTERN = re.compile(
    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
)

# SSN: US format (XXX-XX-XXXX)
SSN_PATTERN = re.compile(
    r'\b\d{3}-\d{2}-\d{4}\b'
)

# API Keys/Secrets: Common prefixes followed by 20+ characters (including separators)
# Matches: api_*, sk_*, pk_*, token_*, API_*, sk_test_*, pk_live_*, etc.
API_KEY_PATTERN = re.compile(
    r'\b(sk|pk|api|token)[-_][A-Za-z0-9_-]{20,}\b',
    re.IGNORECASE
)


def redact(text: str) -> str:
    """
    Redact PII from text before storage.

    Redacts the following PII types:
    - Email addresses → [EMAIL_REDACTED]
    - Phone numbers (US format) → [PHONE_REDACTED]
    - Social Security Numbers → [SSN_REDACTED]
    - API keys/tokens → [SECRET_REDACTED]

    Args:
        text: Input text potentially containing PII

    Returns:
        Text with PII replaced by redaction markers

    Examples:
        >>> redact("Email: john@test.com, Phone: 123-456-7890")
        'Email: [EMAIL_REDACTED], Phone: [PHONE_REDACTED]'

        >>> redact("API key: sk_test_1234567890abcdefghij")
        'API key: [SECRET_REDACTED]'
    """
    if not text:
        return text

    # Apply redaction patterns in order
    # Order matters: more specific patterns first to avoid partial redactions

    # 1. Emails
    text = EMAIL_PATTERN.sub('[EMAIL_REDACTED]', text)

    # 2. SSNs (before phone, to avoid SSN being partially matched as phone)
    text = SSN_PATTERN.sub('[SSN_REDACTED]', text)

    # 3. Phone numbers
    text = PHONE_PATTERN.sub('[PHONE_REDACTED]', text)

    # 4. API keys and secrets
    text = API_KEY_PATTERN.sub('[SECRET_REDACTED]', text)

    return text


def redact_dict(data: dict) -> dict:
    """
    Recursively redact PII from dictionary values.

    Useful for redacting JSON-serializable data structures.

    Args:
        data: Dictionary with potentially sensitive values

    Returns:
        New dictionary with PII redacted from string values

    Examples:
        >>> redact_dict({"email": "user@test.com", "count": 42})
        {'email': '[EMAIL_REDACTED]', 'count': 42}
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = redact(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
        elif isinstance(value, list):
            result[key] = [
                redact(item) if isinstance(item, str) else
                redact_dict(item) if isinstance(item, dict) else
                item
                for item in value
            ]
        else:
            result[key] = value
    return result


def is_redacted(text: str) -> bool:
    """
    Check if text contains redaction markers.

    Useful for testing or avoiding double-redaction.

    Args:
        text: Text to check

    Returns:
        True if text contains any redaction markers

    Examples:
        >>> is_redacted("Contact: [EMAIL_REDACTED]")
        True

        >>> is_redacted("No PII here")
        False
    """
    redaction_markers = [
        '[EMAIL_REDACTED]',
        '[PHONE_REDACTED]',
        '[SSN_REDACTED]',
        '[SECRET_REDACTED]'
    ]
    return any(marker in text for marker in redaction_markers)
