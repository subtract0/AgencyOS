"""Tests for Trinity Ambient Listener Service.

Constitutional Compliance:
- Article I: Complete context before action (full test coverage)
- Article II: Strict typing with Pydantic models
- TDD: Tests written before implementation
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from trinity_protocol.ambient_listener_service import (
    AmbientListenerService,
    AmbientListenerConfig,
    ServiceStatus,
)
from trinity_protocol.experimental.models.audio import (
    AudioConfig,
    AudioSegment,
    TranscriptionResult,
    WhisperConfig,
)
from trinity_protocol.core.models.patterns import DetectedPattern, PatternType
from shared.type_definitions.result import Result, Ok, Err


class TestAmbientListenerConfig:
    """Test suite for AmbientListenerConfig model."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = AmbientListenerConfig()

        assert config.model_name == "base.en"
        assert config.min_confidence == 0.6
        assert config.chunk_duration == 3.0
        assert config.silence_threshold == 500.0
        assert config.pattern_check_interval == 30.0

    def test_config_custom_values(self):
        """Test custom configuration values."""
        config = AmbientListenerConfig(
            model_name="tiny.en",
            min_confidence=0.7,
            chunk_duration=5.0,
            silence_threshold=300.0,
            pattern_check_interval=60.0,
        )

        assert config.model_name == "tiny.en"
        assert config.min_confidence == 0.7
        assert config.chunk_duration == 5.0
        assert config.silence_threshold == 300.0
        assert config.pattern_check_interval == 60.0

    def test_config_validation_min_confidence(self):
        """Test min_confidence validation (must be 0.0-1.0)."""
        with pytest.raises(ValueError):
            AmbientListenerConfig(min_confidence=1.5)

        with pytest.raises(ValueError):
            AmbientListenerConfig(min_confidence=-0.1)

    def test_config_validation_chunk_duration(self):
        """Test chunk_duration validation (must be > 0)."""
        with pytest.raises(ValueError):
            AmbientListenerConfig(chunk_duration=0.0)

        with pytest.raises(ValueError):
            AmbientListenerConfig(chunk_duration=-1.0)


class TestServiceStatus:
    """Test suite for ServiceStatus enum."""

    def test_status_enum_values(self):
        """Test all status enum values exist."""
        assert ServiceStatus.STOPPED == "stopped"
        assert ServiceStatus.STARTING == "starting"
        assert ServiceStatus.RUNNING == "running"
        assert ServiceStatus.ERROR == "error"


