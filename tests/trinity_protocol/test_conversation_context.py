"""
Tests for Conversation Context Manager.

Validates rolling window management, topic tracking, and segmentation.

Constitutional Compliance:
- Article II: 100% test coverage
- TDD approach
"""

import pytest
from datetime import datetime, timedelta
from trinity_protocol.experimental.conversation_context import ConversationContext, TranscriptEntry


@pytest.fixture
def context():
    """Create conversation context for testing."""
    return ConversationContext(
        window_minutes=10.0,
        max_entries=100,
        silence_threshold_seconds=120.0
    )


class TestTranscriptionManagement:
    """Test transcription entry management."""

    def test_add_transcription(self, context):
        """Should add transcription to context."""
        text = "Hello world"
        timestamp = datetime.now()
        confidence = 0.95

        context.add_transcription(text, timestamp, confidence)

        entries = context.get_recent_entries()
        assert len(entries) == 1
        assert entries[0].text == text
        assert entries[0].confidence == confidence

    def test_rolling_window_cleanup(self, context):
        """Should remove entries outside time window."""
        now = datetime.now()

        # Add old entry (15 minutes ago, outside 10-minute window)
        old_time = now - timedelta(minutes=15)
        context.add_transcription("Old text", old_time, 0.9)

        # Add current entry
        context.add_transcription("New text", now, 0.9)

        # Only current entry should remain
        entries = context.get_recent_entries()
        assert len(entries) == 1
        assert entries[0].text == "New text"

    def test_max_entries_limit(self, context):
        """Should respect max entries limit."""
        context_small = ConversationContext(
            window_minutes=10.0,
            max_entries=5,  # Small limit
            silence_threshold_seconds=120.0
        )

        now = datetime.now()

        # Add 10 entries
        for i in range(10):
            timestamp = now + timedelta(seconds=i)
            context_small.add_transcription(f"Text {i}", timestamp, 0.9)

        # Should only keep last 5
        entries = context_small.get_recent_entries()
        assert len(entries) == 5
        assert entries[-1].text == "Text 9"


class TestConversationSegmentation:
    """Test conversation boundary detection."""

    def test_new_conversation_after_silence(self, context):
        """Should start new conversation after long silence."""
        now = datetime.now()

        # First transcription
        context.add_transcription("First", now, 0.9)
        first_conv_id = context.conversation_id

        # Long silence (3 minutes, exceeds 2-minute threshold)
        later = now + timedelta(minutes=3)
        context.add_transcription("Second", later, 0.9)
        second_conv_id = context.conversation_id

        # Should have different conversation IDs
        assert first_conv_id != second_conv_id

    def test_same_conversation_within_threshold(self, context):
        """Should maintain conversation within silence threshold."""
        now = datetime.now()

        # First transcription
        context.add_transcription("First", now, 0.9)
        first_conv_id = context.conversation_id

        # Short silence (1 minute, within 2-minute threshold)
        soon = now + timedelta(minutes=1)
        context.add_transcription("Second", soon, 0.9)
        second_conv_id = context.conversation_id

        # Should have same conversation ID
        assert first_conv_id == second_conv_id

    def test_conversation_id_generation(self, context):
        """Should generate unique conversation IDs."""
        now = datetime.now()

        context.add_transcription("Test", now, 0.9)
        conv_id = context.conversation_id

        assert conv_id is not None
        assert conv_id.startswith("conv_")
        assert len(conv_id) > 10  # Should have hash component


class TestTextRetrieval:
    """Test text retrieval methods."""

    def test_get_recent_text(self, context):
        """Should concatenate recent text."""
        now = datetime.now()

        texts = ["Hello", "world", "from", "ambient"]
        for i, text in enumerate(texts):
            timestamp = now + timedelta(seconds=i)
            context.add_transcription(text, timestamp, 0.9)

        recent = context.get_recent_text()
        assert recent == "Hello world from ambient"

    def test_get_recent_text_with_time_window(self, context):
        """Should filter by time window."""
        now = datetime.now()

        # Add entries at different times
        context.add_transcription("Old", now - timedelta(minutes=5), 0.9)
        context.add_transcription("Recent", now - timedelta(minutes=1), 0.9)
        context.add_transcription("Current", now, 0.9)

        # Get only last 2 minutes
        recent = context.get_recent_text(last_n_minutes=2.0)

        assert "Old" not in recent
        assert "Recent" in recent
        assert "Current" in recent

    def test_get_recent_entries_with_filter(self, context):
        """Should filter entries by time."""
        now = datetime.now()

        # Add entries across time range
        for i in range(5):
            timestamp = now - timedelta(minutes=i)
            context.add_transcription(f"Text {i}", timestamp, 0.9)

        # Get last 2 minutes
        entries = context.get_recent_entries(last_n_minutes=2.0)

        # Should only get entries from last 2 minutes
        assert len(entries) <= 3  # 0, 1, 2 minutes ago


class TestTopicTracking:
    """Test topic mention tracking."""

    def test_track_topic_mention(self, context):
        """Should track topic mentions."""
        topic = "book for coaches"
        now = datetime.now()

        context.track_topic_mention(topic, now)

        count = context.get_topic_mention_count(topic)
        assert count == 1

    def test_multiple_topic_mentions(self, context):
        """Should count multiple mentions."""
        topic = "project x"
        now = datetime.now()

        # Add 3 mentions
        for i in range(3):
            timestamp = now + timedelta(minutes=i)
            context.track_topic_mention(topic, timestamp)

        count = context.get_topic_mention_count(topic)
        assert count == 3

    def test_topic_case_insensitive(self, context):
        """Should treat topics case-insensitively."""
        now = datetime.now()

        context.track_topic_mention("Book", now)
        context.track_topic_mention("book", now + timedelta(seconds=1))
        context.track_topic_mention("BOOK", now + timedelta(seconds=2))

        count = context.get_topic_mention_count("book")
        assert count == 3

    def test_topic_mention_time_window(self, context):
        """Should filter topic mentions by time window."""
        topic = "feature"
        now = datetime.now()

        # Add old mention
        context.track_topic_mention(topic, now - timedelta(minutes=15))

        # Add recent mentions
        context.track_topic_mention(topic, now - timedelta(minutes=1))
        context.track_topic_mention(topic, now)

        # Get count for last 5 minutes
        count = context.get_topic_mention_count(topic, time_window_minutes=5.0)
        assert count == 2  # Only recent mentions


