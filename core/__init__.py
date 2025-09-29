"""
Unified Core Module - Single import point for all core functionality.
Simplifies imports and provides a clean API for autonomous agents.
"""

import os
from typing import Optional, List, Union, Dict
from shared.type_definitions.json import JSONValue

# Feature flags
ENABLE_UNIFIED_CORE = os.getenv("ENABLE_UNIFIED_CORE", "true").lower() == "true"
PERSIST_PATTERNS = os.getenv("PERSIST_PATTERNS", "false").lower() == "true"

# Core imports
from .self_healing import SelfHealingCore, Finding, Patch
from .telemetry import SimpleTelemetry, get_telemetry, emit
from pattern_intelligence import PatternStore, CodingPattern
from shared.models.core import (
    ErrorDetectionResult, HealthStatus,
    HealingAttempt, ToolCall, TelemetryEvent
)

# Learning loop imports (conditionally imported to avoid circular dependencies)
try:
    from learning_loop import LearningLoop
    LEARNING_LOOP_AVAILABLE = True
except ImportError:
    LearningLoop = None  # type: ignore[misc,assignment]
    LEARNING_LOOP_AVAILABLE = False

# Singleton instances
_healing_core: Optional[SelfHealingCore] = None
_telemetry: Optional[SimpleTelemetry] = None
_pattern_store: Optional[PatternStore] = None
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


