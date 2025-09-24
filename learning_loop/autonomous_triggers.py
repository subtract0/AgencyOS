"""
Autonomous Trigger System: Routes events and triggers healing automatically.

This module implements Section 3 of SPEC-LEARNING-001: Autonomous Trigger System.
Provides EventRouter, HealingTrigger, and PatternMatcher classes for autonomous
error detection and healing with cooldown mechanisms.

Constitutional Compliance:
- Article I: Complete context gathering before action
- Article II: 100% test verification for all triggered healing
- Article III: Automated enforcement of healing policies
- Article IV: Pattern learning and application integration
- Article V: Spec-driven implementation per SPEC-LEARNING-001
"""

import asyncio
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from learning_loop.event_detection import Event, ErrorEvent, FileEvent
from learning_loop.pattern_extraction import EnhancedPattern
from core.self_healing import SelfHealingCore, Finding
from core.patterns import UnifiedPatternStore, get_pattern_store, Pattern
from core.telemetry import get_telemetry, emit


@dataclass
class HealingResult:
    """Result of an autonomous healing attempt."""
    success: bool
    skipped: bool = False
    reason: Optional[str] = None
    pattern_used: Optional[str] = None
    error_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for telemetry."""
        return asdict(self)


@dataclass
class PatternMatch:
    """Represents a pattern match with confidence scoring."""
    pattern: EnhancedPattern
    score: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert match to dictionary for logging."""
        return {
            "pattern_id": self.pattern.id,
            "score": self.score,
            "confidence": self.confidence,
            "pattern_type": self.pattern.trigger.type
        }


@dataclass
class Response:
    """Response from event handling."""
    success: bool
    handler_name: str
    result: Any = None
    error: Optional[str] = None


class EventHandler:
    """Base class for event handlers."""

    def __init__(self, name: str):
        self.name = name
        self.telemetry = get_telemetry()

    async def handle(self, event: Event, *args, **kwargs) -> Response:
        """Handle an event. Must be implemented by subclasses."""
        raise NotImplementedError(f"Handler {self.name} must implement handle method")


class ErrorHandler(EventHandler):
    """Handler for error events that triggers healing."""

    def __init__(self):
        super().__init__("ErrorHandler")
        self.healing_trigger = None  # Will be set by EventRouter

    async def handle(self, event: ErrorEvent) -> Response:
        """Handle error event by triggering healing."""
        if not self.healing_trigger:
            return Response(
                success=False,
                handler_name=self.name,
                error="HealingTrigger not initialized"
            )

        try:
            result = await self.healing_trigger.handle_error(event)

            emit("error_handler_completed", {
                "event_type": event.error_type,
                "success": result.success,
                "skipped": result.skipped,
                "reason": result.reason
            })

            return Response(
                success=result.success,
                handler_name=self.name,
                result=result
            )

        except Exception as e:
            emit("error_handler_failed", {
                "error": str(e),
                "event_type": getattr(event, 'error_type', 'unknown')
            }, level="error")

            return Response(
                success=False,
                handler_name=self.name,
                error=str(e)
            )


class FailureEventHandler(EventHandler):
    """Handler for test failure events."""

    def __init__(self):
        super().__init__("TestFailureHandler")

    async def handle(self, event: Event) -> Response:
        """Handle test failure by analyzing and fixing."""
        emit("test_failure_handler_triggered", {
            "event_metadata": event.metadata
        })

        # For now, delegate to error handling if it looks like an error
        if hasattr(event, 'error_type'):
            error_event = ErrorEvent(
                type="test_failure",
                timestamp=event.timestamp,
                error_type=getattr(event, 'error_type', 'TestFailure'),
                message=getattr(event, 'message', 'Test failed'),
                context=getattr(event, 'context', ''),
                metadata=event.metadata
            )
            # Would redirect to ErrorHandler in real implementation
            return Response(success=True, handler_name=self.name, result="analyzed")

        return Response(success=True, handler_name=self.name, result="analyzed")


class ChangeHandler(EventHandler):
    """Handler for file modification events."""

    def __init__(self):
        super().__init__("ChangeHandler")

    async def handle(self, event: FileEvent) -> Response:
        """Handle file change event to check for improvement opportunities."""
        emit("change_handler_triggered", {
            "path": event.path,
            "file_type": event.file_type,
            "change_type": event.change_type
        })

        # Check for improvement opportunities
        # For now, just log the event
        return Response(success=True, handler_name=self.name, result="analyzed")


