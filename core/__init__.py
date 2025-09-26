"""
Unified Core Module - Single import point for all core functionality.
Simplifies imports and provides a clean API for autonomous agents.
"""

import os
from typing import Optional, List
from shared.types.json import JSONValue

# Feature flags
ENABLE_UNIFIED_CORE = os.getenv("ENABLE_UNIFIED_CORE", "true").lower() == "true"
PERSIST_PATTERNS = os.getenv("PERSIST_PATTERNS", "false").lower() == "true"

# Core imports
from .self_healing import SelfHealingCore, Finding, Patch
from .telemetry import SimpleTelemetry, get_telemetry, emit
from .patterns import UnifiedPatternStore, Pattern, get_pattern_store
from shared.models.core import (
    ErrorDetectionResult, HealthStatus,
    HealingAttempt, ToolCall, TelemetryEvent
)

# Learning loop imports (conditionally imported to avoid circular dependencies)
try:
    from learning_loop import LearningLoop
    LEARNING_LOOP_AVAILABLE = True
except ImportError:
    LearningLoop = None
    LEARNING_LOOP_AVAILABLE = False

# Singleton instances
_healing_core: Optional[SelfHealingCore] = None
_telemetry: Optional[SimpleTelemetry] = None
_pattern_store: Optional[UnifiedPatternStore] = None
_learning_loop: Optional['LearningLoop'] = None


def get_healing_core() -> SelfHealingCore:
    """Get the global self-healing core instance."""
    global _healing_core
    if _healing_core is None:
        _healing_core = SelfHealingCore()
    return _healing_core


def get_unified_telemetry() -> SimpleTelemetry:
    """Get the global telemetry instance."""
    return get_telemetry()


def get_unified_patterns() -> UnifiedPatternStore:
    """Get the global pattern store instance."""
    return get_pattern_store()


def get_learning_loop() -> Optional['LearningLoop']:
    """
    Get the global learning loop instance.

    Returns:
        LearningLoop instance or None if not available
    """
    global _learning_loop
    if not LEARNING_LOOP_AVAILABLE:
        return None

    if _learning_loop is None:
        _learning_loop = LearningLoop()
    return _learning_loop


