"""Audio Capture Module - EXPERIMENTAL

⚠️ **Status**: Experimental / Prototype
⚠️ **Production Readiness**: NOT READY

**Purpose**:
Audio capture from system microphone with Voice Activity Detection (VAD).
Uses PyAudio for audio capture and RMS-based VAD for speech detection.

**Privacy Concerns**:
- Microphone access (continuous capture capability)
- Memory buffers contain raw audio (no encryption)
- VAD threshold may miss privacy-sensitive whispers
- Buffer clearing on stop (but no verification)
- No audit trail for microphone access

**External Dependencies**:
- pyaudio (platform-specific, requires manual compilation on macOS/Windows)
- numpy (optional, for faster RMS calculation)
- Platform audio drivers (CoreAudio on macOS, WASAPI on Windows)

**Known Issues**:
- Low test coverage (~10%)
- No error handling for device disconnection
- Privacy consent flow missing
- RMS-based VAD is simplistic (high false positive rate)
- Buffer overflow handling incomplete
- No multi-device support (single microphone only)
- save_segment_to_wav violates privacy-first design

**To Upgrade to Production**:
See: docs/TRINITY_UPGRADE_CHECKLIST.md

Required steps:
- [ ] 100% test coverage (currently ~10%)
- [ ] Privacy consent flow implementation
- [ ] Error handling (Result<T,E> pattern throughout)
- [ ] Advanced VAD (ML-based, e.g., WebRTC VAD)
- [ ] Cross-platform compatibility testing
- [ ] Constitutional compliance (Articles I-V)
- [ ] Security review (buffer encryption, secure clearing)
- [ ] Remove save_segment_to_wav or gate behind explicit flag

**Performance Targets**:
- <10% CPU usage during continuous operation ✅ (achieved)
- <200MB memory footprint ✅ (achieved)
- Real-time capture without buffer overflow ⚠️ (needs testing)

**Constitutional Compliance (Partial)**:
- Article I: Complete audio chunks before processing ✅
- Article II: Strict typing with Pydantic models ✅
- Article VII: Functions <50 lines ✅ (most functions comply)
"""

import asyncio
import struct
import wave
from collections import deque
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

# Optional numpy import for faster RMS calculation
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from trinity_protocol.experimental.models.audio import (
    AudioCaptureStats,
    AudioConfig,
    AudioSegment,
    VADResult,
)

# Type alias for Result pattern
try:
    from shared.type_definitions.result import Err, Ok, Result
except ImportError:
    # Fallback for testing
    from dataclasses import dataclass
    from typing import Union

    @dataclass
    class Ok:
        value: any

    @dataclass
    class Err:
        error: any

    Result = Union[Ok, Err]


