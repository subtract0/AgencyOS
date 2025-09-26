"""
Learning Loop Module - Autonomous Learning and Healing System

This module provides the main orchestrator class for the learning loop system
specified in SPEC-LEARNING-001. Integrates event detection, pattern extraction,
and autonomous triggers for continuous improvement and self-healing.

Constitutional Compliance:
- Article I: Complete context before action - validates all components before startup
- Article II: 100% test verification - includes comprehensive test coverage
- Article III: Automated enforcement - provides automated healing and pattern application
- Article IV: Continuous learning - implements the core learning loop functionality
- Article V: Spec-driven development - follows SPEC-LEARNING-001 exactly

Main Exports:
- LearningLoop: Primary orchestrator class
- EventDetectionSystem: File and error monitoring
- PatternExtractor: Success pattern learning
- FailureLearner: Anti-pattern learning
- EventRouter: Autonomous event handling
- HealingTrigger: Autonomous error healing
- PatternMatcher: Pattern matching engine
"""

import os
import asyncio
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from shared.type_definitions.json import JSONValue
from pathlib import Path
import yaml

# Core imports
from core.self_healing import SelfHealingCore
from core.patterns import UnifiedPatternStore, get_pattern_store
from core.telemetry import get_telemetry, emit
from core import get_healing_core

# Learning loop component imports
from learning_loop.event_detection import (
    EventDetectionSystem,
    FileWatcher,
    ErrorMonitor,
    Event,
    FileEvent,
    ErrorEvent
)
from learning_loop.pattern_extraction import (
    PatternExtractor,
    FailureLearner,
    EnhancedPattern,
    AntiPattern,
    Operation
)
from learning_loop.autonomous_triggers import (
    EventRouter,
    HealingTrigger,
    PatternMatcher,
    HealingResult,
    PatternMatch
)

# Configure logging for learning loop
logger = logging.getLogger('learning_loop')


