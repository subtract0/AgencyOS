"""
Constitutional telemetry emission.

Captures constitutional enforcement events to JSONL and SimpleTelemetry.
Implements Article VII Phase 1: Event Emission Logic.

Dual-path architecture:
1. JSONL append to logs/constitutional_telemetry/events_YYYYMMDD.jsonl
2. SimpleTelemetry integration for unified telemetry sink

Performance requirement: <10ms latency per event
Reliability requirement: Failures never block enforcement
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from core.telemetry import get_telemetry
from shared.models.constitutional import (
    Article,
    ConstitutionalEvent,
    EnforcementAction,
    EnforcementOutcome,
)
from shared.type_definitions.json import JSONValue

logger = logging.getLogger(__name__)


class ConstitutionalTelemetry:
    """
    Manages constitutional enforcement telemetry.

    Dual-path logging:
    1. JSONL files for dedicated constitutional event storage
    2. SimpleTelemetry for unified telemetry sink

    Non-blocking: Failures are logged but never raised
    Performance: <10ms latency per event
    """

    def __init__(self, log_dir: Path | None = None):
        """
        Initialize telemetry with log directory.

        Args:
            log_dir: Directory for JSONL logs (defaults to logs/constitutional_telemetry)
        """
        self.log_dir = log_dir or Path.cwd() / "logs" / "constitutional_telemetry"

        # Best-effort directory creation (non-fatal if fails)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create telemetry directory: {e}")

        self.telemetry = get_telemetry()

    def emit_event(
        self,
        article: Article,
        rule_description: str,
        action: EnforcementAction,
        context: dict[str, JSONValue] | None = None,
        outcome: EnforcementOutcome = EnforcementOutcome.SUCCESS,
        section: str | None = None,
        error_message: str | None = None,
        suggested_fix: str | None = None,
        **kwargs: JSONValue
    ) -> ConstitutionalEvent:
        """
        Emit a constitutional enforcement event.

        Args:
            article: Constitutional article triggered
            rule_description: Human-readable rule description
            action: Enforcement action taken
            context: Contextual metadata
            outcome: Outcome classification
            section: Article section
            error_message: Error message if blocked
            suggested_fix: Suggested remediation
            **kwargs: Additional metadata

        Returns:
            ConstitutionalEvent: Created event
        """
        # Generate unique event ID
        from datetime import UTC
        event_id = f"const_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Create event
        event = ConstitutionalEvent(
            event_id=event_id,
            article=article,
            section=section,
            rule_description=rule_description,
            context=context or {},
            action=action,
            outcome=outcome,
            error_message=error_message,
            suggested_fix=suggested_fix,
            metadata=kwargs,
        )

        # Path 1: Write to dedicated JSONL log
        self._write_jsonl(event)

        # Path 2: Emit to unified telemetry
        self._emit_to_telemetry(event)

        return event

    def _write_jsonl(self, event: ConstitutionalEvent) -> None:
        """
        Write event to daily JSONL file.

        Non-blocking: Failures are logged but never raised.

        Args:
            event: Event to write
        """
        date_str = event.timestamp.strftime("%Y%m%d")
        log_file = self.log_dir / f"events_{date_str}.jsonl"

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.to_jsonl() + "\n")
        except Exception as e:
            # Non-fatal: telemetry failures should not block enforcement
            logger.warning(f"Failed to write constitutional telemetry: {e}")

    def _emit_to_telemetry(self, event: ConstitutionalEvent) -> None:
        """
        Emit event to unified telemetry system.

        Args:
            event: Event to emit
        """
        try:
            self.telemetry.log(
                event="constitutional_enforcement",
                data={
                    "event_id": event.event_id,
                    "article": event.article.value,
                    "section": event.section,
                    "rule": event.rule_description,
                    "action": event.action.value,
                    "outcome": event.outcome.value,
                    "context": event.context,
                },
                level=self._map_severity(event.action),
            )
        except Exception as e:
            # Non-fatal: telemetry failures should not block enforcement
            logger.warning(f"Failed to emit to SimpleTelemetry: {e}")

    def _map_severity(self, action: EnforcementAction) -> str:
        """
        Map enforcement action to telemetry severity level.

        Args:
            action: Enforcement action

        Returns:
            Severity level (info, warning, error, critical)
        """
        mapping = {
            EnforcementAction.BLOCKED: "error",
            EnforcementAction.WARNING: "warning",
            EnforcementAction.AUTO_FIX: "info",
            EnforcementAction.PASSED: "info",
        }
        return mapping.get(action, "info")


# Global singleton
_telemetry_instance: ConstitutionalTelemetry | None = None


def get_constitutional_telemetry() -> ConstitutionalTelemetry:
    """
    Get global constitutional telemetry instance (singleton).

    Returns:
        ConstitutionalTelemetry: Global instance
    """
    global _telemetry_instance
    if _telemetry_instance is None:
        _telemetry_instance = ConstitutionalTelemetry()
    return _telemetry_instance


def emit_constitutional_event(
    article: Article,
    rule_description: str,
    action: EnforcementAction,
    **kwargs: JSONValue
) -> ConstitutionalEvent:
    """
    Convenience function to emit constitutional event.

    Args:
        article: Constitutional article
        rule_description: Rule description
        action: Enforcement action
        **kwargs: Additional event parameters

    Returns:
        ConstitutionalEvent: Created event
    """
    telemetry = get_constitutional_telemetry()
    return telemetry.emit_event(article, rule_description, action, **kwargs)
