"""
Enhanced Memory Architecture (v2) for Agent Swarms

Implements industry best practices from 2024-2025 research:
- Explicit episodic vs semantic memory separation
- Attention-weighted memory importance scoring
- Enhanced memory consolidation with semantic clustering
- Multimodal memory support framework
- Improved performance optimizations
"""

import logging
import hashlib
import json
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from shared.type_definitions.json import JSONValue
from collections import defaultdict, Counter
from enum import Enum, IntEnum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Memory type classification based on cognitive science."""

    EPISODIC = "episodic"  # Events, conversations, interactions
    SEMANTIC = "semantic"  # Facts, knowledge, relationships
    PROCEDURAL = "procedural"  # Skills, patterns, procedures
    WORKING = "working"  # Temporary context, current tasks


class MemoryPriority(IntEnum):
    """Memory importance levels for prioritization."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MemoryModality(Enum):
    """Content type for multimodal memory support."""

    TEXT = "text"
    IMAGE = "image"
    STRUCTURED = "structured"
    CODE = "code"
    MULTIMODAL = "multimodal"


@dataclass
class MemoryMetadata:
    """Enhanced metadata for memory records."""

    key: str
    agent_id: str
    memory_type: MemoryType
    modality: MemoryModality
    priority: MemoryPriority
    tags: List[str]
    timestamp: str
    last_accessed: str
    access_count: int
    importance_score: float
    is_shared: bool
    consolidation_level: int = 0  # 0=original, 1=first consolidation, etc.
    parent_memory_id: Optional[str] = None
    related_memory_ids: List[str] = None

    def __post_init__(self):
        if self.related_memory_ids is None:
            self.related_memory_ids = []


@dataclass
class MemoryContent:
    """Structured memory content with embeddings."""

    raw_content: Any
    content_type: str
    text_representation: str
    embeddings: Optional[Dict[str, List[float]]] = None
    content_hash: Optional[str] = None

    def __post_init__(self):
        if self.embeddings is None:
            self.embeddings = {}
        if self.content_hash is None:
            self.content_hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate content hash for deduplication."""
        content_str = json.dumps(self.raw_content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


@dataclass
class EnhancedMemoryRecord:
    """Complete memory record with metadata and content."""

    metadata: MemoryMetadata
    content: MemoryContent

    @property
    def namespaced_key(self) -> str:
        return f"{self.metadata.agent_id}:{self.metadata.key}"

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert to dictionary for storage."""
        return {"metadata": asdict(self.metadata), "content": asdict(self.content)}

    @classmethod
    def from_dict(cls, data: Dict[str, JSONValue]) -> "EnhancedMemoryRecord":
        """Create from dictionary."""
        metadata = MemoryMetadata(**data["metadata"])
        content = MemoryContent(**data["content"])
        return cls(metadata=metadata, content=content)


class AttentionMechanism:
    """Neural pathway-inspired attention mechanism for memory importance."""

    def __init__(
        self,
        decay_rate: float = 0.1,
        frequency_weight: float = 0.3,
        recency_weight: float = 0.3,
        relevance_weight: float = 0.3,
        priority_weight: float = 0.1,
    ):
        """
        Initialize attention mechanism.

        Args:
            decay_rate: Rate at which memory importance decays over time
            frequency_weight: Weight for access frequency in importance calculation
            recency_weight: Weight for recency in importance calculation
            relevance_weight: Weight for contextual relevance
            priority_weight: Weight for explicit priority
        """
        self.decay_rate = decay_rate
        self.frequency_weight = frequency_weight
        self.recency_weight = recency_weight
        self.relevance_weight = relevance_weight
        self.priority_weight = priority_weight

    def calculate_importance_score(
        self,
        memory: EnhancedMemoryRecord,
        current_context: Optional[str] = None,
        max_access_count: int = 100,
    ) -> float:
        """
        Calculate importance score using attention-weighted approach.

        Args:
            memory: Memory record to score
            current_context: Current context for relevance calculation
            max_access_count: Maximum access count for normalization

        Returns:
            Importance score between 0.0 and 1.0
        """
        # Recency score (exponential decay)
        now = datetime.now()
        last_accessed = datetime.fromisoformat(memory.metadata.last_accessed)
        time_diff = (now - last_accessed).total_seconds() / 3600  # Hours
        recency_score = math.exp(-self.decay_rate * time_diff)

        # Frequency score (normalized access count)
        frequency_score = min(memory.metadata.access_count / max_access_count, 1.0)

        # Priority score (normalized)
        priority_score = memory.metadata.priority.value / MemoryPriority.CRITICAL.value

        # Relevance score (contextual similarity)
        relevance_score = 0.5  # Default neutral relevance
        if current_context and memory.content.embeddings.get("text"):
            # TODO: Implement semantic similarity calculation
            # This would require embedding the current_context and comparing
            relevance_score = self._calculate_semantic_similarity(
                current_context, memory.content.text_representation
            )

        # Combine scores with weights
        importance = (
            self.frequency_weight * frequency_score
            + self.recency_weight * recency_score
            + self.relevance_weight * relevance_score
            + self.priority_weight * priority_score
        )

        return min(importance, 1.0)

    def _calculate_semantic_similarity(self, context: str, memory_text: str) -> float:
        """
        Calculate semantic similarity between context and memory.

        This is a placeholder implementation. In production, this would use
        embeddings and cosine similarity.
        """
        # Simple word overlap as fallback
        context_words = set(context.lower().split())
        memory_words = set(memory_text.lower().split())

        if not context_words or not memory_words:
            return 0.0

        overlap = context_words.intersection(memory_words)
        return len(overlap) / len(context_words.union(memory_words))

    def update_memory_importance(
        self, memory: EnhancedMemoryRecord, current_context: Optional[str] = None
    ) -> float:
        """Update and return memory importance score."""
        score = self.calculate_importance_score(memory, current_context)
        memory.metadata.importance_score = score
        return score


