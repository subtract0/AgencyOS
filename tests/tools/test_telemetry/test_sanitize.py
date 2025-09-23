from __future__ import annotations

from tools.telemetry.sanitize import redact_event


def test_redact_sensitive_keys_and_patterns():
    ev = {
        "type": "task_finished",
        "agent": "A",
        "Authorization": "Bearer sk-THISISASECRET123456",
        "api_key": "ghp_ABCDEF0123456789SECRETKEY",
        "nested": {
            "token": "xoxb-1234-SECRET-5678",
            "note": "Google key AIzaSyDUMMYKEY-123456",
        },
        "usage": {"prompt_tokens": 10},
    }

    red = redact_event(ev)

    # Keys are preserved but sensitive values redacted
    assert red["Authorization"].endswith("[REDACTED]") or red["Authorization"] == "[REDACTED]" or "[REDACTED]" in red["Authorization"]
    assert red["api_key"] == "[REDACTED]"
    assert red["nested"]["token"] == "[REDACTED]"
    assert "[REDACTED]" in red["nested"]["note"]

    # Non-sensitive data should remain
    assert red["usage"]["prompt_tokens"] == 10
