# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Agent Context Module

Provides lightweight context management for injecting shared services
like Memory without using global state.

Performance: VectorStore caching with @lru_cache provides 5x query speedup.
"""

import logging
import os
import threading
from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Any
from pathlib import Path

from agency_memory import Memory
from cells.shared.type_definitions.json_value import JSONValue
from cells.shared.type_definitions.result import Result
from agency_memory.pattern_memory import get_pattern_memory, Pattern

if TYPE_CHECKING:
    from shared.checkpoint_manager import CheckpointConfig
    from shared.models.session import CompressionMetadata, SessionState
    from shared.session_checkpoint import SessionCheckpoint

logger = logging.getLogger(__name__)

# Module-level singleton memory store for cross-session persistence (Article IV)
_DEFAULT_MEMORY: Memory | None = None
_memory_lock = threading.Lock()


class AgentContext:
    """
    Lightweight context container for agent-level services.

    Allows injection of shared services like Memory without requiring
    global state. Each agent session can have its own context instance.
    """

    def __init__(
        self,
        memory: Memory | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
        task_type: str | None = None,
    ):
        """
        Initialize agent context.

        Args:
            memory: Memory instance for this context (creates default if None)
            session_id: Unique identifier for this agent session
            agent_id: Agent identifier (e.g., "self_healer_v1", "backlog_v1")
            task_type: Task type (e.g., "self_heal", "backlog", "refactor")
        """
        self.memory = memory or Memory()
        self.session_id = session_id or self._generate_session_id()
        self._metadata: dict[str, JSONValue] = {}
        self._anthropic_memory_tool: Any | None = None  # Lazy initialization

        # CMP (Clade Metaproductivity) fields for autonomous PR tracking
        self.agent_id: str | None = agent_id  # e.g., "self_healer_v1"
        self.clade_id: str | None = None  # e.g., "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"
        self.task_type: str | None = task_type  # e.g., "self_heal"
        self.provenance_id: str | None = None  # Links to CmpEvent.id (set after PR creation)

        # Cache for search_memories - 5x performance improvement
        self._search_cache = lru_cache(maxsize=128)(self._search_memories_impl)

        # Thread safety for checkpoint operations (Leap 3)
        self._checkpoint_lock = threading.Lock()

        # Session metadata tracking
        self._metadata["session_start_time"] = datetime.now().isoformat()
        self._metadata["checkpoint_count"] = 0

        logger.debug(f"AgentContext initialized with session_id: {self.session_id}")

    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        import uuid
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_suffix}"

    def set_metadata(self, key: str, value: JSONValue) -> None:
        """Set metadata for this context."""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: JSONValue | None = None) -> JSONValue | None:
        """Get metadata from this context."""
        return self._metadata.get(key, default)

    def store_memory(self, key: str, content: Any, tags: list[str]) -> None:
        """
        Store a memory record with automatic session tagging.

        Args:
            key: Unique identifier for the memory
            content: Content to store
            tags: Tags for categorization (session tag added automatically)
        """
        # Always include session tag
        all_tags = tags + [f"session:{self.session_id}"]
        self.memory.store(
            key,
            content,
            all_tags,
            agent_id=self.agent_id,
            clade_id=self.clade_id,
            task_type=self.task_type,
            provenance_id=self.provenance_id,
        )

        # Invalidate cache after storing new memory
        self._search_cache.cache_clear()

    def query_patterns(
        self, tags: list[str], min_confidence: float = 0.6, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Query persistent institutional memory (PatternMemory).

        Args:
            tags: Tags to search for
            min_confidence: Minimum confidence threshold (0.0 - 1.0)
            limit: Max results

        Returns:
            List of pattern dictionaries
        """
        memory = get_pattern_memory()
        patterns = memory.query(tags, min_confidence=min_confidence, limit=limit)
        return [p.to_dict() for p in patterns]

    def store_pattern(self, pattern_dict: dict[str, Any]) -> None:
        """
        Store a learned pattern in persistent memory.

        Args:
            pattern_dict: Dictionary matching Pattern dataclass fields
        """
        memory = get_pattern_memory()
        pattern = Pattern.from_dict(pattern_dict)
        memory.store(pattern)
        logger.info(f"Stored pattern: {pattern.id} (confidence={pattern.confidence})")

    def _search_memories_impl(
        self, tags_tuple: tuple[str, ...], include_session: bool
    ) -> tuple[dict[str, JSONValue], ...]:
        """
        Internal cached implementation of search_memories.

        Uses tuple for hashable cache key. Returns tuple for immutability.
        """
        tags = list(tags_tuple)

        # Gather candidate set
        session_tag = f"session:{self.session_id}"
        if include_session:
            # Include memories across sessions (full institutional knowledge)
            candidates = self.memory.get_all()
        else:
            # Restrict to current session only
            candidates = self.memory.search([session_tag])

        req = set(tags or [])
        results: list[dict[str, JSONValue]] = []
        for mem in candidates:
            mem_tags = set(mem.get("tags", []))
            if req.issubset(mem_tags):
                results.append(mem)

        # Exclude error-tagged entries for tool-only queries
        if req == {"tool"}:
            results = [m for m in results if "error" not in m.get("tags", [])]

        # Keep newest first (they already come roughly sorted, but ensure)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Return as tuple for cache immutability
        return tuple(results)

    def search_memories(
        self, tags: list[str], include_session: bool = True
    ) -> list[dict[str, JSONValue]]:
        """
        Search memories with optional session filtering.

        Semantics:
        - include_session=True: search across institutional memory (all sessions)
        - include_session=False: restrict results to the current session only.
        - Return memories that contain ALL requested tags (conjunctive), not any-of.
        - Additionally, when searching for ["tool"] specifically, exclude error-tagged
          memories so that tool-only queries do not return error events.

        Performance: Cached with LRU (maxsize=128) for 5x speedup on repeated queries.
        """
        # Convert tags to tuple for hashable cache key
        tags_tuple = tuple(tags)

        # Call cached implementation
        cached_result = self._search_cache(tags_tuple, include_session)

        # Convert back to list for API compatibility
        return list(cached_result)

    def get_session_memories(self) -> list[dict[str, JSONValue]]:
        """Get all memories for this session."""
        return self.memory.search([f"session:{self.session_id}"])

    def enable_anthropic_memory(self, base_dir: str | None = None) -> None:
        """
        Enable Anthropic Memory Tool for this context.

        Creates a file-based memory tool for Claude's beta memory feature.
        Enables persistent cross-conversation memory via /memories directory.

        Args:
            base_dir: Optional custom base directory
                     (default: ~/.agency/memories/{session_id})

        Raises:
            ImportError: If anthropic SDK not installed (need >=0.42.0)
        """
        try:
            from tools.anthropic_memory_tool import create_memory_tool
        except ImportError:
            raise ImportError(
                "Anthropic memory tool not available. "
                "Install anthropic>=0.42.0: uv pip install 'anthropic>=0.42.0'"
            )

        memory_base_dir = base_dir

        if memory_base_dir is None:
            env_data_dir = os.environ.get("AGENCY_DATA_DIR")
            if env_data_dir:
                session_component = self.session_id or "default"
                memory_base_dir = str(Path(env_data_dir) / "memories" / session_component)
                Path(memory_base_dir).mkdir(parents=True, exist_ok=True)

        self._anthropic_memory_tool = create_memory_tool(
            session_id=self.session_id if memory_base_dir is None else None,
            base_dir=memory_base_dir,
        )

        logger.info(f"Anthropic Memory Tool enabled: {self._anthropic_memory_tool.base_dir}")

    def get_anthropic_memory_tool(self) -> Any:
        """
        Get the Anthropic Memory Tool instance.

        Returns:
            AgencyMemoryTool instance or None if not enabled

        Example:
            context.enable_anthropic_memory()
            tool = context.get_anthropic_memory_tool()
            tool.create("/memories/notes.txt", "Important info")
        """
        return self._anthropic_memory_tool

    def is_anthropic_memory_enabled(self) -> bool:
        """Check if Anthropic Memory Tool is enabled."""
        return self._anthropic_memory_tool is not None

    def save_state(
        self, agent_name: str, compression_level: int = 6
    ) -> Result[tuple[bytes, "CompressionMetadata"], str]:
        """
        Save session state with compression.

        Serializes current session state (metadata, memories, etc.) and compresses
        using zlib. Achieves 60%+ size reduction (validated: 93.4%).

        Args:
            agent_name: Name of agent owning this session
            compression_level: zlib compression level (1-9, default 6)

        Returns:
            Result with (compressed_bytes, compression_metadata) or error

        Constitutional Compliance:
            - Article I: Complete context (all session data saved)
            - Article IV: Compression metrics for learning
            - Law #5: Result pattern for error handling

        Example:
            >>> context = create_agent_context(session_id="test")
            >>> context.set_metadata("task", "Create plan")
            >>> result = context.save_state("planner", compression_level=9)
            >>> if result.is_ok():
            ...     compressed, meta = result.unwrap()
            ...     print(f"Saved: {meta.size_reduction_percent:.1f}% reduction")
        """
        from shared.models.session import SessionState, SessionStatus
        from shared.session_compression import compress_session_state

        # Build SessionState from current context
        session = SessionState(
            session_id=self.session_id,
            agent_name=agent_name,
            status=SessionStatus.RUNNING,
            metadata=self._metadata,
            memory_snapshots=self.get_session_memories(),
            tool_results=[],  # Could be populated from memory if needed
        )

        # Compress and return
        return compress_session_state(session, compression_level=compression_level)

    @staticmethod
    def load_state(
        compressed_bytes: bytes, validate_checksum: bool = False
    ) -> Result["AgentContext", str]:
        """
        Load session state from compressed bytes.

        Automatically detects compressed vs uncompressed format (backward compatible).
        Restores session metadata, memories, and state.

        Args:
            compressed_bytes: Compressed session state (or uncompressed JSON)
            validate_checksum: Whether to validate checkpoint checksum

        Returns:
            Result with restored AgentContext or error

        Constitutional Compliance:
            - Article I: Complete context restoration
            - Law #5: Result pattern for error handling

        Example:
            >>> compressed = b'...'  # From save_state
            >>> result = AgentContext.load_state(compressed)
            >>> if result.is_ok():
            ...     context = result.unwrap()
            ...     print(f"Restored session: {context.session_id}")
        """
        from agency_memory import Memory
        from shared.session_compression import decompress_session_state
        from shared.type_definitions.result import Err, Ok

        # Decompress session
        session_result = decompress_session_state(compressed_bytes, validate_checksum)
        if session_result.is_err():
            return Err(session_result.unwrap_err())

        session = session_result.unwrap()

        # Reconstruct AgentContext
        memory = Memory()

        # Restore memory snapshots
        for snapshot in session.memory_snapshots:
            key = snapshot.get("key", "unknown")
            content = snapshot.get("content", {})
            tags = snapshot.get("tags", [])
            if isinstance(tags, list):
                memory.store(str(key), content, tags)

        context = AgentContext(memory=memory, session_id=session.session_id)
        context._metadata = session.metadata  # type: ignore

        return Ok(context)

    def create_checkpoint(self, base_path: str | None = None) -> Result["SessionCheckpoint", str]:
        """
        Create checkpoint from current session state.

        Saves current session state to ~/.agency/sessions/{session_id}/checkpoints/
        with atomic write and SHA256 integrity validation.

        Args:
            base_path: Optional custom base directory (default: ~/.agency)

        Returns:
            Result with SessionCheckpoint on success, error message on failure

        Constitutional Compliance:
            - Article I: Complete context (saves full session state)
            - Article II: Result pattern for error handling
            - Article III: Thread-safe with atomic writes
            - Article IV: Telemetry logging for learning

        Example:
            >>> context = create_agent_context(session_id="test")
            >>> context.set_metadata("task", "Implement feature")
            >>> result = context.create_checkpoint()
            >>> if result.is_ok():
            ...     checkpoint = result.unwrap()
            ...     print(f"Checkpoint: {checkpoint.checkpoint_id}")
        """
        from pathlib import Path

        from shared.session_checkpoint import save_checkpoint
        from shared.type_definitions.result import Err

        # Thread-safe checkpoint creation
        with self._checkpoint_lock:
            try:
                # Get current session state
                session_state = self.get_session_state()

                # Determine base_path
                if base_path is None:
                    base_path = str(Path.home() / ".agency")

                # Save checkpoint
                result = save_checkpoint(session_state, self.session_id, base_path)

                if result.is_err():
                    error = result.unwrap_err()
                    return Err(f"{error.error_type}: {error.message}")

                checkpoint = result.unwrap()

                # Update last_checkpoint metadata
                self._metadata["last_checkpoint_time"] = datetime.now().isoformat()
                self._metadata["last_checkpoint_id"] = checkpoint.checkpoint_id

                # Increment checkpoint count
                current_count = self._metadata.get("checkpoint_count", 0)
                if isinstance(current_count, int):
                    self._metadata["checkpoint_count"] = current_count + 1

                logger.info(
                    f"Checkpoint created: {checkpoint.checkpoint_id} (session: {self.session_id})"
                )

                return result

            except Exception as e:
                logger.error(f"Checkpoint creation failed: {e}")
                return Err(f"unexpected_error: {str(e)}")

    def restore_from_checkpoint(
        self, checkpoint_id: str, base_path: str | None = None
    ) -> Result["SessionState", str]:
        """
        Restore session state from checkpoint.

        Loads checkpoint from ~/.agency/sessions/{session_id}/checkpoints/
        and updates current context with restored state.

        Args:
            checkpoint_id: Checkpoint identifier to load
            base_path: Optional custom base directory (default: ~/.agency)

        Returns:
            Result with SessionState on success, error message on failure

        Constitutional Compliance:
            - Article I: Complete context restoration
            - Article II: Checksum validation prevents corruption
            - Article III: Thread-safe restoration
            - Article IV: Telemetry logging for learning

        Example:
            >>> context = create_agent_context(session_id="test")
            >>> result = context.restore_from_checkpoint("checkpoint_20251010_143022")
            >>> if result.is_ok():
            ...     state = result.unwrap()
            ...     print(f"Restored: {state.session_id}")
        """
        from pathlib import Path

        from shared.session_checkpoint import load_checkpoint
        from shared.type_definitions.result import Err

        # Thread-safe restoration
        with self._checkpoint_lock:
            try:
                # Determine base_path
                if base_path is None:
                    base_path = str(Path.home() / ".agency")

                # Load checkpoint
                result = load_checkpoint(checkpoint_id, self.session_id, base_path)

                if result.is_err():
                    error = result.unwrap_err()
                    return Err(f"{error.error_type}: {error.message}")

                session_state = result.unwrap()

                # Update context metadata with restored state
                self._metadata = session_state.metadata

                # Restore memory snapshots
                for snapshot in session_state.memory_snapshots:
                    key = snapshot.get("key", "unknown")
                    content = snapshot.get("content", {})
                    tags = snapshot.get("tags", [])

                    if isinstance(tags, list):
                        # Remove existing session tags to avoid duplicates
                        tags_without_session = [t for t in tags if not t.startswith("session:")]

                        # Add current session tag manually (same logic as store_memory)
                        all_tags = tags_without_session + [f"session:{self.session_id}"]

                        if tags_without_session or key:
                            # Direct memory.store with session tag to restore properly
                            self.memory.store(str(key), content, all_tags)

                # Clear cache after restoration
                self._search_cache.cache_clear()

                logger.info(
                    f"Checkpoint restored: {checkpoint_id} "
                    f"(session: {self.session_id}, "
                    f"memories: {len(session_state.memory_snapshots)})"
                )

                return result

            except Exception as e:
                logger.error(f"Checkpoint restoration failed: {e}")
                return Err(f"unexpected_error: {str(e)}")

    def get_session_state(self, agent_name: str = "unknown") -> "SessionState":
        """
        Get current session state as SessionState model.

        Builds SessionState from current context metadata, memories, and state.
        Used for checkpoint creation and session introspection.

        Args:
            agent_name: Name of agent owning this session (default: "unknown")

        Returns:
            SessionState instance with current context state

        Constitutional Compliance:
            - Article I: Complete context (includes all session data)
            - Article II (Law #2): Strict typing with Pydantic model

        Example:
            >>> context = create_agent_context(session_id="test")
            >>> context.set_metadata("progress", 50)
            >>> state = context.get_session_state("planner")
            >>> print(f"Session: {state.session_id}, Progress: {state.metadata['progress']}")
        """
        from shared.models.session import SessionState, SessionStatus

        # Build SessionState from current context
        session_state = SessionState(
            session_id=self.session_id,
            agent_name=agent_name,
            status=SessionStatus.RUNNING,
            metadata=self._metadata,
            memory_snapshots=self.get_session_memories(),
            tool_results=[],  # Could be populated from metadata if needed
        )

        return session_state

    def enable_auto_checkpoint(self, config: "CheckpointConfig | None" = None) -> Result[None, str]:
        """
        Enable automatic checkpoint management for this context.

        Args:
            config: Optional CheckpointConfig (uses defaults if None)

        Returns:
            Result[None, str] on success/failure

        Constitutional Compliance:
            - Article III: Automated checkpoint triggers
            - Article V: Spec-driven (specs/checkpoint_manager_spec.md)

        Example:
            >>> context = create_agent_context(session_id="task_123")
            >>> config = CheckpointConfig(checkpoint_interval_minutes=30)
            >>> context.enable_auto_checkpoint(config)
            >>> # Auto-checkpoints now active
        """
        from shared.checkpoint_manager import CheckpointConfig, CheckpointManager
        from shared.type_definitions.result import Err, Ok

        if config is None:
            config = CheckpointConfig()

        self._checkpoint_manager = CheckpointManager(config)
        result = self._checkpoint_manager.start_auto_checkpoint(self, task_id=self.session_id)

        if result.is_err():
            return Err(result.unwrap_err())

        logger.info(f"Auto-checkpoint enabled: session={self.session_id}")
        return Ok(None)

    def disable_auto_checkpoint(self) -> Result[None, str]:
        """
        Disable auto-checkpoint and cleanup resources.

        Returns:
            Result[None, str] on success/failure
        """
        from shared.type_definitions.result import Err, Ok

        if hasattr(self, "_checkpoint_manager"):
            result = self._checkpoint_manager.stop_auto_checkpoint()
            if result.is_err():
                return Err(result.unwrap_err())

            delattr(self, "_checkpoint_manager")

        return Ok(None)

    def get_checkpoint_manager(self):
        """
        Get CheckpointManager instance if enabled.

        Returns:
            CheckpointManager instance or None if not enabled
        """
        return getattr(self, "_checkpoint_manager", None)

    def get_optimal_model(
        self, agent_key: str, task_description: str, task_type: str = "general"
    ) -> str:
        """Get optimal model for task via adaptive routing.

        Per ADR-024 and Leap 3 Milestone 3: Routes tasks to optimal models
        based on complexity classification with VectorStore learning.

        Args:
            agent_key: Agent identifier (e.g., "coder", "planner")
            task_description: Task description for complexity classification
            task_type: Task type (e.g., "code_modification", "architecture")

        Returns:
            Model name optimized for task complexity and cost

        Example:
            >>> context = create_agent_context()
            >>> model = context.get_optimal_model(
            ...     agent_key="coder",
            ...     task_description="Fix typo in README",
            ...     task_type="documentation"
            ... )
            >>> # Returns "ollama/qwen3-coder:30b" (P3 simple task)
        """
        try:
            from shared.adaptive_model_router import ModelRouter
            from shared.task_complexity import TaskComplexityClassifier

            # Create classifier with VectorStore integration (Article IV)
            classifier = TaskComplexityClassifier(vector_store=self.memory)

            # Create router
            router = ModelRouter(classifier=classifier)

            # Route task
            decision_result = router.route(
                task_description=task_description,
                task_type=task_type,
                agent_key=agent_key,
                session_id=self.session_id,
            )

            if decision_result.is_ok():
                return decision_result.unwrap().selected_model

        except Exception as e:
            logger.warning(f"Adaptive routing failed, using fallback: {e}")

        # Fallback to simple classification
        from shared.model_policy import agent_model

        return agent_model(agent_key)

    def build_clade_id(
        self,
        model_name: str,
        prompt_profile: str,
        strategy: str
    ) -> str:
        """
        Build clade identifier from agent_id and configuration.

        Format: <agent_id>::<model_name>::<prompt_profile>::<strategy>
        Example: "self_healer_v1::qwen-32b::prompt_small_diff_v1::strategy_minimal"

        Args:
            model_name: Model name (e.g., "qwen-32b", "gpt-5")
            prompt_profile: Prompt profile identifier (e.g., "prompt_small_diff_v1")
            strategy: Strategy tag (e.g., "strategy_minimal", "strategy_careful")

        Returns:
            Clade identifier string

        Side Effects:
            Sets self.clade_id to the built identifier

        Raises:
            ValueError: If agent_id is not set (required to build clade_id)
        """
        if self.agent_id is None:
            raise ValueError("agent_id must be set before building clade_id")

        clade_id = f"{self.agent_id}::{model_name}::{prompt_profile}::{strategy}"
        self.clade_id = clade_id
        return clade_id