class TestAmbientListenerService:
    """Test suite for AmbientListenerService."""

    @pytest.fixture
    def mock_audio_capture(self):
        """Mock AudioCaptureModule."""
        mock = AsyncMock()
        mock.start = AsyncMock(return_value=Ok(None))
        mock.stop = AsyncMock()
        mock.is_running = False
        return mock

    @pytest.fixture
    def mock_transcriber(self):
        """Mock WhisperTranscriber."""
        mock = AsyncMock()
        mock.start = AsyncMock(return_value=Ok(None))
        mock.stop = AsyncMock()
        mock.is_running = False
        return mock

    @pytest.fixture
    def mock_pattern_detector(self):
        """Mock AmbientPatternDetector."""
        mock = Mock()
        mock.detect_patterns = Mock(return_value=[])
        return mock

    @pytest.fixture
    def mock_conversation_context(self):
        """Mock ConversationContext."""
        mock = Mock()
        mock.add_transcription = Mock()
        mock.get_recent_text = Mock(return_value="")
        return mock

    @pytest.fixture
    def service(
        self,
        mock_audio_capture,
        mock_transcriber,
        mock_pattern_detector,
        mock_conversation_context,
    ):
        """Create AmbientListenerService with mocked dependencies."""
        return AmbientListenerService(
            audio_capture=mock_audio_capture,
            transcriber=mock_transcriber,
            pattern_detector=mock_pattern_detector,
            conversation_context=mock_conversation_context,
        )

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initializes with correct default state."""
        assert service.status == ServiceStatus.STOPPED
        assert service.config.model_name == "base.en"
        assert service.config.min_confidence == 0.6

    @pytest.mark.asyncio
    async def test_start_service_success(
        self, service, mock_audio_capture, mock_transcriber
    ):
        """Test successful service startup."""
        result = await service.start()

        assert isinstance(result, Ok)
        assert service.status == ServiceStatus.RUNNING
        mock_audio_capture.start.assert_called_once()
        mock_transcriber.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_service_already_running(self, service):
        """Test starting service when already running."""
        service.status = ServiceStatus.RUNNING

        result = await service.start()

        assert isinstance(result, Err)
        assert "already running" in result.unwrap_err().lower()

    @pytest.mark.asyncio
    async def test_start_service_audio_capture_failure(
        self, service, mock_audio_capture
    ):
        """Test service startup when audio capture fails."""
        mock_audio_capture.start = AsyncMock(
            return_value=Err("PyAudio not installed")
        )

        result = await service.start()

        assert isinstance(result, Err)
        assert "PyAudio not installed" in result.unwrap_err()
        assert service.status == ServiceStatus.ERROR

    @pytest.mark.asyncio
    async def test_start_service_transcriber_failure(
        self, service, mock_transcriber
    ):
        """Test service startup when transcriber fails."""
        mock_transcriber.start = AsyncMock(
            return_value=Err("Whisper model not found")
        )

        result = await service.start()

        assert isinstance(result, Err)
        assert "Whisper model not found" in result.unwrap_err()
        assert service.status == ServiceStatus.ERROR

    @pytest.mark.asyncio
    async def test_stop_service(
        self, service, mock_audio_capture, mock_transcriber
    ):
        """Test service shutdown."""
        service.status = ServiceStatus.RUNNING
        service._running = True

        await service.stop()

        assert service.status == ServiceStatus.STOPPED
        assert not service._running
        mock_audio_capture.stop.assert_called_once()
        mock_transcriber.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_service_not_running(self, service):
        """Test stopping service when not running."""
        service.status = ServiceStatus.STOPPED

        await service.stop()

        # Should not raise error, just no-op
        assert service.status == ServiceStatus.STOPPED

    @pytest.mark.asyncio
    async def test_process_audio_chunk_with_speech(
        self,
        service,
        mock_transcriber,
        mock_conversation_context,
        mock_pattern_detector,
    ):
        """Test processing audio chunk containing speech."""
        # Create audio segment with speech
        audio_segment = AudioSegment(
            data=b"fake_audio_data",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=True,
        )

        # Mock transcription result
        transcription = TranscriptionResult(
            text="Hello world",
            confidence=0.85,
            language="en",
            duration_seconds=3.0,
            timestamp=datetime.now().isoformat(),
        )
        mock_transcriber.transcribe_segment = AsyncMock(
            return_value=Ok(transcription)
        )

        # Mock pattern detection
        pattern = DetectedPattern(
            pattern_id="test_pattern_1",
            pattern_type=PatternType.ACTION_ITEM,
            topic="test",
            confidence=0.8,
            mention_count=1,
            first_mention=datetime.now(),
            last_mention=datetime.now(),
            context_summary="Test context",
            keywords=["test"],
            urgency="MEDIUM",
        )
        mock_pattern_detector.detect_patterns.return_value = [pattern]

        result = await service._process_audio_chunk(audio_segment)

        assert isinstance(result, Ok)
        mock_transcriber.transcribe_segment.assert_called_once_with(
            audio_segment
        )
        mock_conversation_context.add_transcription.assert_called_once()
        mock_pattern_detector.detect_patterns.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_audio_chunk_no_speech(self, service):
        """Test processing audio chunk with no speech detected."""
        audio_segment = AudioSegment(
            data=b"silence",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=False,
        )

        result = await service._process_audio_chunk(audio_segment)

        assert isinstance(result, Ok)
        assert result.unwrap() is None  # Should skip transcription

    @pytest.mark.asyncio
    async def test_process_audio_chunk_low_confidence(
        self, service, mock_transcriber, mock_conversation_context
    ):
        """Test processing audio with transcription below confidence threshold."""
        audio_segment = AudioSegment(
            data=b"unclear_audio",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=True,
        )

        # Low confidence transcription
        transcription = TranscriptionResult(
            text="unclear",
            confidence=0.4,  # Below default threshold of 0.6
            language="en",
            duration_seconds=3.0,
            timestamp=datetime.now().isoformat(),
        )
        mock_transcriber.transcribe_segment = AsyncMock(
            return_value=Ok(transcription)
        )

        result = await service._process_audio_chunk(audio_segment)

        assert isinstance(result, Ok)
        # Should not add to conversation context (low confidence)
        mock_conversation_context.add_transcription.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_audio_chunk_transcription_failure(
        self, service, mock_transcriber
    ):
        """Test handling transcription failure."""
        audio_segment = AudioSegment(
            data=b"audio",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=True,
        )

        mock_transcriber.transcribe_segment = AsyncMock(
            return_value=Err("Transcription failed")
        )

        result = await service._process_audio_chunk(audio_segment)

        assert isinstance(result, Err)
        assert "Transcription failed" in result.unwrap_err()

    @pytest.mark.asyncio
    async def test_handle_detected_patterns(self, service, mock_pattern_detector):
        """Test handling detected patterns."""
        pattern = DetectedPattern(
            pattern_id="test_pattern",
            pattern_type=PatternType.RECURRING_TOPIC,
            topic="project",
            confidence=0.9,
            mention_count=3,
            first_mention=datetime.now(),
            last_mention=datetime.now(),
            context_summary="User mentioned project 3 times",
            keywords=["project", "build", "create"],
            urgency="MEDIUM",
        )

        # Should log pattern and persist
        with patch("trinity_protocol.ambient_listener_service.logger") as mock_logger:
            await service._handle_detected_patterns([pattern])
            mock_logger.info.assert_called()
            mock_pattern_detector.persist_pattern.assert_called_once_with(pattern)

    def test_get_stats(self, service, mock_conversation_context, mock_audio_capture):
        """Test getting service statistics."""
        from trinity_protocol.experimental.models.audio import AudioCaptureStats

        mock_conversation_context.get_stats.return_value = {
            "entry_count": 10,
            "duration_minutes": 5.0,
        }

        # Mock audio capture stats
        mock_stats = AudioCaptureStats(
            total_duration_seconds=100.0,
            speech_duration_seconds=60.0,
            silence_duration_seconds=40.0,
            segments_captured=20,
        )
        mock_audio_capture.get_stats = Mock(return_value=mock_stats)

        stats = service.get_stats()

        assert stats["status"] == ServiceStatus.STOPPED
        assert "conversation_stats" in stats
        assert stats["conversation_stats"]["entry_count"] == 10

    def test_create_audio_config(self):
        """Test creating AudioConfig from service config."""
        service_config = AmbientListenerConfig(silence_threshold=400.0)

        audio_config = AmbientListenerService._create_audio_config(
            service_config
        )

        assert isinstance(audio_config, AudioConfig)
        assert audio_config.sample_rate == 16000
        assert audio_config.channels == 1

    def test_create_whisper_config(self):
        """Test creating WhisperConfig from service config."""
        service_config = AmbientListenerConfig(model_name="tiny.en")

        whisper_config = AmbientListenerService._create_whisper_config(
            service_config
        )

        assert isinstance(whisper_config, WhisperConfig)
        assert whisper_config.model_name == "tiny.en"
        assert whisper_config.language == "en"


class TestAmbientListenerServiceIntegration:
    """Integration tests for full audio pipeline (mocked components)."""

    @pytest.mark.asyncio
    async def test_full_pipeline_integration(self):
        """Test complete pipeline: capture -> transcribe -> detect -> handle."""
        # Create mocks
        mock_audio = AsyncMock()
        mock_audio.start = AsyncMock(return_value=Ok(None))
        mock_audio.stop = AsyncMock()
        mock_audio.capture_stream = AsyncMock()

        # Create audio segment stream
        audio_segment = AudioSegment(
            data=b"test_audio",
            sample_rate=16000,
            channels=1,
            duration_seconds=3.0,
            timestamp=datetime.now(),
            has_speech=True,
        )

        async def mock_stream():
            yield audio_segment
            # Stop after one chunk
            await asyncio.sleep(0.1)

        mock_audio.capture_stream.return_value = mock_stream()

        mock_transcriber = AsyncMock()
        mock_transcriber.start = AsyncMock(return_value=Ok(None))
        mock_transcriber.stop = AsyncMock()
        mock_transcriber.transcribe_segment = AsyncMock(
            return_value=Ok(
                TranscriptionResult(
                    text="Integration test",
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
        mock_context.get_recent_text = Mock(return_value="Integration test")

        # Create service
        service = AmbientListenerService(
            audio_capture=mock_audio,
            transcriber=mock_transcriber,
            pattern_detector=mock_detector,
            conversation_context=mock_context,
        )

        # Start service
        result = await service.start()
        assert isinstance(result, Ok)

        # Run for short duration
        await asyncio.sleep(0.2)

        # Stop service
        await service.stop()

        assert service.status == ServiceStatus.STOPPED


class TestCLIArgumentParsing:
    """Test suite for CLI argument parsing."""

    def test_parse_args_defaults(self):
        """Test default CLI arguments."""
        from trinity_protocol.ambient_listener_service import parse_args

        args = parse_args(["--model", "base.en"])

        assert args.model == "base.en"
        assert args.min_confidence == 0.6
        assert args.chunk_duration == 3.0

    def test_parse_args_custom(self):
        """Test custom CLI arguments."""
        from trinity_protocol.ambient_listener_service import parse_args

        args = parse_args([
            "--model", "tiny.en",
            "--min-confidence", "0.7",
            "--chunk-duration", "5.0",
            "--silence-threshold", "400.0",
        ])

        assert args.model == "tiny.en"
        assert args.min_confidence == 0.7
        assert args.chunk_duration == 5.0
        assert args.silence_threshold == 400.0
