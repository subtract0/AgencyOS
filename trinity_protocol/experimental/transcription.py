"""Whisper Transcription Module - EXPERIMENTAL

⚠️ **Status**: Experimental / Prototype
⚠️ **Production Readiness**: NOT READY

**Purpose**:
Whisper-based audio transcription with GPU acceleration.
Supports both whisper.cpp (fast, C++) and openai-whisper (Python fallback).

**Privacy Concerns**:
- Temporary audio files written to disk (despite "memory-only" claim)
- Whisper models may expose audio characteristics in embeddings
- No secure deletion of temp files (OS-dependent cleanup)
- Model weights stored unencrypted on disk
- No audit trail for transcription operations

**External Dependencies**:
- whisper.cpp (requires manual compilation, C++ toolchain)
- openai-whisper (Python fallback, slower)
- PyTorch or TensorFlow (for openai-whisper)
- GPU drivers (Metal on macOS, CUDA on Linux/Windows)
- Model files (75MB - 1.5GB, requires download)

**Known Issues**:
- Low test coverage (~5%)
- No error handling for model loading failures
- Privacy: temp files violate "memory-only" claim
- GPU detection unreliable across platforms
- Whisper.cpp path hardcoded (not configurable)
- No fallback if both whisper.cpp and openai-whisper fail
- Language detection not exposed to caller

**To Upgrade to Production**:
See: docs/TRINITY_UPGRADE_CHECKLIST.md

Required steps:
- [ ] 100% test coverage (currently ~5%)
- [ ] True memory-only transcription (no temp files)
- [ ] Error handling (Result<T,E> pattern throughout)
- [ ] Configurable model paths and GPU backends
- [ ] Cross-platform GPU detection and fallback
- [ ] Constitutional compliance (Articles I-V)
- [ ] Security review (secure temp file handling)
- [ ] Performance benchmarks on target hardware

**Performance Targets**:
- <500ms latency for 1s audio (whisper.cpp + Metal) ⚠️ (needs validation)
- <2s latency with Python whisper (fallback) ⚠️ (needs validation)
- RTF (real-time factor) <0.5 ⚠️ (not measured)

**Constitutional Compliance (Partial)**:
- Article I: Complete audio processing before returning ✅
- Article II: Strict typing with Pydantic models ✅
- Article VII: Functions <50 lines ⚠️ (some functions exceed limit)
"""

