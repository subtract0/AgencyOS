"""
Tests for Memory() VectorStore default (spec-027).

Validates that Memory() constructor defaults to EnhancedMemoryStore
instead of InMemoryStore, fixing Article IV constitutional violation.

Constitutional Compliance:
- Article II: TDD enforced (tests written FIRST, must fail initially)
- Article IV: VectorStore integration mandatory
- Article V: Spec-driven (spec-027)
"""

import os

import pytest
from agency_memory import EnhancedMemoryStore, InMemoryStore, Memory

try:
    import sentence_transformers  # noqa: F401
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
else:
    _SENTENCE_TRANSFORMERS_AVAILABLE = True

_RUN_VECTORSTORE_INTEGRATION = os.getenv("AGENCY_RUN_VECTORSTORE_TESTS", "0") == "1"

def test_memory_defaults_to_enhanced_memory_store():
    """
    Verify Memory() creates EnhancedMemoryStore by default.

    This test MUST fail initially (RED phase) before implementation.

    Article IV: VectorStore integration is constitutionally required.
    Article II: TDD mandatory (test first, implement second).
    """
    # Arrange: Create Memory with no explicit store parameter
    memory = Memory()

    # Act: Check the underlying store type
    actual_store = memory._store

    # Assert: Should be EnhancedMemoryStore (VectorStore), NOT InMemoryStore
    assert isinstance(
        actual_store, EnhancedMemoryStore
    ), f"Expected EnhancedMemoryStore, got {type(actual_store).__name__}"

    assert not isinstance(
        actual_store, InMemoryStore
    ), "Should NOT be InMemoryStore (ephemeral)"


def test_memory_explicit_store_works():
    """
    Verify explicit store param preserved (backward compatibility).

    Tests can explicitly pass InMemoryStore for ephemeral memory.

    Article II: Backward compatibility preserved.
    """
    # Arrange: Create Memory with explicit InMemoryStore
    memory = Memory(store=InMemoryStore())

    # Act: Check the underlying store type
    actual_store = memory._store

    # Assert: Should respect explicit parameter
    assert isinstance(
        actual_store, InMemoryStore
    ), "Explicit InMemoryStore parameter should be preserved"

    assert not isinstance(
        actual_store, EnhancedMemoryStore
    ), "Should NOT override explicit parameter"


def test_memory_explicit_enhanced_memory_store():
    """
    Verify explicit EnhancedMemoryStore param works.

    Tests backward compatibility for explicit VectorStore usage.
    """
    # Arrange: Create Memory with explicit EnhancedMemoryStore
    memory = Memory(store=EnhancedMemoryStore())

    # Act: Check the underlying store type
    actual_store = memory._store

    # Assert: Should respect explicit parameter
    assert isinstance(
        actual_store, EnhancedMemoryStore
    ), "Explicit EnhancedMemoryStore parameter should be preserved"


def test_memory_store_operations():
    """
    Verify Memory with default VectorStore supports basic operations.

    Tests that default Memory() is fully functional.
    """
    # Arrange: Create Memory with default store
    memory = Memory()

    # Act: Perform basic memory operations
    test_key = "test_pattern_memory_ops"
    test_content = {"type": "Result<T,E>", "confidence": 0.9}
    test_tags = ["pattern", "test"]

    # Store memory
    memory.store(test_key, test_content, tags=test_tags)

    # Search memory
    results = memory.search(tags=["pattern"])

    # Assert: Operations should work correctly
    assert len(results) > 0, "Should find stored pattern"

    # Verify stored content
    found = next((r for r in results if test_key in r.get("key", "")), None)
    assert found is not None, "Should find exact pattern by key"
    assert found["content"]["type"] == "Result<T,E>", "Content should match"


@pytest.mark.integration
@pytest.mark.skipif(
    not (_SENTENCE_TRANSFORMERS_AVAILABLE and _RUN_VECTORSTORE_INTEGRATION),
    reason=(
        "Requires sentence-transformers and AGENCY_RUN_VECTORSTORE_TESTS=1 "
        "to exercise vector-store persistence"
    ),
)
def test_memory_persistence_across_instances():
    """
    Integration test: Verify patterns persist across Memory instances.

    This validates Article IV requirement for institutional memory.

    Article IV: Cross-session learning accumulation mandatory.

    Note: Requires sentence-transformers package for full VectorStore functionality.
    """
    # Arrange: Create first Memory instance and store pattern
    memory1 = Memory()
    test_key = f"test_pattern_persistence_{id(memory1)}"
    test_content = {"type": "Pydantic", "confidence": 0.85}

    # Act: Store pattern in first instance
    memory1.store(test_key, test_content, tags=["pattern", "persistence_test"])

    # Create second Memory instance (simulates new process)
    memory2 = Memory()

    # Search for pattern from second instance
    results = memory2.search(tags=["persistence_test"])

    # Assert: Pattern should be found across instances
    assert len(results) > 0, "Should find pattern stored in different Memory instance"

    # Verify pattern content
    found = next((r for r in results if test_key in r.get("key", "")), None)
    assert found is not None, "Should find exact pattern by key"
    assert found["content"]["type"] == "Pydantic", "Pattern content should match"
