"""Integration tests for cross-session learning via VectorStore.

Article IV: Continuous Learning and Improvement (ADR-004)
- Patterns stored in one session must be queryable in another session
- Cross-session knowledge accumulation is constitutionally mandatory
- VectorStore provides institutional memory across restarts
"""
import uuid
import pytest
from shared.agent_context import create_agent_context


def test_pattern_persists_across_sessions():
    """Verify patterns stored in session 1 are queryable in session 2."""
    # Session 1: Store pattern with unique tag
    session_1_id = f"test_session_{uuid.uuid4()}"
    context_1 = create_agent_context(session_id=session_1_id)

    test_pattern_key = f"test_pattern_{uuid.uuid4()}"
    unique_tag = f"cross_session_test_{uuid.uuid4()}"

    context_1.store_memory(
        key=test_pattern_key,
        content={"solution": "test_fix", "confidence": 0.95},
        tags=["test", unique_tag, "pattern"]
    )

    # Session 2: Query pattern
    session_2_id = f"test_session_{uuid.uuid4()}"
    context_2 = create_agent_context(session_id=session_2_id)

    results = context_2.search_memories(
        tags=[unique_tag],
        include_session=True  # Include cross-session memories
    )

    # Pattern should be found in session 2
    assert len(results) > 0, f"Pattern with tag {unique_tag} not found in cross-session search"
    found_keys = [r["key"] for r in results]
    assert test_pattern_key in found_keys, f"Expected key {test_pattern_key} not in results: {found_keys}"


def test_search_memories_cross_session_flag():
    """Verify include_session flag controls cross-session search."""
    context = create_agent_context()

    # Store pattern with unique tag
    unique_tag = f"unique_test_{uuid.uuid4()}"
    context.store_memory(
        key=f"pattern_{uuid.uuid4()}",
        content={"test": "data"},
        tags=[unique_tag]
    )

    # Search with include_session=False (session-only)
    session_only = context.search_memories(
        tags=[unique_tag],
        include_session=False
    )

    # Search with include_session=True (cross-session)
    cross_session = context.search_memories(
        tags=[unique_tag],
        include_session=True
    )

    # Cross-session should have equal or more results than session-only
    assert len(cross_session) >= len(session_only), (
        f"Cross-session search ({len(cross_session)} results) should have >= "
        f"session-only search ({len(session_only)} results)"
    )


def test_pattern_confidence_preserved():
    """Verify pattern confidence scores persist across restarts."""
    # Store pattern with specific confidence
    context_1 = create_agent_context()
    test_key = f"confidence_test_{uuid.uuid4()}"
    unique_tag = f"confidence_preservation_{uuid.uuid4()}"

    context_1.store_memory(
        key=test_key,
        content={"solution": "test", "confidence": 0.87},
        tags=[unique_tag]
    )

    # Query in new session
    context_2 = create_agent_context()
    results = context_2.search_memories(
        tags=[unique_tag],
        include_session=True
    )

    # Find our pattern
    our_pattern = next((r for r in results if r["key"] == test_key), None)
    assert our_pattern is not None, f"Pattern with key {test_key} not found in results"
    assert our_pattern["content"]["confidence"] == 0.87, (
        f"Expected confidence 0.87, got {our_pattern['content']['confidence']}"
    )


def test_vectorstore_integration_mandatory():
    """Verify VectorStore integration is constitutionally mandatory (Article IV)."""
    from shared.constitutional_validator import validate_article_iv

    # Default context should use VectorStore (EnhancedMemoryStore)
    context = create_agent_context()

    # Article IV validation should PASS with VectorStore
    result = validate_article_iv(context)

    assert result.is_ok(), f"Article IV validation failed: {result.unwrap_err() if result.is_err() else 'N/A'}"

    # Verify memory backend is NOT InMemoryStore
    from agency_memory import InMemoryStore
    assert not isinstance(context.memory._store, InMemoryStore), (
        "Memory backend is InMemoryStore (violates Article IV)"
    )


def test_cross_session_tag_filtering():
    """Verify tag filtering works across sessions."""
    context_1 = create_agent_context()

    # Store patterns with different tags
    unique_prefix = f"tag_filter_{uuid.uuid4()}"
    tag_a = f"{unique_prefix}_a"
    tag_b = f"{unique_prefix}_b"

    context_1.store_memory(
        key=f"pattern_a_{uuid.uuid4()}",
        content={"type": "A"},
        tags=[tag_a]
    )

    context_1.store_memory(
        key=f"pattern_b_{uuid.uuid4()}",
        content={"type": "B"},
        tags=[tag_b]
    )

    # Query in new session with specific tag
    context_2 = create_agent_context()

    results_a = context_2.search_memories(tags=[tag_a], include_session=True)
    results_b = context_2.search_memories(tags=[tag_b], include_session=True)

    # Each query should only return patterns with the requested tag
    assert len(results_a) > 0, f"No results found for tag {tag_a}"
    assert len(results_b) > 0, f"No results found for tag {tag_b}"

    # Verify content type matches
    for result in results_a:
        assert result["content"]["type"] == "A", f"Expected type A, got {result['content']['type']}"

    for result in results_b:
        assert result["content"]["type"] == "B", f"Expected type B, got {result['content']['type']}"
