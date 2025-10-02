"""
Ambient Listener Service - Phase 4 Integration & Orchestration.

Orchestrates: AudioCapture → Whisper → MessageBus publishing.
Publishes transcriptions to personal_context_stream for WITNESS consumption.

Flow:
1. Capture audio from microphone
2. Transcribe with Whisper (local)
3. Publish to message bus
4. WITNESS consumes and detects patterns
5. ARCHITECT receives patterns and formulates questions

Constitutional Compliance:
- Article I: Complete context (full audio chunks before transcription)
- Article II: 100% verification (strict typing, error handling)
- Article IV: Continuous learning (pattern persistence)
"""

import asyncio
import uuid
from typing import Optional
from datetime import datetime
from pathlib import Path

from trinity_protocol.transcription_service import TranscriptionService
from trinity_protocol.message_bus import MessageBus
from trinity_protocol.conversation_context import ConversationContext
from trinity_protocol.experimental.models.audio import (
    AudioConfig,
    WhisperConfig,
    TranscriptionResult
)
from trinity_protocol.core.models.patterns import AmbientEvent

# Result pattern
try:
    from shared.type_definitions.result import Result, Ok, Err
except ImportError:
    from typing import Union
    from dataclasses import dataclass

    @dataclass
    class Ok:
        value: any

    @dataclass
    class Err:
        error: any

    Result = Union[Ok, Err]


class AmbientListenerService:
    """
    Main orchestrator for ambient intelligence system.

    Coordinates audio capture, transcription, and message publishing
    for continuous ambient listening and proactive assistance.
    """

    def __init__(
        self,
        message_bus: MessageBus,
        audio_config: Optional[AudioConfig] = None,
        whisper_config: Optional[WhisperConfig] = None,
        device_index: Optional[int] = None,
        queue_name: str = "personal_context_stream",
        min_confidence: float = 0.6
    ):
        """
        Initialize ambient listener service.

        Args:
            message_bus: Message bus for publishing transcriptions
            audio_config: Audio capture configuration
            whisper_config: Whisper model configuration
            device_index: Microphone device index (None = default)
            queue_name: Message bus queue for transcriptions
            min_confidence: Minimum confidence to publish transcription
        """
        self.message_bus = message_bus
        self.queue_name = queue_name
        self.min_confidence = min_confidence

        # Initialize transcription service
        self.transcription_service = TranscriptionService(
            audio_config=audio_config,
            whisper_config=whisper_config,
            device_index=device_index
        )

        # Initialize conversation context
        self.conversation_context = ConversationContext(
            window_minutes=10.0,
            max_entries=100,
            silence_threshold_seconds=120.0
        )

        # Session tracking
        self.session_id: Optional[str] = None
        self.is_running = False
        self._transcription_count = 0
        self._publish_count = 0

    async def start(self) -> Result[None, str]:
        """
        Start ambient listener service.

        Initializes transcription service and begins continuous operation.

        Returns:
            Result with None on success, error message on failure
        """
        if self.is_running:
            return Err("Service already running")

        # Generate session ID
        self.session_id = self._generate_session_id()

        # Start transcription service
        result = await self.transcription_service.start()
        if isinstance(result, Err):
            return result

        self.is_running = True
        return Ok(None)

    async def stop(self) -> None:
        """Stop ambient listener service and clean up resources."""
        if not self.is_running:
            return

        self.is_running = False

        # Stop transcription service
        await self.transcription_service.stop()

        # Reset state
        self.session_id = None

    async def run(
        self,
        chunk_duration: float = 1.0,
        skip_silence: bool = True
    ) -> None:
        """
        Run continuous ambient listening loop.

        Streams transcriptions from audio capture, publishes to message bus,
        and updates conversation context.

        Args:
            chunk_duration: Audio chunk duration in seconds
            skip_silence: Skip transcription of silent segments

        Raises:
            RuntimeError: If service not started
        """
        if not self.is_running:
            raise RuntimeError("Service not started - call start() first")

        try:
            async for transcription in self.transcription_service.transcribe_stream(
                chunk_duration=chunk_duration,
                skip_silence=skip_silence
            ):
                if not self.is_running:
                    break

                # Process transcription
                await self._process_transcription(transcription)

        except asyncio.CancelledError:
            # Graceful shutdown
            await self.stop()
            raise

    async def _process_transcription(
        self,
        transcription: TranscriptionResult
    ) -> None:
        """
        Process transcription: update context and publish to message bus.

        Args:
            transcription: Whisper transcription result
        """
        self._transcription_count += 1

        # Skip low-confidence transcriptions
        if transcription.confidence < self.min_confidence:
            return

        # Parse timestamp
        timestamp = datetime.fromisoformat(transcription.timestamp)

        # Update conversation context
        self.conversation_context.add_transcription(
            text=transcription.text,
            timestamp=timestamp,
            confidence=transcription.confidence
        )

        # Create ambient event
        event = self._create_ambient_event(transcription, timestamp)

        # Publish to message bus
        await self._publish_event(event)

        self._publish_count += 1

    def _create_ambient_event(
        self,
        transcription: TranscriptionResult,
        timestamp: datetime
    ) -> AmbientEvent:
        """
        Create ambient event from transcription.

        Args:
            transcription: Whisper transcription result
            timestamp: Transcription timestamp

        Returns:
            AmbientEvent ready for message bus
        """
        # Get conversation metadata
        conversation_id = self.conversation_context.conversation_id

        # Build metadata
        metadata = {
            "audio_duration_seconds": transcription.duration_seconds,
            "language": transcription.language,
            "whisper_confidence": transcription.confidence,
            "session_id": self.session_id,
            "conversation_duration_minutes": self.conversation_context.get_conversation_duration(),
            "speaker_count": self.conversation_context.get_speaker_count(),
            "transcription_number": self._transcription_count
        }

        # Add segment timestamps if available
        if transcription.segments:
            metadata["segment_count"] = len(transcription.segments)
            metadata["has_timestamps"] = True

        return AmbientEvent(
            event_type="ambient_transcription",
            source="ambient_listener",
            content=transcription.text,
            timestamp=timestamp.isoformat(),
            confidence=transcription.confidence,
            session_id=self.session_id,
            conversation_id=conversation_id,
            metadata=metadata
        )

    async def _publish_event(self, event: AmbientEvent) -> None:
        """
        Publish ambient event to message bus.

        Args:
            event: AmbientEvent to publish
        """
        try:
            await self.message_bus.publish(
                queue_name=self.queue_name,
                message=event.dict(),
                priority=0,  # NORMAL priority
                correlation_id=event.conversation_id
            )
        except Exception as e:
            # Log error but continue processing
            print(f"Failed to publish event: {e}")

    def _generate_session_id(self) -> str:
        """
        Generate unique session ID.

        Returns:
            Session ID string
        """
        timestamp = datetime.now().isoformat()
        unique_id = uuid.uuid4().hex[:8]
        return f"ambient_{timestamp}_{unique_id}"

    def get_stats(self) -> dict:
        """
        Get ambient listener statistics.

        Returns:
            Dict with service metrics
        """
        transcription_stats = self.transcription_service.get_stats()
        conversation_stats = self.conversation_context.get_stats()

        return {
            "session_id": self.session_id,
            "is_running": self.is_running,
            "transcription_count": self._transcription_count,
            "publish_count": self._publish_count,
            "min_confidence": self.min_confidence,
            "queue_name": self.queue_name,
            "transcription_service": {
                "total_processed_seconds": self.transcription_service.total_processed,
                "audio_stats": transcription_stats.dict()
            },
            "conversation_context": conversation_stats
        }

    def reset_stats(self) -> None:
        """Reset service statistics."""
        self._transcription_count = 0
        self._publish_count = 0
        self.transcription_service.reset_stats()
        self.conversation_context.reset()


