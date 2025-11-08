"""
Tests for VectorStore integration fix (spec-027).

Validates that create_agent_context() defaults to EnhancedMemoryStore
instead of InMemoryStore, fixing Article IV constitutional violation.

Constitutional Compliance:
- Article II: TDD enforced (tests written FIRST, must fail initially)
- Article IV: VectorStore integration mandatory
- Article V: Spec-driven (spec-027)
"""

import os

import pytest
from agency_memory import EnhancedMemoryStore, InMemoryStore, Memory
from shared.agent_context import create_agent_context

try:
    import sentence_transformers  # noqa: F401
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
else:
    _SENTENCE_TRANSFORMERS_AVAILABLE = True

_RUN_VECTORSTORE_INTEGRATION = os.getenv("AGENCY_RUN_VECTORSTORE_TESTS", "0") == "1"

def test_create_agent_context_defaults_to_vectorstore():
    """
    Verify create_agent_context() creates EnhancedMemoryStore by default.

    This test MUST fail initially (RED phase) before implementation.

    Article IV: VectorStore integration is constitutionally required.
    Article II: TDD mandatory (test first, implement second).
    """
    # Arrange: Create context with no explicit memory parameter
    context = create_agent_context()

    # Act: Check the underlying store type
    actual_store = context.memory._store

    # Assert: Should be EnhancedMemoryStore (VectorStore), NOT InMemoryStore
    assert isinstance(
        actual_store, EnhancedMemoryStore
    ), f"Expected EnhancedMemoryStore, got {type(actual_store).__name__}"

    assert not isinstance(
        actual_store, InMemoryStore
    ), "Should NOT be InMemoryStore (ephemeral)"


def test_create_agent_context_backward_compatibility():
    """
    Verify explicit Memory param still works (backward compatibility).

    Tests can explicitly pass InMemoryStore for ephemeral memory.

    Article II: Backward compatibility preserved.
    """
    # Arrange: Create context with explicit InMemoryStore
    explicit_memory = Memory(store=InMemoryStore())
    context = create_agent_context(memory=explicit_memory)

    # Act: Check the underlying store type
    actual_store = context.memory._store

    # Assert: Should respect explicit parameter
    assert isinstance(
        actual_store, InMemoryStore
    ), "Explicit InMemoryStore parameter should be preserved"

    assert not isinstance(
        actual_store, EnhancedMemoryStore
    ), "Should NOT override explicit parameter"


def test_create_agent_context_explicit_enhanced_memory_store():
    """
    Verify explicit EnhancedMemoryStore param works.

    Tests backward compatibility for explicit VectorStore usage.
    """
    # Arrange: Create context with explicit EnhancedMemoryStore
    explicit_memory = Memory(store=EnhancedMemoryStore())
    context = create_agent_context(memory=explicit_memory)

    # Act: Check the underlying store type
    actual_store = context.memory._store

    # Assert: Should respect explicit parameter
    assert isinstance(
        actual_store, EnhancedMemoryStore
    ), "Explicit EnhancedMemoryStore parameter should be preserved"


def test_create_agent_context_with_session_id():
    """
    Verify create_agent_context() with session_id uses VectorStore.

    Session ID should not affect store type selection.
    """
    # Arrange: Create context with session_id
    context = create_agent_context(session_id="test_session_123")

    # Act: Check the underlying store type
    actual_store = context.memory._store

    # Assert: Should still use EnhancedMemoryStore
    assert isinstance(
        actual_store, EnhancedMemoryStore
    ), "Session ID should not affect VectorStore default"

    # Verify session_id was set correctly
    assert context.session_id == "test_session_123"


@pytest.mark.integration
@pytest.mark.skipif(
    not (_SENTENCE_TRANSFORMERS_AVAILABLE and _RUN_VECTORSTORE_INTEGRATION),
    reason=(
        "Requires sentence-transformers and AGENCY_RUN_VECTORSTORE_TESTS=1 "
        "to exercise vector-store persistence"
    ),
)
def test_create_agent_context_cross_session_persistence():
    """
    Integration test: Verify patterns persist across different contexts.

    This validates Article IV requirement for institutional memory.

    Article IV: Cross-session learning accumulation mandatory.

    Note: Requires sentence-transformers package for full VectorStore functionality.
    """
    # Arrange: Create first context and store pattern
    context1 = create_agent_context(session_id="session_1")
    test_key = f"test_pattern_cross_session_{context1.session_id}"

    # Act: Store pattern in session 1
    context1.store_memory(
        test_key, {"type": "Result<T,E>", "confidence": 0.9}, tags=["pattern", "test"]
    )

    # Create second context (simulates new process/session)
    context2 = create_agent_context(session_id="session_2")

    # Search for pattern from session 2
    results = context2.search_memories(["pattern", "test"], include_session=True)

    # Assert: Pattern should be found across sessions
    assert len(results) > 0, "Should find pattern stored in different session"

    # Verify pattern content
    found_pattern = next(
        (r for r in results if test_key in r.get("key", "")), None
    )
    assert found_pattern is not None, "Should find exact pattern by key"
    assert (
        found_pattern["content"]["type"] == "Result<T,E>"
    ), "Pattern content should match"
