"""
Enhanced Memory Store with VectorStore Integration.

Provides unified memory access with both tag-based and semantic search capabilities.
Automatically populates VectorStore during normal memory operations.
"""

import json
import logging
from datetime import datetime
from typing import cast

from shared.models.memory import MemorySearchResult
from shared.type_definitions.json import JSONValue

from .memory import MemoryStore
from .type_conversion_utils import create_memory_converter
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class EnhancedMemoryStore(MemoryStore):
    """
    Enhanced memory store that integrates tag-based and semantic search.

    This store automatically populates the VectorStore during normal memory operations,
    ensuring that all stored memories are available for both tag-based and semantic search.
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedding_provider: str = "sentence-transformers",
    ):
        """
        Initialize enhanced memory store.

        Args:
            vector_store: Optional VectorStore instance
            embedding_provider: Embedding provider for semantic search
        """
        self._memories: dict[str, dict[str, JSONValue]] = {}
        self.vector_store = vector_store or VectorStore(embedding_provider=embedding_provider)
        self._learning_triggers: list[str] = []
        self.memory_converter = create_memory_converter()

        logger.info(
            f"EnhancedMemoryStore initialized with embedding provider: {embedding_provider}"
        )

    def store(self, key: str, content: JSONValue, tags: list[str]) -> None:
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

    def store_memory(
        self,
        key: str,
        value: JSONValue,
        tags: list[str],
        metadata: dict[str, JSONValue] | None = None,
    ) -> None:
        """
        Store memory with unified interface (facade compatibility).

        Args:
            key: Unique memory key
            value: Content to store
            tags: Tags for categorization
            metadata: Additional metadata (ignored for now)
        """
        self.store(key, value, tags)

    def get_memory(self, key: str) -> JSONValue | None:
        """
        Get memory by key (facade compatibility).

        Args:
            key: Memory key

        Returns:
            Memory content or None if not found
        """
        memory_record = self._memories.get(key)
        if memory_record:
            return memory_record.get("content")
        return None

    def get_memory_count(self) -> int:
        """
        Get total number of memories (facade compatibility).

        Returns:
            Number of stored memories
        """
        return len(self._memories)

    def search_memories(
        self, query: str, tags: list[str] | None = None, limit: int = 10
    ) -> list[dict[str, JSONValue]]:
        """
        Search memories using text query and optional tags (facade compatibility).

        Args:
            query: Search query text
            tags: Optional tags to filter by
            limit: Maximum results to return

        Returns:
            List of matching memory records
        """
        if tags:
            # Use existing tag-based search
            result = self.search(tags)
            memories = result.memories[:limit]
        else:
            # Use semantic search
            memories = self.semantic_search(query, top_k=limit)

        return memories

    def search(self, tags: list[str]) -> MemorySearchResult:
        """
        Return memories that have any of the specified tags.

        Args:
            tags: List of tags to search for

        Returns:
            List of matching memory records
        """
        if not tags:
            return MemorySearchResult(
                records=[],
                total_count=0,
                search_query={"tags": cast(JSONValue, [])},
                execution_time_ms=0,
            )

        matches = []
        tag_set = set(tags)

        for memory in self._memories.values():
            tags_value = memory.get("tags", [])
            memory_tags = set(self.memory_converter.extract_tags_list(tags_value))
            if tag_set.intersection(memory_tags):
                matches.append(memory)

        # Sort by timestamp (newest first) with type guard
        def sort_key(x: dict[str, JSONValue]) -> str:
            timestamp = x.get("timestamp")
            return self.memory_converter.safe_string_conversion(timestamp)

        matches.sort(key=sort_key, reverse=True)
        logger.debug(f"Found {len(matches)} memories matching tags: {tags}")

        # Convert to MemorySearchResult
        memory_records = []
        for match in matches:
            record = self.memory_converter.memory_dict_to_record(match)
            if record:
                memory_records.append(record)
            else:
                logger.warning(
                    f"Failed to convert memory to MemoryRecord: {match.get('key', 'unknown')}"
                )

        search_query: dict[str, JSONValue] = {"tags": cast(JSONValue, tags)}
        return MemorySearchResult(
            records=memory_records,
            total_count=len(memory_records),
            search_query=search_query,
            execution_time_ms=0,
        )

    def semantic_search(
        self, query: str, top_k: int = 10, min_similarity: float = 0.5
    ) -> list[dict[str, JSONValue]]:
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
                    memory_with_score["relevance_score"] = result.similarity_score
                    memory_with_score["search_type"] = result.search_type
                    filtered_results.append(memory_with_score)

            logger.debug(f"Semantic search for '{query}' returned {len(filtered_results)} results")
            return filtered_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _filter_memories_by_tags(self, tags: list[str]) -> list[dict[str, JSONValue]]:
        """
        Filter memories by tags and return as list of dictionaries.

        Args:
            tags: List of tags to filter by

        Returns:
            List of filtered memory dictionaries
        """
        search_result = self.search(tags)
        filtered_memories = []

        for record in search_result.records:
            memory_dict = self.memory_converter.record_to_dict(record)
            filtered_memories.append(memory_dict)

        return filtered_memories

    def _perform_semantic_search_on_memories(
        self, query: str, memories: list[dict[str, JSONValue]], top_k: int
    ) -> list[dict[str, JSONValue]]:
        """
        Perform semantic search on a list of memories.

        Args:
            query: Search query
            memories: List of memory dictionaries to search
            top_k: Maximum number of results

        Returns:
            List of semantically similar memories with relevance scores
        """
        if not memories:
            return []

        try:
            semantic_results = self.vector_store.hybrid_search(query, memories, top_k)
            return [
                self.memory_converter.add_relevance_score(
                    result.memory, result.similarity_score, result.search_type
                )
                for result in semantic_results
            ]
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _format_tag_only_results(
        self, memories: list[dict[str, JSONValue]], top_k: int
    ) -> list[dict[str, JSONValue]]:
        """
        Format tag-based search results.

        Args:
            memories: List of memory dictionaries
            top_k: Maximum number of results

        Returns:
            Formatted list of memory dictionaries
        """
        return memories[:top_k]

    def _format_all_memories_results(self, top_k: int) -> list[dict[str, JSONValue]]:
        """
        Format all memories results.

        Args:
            top_k: Maximum number of results

        Returns:
            Formatted list of all memory dictionaries
        """
        all_result = self.get_all()
        result_list = []

        for record in all_result.records[:top_k]:
            record_dict = self.memory_converter.record_to_dict(record)
            result_list.append(record_dict)

        return result_list

    def combined_search(
        self, tags: list[str] = None, query: str = None, top_k: int = 10
    ) -> list[dict[str, JSONValue]]:
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
            tag_filtered = self._filter_memories_by_tags(tags)
            return self._perform_semantic_search_on_memories(query, tag_filtered, top_k)

        elif tags:
            # Tag-based search only
            tag_filtered = self._filter_memories_by_tags(tags)
            return self._format_tag_only_results(tag_filtered, top_k)

        elif query:
            # Semantic search only
            return self.semantic_search(query, top_k)

        else:
            # Return all memories
            return self._format_all_memories_results(top_k)

    def get_all(self) -> MemorySearchResult:
        """Return all memories sorted by timestamp (newest first)."""
        all_memories = list(self._memories.values())

        # Sort by timestamp with type guard
        def sort_key(x: dict[str, JSONValue]) -> str:
            timestamp = x.get("timestamp")
            return self.memory_converter.safe_string_conversion(timestamp)

        all_memories.sort(key=sort_key, reverse=True)
        logger.debug(f"Retrieved all {len(all_memories)} memories")

        # Convert to MemorySearchResult
        memory_records = []
        for memory in all_memories:
            record = self.memory_converter.memory_dict_to_record(memory)
            if record:
                memory_records.append(record)
            else:
                logger.warning(
                    f"Failed to convert memory to MemoryRecord: {memory.get('key', 'unknown')}"
                )

        return MemorySearchResult(
            records=memory_records,
            total_count=len(memory_records),
            search_query={},
            execution_time_ms=0,
        )

    def get_learning_patterns(self, min_confidence: float = 0.7) -> list[dict[str, JSONValue]]:
        """
        Extract learning patterns from stored memories.

        Args:
            min_confidence: Minimum confidence threshold for patterns

        Returns:
            List of extracted learning patterns
        """
        try:
            all_result = self.get_all()
            all_memories = []
            for record in all_result.records:
                memory_dict: dict[str, JSONValue] = {
                    "key": record.key,
                    "content": record.content,
                    "tags": cast(JSONValue, record.tags),
                    "timestamp": record.timestamp.isoformat(),
                }
                all_memories.append(memory_dict)
            patterns: list[dict[str, JSONValue]] = []

            # Pattern 1: Successful tool usage patterns
            tool_patterns = self._extract_tool_patterns(all_memories)
            for p in tool_patterns:
                conf = p.get("confidence", 0)
                if isinstance(conf, (int, float)) and conf >= min_confidence:
                    patterns.append(p)

            # Pattern 2: Error resolution patterns
            error_patterns = self._extract_error_patterns(all_memories)
            for p in error_patterns:
                conf = p.get("confidence", 0)
                if isinstance(conf, (int, float)) and conf >= min_confidence:
                    patterns.append(p)

            # Pattern 3: Agent interaction patterns
            interaction_patterns = self._extract_interaction_patterns(all_memories)
            for p in interaction_patterns:
                conf = p.get("confidence", 0)
                if isinstance(conf, (int, float)) and conf >= min_confidence:
                    patterns.append(p)

            logger.info(f"Extracted {len(patterns)} learning patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error extracting learning patterns: {e}")
            return []

    def _extract_tool_patterns(
        self, memories: list[dict[str, JSONValue]]
    ) -> list[dict[str, JSONValue]]:
        """Extract tool usage patterns from memories."""
        patterns: list[dict[str, JSONValue]] = []

        # Find tool-related memories
        tool_memories = []
        for m in memories:
            tags = m.get("tags", [])
            tags_list = self.memory_converter.extract_tags_list(tags)
            if any("tool" in tag for tag in tags_list):
                tool_memories.append(m)

        if len(tool_memories) < 3:
            return patterns

        # Group by tool type
        tool_groups: dict[str, list[dict[str, JSONValue]]] = {}
        for memory in tool_memories:
            content = str(memory.get("content", ""))

            # Extract tool names (simplified pattern matching)
            for tool in ["Read", "Write", "Edit", "Grep", "Bash", "TodoWrite"]:
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
                    patterns.append(
                        {
                            "pattern_id": f"tool_success_{tool.lower()}",
                            "type": "tool_pattern",
                            "tool": tool,
                            "usage_count": len(tool_memories),
                            "success_rate": success_rate,
                            "confidence": min(0.9, len(tool_memories) / 10),
                            "description": f"Tool {tool} shows high success rate ({success_rate:.1%})",
                            "actionable_insight": f"Prioritize {tool} for similar tasks",
                            "evidence": cast(JSONValue, tool_memories[:2]),
                        }
                    )

        return patterns

    def _extract_error_patterns(
        self, memories: list[dict[str, JSONValue]]
    ) -> list[dict[str, JSONValue]]:
        """Extract error resolution patterns from memories."""
        patterns: list[dict[str, JSONValue]] = []

        # Find error-related memories
        error_memories = []
        for m in memories:
            tags = m.get("tags", [])
            tags_list = self.memory_converter.extract_tags_list(tags)
            if any("error" in tag for tag in tags_list):
                error_memories.append(m)

        if len(error_memories) < 2:
            return patterns

        # Group by error types (simplified)
        error_groups: dict[str, list[dict[str, JSONValue]]] = {}
        for memory in error_memories:
            content = str(memory.get("content", "")).lower()

            # Simple error type detection
            if "permission" in content:
                error_type = "permission_error"
            elif "not found" in content or "missing" in content:
                error_type = "file_not_found"
            elif "timeout" in content:
                error_type = "timeout_error"
            elif "connection" in content:
                error_type = "connection_error"
            else:
                error_type = "general_error"

            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(memory)

        # Create patterns for common errors
        for error_type, error_memories in error_groups.items():
            if len(error_memories) >= 2:
                # Check for resolution patterns
                resolved = [m for m in error_memories if self._is_resolved_error(m)]
                resolution_rate = len(resolved) / len(error_memories)

                patterns.append(
                    {
                        "pattern_id": f"error_resolution_{error_type}",
                        "type": "error_resolution",
                        "error_type": error_type,
                        "occurrence_count": len(error_memories),
                        "resolution_rate": resolution_rate,
                        "confidence": min(0.8, len(error_memories) / 5),
                        "description": f"Error type {error_type} with {resolution_rate:.1%} resolution rate",
                        "actionable_insight": f"Apply known resolution patterns for {error_type}",
                        "evidence": cast(
                            JSONValue, resolved[:2] if resolved else error_memories[:2]
                        ),
                    }
                )

        return patterns

    def _extract_interaction_patterns(
        self, memories: list[dict[str, JSONValue]]
    ) -> list[dict[str, JSONValue]]:
        """Extract agent interaction patterns from memories."""
        patterns: list[dict[str, JSONValue]] = []

        # Find handoff-related memories
        handoff_memories = []
        for m in memories:
            tags = m.get("tags", [])
            tags_list = self.memory_converter.extract_tags_list(tags)
            if any(keyword in tags_list for keyword in ["handoff", "agent", "communication"]):
                handoff_memories.append(m)

        if len(handoff_memories) < 3:
            return patterns

        # Analyze handoff success
        successful_handoffs = [m for m in handoff_memories if self._is_successful_memory(m)]
        success_rate = len(successful_handoffs) / len(handoff_memories)

        if success_rate > 0.6:
            patterns.append(
                {
                    "pattern_id": "agent_interaction_success",
                    "type": "interaction_pattern",
                    "interaction_type": "handoff",
                    "total_interactions": len(handoff_memories),
                    "success_rate": success_rate,
                    "confidence": min(0.8, len(handoff_memories) / 8),
                    "description": f"Agent interactions have {success_rate:.1%} success rate",
                    "actionable_insight": "Current handoff patterns are effective, maintain approach",
                    "evidence": cast(JSONValue, successful_handoffs[:2]),
                }
            )

        return patterns

    def _is_successful_memory(self, memory: dict[str, JSONValue]) -> bool:
        """Check if a memory indicates success."""
        content = str(memory.get("content", "")).lower()
        success_indicators = ["success", "completed", "resolved", "fixed", "working", "done"]
        return any(indicator in content for indicator in success_indicators)

    def _is_resolved_error(self, memory: dict[str, JSONValue]) -> bool:
        """Check if an error memory indicates resolution."""
        content = str(memory.get("content", "")).lower()
        resolution_indicators = ["resolved", "fixed", "solved", "recovered", "retry succeeded"]
        return any(indicator in content for indicator in resolution_indicators)

    def _check_learning_triggers(self, memory_record: dict[str, JSONValue]) -> None:
        """Check if memory triggers learning consolidation."""
        tags = memory_record.get("tags", [])
        content = str(memory_record.get("content", "")).lower()

        # Trigger learning for certain types of memories
        tags_list = self.memory_converter.extract_tags_list(tags)
        learning_trigger_conditions = [
            "success" in tags_list and "task_completion" in tags_list,
            "error" in tags_list and "resolved" in content,
            "optimization" in tags_list,
            "pattern" in tags_list,
            len(self._memories) % 50 == 0,  # Every 50 memories
        ]

        if any(learning_trigger_conditions):
            trigger_dict = {
                "trigger_time": str(memory_record.get("timestamp", "")),
                "trigger_key": str(memory_record.get("key", "")),
                "trigger_reason": "automatic_learning_consolidation",
                "memory_count": len(self._memories),
            }
            trigger_str = json.dumps(trigger_dict)  # Convert to string for the List[str] type
            self._learning_triggers.append(trigger_str)

            logger.info(f"Learning trigger activated for memory: {memory_record['key']}")

    def get_learning_triggers(self) -> list[dict[str, JSONValue]]:
        """Get pending learning triggers."""
        # Convert string triggers back to dicts
        result = []
        for trigger_str in self._learning_triggers:
            try:
                trigger_dict = json.loads(trigger_str)
                result.append(cast(dict[str, JSONValue], trigger_dict))
            except (json.JSONDecodeError, TypeError):
                pass
        return result

    def clear_learning_triggers(self) -> None:
        """Clear processed learning triggers."""
        self._learning_triggers.clear()

    def get_vector_store_stats(self) -> dict[str, JSONValue]:
        """Get VectorStore statistics."""
        try:
            return self.vector_store.get_stats()
        except Exception as e:
            logger.error(f"Error getting VectorStore stats: {e}")
            return {"error": str(e)}

    def optimize_vector_store(self) -> dict[str, JSONValue]:
        """Optimize VectorStore by ensuring all memories have embeddings."""
        try:
            optimization_stats: dict[str, JSONValue] = {
                "memories_processed": 0,
                "embeddings_generated": 0,
                "errors": 0,
            }

            for key, memory in self._memories.items():
                # Type-safe increment
                memories_processed = optimization_stats["memories_processed"]
                if isinstance(memories_processed, int):
                    optimization_stats["memories_processed"] = memories_processed + 1

                try:
                    # Check if memory exists in vector store
                    if key not in self.vector_store._embeddings:
                        self.vector_store.add_memory(key, memory)
                        embeddings_generated = optimization_stats["embeddings_generated"]
                        if isinstance(embeddings_generated, int):
                            optimization_stats["embeddings_generated"] = embeddings_generated + 1

                except Exception as e:
                    errors_count = optimization_stats["errors"]
                    if isinstance(errors_count, int):
                        optimization_stats["errors"] = errors_count + 1
                    logger.warning(f"Error optimizing memory {key}: {e}")

            logger.info(f"VectorStore optimization completed: {optimization_stats}")
            return cast(dict[str, JSONValue], optimization_stats)

        except Exception as e:
            logger.error(f"VectorStore optimization failed: {e}")
            return {"error": str(e)}

    def export_for_learning(self, session_id: str = None) -> dict[str, JSONValue]:
        """Export memories in format suitable for learning analysis."""
        try:
            # Get memories for the session or all memories
            if session_id:
                session_memories = []
                for m in self._memories.values():
                    tags = m.get("tags", [])
                    tags_list = self.memory_converter.extract_tags_list(tags)
                    if f"session:{session_id}" in tags_list:
                        session_memories.append(m)
            else:
                session_memories = list(self._memories.values())

            # Extract patterns
            patterns = self.get_learning_patterns()

            # Get vector store stats
            vector_stats = self.get_vector_store_stats()

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "total_memories": len(session_memories),
                "memory_records": session_memories,
                "extracted_patterns": patterns,
                "vector_store_stats": vector_stats,
                "learning_triggers": self.get_learning_triggers(),
            }

            logger.info(f"Exported {len(session_memories)} memories for learning analysis")
            return cast(dict[str, JSONValue], export_data)

        except Exception as e:
            logger.error(f"Export for learning failed: {e}")
            return {"error": str(e)}


def create_enhanced_memory_store(
    embedding_provider: str = "sentence-transformers",
) -> EnhancedMemoryStore:
    """
    Factory function to create an EnhancedMemoryStore.

    Args:
        embedding_provider: Embedding provider for semantic search

    Returns:
        Configured EnhancedMemoryStore instance
    """
    return EnhancedMemoryStore(embedding_provider=embedding_provider)