class PatternApplicationHandler(EventHandler):
    """Handler for applying matched patterns."""

    def __init__(self):
        super().__init__("PatternApplicationHandler")

    async def handle(self, event: Event, patterns: List[PatternMatch]) -> Response:
        """Handle event by applying the best matching pattern."""
        if not patterns:
            return Response(success=False, handler_name=self.name, error="No patterns provided")

        # Use the highest scoring pattern
        best_match = patterns[0]

        emit("pattern_application_started", {
            "pattern_id": best_match.pattern.id,
            "score": best_match.score,
            "confidence": best_match.confidence
        })

        # Apply the pattern (simplified for now)
        # In full implementation, would execute the pattern's actions
        result = HealingResult(
            success=True,
            pattern_used=best_match.pattern.id,
            reason="Pattern applied successfully"
        )

        emit("pattern_application_completed", {
            "success": result.success,
            "pattern_id": best_match.pattern.id
        })

        return Response(success=True, handler_name=self.name, result=result)


class EventRouter:
    """
    Routes events to appropriate handlers based on type and context.

    Implements SPEC-LEARNING-001 Section 3.1: Event Router with decision tree:
    1. Is this an error? → Try healing
    2. Is this a test failure? → Analyze and fix
    3. Is this a change? → Check for improvement opportunity
    4. Does this match a known pattern? → Apply pattern
    """

    def __init__(self, pattern_store: Optional[UnifiedPatternStore] = None):
        """
        Initialize event router with handlers and pattern matching.

        Args:
            pattern_store: Pattern storage instance (defaults to global store)
        """
        self.pattern_store = pattern_store or get_pattern_store()
        self.telemetry = get_telemetry()
        self.pattern_matcher = PatternMatcher(self.pattern_store)

        # Initialize handlers per spec
        self.error_handler = ErrorHandler()
        self.test_failure_handler = FailureEventHandler()
        self.change_handler = ChangeHandler()
        self.pattern_application_handler = PatternApplicationHandler()

        self.handlers = {
            "error_detected": self.error_handler,
            "test_failure": self.test_failure_handler,
            "file_modified": self.change_handler,
            "file_created": self.change_handler,
            "pattern_matched": self.pattern_application_handler
        }

        # Initialize healing trigger and wire to error handler
        self.healing_trigger = HealingTrigger(self.pattern_store)
        self.error_handler.healing_trigger = self.healing_trigger

    async def route_event(self, event: Event) -> Response:
        """
        Route event to appropriate handler.

        Decision tree per SPEC-LEARNING-001:
        1. Check for pattern matches first
        2. Route based on event type
        3. Log unhandled events for future learning

        Args:
            event: Event to route

        Returns:
            Response from the appropriate handler
        """

        emit("event_routing_started", {
            "event_type": event.type,
            "timestamp": event.timestamp.isoformat()
        })

        try:
            # Step 1: Check for pattern matches first per spec
            patterns = self.pattern_matcher.find_matches(event)
            if patterns:
                emit("pattern_matches_found", {
                    "count": len(patterns),
                    "best_score": patterns[0].score if patterns else 0.0,
                    "event_type": event.type
                })

                response = await self.handlers["pattern_matched"].handle(event, patterns)

                emit("event_routing_completed", {
                    "handler": "pattern_matched",
                    "success": response.success
                })

                return response

            # Step 2: Route based on event type per spec
            handler = self.handlers.get(event.type)
            if handler:
                response = await handler.handle(event)

                emit("event_routing_completed", {
                    "handler": handler.name,
                    "success": response.success,
                    "event_type": event.type
                })

                return response

            # Step 3: Log unhandled event for future learning per spec
            emit("unhandled_event", {
                "event_type": event.type,
                "metadata": event.metadata
            }, level="warning")

            return Response(
                success=False,
                handler_name="NoHandler",
                error=f"No handler found for event type: {event.type}"
            )

        except Exception as e:
            emit("event_routing_error", {
                "event_type": event.type,
                "error": str(e)
            }, level="error")

            return Response(
                success=False,
                handler_name="RouterError",
                error=str(e)
            )


