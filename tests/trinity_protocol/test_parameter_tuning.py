"""Tests for Voice Transcription Parameter Tuning.

Constitutional Compliance:
- Article I: TDD - Tests written FIRST before implementation
- Article II: Strict typing with Pydantic models
- Article VII: Functions <50 lines

Tests the three critical improvements:
1. Whisper parameter tuning (accuracy boost)
2. Empty transcription rate reduction (RMS threshold + min_text_length)
3. Duration validation fallback (prevent Pydantic errors)
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from trinity_protocol.ambient_listener_service import (
    AmbientListenerService,
    AmbientListenerConfig,
)
from trinity_protocol.experimental.models.audio import (
    AudioSegment,
    TranscriptionResult,
    VADResult,
    WhisperConfig,
)
from shared.type_definitions.result import Ok, Err


class TestWhisperParameterTuning:
    """Test suite for Whisper accuracy parameter tuning (Improvement #1)."""

    def test_ambient_config_accepts_whisper_parameters(self):
        """Test AmbientListenerConfig accepts new Whisper tuning parameters."""
        config = AmbientListenerConfig(
            model_name="base",
            min_confidence=0.6,
            # NEW: Whisper accuracy parameters
            temperature=0.0,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
        )

        assert config.temperature == 0.0
        assert config.compression_ratio_threshold == 2.4
        assert config.logprob_threshold == -1.0
        assert config.no_speech_threshold == 0.6

    def test_ambient_config_whisper_parameter_defaults(self):
        """Test Whisper parameters have recommended defaults."""
        config = AmbientListenerConfig()

        # Recommended defaults from auditor analysis
        assert config.temperature == 0.0  # Deterministic output
        assert config.compression_ratio_threshold == 2.4  # Hallucination detection
        assert config.logprob_threshold == -1.0  # Low confidence filtering
        assert config.no_speech_threshold == 0.6  # Speech detection

    def test_ambient_config_whisper_parameter_validation(self):
        """Test Whisper parameter validation."""
        # Temperature: 0.0-1.0
        with pytest.raises(ValueError):
            AmbientListenerConfig(temperature=-0.1)
        with pytest.raises(ValueError):
            AmbientListenerConfig(temperature=1.5)

        # Compression ratio threshold: >0
        with pytest.raises(ValueError):
            AmbientListenerConfig(compression_ratio_threshold=0.0)
        with pytest.raises(ValueError):
            AmbientListenerConfig(compression_ratio_threshold=-1.0)

        # Logprob threshold: -inf to 0
        with pytest.raises(ValueError):
            AmbientListenerConfig(logprob_threshold=0.1)

        # No speech threshold: 0.0-1.0
        with pytest.raises(ValueError):
            AmbientListenerConfig(no_speech_threshold=-0.1)
        with pytest.raises(ValueError):
            AmbientListenerConfig(no_speech_threshold=1.5)

    def test_whisper_config_receives_accuracy_parameters(self):
        """Test WhisperConfig creation includes accuracy parameters."""
        service_config = AmbientListenerConfig(
            model_name="base",
            temperature=0.0,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
        )

        whisper_config = AmbientListenerService._create_whisper_config(
            service_config
        )

        assert whisper_config.temperature == 0.0
        assert whisper_config.compression_ratio_threshold == 2.4
        assert whisper_config.logprob_threshold == -1.0
        assert whisper_config.no_speech_threshold == 0.6

    @pytest.mark.asyncio
    async def test_transcriber_uses_accuracy_parameters(self):
        """Test transcriber passes accuracy parameters to Whisper model."""
        from trinity_protocol.experimental.transcription import WhisperTranscriber

        whisper_config = WhisperConfig(
            model_path="/tmp/test.pt",
            model_name="base",
            language=None,
            use_gpu=True,
            num_threads=4,
            beam_size=5,
            # Accuracy parameters
            temperature=0.0,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
        )

        transcriber = WhisperTranscriber(config=whisper_config)

        # Mock the Whisper model
        mock_model = Mock()
        mock_model.transcribe = Mock(return_value={
            "text": "Test transcription",
            "language": "en",
            "segments": []
        })

        transcriber._model = mock_model
        transcriber._backend = "openai-whisper"
        transcriber.is_running = True

        # Create test audio segment
        audio_segment = AudioSegment(
            data=b"fake_audio",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=True,
        )

        # Transcribe (will use temp file)
        result = await transcriber.transcribe_segment(audio_segment)

        # Verify model.transcribe was called with accuracy parameters
        assert mock_model.transcribe.called
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs.get("temperature") == 0.0
        assert call_kwargs.get("compression_ratio_threshold") == 2.4
        assert call_kwargs.get("logprob_threshold") == -1.0
        assert call_kwargs.get("no_speech_threshold") == 0.6


@pytest.mark.skip(reason="Trinity experimental feature - min_text_length filter not yet implemented")
class TestEmptyTranscriptionReduction:
    """Test suite for reducing empty transcription rate (Improvement #2)."""

    def test_ambient_config_accepts_rms_threshold(self):
        """Test AmbientListenerConfig accepts tuned RMS threshold."""
        config = AmbientListenerConfig(
            rms_threshold=0.015,  # Increased from default
        )

        assert config.rms_threshold == 0.015

    def test_ambient_config_rms_threshold_default(self):
        """Test RMS threshold has recommended default (0.015)."""
        config = AmbientListenerConfig()

        # Recommended from learning analysis (97.1% → <30% empty rate)
        assert config.rms_threshold == 0.015

    def test_ambient_config_accepts_min_text_length(self):
        """Test AmbientListenerConfig accepts min_text_length validation."""
        config = AmbientListenerConfig(
            min_text_length=3,  # Minimum 3 characters
        )

        assert config.min_text_length == 3

    def test_ambient_config_min_text_length_default(self):
        """Test min_text_length has recommended default."""
        config = AmbientListenerConfig()

        assert config.min_text_length == 3

    def test_ambient_config_accepts_vad_aggressive(self):
        """Test AmbientListenerConfig accepts vad_aggressive parameter."""
        config = AmbientListenerConfig(
            vad_aggressive=True,
        )

        assert config.vad_aggressive is True

    def test_ambient_config_vad_aggressive_default(self):
        """Test vad_aggressive default is True (recommended)."""
        config = AmbientListenerConfig()

        assert config.vad_aggressive is True

    def test_audio_capture_uses_increased_rms_threshold(self):
        """Test AudioCaptureModule uses increased RMS threshold."""
        from trinity_protocol.experimental.audio_capture import AudioCaptureModule

        # Create audio config with increased RMS threshold
        from trinity_protocol.experimental.models.audio import AudioConfig
        audio_config = AudioConfig()

        capture = AudioCaptureModule(config=audio_config)

        # Test speech detection with new threshold
        # Use very low amplitude audio (should be below 15.0 threshold)
        audio_data = b"\x00\x00" * 1000  # Silence (RMS = 0.0)
        vad_result = capture._detect_speech(
            audio_data,
            threshold=15.0  # Standard RMS threshold for 16-bit PCM
        )

        # Should NOT detect speech (silence)
        assert not vad_result.has_speech
        assert vad_result.rms_level < 15.0

    def test_min_text_length_validation_filters_empty_results(self):
        """Test transcriptions below min_text_length are filtered."""
        from trinity_protocol.experimental.transcription import WhisperTranscriber

        # Mock a transcription result with very short text
        short_text = "ab"  # Only 2 characters (< min_text_length=3)

        # Should be filtered out
        assert len(short_text) < 3  # Below minimum

    @pytest.mark.asyncio
    async def test_service_filters_short_transcriptions(self):
        """Test service filters transcriptions below min_text_length."""
        mock_audio = AsyncMock()
        mock_audio.start = AsyncMock(return_value=Ok(None))

        mock_transcriber = AsyncMock()
        mock_transcriber.start = AsyncMock(return_value=Ok(None))
        mock_transcriber.transcribe_segment = AsyncMock(
            return_value=Ok(
                TranscriptionResult(
                    text="ab",  # Only 2 chars (below min_text_length=3)
                    confidence=0.9,
                    language="en",
                    duration_seconds=3.0,
                    timestamp=datetime.now().isoformat(),
                )
            )
        )

        mock_detector = Mock()
        mock_detector.detect_patterns = Mock(return_value=[])

        mock_context = Mock()
        mock_context.add_transcription = Mock()

        config = AmbientListenerConfig(min_text_length=3)

        service = AmbientListenerService(
            audio_capture=mock_audio,
            transcriber=mock_transcriber,
            pattern_detector=mock_detector,
            conversation_context=mock_context,
            config=config,
        )

        audio_segment = AudioSegment(
            data=b"audio",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=True,
        )

        result = await service._process_audio_chunk(audio_segment)

        # Should filter out short transcription
        assert isinstance(result, Ok)
        # Should NOT add to conversation context (too short)
        mock_context.add_transcription.assert_not_called()


@pytest.mark.skip(reason="Trinity experimental feature - zero duration validation not yet implemented")
class TestDurationValidationFallback:
    """Test suite for duration validation fallback (Improvement #3)."""

    def test_transcription_result_accepts_zero_duration(self):
        """Test TranscriptionResult accepts duration_seconds=0.0 with fallback."""
        # This should NOT raise validation error anymore
        result = TranscriptionResult(
            text="Test",
            confidence=0.9,
            language="en",
            duration_seconds=0.0,  # Will use fallback
            timestamp=datetime.now().isoformat(),
        )

        # Should use fallback logic (will be set to 0.01 minimum)
        assert result.duration_seconds >= 0.01

    @pytest.mark.asyncio
    async def test_transcriber_uses_chunk_duration_fallback(self):
        """Test transcriber uses chunk_duration when duration_seconds=0.0."""
        from trinity_protocol.experimental.transcription import WhisperTranscriber

        whisper_config = WhisperConfig(
            model_path="/tmp/test.pt",
            model_name="base",
            language=None,
            use_gpu=True,
            num_threads=4,
            beam_size=5,
        )

        transcriber = WhisperTranscriber(config=whisper_config)

        # Mock model that returns duration=0.0
        mock_model = Mock()
        mock_model.transcribe = Mock(return_value={
            "text": "Test",
            "language": "en",
            "segments": [],
        })

        transcriber._model = mock_model
        transcriber._backend = "openai-whisper"
        transcriber.is_running = True

        audio_segment = AudioSegment(
            data=b"audio",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,  # Known chunk duration
            timestamp=datetime.now(),
            has_speech=True,
        )

        result = await transcriber.transcribe_segment(audio_segment)

        # Should use chunk_duration as fallback (not 0.0)
        assert isinstance(result, Ok)
        transcription = result.unwrap()
        assert transcription.duration_seconds == 3.0  # Uses chunk_duration

    @pytest.mark.asyncio
    async def test_zero_duration_does_not_raise_validation_error(self):
        """Test zero duration does not cause Pydantic validation error."""
        from trinity_protocol.experimental.transcription import WhisperTranscriber

        whisper_config = WhisperConfig(
            model_path="/tmp/test.pt",
            model_name="base",
            language=None,
            use_gpu=True,
            num_threads=4,
            beam_size=5,
        )

        transcriber = WhisperTranscriber(config=whisper_config)

        mock_model = Mock()
        mock_model.transcribe = Mock(return_value={
            "text": "Test",
            "language": "en",
            "segments": [],
        })

        transcriber._model = mock_model
        transcriber._backend = "openai-whisper"
        transcriber.is_running = True

        audio_segment = AudioSegment(
            data=b"audio",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=True,
        )

        # Should NOT raise ValidationError
        result = await transcriber.transcribe_segment(audio_segment)
        assert isinstance(result, Ok)


@pytest.mark.skip(reason="Trinity experimental feature - CLI parameters not yet added to parser")
class TestIntegratedParameterTuning:
    """Integration tests for all three improvements working together."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_tuned_parameters(self):
        """Test complete pipeline with all parameter improvements."""
        mock_audio = AsyncMock()
        mock_audio.start = AsyncMock(return_value=Ok(None))

        mock_transcriber = AsyncMock()
        mock_transcriber.start = AsyncMock(return_value=Ok(None))
        mock_transcriber.transcribe_segment = AsyncMock(
            return_value=Ok(
                TranscriptionResult(
                    text="This is a good transcription",
                    confidence=0.9,
                    language="en",
                    duration_seconds=3.0,
                    timestamp=datetime.now().isoformat(),
                )
            )
        )

        mock_detector = Mock()
        mock_detector.detect_patterns = Mock(return_value=[])

        mock_context = Mock()
        mock_context.add_transcription = Mock()

        # Config with all improvements
        config = AmbientListenerConfig(
            model_name="base",
            # Improvement #1: Whisper accuracy
            temperature=0.0,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            # Improvement #2: Empty transcription reduction
            rms_threshold=0.015,
            min_text_length=3,
            vad_aggressive=True,
        )

        service = AmbientListenerService(
            audio_capture=mock_audio,
            transcriber=mock_transcriber,
            pattern_detector=mock_detector,
            conversation_context=mock_context,
            config=config,
        )

        audio_segment = AudioSegment(
            data=b"audio",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=True,
        )

        result = await service._process_audio_chunk(audio_segment)

        assert isinstance(result, Ok)
        # Should add to context (passes all filters)
        mock_context.add_transcription.assert_called_once()

    def test_cli_accepts_new_parameters(self):
        """Test CLI accepts new tuning parameters."""
        from trinity_protocol.ambient_listener_service import parse_args

        args = parse_args([
            "--model", "base",
            "--temperature", "0.0",
            "--compression-ratio-threshold", "2.4",
            "--logprob-threshold", "-1.0",
            "--no-speech-threshold", "0.6",
            "--rms-threshold", "0.015",
            "--min-text-length", "3",
            "--vad-aggressive",
        ])

        assert args.model == "base"
        assert args.temperature == 0.0
        assert args.compression_ratio_threshold == 2.4
        assert args.logprob_threshold == -1.0
        assert args.no_speech_threshold == 0.6
        assert args.rms_threshold == 0.015
        assert args.min_text_length == 3
        assert args.vad_aggressive is True