import asyncio
import wave
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from trinity_protocol.experimental.models.audio import (
    WhisperConfig,
    AudioSegment,
    TranscriptionResult,
    TranscriptionSegment,
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


class WhisperTranscriber:
    """
    Audio transcription using Whisper models.

    Attempts to use whisper.cpp for fast GPU-accelerated transcription,
    falls back to openai-whisper Python library if unavailable.
    """

    def __init__(self, config: Optional[WhisperConfig] = None):
        """
        Initialize Whisper transcriber.

        Args:
            config: Whisper configuration (model, language, etc.)
        """
        self.config = config
        self.is_running = False
        self._model = None
        self._backend = None  # "whisper.cpp" or "openai-whisper"

    async def start(self) -> Result[None, str]:
        """
        Load Whisper model and initialize transcriber.

        Returns:
            Result with None on success, error message on failure
        """
        if self.is_running:
            return Err("Transcriber already running")

        # Try whisper.cpp first (fastest)
        result = await self._try_load_whisper_cpp()
        if isinstance(result, Ok):
            self._backend = "whisper.cpp"
            self.is_running = True
            return Ok(None)

        # Fall back to openai-whisper
        result = await self._try_load_openai_whisper()
        if isinstance(result, Ok):
            self._backend = "openai-whisper"
            self.is_running = True
            return Ok(None)

        return Err(
            "No Whisper backend available. Install:\n"
            "  whisper.cpp: pip install whisper-cpp-python\n"
            "  OR openai-whisper: pip install openai-whisper"
        )

    async def _try_load_whisper_cpp(self) -> Result[None, str]:
        """
        Try to load whisper.cpp backend.

        Returns:
            Result with None on success, error message on failure
        """
        try:
            from whispercpp import Whisper

            if self.config is None:
                return Err("WhisperConfig required")

            # Load model
            self._model = Whisper.from_pretrained(
                self.config.model_name,
                basedir=str(Path(self.config.model_path).parent)
            )

            return Ok(None)
        except ImportError:
            return Err("whisper.cpp not installed")
        except Exception as e:
            return Err(f"Failed to load whisper.cpp: {str(e)}")

    async def _try_load_openai_whisper(self) -> Result[None, str]:
        """
        Try to load openai-whisper backend.

        Returns:
            Result with None on success, error message on failure
        """
        try:
            import whisper

            # Use smaller model if not specified
            model_name = (
                self.config.model_name if self.config else "base.en"
            )

            # Load model (blocks, but fast for small models)
            self._model = whisper.load_model(model_name)

            return Ok(None)
        except ImportError:
            return Err("openai-whisper not installed")
        except Exception as e:
            return Err(f"Failed to load openai-whisper: {str(e)}")

    async def stop(self) -> None:
        """Unload model and clean up resources."""
        if not self.is_running:
            return

        self.is_running = False
        self._model = None
        self._backend = None

    async def transcribe_segment(
        self,
        segment: AudioSegment
    ) -> Result[TranscriptionResult, str]:
        """
        Transcribe audio segment to text.

        Args:
            segment: Audio segment to transcribe

        Returns:
            Result with TranscriptionResult or error message
        """
        if not self.is_running:
            return Err("Transcriber not running")

        try:
            # Create temporary WAV file (Whisper requires file input)
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=True
            ) as temp_file:
                # Write segment to temp WAV
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(segment.channels)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(segment.sample_rate)
                    wav_file.writeframes(segment.data)

                # Transcribe based on backend (pass segment duration)
                if self._backend == "whisper.cpp":
                    result = await self._transcribe_with_cpp(
                        Path(temp_file.name),
                        segment.duration_seconds
                    )
                else:
                    result = await self._transcribe_with_python(
                        Path(temp_file.name),
                        segment.duration_seconds
                    )

                return result

        except Exception as e:
            return Err(f"Transcription failed: {str(e)}")

    async def _transcribe_with_cpp(
        self,
        audio_path: Path,
        duration_seconds: float
    ) -> Result[TranscriptionResult, str]:
        """
        Transcribe using whisper.cpp backend.

        Args:
            audio_path: Path to WAV file
            duration_seconds: Duration of audio segment

        Returns:
            Result with TranscriptionResult or error message
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(str(audio_path))
            )

            # Parse whisper.cpp output
            text = output.strip()

            result = TranscriptionResult(
                text=text,
                confidence=0.90,  # whisper.cpp doesn't provide confidence
                language=self.config.language if self.config else "en",
                duration_seconds=duration_seconds,
                timestamp=datetime.now().isoformat()
            )

            return Ok(result)

        except Exception as e:
            return Err(f"whisper.cpp transcription failed: {str(e)}")

    async def _transcribe_with_python(
        self,
        audio_path: Path,
        duration_seconds: float
    ) -> Result[TranscriptionResult, str]:
        """
        Transcribe using openai-whisper backend.

        Args:
            audio_path: Path to WAV file
            duration_seconds: Duration of audio segment

        Returns:
            Result with TranscriptionResult or error message
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result_dict = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(str(audio_path))
            )

            # Parse openai-whisper output
            text = result_dict.get("text", "").strip()
            language = result_dict.get("language", "en")

            # Calculate average confidence from segments
            segments_data = result_dict.get("segments", [])
            if segments_data:
                avg_confidence = sum(
                    s.get("no_speech_prob", 0.0)
                    for s in segments_data
                ) / len(segments_data)
                # Invert no_speech_prob to get speech confidence
                confidence = 1.0 - avg_confidence
            else:
                confidence = 0.85  # Default confidence

            # Build TranscriptionSegment list
            segments = [
                TranscriptionSegment(
                    text=s["text"].strip(),
                    start_time=s["start"],
                    end_time=s["end"],
                    confidence=1.0 - s.get("no_speech_prob", 0.15)
                )
                for s in segments_data
                if s.get("text", "").strip()
            ]

            result = TranscriptionResult(
                text=text,
                confidence=confidence,
                language=language,
                duration_seconds=duration_seconds,
                timestamp=datetime.now().isoformat(),
                segments=segments if segments else None
            )

            return Ok(result)

        except Exception as e:
            return Err(f"openai-whisper transcription failed: {str(e)}")

    async def transcribe_file(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> Result[TranscriptionResult, str]:
        """
        Transcribe audio file directly.

        Args:
            audio_path: Path to audio file (WAV)
            language: Language code (overrides config)

        Returns:
            Result with TranscriptionResult or error message
        """
        if not self.is_running:
            return Err("Transcriber not running")

        # Override language if specified
        original_language = None
        if language and self.config:
            original_language = self.config.language
            self.config.language = language

        try:
            if self._backend == "whisper.cpp":
                result = await self._transcribe_with_cpp(audio_path)
            else:
                result = await self._transcribe_with_python(audio_path)

            return result

        finally:
            # Restore original language
            if original_language and self.config:
                self.config.language = original_language

    def get_backend(self) -> Optional[str]:
        """
        Get current transcription backend.

        Returns:
            Backend name or None if not running
        """
        return self._backend