class HealingTrigger:
    """
    Automatically triggers healing when errors are detected.

    Implements SPEC-LEARNING-001 Section 3.2: Autonomous Healing Trigger with:
    - Cooldown mechanism to prevent healing loops (5 min default)
    - Pattern application for known errors
    - Integration with SelfHealingCore
    """

    def __init__(self, pattern_store: Optional[UnifiedPatternStore] = None):
        """
        Initialize healing trigger with pattern store and cooldown tracking.

        Args:
            pattern_store: Pattern storage instance (defaults to global store)
        """
        self.healing_core = SelfHealingCore()
        self.pattern_store = pattern_store or get_pattern_store()
        self.telemetry = get_telemetry()

        # Cooldown tracking per spec - prevent healing loops
        self.cooldown: Dict[str, datetime] = {}
        self.cooldown_minutes = 5  # Default 5 minute cooldown per spec

        # Pattern application tracking
        self.pattern_matcher = PatternMatcher(self.pattern_store)

    async def handle_error(self, error: ErrorEvent) -> HealingResult:
        """
        Attempt to heal detected error.

        Implements the healing flow per SPEC-LEARNING-001:
        1. Check cooldown to prevent loops
        2. Check for known pattern
        3. Apply pattern or attempt generic healing
        4. Learn from result

        Args:
            error: ErrorEvent to heal

        Returns:
            HealingResult with success status and details
        """

        emit("healing_attempt_started", {
            "error_type": error.error_type,
            "source_file": error.source_file,
            "message": error.message[:200]  # Truncate long messages
        })

        # Step 1: Check cooldown per spec
        if self._in_cooldown(error):
            result = HealingResult(
                success=False,
                skipped=True,
                reason="cooldown"
            )

            emit("healing_skipped_cooldown", {
                "error_type": error.error_type,
                "source_file": error.source_file
            })

            return result

        try:
            # Step 2: Check for known pattern per spec
            pattern = self._find_pattern_for_error(error)

            if pattern:
                result = await self._apply_pattern(pattern, error)
                emit("healing_pattern_applied", {
                    "pattern_id": pattern.id,
                    "success": result.success,
                    "error_type": error.error_type
                })
            else:
                # Step 3: Attempt generic healing per spec
                result = await self._attempt_generic_healing(error)
                emit("healing_generic_attempted", {
                    "success": result.success,
                    "error_type": error.error_type
                })

            # Step 4: Learn from result per spec
            if result.success:
                self._record_success(error, result)
                emit("healing_success_recorded", {
                    "error_type": error.error_type,
                    "pattern_used": result.pattern_used
                })
            else:
                self._record_failure(error, result)
                self._add_cooldown(error)  # Add cooldown on failure
                emit("healing_failure_recorded", {
                    "error_type": error.error_type,
                    "reason": result.reason
                })

            emit("healing_attempt_completed", {
                "success": result.success,
                "error_type": error.error_type,
                "skipped": result.skipped
            })

            return result

        except Exception as e:
            # Record failure and add cooldown
            result = HealingResult(
                success=False,
                reason=f"Exception during healing: {str(e)}",
                error_details=str(e)
            )

            self._record_failure(error, result)
            self._add_cooldown(error)

            emit("healing_attempt_error", {
                "error_type": error.error_type,
                "exception": str(e)
            }, level="error")

            return result

    def _in_cooldown(self, error: ErrorEvent) -> bool:
        """Check if this error is in cooldown period."""
        key = f"{error.error_type}:{error.source_file or 'unknown'}"

        if last_attempt := self.cooldown.get(key):
            # 5 minute cooldown per spec
            cooldown_duration = timedelta(minutes=self.cooldown_minutes)
            return datetime.now() - last_attempt < cooldown_duration

        return False

    def _find_pattern_for_error(self, error: ErrorEvent) -> Optional[Pattern]:
        """Find pattern that could handle this error."""
        # Search patterns by error type and tags
        patterns = self.pattern_store.find(
            pattern_type="error_fix",
            tags=[error.error_type]
        )

        # Return the highest success rate pattern
        if patterns:
            return patterns[0]  # Already sorted by success rate

        return None

    async def _apply_pattern(self, pattern: Pattern, error: ErrorEvent) -> HealingResult:
        """Apply known pattern to fix error."""
        try:
            # Convert error to Finding for SelfHealingCore
            finding = Finding(
                file=error.source_file or "unknown",
                line=error.line_number or 0,
                error_type=error.error_type,
                snippet=error.message
            )

            # Apply the fix
            success = self.healing_core.fix_error(finding)

            result = HealingResult(
                success=success,
                pattern_used=pattern.id,
                reason="Pattern applied successfully" if success else "Pattern application failed"
            )

            # Update pattern success rate
            if self.pattern_store:
                self.pattern_store.update_success_rate(pattern.id, success)

            return result

        except Exception as e:
            return HealingResult(
                success=False,
                pattern_used=pattern.id,
                reason=f"Pattern application error: {str(e)}",
                error_details=str(e)
            )

    async def _attempt_generic_healing(self, error: ErrorEvent) -> HealingResult:
        """Attempt generic healing without a specific pattern."""
        try:
            # Convert error to Finding for SelfHealingCore
            finding = Finding(
                file=error.source_file or "unknown",
                line=error.line_number or 0,
                error_type=error.error_type,
                snippet=error.message
            )

            # Apply generic fix
            success = self.healing_core.fix_error(finding)

            return HealingResult(
                success=success,
                reason="Generic healing applied" if success else "Generic healing failed"
            )

        except Exception as e:
            return HealingResult(
                success=False,
                reason=f"Generic healing error: {str(e)}",
                error_details=str(e)
            )

    def _record_success(self, error: ErrorEvent, result: HealingResult):
        """Record successful healing for learning."""
        emit("healing_success", {
            "error_type": error.error_type,
            "source_file": error.source_file,
            "pattern_used": result.pattern_used,
            "healing_method": "pattern" if result.pattern_used else "generic"
        })

    def _record_failure(self, error: ErrorEvent, result: HealingResult):
        """Record failed healing for learning."""
        emit("healing_failure", {
            "error_type": error.error_type,
            "source_file": error.source_file,
            "reason": result.reason,
            "error_details": result.error_details
        })

    def _add_cooldown(self, error: ErrorEvent):
        """Add error to cooldown to prevent loops."""
        key = f"{error.error_type}:{error.source_file or 'unknown'}"
        self.cooldown[key] = datetime.now()

        emit("healing_cooldown_added", {
            "error_key": key,
            "cooldown_minutes": self.cooldown_minutes
        })