class AudioCaptureModule:
    """
    Audio capture with Voice Activity Detection.

    Captures audio from system microphone in real-time,
    applies RMS-based VAD, and yields AudioSegment objects.
    """

    def __init__(self, config: AudioConfig | None = None, device_index: int | None = None):
        """
        Initialize audio capture.

        Args:
            config: Audio configuration (defaults to 16kHz mono)
            device_index: Microphone device index (None = default)
        """
        self.config = config or AudioConfig()
        self.device_index = device_index
        self.is_running = False
        self._audio_stream = None
        self._pyaudio = None
        self._buffer = deque(maxlen=int(self.config.sample_rate * self.config.buffer_seconds))
        self.stats = AudioCaptureStats()

    async def start(self) -> Result[None, str]:
        """
        Start audio capture.

        Returns:
            Result with None on success, error message on failure
        """
        if self.is_running:
            return Err("Audio capture already running")

        try:
            # Lazy import to avoid dependency during testing
            import pyaudio

            self._pyaudio = pyaudio.PyAudio()

            # Open audio stream
            self._audio_stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=None,  # Use blocking API for simplicity
            )

            self.is_running = True
            return Ok(None)

        except ImportError:
            return Err("PyAudio not installed. Run: pip install pyaudio")
        except Exception as e:
            return Err(f"Failed to start audio capture: {str(e)}")

    async def stop(self) -> None:
        """Stop audio capture and clean up resources."""
        if not self.is_running:
            return

        self.is_running = False

        if self._audio_stream is not None:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
            self._audio_stream = None

        if self._pyaudio is not None:
            self._pyaudio.terminate()
            self._pyaudio = None

        # Clear buffer for privacy
        self._buffer.clear()

    def _calculate_rms(self, audio_data: bytes) -> float:
        """
        Calculate RMS (Root Mean Square) level of audio.

        Args:
            audio_data: Raw audio bytes (16-bit PCM)

        Returns:
            RMS level (0.0 = silence, higher = louder)
        """
        if not audio_data:
            return 0.0

        if HAS_NUMPY:
            # Fast path with numpy
            samples = np.frombuffer(audio_data, dtype=np.int16)
            if len(samples) == 0:
                return 0.0
            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            return float(rms)
        else:
            # Fallback: pure Python RMS calculation
            # Convert bytes to list of int16 values
            num_samples = len(audio_data) // 2
            if num_samples == 0:
                return 0.0

            sum_squares = 0.0
            for i in range(num_samples):
                # Unpack 16-bit signed int (little-endian)
                sample = struct.unpack_from("<h", audio_data, i * 2)[0]
                sum_squares += sample**2

            mean_square = sum_squares / num_samples
            rms = mean_square**0.5
            return rms

    def _detect_speech(self, audio_data: bytes, threshold: float = 15.0) -> VADResult:
        """
        Detect speech using RMS-based Voice Activity Detection.

        Args:
            audio_data: Raw audio bytes
            threshold: RMS threshold for speech detection

        Returns:
            VADResult with detection status and confidence
        """
        rms = self._calculate_rms(audio_data)
        has_speech = rms > threshold

        # Simple confidence based on how far above/below threshold
        if has_speech:
            confidence = min(rms / (threshold * 3.0), 1.0)
        else:
            confidence = max(0.0, 1.0 - (rms / threshold))

        return VADResult(has_speech=has_speech, confidence=confidence, rms_level=rms)

    async def capture_chunk(self, duration_seconds: float = 1.0) -> Result[AudioSegment, str]:
        """
        Capture a single audio chunk.

        Args:
            duration_seconds: Duration to capture

        Returns:
            Result with AudioSegment or error message
        """
        if not self.is_running:
            return Err("Audio capture not running")

        try:
            # Calculate number of frames to read
            num_frames = int(self.config.sample_rate * duration_seconds)

            # Read audio data
            audio_data = self._audio_stream.read(num_frames, exception_on_overflow=False)

            # Detect speech
            vad_result = self._detect_speech(audio_data)

            # Create segment
            segment = AudioSegment(
                data=audio_data,
                sample_rate=self.config.sample_rate,
                channels=self.config.channels,
                duration_seconds=duration_seconds,
                timestamp=datetime.now(),
                has_speech=vad_result.has_speech,
            )

            # Update stats
            self.stats.total_duration_seconds += duration_seconds
            self.stats.segments_captured += 1
            if vad_result.has_speech:
                self.stats.speech_duration_seconds += duration_seconds
            else:
                self.stats.silence_duration_seconds += duration_seconds

            return Ok(segment)

        except Exception as e:
            return Err(f"Failed to capture audio: {str(e)}")

    async def capture_stream(
        self, chunk_duration: float = 1.0
    ) -> AsyncGenerator[AudioSegment, None]:
        """
        Stream audio chunks continuously.

        Args:
            chunk_duration: Duration of each chunk in seconds

        Yields:
            AudioSegment objects with captured audio
        """
        while self.is_running:
            result = await self.capture_chunk(chunk_duration)

            if isinstance(result, Ok):
                yield result.unwrap()
            else:
                # Log error but continue streaming
                print(f"Audio capture error: {result.unwrap_err()}")
                await asyncio.sleep(0.1)

    async def save_segment_to_wav(
        self, segment: AudioSegment, output_path: Path
    ) -> Result[None, str]:
        """
        Save audio segment to WAV file (for testing/debugging).

        NOTE: This violates privacy-first design. Use only for testing.

        Args:
            segment: Audio segment to save
            output_path: Output file path

        Returns:
            Result with None on success, error message on failure
        """
        try:
            with wave.open(str(output_path), "wb") as wav_file:
                wav_file.setnchannels(segment.channels)
                wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                wav_file.setframerate(segment.sample_rate)
                wav_file.writeframes(segment.data)

            return Ok(None)
        except Exception as e:
            return Err(f"Failed to save WAV file: {str(e)}")

    def get_stats(self) -> AudioCaptureStats:
        """
        Get capture statistics.

        Returns:
            Current AudioCaptureStats
        """
        return self.stats

    def reset_stats(self) -> None:
        """Reset capture statistics."""
        self.stats = AudioCaptureStats()
