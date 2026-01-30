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



# Import AgencyGraph 
from agency_memory.knowledge_graph import AgencyGraph

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
    Unified pattern memory with file persistence, in-memory index, AND knowledge graph.

    Features:
    - Loads patterns from disk on startup
    - Fast tag-based queries via in-memory index
    - Knowledge Graph integration for semantic linking
    - Automatic ADD/UPDATE logic on store
    """

    def __init__(self, base_dir: Optional[str | Path] = None):
        if base_dir is None:
            base_dir = Path.home() / ".agency" / "memories" / "patterns"
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage
        self._patterns: Dict[str, Pattern] = {}
        self._tag_index: Dict[str, set[str]] = {}
        
        # Knowledge Graph
        self.graph = AgencyGraph(self.base_dir)

        # Load on startup
        self._load_all()

    def _load_all(self) -> None:
        """Load all patterns from disk into memory."""
        loaded = 0
        failed = 0

        for file_path in self.base_dir.glob("*.json"):
            if file_path.name.startswith("_") or file_path.name == "knowledge_graph.json":  # Skip manifest, graph
                continue

            try:
                data = json.loads(file_path.read_text())
                pattern = Pattern.from_dict(data)
                self._add_to_index(pattern)
                
                # Check consistency: Ensure pattern is in graph
                # If loading from old files, we might need to populate the graph
                # But for now, assume graph persists itself.
                # If graph is empty but we have files, we should backfill.
                # Simplification: Always add to graph in memory (idempotent usually)
                self.graph.add_pattern(pattern.id, pattern.tags)
                
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
        Find patterns matching tags AND their semantic neighbors in the graph.
        """
        if not tags:
            return []

        # 1. Direct Hit: Find patterns matching given tags
        matching_ids: set[str] = set()
        for tag in tags:
            tag = tag.lower().strip()
            # Direct tag lookup
            matching_ids.update(self._tag_index.get(tag, set()))
            
            # 2. Semantic Expansion: Find patterns connected to this Concept via Graph
            # The graph knows which patterns are tagged with 'tag' (NodeType.CONCEPT)
            # This overlaps with _tag_index but is the "Graph Way"
            related_via_concept = self.graph.search_by_concept(tag)
            matching_ids.update(related_via_concept)

        # 3. Graph Traversal: Find patterns related to the *found* patterns
        # e.g. If Pattern A is found, and Pattern A -> CAUSES -> Pattern B, include B.
        # Limit recursion to avoid explosion.
        expansion_ids = set()
        for pid in list(matching_ids):
            related = self.graph.find_related(pid, max_hops=1)
            # Filter for only Patterns (ignore Concepts for result list)
            # Actually find_related returns IDs.
            for rid in related:
                if rid in self._patterns:
                    expansion_ids.add(rid)
        
        matching_ids.update(expansion_ids)

        # Filter and sort
        patterns = [
            self._patterns[pid]
            for pid in matching_ids
            if pid in self._patterns and self._patterns[pid].confidence >= min_confidence
        ]
        
        # Sort by confidence + semantic relevance (todo)
        # For now, pure confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)

        return patterns[:limit]

    def store(self, pattern: Pattern) -> None:
        """
        Store pattern with ADD/UPDATE logic.
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
        
        # Update Knowledge Graph
        self.graph.add_pattern(pattern.id, pattern.tags)
        self.graph.save() # Persist graph immediately

        logger.debug(f"Stored pattern: {pattern.id} (confidence={pattern.confidence:.2f})")

    def delete(self, pattern_id: str) -> bool:
        """Remove a pattern."""
        if pattern_id not in self._patterns:
            return False

        self._remove_from_index(pattern_id)

        file_path = self.base_dir / f"{pattern_id}.json"
        if file_path.exists():
            file_path.unlink()
            
        # TODO: Remove from graph as well?
        # For now, leaving nodes in graph is okay (orphaned knowledge history)

        return True

    def get(self, pattern_id: str) -> Optional[Pattern]:
        """Get a specific pattern by ID."""
        return self._patterns.get(pattern_id)

    def count(self) -> int:
        """Return total number of patterns."""
        return len(self._patterns)

    def get_all_patterns(self) -> List[Pattern]:
        """Return all patterns in memory."""
        return list(self._patterns.values())

    def bulk_store(self, patterns: List[Pattern]) -> int:
        """
        Store multiple patterns efficiently.
        Returns number of patterns stored.
        """
        count = 0
        for p in patterns:
            try:
                self.store(p)
                count += 1
            except Exception as e:
                logger.error(f"Failed to store pattern {p.id}: {e}")
        return count

    def bulk_delete(self, pattern_ids: List[str]) -> int:
        """
        Delete multiple patterns by ID.
        Returns number of patterns deleted.
        """
        count = 0
        for pid in pattern_ids:
            if self.delete(pid):
                count += 1
        return count

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
            "graph_nodes": len(self.graph.graph.nodes),
            "graph_edges": len(self.graph.graph.edges)
        }


# Singleton for easy access
_default_memory: Optional[PatternMemory] = None


def get_pattern_memory() -> PatternMemory:
    """Get the default PatternMemory instance (singleton)."""
    global _default_memory
    if _default_memory is None:
        _default_memory = PatternMemory()
    return _default_memory