async def main():
    """
    Demo: Run ambient listener service for testing.

    Example flow:
    1. Start service
    2. Capture audio
    3. Transcribe
    4. Publish to message bus
    5. WITNESS consumes
    """
    from trinity_protocol.message_bus import MessageBus

    # Initialize message bus
    bus = MessageBus(db_path="test_ambient.db")

    # Create ambient listener (will use default configs)
    service = AmbientListenerService(
        message_bus=bus,
        min_confidence=0.6
    )

    print("Starting ambient listener service...")

    # Start service
    result = await service.start()
    if isinstance(result, Err):
        print(f"Failed to start: {result.error}")
        return

    print("Service started. Listening for ambient audio...")
    print("Press Ctrl+C to stop.")

    try:
        # Run for 60 seconds or until interrupted
        await asyncio.wait_for(
            service.run(chunk_duration=1.0, skip_silence=True),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        print("\nDemo timeout reached.")
    except KeyboardInterrupt:
        print("\nStopping service...")
    finally:
        await service.stop()
        stats = service.get_stats()
        print(f"\nFinal stats:")
        print(f"  Transcriptions: {stats['transcription_count']}")
        print(f"  Published: {stats['publish_count']}")
        print(f"  Total audio: {stats['transcription_service']['total_processed_seconds']:.1f}s")

        bus.close()


if __name__ == "__main__":
    asyncio.run(main())
