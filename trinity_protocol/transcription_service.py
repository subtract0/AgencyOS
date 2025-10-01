"""
Transcription Service - Main orchestrator for Ambient Intelligence.

Coordinates audio capture and Whisper transcription for real-time
speech-to-text processing with privacy-first design.

Constitutional Compliance:
- Article I: Complete Context Before Action (full audio chunks)
- Article II: 100% Verification (strict typing, comprehensive tests)
- Article VII: Functions <50 lines, clear naming

Performance Targets:
- <500ms latency for 1s audio transcription
- <10% CPU usage during continuous operation
- <200MB memory footprint
- Real-time factor (RTF) <0.5

Privacy Guarantees:
- Memory-only processing (no disk writes for raw audio)
- Local Whisper models (no cloud API calls)
- User control (start/stop/pause)
"""

import asyncio
from pathlib import Path
from typing import Optional, AsyncGenerator
from datetime import datetime

from trinity_protocol.audio_capture import AudioCaptureModule
from trinity_protocol.whisper_transcriber import WhisperTranscriber
from trinity_protocol.models.audio import (
    AudioConfig,
    WhisperConfig,
    AudioSegment,
    TranscriptionResult,
    AudioCaptureStats,
)

# Type alias for Result pattern
try:
    from shared.type_definitions.result import Result, Ok, Err
except ImportError:
    # Fallback for testing
    from typing import Union
    from dataclasses import dataclass

    @dataclass
    class Ok:
        value: any

    @dataclass
    class Err:
        error: any

    Result = Union[Ok, Err]


class TranscriptionService:
    """
    Main transcription service orchestrator.

    Coordinates AudioCaptureModule and WhisperTranscriber to provide
    real-time speech-to-text transcription with privacy guarantees.
    """

    def __init__(
        self,
        audio_config: Optional[AudioConfig] = None,
        whisper_config: Optional[WhisperConfig] = None,
        device_index: Optional[int] = None,
    ):
        """
        Initialize transcription service.

        Args:
            audio_config: Audio capture configuration
            whisper_config: Whisper model configuration
            device_index: Microphone device index (None = default)
        """
        self.audio_config = audio_config or AudioConfig()
        self.whisper_config = whisper_config
        self.device_index = device_index

        self.audio_capture = AudioCaptureModule(
            config=self.audio_config,
            device_index=device_index
        )
        self.transcriber = WhisperTranscriber(config=whisper_config)

        self.is_running = False
        self._total_processed = 0.0

    async def start(self) -> Result[None, str]:
        """
        Start transcription service.

        Initializes both audio capture and Whisper transcriber.

        Returns:
            Result with None on success, error message on failure
        """
        if self.is_running:
            return Err("Service already running")

        # Start audio capture
        audio_result = await self.audio_capture.start()
        if isinstance(audio_result, Err):
            return Err(f"Audio capture failed: {audio_result.error}")

        # Start transcriber
        transcriber_result = await self.transcriber.start()
        if isinstance(transcriber_result, Err):
            await self.audio_capture.stop()  # Clean up
            return Err(f"Transcriber failed: {transcriber_result.error}")

        self.is_running = True
        return Ok(None)

    async def stop(self) -> None:
        """Stop transcription service and clean up resources."""
        if not self.is_running:
            return

        self.is_running = False

        # Stop both components
        await self.audio_capture.stop()
        await self.transcriber.stop()

    async def transcribe_file(
        self,
        audio_path: Path,
        language: str = "en"
    ) -> Result[TranscriptionResult, str]:
        """
        Transcribe audio file.

        Args:
            audio_path: Path to WAV audio file
            language: Language code (ISO 639-1)

        Returns:
            Result with TranscriptionResult or error message
        """
        if not self.is_running:
            return Err("Service not started")

        # Delegate to transcriber
        result = await self.transcriber.transcribe_file(
            audio_path,
            language
        )

        if isinstance(result, Ok):
            self._total_processed += result.value.duration_seconds

        return result

    async def transcribe_segment(
        self,
        segment: AudioSegment
    ) -> Result[TranscriptionResult, str]:
        """
        Transcribe audio segment.

        Args:
            segment: Audio segment to transcribe

        Returns:
            Result with TranscriptionResult or error message
        """
        if not self.is_running:
            return Err("Service not started")

        # Transcribe segment
        result = await self.transcriber.transcribe_segment(segment)

        if isinstance(result, Ok):
            # Update duration from segment
            result.value.duration_seconds = segment.duration_seconds
            self._total_processed += segment.duration_seconds

        return result

    async def transcribe_stream(
        self,
        chunk_duration: float = 1.0,
        skip_silence: bool = True
    ) -> AsyncGenerator[TranscriptionResult, None]:
        """
        Stream transcriptions from continuous audio capture.

        Args:
            chunk_duration: Duration of each audio chunk in seconds
            skip_silence: Skip transcription of silent audio segments

        Yields:
            TranscriptionResult objects
        """
        if not self.is_running:
            raise RuntimeError("Service not started")

        async for segment in self.audio_capture.capture_stream(
            chunk_duration
        ):
            # Skip silent segments if requested
            if skip_silence and not segment.has_speech:
                continue

            # Transcribe segment
            result = await self.transcribe_segment(segment)

            if isinstance(result, Ok):
                yield result.value
            else:
                # Log error but continue streaming
                print(f"Transcription error: {result.error}")

    def get_stats(self) -> AudioCaptureStats:
        """
        Get audio capture statistics.

        Returns:
            Current AudioCaptureStats
        """
        return self.audio_capture.get_stats()

    def reset_stats(self) -> None:
        """Reset audio capture statistics."""
        self.audio_capture.reset_stats()
        self._total_processed = 0.0

    @property
    def total_processed(self) -> float:
        """
        Total audio duration processed (in seconds).

        Returns:
            Total seconds of audio transcribed
        """
        return self._total_processed

    @property
    def buffer(self) -> AudioConfig:
        """
        Get audio buffer configuration.

        Returns:
            Current AudioConfig
        """
        return self.audio_config

    def get_backend(self) -> Optional[str]:
        """
        Get current Whisper backend.

        Returns:
            Backend name ("whisper.cpp" or "openai-whisper")
        """
        return self.transcriber.get_backend()
