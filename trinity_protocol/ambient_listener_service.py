"""Trinity Ambient Listener Service - Main Orchestrator

PRODUCTION-READY implementation for capturing real voice data.

Constitutional Compliance:
- Article I: Complete context before action (full audio chunks)
- Article II: Strict typing with Pydantic models (no Dict[Any, Any])
- Article V: Spec-driven development
- Article VII: Functions <50 lines

Flow:
1. AudioCapture: Capture audio from microphone with VAD
2. Transcription: Transcribe with faster-whisper
3. PatternDetection: Detect conversation patterns
4. Response: Log patterns for ARCHITECT/EXECUTOR pickup

No mocks, no simulations - REAL microphone capture only.
"""

import asyncio
import argparse
import sys
import logging
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field

from trinity_protocol.experimental.audio_capture import AudioCaptureModule
from trinity_protocol.experimental.transcription import WhisperTranscriber
from trinity_protocol.experimental.ambient_patterns import (
    AmbientPatternDetector,
)
from trinity_protocol.experimental.conversation_context import (
    ConversationContext,
)
from trinity_protocol.experimental.models.audio import (
    AudioConfig,
    AudioSegment,
    WhisperConfig,
    TranscriptionResult,
)
from trinity_protocol.core.models.patterns import DetectedPattern
from shared.persistent_store import PersistentStore
from shared.type_definitions.result import Result, Ok, Err

# Configure logging for stdout (nohup capture)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


