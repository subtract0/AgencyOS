"""
UnifiedPatternStore: Consolidated pattern learning and retrieval.
In-memory start with optional persistence to SQLite.

DEPRECATION NOTICE: This module is being migrated to pattern_intelligence.
The Pattern class is deprecated in favor of CodingPattern.
UnifiedPatternStore is deprecated in favor of PatternStore.
"""

import json
import sqlite3
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from shared.type_definitions.json import JSONValue
from datetime import datetime
from pathlib import Path
import warnings
import logging

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """
    DEPRECATED: Use pattern_intelligence.CodingPattern instead.

    Represents a learned pattern from autonomous operations.
    This class is maintained for backward compatibility only.
    """
    id: str
    pattern_type: str  # error_fix, optimization, refactoring, etc.
    context: dict[str, JSONValue]
    solution: str
    success_rate: float
    usage_count: int
    created_at: str
    last_used: str
    tags: List[str]

    def __post_init__(self):
        warnings.warn(
            "Pattern class is deprecated. Use pattern_intelligence.CodingPattern instead.",
            DeprecationWarning,
            stacklevel=2
        )

    def to_coding_pattern(self):
        """Convert this Pattern to the new CodingPattern format."""
        from pattern_intelligence.migration import pattern_to_coding_pattern
        return pattern_to_coding_pattern(self)


