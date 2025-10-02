"""
WITNESS Agent - Trinity Protocol Perception Layer

Stateless signal intelligence agent that monitors telemetry and context streams,
detects patterns, and publishes high-confidence signals to improvement_queue.

Core Loop: LISTEN → CLASSIFY → VALIDATE → ENRICH → SELF-VERIFY → PUBLISH → PERSIST → RESET

Constitutional Compliance:
- Article I: Complete context - await full events before classification
- Article II: 100% Verification - self-verify JSON before publishing
- Article IV: Continuous learning - persist patterns to Firestore

Model: qwen2.5-coder:1.5b (local, fast, cost-free)
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from dataclasses import dataclass, asdict

from shared.pattern_detector import PatternDetector, PatternMatch
from shared.message_bus import MessageBus
from shared.persistent_store import PersistentStore


@dataclass
class Signal:
    """Output signal from WITNESS agent."""
    priority: str  # CRITICAL, HIGH, NORMAL
    source: str  # telemetry, personal_context
    pattern: str  # Pattern name
    confidence: float  # 0.7-1.0
    data: Dict[str, Any]  # Extracted metadata
    summary: str  # Max 120 chars
    timestamp: str  # ISO8601
    source_id: str  # Event ID
    correlation_id: Optional[str] = None  # Optional correlation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class WitnessAgent:
    """
    WITNESS (AUDITLEARN) agent - Perception layer of Trinity Protocol.

    Continuously monitors event streams and detects patterns using
    lightweight heuristics and local model inference.
    """

    def __init__(
        self,
        message_bus: MessageBus,
        pattern_store: PersistentStore,
        min_confidence: float = 0.7,
        telemetry_queue: str = "telemetry_stream",
        context_queue: str = "personal_context_stream",
        output_queue: str = "improvement_queue"
    ):
        """
        Initialize WITNESS agent.

        Args:
            message_bus: Message bus for pub/sub
            pattern_store: Persistent pattern storage
            min_confidence: Minimum confidence for pattern publishing
            telemetry_queue: Input queue for telemetry events
            context_queue: Input queue for user context
            output_queue: Output queue for detected patterns
        """
        self.message_bus = message_bus
        self.pattern_store = pattern_store
        self.detector = PatternDetector(min_confidence=min_confidence)
        self.telemetry_queue = telemetry_queue
        self.context_queue = context_queue
        self.output_queue = output_queue
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def run(self) -> None:
        """
        Run WITNESS agent continuous loop.

        Subscribes to telemetry and context streams, processes events,
        and publishes detected patterns.
        """
        self._running = True

        # Start monitoring both streams concurrently
        telemetry_task = asyncio.create_task(
            self._monitor_stream(self.telemetry_queue, "telemetry")
        )
        context_task = asyncio.create_task(
            self._monitor_stream(self.context_queue, "personal_context")
        )

        self._tasks = [telemetry_task, context_task]

        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            self._running = False
            raise

    async def _monitor_stream(self, queue_name: str, source_type: str) -> None:
        """
        Monitor a single event stream.

        Args:
            queue_name: Queue to subscribe to
            source_type: Source type for signal attribution
        """
        async for event in self.message_bus.subscribe(queue_name):
            if not self._running:
                break

            try:
                await self._process_event(event, source_type)
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing event: {e}")
                continue

    async def _process_event(self, event: Dict[str, Any], source_type: str) -> None:
        """
        Process single event through the 8-step loop.

        Steps:
        1. LISTEN (completed - event received)
        2. CLASSIFY - detect pattern
        3. VALIDATE - check confidence threshold
        4. ENRICH - add metadata
        5. SELF-VERIFY - validate JSON schema
        6. PUBLISH - send to improvement_queue
        7. PERSIST - store in pattern_store
        8. RESET - clear state for next event
        """
        # Step 1: LISTEN (implicit - event already received)

        # Extract event text
        event_text = self._extract_text(event)
        if not event_text:
            return

        # Step 2: CLASSIFY
        pattern_match = self.detector.detect(
            event_text=event_text,
            metadata=event.get("metadata", {})
        )

        # Step 3: VALIDATE
        if not pattern_match:
            return  # Below confidence threshold

        # Step 4: ENRICH
        signal = self._create_signal(
            pattern_match=pattern_match,
            source_type=source_type,
            event=event
        )

        # Step 5: SELF-VERIFY
        if not self._verify_signal(signal):
            print(f"Signal validation failed: {signal}")
            return

        # Step 6: PUBLISH
        await self.message_bus.publish(
            queue_name=self.output_queue,
            message=signal.to_dict(),
            priority=self._get_priority_value(signal.priority),
            correlation_id=signal.correlation_id
        )

        # Step 7: PERSIST
        self.pattern_store.store_pattern(
            pattern_type=pattern_match.pattern_type,
            pattern_name=pattern_match.pattern_name,
            content=signal.summary,
            confidence=signal.confidence,
            metadata=signal.data,
            evidence_count=1
        )

        # Step 8: RESET (implicit - no state carried to next event)

    def _extract_text(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract text content from event."""
        # Try multiple common keys
        for key in ["message", "text", "content", "error", "description"]:
            if key in event and event[key]:
                return str(event[key])

        # Fallback to full event as string
        return json.dumps(event)

    def _create_signal(
        self,
        pattern_match: PatternMatch,
        source_type: str,
        event: Dict[str, Any]
    ) -> Signal:
        """Create Signal from pattern match."""
        # Determine priority
        priority = self._determine_priority(pattern_match)

        # Extract data
        data = {
            "pattern_type": pattern_match.pattern_type,
            "keywords": pattern_match.keywords_matched,
            "base_score": pattern_match.base_score,
            "keyword_score": pattern_match.keyword_score
        }

        # Add event metadata if present
        if "metadata" in event:
            data.update(event.get("metadata", {}))

        # Generate summary (max 120 chars)
        summary = self._generate_summary(pattern_match, event)

        return Signal(
            priority=priority,
            source=source_type,
            pattern=pattern_match.pattern_name,
            confidence=pattern_match.confidence,
            data=data,
            summary=summary,
            timestamp=datetime.now().isoformat(),
            source_id=event.get("_message_id", event.get("id", "unknown")),
            correlation_id=event.get("correlation_id")
        )

    def _determine_priority(self, pattern_match: PatternMatch) -> str:
        """Determine signal priority based on pattern."""
        if pattern_match.pattern_type == "failure":
            if pattern_match.confidence >= 0.9:
                return "CRITICAL"
            elif pattern_match.confidence >= 0.8:
                return "HIGH"
            else:
                return "NORMAL"
        elif pattern_match.pattern_type == "opportunity":
            if pattern_match.pattern_name == "constitutional_violation":
                return "HIGH"
            else:
                return "NORMAL"
        else:  # user_intent
            return "NORMAL"

    def _generate_summary(self, pattern_match: PatternMatch, event: Dict[str, Any]) -> str:
        """Generate summary string (max 120 chars)."""
        pattern_desc = pattern_match.pattern_name.replace("_", " ").title()
        source_text = self._extract_text(event) or "event"

        # Truncate source text if needed
        max_source_len = 120 - len(pattern_desc) - 20
        if len(source_text) > max_source_len:
            source_text = source_text[:max_source_len] + "..."

        summary = f"{pattern_desc}: {source_text}"
        return summary[:120]

    def _verify_signal(self, signal: Signal) -> bool:
        """Verify signal has required fields and valid values."""
        try:
            # Required fields
            assert signal.priority in ["CRITICAL", "HIGH", "NORMAL"]
            assert signal.source in ["telemetry", "personal_context"]
            assert isinstance(signal.pattern, str) and signal.pattern
            assert 0.7 <= signal.confidence <= 1.0
            assert isinstance(signal.data, dict)
            assert isinstance(signal.summary, str) and len(signal.summary) <= 120
            assert isinstance(signal.timestamp, str)
            assert isinstance(signal.source_id, str) or isinstance(signal.source_id, int)

            # Validate JSON serialization
            json.dumps(signal.to_dict())

            return True
        except (AssertionError, TypeError, ValueError) as e:
            # Debug: print what failed
            print(f"Signal validation failed: {signal}")
            return False

    def _get_priority_value(self, priority: str) -> int:
        """Convert priority string to integer for message bus."""
        return {"CRITICAL": 10, "HIGH": 5, "NORMAL": 0}.get(priority, 0)

    async def stop(self) -> None:
        """Stop WITNESS agent."""
        self._running = False
        for task in self._tasks:
            task.cancel()

        try:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Get WITNESS agent statistics."""
        detector_stats = self.detector.get_pattern_stats()
        store_stats = self.pattern_store.get_stats()

        return {
            "detector": detector_stats,
            "store": store_stats,
            "running": self._running,
            "monitored_queues": [self.telemetry_queue, self.context_queue]
        }
