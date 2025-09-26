"""
Enhanced Memory Store with VectorStore Integration.

Provides unified memory access with both tag-based and semantic search capabilities.
Automatically populates VectorStore during normal memory operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from shared.type_definitions.json import JSONValue
from .memory import MemoryStore
from .vector_store import VectorStore, SimilarityResult
import json

logger = logging.getLogger(__name__)


class EnhancedMemoryStore(MemoryStore):
    """
    Enhanced memory store that integrates tag-based and semantic search.

    This store automatically populates the VectorStore during normal memory operations,
    ensuring that all stored memories are available for both tag-based and semantic search.
    """

    def __init__(self, vector_store: Optional[VectorStore] = None, embedding_provider: str = "sentence-transformers"):
        """
        Initialize enhanced memory store.

        Args:
            vector_store: Optional VectorStore instance
            embedding_provider: Embedding provider for semantic search
        """
        self._memories: Dict[str, Dict[str, JSONValue]] = {}
        self.vector_store = vector_store or VectorStore(embedding_provider=embedding_provider)
        self._learning_triggers = []

        logger.info(f"EnhancedMemoryStore initialized with embedding provider: {embedding_provider}")

    def store(self, key: str, content: Any, tags: List[str]) -> None:
        """
        Store content with automatic VectorStore integration.

        Args:
            key: Unique memory key
            content: Content to store
            tags: Tags for categorization
        """
        # Create memory record with timestamp
        memory_record = {
            "key": key,
            "content": content,
            "tags": tags,
            "timestamp": datetime.now().isoformat(),
        }

        # Store in traditional memory
        self._memories[key] = memory_record

        # Add to vector store for semantic search
        try:
            self.vector_store.add_memory(key, memory_record)
            logger.debug(f"Added memory to VectorStore: {key}")
        except Exception as e:
            logger.warning(f"Failed to add memory to VectorStore: {e}")

        # Check for learning trigger conditions
        self._check_learning_triggers(memory_record)

        logger.debug(f"Stored memory with key: {key}, tags: {tags}")

    def search(self, tags: List[str]) -> List[dict[str, JSONValue]]:
        """
        Return memories that have any of the specified tags.

        Args:
            tags: List of tags to search for

        Returns:
            List of matching memory records
        """
        if not tags:
            return []

        matches = []
        tag_set = set(tags)

        for memory in self._memories.values():
            memory_tags = set(memory.get("tags", []))
            if tag_set.intersection(memory_tags):
                matches.append(memory)

        # Sort by timestamp (newest first)
        matches.sort(key=lambda x: x["timestamp"], reverse=True)
        logger.debug(f"Found {len(matches)} memories matching tags: {tags}")
        return matches

    def semantic_search(self, query: str, top_k: int = 10, min_similarity: float = 0.5) -> List[dict[str, JSONValue]]:
        """
        Perform semantic search using VectorStore.

        Args:
            query: Search query
            top_k: Maximum number of results
            min_similarity: Minimum similarity threshold

        Returns:
            List of semantically similar memories with relevance scores
        """
        try:
            # Get all memories for search
            all_memories = list(self._memories.values())

            if not all_memories:
                return []

            # Perform semantic search
            results = self.vector_store.hybrid_search(query, all_memories, top_k)

            # Filter by minimum similarity and convert to memory format
            filtered_results = []
            for result in results:
                if result.similarity_score >= min_similarity:
                    memory_with_score = result.memory.copy()
                    memory_with_score['relevance_score'] = result.similarity_score
                    memory_with_score['search_type'] = result.search_type
                    filtered_results.append(memory_with_score)

            logger.debug(f"Semantic search for '{query}' returned {len(filtered_results)} results")
            return filtered_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def combined_search(self, tags: List[str] = None, query: str = None, top_k: int = 10) -> List[dict[str, JSONValue]]:
        """
        Perform combined tag-based and semantic search.

        Args:
            tags: Optional tags to filter by
            query: Optional semantic query
            top_k: Maximum number of results

        Returns:
            Combined search results with relevance scores
        """
        if tags and query:
            # First filter by tags, then semantic search on filtered results
            tag_filtered = self.search(tags)
            if tag_filtered:
                semantic_results = self.vector_store.hybrid_search(query, tag_filtered, top_k)
                return [
                    {
                        **result.memory,
                        "relevance_score": result.similarity_score,
                        "search_type": result.search_type,
                    }
                    for result in semantic_results
                ]
            else:
                return []

        elif tags:
            # Tag-based search only
            return self.search(tags)[:top_k]

        elif query:
            # Semantic search only
            return self.semantic_search(query, top_k)

        else:
            # Return all memories
            return self.get_all()[:top_k]

    def get_all(self) -> List[dict[str, JSONValue]]:
        """Return all memories sorted by timestamp (newest first)."""
        all_memories = list(self._memories.values())
        all_memories.sort(key=lambda x: x["timestamp"], reverse=True)
        logger.debug(f"Retrieved all {len(all_memories)} memories")
        return all_memories

    def get_learning_patterns(self, min_confidence: float = 0.7) -> List[dict[str, JSONValue]]:
        """
        Extract learning patterns from stored memories.

        Args:
            min_confidence: Minimum confidence threshold for patterns

        Returns:
            List of extracted learning patterns
        """
        try:
            all_memories = self.get_all()
            patterns = []

            # Pattern 1: Successful tool usage patterns
            tool_patterns = self._extract_tool_patterns(all_memories)
            patterns.extend([p for p in tool_patterns if p.get('confidence', 0) >= min_confidence])

            # Pattern 2: Error resolution patterns
            error_patterns = self._extract_error_patterns(all_memories)
            patterns.extend([p for p in error_patterns if p.get('confidence', 0) >= min_confidence])

            # Pattern 3: Agent interaction patterns
            interaction_patterns = self._extract_interaction_patterns(all_memories)
            patterns.extend([p for p in interaction_patterns if p.get('confidence', 0) >= min_confidence])

            logger.info(f"Extracted {len(patterns)} learning patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error extracting learning patterns: {e}")
            return []

    def _extract_tool_patterns(self, memories: List[dict[str, JSONValue]]) -> List[dict[str, JSONValue]]:
        """Extract tool usage patterns from memories."""
        patterns = []

        # Find tool-related memories
        tool_memories = [m for m in memories if 'tool' in m.get('tags', [])]

        if len(tool_memories) < 3:
            return patterns

        # Group by tool type
        tool_groups = {}
        for memory in tool_memories:
            content = str(memory.get('content', ''))

            # Extract tool names (simplified pattern matching)
            for tool in ['Read', 'Write', 'Edit', 'Grep', 'Bash', 'TodoWrite']:
                if tool in content:
                    if tool not in tool_groups:
                        tool_groups[tool] = []
                    tool_groups[tool].append(memory)

        # Create patterns for frequently used tools
        for tool, tool_memories in tool_groups.items():
            if len(tool_memories) >= 3:
                # Check for success indicators
                successful = [m for m in tool_memories if self._is_successful_memory(m)]
                success_rate = len(successful) / len(tool_memories)

                if success_rate > 0.7:
                    patterns.append({
                        'pattern_id': f'tool_success_{tool.lower()}',
                        'type': 'tool_pattern',
                        'tool': tool,
                        'usage_count': len(tool_memories),
                        'success_rate': success_rate,
                        'confidence': min(0.9, len(tool_memories) / 10),
                        'description': f'Tool {tool} shows high success rate ({success_rate:.1%})',
                        'actionable_insight': f'Prioritize {tool} for similar tasks',
                        'evidence': tool_memories[:2]
                    })

        return patterns

    def _extract_error_patterns(self, memories: List[dict[str, JSONValue]]) -> List[dict[str, JSONValue]]:
        """Extract error resolution patterns from memories."""
        patterns = []

        # Find error-related memories
        error_memories = [m for m in memories if 'error' in m.get('tags', [])]

        if len(error_memories) < 2:
            return patterns

        # Group by error types (simplified)
        error_groups = {}
        for memory in error_memories:
            content = str(memory.get('content', '')).lower()

            # Simple error type detection
            if 'permission' in content:
                error_type = 'permission_error'
            elif 'not found' in content or 'missing' in content:
                error_type = 'file_not_found'
            elif 'timeout' in content:
                error_type = 'timeout_error'
            elif 'connection' in content:
                error_type = 'connection_error'
            else:
                error_type = 'general_error'

            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(memory)

        # Create patterns for common errors
        for error_type, error_memories in error_groups.items():
            if len(error_memories) >= 2:
                # Check for resolution patterns
                resolved = [m for m in error_memories if self._is_resolved_error(m)]
                resolution_rate = len(resolved) / len(error_memories)

                patterns.append({
                    'pattern_id': f'error_resolution_{error_type}',
                    'type': 'error_resolution',
                    'error_type': error_type,
                    'occurrence_count': len(error_memories),
                    'resolution_rate': resolution_rate,
                    'confidence': min(0.8, len(error_memories) / 5),
                    'description': f'Error type {error_type} with {resolution_rate:.1%} resolution rate',
                    'actionable_insight': f'Apply known resolution patterns for {error_type}',
                    'evidence': resolved[:2] if resolved else error_memories[:2]
                })

        return patterns

    def _extract_interaction_patterns(self, memories: List[dict[str, JSONValue]]) -> List[dict[str, JSONValue]]:
        """Extract agent interaction patterns from memories."""
        patterns = []

        # Find handoff-related memories
        handoff_memories = [m for m in memories if any(tag in ['handoff', 'agent', 'communication'] for tag in m.get('tags', []))]

        if len(handoff_memories) < 3:
            return patterns

        # Analyze handoff success
        successful_handoffs = [m for m in handoff_memories if self._is_successful_memory(m)]
        success_rate = len(successful_handoffs) / len(handoff_memories)

        if success_rate > 0.6:
            patterns.append({
                'pattern_id': 'agent_interaction_success',
                'type': 'interaction_pattern',
                'interaction_type': 'handoff',
                'total_interactions': len(handoff_memories),
                'success_rate': success_rate,
                'confidence': min(0.8, len(handoff_memories) / 8),
                'description': f'Agent interactions have {success_rate:.1%} success rate',
                'actionable_insight': 'Current handoff patterns are effective, maintain approach',
                'evidence': successful_handoffs[:2]
            })

        return patterns

    def _is_successful_memory(self, memory: Dict[str, JSONValue]) -> bool:
        """Check if a memory indicates success."""
        content = str(memory.get('content', '')).lower()
        success_indicators = ['success', 'completed', 'resolved', 'fixed', 'working', 'done']
        return any(indicator in content for indicator in success_indicators)

    def _is_resolved_error(self, memory: Dict[str, JSONValue]) -> bool:
        """Check if an error memory indicates resolution."""
        content = str(memory.get('content', '')).lower()
        resolution_indicators = ['resolved', 'fixed', 'solved', 'recovered', 'retry succeeded']
        return any(indicator in content for indicator in resolution_indicators)

    def _check_learning_triggers(self, memory_record: Dict[str, JSONValue]) -> None:
        """Check if memory triggers learning consolidation."""
        tags = memory_record.get('tags', [])
        content = str(memory_record.get('content', '')).lower()

        # Trigger learning for certain types of memories
        learning_trigger_conditions = [
            'success' in tags and 'task_completion' in tags,
            'error' in tags and 'resolved' in content,
            'optimization' in tags,
            'pattern' in tags,
            len(self._memories) % 50 == 0  # Every 50 memories
        ]

        if any(learning_trigger_conditions):
            self._learning_triggers.append({
                'trigger_time': memory_record['timestamp'],
                'trigger_key': memory_record['key'],
                'trigger_reason': 'automatic_learning_consolidation',
                'memory_count': len(self._memories)
            })

            logger.info(f"Learning trigger activated for memory: {memory_record['key']}")

    def get_learning_triggers(self) -> List[dict[str, JSONValue]]:
        """Get pending learning triggers."""
        return self._learning_triggers.copy()

    def clear_learning_triggers(self) -> None:
        """Clear processed learning triggers."""
        self._learning_triggers.clear()

    def get_vector_store_stats(self) -> Dict[str, JSONValue]:
        """Get VectorStore statistics."""
        try:
            return self.vector_store.get_stats()
        except Exception as e:
            logger.error(f"Error getting VectorStore stats: {e}")
            return {'error': str(e)}

    def optimize_vector_store(self) -> Dict[str, JSONValue]:
        """Optimize VectorStore by ensuring all memories have embeddings."""
        try:
            optimization_stats = {
                'memories_processed': 0,
                'embeddings_generated': 0,
                'errors': 0
            }

            for key, memory in self._memories.items():
                optimization_stats['memories_processed'] += 1

                try:
                    # Check if memory exists in vector store
                    if key not in self.vector_store._embeddings:
                        self.vector_store.add_memory(key, memory)
                        optimization_stats['embeddings_generated'] += 1

                except Exception as e:
                    optimization_stats['errors'] += 1
                    logger.warning(f"Error optimizing memory {key}: {e}")

            logger.info(f"VectorStore optimization completed: {optimization_stats}")
            return optimization_stats

        except Exception as e:
            logger.error(f"VectorStore optimization failed: {e}")
            return {'error': str(e)}

    def export_for_learning(self, session_id: str = None) -> Dict[str, JSONValue]:
        """Export memories in format suitable for learning analysis."""
        try:
            # Get memories for the session or all memories
            if session_id:
                session_memories = [m for m in self._memories.values()
                                   if f"session:{session_id}" in m.get('tags', [])]
            else:
                session_memories = list(self._memories.values())

            # Extract patterns
            patterns = self.get_learning_patterns()

            # Get vector store stats
            vector_stats = self.get_vector_store_stats()

            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'total_memories': len(session_memories),
                'memory_records': session_memories,
                'extracted_patterns': patterns,
                'vector_store_stats': vector_stats,
                'learning_triggers': self.get_learning_triggers()
            }

            logger.info(f"Exported {len(session_memories)} memories for learning analysis")
            return export_data

        except Exception as e:
            logger.error(f"Export for learning failed: {e}")
            return {'error': str(e)}


def create_enhanced_memory_store(embedding_provider: str = "sentence-transformers") -> EnhancedMemoryStore:
    """
    Factory function to create an EnhancedMemoryStore.

    Args:
        embedding_provider: Embedding provider for semantic search

    Returns:
        Configured EnhancedMemoryStore instance
    """
    return EnhancedMemoryStore(embedding_provider=embedding_provider)