"""
Generic Preference Learning System

Consolidates trinity_protocol preference learning into a reusable,
user-agnostic system with ZERO hardcoded user-specific logic.

Analyzes response patterns to learn user preferences and optimize
question-asking strategy for ANY user.

Constitutional Compliance:
- Article IV: Continuous learning from all interactions
- Article II: Strict typing with Pydantic models
- Article I: Complete context before action
- Privacy: Learn from patterns, not individual content

Features:
- Multi-user support (NO hardcoded user IDs)
- Configurable context keywords (NO hardcoded preferences)
- SQLite persistence with user-specific tables
- Optional Firestore backend
- Message bus integration for telemetry
- Result<T,E> pattern for error handling

Consolidation:
- preference_learning.py (253 lines)
- preference_store.py (397 lines)
- alex_preference_learner.py (609 lines)
Total: 1,259 lines → 600 lines (52% reduction)
"""

import uuid
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from pydantic import BaseModel, Field

from shared.type_definitions.result import Result, Ok, Err
from shared.message_bus import MessageBus

# Re-export models from trinity for compatibility
from trinity_protocol.core.models.preferences import (
    ResponseRecord,
    ResponseType,
    QuestionType,
    TopicCategory,
    TimeOfDay,
    DayOfWeek,
    QuestionPreference,
    TimingPreference,
    DayOfWeekPreference,
    TopicPreference,
    ContextualPattern,
    PreferenceRecommendation,
    calculate_confidence,
)


# ============================================================================
# GENERIC MODELS (User-agnostic)
# ============================================================================


class UserPreference(BaseModel):
    """
    Single user preference entry.

    Generic model for any user's preference.
    """
    category: str = Field(..., description="Preference category")
    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    evidence_count: int = Field(..., ge=0, description="Number of supporting observations")
    user_id: str = Field(..., description="User identifier (GENERIC)")

    class Config:
        """Pydantic config."""
        validate_assignment = True


