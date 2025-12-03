"""
Life OS API Backends
====================

Pluggable backends for Life Tools to connect to real services.

Backends:
- google_calendar: Google Calendar API integration
- gmail: Gmail API for email
- smtp: SMTP for email sending

Configuration via environment variables:
- LIFE_CALENDAR_BACKEND: "mock" (default) | "google"
- LIFE_EMAIL_BACKEND: "mock" (default) | "gmail" | "smtp"
- GOOGLE_CREDENTIALS_PATH: Path to Google OAuth credentials.json
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD: SMTP configuration
"""

from .base import CalendarBackend, EmailBackend, BackendConfig
from .mock_backend import MockCalendarBackend, MockEmailBackend

# Lazy imports for real backends (require additional dependencies)
def get_calendar_backend(config: BackendConfig = None) -> CalendarBackend:
    """Get the configured calendar backend."""
    import os
    backend_type = os.getenv("LIFE_CALENDAR_BACKEND", "mock")

    if backend_type == "google":
        from .google_calendar import GoogleCalendarBackend
        return GoogleCalendarBackend(config)
    elif backend_type == "apple":
        from .apple_calendar import AppleCalendarBackend
        return AppleCalendarBackend(config)
    else:
        return MockCalendarBackend(config)


def get_email_backend(config: BackendConfig = None) -> EmailBackend:
    """Get the configured email backend."""
    import os
    backend_type = os.getenv("LIFE_EMAIL_BACKEND", "mock")

    if backend_type == "gmail":
        from .gmail import GmailBackend
        return GmailBackend(config)
    elif backend_type == "smtp":
        from .smtp_backend import SmtpBackend
        return SmtpBackend(config)
    else:
        return MockEmailBackend(config)


__all__ = [
    "CalendarBackend",
    "EmailBackend",
    "BackendConfig",
    "MockCalendarBackend",
    "MockEmailBackend",
    "get_calendar_backend",
    "get_email_backend",
]