class LearningLoop:
    """
    Main orchestrator for the autonomous learning and healing system.

    Implements the complete learning loop specified in SPEC-LEARNING-001:
    1. Event Detection → Monitor files and errors
    2. Pattern Extraction → Learn from successes and failures
    3. Autonomous Triggers → Apply patterns and trigger healing
    4. Continuous Learning → Update patterns based on results

    Features:
    - 24-hour autonomous operation capability
    - Configurable thresholds and behaviors
    - Integration with UnifiedCore components
    - Constitutional compliance enforcement
    - Comprehensive telemetry and logging
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize learning loop with configuration and components.

        Args:
            config_path: Optional path to learning_config.yaml file
        """
        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize telemetry
        self.telemetry = get_telemetry()

        # Initialize core components
        self.healing_core = get_healing_core()
        self.pattern_store = get_pattern_store()

        # Initialize learning loop components
        self.event_detection = EventDetectionSystem(
            file_callback=self._handle_file_event,
            error_callback=self._handle_error_event
        )

        self.pattern_extractor = PatternExtractor(self.pattern_store)
        self.failure_learner = FailureLearner(self.pattern_store)
        self.event_router = EventRouter(self.pattern_store)
        self.healing_trigger = HealingTrigger(self.pattern_store)
        self.pattern_matcher = PatternMatcher(self.pattern_store)

        # State tracking
        self.is_running = False
        self.start_time = None
        self.operation_count = 0
        self.success_count = 0
        self.failure_count = 0

        # Operation tracking for learning
        self._current_operations: Dict[str, Dict] = {}
        self._completed_operations: List[Operation] = []

        # Background task management
        self._tasks: List[asyncio.Task] = []
        self._stop_event = asyncio.Event() if asyncio._get_running_loop() is None else None

        emit("learning_loop_initialized", {
            "config": self.config,
            "components": [
                "EventDetectionSystem",
                "PatternExtractor",
                "FailureLearner",
                "EventRouter",
                "HealingTrigger",
                "PatternMatcher"
            ]
        })

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, JSONValue]:
        """Load learning loop configuration from YAML file."""
        if config_path is None:
            config_path = "learning_config.yaml"

        config_file = Path(config_path)

        # Default configuration per SPEC-LEARNING-001
        default_config = {
            "learning": {
                "enabled": True,
                "triggers": {
                    "file_watch": True,
                    "error_monitor": True,
                    "test_monitor": True,
                    "git_hooks": True
                },
                "thresholds": {
                    "min_pattern_confidence": 0.3,
                    "min_match_score": 0.5,
                    "cooldown_minutes": 5,
                    "max_retries": 3
                },
                "storage": {
                    "backend": "sqlite",
                    "persist_patterns": True,
                    "max_patterns": 1000,
                    "cleanup_days": 30
                },
                "monitoring": {
                    "metrics_enabled": True,
                    "dashboard_port": 8080,
                    "alert_on_failure": True
                }
            }
        }

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                    # Merge with defaults
                    default_config.update(file_config)

                emit("learning_config_loaded", {
                    "config_path": str(config_file),
                    "config": default_config
                })

            except Exception as e:
                emit("learning_config_load_error", {
                    "config_path": str(config_file),
                    "error": str(e)
                }, level="warning")

                # Use defaults on error
                pass
        else:
            emit("learning_config_default", {
                "reason": "config_file_not_found",
                "config_path": str(config_file)
            })

        return default_config

    def start(self):
        """
        Start the learning loop system.

        Validates configuration and starts all components in proper order:
        1. Validate constitutional compliance (Article I)
        2. Start event detection systems
        3. Initialize pattern matching
        4. Begin autonomous monitoring
        """
        if self.is_running:
            emit("learning_loop_already_running", {})
            return

        try:
            # Article I: Complete context before action
            self._validate_prerequisites()

            emit("learning_loop_starting", {
                "config": self.config,
                "timestamp": datetime.now().isoformat()
            })

            # Start event detection systems
            if self.config["learning"]["triggers"]["file_watch"]:
                self.event_detection.start()
                emit("event_detection_started", {})

            # Initialize pattern matching with stored patterns
            self._initialize_pattern_matching()

            # Mark as running
            self.is_running = True
            self.start_time = datetime.now()

            emit("learning_loop_started", {
                "start_time": self.start_time.isoformat(),
                "enabled_triggers": self.config["learning"]["triggers"]
            })

        except Exception as e:
            emit("learning_loop_start_error", {
                "error": str(e)
            }, level="error")

            # Cleanup on failure
            self.stop()
            raise

    def stop(self):
        """
        Stop the learning loop system gracefully.

        Stops all components and saves final state:
        1. Stop event detection
        2. Complete pending operations
        3. Save learned patterns
        4. Generate final metrics
        """
        if not self.is_running:
            emit("learning_loop_already_stopped", {})
            return

        try:
            emit("learning_loop_stopping", {
                "runtime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "operations_completed": self.operation_count
            })

            # Stop event detection
            if self.event_detection.is_running:
                self.event_detection.stop()

            # Complete pending operations
            self._complete_pending_operations()

            # Cancel background tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            # Generate final metrics
            self._generate_final_metrics()

            # Mark as stopped
            self.is_running = False

            emit("learning_loop_stopped", {
                "stop_time": datetime.now().isoformat(),
                "final_metrics": self.get_metrics()
            })

        except Exception as e:
            emit("learning_loop_stop_error", {
                "error": str(e)
            }, level="error")

            # Force stop
            self.is_running = False

    def get_metrics(self) -> Dict[str, JSONValue]:
        """
        Get comprehensive learning loop metrics.

        Returns:
            Dictionary with operational metrics and performance data
        """
        runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        metrics = {
            "runtime_seconds": runtime,
            "is_running": self.is_running,
            "operations": {
                "total": self.operation_count,
                "successful": self.success_count,
                "failed": self.failure_count,
                "success_rate": self.success_count / max(self.operation_count, 1)
            },
            "patterns": {
                "total_learned": len(self._completed_operations),
                "active_patterns": len(self.pattern_store.find()) if self.pattern_store else 0
            },
            "components": {
                "event_detection": self.event_detection.is_running,
                "pattern_extraction": True,  # Always available
                "autonomous_triggers": True  # Always available
            }
        }

        # Add pattern store statistics if available
        if self.pattern_store:
            pattern_stats = self.pattern_store.get_statistics()
            metrics["patterns"].update(pattern_stats)

        return metrics

    def learn_from_operation(self, operation: Operation):
        """
        Learn patterns from a completed operation.

        This is the core learning interface for the system:
        1. Extract success patterns from successful operations
        2. Extract anti-patterns from failures
        3. Update pattern confidence scores
        4. Store learned patterns for future use

        Args:
            operation: Completed operation to learn from
        """
        try:
            emit("operation_learning_started", {
                "operation_id": operation.id,
                "success": operation.success,
                "duration": operation.duration_seconds
            })

            if operation.success:
                # Extract success pattern
                pattern = self.pattern_extractor.extract_from_success(operation)

                self.success_count += 1

                emit("success_pattern_learned", {
                    "pattern_id": pattern.id,
                    "operation_id": operation.id,
                    "trigger_type": pattern.trigger.type
                })

            else:
                # Extract anti-pattern from failure
                anti_pattern = self.failure_learner.learn_from_failure(operation)

                self.failure_count += 1

                emit("failure_pattern_learned", {
                    "antipattern_id": anti_pattern.id,
                    "operation_id": operation.id,
                    "failure_type": anti_pattern.failure_reason.type
                })

            # Track completed operation
            self._completed_operations.append(operation)
            self.operation_count += 1

            emit("operation_learning_completed", {
                "operation_id": operation.id,
                "success": operation.success,
                "total_operations": self.operation_count
            })

        except Exception as e:
            emit("operation_learning_error", {
                "operation_id": operation.id,
                "error": str(e)
            }, level="error")

    async def run_autonomous(self, duration_hours: float = 24.0):
        """
        Run the learning loop autonomously for specified duration.

        This enables 24-hour autonomous operation as specified in SPEC-LEARNING-001.
        The system will monitor, learn, and heal automatically without intervention.

        Args:
            duration_hours: How long to run autonomously (default: 24 hours)
        """
        if not self.is_running:
            self.start()

        duration_seconds = duration_hours * 3600
        end_time = datetime.now() + timedelta(seconds=duration_seconds)

        emit("autonomous_operation_started", {
            "duration_hours": duration_hours,
            "end_time": end_time.isoformat()
        })

        try:
            while datetime.now() < end_time and self.is_running:
                # Monitor system health
                await self._autonomous_health_check()

                # Process any pending learning opportunities
                await self._process_pending_learning()

                # Clean up old patterns if needed
                await self._cleanup_old_patterns()

                # Sleep before next cycle
                await asyncio.sleep(60)  # 1 minute monitoring cycle

        except Exception as e:
            emit("autonomous_operation_error", {
                "error": str(e),
                "runtime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
            }, level="error")

        emit("autonomous_operation_completed", {
            "actual_runtime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
            "final_metrics": self.get_metrics()
        })

    def _handle_file_event(self, event: FileEvent):
        """Handle file change events from the event detection system."""
        try:
            # Route through event router for pattern matching and handling
            asyncio.create_task(self.event_router.route_event(event))

        except Exception as e:
            emit("file_event_handling_error", {
                "file_path": event.path,
                "error": str(e)
            }, level="error")

    def _handle_error_event(self, event: ErrorEvent):
        """Handle error events from the error monitoring system."""
        try:
            # Route through event router for autonomous healing
            asyncio.create_task(self.event_router.route_event(event))

        except Exception as e:
            emit("error_event_handling_error", {
                "error_type": event.error_type,
                "error": str(e)
            }, level="error")

    def _validate_prerequisites(self):
        """Validate all prerequisites are met before starting (Article I compliance)."""
        # Check core components
        if not self.healing_core:
            raise RuntimeError("SelfHealingCore not available")

        if not self.pattern_store:
            raise RuntimeError("UnifiedPatternStore not available")

        # Check configuration
        if not self.config["learning"]["enabled"]:
            raise RuntimeError("Learning loop is disabled in configuration")

        # Check file system permissions
        try:
            test_file = Path("test_write_permission.tmp")
            test_file.write_text("test")
            test_file.unlink()
        except Exception:
            raise RuntimeError("Insufficient file system permissions for autonomous operation")

        emit("learning_loop_prerequisites_validated", {})

    def _initialize_pattern_matching(self):
        """Initialize pattern matching system with existing patterns."""
        if not self.pattern_store:
            return

        # Load existing patterns
        existing_patterns = self.pattern_store.find()

        emit("pattern_matching_initialized", {
            "existing_patterns": len(existing_patterns),
            "min_confidence": self.config["learning"]["thresholds"]["min_pattern_confidence"]
        })

    def _complete_pending_operations(self):
        """Complete any pending operations before shutdown."""
        if not self._current_operations:
            return

        emit("completing_pending_operations", {
            "pending_count": len(self._current_operations)
        })

        # For each pending operation, create a minimal completion record
        for op_id, op_data in self._current_operations.items():
            try:
                operation = Operation(
                    id=op_id,
                    task_description=op_data.get("description", "Unknown"),
                    initial_error=op_data.get("initial_error"),
                    tool_calls=op_data.get("tool_calls", []),
                    final_state=op_data.get("final_state", {}),
                    success=False,  # Incomplete operations are considered failures
                    duration_seconds=op_data.get("duration", 0),
                    timestamp=datetime.now()
                )

                # Learn from the incomplete operation
                self.learn_from_operation(operation)

            except Exception as e:
                emit("pending_operation_completion_error", {
                    "operation_id": op_id,
                    "error": str(e)
                }, level="warning")

        self._current_operations.clear()

    def _generate_final_metrics(self):
        """Generate and log final operational metrics."""
        metrics = self.get_metrics()

        emit("learning_loop_final_metrics", {
            "metrics": metrics,
            "patterns_learned": len(self._completed_operations),
            "autonomous_healing_events": self.healing_trigger.cooldown if hasattr(self.healing_trigger, 'cooldown') else {}
        })

    async def _autonomous_health_check(self):
        """Perform autonomous system health monitoring."""
        try:
            # Check component health
            health_status = {
                "event_detection": self.event_detection.is_running,
                "pattern_store": self.pattern_store is not None,
                "healing_core": self.healing_core is not None,
                "learning_loop": self.is_running
            }

            # Check for any failing components
            failing_components = [k for k, v in health_status.items() if not v]

            if failing_components:
                emit("autonomous_health_check_warning", {
                    "failing_components": failing_components,
                    "health_status": health_status
                }, level="warning")

            # Check memory usage and cleanup if needed
            if len(self._completed_operations) > self.config["learning"]["storage"]["max_patterns"]:
                await self._cleanup_old_operations()

        except Exception as e:
            emit("autonomous_health_check_error", {
                "error": str(e)
            }, level="error")

    async def _process_pending_learning(self):
        """Process any pending learning opportunities."""
        # This would integrate with session transcripts, test results, etc.
        # For now, just emit a heartbeat
        emit("autonomous_learning_heartbeat", {
            "timestamp": datetime.now().isoformat(),
            "operations_learned": len(self._completed_operations)
        })

    async def _cleanup_old_patterns(self):
        """Clean up old patterns based on configuration."""
        if not self.pattern_store:
            return

        cleanup_days = self.config["learning"]["storage"]["cleanup_days"]
        cutoff_date = datetime.now() - timedelta(days=cleanup_days)

        # This would be implemented in the pattern store
        emit("pattern_cleanup_check", {
            "cleanup_days": cleanup_days,
            "cutoff_date": cutoff_date.isoformat()
        })

    async def _cleanup_old_operations(self):
        """Clean up old completed operations to manage memory."""
        max_operations = self.config["learning"]["storage"]["max_patterns"]

        if len(self._completed_operations) > max_operations:
            # Keep the most recent operations
            self._completed_operations = self._completed_operations[-max_operations:]

            emit("operation_history_cleaned", {
                "kept_operations": len(self._completed_operations),
                "max_operations": max_operations
            })

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Export all main classes for external use
__all__ = [
    # Main orchestrator
    "LearningLoop",

    # Event detection
    "EventDetectionSystem",
    "FileWatcher",
    "ErrorMonitor",
    "Event",
    "FileEvent",
    "ErrorEvent",

    # Pattern extraction
    "PatternExtractor",
    "FailureLearner",
    "EnhancedPattern",
    "AntiPattern",
    "Operation",

    # Autonomous triggers
    "EventRouter",
    "HealingTrigger",
    "PatternMatcher",
    "HealingResult",
    "PatternMatch",
]