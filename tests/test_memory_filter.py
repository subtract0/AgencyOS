"""
Tests for PII redaction filter.

Mission 1.5 of Metaproductivity 2.0 - Privacy protection for memory storage.
"""

import pytest

from shared.memory_filter import redact


class TestEmailRedaction:
    """Test email address redaction patterns."""

    def test_simple_email(self):
        """Should redact standard email format."""
        text = "Contact me at john.doe@example.com for details"
        result = redact(text)
        assert "[EMAIL_REDACTED]" in result
        assert "john.doe@example.com" not in result

    def test_multiple_emails(self):
        """Should redact all email addresses."""
        text = "Email alice@test.com or bob@company.org"
        result = redact(text)
        assert result.count("[EMAIL_REDACTED]") == 2
        assert "alice@test.com" not in result
        assert "bob@company.org" not in result

    def test_email_with_plus_sign(self):
        """Should redact emails with + sign (common Gmail pattern)."""
        text = "Send to user+tag@gmail.com"
        result = redact(text)
        assert "[EMAIL_REDACTED]" in result
        assert "user+tag@gmail.com" not in result

    def test_email_with_subdomain(self):
        """Should redact emails with subdomain."""
        text = "Contact admin@mail.example.com"
        result = redact(text)
        assert "[EMAIL_REDACTED]" in result
        assert "admin@mail.example.com" not in result


class TestPhoneRedaction:
    """Test phone number redaction patterns."""

    def test_phone_with_dashes(self):
        """Should redact phone with dashes (123-456-7890)."""
        text = "Call me at 123-456-7890"
        result = redact(text)
        assert "[PHONE_REDACTED]" in result
        assert "123-456-7890" not in result

    def test_phone_with_dots(self):
        """Should redact phone with dots (123.456.7890)."""
        text = "Phone: 123.456.7890"
        result = redact(text)
        assert "[PHONE_REDACTED]" in result
        assert "123.456.7890" not in result

    def test_phone_no_separator(self):
        """Should redact phone without separators (1234567890)."""
        text = "Text 1234567890 for info"
        result = redact(text)
        assert "[PHONE_REDACTED]" in result
        assert "1234567890" not in result

    def test_multiple_phones(self):
        """Should redact all phone numbers."""
        text = "Call 123-456-7890 or 987.654.3210"
        result = redact(text)
        assert result.count("[PHONE_REDACTED]") == 2


class TestSSNRedaction:
    """Test SSN redaction patterns."""

    def test_ssn_with_dashes(self):
        """Should redact SSN format (123-45-6789)."""
        text = "SSN: 123-45-6789"
        result = redact(text)
        assert "[SSN_REDACTED]" in result
        assert "123-45-6789" not in result

    def test_ssn_in_sentence(self):
        """Should redact SSN embedded in text."""
        text = "Employee SSN 987-65-4321 verified"
        result = redact(text)
        assert "[SSN_REDACTED]" in result
        assert "987-65-4321" not in result


class TestAPIKeyRedaction:
    """Test API key and secret redaction patterns."""

    def test_api_key_with_prefix(self):
        """Should redact API keys with common prefixes."""
        text = "Use API key: api_1234567890abcdefghij"
        result = redact(text)
        assert "[SECRET_REDACTED]" in result
        assert "api_1234567890abcdefghij" not in result

    def test_secret_key_prefix(self):
        """Should redact secret keys with sk prefix."""
        text = "Secret: sk-1234567890abcdefghijklmnop"
        result = redact(text)
        assert "[SECRET_REDACTED]" in result
        assert "sk-1234567890abcdefghijklmnop" not in result

    def test_public_key_prefix(self):
        """Should redact public keys with pk prefix."""
        text = "Public key: pk_test_1234567890abcdefg"
        result = redact(text)
        assert "[SECRET_REDACTED]" in result
        assert "pk_test_1234567890abcdefg" not in result

    def test_token_prefix(self):
        """Should redact tokens."""
        text = "Bearer token-abcdefghijklmnopqrstuvwxyz123456"
        result = redact(text)
        assert "[SECRET_REDACTED]" in result
        assert "token-abcdefghijklmnopqrstuvwxyz123456" not in result

    def test_case_insensitive_api_key(self):
        """Should redact API keys regardless of case."""
        text = "API_KEY: API_1234567890ABCDEFGHIJ"
        result = redact(text)
        assert "[SECRET_REDACTED]" in result
        assert "API_1234567890ABCDEFGHIJ" not in result


class TestMultiplePatterns:
    """Test redacting multiple PII types in same text."""

    def test_email_and_phone(self):
        """Should redact both email and phone."""
        text = "Contact john@example.com or call 123-456-7890"
        result = redact(text)
        assert "[EMAIL_REDACTED]" in result
        assert "[PHONE_REDACTED]" in result
        assert "john@example.com" not in result
        assert "123-456-7890" not in result

    def test_all_patterns(self):
        """Should redact all PII types in complex text."""
        text = (
            "Employee john.doe@company.com, SSN 123-45-6789, "
            "phone 555-123-4567, API key: api_secret1234567890abcdef"
        )
        result = redact(text)
        assert "[EMAIL_REDACTED]" in result
        assert "[SSN_REDACTED]" in result
        assert "[PHONE_REDACTED]" in result
        assert "[SECRET_REDACTED]" in result
        assert "john.doe@company.com" not in result
        assert "123-45-6789" not in result
        assert "555-123-4567" not in result
        assert "api_secret1234567890abcdef" not in result

    def test_preserves_non_pii_text(self):
        """Should preserve text that is not PII."""
        text = "This is a test message with no PII"
        result = redact(text)
        assert result == text  # No changes


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string(self):
        """Should handle empty string."""
        result = redact("")
        assert result == ""

    def test_none_pii_numbers(self):
        """Should not redact non-PII numbers."""
        text = "Version 1.2.3 requires Python 3.10"
        result = redact(text)
        assert "1.2.3" in result
        assert "3.10" in result

    def test_partial_phone_not_redacted(self):
        """Should not redact partial phone numbers."""
        text = "The code is 12345"
        result = redact(text)
        assert "12345" in result  # Too short for phone pattern

    def test_url_email_distinction(self):
        """Should redact email but preserve non-email @ symbols."""
        text = "Mention @user on social media, email: real@example.com"
        result = redact(text)
        assert "@user" in result  # Social media handle preserved
        assert "[EMAIL_REDACTED]" in result
        assert "real@example.com" not in result


class TestIntegrationWithMemoryStore:
    """Test integration patterns with EnhancedMemoryStore."""

    def test_redact_json_serializable_content(self):
        """Should handle JSON-like content."""
        text = '{"email": "user@test.com", "phone": "123-456-7890"}'
        result = redact(text)
        assert "[EMAIL_REDACTED]" in result
        assert "[PHONE_REDACTED]" in result

    def test_redact_multiline_content(self):
        """Should handle multiline content."""
        text = """Line 1: Contact alice@example.com
Line 2: Phone: 555-123-4567
Line 3: API key: sk_test_1234567890abcdefghij"""
        result = redact(text)
        assert "[EMAIL_REDACTED]" in result
        assert "[PHONE_REDACTED]" in result
        assert "[SECRET_REDACTED]" in result

    def test_idempotent_redaction(self):
        """Should be idempotent - redacting already redacted text."""
        text = "Email: [EMAIL_REDACTED], Phone: [PHONE_REDACTED]"
        result = redact(text)
        assert result == text  # No double redaction