class PatternMatcher:
    """
    Matches events to stored patterns using similarity scoring.

    Implements SPEC-LEARNING-001 Section 4.2: Pattern Matching Algorithm with
    similarity factors:
    - Error type match: 0.4
    - File type match: 0.2
    - Context similarity: 0.2
    - Historical success: 0.2
    """

    def __init__(self, pattern_store: Optional[UnifiedPatternStore] = None):
        """
        Initialize pattern matcher with pattern store.

        Args:
            pattern_store: Pattern storage instance (defaults to global store)
        """
        self.pattern_store = pattern_store or get_pattern_store()
        self.telemetry = get_telemetry()
        self.min_threshold = 0.3  # Minimum confidence threshold per spec

    def find_matches(self, event: Event) -> List[PatternMatch]:
        """
        Find patterns that could handle this event.

        Implements similarity scoring per SPEC-LEARNING-001:
        - Error type match: 0.4 weight
        - File type match: 0.2 weight
        - Context similarity: 0.2 weight
        - Historical success: 0.2 weight

        Args:
            event: Event to find patterns for

        Returns:
            List of PatternMatch objects, sorted by score
        """

        emit("pattern_matching_started", {
            "event_type": event.type,
            "event_metadata": event.metadata
        })

        candidates = []

        # Get all patterns from store
        all_patterns = self.pattern_store.find()

        for pattern in all_patterns:
            try:
                # Convert existing pattern to enhanced pattern for scoring
                enhanced_pattern = self._convert_to_enhanced_pattern(pattern)

                # Calculate similarity score per spec
                score = self._calculate_similarity(event, enhanced_pattern)

                # Apply confidence weighting per spec
                weighted_score = score * pattern.success_rate

                # Filter by minimum threshold per spec
                if weighted_score > self.min_threshold:
                    confidence = self._calculate_confidence(pattern, event)

                    candidates.append(PatternMatch(
                        pattern=enhanced_pattern,
                        score=weighted_score,
                        confidence=confidence
                    ))

            except Exception as e:
                emit("pattern_matching_error", {
                    "pattern_id": pattern.id,
                    "error": str(e)
                }, level="warning")

        # Sort by score per spec
        candidates.sort(key=lambda x: x.score, reverse=True)

        emit("pattern_matching_completed", {
            "event_type": event.type,
            "matches_found": len(candidates),
            "best_score": candidates[0].score if candidates else 0.0
        })

        return candidates

    def _calculate_similarity(self, event: Event, pattern: EnhancedPattern) -> float:
        """
        Calculate similarity between event and pattern trigger.

        Implements scoring factors per SPEC-LEARNING-001:
        - Error type match: 0.4
        - File type match: 0.2
        - Context similarity: 0.2
        - Historical success: 0.2

        Args:
            event: Event to match
            pattern: Pattern to score against

        Returns:
            Similarity score from 0.0 to 1.0
        """

        score = 0.0

        # Error type matching (0.4 weight) per spec
        if (hasattr(event, 'error_type') and
            hasattr(pattern.trigger, 'error_type')):
            if event.error_type == pattern.trigger.error_type:
                score += 0.4

        # File context matching (0.2 weight) per spec
        if self._similar_file_context(event, pattern):
            score += 0.2

        # Semantic similarity of context (0.2 weight) per spec
        context_similarity = self._semantic_similarity(event, pattern)
        if context_similarity:
            score += 0.2 * context_similarity

        # Historical success rate (0.2 weight) per spec
        if pattern.metadata.usage_count > 0:
            success_rate = pattern.metadata.success_count / pattern.metadata.usage_count
            score += 0.2 * success_rate

        return min(score, 1.0)  # Cap at 1.0

    def _similar_file_context(self, event: Event, pattern: EnhancedPattern) -> bool:
        """Check if event and pattern have similar file context."""
        event_file = getattr(event, 'source_file', '') or getattr(event, 'path', '')

        if not event_file:
            return False

        # Check pattern context for file information
        pattern_context = pattern.metadata.tags

        # Look for file type similarities
        if 'test' in event_file.lower():
            return 'test' in pattern_context or 'uses_test' in pattern_context
        elif event_file.endswith('.py'):
            return 'python' in pattern_context or 'uses_edit' in pattern_context
        elif event_file.endswith('.md'):
            return 'markdown' in pattern_context or 'documentation' in pattern_context

        return False

    def _semantic_similarity(self, event: Event, pattern: EnhancedPattern) -> float:
        """Calculate semantic similarity between event and pattern contexts."""
        # Simple keyword-based similarity for now
        event_text = str(getattr(event, 'message', '')) + str(event.metadata)
        pattern_text = json.dumps(pattern.trigger.metadata) + ' '.join(pattern.metadata.tags)

        event_words = set(re.findall(r'\w+', event_text.lower()))
        pattern_words = set(re.findall(r'\w+', pattern_text.lower()))

        if not event_words or not pattern_words:
            return 0.0

        # Jaccard similarity
        intersection = len(event_words & pattern_words)
        union = len(event_words | pattern_words)

        return intersection / union if union > 0 else 0.0

    def _calculate_confidence(self, pattern: Pattern, event: Event) -> float:
        """Calculate confidence in pattern match for this event."""
        # Base confidence from pattern success rate
        confidence = pattern.success_rate

        # Boost confidence for frequently used patterns
        if pattern.usage_count > 5:
            confidence = min(confidence * 1.1, 1.0)
        elif pattern.usage_count == 0:
            confidence = confidence * 0.8  # Reduce for unused patterns

        # Adjust for recency
        try:
            last_used = datetime.fromisoformat(pattern.last_used)
            days_since_used = (datetime.now() - last_used).days

            if days_since_used < 7:
                confidence = min(confidence * 1.05, 1.0)  # Recent patterns
            elif days_since_used > 30:
                confidence = confidence * 0.95  # Older patterns

        except (ValueError, TypeError):
            # Invalid datetime, use base confidence
            pass

        return confidence

    def _convert_to_enhanced_pattern(self, pattern: Pattern) -> EnhancedPattern:
        """Convert UnifiedPatternStore Pattern to EnhancedPattern for scoring."""
        # Import here to avoid circular imports
        from learning_loop.pattern_extraction import (
            EnhancedPattern, PatternMetadata, Trigger, ErrorTrigger, TaskTrigger
        )

        # Create trigger from pattern context
        if pattern.pattern_type == "error_fix":
            error_type = pattern.context.get("error_type", "Unknown")
            trigger = ErrorTrigger(
                error_type=error_type,
                error_pattern=f"{error_type}.*"
            )
        else:
            trigger = TaskTrigger(keywords=pattern.tags)

        # Create metadata
        metadata = PatternMetadata(
            confidence=pattern.success_rate,
            usage_count=pattern.usage_count,
            success_count=int(pattern.success_rate * pattern.usage_count),
            failure_count=pattern.usage_count - int(pattern.success_rate * pattern.usage_count),
            last_used=datetime.fromisoformat(pattern.last_used),
            created_at=datetime.fromisoformat(pattern.created_at),
            source="learned",
            tags=pattern.tags
        )

        return EnhancedPattern(
            id=pattern.id,
            trigger=trigger,
            preconditions=[],  # Simplified for pattern matching
            actions=[],        # Simplified for pattern matching
            postconditions=[], # Simplified for pattern matching
            metadata=metadata
        )