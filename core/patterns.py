"""
UnifiedPatternStore: Consolidated pattern learning and retrieval.
In-memory start with optional persistence to SQLite.
"""

import json
import sqlite3
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from shared.types.json import JSONValue
from datetime import datetime
from pathlib import Path


@dataclass
class Pattern:
    """Represents a learned pattern from autonomous operations."""
    id: str
    pattern_type: str  # error_fix, optimization, refactoring, etc.
    context: dict[str, JSONValue]
    solution: str
    success_rate: float
    usage_count: int
    created_at: str
    last_used: str
    tags: List[str]


class UnifiedPatternStore:
    """
    Unified storage for learned patterns from self-healing operations.
    Starts in-memory, with optional SQLite persistence.
    """

    def __init__(self, persist: bool = False, db_path: str = "logs/patterns.db"):
        """
        Initialize pattern store.

        Args:
            persist: Whether to persist patterns to SQLite
            db_path: Path to SQLite database file
        """
        self.patterns: Dict[str, Pattern] = {}
        self.persist = persist
        self.db_path = Path(db_path) if persist else None

        if self.persist:
            self._init_db()
            self._load_from_db()

    def add(self, pattern: Pattern) -> bool:
        """
        Add a new pattern to the store.

        Args:
            pattern: Pattern to add

        Returns:
            True if added successfully
        """
        # Update in-memory store
        self.patterns[pattern.id] = pattern

        # Persist if enabled
        if self.persist:
            self._save_to_db(pattern)

        # Log the addition
        self._emit_telemetry("pattern_added", {
            "id": pattern.id,
            "type": pattern.pattern_type,
            "tags": pattern.tags
        })

        return True

    def find(self, query: str = None, pattern_type: str = None, tags: List[str] = None) -> List[Pattern]:
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
        context = {
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
            return {
                "total_patterns": 0,
                "pattern_types": {},
                "average_success_rate": 0.0,
                "most_used": None,
                "most_successful": None
            }

        # Calculate statistics
        pattern_types = {}
        total_success = 0
        most_used = None
        most_successful = None

        for pattern in self.patterns.values():
            # Count by type
            pattern_types[pattern.pattern_type] = pattern_types.get(pattern.pattern_type, 0) + 1

            # Track success rate
            total_success += pattern.success_rate

            # Find most used
            if not most_used or pattern.usage_count > most_used.usage_count:
                most_used = pattern

            # Find most successful
            if not most_successful or pattern.success_rate > most_successful.success_rate:
                most_successful = pattern

        return {
            "total_patterns": len(self.patterns),
            "pattern_types": pattern_types,
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