class SemanticMemoryClusterer:
    """Cluster related memories for intelligent consolidation."""

    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize clusterer.

        Args:
            similarity_threshold: Minimum similarity for clustering
        """
        self.similarity_threshold = similarity_threshold

    def cluster_memories(
        self, memories: List[EnhancedMemoryRecord]
    ) -> List[List[EnhancedMemoryRecord]]:
        """
        Cluster memories by semantic similarity.

        Args:
            memories: List of memory records to cluster

        Returns:
            List of memory clusters
        """
        if not memories:
            return []

        clusters = []
        unclustered = memories.copy()

        while unclustered:
            # Start new cluster with first unclustered memory
            seed_memory = unclustered.pop(0)
            cluster = [seed_memory]

            # Find similar memories
            similar_memories = []
            for memory in unclustered:
                if self._are_memories_similar(seed_memory, memory):
                    similar_memories.append(memory)

            # Add similar memories to cluster
            for memory in similar_memories:
                cluster.append(memory)
                unclustered.remove(memory)

            clusters.append(cluster)

        return clusters

    def _are_memories_similar(
        self, memory1: EnhancedMemoryRecord, memory2: EnhancedMemoryRecord
    ) -> bool:
        """
        Determine if two memories are similar enough to cluster.

        Args:
            memory1: First memory
            memory2: Second memory

        Returns:
            True if memories should be clustered together
        """
        # Check tag overlap
        tags1 = set(memory1.metadata.tags)
        tags2 = set(memory2.metadata.tags)
        tag_similarity = (
            len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            if tags1.union(tags2)
            else 0
        )

        # Check content similarity (simplified)
        content_similarity = self._text_similarity(
            memory1.content.text_representation, memory2.content.text_representation
        )

        # Check temporal proximity
        time1 = datetime.fromisoformat(memory1.metadata.timestamp)
        time2 = datetime.fromisoformat(memory2.metadata.timestamp)
        time_diff_hours = abs((time1 - time2).total_seconds()) / 3600
        temporal_similarity = max(
            0, 1 - time_diff_hours / 24
        )  # Similarity decreases over 24 hours

        # Combined similarity score
        combined_similarity = (
            0.4 * content_similarity + 0.4 * tag_similarity + 0.2 * temporal_similarity
        )

        return combined_similarity >= self.similarity_threshold

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0


class EnhancedMemoryStore(ABC):
    """Abstract interface for enhanced memory storage backends."""

    @abstractmethod
    def store_memory(self, memory: EnhancedMemoryRecord) -> None:
        """Store a memory record."""
        pass

    @abstractmethod
    def retrieve_memory(
        self, agent_id: str, key: str
    ) -> Optional[EnhancedMemoryRecord]:
        """Retrieve a specific memory."""
        pass

    @abstractmethod
    def search_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        include_shared: bool = True,
        min_importance: float = 0.0,
        limit: int = 100,
    ) -> List[EnhancedMemoryRecord]:
        """Search memories with advanced filtering."""
        pass

    @abstractmethod
    def get_agent_memories(
        self, agent_id: str, memory_type: Optional[MemoryType] = None
    ) -> List[EnhancedMemoryRecord]:
        """Get all memories for an agent."""
        pass

    @abstractmethod
    def remove_memory(self, agent_id: str, key: str) -> bool:
        """Remove a memory."""
        pass

    @abstractmethod
    def get_memory_stats(self, agent_id: Optional[str] = None) -> Dict[str, JSONValue]:
        """Get memory statistics."""
        pass


class EnhancedInMemoryStore(EnhancedMemoryStore):
    """Enhanced in-memory implementation with optimization features."""

    def __init__(self, max_memories_per_agent: int = 10000):
        """
        Initialize enhanced in-memory store.

        Args:
            max_memories_per_agent: Maximum memories per agent
        """
        self._memories: Dict[str, EnhancedMemoryRecord] = {}
        self._agent_indices: Dict[str, Set[str]] = defaultdict(set)
        self._type_indices: Dict[MemoryType, Set[str]] = defaultdict(set)
        self._tag_indices: Dict[str, Set[str]] = defaultdict(set)
        self._shared_memories: Set[str] = set()

        self.max_memories_per_agent = max_memories_per_agent
        self.attention_mechanism = AttentionMechanism()
        self.clusterer = SemanticMemoryClusterer()

        logger.info(
            f"EnhancedInMemoryStore initialized - max {max_memories_per_agent} memories per agent"
        )

    def store_memory(self, memory: EnhancedMemoryRecord) -> None:
        """Store memory with automatic indexing."""
        namespaced_key = memory.namespaced_key

        # Update access timestamp if storing existing memory
        if namespaced_key in self._memories:
            memory.metadata.last_accessed = datetime.now().isoformat()
            memory.metadata.access_count += 1

        # Store memory
        self._memories[namespaced_key] = memory

        # Update indices
        self._agent_indices[memory.metadata.agent_id].add(namespaced_key)
        self._type_indices[memory.metadata.memory_type].add(namespaced_key)

        for tag in memory.metadata.tags:
            self._tag_indices[tag].add(namespaced_key)

        if memory.metadata.is_shared:
            self._shared_memories.add(namespaced_key)

        # Update importance score
        self.attention_mechanism.update_memory_importance(memory)

        logger.debug(
            f"Stored memory: {namespaced_key} (type: {memory.metadata.memory_type.value})"
        )

        # Check if pruning is needed
        self._check_and_prune_agent_memories(memory.metadata.agent_id)

    def retrieve_memory(
        self, agent_id: str, key: str
    ) -> Optional[EnhancedMemoryRecord]:
        """Retrieve specific memory and update access tracking."""
        namespaced_key = f"{agent_id}:{key}"
        memory = self._memories.get(namespaced_key)

        if memory:
            # Update access tracking
            memory.metadata.access_count += 1
            memory.metadata.last_accessed = datetime.now().isoformat()

            # Update importance score
            self.attention_mechanism.update_memory_importance(memory)

        return memory

    def search_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        include_shared: bool = True,
        min_importance: float = 0.0,
        limit: int = 100,
    ) -> List[EnhancedMemoryRecord]:
        """Advanced memory search with multiple filters."""
        candidate_keys = set()

        # Start with agent memories
        candidate_keys.update(self._agent_indices.get(agent_id, set()))

        # Add shared memories if requested
        if include_shared:
            shared_keys = {
                key
                for key in self._shared_memories
                if not key.startswith(f"{agent_id}:")
            }
            candidate_keys.update(shared_keys)

        # Filter by memory type
        if memory_type:
            type_keys = self._type_indices.get(memory_type, set())
            candidate_keys = candidate_keys.intersection(type_keys)

        # Filter by tags
        if tags:
            tag_keys = set()
            for tag in tags:
                tag_keys.update(self._tag_indices.get(tag, set()))
            candidate_keys = candidate_keys.intersection(tag_keys)

        # Get memories and filter by importance
        memories = []
        for key in candidate_keys:
            memory = self._memories.get(key)
            if memory and memory.metadata.importance_score >= min_importance:
                memories.append(memory)

        # Sort by importance score (descending)
        memories.sort(key=lambda m: m.metadata.importance_score, reverse=True)

        return memories[:limit]

    def get_agent_memories(
        self, agent_id: str, memory_type: Optional[MemoryType] = None
    ) -> List[EnhancedMemoryRecord]:
        """Get all memories for an agent."""
        agent_keys = self._agent_indices.get(agent_id, set())

        memories = []
        for key in agent_keys:
            memory = self._memories.get(key)
            if memory and (
                not memory_type or memory.metadata.memory_type == memory_type
            ):
                memories.append(memory)

        # Sort by importance
        memories.sort(key=lambda m: m.metadata.importance_score, reverse=True)
        return memories

    def remove_memory(self, agent_id: str, key: str) -> bool:
        """Remove memory and clean up indices."""
        namespaced_key = f"{agent_id}:{key}"
        memory = self._memories.get(namespaced_key)

        if not memory:
            return False

        # Remove from all indices
        del self._memories[namespaced_key]
        self._agent_indices[agent_id].discard(namespaced_key)
        self._type_indices[memory.metadata.memory_type].discard(namespaced_key)

        for tag in memory.metadata.tags:
            self._tag_indices[tag].discard(namespaced_key)

        self._shared_memories.discard(namespaced_key)

        logger.debug(f"Removed memory: {namespaced_key}")
        return True

    def get_memory_stats(self, agent_id: Optional[str] = None) -> Dict[str, JSONValue]:
        """Get comprehensive memory statistics."""
        if agent_id:
            # Agent-specific stats
            agent_memories = self.get_agent_memories(agent_id)

            type_counts = Counter(m.metadata.memory_type for m in agent_memories)
            modality_counts = Counter(m.metadata.modality for m in agent_memories)
            priority_counts = Counter(m.metadata.priority for m in agent_memories)

            avg_importance = (
                sum(m.metadata.importance_score for m in agent_memories)
                / len(agent_memories)
                if agent_memories
                else 0
            )
            avg_access_count = (
                sum(m.metadata.access_count for m in agent_memories)
                / len(agent_memories)
                if agent_memories
                else 0
            )

            return {
                "agent_id": agent_id,
                "total_memories": len(agent_memories),
                "memory_types": {t.value: count for t, count in type_counts.items()},
                "modalities": {m.value: count for m, count in modality_counts.items()},
                "priorities": {p.name: count for p, count in priority_counts.items()},
                "avg_importance_score": round(avg_importance, 3),
                "avg_access_count": round(avg_access_count, 2),
                "memory_utilization": round(
                    len(agent_memories) / self.max_memories_per_agent, 2
                ),
            }
        else:
            # Global stats
            all_agents = list(self._agent_indices.keys())
            return {
                "total_agents": len(all_agents),
                "total_memories": len(self._memories),
                "shared_memories": len(self._shared_memories),
                "agent_summaries": {
                    agent: self.get_memory_stats(agent) for agent in all_agents
                },
            }

    def _check_and_prune_agent_memories(self, agent_id: str) -> None:
        """Check if agent needs memory pruning."""
        agent_memory_count = len(self._agent_indices[agent_id])
        threshold = int(self.max_memories_per_agent * 0.8)

        if agent_memory_count >= threshold:
            logger.info(
                f"Agent {agent_id} memory threshold reached ({agent_memory_count}/{self.max_memories_per_agent})"
            )
            self._prune_agent_memories(agent_id)

    def _prune_agent_memories(self, agent_id: str, target_ratio: float = 0.7) -> int:
        """Prune low-importance memories for an agent."""
        target_count = int(self.max_memories_per_agent * target_ratio)
        agent_memories = self.get_agent_memories(agent_id)

        if len(agent_memories) <= target_count:
            return 0

        # Sort by importance (ascending) to prune least important first
        agent_memories.sort(
            key=lambda m: (
                m.metadata.priority.value,
                m.metadata.importance_score,
                m.metadata.timestamp,
            )
        )

        memories_to_prune = agent_memories[: len(agent_memories) - target_count]
        pruned_count = 0

        for memory in memories_to_prune:
            # Don't prune critical memories or very recent ones
            if memory.metadata.priority >= MemoryPriority.HIGH:
                continue

            last_accessed = datetime.fromisoformat(memory.metadata.last_accessed)
            if datetime.now() - last_accessed < timedelta(hours=24):
                continue

            # Remove memory
            if self.remove_memory(agent_id, memory.metadata.key):
                pruned_count += 1

        logger.info(f"Pruned {pruned_count} memories for agent {agent_id}")
        return pruned_count

    def consolidate_agent_memories(self, agent_id: str) -> Dict[str, JSONValue]:
        """Consolidate agent memories using semantic clustering."""
        agent_memories = self.get_agent_memories(agent_id)

        if len(agent_memories) < 50:  # Not enough memories to consolidate
            return {
                "action": "no_consolidation_needed",
                "memory_count": len(agent_memories),
            }

        # Cluster memories by similarity
        clusters = self.clusterer.cluster_memories(agent_memories)

        consolidation_results = []
        for i, cluster in enumerate(clusters):
            if len(cluster) > 3:  # Only consolidate clusters with multiple memories
                summary = self._create_cluster_summary(cluster, agent_id, i)
                if summary:
                    consolidation_results.append(summary)

                    # Remove original memories (except highest importance)
                    cluster.sort(
                        key=lambda m: m.metadata.importance_score, reverse=True
                    )
                    for memory in cluster[1:]:  # Keep the most important one
                        self.remove_memory(agent_id, memory.metadata.key)

        return {
            "action": "consolidated",
            "clusters_processed": len(clusters),
            "clusters_consolidated": len(consolidation_results),
            "consolidation_summaries": consolidation_results,
        }

    def _create_cluster_summary(
        self, cluster: List[EnhancedMemoryRecord], agent_id: str, cluster_id: int
    ) -> Optional[EnhancedMemoryRecord]:
        """Create a summary memory from a cluster of related memories."""
        if not cluster:
            return None

        # Create summary content
        summary_data = {
            "type": "memory_consolidation",
            "cluster_id": cluster_id,
            "original_memory_count": len(cluster),
            "date_range": {
                "earliest": min(m.metadata.timestamp for m in cluster),
                "latest": max(m.metadata.timestamp for m in cluster),
            },
            "consolidated_tags": list(
                set(tag for m in cluster for tag in m.metadata.tags)
            ),
            "sample_memories": [
                {
                    "key": m.metadata.key,
                    "content_preview": m.content.text_representation[:100] + "..."
                    if len(m.content.text_representation) > 100
                    else m.content.text_representation,
                    "importance": m.metadata.importance_score,
                }
                for m in sorted(
                    cluster, key=lambda x: x.metadata.importance_score, reverse=True
                )[:3]
            ],
        }

        # Create summary metadata
        summary_key = (
            f"consolidation_{cluster_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        all_tags = list(set(tag for m in cluster for tag in m.metadata.tags))
        all_tags.append("memory_consolidation")

        metadata = MemoryMetadata(
            key=summary_key,
            agent_id=agent_id,
            memory_type=MemoryType.SEMANTIC,  # Consolidations are semantic
            modality=MemoryModality.STRUCTURED,
            priority=MemoryPriority.HIGH,  # Summaries are important
            tags=all_tags,
            timestamp=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            access_count=0,
            importance_score=0.8,  # High importance for summaries
            is_shared=False,
            consolidation_level=1,
        )

        # Create summary content
        content = MemoryContent(
            raw_content=summary_data,
            content_type="consolidation_summary",
            text_representation=json.dumps(summary_data, indent=2),
        )

        summary_memory = EnhancedMemoryRecord(metadata=metadata, content=content)
        self.store_memory(summary_memory)

        return summary_memory


class EnhancedSwarmMemory:
    """
    Enhanced memory system optimized for agent swarms.

    Implements latest industry best practices for multi-agent memory management.
    """

    def __init__(
        self,
        store: Optional[EnhancedMemoryStore] = None,
        agent_id: str = "default",
        max_memories: int = 10000,
    ):
        """
        Initialize enhanced swarm memory.

        Args:
            store: Optional memory store backend
            agent_id: Default agent identifier
            max_memories: Maximum memories per agent
        """
        self._store = store or EnhancedInMemoryStore(max_memories)
        self.agent_id = agent_id

        logger.info(f"EnhancedSwarmMemory initialized for agent: {agent_id}")

    def store(
        self,
        key: str,
        content: Any,
        tags: List[str],
        memory_type: MemoryType = MemoryType.EPISODIC,
        modality: MemoryModality = MemoryModality.TEXT,
        priority: MemoryPriority = MemoryPriority.NORMAL,
        is_shared: bool = False,
        agent_id: Optional[str] = None,
    ) -> str:
        """
        Store memory with enhanced metadata.

        Args:
            key: Memory key
            content: Memory content
            tags: Associated tags
            memory_type: Type of memory (episodic, semantic, etc.)
            modality: Content modality (text, image, etc.)
            priority: Memory importance
            is_shared: Whether to share with other agents
            agent_id: Override default agent ID

        Returns:
            Namespaced memory key
        """
        effective_agent_id = agent_id or self.agent_id

        # Create metadata
        metadata = MemoryMetadata(
            key=key,
            agent_id=effective_agent_id,
            memory_type=memory_type,
            modality=modality,
            priority=priority,
            tags=tags,
            timestamp=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            access_count=0,
            importance_score=0.5,  # Will be calculated by attention mechanism
            is_shared=is_shared,
        )

        # Create content representation
        if isinstance(content, str):
            text_repr = content
        elif isinstance(content, dict):
            text_repr = json.dumps(content, default=str)
        else:
            text_repr = str(content)

        memory_content = MemoryContent(
            raw_content=content,
            content_type=type(content).__name__,
            text_representation=text_repr,
        )

        # Create and store memory record
        memory = EnhancedMemoryRecord(metadata=metadata, content=memory_content)
        self._store.store_memory(memory)

        logger.debug(
            f"Stored memory: {key} (type: {memory_type.value}, agent: {effective_agent_id})"
        )
        return memory.namespaced_key

    def retrieve(self, key: str, agent_id: Optional[str] = None) -> Optional[Any]:
        """Retrieve memory content by key."""
        effective_agent_id = agent_id or self.agent_id
        memory = self._store.retrieve_memory(effective_agent_id, key)
        return memory.content.raw_content if memory else None

    def search(
        self,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        include_shared: bool = True,
        min_importance: float = 0.0,
        limit: int = 50,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, JSONValue]]:
        """
        Search memories with advanced filtering.

        Args:
            tags: Optional tags to filter by
            memory_type: Optional memory type filter
            include_shared: Include shared memories from other agents
            min_importance: Minimum importance score
            limit: Maximum number of results
            agent_id: Override default agent ID

        Returns:
            List of memory records with content and metadata
        """
        effective_agent_id = agent_id or self.agent_id

        memories = self._store.search_memories(
            agent_id=effective_agent_id,
            memory_type=memory_type,
            tags=tags,
            include_shared=include_shared,
            min_importance=min_importance,
            limit=limit,
        )

        # Convert to dictionaries for return
        results = []
        for memory in memories:
            result = memory.to_dict()
            result["content"] = memory.content.raw_content  # Return original content
            results.append(result)

        return results

    def get_stats(self, agent_id: Optional[str] = None) -> Dict[str, JSONValue]:
        """Get memory statistics."""
        effective_agent_id = agent_id or self.agent_id
        return self._store.get_memory_stats(effective_agent_id)

    def consolidate_memories(self, agent_id: Optional[str] = None) -> Dict[str, JSONValue]:
        """Consolidate agent memories using semantic clustering."""
        effective_agent_id = agent_id or self.agent_id
        if hasattr(self._store, "consolidate_agent_memories"):
            return self._store.consolidate_agent_memories(effective_agent_id)
        else:
            return {
                "action": "not_supported",
                "message": "Store does not support consolidation",
            }

    def get_swarm_overview(self) -> Dict[str, JSONValue]:
        """Get overview of entire swarm memory state."""
        return self._store.get_memory_stats()

    def create_semantic_memory(
        self, key: str, fact: str, tags: List[str], agent_id: Optional[str] = None
    ) -> str:
        """Create a semantic memory for facts and knowledge."""
        return self.store(
            key=key,
            content=fact,
            tags=tags,
            memory_type=MemoryType.SEMANTIC,
            modality=MemoryModality.TEXT,
            priority=MemoryPriority.NORMAL,
            agent_id=agent_id,
        )

    def create_episodic_memory(
        self,
        key: str,
        event: Dict[str, JSONValue],
        tags: List[str],
        agent_id: Optional[str] = None,
    ) -> str:
        """Create an episodic memory for events and experiences."""
        return self.store(
            key=key,
            content=event,
            tags=tags,
            memory_type=MemoryType.EPISODIC,
            modality=MemoryModality.STRUCTURED,
            priority=MemoryPriority.NORMAL,
            agent_id=agent_id,
        )

    def create_procedural_memory(
        self, key: str, procedure: str, tags: List[str], agent_id: Optional[str] = None
    ) -> str:
        """Create a procedural memory for skills and procedures."""
        return self.store(
            key=key,
            content=procedure,
            tags=tags,
            memory_type=MemoryType.PROCEDURAL,
            modality=MemoryModality.CODE,
            priority=MemoryPriority.HIGH,  # Procedures are typically important
            agent_id=agent_id,
        )