class AmbientListenerConfig(BaseModel):
    """Configuration for ambient listener service."""

    model_name: str = Field(
        default="base.en", description="Whisper model name"
    )
    min_confidence: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum transcription confidence",
    )
    chunk_duration: float = Field(
        default=3.0, gt=0.0, description="Audio chunk duration (seconds)"
    )
    silence_threshold: float = Field(
        default=500.0,
        gt=0.0,
        description="RMS threshold for speech detection",
    )
    pattern_check_interval: float = Field(
        default=30.0,
        gt=0.0,
        description="Interval for pattern detection (seconds)",
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True


class AmbientListenerService:
    """
    Main orchestrator for Trinity ambient listener.

    Coordinates audio capture, transcription, and pattern detection
    to enable ambient intelligence capabilities.
    """

    def __init__(
        self,
        audio_capture: Optional[AudioCaptureModule] = None,
        transcriber: Optional[WhisperTranscriber] = None,
        pattern_detector: Optional[AmbientPatternDetector] = None,
        conversation_context: Optional[ConversationContext] = None,
        config: Optional[AmbientListenerConfig] = None,
    ):
        """
        Initialize ambient listener service.

        Args:
            audio_capture: Audio capture module (auto-created if None)
            transcriber: Whisper transcriber (auto-created if None)
            pattern_detector: Pattern detector (auto-created if None)
            conversation_context: Context manager (auto-created if None)
            config: Service configuration
        """
        self.config = config or AmbientListenerConfig()
        self.status = ServiceStatus.STOPPED
        self._running = False

        # Initialize components (or use provided mocks for testing)
        if conversation_context is None:
            conversation_context = ConversationContext(
                window_minutes=10.0, silence_threshold_seconds=120.0
            )
        self.conversation_context = conversation_context

        if audio_capture is None:
            audio_config = self._create_audio_config(self.config)
            audio_capture = AudioCaptureModule(config=audio_config)
        self.audio_capture = audio_capture

        if transcriber is None:
            whisper_config = self._create_whisper_config(self.config)
            transcriber = WhisperTranscriber(config=whisper_config)
        self.transcriber = transcriber

        if pattern_detector is None:
            pattern_store = PersistentStore(db_path="trinity_patterns.db")
            pattern_detector = AmbientPatternDetector(
                conversation_context=self.conversation_context,
                pattern_store=pattern_store,
                min_confidence=self.config.min_confidence,
            )
        self.pattern_detector = pattern_detector

        logger.info("Ambient listener service initialized")

    @staticmethod
    def _create_audio_config(
        config: AmbientListenerConfig,
    ) -> AudioConfig:
        """Create AudioConfig from service config."""
        return AudioConfig(
            sample_rate=16000,  # Whisper native
            channels=1,  # Mono
            chunk_size=1024,
            buffer_seconds=30.0,
        )

    @staticmethod
    def _create_whisper_config(
        config: AmbientListenerConfig,
    ) -> WhisperConfig:
        """Create WhisperConfig from service config."""
        model_path = (
            Path.home()
            / ".cache"
            / "whisper"
            / f"{config.model_name}.pt"
        )

        return WhisperConfig(
            model_path=str(model_path),
            model_name=config.model_name,
            language="en",
            use_gpu=True,
            num_threads=4,
            beam_size=5,
        )

    async def start(self) -> Result[None, str]:
        """
        Start ambient listener service.

        Returns:
            Result with None on success, error message on failure
        """
        if self.status == ServiceStatus.RUNNING:
            return Err("Service already running")

        logger.info("Starting ambient listener service...")
        self.status = ServiceStatus.STARTING

        # Start audio capture
        audio_result = await self.audio_capture.start()
        if isinstance(audio_result, Err):
            self.status = ServiceStatus.ERROR
            return Err(f"Audio capture failed: {audio_result._error}")

        # Start transcriber
        transcriber_result = await self.transcriber.start()
        if isinstance(transcriber_result, Err):
            await self.audio_capture.stop()
            self.status = ServiceStatus.ERROR
            return Err(f"Transcriber failed: {transcriber_result._error}")

        self.status = ServiceStatus.RUNNING
        self._running = True
        logger.info("Ambient listener service started successfully")

        # Start background tasks
        asyncio.create_task(self._run_audio_pipeline())

        return Ok(None)

    async def stop(self) -> None:
        """Stop ambient listener service."""
        if self.status == ServiceStatus.STOPPED:
            return

        logger.info("Stopping ambient listener service...")
        self._running = False

        # Stop components
        await self.audio_capture.stop()
        await self.transcriber.stop()

        self.status = ServiceStatus.STOPPED
        logger.info("Ambient listener service stopped")

    async def _run_audio_pipeline(self) -> None:
        """Run main audio processing pipeline."""
        logger.info("Audio pipeline started")

        try:
            async for audio_segment in self.audio_capture.capture_stream(
                chunk_duration=self.config.chunk_duration
            ):
                if not self._running:
                    break

                # Process audio chunk
                result = await self._process_audio_chunk(audio_segment)

                if isinstance(result, Err):
                    logger.error(
                        f"Audio processing error: {result._error}"
                    )
                    continue

        except Exception as e:
            logger.error(f"Audio pipeline error: {str(e)}")
            self.status = ServiceStatus.ERROR

        logger.info("Audio pipeline stopped")

    async def _process_audio_chunk(
        self, segment: AudioSegment
    ) -> Result[Optional[TranscriptionResult], str]:
        """
        Process single audio chunk.

        Args:
            segment: Audio segment to process

        Returns:
            Result with TranscriptionResult or None (no speech)
        """
        # Skip if no speech detected
        if not segment.has_speech:
            return Ok(None)

        # Transcribe audio
        transcription_result = await self.transcriber.transcribe_segment(
            segment
        )

        if isinstance(transcription_result, Err):
            return Err(transcription_result._error)

        transcription = transcription_result._value

        # Check confidence threshold
        if transcription.confidence < self.config.min_confidence:
            logger.debug(
                f"Low confidence transcription ({transcription.confidence:.2f}): "
                f"'{transcription.text}'"
            )
            return Ok(None)

        logger.info(
            f"Transcription ({transcription.confidence:.2f}): "
            f"'{transcription.text}'"
        )

        # Add to conversation context
        self.conversation_context.add_transcription(
            text=transcription.text,
            timestamp=segment.timestamp,
            confidence=transcription.confidence,
        )

        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(
            transcription_text=transcription.text,
            timestamp=segment.timestamp,
        )

        if patterns:
            await self._handle_detected_patterns(patterns)

        return Ok(transcription)

    async def _handle_detected_patterns(
        self, patterns: List[DetectedPattern]
    ) -> None:
        """
        Handle detected patterns.

        Args:
            patterns: List of detected patterns
        """
        for pattern in patterns:
            logger.info(
                f"Pattern detected: {pattern.pattern_type} "
                f"(confidence={pattern.confidence:.2f}, "
                f"topic='{pattern.topic}')"
            )

            # Persist pattern for cross-session learning
            self.pattern_detector.persist_pattern(pattern)

            # Log pattern details for monitoring
            logger.info(f"  Context: {pattern.context_summary}")
            logger.info(f"  Keywords: {', '.join(pattern.keywords)}")
            logger.info(f"  Urgency: {pattern.urgency}")

    def get_stats(self) -> dict:
        """
        Get service statistics.

        Returns:
            Dictionary with service metrics
        """
        return {
            "status": self.status,
            "config": self.config.model_dump(),
            "conversation_stats": self.conversation_context.get_stats(),
            "audio_stats": (
                self.audio_capture.get_stats().model_dump()
                if hasattr(self.audio_capture, "get_stats")
                else {}
            ),
        }


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse CLI arguments.

    Args:
        args: Arguments to parse (uses sys.argv if None)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Trinity Ambient Listener Service"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="base.en",
        help="Whisper model name (default: base.en)",
    )

    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.6,
        help="Minimum transcription confidence (default: 0.6)",
    )

    parser.add_argument(
        "--chunk-duration",
        type=float,
        default=3.0,
        help="Audio chunk duration in seconds (default: 3.0)",
    )

    parser.add_argument(
        "--silence-threshold",
        type=float,
        default=500.0,
        help="RMS silence threshold (default: 500.0)",
    )

    return parser.parse_args(args)


async def main() -> None:
    """Main entry point for ambient listener service."""
    args = parse_args()

    # Create configuration from CLI args
    config = AmbientListenerConfig(
        model_name=args.model,
        min_confidence=args.min_confidence,
        chunk_duration=args.chunk_duration,
        silence_threshold=args.silence_threshold,
    )

    # Create service
    service = AmbientListenerService(config=config)

    # Start service
    logger.info("=" * 60)
    logger.info("TRINITY AMBIENT LISTENER - Starting")
    logger.info("=" * 60)
    logger.info(f"Model: {config.model_name}")
    logger.info(f"Min Confidence: {config.min_confidence}")
    logger.info(f"Chunk Duration: {config.chunk_duration}s")
    logger.info("=" * 60)

    result = await service.start()

    if isinstance(result, Err):
        logger.error(f"Failed to start service: {result._error}")
        sys.exit(1)

    # Run until interrupted
    try:
        while True:
            await asyncio.sleep(60)  # Check every minute
            stats = service.get_stats()
            logger.info(f"Status: {stats['status']}")

    except KeyboardInterrupt:
        logger.info("Shutdown signal received")

    finally:
        await service.stop()
        logger.info("Service stopped")


if __name__ == "__main__":
    asyncio.run(main())
