"""
Preference Store for Trinity Protocol.

Manages persistent storage of Alex's preferences in Firestore.

Constitutional Compliance:
- Article IV: Continuous learning with persistent storage
- Article I: Complete context - version history for trend analysis
- Privacy: Secure storage of personal preferences
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from trinity_protocol.core.models.preferences import (
    AlexPreferences,
    PreferenceSnapshot,
    ResponseRecord,
)


class PreferenceStore:
    """
    Firestore-backed storage for preference data.

    Collections:
    - alex_responses: Individual response records
    - alex_preferences: Current preference snapshot
    - alex_preference_history: Historical snapshots

    Designed for:
    - Fast querying of recent responses
    - Version history tracking
    - Trend analysis over time
    """

    def __init__(self, firestore_client: Optional[Any] = None, use_firestore: bool = False):
        """
        Initialize preference store.

        Args:
            firestore_client: Firestore client instance (if None and use_firestore=True, creates one)
            use_firestore: Whether to use Firestore backend (False = in-memory only)
        """
        self.use_firestore = use_firestore
        self.db = None

        if self.use_firestore:
            if firestore_client:
                self.db = firestore_client
            else:
                # Lazy import to avoid dependency if not using Firestore
                try:
                    import firebase_admin  # type: ignore
                    from firebase_admin import credentials, firestore  # type: ignore

                    # Check if already initialized
                    try:
                        app = firebase_admin.get_app()
                    except ValueError:
                        # Initialize Firebase
                        cred = credentials.ApplicationDefault()
                        firebase_admin.initialize_app(cred)

                    self.db = firestore.client()
                except ImportError:
                    raise ImportError(
                        "firebase-admin package required for Firestore backend. "
                        "Install with: pip install firebase-admin"
                    )

        # In-memory cache (always used)
        self._cache: Dict[str, Any] = {
            "responses": [],
            "current_preferences": None,
            "history": []
        }

    def store_response(self, response: ResponseRecord) -> str:
        """
        Store a single response record.

        Args:
            response: Response record to store

        Returns:
            Response ID
        """
        response_dict = response.dict()

        # Convert datetime to ISO string for Firestore
        if isinstance(response_dict["timestamp"], datetime):
            response_dict["timestamp"] = response_dict["timestamp"].isoformat()

        # Store in cache
        self._cache["responses"].append(response_dict)

        # Store in Firestore
        if self.use_firestore and self.db:
            doc_ref = self.db.collection("alex_responses").document(response.response_id)
            doc_ref.set(response_dict)

        return response.response_id

    def get_recent_responses(
        self,
        limit: int = 100,
        days_back: Optional[int] = None
    ) -> List[ResponseRecord]:
        """
        Get recent response records.

        Args:
            limit: Maximum number of responses to return
            days_back: Only return responses from last N days (None = all)

        Returns:
            List of ResponseRecord instances
        """
        if self.use_firestore and self.db:
            # Query Firestore
            query = self.db.collection("alex_responses").order_by(
                "timestamp",
                direction="DESCENDING"
            ).limit(limit)

            if days_back:
                cutoff = datetime.now() - timedelta(days=days_back)
                query = query.where("timestamp", ">=", cutoff.isoformat())

            docs = query.stream()
            response_dicts = [doc.to_dict() for doc in docs]
        else:
            # Use cache
            response_dicts = self._cache["responses"][-limit:]

        # Convert to ResponseRecord instances
        responses = []
        for r_dict in response_dicts:
            # Convert timestamp string back to datetime
            if isinstance(r_dict["timestamp"], str):
                r_dict["timestamp"] = datetime.fromisoformat(r_dict["timestamp"])
            responses.append(ResponseRecord(**r_dict))

        return responses

    def store_preferences(
        self,
        preferences: AlexPreferences,
        snapshot_reason: str = "automatic_update"
    ) -> str:
        """
        Store current preference snapshot.

        Args:
            preferences: Preference model
            snapshot_reason: Why snapshot was taken

        Returns:
            Snapshot ID
        """
        # Create snapshot
        snapshot = PreferenceSnapshot(
            snapshot_id=f"snap_{int(datetime.now().timestamp())}",
            snapshot_date=datetime.now(),
            preferences=preferences,
            snapshot_reason=snapshot_reason
        )

        snapshot_dict = snapshot.dict()

        # Convert datetime to ISO string
        if isinstance(snapshot_dict["snapshot_date"], datetime):
            snapshot_dict["snapshot_date"] = snapshot_dict["snapshot_date"].isoformat()
        if isinstance(snapshot_dict["preferences"]["last_updated"], datetime):
            snapshot_dict["preferences"]["last_updated"] = snapshot_dict["preferences"]["last_updated"].isoformat()

        # Store in cache
        self._cache["current_preferences"] = snapshot_dict
        self._cache["history"].append(snapshot_dict)

        # Store in Firestore
        if self.use_firestore and self.db:
            # Update current preferences
            self.db.collection("alex_preferences").document("current").set(
                snapshot_dict
            )

            # Archive in history
            self.db.collection("alex_preference_history").document(
                snapshot.snapshot_id
            ).set(snapshot_dict)

        return snapshot.snapshot_id

    def get_current_preferences(self) -> Optional[AlexPreferences]:
        """
        Get current preference snapshot.

        Returns:
            AlexPreferences or None if not yet created
        """
        if self.use_firestore and self.db:
            doc = self.db.collection("alex_preferences").document("current").get()
            if doc.exists:
                snapshot_dict = doc.to_dict()
            else:
                return None
        else:
            snapshot_dict = self._cache.get("current_preferences")
            if not snapshot_dict:
                return None

        # Convert timestamps
        if isinstance(snapshot_dict["preferences"]["last_updated"], str):
            snapshot_dict["preferences"]["last_updated"] = datetime.fromisoformat(
                snapshot_dict["preferences"]["last_updated"]
            )

        # Extract preferences from snapshot
        prefs_dict = snapshot_dict["preferences"]
        return AlexPreferences(**prefs_dict)

    def get_preference_history(
        self,
        limit: int = 10
    ) -> List[PreferenceSnapshot]:
        """
        Get historical preference snapshots.

        Args:
            limit: Maximum snapshots to return

        Returns:
            List of PreferenceSnapshot instances (reverse chronological order)
        """
        if self.use_firestore and self.db:
            docs = self.db.collection("alex_preference_history").order_by(
                "snapshot_date",
                direction="DESCENDING"
            ).limit(limit).stream()
            snapshot_dicts = [doc.to_dict() for doc in docs]
        else:
            # Get most recent snapshots and reverse order
            snapshot_dicts = list(reversed(self._cache["history"][-limit:]))

        # Convert to PreferenceSnapshot instances
        snapshots = []
        for s_dict in snapshot_dicts:
            # Convert timestamps
            if isinstance(s_dict["snapshot_date"], str):
                s_dict["snapshot_date"] = datetime.fromisoformat(s_dict["snapshot_date"])
            if isinstance(s_dict["preferences"]["last_updated"], str):
                s_dict["preferences"]["last_updated"] = datetime.fromisoformat(
                    s_dict["preferences"]["last_updated"]
                )
            snapshots.append(PreferenceSnapshot(**s_dict))

        return snapshots

    def query_responses(
        self,
        question_type: Optional[str] = None,
        topic_category: Optional[str] = None,
        response_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ResponseRecord]:
        """
        Query responses with filters.

        Args:
            question_type: Filter by question type
            topic_category: Filter by topic
            response_type: Filter by response type (YES/NO/LATER/IGNORED)
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum results

        Returns:
            List of ResponseRecord instances
        """
        if self.use_firestore and self.db:
            query = self.db.collection("alex_responses")

            if question_type:
                query = query.where("question_type", "==", question_type)
            if topic_category:
                query = query.where("topic_category", "==", topic_category)
            if response_type:
                query = query.where("response_type", "==", response_type)
            if start_date:
                query = query.where("timestamp", ">=", start_date.isoformat())
            if end_date:
                query = query.where("timestamp", "<=", end_date.isoformat())

            query = query.order_by("timestamp", direction="DESCENDING").limit(limit)

            docs = query.stream()
            response_dicts = [doc.to_dict() for doc in docs]
        else:
            # In-memory filtering
            response_dicts = self._cache["responses"]

            if question_type:
                response_dicts = [r for r in response_dicts if r["question_type"] == question_type]
            if topic_category:
                response_dicts = [r for r in response_dicts if r["topic_category"] == topic_category]
            if response_type:
                response_dicts = [r for r in response_dicts if r["response_type"] == response_type]
            if start_date:
                response_dicts = [
                    r for r in response_dicts
                    if datetime.fromisoformat(r["timestamp"]) >= start_date
                ]
            if end_date:
                response_dicts = [
                    r for r in response_dicts
                    if datetime.fromisoformat(r["timestamp"]) <= end_date
                ]

            response_dicts = response_dicts[-limit:]

        # Convert to ResponseRecord instances
        responses = []
        for r_dict in response_dicts:
            if isinstance(r_dict["timestamp"], str):
                r_dict["timestamp"] = datetime.fromisoformat(r_dict["timestamp"])
            responses.append(ResponseRecord(**r_dict))

        return responses

    def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Stats dict
        """
        if self.use_firestore and self.db:
            # Count documents
            response_count = len(list(self.db.collection("alex_responses").limit(1000).stream()))
            history_count = len(list(self.db.collection("alex_preference_history").limit(100).stream()))

            current = self.db.collection("alex_preferences").document("current").get()
            has_current = current.exists
        else:
            response_count = len(self._cache["responses"])
            history_count = len(self._cache["history"])
            has_current = self._cache["current_preferences"] is not None

        return {
            "backend": "firestore" if self.use_firestore else "in_memory",
            "response_count": response_count,
            "history_snapshots": history_count,
            "has_current_preferences": has_current
        }

    def clear_cache(self) -> None:
        """Clear in-memory cache (for testing)."""
        self._cache = {
            "responses": [],
            "current_preferences": None,
            "history": []
        }

    def delete_all_responses(self) -> int:
        """
        Delete all response records (DANGEROUS - use with caution).

        Returns:
            Number of records deleted
        """
        count = 0

        if self.use_firestore and self.db:
            # Delete from Firestore (batch delete)
            batch = self.db.batch()
            docs = self.db.collection("alex_responses").limit(500).stream()

            for doc in docs:
                batch.delete(doc.reference)
                count += 1

            batch.commit()

        # Clear cache
        cache_count = len(self._cache["responses"])
        self._cache["responses"] = []

        return count if self.use_firestore else cache_count


# Missing import fix
from datetime import timedelta
