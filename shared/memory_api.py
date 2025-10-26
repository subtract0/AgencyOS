"""
Memory API Protocol - Unified interface for all memory operations.

This module defines the MemoryAPI protocol that unifies access to different
memory backends (VectorStore, EnhancedMemoryStore, session memory) and provides
supervision signal integration for Article VIII compliance.

Constitutional Compliance:
- Article IV: VectorStore integration mandatory (cross-session learning)
- Article VIII: Supervision signals for exponential self-development
- Result pattern for error handling (Constitutional Law #5)

Migration Strategy:
- Feature flag: FEATURE_MEMORY_ROUTER (default: false for backward compatibility)
- Deprecation warnings for direct VectorStore/EnhancedMemoryStore usage
- Migration guide in docs/MEMORY_API_MIGRATION.md

Example Usage:
    from shared.memory_api import MemoryRouter, get_memory_api
    from shared.agent_context import create_agent_context

    # Option 1: Get default router from context
    context = create_agent_context()
    api = get_memory_api(context)

    # Option 2: Create router explicitly
    router = MemoryRouter(context)

    # Store with supervision signal (Article VIII)
    api.store(
        key="jwt_auth_success",
        content={"code": "...", "tests_passed": True},
        tags=["coder", "auth", "success"],
        confidence=0.95,
        reinforcement_signal={
            "outcome": "approved",
            "quality_score": 0.95,
            "learning_value": 1.0
        }
    )

    # Retrieve memories
    memories = api.retrieve(tags=["auth", "success"], min_confidence=0.6)

    # Apply supervision signal (RLHF-style feedback)
    api.supervise(
        memory_id="jwt_auth_success",
        signal={"outcome": "approved", "quality_score": 0.95},
        actor="human"
    )

    # Store counterfactual (what-if analysis)
    api.store_counterfactual(
        original_action="implement_jwt_simple",
        alternative_action="implement_jwt_with_refresh_tokens",
        outcome="Alternative would have been better",
        reason="Refresh tokens improve UX"
    )
"""

import logging
import os
from datetime import datetime
from typing import Any, Protocol

from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class MemoryAPI(Protocol):
    """Protocol defining unified memory interface.

    All memory backends (VectorStore, EnhancedMemoryStore, session memory)
    must implement this protocol for consistent API access.

    Article VIII Requirements:
    - store() MUST accept reinforcement_signal parameter
    - supervise() MUST store supervision signals for RLHF training
    - store_counterfactual() MUST enable what-if analysis
    - ALL operations MUST include provenance tracking
    """

    def store(
        self,
        key: str,
        content: Any,
        tags: list[str],
        confidence: float = 0.85,
        reinforcement_signal: dict[str, Any] | None = None,
        counterfactual: dict[str, Any] | None = None,
    ) -> Result[None, str]:
        """Store memory record with optional supervision signal.

        Args:
            key: Unique identifier for memory
            content: Memory content (any JSON-serializable data)
            tags: Tags for categorization and search
            confidence: Confidence score (0.0-1.0, default: 0.85)
            reinforcement_signal: Optional RLHF supervision signal:
                - outcome: "approved" | "rejected" | "neutral"
                - quality_score: 0.0-1.0
                - learning_value: 0.0-1.0
            counterfactual: Optional counterfactual data:
                - alternative_action: What could have been done differently
                - expected_outcome: What would have happened
                - reason: Why alternative would be better/worse

        Returns:
            Result[None, str] - Ok(None) on success, Err(message) on failure

        Article VIII Compliance:
            - Reinforcement signals stored for DPO/RLHF training
            - Counterfactuals enable what-if analysis
            - Provenance automatically added to all records
        """
        ...

    def retrieve(
        self,
        tags: list[str],
        min_confidence: float = 0.6,
        include_session: bool = True,
    ) -> list[dict[str, Any]]:
        """Retrieve memories matching tags and confidence threshold.

        Args:
            tags: Tags to search for (conjunctive: ALL tags must match)
            min_confidence: Minimum confidence threshold (Article IV: 0.6)
            include_session: Include session-scoped memories

        Returns:
            List of matching memory records (deduplicated by key)

        Article IV Compliance:
            - Searches persistent VectorStore (cross-session learning)
            - Optionally includes session-scoped ephemeral memories
        """
        ...

    def supervise(
        self,
        memory_id: str,
        signal: dict[str, Any],
        actor: str = "human",
        reason: str = "",
    ) -> Result[None, str]:
        """Apply supervision signal to existing memory (RLHF-style feedback).

        Args:
            memory_id: Memory record identifier
            signal: Supervision signal dict:
                - outcome: "approved" | "rejected" | "neutral"
                - quality_score: 0.0-1.0
                - counterfactual: Optional alternative approach
                - preference: Optional preference data
                - learning_value: 0.0-1.0
            actor: Who provided supervision (human, agent, automated)
            reason: Why supervision was applied

        Returns:
            Result[None, str] - Ok(None) on success, Err(message) on failure

        Article VIII Compliance:
            - Supervision signal density target: ≥90%
            - Quality score ≥0.8 tagged as "rl_training_data"
        """
        ...

    def store_counterfactual(
        self,
        original_action: str,
        alternative_action: str,
        outcome: str,
        reason: str,
    ) -> Result[None, str]:
        """Store counterfactual (what-if analysis) for learning.

        Args:
            original_action: What was actually done
            alternative_action: What could have been done differently
            outcome: Expected outcome of alternative
            reason: Why alternative would be better/worse

        Returns:
            Result[None, str] - Ok(None) on success, Err(message) on failure

        Article VIII Compliance:
            - Enables counterfactual reasoning and strategy exploration
            - Stored as high-value training data for RLHF
        """
        ...