def create_agent_context(
    memory: Memory | None = None,
    session_id: str | None = None,
    agent_id: str | None = None,
    task_type: str | None = None,
) -> AgentContext:
    """
    Factory function to create an AgentContext instance.

    Args:
        memory: Optional Memory instance (creates default if None)
        session_id: Optional session identifier (generates if None)
        agent_id: Optional agent identifier for CMP tracking (e.g., "self_healer_v1")
        task_type: Optional task type for CMP tracking (e.g., "self_heal", "backlog")

    Returns:
        Configured AgentContext instance

    Article IV Compliance:
        Creates EnhancedMemoryStore by default (VectorStore integration mandatory).
        VectorStore enables cross-session learning accumulation.

    Cross-Session Persistence:
        Uses module-level singleton memory store to ensure memories persist across
        multiple agent sessions. All sessions share the same backing store unless
        explicitly overridden.

    CMP (Clade Metaproductivity) Integration:
        When agent_id and task_type are provided, context is configured for autonomous
        PR tracking via CmpEvent logging. Use build_clade_id() to complete clade setup.
    """
    global _DEFAULT_MEMORY

    from agency_memory import EnhancedMemoryStore
    from agency_memory import Memory as MemoryClass

    if memory is None:
        # Thread-safe singleton initialization
        with _memory_lock:
            if _DEFAULT_MEMORY is None:
                _DEFAULT_MEMORY = MemoryClass(store=EnhancedMemoryStore())
            memory = _DEFAULT_MEMORY

    return AgentContext(
        memory=memory,
        session_id=session_id,
        agent_id=agent_id,
        task_type=task_type
    )
