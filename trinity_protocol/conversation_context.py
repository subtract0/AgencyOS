"""
Conversation Context Manager for Ambient Intelligence.

Maintains rolling conversation window for topic tracking, segmentation,
and context-aware pattern detection.

Constitutional Compliance:
- Article I: Complete context before action (full conversation segments)
- Article II: Strict typing with Pydantic models
- Article IV: Persist context for cross-session learning
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
import hashlib

from trinity_protocol.models.patterns import TopicCluster


@dataclass
class TranscriptEntry:
    """Single transcript entry in conversation."""
    text: str
    timestamp: datetime
    confidence: float
    speaker_id: Optional[str] = None


class ConversationContext:
    """
    Manages rolling conversation window for ambient intelligence.

    Tracks recent transcriptions, detects conversation boundaries,
    and provides context for pattern detection.
    """

    def __init__(
        self,
        window_minutes: float = 10.0,
        max_entries: int = 100,
        silence_threshold_seconds: float = 120.0
    ):
        """
        Initialize conversation context manager.

        Args:
            window_minutes: Rolling window duration in minutes
            max_entries: Maximum transcript entries to keep
            silence_threshold_seconds: Silence duration that ends conversation
        """
        self.window_minutes = window_minutes
        self.max_entries = max_entries
        self.silence_threshold_seconds = silence_threshold_seconds

        # Rolling buffer of transcript entries
        self._entries: deque[TranscriptEntry] = deque(maxlen=max_entries)

        # Current conversation metadata
        self.conversation_id: Optional[str] = None
        self.conversation_start: Optional[datetime] = None
        self.last_activity: Optional[datetime] = None

        # Topic tracking
        self._topic_mentions: Dict[str, List[datetime]] = {}

    def add_transcription(
        self,
        text: str,
        timestamp: datetime,
        confidence: float,
        speaker_id: Optional[str] = None
    ) -> None:
        """
        Add transcription to conversation context.

        Automatically handles conversation segmentation based on
        silence detection and time windows.

        Args:
            text: Transcribed text
            timestamp: Transcription timestamp
            confidence: Whisper confidence score
            speaker_id: Optional speaker identifier
        """
        # Check if new conversation (after long silence)
        if self._should_start_new_conversation(timestamp):
            self._start_new_conversation(timestamp)

        # Add entry
        entry = TranscriptEntry(
            text=text,
            timestamp=timestamp,
            confidence=confidence,
            speaker_id=speaker_id
        )
        self._entries.append(entry)

        # Update activity tracking
        self.last_activity = timestamp

        # Clean old entries outside window
        self._clean_old_entries(timestamp)

    def _should_start_new_conversation(self, timestamp: datetime) -> bool:
        """Check if new conversation should start."""
        if self.last_activity is None:
            return True

        silence_duration = (timestamp - self.last_activity).total_seconds()
        return silence_duration >= self.silence_threshold_seconds

    def _start_new_conversation(self, timestamp: datetime) -> None:
        """Start new conversation segment."""
        # Generate conversation ID from timestamp
        self.conversation_id = self._generate_conversation_id(timestamp)
        self.conversation_start = timestamp
        self.last_activity = timestamp

        # Clear old entries when starting new conversation
        self._entries.clear()

    def _generate_conversation_id(self, timestamp: datetime) -> str:
        """Generate unique conversation ID."""
        timestamp_str = timestamp.isoformat()
        hash_obj = hashlib.sha256(timestamp_str.encode())
        return f"conv_{hash_obj.hexdigest()[:12]}"

    def _clean_old_entries(self, current_time: datetime) -> None:
        """Remove entries outside rolling window."""
        cutoff_time = current_time - timedelta(minutes=self.window_minutes)

        # Remove from left (oldest) until all entries are within window
        while self._entries and self._entries[0].timestamp < cutoff_time:
            self._entries.popleft()

    def get_recent_text(self, last_n_minutes: Optional[float] = None) -> str:
        """
        Get recent conversation text.

        Args:
            last_n_minutes: Optional time window (uses full window if None)

        Returns:
            Concatenated text from recent entries
        """
        if not self._entries:
            return ""

        if last_n_minutes is None:
            # Return all entries in window
            texts = [entry.text for entry in self._entries]
        else:
            # Filter by specific time window
            cutoff = datetime.now() - timedelta(minutes=last_n_minutes)
            texts = [
                entry.text
                for entry in self._entries
                if entry.timestamp >= cutoff
            ]

        return " ".join(texts)

    def get_recent_entries(
        self,
        last_n_minutes: Optional[float] = None
    ) -> List[TranscriptEntry]:
        """
        Get recent transcript entries.

        Args:
            last_n_minutes: Optional time window (uses full window if None)

        Returns:
            List of recent TranscriptEntry objects
        """
        if not self._entries:
            return []

        if last_n_minutes is None:
            return list(self._entries)

        cutoff = datetime.now() - timedelta(minutes=last_n_minutes)
        return [
            entry
            for entry in self._entries
            if entry.timestamp >= cutoff
        ]

    def track_topic_mention(self, topic: str, timestamp: datetime) -> None:
        """
        Track mention of a topic.

        Args:
            topic: Topic/keyword mentioned
            timestamp: When topic was mentioned
        """
        topic_key = topic.lower().strip()

        if topic_key not in self._topic_mentions:
            self._topic_mentions[topic_key] = []

        self._topic_mentions[topic_key].append(timestamp)

    def get_topic_mention_count(
        self,
        topic: str,
        time_window_minutes: Optional[float] = None
    ) -> int:
        """
        Get mention count for topic.

        Args:
            topic: Topic to check
            time_window_minutes: Optional time window (uses full window if None)

        Returns:
            Number of mentions in time window
        """
        topic_key = topic.lower().strip()

        if topic_key not in self._topic_mentions:
            return 0

        mentions = self._topic_mentions[topic_key]

        if time_window_minutes is None:
            return len(mentions)

        cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
        return sum(1 for ts in mentions if ts >= cutoff)

    def get_topic_cluster(
        self,
        topic: str,
        time_window_hours: float = 24.0
    ) -> Optional[TopicCluster]:
        """
        Get topic cluster for recurrence analysis.

        Args:
            topic: Central topic
            time_window_hours: Time window for clustering

        Returns:
            TopicCluster if topic has mentions, None otherwise
        """
        topic_key = topic.lower().strip()

        if topic_key not in self._topic_mentions:
            return None

        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        recent_mentions = [
            ts for ts in self._topic_mentions[topic_key]
            if ts >= cutoff
        ]

        if not recent_mentions:
            return None

        # Calculate recurrence score based on frequency
        mention_count = len(recent_mentions)
        recurrence_score = min(1.0, mention_count / 10.0)  # 10+ mentions = max score

        return TopicCluster(
            cluster_id=f"cluster_{topic_key}_{int(cutoff.timestamp())}",
            central_topic=topic,
            related_keywords=[topic_key],
            mention_timestamps=recent_mentions,
            recurrence_score=recurrence_score,
            time_window_hours=time_window_hours
        )

    def get_conversation_duration(self) -> float:
        """
        Get current conversation duration in minutes.

        Returns:
            Duration in minutes, or 0.0 if no conversation
        """
        if self.conversation_start is None or self.last_activity is None:
            return 0.0

        delta = self.last_activity - self.conversation_start
        return delta.total_seconds() / 60.0

    def get_speaker_count(self) -> int:
        """
        Get number of distinct speakers in current context.

        Returns:
            Number of unique speaker IDs (1 if no speaker IDs)
        """
        speaker_ids = {
            entry.speaker_id
            for entry in self._entries
            if entry.speaker_id is not None
        }

        return len(speaker_ids) if speaker_ids else 1

    def get_average_confidence(self) -> float:
        """
        Get average transcription confidence.

        Returns:
            Average confidence score, or 0.0 if no entries
        """
        if not self._entries:
            return 0.0

        total_confidence = sum(entry.confidence for entry in self._entries)
        return total_confidence / len(self._entries)

    def get_context_summary(self, max_length: int = 500) -> str:
        """
        Get summary of current conversation context.

        Args:
            max_length: Maximum summary length

        Returns:
            Summarized conversation text
        """
        full_text = self.get_recent_text()

        if len(full_text) <= max_length:
            return full_text

        # Truncate and add ellipsis
        return full_text[:max_length - 3] + "..."

    def reset(self) -> None:
        """Reset conversation context (start fresh)."""
        self._entries.clear()
        self._topic_mentions.clear()
        self.conversation_id = None
        self.conversation_start = None
        self.last_activity = None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get conversation context statistics.

        Returns:
            Dict with context metrics
        """
        return {
            "conversation_id": self.conversation_id,
            "conversation_start": self.conversation_start.isoformat() if self.conversation_start else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "duration_minutes": self.get_conversation_duration(),
            "entry_count": len(self._entries),
            "speaker_count": self.get_speaker_count(),
            "average_confidence": self.get_average_confidence(),
            "tracked_topics": len(self._topic_mentions),
            "window_minutes": self.window_minutes,
            "max_entries": self.max_entries
        }
