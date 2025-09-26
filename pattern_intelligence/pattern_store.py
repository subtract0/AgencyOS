"""
PatternStore - VectorStore-backed repository for coding patterns.

Provides semantic search, pattern clustering, and effectiveness tracking
for the Infinite Intelligence Amplifier.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from shared.type_definitions.json import JSONValue
from dataclasses import dataclass
from datetime import datetime

from agency_memory.vector_store import VectorStore, SimilarityResult
from .coding_pattern import CodingPattern, ProblemContext

logger = logging.getLogger(__name__)


@dataclass
class PatternSearchResult:
    """Result from pattern search with relevance scoring."""

    pattern: CodingPattern
    relevance_score: float
    search_type: str  # 'semantic', 'keyword', or 'hybrid'
    match_reason: str  # Why this pattern was matched


class PatternStore:
    """
    VectorStore-backed repository for coding patterns.

    Provides:
    - Semantic pattern search
    - Pattern effectiveness tracking
    - Pattern clustering and relationships
    - Usage analytics and optimization
    """

    def __init__(self, embedding_provider: Optional[str] = None, namespace: str = "patterns"):
        """
        Initialize PatternStore.

        Args:
            embedding_provider: Embedding provider for semantic search
            namespace: Namespace for pattern storage
        """
        self.vector_store = VectorStore(embedding_provider=embedding_provider)
        self.namespace = namespace
        self._patterns_cache: Dict[str, CodingPattern] = {}

        logger.info(f"PatternStore initialized with namespace: {namespace}")

    def store_pattern(self, pattern: CodingPattern) -> bool:
        """
        Store a coding pattern in the vector store.

        Args:
            pattern: CodingPattern to store

        Returns:
            True if stored successfully
        """
        try:
            # Convert pattern to memory record format
            memory_record = {
                "key": pattern.metadata.pattern_id,
                "content": pattern.to_dict(),
                "tags": [
                    "coding_pattern",
                    pattern.context.domain,
                    f"effectiveness_{pattern.outcome.effectiveness_score():.1f}",
                ] + pattern.metadata.tags,
                "timestamp": pattern.metadata.discovered_timestamp,
                "metadata": {
                    "namespace": self.namespace,
                    "pattern_type": "coding_pattern",
                    "domain": pattern.context.domain,
                    "effectiveness_score": pattern.outcome.effectiveness_score(),
                    "success_rate": pattern.outcome.success_rate,
                    "validation_status": pattern.metadata.validation_status,
                },
                "searchable_text": pattern.to_searchable_text(),
            }

            # Add to vector store
            self.vector_store.add_memory(pattern.metadata.pattern_id, memory_record)

            # Cache the pattern
            self._patterns_cache[pattern.metadata.pattern_id] = pattern

            logger.info(f"Stored pattern: {pattern.metadata.pattern_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store pattern {pattern.metadata.pattern_id}: {e}")
            return False

    def find_patterns(
        self,
        query: str = None,
        context: ProblemContext = None,
        domain: str = None,
        min_effectiveness: float = 0.5,
        max_results: int = 10
    ) -> List[PatternSearchResult]:
        """
        Find patterns matching search criteria.

        Args:
            query: Text query for semantic search
            context: ProblemContext for context-aware search
            domain: Filter by problem domain
            min_effectiveness: Minimum effectiveness score
            max_results: Maximum number of results

        Returns:
            List of PatternSearchResult ordered by relevance
        """
        try:
            search_results = []

            # Build search query
            if context:
                search_query = context.to_searchable_text()
                if query:
                    search_query = f"{query} {search_query}"
            else:
                search_query = query or ""

            # Get all patterns if no specific query
            if not search_query:
                all_memories = list(self.vector_store._memory_records.values())
                pattern_memories = [m for m in all_memories
                                  if m.get("metadata", {}).get("namespace") == self.namespace]
            else:
                # Perform semantic/hybrid search
                pattern_memories = self.vector_store.search(
                    query=search_query,
                    namespace=self.namespace,
                    limit=max_results * 2  # Get more for filtering
                )

            # Convert to PatternSearchResult objects
            for memory in pattern_memories:
                try:
                    pattern_data = memory.get("content", {})
                    if not isinstance(pattern_data, dict):
                        continue

                    pattern = CodingPattern.from_dict(pattern_data)

                    # Apply filters
                    if domain and pattern.context.domain != domain:
                        continue

                    if pattern.outcome.effectiveness_score() < min_effectiveness:
                        continue

                    # Calculate relevance score
                    relevance_score = memory.get("relevance_score", 0.5)

                    # Boost score based on effectiveness
                    effectiveness_boost = pattern.outcome.effectiveness_score() * 0.3
                    final_score = min(1.0, relevance_score + effectiveness_boost)

                    # Determine match reason
                    match_reason = self._determine_match_reason(pattern, query, context, domain)

                    search_results.append(PatternSearchResult(
                        pattern=pattern,
                        relevance_score=final_score,
                        search_type=memory.get("search_type", "hybrid"),
                        match_reason=match_reason
                    ))

                except Exception as e:
                    logger.warning(f"Failed to process pattern memory: {e}")
                    continue

            # Sort by relevance score
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)

            # Return top results
            results = search_results[:max_results]
            logger.info(f"Found {len(results)} patterns for query: {search_query[:50]}...")

            return results

        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return []

    def get_pattern(self, pattern_id: str) -> Optional[CodingPattern]:
        """Get a specific pattern by ID."""
        try:
            # Check cache first
            if pattern_id in self._patterns_cache:
                return self._patterns_cache[pattern_id]

            # Search in vector store
            memory_record = self.vector_store._memory_records.get(pattern_id)
            if memory_record:
                pattern_data = memory_record.get("content", {})
                if isinstance(pattern_data, dict):
                    pattern = CodingPattern.from_dict(pattern_data)
                    self._patterns_cache[pattern_id] = pattern
                    return pattern

            return None

        except Exception as e:
            logger.error(f"Failed to get pattern {pattern_id}: {e}")
            return None

    def update_pattern_usage(self, pattern_id: str, success: bool = True) -> bool:
        """
        Update pattern usage statistics.

        Args:
            pattern_id: Pattern to update
            success: Whether the application was successful

        Returns:
            True if updated successfully
        """
        try:
            pattern = self.get_pattern(pattern_id)
            if not pattern:
                return False

            # Update usage statistics
            pattern.metadata.application_count += 1
            pattern.metadata.last_applied = datetime.now().isoformat()

            if success:
                # Boost effectiveness metrics
                current_success = pattern.outcome.success_rate
                new_success = (current_success * 0.9) + (1.0 * 0.1)  # Exponential moving average
                pattern.outcome.success_rate = min(1.0, new_success)

                # Increase confidence slightly
                pattern.outcome.confidence = min(1.0, pattern.outcome.confidence + 0.05)
            else:
                # Decrease success rate slightly for failures
                current_success = pattern.outcome.success_rate
                new_success = (current_success * 0.9) + (0.0 * 0.1)
                pattern.outcome.success_rate = max(0.0, new_success)

            # Re-store the updated pattern
            return self.store_pattern(pattern)

        except Exception as e:
            logger.error(f"Failed to update pattern usage {pattern_id}: {e}")
            return False

    def get_patterns_by_domain(self, domain: str, limit: int = 20) -> List[CodingPattern]:
        """Get all patterns for a specific domain."""
        results = self.find_patterns(domain=domain, max_results=limit)
        return [result.pattern for result in results]

    def get_top_patterns(self, limit: int = 10) -> List[CodingPattern]:
        """Get top patterns by effectiveness score."""
        try:
            all_patterns = []

            # Get all pattern memories
            for memory in self.vector_store._memory_records.values():
                if memory.get("metadata", {}).get("namespace") == self.namespace:
                    try:
                        pattern_data = memory.get("content", {})
                        if isinstance(pattern_data, dict):
                            pattern = CodingPattern.from_dict(pattern_data)
                            all_patterns.append(pattern)
                    except Exception:
                        continue

            # Sort by effectiveness score
            all_patterns.sort(key=lambda p: p.outcome.effectiveness_score(), reverse=True)

            return all_patterns[:limit]

        except Exception as e:
            logger.error(f"Failed to get top patterns: {e}")
            return []

    def find_related_patterns(self, pattern_id: str, limit: int = 5) -> List[PatternSearchResult]:
        """Find patterns related to the given pattern."""
        try:
            base_pattern = self.get_pattern(pattern_id)
            if not base_pattern:
                return []

            # Search using the pattern's context and solution
            search_query = f"{base_pattern.context.to_searchable_text()} {base_pattern.solution.to_searchable_text()}"

            results = self.find_patterns(query=search_query, max_results=limit + 1)

            # Filter out the base pattern itself
            related_results = [r for r in results if r.pattern.metadata.pattern_id != pattern_id]

            return related_results[:limit]

        except Exception as e:
            logger.error(f"Failed to find related patterns for {pattern_id}: {e}")
            return []

    def get_stats(self) -> Dict[str, JSONValue]:
        """Get pattern store statistics."""
        try:
            all_patterns = []
            total_applications = 0
            domains = set()
            validation_counts = {"validated": 0, "unvalidated": 0, "deprecated": 0}

            # Analyze all patterns
            for memory in self.vector_store._memory_records.values():
                if memory.get("metadata", {}).get("namespace") == self.namespace:
                    try:
                        pattern_data = memory.get("content", {})
                        if isinstance(pattern_data, dict):
                            pattern = CodingPattern.from_dict(pattern_data)
                            all_patterns.append(pattern)
                            total_applications += pattern.metadata.application_count
                            domains.add(pattern.context.domain)
                            validation_counts[pattern.metadata.validation_status] += 1
                    except Exception:
                        continue

            # Calculate statistics
            if all_patterns:
                avg_effectiveness = sum(p.outcome.effectiveness_score() for p in all_patterns) / len(all_patterns)
                avg_success_rate = sum(p.outcome.success_rate for p in all_patterns) / len(all_patterns)
                avg_confidence = sum(p.outcome.confidence for p in all_patterns) / len(all_patterns)
            else:
                avg_effectiveness = avg_success_rate = avg_confidence = 0.0

            return {
                "total_patterns": len(all_patterns),
                "total_applications": total_applications,
                "unique_domains": len(domains),
                "domains": list(domains),
                "validation_status": validation_counts,
                "average_effectiveness": avg_effectiveness,
                "average_success_rate": avg_success_rate,
                "average_confidence": avg_confidence,
                "vector_store_stats": self.vector_store.get_stats(),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get pattern store stats: {e}")
            return {"error": str(e)}

    def _determine_match_reason(
        self,
        pattern: CodingPattern,
        query: str = None,
        context: ProblemContext = None,
        domain: str = None
    ) -> str:
        """Determine why this pattern was matched."""
        reasons = []

        if domain and pattern.context.domain == domain:
            reasons.append(f"domain match: {domain}")

        if context:
            if pattern.context.domain == context.domain:
                reasons.append(f"context domain match: {context.domain}")

            # Check for symptom overlap
            context_symptoms = set(context.symptoms)
            pattern_symptoms = set(pattern.context.symptoms)
            if context_symptoms.intersection(pattern_symptoms):
                reasons.append("symptom similarity")

        if query:
            # Check for keyword overlap (simplified)
            query_words = set(query.lower().split())
            pattern_text = pattern.to_searchable_text().lower()
            if any(word in pattern_text for word in query_words):
                reasons.append("keyword match")

        if not reasons:
            reasons.append("semantic similarity")

        return ", ".join(reasons)

    def export_patterns(self, format: str = "json") -> str:
        """Export all patterns in specified format."""
        try:
            all_patterns = []

            for memory in self.vector_store._memory_records.values():
                if memory.get("metadata", {}).get("namespace") == self.namespace:
                    try:
                        pattern_data = memory.get("content", {})
                        if isinstance(pattern_data, dict):
                            all_patterns.append(pattern_data)
                    except Exception:
                        continue

            if format == "json":
                return json.dumps({
                    "patterns": all_patterns,
                    "export_timestamp": datetime.now().isoformat(),
                    "total_count": len(all_patterns)
                }, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Failed to export patterns: {e}")
            return json.dumps({"error": str(e)})

    def clear_patterns(self) -> bool:
        """Clear all patterns from the store."""
        try:
            # Get all pattern memory keys
            pattern_keys = []
            for key, memory in self.vector_store._memory_records.items():
                if memory.get("metadata", {}).get("namespace") == self.namespace:
                    pattern_keys.append(key)

            # Remove all pattern memories
            for key in pattern_keys:
                self.vector_store.remove_memory(key)

            # Clear cache
            self._patterns_cache.clear()

            logger.info(f"Cleared {len(pattern_keys)} patterns from store")
            return True

        except Exception as e:
            logger.error(f"Failed to clear patterns: {e}")
            return False