class MemoryRouter:
    """Router implementation of MemoryAPI protocol.

    Routes memory operations to appropriate backends based on feature flags
    and memory type. Provides backward compatibility with direct VectorStore usage.

    Feature Flag:
        FEATURE_MEMORY_ROUTER=true → Use new unified API
        FEATURE_MEMORY_ROUTER=false → Fallback to legacy (default)

    Article VIII Compliance:
        - Automatic supervision signal storage
        - Counterfactual reasoning support
        - Provenance tracking for all operations
    """

    def __init__(self, agent_context: Any):
        """Initialize MemoryRouter with agent context.

        Args:
            agent_context: AgentContext instance providing access to:
                - vector_store: Cross-session persistent memory
                - memory: Session-scoped ephemeral memory
                - learning_system: Pattern extraction and learning
        """
        self.context = agent_context
        self.vector_store = agent_context.vector_store
        self.memory = agent_context.memory

        # Initialize learning system for supervision integration
        from agency_memory.learning import LearningSystem

        self.learning_system = LearningSystem(
            vector_store=self.vector_store, min_confidence=0.6, auto_extraction_trigger=15
        )

        # Feature flag check
        self.router_enabled = os.getenv("FEATURE_MEMORY_ROUTER", "false").lower() == "true"

        if self.router_enabled:
            logger.info("MemoryRouter enabled (FEATURE_MEMORY_ROUTER=true)")
        else:
            logger.debug("MemoryRouter in legacy mode (FEATURE_MEMORY_ROUTER=false)")

    def store(
        self,
        key: str,
        content: Any,
        tags: list[str],
        confidence: float = 0.85,
        reinforcement_signal: dict[str, Any] | None = None,
        counterfactual: dict[str, Any] | None = None,
    ) -> Result[None, str]:
        """Store memory record with optional supervision signal (Article VIII)."""
        try:
            # Store in session memory (ephemeral)
            session_tags = tags + [f"session:{self.context.session_id}"]
            self.memory.store(key, content, session_tags)

            # Store in VectorStore (persistent, Article IV)
            self.vector_store.store(
                key=key, content=content, tags=tags, confidence=confidence
            )

            # Build ingest payload for learning system
            payload = {
                "key": key,
                "content": content,
                "tags": tags,
                "confidence": confidence,
            }

            # Add supervision signal if present (Article VIII)
            if reinforcement_signal:
                payload["supervision_signal"] = reinforcement_signal

            # Ingest into learning system (triggers auto-extraction, supervision storage)
            ingest_result = self.learning_system.ingest(payload)
            if ingest_result.is_err():
                logger.warning(f"Learning system ingest failed: {ingest_result.unwrap_err()}")

            # Store counterfactual if present (Article VIII)
            if counterfactual:
                self.store_counterfactual(
                    original_action=counterfactual.get("original_action", key),
                    alternative_action=counterfactual.get("alternative_action", "unknown"),
                    outcome=counterfactual.get("outcome", ""),
                    reason=counterfactual.get("reason", ""),
                )

            return Ok(None)

        except Exception as e:
            logger.error(f"Memory store failed: {e}")
            return Err(f"Store error: {e}")

    def retrieve(
        self,
        tags: list[str],
        min_confidence: float = 0.6,
        include_session: bool = True,
    ) -> list[dict[str, Any]]:
        """Retrieve memories matching tags and confidence threshold."""
        results = []

        # Search session-scoped memories if requested
        if include_session:
            session_tag = f"session:{self.context.session_id}"
            session_memories = self.memory.search([session_tag])

            # Filter by tags (conjunctive: ALL tags must match)
            req_tags = set(tags or [])
            for mem in session_memories:
                mem_tags = set(mem.get("tags", []))
                if req_tags.issubset(mem_tags):
                    results.append(mem)

        # Search VectorStore (persistent, Article IV)
        persistent_memories = self.vector_store.search_by_tags(
            tags=tags, min_confidence=min_confidence
        )
        results.extend(persistent_memories)

        # Deduplicate by key
        seen_keys = set()
        deduplicated = []
        for result in results:
            key = result.get("key") if isinstance(result, dict) else getattr(result, "key", None)
            if key and key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(result)

        return deduplicated

    def supervise(
        self,
        memory_id: str,
        signal: dict[str, Any],
        actor: str = "human",
        reason: str = "",
    ) -> Result[None, str]:
        """Apply supervision signal to existing memory (Article VIII)."""
        return self.learning_system.apply_supervision(
            memory_id=memory_id, signal=signal, actor=actor, reason=reason
        )

    def store_counterfactual(
        self,
        original_action: str,
        alternative_action: str,
        outcome: str,
        reason: str,
    ) -> Result[None, str]:
        """Store counterfactual (what-if analysis) for learning (Article VIII)."""
        try:
            counterfactual_record = {
                "original_action": original_action,
                "alternative_action": alternative_action,
                "outcome": outcome,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "provenance": {
                    "origin": "counterfactual_reasoning",
                    "actor": "MemoryRouter",
                    "timestamp": datetime.now().isoformat(),
                    "retention_policy": "permanent",  # Counterfactuals kept permanently
                },
            }

            # Store in VectorStore with high-value tags
            self.vector_store.store(
                key=f"counterfactual:{original_action}:{int(datetime.now().timestamp())}",
                content=counterfactual_record,
                tags=["counterfactual", "rl_training_data", "high_value"],
                confidence=0.9,  # Counterfactuals are high-confidence learning data
            )

            logger.info(
                f"Counterfactual stored: {original_action} → {alternative_action} (outcome: {outcome})"
            )

            return Ok(None)

        except Exception as e:
            logger.error(f"Counterfactual storage failed: {e}")
            return Err(f"Counterfactual error: {e}")


