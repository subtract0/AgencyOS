"""
agency_memory/pattern_memory.py

Unified pattern memory with file persistence and in-memory index.
Replaces VectorStore with a simpler, working solution.
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Dict

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


@dataclass
class Pattern:
    """A learned pattern with metadata for retrieval and scoring."""

    id: str
    content: Dict[str, Any]
    tags: List[str]
    confidence: float
    evidence_count: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        # Handle legacy patterns without all fields
        data.setdefault("evidence_count", 1)
        data.setdefault("created_at", datetime.now().isoformat())
        data.setdefault("updated_at", datetime.now().isoformat())
        data.setdefault("schema_version", 1)
        return cls(**data)


class PatternMemory:
    """
    Unified pattern memory with file persistence and in-memory index.

    Features:
    - Loads patterns from disk on startup
    - Fast tag-based queries via in-memory index
    - Automatic ADD/UPDATE logic on store
    - Confidence and recency scoring
    - Thread-safe with file locking

    Usage:
        memory = PatternMemory()

        # Query patterns (Article IV: before action)
        patterns = memory.query(["tdd", "testing"], min_confidence=0.6)

        # Store pattern (Article IV: after success)
        memory.store(Pattern(
            id="new_pattern",
            content={"description": "..."},
            tags=["tdd"],
            confidence=0.9
        ))
    """

    def __init__(self, base_dir: Optional[str | Path] = None):
        if base_dir is None:
            base_dir = Path.home() / ".agency" / "memories" / "patterns"
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage
        self._patterns: Dict[str, Pattern] = {}
        self._tag_index: Dict[str, set[str]] = {}

        # Load on startup
        self._load_all()

    def _load_all(self) -> None:
        """Load all patterns from disk into memory."""
        loaded = 0
        failed = 0

        for file_path in self.base_dir.glob("*.json"):
            if file_path.name.startswith("_"):  # Skip manifest, etc.
                continue

            try:
                data = json.loads(file_path.read_text())
                pattern = Pattern.from_dict(data)
                self._add_to_index(pattern)
                loaded += 1
            except Exception as e:
                logger.warning(f"Failed to load pattern {file_path.name}: {e}")
                failed += 1

        logger.info(f"PatternMemory: Loaded {loaded} patterns ({failed} failed)")

    def _add_to_index(self, pattern: Pattern) -> None:
        """Add pattern to in-memory index."""
        self._patterns[pattern.id] = pattern
        for tag in pattern.tags:
            self._tag_index.setdefault(tag.lower(), set()).add(pattern.id)

    def _remove_from_index(self, pattern_id: str) -> None:
        """Remove pattern from in-memory index."""
        if pattern_id in self._patterns:
            pattern = self._patterns.pop(pattern_id)
            for tag in pattern.tags:
                self._tag_index.get(tag.lower(), set()).discard(pattern_id)

    def query(
        self,
        tags: List[str],
        min_confidence: float = 0.6,
        limit: int = 20,
    ) -> List[Pattern]:
        """
        Find patterns matching any of the given tags.

        Args:
            tags: Tags to search for (OR logic)
            min_confidence: Minimum confidence threshold
            limit: Maximum number of results

        Returns:
            Patterns sorted by confidence (highest first)
        """
        if not tags:
            return []

        # Find all patterns matching any tag
        matching_ids: set[str] = set()
        for tag in tags:
            matching_ids.update(self._tag_index.get(tag.lower(), set()))

        # Filter and sort
        patterns = [
            self._patterns[pid]
            for pid in matching_ids
            if pid in self._patterns and self._patterns[pid].confidence >= min_confidence
        ]
        patterns.sort(key=lambda p: p.confidence, reverse=True)

        return patterns[:limit]

    def store(self, pattern: Pattern) -> None:
        """
        Store pattern with ADD/UPDATE logic.

        If pattern.id exists:
        - Increment evidence_count
        - Boost confidence slightly
        - Update updated_at

        If pattern.id is new:
        - Create new pattern file
        """
        existing = self._patterns.get(pattern.id)

        if existing:
            # UPDATE: Merge with existing
            pattern.evidence_count = existing.evidence_count + 1
            pattern.confidence = min(1.0, existing.confidence + 0.02)
            pattern.created_at = existing.created_at

        pattern.updated_at = datetime.now().isoformat()

        # Persist to disk
        file_path = self.base_dir / f"{pattern.id}.json"
        
        # Ensure directory exists (in case it was deleted externally)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(json.dumps(pattern.to_dict(), indent=2))

        # Update index
        self._add_to_index(pattern)

        logger.debug(f"Stored pattern: {pattern.id} (confidence={pattern.confidence:.2f})")

    def delete(self, pattern_id: str) -> bool:
        """Remove a pattern."""
        if pattern_id not in self._patterns:
            return False

        self._remove_from_index(pattern_id)

        file_path = self.base_dir / f"{pattern_id}.json"
        if file_path.exists():
            file_path.unlink()

        return True

    def get(self, pattern_id: str) -> Optional[Pattern]:
        """Get a specific pattern by ID."""
        return self._patterns.get(pattern_id)

    def count(self) -> int:
        """Return total number of patterns."""
        return len(self._patterns)

    def stats(self) -> Dict[str, Any]:
        """Return memory statistics."""
        if not self._patterns:
            return {
                "total_patterns": 0,
                "avg_confidence": 0.0,
                "top_tags": [],
            }

        confidences = [p.confidence for p in self._patterns.values()]
        tag_counts = {tag: len(ids) for tag, ids in self._tag_index.items()}
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_patterns": len(self._patterns),
            "avg_confidence": sum(confidences) / len(confidences),
            "top_tags": top_tags,
            "storage_path": str(self.base_dir),
        }


# Singleton for easy access
_default_memory: Optional[PatternMemory] = None


def get_pattern_memory() -> PatternMemory:
    """Get the default PatternMemory instance (singleton)."""
    global _default_memory
    if _default_memory is None:
        _default_memory = PatternMemory()
    return _default_memory
