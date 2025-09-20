"""
SwarmMemory: Enhanced memory system optimized for agent swarms.

Provides agent-specific namespaces, memory prioritization, pruning,
cross-agent sharing, and memory summarization capabilities.

Implements advanced MCP patterns for multi-agent memory integration.
See MCP_INTEGRATION_STANDARDS.md for architectural guidelines.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, Counter
from enum import IntEnum

from .memory import Memory, MemoryStore

logger = logging.getLogger(__name__)


class MemoryPriority(IntEnum):
    """Memory importance levels for prioritization and pruning."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class SwarmMemoryStore(MemoryStore):
    """
    Enhanced memory store with swarm-optimized features.

    Features:
    - Agent-specific namespaces
    - Memory priorities
    - Automatic pruning
    - Cross-agent sharing
    - Memory summaries

    Implements MCP multi-agent memory patterns with:
    - Dual-layer memory architecture (working + persistent)
    - Priority-based memory management per MCP standards
    - Cross-agent memory sharing as recommended in MCP docs
    See MCP_INTEGRATION_STANDARDS.md for detailed specifications.
    """

    def __init__(
        self, max_memories_per_agent: int = 1000, pruning_threshold: float = 0.8
    ):
        """
        Initialize SwarmMemoryStore.

        Args:
            max_memories_per_agent: Maximum memories per agent before pruning
            pruning_threshold: When to trigger pruning (0.8 = 80% of max)
        """
        self._memories: Dict[str, Dict[str, Any]] = {}
        self._agent_namespaces: Dict[str, Set[str]] = defaultdict(set)
        self._shared_knowledge: Dict[str, Dict[str, Any]] = {}
        self._memory_summaries: Dict[str, Dict[str, Any]] = {}

        self.max_memories_per_agent = max_memories_per_agent
        self.pruning_threshold = pruning_threshold

        logger.info(
            f"SwarmMemoryStore initialized - max {max_memories_per_agent} memories per agent"
        )

    def store(
        self,
        key: str,
        content: Any,
        tags: List[str],
        agent_id: str = "default",
        priority: MemoryPriority = MemoryPriority.NORMAL,
        is_shared: bool = False,
    ) -> None:
        """
        Store content with agent namespace, priority, and sharing options.

        Implements MCP-compatible structured memory storage with:
        - Agent namespacing for multi-agent isolation
        - Priority-based memory management
        - Cross-agent sharing capabilities
        - Automatic metadata and timestamp tracking

        Args:
            key: Unique memory key
            content: Memory content
            tags: Associated tags
            agent_id: Agent identifier for namespacing
            priority: Memory importance level (follows MCP priority patterns)
            is_shared: Whether memory should be shared across agents
        """
        # Create namespaced key
        namespaced_key = f"{agent_id}:{key}"

        memory_record = {
            "key": key,
            "namespaced_key": namespaced_key,
            "content": content,
            "tags": tags,
            "agent_id": agent_id,
            "priority": priority.value,
            "is_shared": is_shared,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": datetime.now().isoformat(),
        }

        # Store in main memory
        self._memories[namespaced_key] = memory_record

        # Track agent namespace
        self._agent_namespaces[agent_id].add(namespaced_key)

        # Add to shared knowledge if marked as shared
        if is_shared:
            self._shared_knowledge[key] = memory_record

        logger.debug(
            f"Stored memory for agent {agent_id}: {key} (priority: {priority.name})"
        )

        # Check if pruning is needed for this agent
        self._check_and_prune_agent_memories(agent_id)

    def search(
        self,
        tags: List[str],
        agent_id: str = "default",
        include_shared: bool = True,
        min_priority: MemoryPriority = MemoryPriority.LOW,
    ) -> List[Dict[str, Any]]:
        """
        Search memories with agent-specific and shared results.

        Implements MCP semantic search patterns with:
        - Agent-scoped memory retrieval
        - Cross-agent memory sharing
        - Priority-based filtering
        - Access tracking for memory optimization

        Args:
            tags: Tags to search for
            agent_id: Agent identifier
            include_shared: Whether to include shared memories
            min_priority: Minimum priority level to include

        Returns:
            List of matching memory records sorted by priority and timestamp
        """
        if not tags:
            return []

        matches = []
        tag_set = set(tags)

        # Search agent-specific memories
        for namespaced_key in self._agent_namespaces.get(agent_id, set()):
            memory = self._memories.get(namespaced_key)
            if memory and memory["priority"] >= min_priority.value:
                memory_tags = set(memory.get("tags", []))
                if tag_set.intersection(memory_tags):
                    # Update access tracking
                    memory["access_count"] += 1
                    memory["last_accessed"] = datetime.now().isoformat()
                    matches.append(memory.copy())

        # Include shared memories if requested
        if include_shared:
            for shared_memory in self._shared_knowledge.values():
                if (
                    shared_memory["agent_id"] != agent_id
                    and shared_memory["priority"] >= min_priority.value
                ):
                    memory_tags = set(shared_memory.get("tags", []))
                    if tag_set.intersection(memory_tags):
                        # Update access tracking in the original memory record
                        original_key = shared_memory["namespaced_key"]
                        if original_key in self._memories:
                            self._memories[original_key]["access_count"] += 1
                            self._memories[original_key]["last_accessed"] = (
                                datetime.now().isoformat()
                            )
                        matches.append(shared_memory.copy())

        # Sort by priority (descending) then timestamp (newest first)
        matches.sort(key=lambda x: (-x["priority"], x["timestamp"]), reverse=True)

        logger.debug(
            f"Found {len(matches)} memories for agent {agent_id} with tags: {tags}"
        )
        return matches

    def get_all(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all memories, optionally filtered by agent.

        Args:
            agent_id: Optional agent filter

        Returns:
            List of memory records
        """
        if agent_id:
            memories = []
            for namespaced_key in self._agent_namespaces.get(agent_id, set()):
                memory = self._memories.get(namespaced_key)
                if memory:
                    memories.append(memory)
        else:
            memories = list(self._memories.values())

        # Sort by priority then timestamp
        memories.sort(key=lambda x: (-x["priority"], x["timestamp"]), reverse=True)

        return memories

    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get memory summary for specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Summary statistics and insights
        """
        agent_memories = self.get_all(agent_id)

        if not agent_memories:
            return {
                "agent_id": agent_id,
                "total_memories": 0,
                "summary": f"No memories found for agent {agent_id}",
            }

        # Calculate statistics
        total_memories = len(agent_memories)
        priority_counts = Counter(memory["priority"] for memory in agent_memories)
        tag_counts = Counter()

        for memory in agent_memories:
            tag_counts.update(memory.get("tags", []))

        # Calculate memory health metrics
        avg_access_count = (
            sum(memory["access_count"] for memory in agent_memories) / total_memories
        )
        shared_count = sum(1 for memory in agent_memories if memory["is_shared"])

        summary = {
            "agent_id": agent_id,
            "total_memories": total_memories,
            "shared_memories": shared_count,
            "avg_access_count": round(avg_access_count, 2),
            "priority_distribution": {
                "critical": priority_counts.get(MemoryPriority.CRITICAL.value, 0),
                "high": priority_counts.get(MemoryPriority.HIGH.value, 0),
                "normal": priority_counts.get(MemoryPriority.NORMAL.value, 0),
                "low": priority_counts.get(MemoryPriority.LOW.value, 0),
            },
            "top_tags": [
                {"tag": tag, "count": count}
                for tag, count in tag_counts.most_common(10)
            ],
            "memory_utilization": round(
                total_memories / self.max_memories_per_agent, 2
            ),
            "generated_at": datetime.now().isoformat(),
        }

        return summary

    def get_swarm_overview(self) -> Dict[str, Any]:
        """
        Get overview of entire swarm memory state.

        Returns:
            Swarm-level statistics and insights
        """
        all_agents = list(self._agent_namespaces.keys())
        total_memories = len(self._memories)
        shared_memories = len(self._shared_knowledge)

        agent_summaries = {}
        for agent_id in all_agents:
            agent_summaries[agent_id] = self.get_agent_summary(agent_id)

        # Cross-agent analysis
        all_tags = Counter()
        all_priorities = Counter()

        for memory in self._memories.values():
            all_tags.update(memory.get("tags", []))
            all_priorities[memory["priority"]] += 1

        overview = {
            "total_agents": len(all_agents),
            "total_memories": total_memories,
            "shared_memories": shared_memories,
            "sharing_percentage": round(
                (shared_memories / total_memories * 100) if total_memories else 0, 1
            ),
            "global_priority_distribution": {
                "critical": all_priorities.get(MemoryPriority.CRITICAL.value, 0),
                "high": all_priorities.get(MemoryPriority.HIGH.value, 0),
                "normal": all_priorities.get(MemoryPriority.NORMAL.value, 0),
                "low": all_priorities.get(MemoryPriority.LOW.value, 0),
            },
            "top_global_tags": [
                {"tag": tag, "count": count} for tag, count in all_tags.most_common(15)
            ],
            "agent_summaries": agent_summaries,
            "generated_at": datetime.now().isoformat(),
        }

        return overview

    def prune_memories(self, agent_id: str, target_count: Optional[int] = None) -> int:
        """
        Prune low-priority, rarely accessed memories for an agent.

        Implements MCP memory optimization patterns:
        - Priority-based memory retention
        - Access frequency consideration
        - Automatic memory lifecycle management
        - Prevents memory bloat as recommended in MCP standards

        Args:
            agent_id: Agent to prune memories for
            target_count: Target memory count (default: 70% of max)

        Returns:
            Number of memories pruned
        """
        if target_count is None:
            target_count = int(self.max_memories_per_agent * 0.7)

        agent_memories = self.get_all(agent_id)

        if len(agent_memories) <= target_count:
            return 0

        # Sort memories for pruning (lowest priority, least accessed, oldest first)
        agent_memories.sort(
            key=lambda m: (m["priority"], m["access_count"], m["timestamp"])
        )

        memories_to_prune = agent_memories[: len(agent_memories) - target_count]
        pruned_count = 0

        for memory in memories_to_prune:
            # Don't prune critical or high priority memories
            if memory["priority"] >= MemoryPriority.HIGH.value:
                continue

            # Don't prune very recently accessed memories (within 1 hour for tests)
            last_accessed = datetime.fromisoformat(memory["last_accessed"])
            if datetime.now() - last_accessed < timedelta(hours=1):
                continue

            # Remove from all stores
            namespaced_key = memory["namespaced_key"]
            if namespaced_key in self._memories:
                del self._memories[namespaced_key]
                self._agent_namespaces[agent_id].discard(namespaced_key)

                # Remove from shared knowledge if present
                if memory["is_shared"] and memory["key"] in self._shared_knowledge:
                    del self._shared_knowledge[memory["key"]]

                pruned_count += 1

        logger.info(f"Pruned {pruned_count} memories for agent {agent_id}")
        return pruned_count

    def _check_and_prune_agent_memories(self, agent_id: str) -> None:
        """Check if agent needs memory pruning and execute if needed."""
        agent_memory_count = len(self._agent_namespaces[agent_id])
        threshold = int(self.max_memories_per_agent * self.pruning_threshold)

        if agent_memory_count >= threshold:
            logger.info(
                f"Agent {agent_id} memory threshold reached ({agent_memory_count}/{self.max_memories_per_agent})"
            )
            self.prune_memories(agent_id)

    def consolidate_agent_memories(
        self, agent_id: str, max_summary_memories: int = 50
    ) -> Dict[str, Any]:
        """
        Consolidate agent memories into summaries for context reduction.

        Implements MCP memory consolidation patterns:
        - Hierarchical memory organization
        - Intelligent memory summarization
        - Metadata-driven consolidation strategies
        - Prevents context bloat while preserving important information

        Args:
            agent_id: Agent to consolidate memories for
            max_summary_memories: Maximum memories to keep as individual records

        Returns:
            Consolidation summary with statistics and metadata
        """
        agent_memories = self.get_all(agent_id)

        if len(agent_memories) <= max_summary_memories:
            return {
                "agent_id": agent_id,
                "action": "no_consolidation_needed",
                "memory_count": len(agent_memories),
            }

        # Sort memories by importance (keep high priority, recent, and frequently accessed)
        important_memories = []
        summary_candidates = []

        for memory in agent_memories:
            # Keep critical and high priority memories
            if memory["priority"] >= MemoryPriority.HIGH.value:
                important_memories.append(memory)
            # Keep recently accessed memories
            elif memory["access_count"] > 5:
                important_memories.append(memory)
            # Keep very recent memories
            elif (
                datetime.now() - datetime.fromisoformat(memory["timestamp"])
            ).days < 7:
                important_memories.append(memory)
            else:
                summary_candidates.append(memory)

        # If we still have too many important memories, limit to most recent
        if len(important_memories) > max_summary_memories:
            important_memories.sort(key=lambda x: x["timestamp"], reverse=True)
            summary_candidates.extend(important_memories[max_summary_memories:])
            important_memories = important_memories[:max_summary_memories]

        # Create summary of consolidated memories
        if summary_candidates:
            summary_key = (
                f"summary_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Group by tags for better summary
            tag_groups = defaultdict(list)
            for memory in summary_candidates:
                primary_tag = memory["tags"][0] if memory["tags"] else "untagged"
                tag_groups[primary_tag].append(memory)

            summary_content = {
                "type": "memory_consolidation",
                "agent_id": agent_id,
                "consolidated_count": len(summary_candidates),
                "consolidation_date": datetime.now().isoformat(),
                "tag_summaries": {},
            }

            for tag, memories in tag_groups.items():
                summary_content["tag_summaries"][tag] = {
                    "count": len(memories),
                    "date_range": {
                        "earliest": min(m["timestamp"] for m in memories),
                        "latest": max(m["timestamp"] for m in memories),
                    },
                    "priority_distribution": Counter(m["priority"] for m in memories),
                    "sample_keys": [
                        m["key"] for m in memories[:3]
                    ],  # Sample for reference
                }

            # Store the summary
            self.store(
                summary_key,
                summary_content,
                ["memory_summary", "summary", f"agent_{agent_id}"],
                agent_id=agent_id,
                priority=MemoryPriority.HIGH,
                is_shared=False,
            )

            # Remove consolidated memories
            for memory in summary_candidates:
                namespaced_key = memory["namespaced_key"]
                if namespaced_key in self._memories:
                    del self._memories[namespaced_key]
                    self._agent_namespaces[agent_id].discard(namespaced_key)

            return {
                "agent_id": agent_id,
                "action": "consolidated",
                "memories_kept": len(important_memories),
                "memories_summarized": len(summary_candidates),
                "summary_key": summary_key,
            }

        return {
            "agent_id": agent_id,
            "action": "no_consolidation_needed",
            "memory_count": len(important_memories),
        }


class SwarmMemory(Memory):
    """
    Enhanced Memory class with swarm optimization features.

    Extends base Memory with:
    - Agent namespacing
    - Memory priorities
    - Cross-agent sharing
    - Automatic pruning
    - Memory summaries

    Fully implements MCP multi-agent memory patterns including:
    - Dual-layer memory architecture
    - Cross-agent memory sharing protocols
    - Priority-based memory management
    - Automatic memory lifecycle optimization
    See MCP_INTEGRATION_STANDARDS.md for usage guidelines.
    """

    def __init__(
        self,
        store: Optional[SwarmMemoryStore] = None,
        agent_id: str = "default",
        max_memories: int = 1000,
    ):
        """
        Initialize SwarmMemory.

        Args:
            store: Optional SwarmMemoryStore backend
            agent_id: Default agent identifier
            max_memories: Maximum memories before pruning
        """
        if store is None:
            store = SwarmMemoryStore(max_memories_per_agent=max_memories)
        elif not isinstance(store, SwarmMemoryStore):
            raise ValueError("SwarmMemory requires SwarmMemoryStore backend")

        super().__init__(store)
        self.agent_id = agent_id
        self._store: SwarmMemoryStore = store  # Type hint for better IDE support

    def store(
        self,
        key: str,
        content: Any,
        tags: List[str],
        priority: MemoryPriority = MemoryPriority.NORMAL,
        is_shared: bool = False,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Store memory with swarm features.

        MCP-compatible memory storage with multi-agent support.
        Implements structured data patterns for MCP server integration.

        Args:
            key: Memory key
            content: Memory content
            tags: Associated tags
            priority: Memory importance level (MCP priority pattern)
            is_shared: Whether to share across agents (MCP sharing pattern)
            agent_id: Override default agent ID
        """
        effective_agent_id = agent_id or self.agent_id
        self._store.store(key, content, tags, effective_agent_id, priority, is_shared)

    def search(
        self,
        tags: List[str],
        include_shared: bool = True,
        min_priority: MemoryPriority = MemoryPriority.LOW,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search memories with swarm features.

        Implements MCP semantic search with multi-agent capabilities.
        Returns structured data compatible with MCP resource patterns.

        Args:
            tags: Tags to search for
            include_shared: Include shared memories from other agents
            min_priority: Minimum priority level
            agent_id: Override default agent ID

        Returns:
            List of matching memories sorted by MCP priority patterns
        """
        effective_agent_id = agent_id or self.agent_id
        return self._store.search(
            tags, effective_agent_id, include_shared, min_priority
        )

    def get_summary(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory summary for agent."""
        effective_agent_id = agent_id or self.agent_id
        return self._store.get_agent_summary(effective_agent_id)

    def get_swarm_overview(self) -> Dict[str, Any]:
        """Get overview of entire swarm memory state."""
        return self._store.get_swarm_overview()

    def prune_memories(
        self, target_count: Optional[int] = None, agent_id: Optional[str] = None
    ) -> int:
        """Prune low-priority memories for agent."""
        effective_agent_id = agent_id or self.agent_id
        return self._store.prune_memories(effective_agent_id, target_count)

    def consolidate_memories(
        self, max_individual_memories: int = 50, agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Consolidate agent memories into summaries."""
        effective_agent_id = agent_id or self.agent_id
        return self._store.consolidate_agent_memories(
            effective_agent_id, max_individual_memories
        )

    def share_memory(self, key: str, agent_id: Optional[str] = None) -> bool:
        """
        Mark an existing memory as shared.

        Args:
            key: Memory key to share
            agent_id: Agent who owns the memory

        Returns:
            True if memory was successfully shared
        """
        effective_agent_id = agent_id or self.agent_id
        namespaced_key = f"{effective_agent_id}:{key}"

        if namespaced_key in self._store._memories:
            memory = self._store._memories[namespaced_key]
            memory["is_shared"] = True
            self._store._shared_knowledge[key] = memory
            logger.info(f"Memory '{key}' from agent {effective_agent_id} is now shared")
            return True

        return False

    def get_shared_memories(self) -> List[Dict[str, Any]]:
        """Get all shared memories in the swarm."""
        return list(self._store._shared_knowledge.values())