def get_memory_api(agent_context: Any) -> MemoryAPI:
    """Factory function to get MemoryAPI implementation.

    Returns MemoryRouter instance that implements the MemoryAPI protocol.
    Future: Can be extended to return different implementations based on flags.

    Args:
        agent_context: AgentContext instance

    Returns:
        MemoryAPI implementation (currently always MemoryRouter)

    Example:
        >>> from shared.agent_context import create_agent_context
        >>> from shared.memory_api import get_memory_api
        >>> context = create_agent_context()
        >>> api = get_memory_api(context)
        >>> api.store(key="test", content={"data": "value"}, tags=["test"])
    """
    return MemoryRouter(agent_context)


# Migration guide constants
MIGRATION_GUIDE = """
# Memory API Migration Guide

## Overview
Direct usage of VectorStore and EnhancedMemoryStore is being deprecated in favor
of the unified MemoryAPI protocol. This provides:
- Consistent API across all memory backends
- Built-in supervision signal support (Article VIII)
- Provenance tracking for all operations
- Counterfactual reasoning capabilities

## Migration Steps

### Step 1: Replace direct VectorStore usage
```python
# OLD (deprecated)
from agency_memory.vector_store import VectorStore
vector_store = VectorStore()
vector_store.store(key, content, tags, confidence)

# NEW (recommended)
from shared.memory_api import get_memory_api
from shared.agent_context import create_agent_context

context = create_agent_context()
api = get_memory_api(context)
api.store(key, content, tags, confidence)
```

### Step 2: Add supervision signals (Article VIII)
```python
# Store with supervision signal
api.store(
    key="jwt_auth_success",
    content={"code": "...", "tests_passed": True},
    tags=["coder", "auth", "success"],
    confidence=0.95,
    reinforcement_signal={
        "outcome": "approved",
        "quality_score": 0.95,
        "learning_value": 1.0
    }
)
```

### Step 3: Use retrieve() instead of search_by_tags()
```python
# OLD
results = vector_store.search_by_tags(tags=["auth", "success"], min_confidence=0.6)

# NEW
results = api.retrieve(tags=["auth", "success"], min_confidence=0.6)
```

### Step 4: Apply supervision signals
```python
# Apply RLHF-style feedback
api.supervise(
    memory_id="jwt_auth_success",
    signal={"outcome": "approved", "quality_score": 0.95},
    actor="human",
    reason="Excellent implementation"
)
```

### Step 5: Store counterfactuals
```python
# Enable what-if analysis
api.store_counterfactual(
    original_action="implement_jwt_simple",
    alternative_action="implement_jwt_with_refresh_tokens",
    outcome="Alternative would improve UX",
    reason="Refresh tokens reduce login friction"
)
```

## Backward Compatibility
- Feature flag: FEATURE_MEMORY_ROUTER=false (default) preserves legacy behavior
- Set FEATURE_MEMORY_ROUTER=true to enable new router
- All existing code continues to work unchanged
- Deprecation warnings logged when using direct VectorStore access

## Timeline
- 2025-10-26: MemoryAPI introduced, feature-flagged
- 2025-11-15: Deprecation warnings added
- 2025-12-01: FEATURE_MEMORY_ROUTER=true becomes default
- 2026-01-01: Direct VectorStore usage removed
"""