class UnifiedCore:
    """
    Facade class providing simplified access to all core functionality.
    This is the primary interface for autonomous agents.
    """

    def __init__(self):
        """Initialize unified core with all subsystems."""
        self.healing = get_healing_core() if ENABLE_UNIFIED_CORE else None
        self.telemetry = get_unified_telemetry()
        self.patterns = get_unified_patterns()
        self.learning_loop = get_learning_loop() if ENABLE_UNIFIED_CORE else None

    def detect_and_fix_errors(self, path: str) -> ErrorDetectionResult:
        """
        Complete error detection and fixing workflow.

        Args:
            path: File path or log content to analyze

        Returns:
            Dictionary with results including errors found, fixes applied, and success status
        """
        results = ErrorDetectionResult(
            errors_found=0,
            fixes_applied=0,
            success=True,
            details=[]
        )

        if not self.healing:
            self.telemetry.log("core.healing_disabled", {
                "reason": "ENABLE_UNIFIED_CORE not set"
            }, level="warning")
            return results

        # Detect errors
        findings = self.healing.detect_errors(path)
        results.errors_found = len(findings)
        results.findings = findings

        # Attempt to fix each error
        for finding in findings:
            fix_success = self.healing.fix_error(finding)

            if fix_success:
                results.fixes_applied += 1
                results.details.append(
                    f"Fixed: {finding.snippet} in {finding.file}"
                )

                # Learn from successful fix
                if self.patterns:
                    self.patterns.update_success_rate(
                        pattern_id=f"{finding.error_type}_auto",
                        success=True
                    )
            else:
                results.success = False
                results.details.append(
                    f"Failed to fix: {finding.snippet} in {finding.file}"
                )

        # Log results
        self.telemetry.log("core.healing_complete", results.model_dump())

        return results

    def get_health_status(self) -> HealthStatus:
        """
        Get overall system health status.

        Returns:
            Dictionary with health metrics and status
        """
        metrics = self.telemetry.get_metrics()
        pattern_stats = self.patterns.get_statistics() if self.patterns else {}

        health_score = metrics.get("health_score", 100.0)
        return HealthStatus(
            status="healthy" if health_score > 80 else "degraded",
            healing_enabled=self.healing is not None,
            patterns_loaded=pattern_stats.get("total_patterns", 0),
            telemetry_active=self.telemetry is not None,
            learning_loop_active=self.learning_loop is not None,
            errors=metrics.get("recent_errors", []),
            warnings=metrics.get("recent_warnings", [])
        )

    def emit_event(self, event: str, data: dict[str, JSONValue] = None, level: str = "info"):
        """
        Emit a telemetry event.

        Args:
            event: Event name
            data: Event data
            level: Log level (info, warning, error, critical)
        """
        self.telemetry.log(event, data or {}, level)

    def learn_pattern(self, error_type: str, original: str, fixed: str, success: bool):
        """
        Learn a new pattern from an error fix.

        Args:
            error_type: Type of error
            original: Original code
            fixed: Fixed code
            success: Whether the fix was successful
        """
        if self.patterns:
            self.patterns.learn_from_fix(error_type, original, fixed, success)

    def find_patterns(self, query: str = None, pattern_type: str = None) -> List[Pattern]:
        """
        Find patterns matching criteria.

        Args:
            query: Search query
            pattern_type: Filter by type

        Returns:
            List of matching patterns
        """
        if self.patterns:
            return self.patterns.find(query=query, pattern_type=pattern_type)
        return []

    def start_learning_loop(self):
        """
        Start the autonomous learning loop system.

        This activates continuous learning and healing capabilities:
        - File monitoring for learning opportunities
        - Error detection and autonomous healing
        - Pattern extraction from successful operations
        - Anti-pattern learning from failures
        """
        if self.learning_loop:
            self.learning_loop.start()
            self.emit_event("learning_loop_started", {
                "timestamp": self.learning_loop.start_time.isoformat() if self.learning_loop.start_time else None
            })
        else:
            self.emit_event("learning_loop_unavailable", {
                "reason": "LearningLoop not available or ENABLE_UNIFIED_CORE disabled"
            }, level="warning")

    def stop_learning_loop(self):
        """
        Stop the autonomous learning loop system gracefully.

        This stops all monitoring and saves learned patterns.
        """
        if self.learning_loop and self.learning_loop.is_running:
            self.learning_loop.stop()
            self.emit_event("learning_loop_stopped", {})
        else:
            self.emit_event("learning_loop_not_running", {}, level="info")

    async def run_autonomous_learning(self, duration_hours: float = 24.0):
        """
        Run autonomous learning for specified duration.

        Args:
            duration_hours: How long to run autonomously (default: 24 hours)
        """
        if self.learning_loop:
            await self.learning_loop.run_autonomous(duration_hours)
        else:
            self.emit_event("autonomous_learning_unavailable", {
                "reason": "LearningLoop not available"
            }, level="warning")

    def get_learning_metrics(self) -> dict[str, JSONValue]:
        """
        Get learning loop operational metrics.

        Returns:
            dict[str, JSONValue]: learning loop metrics when available, otherwise {}
        """
        if self.learning_loop:
            # Preserve backward-compatible raw metrics dict expected by tests/consumers
            metrics = self.learning_loop.get_metrics()
            return metrics if isinstance(metrics, dict) else {}
        return {}

    def learn_from_operation_result(self, operation_id: str, success: bool,
                                  task_description: str = None,
                                  tool_calls: List[ToolCall] = None,
                                  initial_error: str = None,
                                  final_state: str = None,
                                  duration_seconds: float = 0.0):
        """
        Learn patterns from an operation result.

        This is a convenience method for external systems to feed learning data
        into the learning loop.

        Args:
            operation_id: Unique identifier for the operation
            success: Whether the operation succeeded
            task_description: Human-readable description of what was attempted
            tool_calls: List of tool calls made during the operation
            initial_error: Error that triggered the operation (if any)
            final_state: Final state after operation completion
            duration_seconds: How long the operation took
        """
        if not self.learning_loop:
            return

        from learning_loop.pattern_extraction import Operation
        from datetime import datetime

        operation = Operation(
            id=operation_id,
            task_description=task_description,
            initial_error=initial_error,
            tool_calls=tool_calls or [],
            final_state=final_state or {},
            success=success,
            duration_seconds=duration_seconds,
            timestamp=datetime.now()
        )

        self.learning_loop.learn_from_operation(operation)


# Global unified core instance
_unified_core: Optional[UnifiedCore] = None


def get_core() -> UnifiedCore:
    """
    Get the global unified core instance.
    This is the primary entry point for all core functionality.

    Returns:
        UnifiedCore: The global core instance
    """
    global _unified_core
    if _unified_core is None:
        _unified_core = UnifiedCore()
    return _unified_core


# Convenience exports
__all__ = [
    # Main interface
    "get_core",
    "UnifiedCore",

    # Core components
    "SelfHealingCore",
    "SimpleTelemetry",
    "UnifiedPatternStore",

    # Data classes
    "Finding",
    "Patch",
    "Pattern",

    # Convenience functions
    "emit",
    "get_healing_core",
    "get_unified_telemetry",
    "get_unified_patterns",
    "get_learning_loop",

    # Feature flags
    "ENABLE_UNIFIED_CORE",
    "PERSIST_PATTERNS",
    "LEARNING_LOOP_AVAILABLE",
]

# Conditionally add learning loop exports if available
if LEARNING_LOOP_AVAILABLE:
    __all__.append("LearningLoop")