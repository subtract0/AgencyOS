"""
Trinity Protocol Experimental Models - Research & Prototypes

WARNING: Experimental models may change without notice.
Do NOT use in production agents.

These models are for research, testing, and prototype development.
They may lack comprehensive validation or documentation.
"""

from trinity_protocol.experimental.models.audio import (
    AudioFormat,
    AudioConfig,
    AudioSegment,
    WhisperConfig,
    TranscriptionSegment,
    TranscriptionResult,
    VADResult,
    AudioCaptureStats,
)

__all__ = [
    "AudioFormat",
    "AudioConfig",
    "AudioSegment",
    "WhisperConfig",
    "TranscriptionSegment",
    "TranscriptionResult",
    "VADResult",
    "AudioCaptureStats",
]