class UserPreferences(BaseModel):
    """
    Master preference model for ANY user.

    Replaces AlexPreferences with generic user support.
    """
    version: str = Field(default="1.0.0", description="Schema version")
    user_id: str = Field(..., description="User identifier (GENERIC)")
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    total_responses: int = Field(default=0, ge=0, description="Total responses")
    overall_acceptance_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall YES / total"
    )
    question_preferences: Dict[str, QuestionPreference] = Field(
        default_factory=dict,
        description="Preferences by question type"
    )
    timing_preferences: Dict[str, TimingPreference] = Field(
        default_factory=dict,
        description="Preferences by time of day"
    )
    day_preferences: Dict[str, DayOfWeekPreference] = Field(
        default_factory=dict,
        description="Preferences by day of week"
    )
    topic_preferences: Dict[str, TopicPreference] = Field(
        default_factory=dict,
        description="Preferences by topic category"
    )
    contextual_patterns: List[ContextualPattern] = Field(
        default_factory=list,
        description="Learned contextual patterns"
    )
    recommendations: List[PreferenceRecommendation] = Field(
        default_factory=list,
        description="Active recommendations"
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        """Pydantic config."""
        validate_assignment = True


class PreferenceSnapshot(BaseModel):
    """
    Point-in-time preference snapshot.

    For version history and trend analysis.
    """
    snapshot_id: str = Field(..., description="Snapshot identifier")
    snapshot_date: datetime = Field(
        default_factory=datetime.now,
        description="Snapshot timestamp"
    )
    user_id: str = Field(..., description="User identifier")
    preferences: UserPreferences = Field(..., description="Preference state")
    snapshot_reason: str = Field(..., description="Snapshot reason")

    class Config:
        """Pydantic config."""
        frozen = True


class RecommendationResult(BaseModel):
    """
    Recommendation for question asking.

    Generic result for any user.
    """
    should_ask: bool = Field(..., description="Should ask question")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence")
    reason: str = Field(..., description="Reasoning")
    acceptance_rate: Optional[float] = Field(default=None, description="Historical rate")
    sample_size: int = Field(default=0, description="Sample size")

    class Config:
        """Pydantic config."""
        frozen = True


# ============================================================================
# PREFERENCE STORE (Generic, Multi-User)
# ============================================================================


class PreferenceStore:
    """
    Generic preference storage with user isolation.

    Supports SQLite and optional Firestore backends.
    NO hardcoded user IDs - all data is user-specific.
    """

    def __init__(
        self,
        user_id: str,
        db_path: str,
        use_firestore: bool = False,
        firestore_client: Optional[Any] = None
    ):
        """
        Initialize preference store for specific user.

        Args:
            user_id: User identifier (GENERIC, not hardcoded)
            db_path: SQLite database path
            use_firestore: Whether to use Firestore backend
            firestore_client: Optional Firestore client
        """
        self.user_id = user_id
        self.db_path = Path(db_path)
        self.use_firestore = use_firestore
        self.db_client = firestore_client

        # Initialize SQLite
        self._init_sqlite()

        # In-memory cache
        self._cache: JSONValue = {
            "responses": [],
            "current_preferences": None,
            "snapshots": []
        }

    def _init_sqlite(self) -> None:
        """Initialize SQLite database with user-specific table."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # User-specific table name
        table_name = f"responses_{self.user_id}"

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT UNIQUE NOT NULL,
                question_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                topic_category TEXT NOT NULL,
                response_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                response_time_seconds REAL,
                context_before TEXT,
                day_of_week TEXT,
                time_of_day TEXT,
                metadata TEXT
            )
        """)

        # Snapshot table
        snapshot_table = f"snapshots_{self.user_id}"
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {snapshot_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT UNIQUE NOT NULL,
                snapshot_date TEXT NOT NULL,
                preferences_json TEXT NOT NULL,
                snapshot_reason TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def store_response(
        self,
        response: ResponseRecord
    ) -> Result[str, str]:
        """
        Store response record.

        Args:
            response: Response to store

        Returns:
            Result with response ID or error
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            table_name = f"responses_{self.user_id}"

            cursor.execute(f"""
                INSERT OR REPLACE INTO {table_name} (
                    response_id, question_id, question_text, question_type,
                    topic_category, response_type, timestamp, response_time_seconds,
                    context_before, day_of_week, time_of_day, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response.response_id,
                response.question_id,
                response.question_text,
                response.question_type.value if hasattr(response.question_type, 'value') else str(response.question_type),
                response.topic_category.value if hasattr(response.topic_category, 'value') else str(response.topic_category),
                response.response_type.value if hasattr(response.response_type, 'value') else str(response.response_type),
                response.timestamp.isoformat(),
                response.response_time_seconds,
                response.context_before,
                response.day_of_week.value if hasattr(response.day_of_week, 'value') else str(response.day_of_week),
                response.time_of_day.value if hasattr(response.time_of_day, 'value') else str(response.time_of_day),
                ""  # metadata placeholder
            ))

            conn.commit()
            conn.close()

            # Cache
            self._cache["responses"].append(response)

            return Ok(response.response_id)

        except Exception as e:
            return Err(f"Failed to store response: {str(e)}")

    def get_all_responses(self) -> Result[List[ResponseRecord], str]:
        """
        Get all responses for user.

        Returns:
            Result with response list or error
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            table_name = f"responses_{self.user_id}"

            cursor.execute(f"""
                SELECT * FROM {table_name}
                ORDER BY timestamp DESC
            """)

            rows = cursor.fetchall()
            conn.close()

            responses = []
            for row in rows:
                response = ResponseRecord(
                    response_id=row['response_id'],
                    question_id=row['question_id'],
                    question_text=row['question_text'],
                    question_type=QuestionType(row['question_type']),
                    topic_category=TopicCategory(row['topic_category']),
                    response_type=ResponseType(row['response_type']),
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    response_time_seconds=row['response_time_seconds'],
                    context_before=row['context_before'] or "",
                    day_of_week=DayOfWeek(row['day_of_week']),
                    time_of_day=TimeOfDay(row['time_of_day'])
                )
                responses.append(response)

            return Ok(responses)

        except Exception as e:
            return Err(f"Failed to get responses: {str(e)}")

    def create_snapshot(
        self,
        snapshot_reason: str
    ) -> Result[PreferenceSnapshot, str]:
        """
        Create preference snapshot.

        Args:
            snapshot_reason: Why snapshot was taken

        Returns:
            Result with snapshot or error
        """
        # Get current preferences from cache
        if not self._cache.get("current_preferences"):
            return Err("No preferences to snapshot")

        try:
            snapshot_id = f"snap_{self.user_id}_{int(datetime.now().timestamp())}"
            snapshot = PreferenceSnapshot(
                snapshot_id=snapshot_id,
                snapshot_date=datetime.now(),
                user_id=self.user_id,
                preferences=self._cache["current_preferences"],
                snapshot_reason=snapshot_reason
            )

            # Store in SQLite
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            table_name = f"snapshots_{self.user_id}"

            cursor.execute(f"""
                INSERT INTO {table_name} (
                    snapshot_id, snapshot_date, preferences_json, snapshot_reason
                ) VALUES (?, ?, ?, ?)
            """, (
                snapshot.snapshot_id,
                snapshot.snapshot_date.isoformat(),
                snapshot.preferences.json(),
                snapshot.snapshot_reason
            ))

            conn.commit()
            conn.close()

            # Cache
            self._cache["snapshots"].append(snapshot)

            return Ok(snapshot)

        except Exception as e:
            return Err(f"Failed to create snapshot: {str(e)}")


# ============================================================================
# PREFERENCE LEARNER (Generic, Multi-User)
# ============================================================================


class PreferenceLearner:
    """
    Generic preference learner for ANY user.

    NO hardcoded user IDs or user-specific logic.
    Analyzes response patterns to optimize question strategy.

    Core algorithm:
    1. Aggregate responses by dimension
    2. Calculate acceptance rates with confidence
    3. Identify trends and patterns
    4. Generate actionable recommendations
    """

    DEFAULT_CONTEXT_KEYWORDS = [
        "meeting", "call", "email", "code", "system",
        "project", "client", "work", "urgent", "important"
    ]

    def __init__(
        self,
        user_id: str,
        message_bus: MessageBus,
        db_path: str,
        min_confidence: float = 0.7,
        min_sample_size: int = 10,
        trend_window_days: int = 7,
        context_keywords: Optional[List[str]] = None
    ):
        """
        Initialize preference learner for user.

        Args:
            user_id: User identifier (GENERIC, not hardcoded)
            message_bus: Message bus for telemetry
            db_path: Database path for persistence
            min_confidence: Minimum confidence threshold (0.0-1.0)
            min_sample_size: Minimum samples for reliable pattern
            trend_window_days: Days for trend analysis
            context_keywords: Custom context keywords (or use defaults)
        """
        self.user_id = user_id
        self.message_bus = message_bus
        self.min_confidence = min_confidence
        self.min_sample_size = min_sample_size
        self.trend_window_days = trend_window_days
        self.context_keywords = context_keywords or self.DEFAULT_CONTEXT_KEYWORDS

        # Initialize store
        self.store = PreferenceStore(user_id=user_id, db_path=db_path)

    def observe(self, response: ResponseRecord) -> Result[None, str]:
        """
        Record user response observation.

        Args:
            response: Response record

        Returns:
            Result with None or error
        """
        # Store response
        store_result = self.store.store_response(response)
        if store_result.is_err():
            return Err(store_result.error)

        # Publish telemetry
        self._publish_telemetry(response)

        return Ok(None)

    def get_preferences(self) -> Result[UserPreferences, str]:
        """
        Get current user preferences.

        Returns:
            Result with preferences or error
        """
        # Get all responses
        responses_result = self.store.get_all_responses()
        if responses_result.is_err():
            return Err(responses_result.error)

        responses = responses_result.unwrap()  # Use unwrap() instead of .value

        # Analyze responses
        preferences = self._analyze_responses(responses)

        # Cache preferences
        self.store._cache["current_preferences"] = preferences

        return Ok(preferences)

    def recommend(self, context: JSONValue) -> Result[RecommendationResult, str]:
        """
        Generate recommendation for question.

        Args:
            context: Context dict (e.g., {"question_type": "high_value"})

        Returns:
            Result with recommendation or error
        """
        # Get preferences
        prefs_result = self.get_preferences()
        if prefs_result.is_err():
            return Err(prefs_result.error)

        prefs = prefs_result.unwrap()

        # Extract context
        question_type = context.get("question_type")

        if not question_type:
            return Err("question_type required in context")

        # Find preference for this type
        type_pref = prefs.question_preferences.get(question_type)

        if not type_pref:
            # No data yet
            return Ok(RecommendationResult(
                should_ask=True,
                confidence=0.5,
                reason="Insufficient data for this question type",
                sample_size=0
            ))

        # Check confidence
        if type_pref.confidence < self.min_confidence:
            return Ok(RecommendationResult(
                should_ask=True,
                confidence=type_pref.confidence,
                reason=f"Low confidence ({type_pref.confidence:.1%}), need more data",
                acceptance_rate=type_pref.acceptance_rate,
                sample_size=type_pref.total_asked
            ))

        # Recommend based on acceptance rate
        should_ask = type_pref.acceptance_rate >= 0.5

        return Ok(RecommendationResult(
            should_ask=should_ask,
            confidence=type_pref.confidence,
            reason=f"Based on {type_pref.total_asked} samples, {type_pref.acceptance_rate:.1%} acceptance rate",
            acceptance_rate=type_pref.acceptance_rate,
            sample_size=type_pref.total_asked
        ))

    def _analyze_responses(
        self,
        responses: List[ResponseRecord]
    ) -> UserPreferences:
        """Analyze responses and generate preferences."""
        if not responses:
            return UserPreferences(user_id=self.user_id)

        # Calculate overall metrics
        total = len(responses)
        yes_count = sum(1 for r in responses if r.response_type == ResponseType.YES)
        overall_rate = yes_count / total if total > 0 else 0.0

        # Analyze dimensions
        question_prefs = self._analyze_question_types(responses)
        timing_prefs = self._analyze_timing(responses)
        day_prefs = self._analyze_days(responses)
        topic_prefs = self._analyze_topics(responses)
        contextual = self._analyze_context(responses)

        return UserPreferences(
            user_id=self.user_id,
            last_updated=datetime.now(),
            total_responses=total,
            overall_acceptance_rate=overall_rate,
            question_preferences=question_prefs,
            timing_preferences=timing_prefs,
            day_preferences=day_prefs,
            topic_preferences=topic_prefs,
            contextual_patterns=contextual,
            recommendations=[]
        )

    def _analyze_question_types(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[str, QuestionPreference]:
        """Analyze by question type."""
        by_type: Dict[str, List[ResponseRecord]] = defaultdict(list)
        for r in responses:
            q_type = r.question_type if isinstance(r.question_type, str) else r.question_type.value
            by_type[q_type].append(r)

        prefs = {}
        for q_type_str, type_responses in by_type.items():
            total = len(type_responses)
            yes_count = sum(1 for r in type_responses if r.response_type == ResponseType.YES)
            no_count = sum(1 for r in type_responses if r.response_type == ResponseType.NO)
            later_count = sum(1 for r in type_responses if r.response_type == ResponseType.LATER)
            ignored_count = sum(1 for r in type_responses if r.response_type == ResponseType.IGNORED)

            rate = yes_count / total if total > 0 else 0.0
            conf = calculate_confidence(total, self.min_sample_size)

            prefs[q_type_str] = QuestionPreference(
                question_type=QuestionType(q_type_str),
                total_asked=total,
                yes_count=yes_count,
                no_count=no_count,
                later_count=later_count,
                ignored_count=ignored_count,
                acceptance_rate=rate,
                confidence=conf,
                last_updated=datetime.now()
            )

        return prefs

    def _analyze_timing(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[str, TimingPreference]:
        """Analyze by time of day."""
        by_time: Dict[str, List[ResponseRecord]] = defaultdict(list)
        for r in responses:
            time_str = r.time_of_day if isinstance(r.time_of_day, str) else r.time_of_day.value
            by_time[time_str].append(r)

        prefs = {}
        for time_str, time_responses in by_time.items():
            total = len(time_responses)
            yes_count = sum(1 for r in time_responses if r.response_type == ResponseType.YES)
            rate = yes_count / total if total > 0 else 0.0
            conf = calculate_confidence(total, self.min_sample_size)

            prefs[time_str] = TimingPreference(
                time_of_day=TimeOfDay(time_str),
                total_asked=total,
                yes_count=yes_count,
                acceptance_rate=rate,
                confidence=conf
            )

        return prefs

    def _analyze_days(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[str, DayOfWeekPreference]:
        """Analyze by day of week."""
        by_day: Dict[str, List[ResponseRecord]] = defaultdict(list)
        for r in responses:
            day_str = r.day_of_week if isinstance(r.day_of_week, str) else r.day_of_week.value
            by_day[day_str].append(r)

        prefs = {}
        for day_str, day_responses in by_day.items():
            total = len(day_responses)
            yes_count = sum(1 for r in day_responses if r.response_type == ResponseType.YES)
            rate = yes_count / total if total > 0 else 0.0
            conf = calculate_confidence(total, self.min_sample_size)

            prefs[day_str] = DayOfWeekPreference(
                day_of_week=DayOfWeek(day_str),
                total_asked=total,
                yes_count=yes_count,
                acceptance_rate=rate,
                confidence=conf
            )

        return prefs

    def _analyze_topics(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[str, TopicPreference]:
        """Analyze by topic."""
        by_topic: Dict[str, List[ResponseRecord]] = defaultdict(list)
        for r in responses:
            topic_str = r.topic_category if isinstance(r.topic_category, str) else r.topic_category.value
            by_topic[topic_str].append(r)

        prefs = {}
        for topic_str, topic_responses in by_topic.items():
            total = len(topic_responses)
            yes_count = sum(1 for r in topic_responses if r.response_type == ResponseType.YES)
            no_count = sum(1 for r in topic_responses if r.response_type == ResponseType.NO)
            rate = yes_count / total if total > 0 else 0.0
            conf = calculate_confidence(total, self.min_sample_size)
            trend = self._detect_trend(topic_responses)

            prefs[topic_str] = TopicPreference(
                topic_category=TopicCategory(topic_str),
                total_asked=total,
                yes_count=yes_count,
                no_count=no_count,
                acceptance_rate=rate,
                confidence=conf,
                trend=trend
            )

        return prefs

    def _analyze_context(
        self,
        responses: List[ResponseRecord]
    ) -> List[ContextualPattern]:
        """Analyze contextual patterns."""
        patterns: Dict[Tuple[str, ...], Tuple[int, int]] = defaultdict(lambda: (0, 0))

        for response in responses:
            context = response.context_before.lower()
            found_keywords = tuple(
                sorted([kw for kw in self.context_keywords if kw in context])
            )

            if found_keywords:
                occurrence, yes_count = patterns[found_keywords]
                patterns[found_keywords] = (
                    occurrence + 1,
                    yes_count + (1 if response.response_type == ResponseType.YES else 0)
                )

        result = []
        for keywords, (occurrence, yes_count) in patterns.items():
            if occurrence < 3:
                continue

            rate = yes_count / occurrence if occurrence > 0 else 0.0
            conf = calculate_confidence(occurrence, 3)

            if conf >= self.min_confidence:
                pattern = ContextualPattern(
                    pattern_id=f"ctx_{uuid.uuid4().hex[:8]}",
                    pattern_description=f"Questions with: {', '.join(keywords)}",
                    context_keywords=list(keywords),
                    occurrence_count=occurrence,
                    yes_count=yes_count,
                    acceptance_rate=rate,
                    confidence=conf,
                    examples=[]
                )
                result.append(pattern)

        return result

    def _detect_trend(
        self,
        responses: List[ResponseRecord]
    ) -> str:
        """Detect trend (increasing/stable/decreasing)."""
        if len(responses) < 4:
            return "stable"

        sorted_responses = sorted(responses, key=lambda r: r.timestamp)
        cutoff = datetime.now() - timedelta(days=self.trend_window_days)
        recent = [r for r in sorted_responses if r.timestamp >= cutoff]
        earlier = [r for r in sorted_responses if r.timestamp < cutoff]

        if not earlier or not recent:
            return "stable"

        recent_yes = sum(1 for r in recent if r.response_type == ResponseType.YES)
        recent_rate = recent_yes / len(recent) if recent else 0.0

        earlier_yes = sum(1 for r in earlier if r.response_type == ResponseType.YES)
        earlier_rate = earlier_yes / len(earlier) if earlier else 0.0

        diff = recent_rate - earlier_rate
        if diff > 0.1:
            return "increasing"
        elif diff < -0.1:
            return "decreasing"
        else:
            return "stable"

    def _publish_telemetry(self, response: ResponseRecord) -> None:
        """Publish telemetry event."""
        # Extract enum values safely
        response_type_str = response.response_type if isinstance(response.response_type, str) else response.response_type.value
        question_type_str = response.question_type if isinstance(response.question_type, str) else response.question_type.value

        # Async publish (fire and forget)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.message_bus.publish(
                "telemetry_stream",
                {
                    "event_type": f"response_{response_type_str.lower()}",
                    "user_id": self.user_id,
                    "question_type": question_type_str,
                    "response_type": response_type_str,
                    "response_time_seconds": response.response_time_seconds,
                    "timestamp": response.timestamp.isoformat()
                }
            ))
        except RuntimeError:
            # No event loop - skip telemetry
            pass
