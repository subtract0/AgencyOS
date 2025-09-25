"""
Telemetry System - Production-Grade Event Logging and Analysis

This module provides comprehensive telemetry capabilities extracted from
the enterprise infrastructure branch. Key features:

- Fail-safe JSONL event logging
- Automatic secret sanitization
- Real-time event aggregation and analysis
- Cost tracking and resource monitoring
- Configurable retention and filtering
- Dashboard-ready metrics

Usage:
    from tools.telemetry.sanitize import redact_event
    from tools.telemetry.aggregator import aggregate, list_events

    # Sanitize sensitive data before logging
    safe_event = redact_event(raw_event)

    # Get dashboard metrics
    dashboard = aggregate(since="1h")

    # List recent events with filtering
    events = list_events(since="15m", grep="error")
"""

from .sanitize import redact_event
from .aggregator import aggregate, list_events

# Import enterprise aggregator as well for advanced features
try:
    from .aggregator_enterprise import aggregate as aggregate_enterprise
    __all__ = ["redact_event", "aggregate", "list_events", "aggregate_enterprise"]
except ImportError:
    __all__ = ["redact_event", "aggregate", "list_events"]