class TestTopicClustering:
    """Test topic cluster generation."""

    def test_get_topic_cluster(self, context):
        """Should create topic cluster from mentions."""
        topic = "daily standup"
        now = datetime.now()

        # Add multiple mentions
        for i in range(5):
            timestamp = now + timedelta(hours=i)
            context.track_topic_mention(topic, timestamp)

        cluster = context.get_topic_cluster(topic, time_window_hours=24.0)

        assert cluster is not None
        assert cluster.central_topic == topic
        assert cluster.mention_count == 5
        assert cluster.recurrence_score > 0.0

    def test_no_cluster_without_mentions(self, context):
        """Should return None for topic without mentions."""
        cluster = context.get_topic_cluster("nonexistent topic")
        assert cluster is None

    def test_cluster_time_window(self, context):
        """Should respect time window for clustering."""
        topic = "meeting"
        now = datetime.now()

        # Add old mentions (outside window)
        for i in range(3):
            timestamp = now - timedelta(hours=48 + i)
            context.track_topic_mention(topic, timestamp)

        # Add recent mention
        context.track_topic_mention(topic, now)

        # Get cluster for last 24 hours
        cluster = context.get_topic_cluster(topic, time_window_hours=24.0)

        assert cluster is not None
        # Should only include recent mention
        assert cluster.mention_count == 1


class TestConversationMetrics:
    """Test conversation metric calculations."""

    def test_conversation_duration(self, context):
        """Should calculate conversation duration."""
        now = datetime.now()

        # Add transcriptions within silence threshold (not starting new conversation)
        context.add_transcription("Start", now, 0.9)
        # Add second transcription within 2 minutes (silence threshold)
        context.add_transcription("End", now + timedelta(seconds=60), 0.9)

        duration = context.get_conversation_duration()
        assert duration == pytest.approx(1.0, rel=0.1)  # 60 seconds = 1 minute

    def test_speaker_count_without_ids(self, context):
        """Should return 1 speaker when no IDs provided."""
        now = datetime.now()

        context.add_transcription("Text 1", now, 0.9)
        context.add_transcription("Text 2", now + timedelta(seconds=1), 0.9)

        speaker_count = context.get_speaker_count()
        assert speaker_count == 1

    def test_speaker_count_with_ids(self, context):
        """Should count distinct speakers."""
        now = datetime.now()

        context.add_transcription("Text 1", now, 0.9, speaker_id="speaker_1")
        context.add_transcription("Text 2", now + timedelta(seconds=1), 0.9, speaker_id="speaker_2")
        context.add_transcription("Text 3", now + timedelta(seconds=2), 0.9, speaker_id="speaker_1")

        speaker_count = context.get_speaker_count()
        assert speaker_count == 2

    def test_average_confidence(self, context):
        """Should calculate average confidence."""
        now = datetime.now()

        context.add_transcription("Text 1", now, 0.8)
        context.add_transcription("Text 2", now + timedelta(seconds=1), 0.9)
        context.add_transcription("Text 3", now + timedelta(seconds=2), 1.0)

        avg_confidence = context.get_average_confidence()
        assert avg_confidence == pytest.approx(0.9, rel=0.01)

    def test_context_summary(self, context):
        """Should generate context summary."""
        now = datetime.now()

        long_text = "This is a very long text " * 50  # Exceeds 500 chars
        context.add_transcription(long_text, now, 0.9)

        summary = context.get_context_summary(max_length=100)

        assert len(summary) <= 100
        assert summary.endswith("...")  # Truncated

    def test_short_context_summary(self, context):
        """Should not truncate short summaries."""
        now = datetime.now()

        short_text = "Short text"
        context.add_transcription(short_text, now, 0.9)

        summary = context.get_context_summary(max_length=500)

        assert summary == short_text
        assert not summary.endswith("...")


class TestContextReset:
    """Test context reset functionality."""

    def test_reset_clears_all_data(self, context):
        """Should clear all data on reset."""
        now = datetime.now()

        # Add data
        context.add_transcription("Test", now, 0.9)
        context.track_topic_mention("topic", now)

        # Reset
        context.reset()

        # Verify cleared
        assert len(context.get_recent_entries()) == 0
        assert context.conversation_id is None
        assert context.conversation_start is None
        assert context.last_activity is None
        assert context.get_topic_mention_count("topic") == 0


class TestStatistics:
    """Test statistics generation."""

    def test_get_stats(self, context):
        """Should return comprehensive statistics."""
        now = datetime.now()

        context.add_transcription("Test", now, 0.95)
        context.track_topic_mention("topic", now)

        stats = context.get_stats()

        assert "conversation_id" in stats
        assert "entry_count" in stats
        assert "speaker_count" in stats
        assert "average_confidence" in stats
        assert "tracked_topics" in stats
        assert stats["entry_count"] == 1
        assert stats["tracked_topics"] == 1
        assert stats["average_confidence"] == 0.95