def get_unified_patterns() -> PatternStore:
    """Get the global pattern store instance."""
    global _pattern_store
    if _pattern_store is None:
        _pattern_store = PatternStore()
    return _pattern_store


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
        # Backward compatibility attributes
        self.pattern_store = get_unified_patterns() if PERSIST_PATTERNS else None

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
                # Note: PatternStore doesn't have update_success_rate method
                # Learning happens in self_healing.py directly now
            else:
                results.success = False
                results.details.append(
                    f"Failed to fix: {finding.snippet} in {finding.file}"
                )

        # Log results
        self.telemetry.log("core.healing_complete", results.model_dump())

        return results

    def detect_errors(self, path: str) -> List[Finding]:
        """
        Detect errors in file or log content (backward compatibility).

        Args:
            path: File path or log content to analyze

        Returns:
            List of Finding objects with detected errors
        """
        if self.healing:
            return self.healing.detect_errors(path)
        return []

    def fix_errors(self, errors: List[Finding]) -> List[Patch]:
        """
        Generate fixes for detected errors (backward compatibility).

        Args:
            errors: List of Finding objects to fix

        Returns:
            List of Patch objects with fixes
        """
        if self.healing:
            patches = []
            for error in errors:
                patch = self.healing.generate_fix(error)
                if patch:
                    patches.append(patch)
            return patches
        return []

    def verify_fix(self) -> bool:
        """
        Verify that fixes work correctly (backward compatibility).

        Returns:
            True if tests pass after fixes
        """
        if self.healing:
            return self.healing.verify()
        return True

    def get_health_status(self) -> HealthStatus:
        """
        Get overall system health status.

        Returns:
            Dictionary with health metrics and status
        """
        metrics = self.telemetry.get_metrics()
        # Get basic pattern stats from PatternStore
        pattern_stats = {}
        if self.patterns:
            top_patterns = self.patterns.get_top_patterns(limit=10)
            pattern_stats = {"total_patterns": len(top_patterns)}

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

    def emit_event(self, event: str, data: Optional[Dict[str, JSONValue]] = None, level: str = "info"):
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
        # Pattern learning has been migrated to the unified pattern intelligence system
        # This method provides backward compatibility while delegating to the new system

        if not self.pattern_store:
            raise NotImplementedError(
                "Pattern learning requires PatternStore initialization. "
                "Migration: Use pattern_intelligence.pattern_store.PatternStore directly "
                "or enable PERSIST_PATTERNS environment variable."
            )

        # Create a CodingPattern from the error fix
        from pattern_intelligence.coding_pattern import (
            ProblemContext, SolutionApproach, EffectivenessMetric, PatternMetadata
        )
        from datetime import datetime
        import uuid

        pattern = CodingPattern(
            context=ProblemContext(
                description=f"Fix for {error_type} error",
                domain="error_fix",
                constraints=[],
                symptoms=[error_type],
                scale=None,
                urgency="medium"
            ),
            solution=SolutionApproach(
                approach=f"Replace problematic code with fixed version",
                implementation=fixed,
                tools=["Edit"],
                reasoning=f"Automated fix for {error_type}",
                code_examples=[{"before": original, "after": fixed}],
                dependencies=[],
                alternatives=[]
            ),
            outcome=EffectivenessMetric(
                success_rate=1.0 if success else 0.0,
                performance_impact=None,
                maintainability_impact=None,
                user_impact=None,
                technical_debt=None,
                adoption_rate=1,
                longevity=None,
                confidence=0.8 if success else 0.2
            ),
            metadata=PatternMetadata(
                pattern_id=f"fix_{error_type}_{uuid.uuid4().hex[:8]}",
                discovered_timestamp=datetime.now().isoformat(),
                source="unified_core.learn_pattern",
                discoverer="UnifiedCore",
                last_applied=datetime.now().isoformat() if success else None,
                application_count=1 if success else 0,
                validation_status="validated" if success else "failed",
                tags=["error_fix", error_type.lower()],
                related_patterns=[]
            )
        )

        # Store the pattern
        self.pattern_store.store_pattern(pattern)

        self.emit_event("pattern_learned", {
            "pattern_id": pattern.metadata.pattern_id,
            "error_type": error_type,
            "success": success
        })

    def find_patterns(self, query: Optional[str] = None, pattern_type: Optional[str] = None) -> List[CodingPattern]:
        """
        Find patterns matching criteria.

        Args:
            query: Search query
            pattern_type: Filter by type

        Returns:
            List of matching patterns
        """
        if self.patterns:
            if query:
                search_results = self.patterns.find_patterns(search_query=query, max_results=10)
                return [result.pattern for result in search_results]
            else:
                return self.patterns.get_top_patterns(limit=10)
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

    def get_learning_metrics(self) -> Dict[str, JSONValue]:
        """
        Get learning loop operational metrics.

        Returns:
            Dict[str, JSONValue]: learning loop metrics when available, otherwise {}
        """
        if self.learning_loop:
            # Preserve backward-compatible raw metrics dict expected by tests/consumers
            metrics = self.learning_loop.get_metrics()
            return metrics if isinstance(metrics, dict) else {}
        return {}

    def learn_from_operation_result(self, operation_id: str, success: bool,
                                  task_description: Optional[str] = None,
                                  tool_calls: Optional[List[ToolCall]] = None,
                                  initial_error: Optional[str] = None,
                                  final_state: Optional[Union[str, Dict[str, JSONValue]]] = None,
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

        # Convert types to match Operation model expectations
        initial_error_dict: Optional[Dict[str, JSONValue]] = None
        if initial_error is not None:
            initial_error_dict = {"error": initial_error}

        tool_calls_dict: List[Dict[str, JSONValue]] = []
        if tool_calls:
            for tool_call in tool_calls:
                # Convert ToolCall to Dict[str, JSONValue]
                if hasattr(tool_call, 'model_dump'):
                    tool_calls_dict.append(tool_call.model_dump())
                else:
                    tool_calls_dict.append({
                        "name": getattr(tool_call, "name", "unknown"),
                        "args": getattr(tool_call, "args", {})
                    })

        final_state_dict: Dict[str, JSONValue] = {}
        if isinstance(final_state, dict):
            final_state_dict = final_state
        elif isinstance(final_state, str):
            final_state_dict = {"state": final_state}

        operation = Operation(
            id=operation_id,
            task_description=task_description,
            initial_error=initial_error_dict,
            tool_calls=tool_calls_dict,
            final_state=final_state_dict,
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
    "PatternStore",

    # Data classes
    "Finding",
    "Patch",
    "CodingPattern",

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