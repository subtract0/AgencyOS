"""
Audio data models for Ambient Intelligence System.

Defines Pydantic models for audio configuration, audio segments,
transcription results, and related data structures.

Constitutional Compliance:
- Article II: Strict typing with Pydantic (no Dict[Any, Any])
- Article VII: Functions <50 lines
- Clear, descriptive naming
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    PCM = "pcm"
    RAW = "raw"


class AudioConfig(BaseModel):
    """
    Audio capture configuration.

    Optimized for Whisper.cpp requirements:
    - 16kHz sample rate (Whisper native)
    - Mono channel
    - 16-bit samples
    """
    sample_rate: int = Field(
        default=16000,
        ge=8000,
        le=48000,
        description="Sample rate in Hz (Whisper prefers 16kHz)"
    )
    channels: int = Field(
        default=1,
        ge=1,
        le=2,
        description="Number of audio channels (1=mono, 2=stereo)"
    )
    chunk_size: int = Field(
        default=1024,
        ge=512,
        le=8192,
        description="Audio buffer chunk size in frames"
    )
    buffer_seconds: float = Field(
        default=30.0,
        gt=0.0,
        le=120.0,
        description="Max buffer duration before flush"
    )
    format: AudioFormat = Field(
        default=AudioFormat.WAV,
        description="Audio format for processing"
    )

    class Config:
        """Pydantic config."""
        use_enum_values = True


class AudioSegment(BaseModel):
    """
    A segment of captured audio.

    Memory-only representation (no disk writes for privacy).
    """
    data: bytes = Field(..., description="Raw audio data")
    sample_rate: int = Field(..., gt=0, description="Sample rate in Hz")
    channels: int = Field(..., ge=1, le=2, description="Number of channels")
    duration_seconds: float = Field(..., gt=0.0, description="Duration in seconds")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Capture timestamp"
    )
    has_speech: bool = Field(
        default=True,
        description="Voice Activity Detection result"
    )

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


class WhisperConfig(BaseModel):
    """
    Whisper.cpp configuration.

    Balances speed vs accuracy for real-time transcription.
    """
    model_path: str = Field(
        ...,
        description="Path to Whisper GGML model file"
    )
    model_name: str = Field(
        default="base",
        description="Model identifier (tiny, base, small, medium, large) - multilingual"
    )
    language: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="ISO 639-1 language code (None for auto-detection)"
    )
    use_gpu: bool = Field(
        default=True,
        description="Enable Metal GPU acceleration (M4 Pro)"
    )
    num_threads: int = Field(
        default=4,
        ge=1,
        le=16,
        description="CPU threads for inference"
    )
    beam_size: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Beam search size (higher=more accurate, slower)"
    )

    class Config:
        """Pydantic config."""
        frozen = True  # Immutable after creation


class TranscriptionSegment(BaseModel):
    """
    Word-level transcription segment with timestamps.

    Enables precise alignment of text to audio timeline.
    """
    text: str = Field(..., min_length=1, description="Transcribed text")
    start_time: float = Field(..., ge=0.0, description="Start time in seconds")
    end_time: float = Field(..., gt=0.0, description="End time in seconds")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from Whisper"
    )

    class Config:
        """Pydantic config."""
        frozen = True


class TranscriptionResult(BaseModel):
    """
    Complete transcription result from Whisper.

    Includes full text, confidence, language, and optional
    word-level timestamps for advanced processing.
    """
    text: str = Field(..., description="Full transcription text")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score"
    )
    language: str = Field(..., description="Detected language")
    duration_seconds: float = Field(
        ...,
        gt=0.0,
        description="Audio duration in seconds"
    )
    timestamp: str = Field(
        ...,
        description="ISO8601 timestamp of transcription"
    )
    segments: Optional[List[TranscriptionSegment]] = Field(
        default=None,
        description="Word-level timestamps (optional)"
    )

    class Config:
        """Pydantic config."""
        frozen = True


class VADResult(BaseModel):
    """
    Voice Activity Detection result.

    Determines if audio segment contains speech.
    """
    has_speech: bool = Field(..., description="Speech detected")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="VAD confidence"
    )
    rms_level: float = Field(
        ...,
        ge=0.0,
        description="RMS audio level (signal strength)"
    )

    class Config:
        """Pydantic config."""
        frozen = True


class AudioCaptureStats(BaseModel):
    """
    Statistics from audio capture session.

    Used for monitoring and performance tuning.
    """
    total_duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total audio captured"
    )
    speech_duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Duration with detected speech"
    )
    silence_duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Duration of silence"
    )
    segments_captured: int = Field(
        default=0,
        ge=0,
        description="Number of audio segments"
    )
    segments_transcribed: int = Field(
        default=0,
        ge=0,
        description="Number of segments sent to Whisper"
    )
    average_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average transcription confidence"
    )

    class Config:
        """Pydantic config."""
        validate_assignment = True