class UnifiedPatternStore:
    """
    DEPRECATED: Use pattern_intelligence.PatternStore instead.

    Unified storage for learned patterns from self-healing operations.
    This class now delegates to the new PatternStore for compatibility.
    """

    def __init__(self, persist: bool = False, db_path: str = "logs/patterns.db"):
        """
        Initialize pattern store.

        Args:
            persist: Whether to persist patterns to SQLite
            db_path: Path to SQLite database file
        """
        warnings.warn(
            "UnifiedPatternStore is deprecated. Use pattern_intelligence.PatternStore instead.",
            DeprecationWarning,
            stacklevel=2
        )

        # Keep legacy storage for compatibility
        self.patterns: Dict[str, Pattern] = {}
        self.persist = persist
        self.db_path = Path(db_path) if persist else None

        # Initialize the new PatternStore as the backend
        from pattern_intelligence.pattern_store import PatternStore
        self._new_store = PatternStore(namespace="legacy_migration")

        if self.persist:
            self._init_db()
            self._load_from_db()
            # Migrate existing patterns to new store
            self._migrate_to_new_store()

    def _migrate_to_new_store(self):
        """Migrate existing patterns to new PatternStore."""
        for pattern in self.patterns.values():
            try:
                coding_pattern = pattern.to_coding_pattern()
                self._new_store.store_pattern(coding_pattern)
            except Exception as e:
                logger.error(f"Failed to migrate pattern {pattern.id} to new store: {e}")

    def add(self, pattern: Pattern) -> bool:
        """
        Add a new pattern to the store.

        Args:
            pattern: Pattern to add

        Returns:
            True if added successfully
        """
        # Update in-memory store for compatibility
        self.patterns[pattern.id] = pattern

        # Also add to new store
        try:
            coding_pattern = pattern.to_coding_pattern()
            self._new_store.store_pattern(coding_pattern)
        except Exception as e:
            logger.error(f"Failed to add pattern to new store: {e}")

        # Persist if enabled
        if self.persist:
            self._save_to_db(pattern)

        # Log the addition
        from typing import cast
        tags_json = cast(JSONValue, pattern.tags)
        self._emit_telemetry("pattern_added", {
            "id": pattern.id,
            "type": pattern.pattern_type,
            "tags": tags_json
        })

        return True

    def find(self, query: Optional[str] = None, pattern_type: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Pattern]:
        """
        Find patterns matching criteria.

        Args:
            query: Text to search in context/solution
            pattern_type: Filter by pattern type
            tags: Filter by tags (any match)

        Returns:
            List of matching patterns, sorted by success rate
        """
        matches = []

        for pattern in self.patterns.values():
            # Apply filters
            if pattern_type and pattern.pattern_type != pattern_type:
                continue

            if tags and not any(tag in pattern.tags for tag in tags):
                continue

            if query:
                # Search in context and solution
                context_str = json.dumps(pattern.context).lower()
                if query.lower() not in context_str and query.lower() not in pattern.solution.lower():
                    continue

            matches.append(pattern)

        # Sort by success rate and usage count
        matches.sort(key=lambda p: (p.success_rate, p.usage_count), reverse=True)

        return matches

    def get_by_id(self, pattern_id: str) -> Optional[Pattern]:
        """
        Get a specific pattern by ID.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern if found, None otherwise
        """
        return self.patterns.get(pattern_id)

    def update_success_rate(self, pattern_id: str, success: bool):
        """
        Update pattern success rate based on new usage.

        Args:
            pattern_id: Pattern identifier
            success: Whether the pattern application was successful
        """
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return

        # Update success rate with exponential moving average
        alpha = 0.2  # Weight for new observation
        new_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * pattern.success_rate

        pattern.success_rate = new_rate
        pattern.usage_count += 1
        pattern.last_used = datetime.now().isoformat()

        if self.persist:
            self._update_db(pattern)

        self._emit_telemetry("pattern_usage", {
            "id": pattern_id,
            "success": success,
            "new_rate": new_rate,
            "usage_count": pattern.usage_count
        })

    def learn_from_fix(self, error_type: str, original_code: str, fixed_code: str, test_passed: bool):
        """
        Learn a new pattern from a successful fix.

        Args:
            error_type: Type of error that was fixed
            original_code: Code before fix
            fixed_code: Code after fix
            test_passed: Whether tests passed after fix
        """
        # Generate pattern ID
        pattern_id = f"{error_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Extract pattern context
        context: dict[str, JSONValue] = {
            "error_type": error_type,
            "original": original_code[:500],  # Limit size
            "transformation": self._extract_transformation(original_code, fixed_code)
        }

        # Create pattern
        pattern = Pattern(
            id=pattern_id,
            pattern_type="error_fix",
            context=context,
            solution=fixed_code[:500],  # Limit size
            success_rate=1.0 if test_passed else 0.0,
            usage_count=1,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            tags=[error_type, "auto_learned", "self_healing"]
        )

        self.add(pattern)

        return pattern_id

    def get_statistics(self) -> dict[str, JSONValue]:
        """
        Get store statistics.

        Returns:
            Dictionary with pattern statistics
        """
        if not self.patterns:
            return self._get_empty_statistics()

        # Calculate core metrics
        pattern_types, total_success = self._calculate_pattern_metrics()
        most_used, most_successful = self._find_pattern_extremes()

        # Build statistics response
        return self._build_statistics_response(
            pattern_types, total_success, most_used, most_successful
        )

    def _get_empty_statistics(self) -> dict[str, JSONValue]:
        """
        Return empty statistics structure when no patterns exist.

        Returns:
            Empty statistics dictionary
        """
        return {
            "total_patterns": 0,
            "pattern_types": {},
            "average_success_rate": 0.0,
            "most_used": None,
            "most_successful": None
        }

    def _calculate_pattern_metrics(self) -> tuple[dict[str, int], float]:
        """
        Calculate pattern type counts and total success rate.

        Returns:
            Tuple of (pattern_types_dict, total_success_rate)
        """
        pattern_types: dict[str, int] = {}
        total_success: float = 0.0

        for pattern in self.patterns.values():
            # Count by type
            pattern_types[pattern.pattern_type] = pattern_types.get(pattern.pattern_type, 0) + 1
            # Track success rate
            total_success += pattern.success_rate

        return pattern_types, total_success

    def _find_pattern_extremes(self) -> tuple[Optional[Pattern], Optional[Pattern]]:
        """
        Find the most used and most successful patterns.

        Returns:
            Tuple of (most_used_pattern, most_successful_pattern)
        """
        most_used = None
        most_successful = None

        for pattern in self.patterns.values():
            # Find most used
            if not most_used or pattern.usage_count > most_used.usage_count:
                most_used = pattern

            # Find most successful
            if not most_successful or pattern.success_rate > most_successful.success_rate:
                most_successful = pattern

        return most_used, most_successful

    def _build_statistics_response(
        self,
        pattern_types: dict[str, int],
        total_success: float,
        most_used: Optional[Pattern],
        most_successful: Optional[Pattern]
    ) -> dict[str, JSONValue]:
        """
        Build the final statistics response dictionary.

        Args:
            pattern_types: Dictionary of pattern type counts
            total_success: Total success rate across all patterns
            most_used: Pattern with highest usage count
            most_successful: Pattern with highest success rate

        Returns:
            Complete statistics dictionary
        """
        # Convert pattern_types to JSONValue compatible type
        pattern_types_json: JSONValue = {k: v for k, v in pattern_types.items()}

        return {
            "total_patterns": len(self.patterns),
            "pattern_types": pattern_types_json,
            "average_success_rate": total_success / len(self.patterns),
            "most_used": {
                "id": most_used.id,
                "type": most_used.pattern_type,
                "usage": most_used.usage_count
            } if most_used else None,
            "most_successful": {
                "id": most_successful.id,
                "type": most_successful.pattern_type,
                "rate": most_successful.success_rate
            } if most_successful else None
        }

    def _extract_transformation(self, original: str, fixed: str) -> str:
        """
        Extract the transformation pattern between original and fixed code.
        """
        # Simple diff-like representation
        if "if" in fixed and "if" not in original:
            return "add_null_check"
        elif "try" in fixed and "try" not in original:
            return "add_exception_handling"
        elif "or" in fixed and "or" not in original:
            return "add_default_value"
        else:
            return "general_transformation"

    def _emit_telemetry(self, event: str, data: dict[str, JSONValue]):
        """
        Emit telemetry event through unified system.
        """
        try:
            from core.telemetry import emit
            emit(f"pattern_store.{event}", data)
        except ImportError:
            pass  # Telemetry not available

    def _init_db(self):
        """
        Initialize SQLite database schema.
        """
        if not self.db_path:
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                context TEXT NOT NULL,
                solution TEXT NOT NULL,
                success_rate REAL NOT NULL,
                usage_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                last_used TEXT NOT NULL,
                tags TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def _load_from_db(self):
        """
        Load patterns from SQLite database.
        """
        if not self.db_path or not self.db_path.exists():
            return

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM patterns")
        rows = cursor.fetchall()

        for row in rows:
            pattern = Pattern(
                id=row[0],
                pattern_type=row[1],
                context=json.loads(row[2]),
                solution=row[3],
                success_rate=row[4],
                usage_count=row[5],
                created_at=row[6],
                last_used=row[7],
                tags=json.loads(row[8])
            )
            self.patterns[pattern.id] = pattern

        conn.close()

    def _save_to_db(self, pattern: Pattern):
        """
        Save pattern to SQLite database.
        """
        if not self.db_path:
            return

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.id,
            pattern.pattern_type,
            json.dumps(pattern.context),
            pattern.solution,
            pattern.success_rate,
            pattern.usage_count,
            pattern.created_at,
            pattern.last_used,
            json.dumps(pattern.tags)
        ))

        conn.commit()
        conn.close()

    def _update_db(self, pattern: Pattern):
        """
        Update pattern in SQLite database.
        """
        self._save_to_db(pattern)  # INSERT OR REPLACE handles updates


# Global singleton instance
_pattern_store_instance = None


def get_pattern_store() -> UnifiedPatternStore:
    """
    Get the global pattern store instance (singleton pattern).

    Returns:
        UnifiedPatternStore: The global pattern store instance
    """
    global _pattern_store_instance
    if _pattern_store_instance is None:
        # Check if persistence should be enabled
        import os
        persist = os.getenv("PERSIST_PATTERNS", "false").lower() == "true"
        _pattern_store_instance = UnifiedPatternStore(persist=persist)
    return _pattern_store_instance