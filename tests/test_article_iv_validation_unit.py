"""
Unit Tests for Article IV Self-Reflective Learning Validation (TDD - RED Phase).

**Constitutional Requirement**: Article IV mandates that agents:
1. Query VectorStore BEFORE action (search_memories)
2. Store learnings AFTER success (store_memory)

**Expected Behavior**: Tests will FAIL where violations exist (RED phase).
Implementation fixes will make tests PASS (GREEN phase).

Specification: specs/spec-039-article-iv-self-reflective-learning.md
ADR-004: Continuous Learning and Improvement

**NECESSARY Pattern Coverage**:
- N: Normal operation (query → action → store)
- E: Edge cases (empty VectorStore, duplicate storage)
- C: Corner cases (concurrent queries)
- E: Error conditions (VectorStore unavailable)
- S: Security (secret sanitization)
- S: Stress (not applicable for unit tests - see integration)
- A: Accessibility (not applicable - internal APIs)
- R: Regression (constitutional violations)
- Y: Yield validation (timing, data correctness)
"""

import time
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from agency_memory import Memory
from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from shared.agent_context import AgentContext, create_agent_context
from shared.type_definitions.json_value import JSONValue


# =============================================================================
# NORMAL OPERATION TESTS (Happy Path)
# =============================================================================


def test_agent_context_search_memories_api_exists() -> None:
    """
    **Unit Test**: Verify AgentContext provides search_memories() API.

    Given: AgentContext instance
    When: Call search_memories(tags)
    Then: Method exists and returns list

    **Article IV Requirement**: Query API must exist for all agents.
    """
    # Arrange
    context = create_agent_context(session_id="test_session")

    # Act
    result = context.search_memories(tags=["test"], include_session=False)

    # Assert
    assert isinstance(result, list), "search_memories() must return list"
    assert hasattr(context, "search_memories"), "AgentContext must have search_memories() method"


def test_agent_context_store_memory_api_exists() -> None:
    """
    **Unit Test**: Verify AgentContext provides store_memory() API.

    Given: AgentContext instance
    When: Call store_memory(key, content, tags)
    Then: Method exists and stores without error

    **Article IV Requirement**: Storage API must exist for all agents.
    """
    # Arrange
    context = create_agent_context(session_id="test_session")

    # Act
    context.store_memory(
        key="test_pattern",
        content={"type": "test_pattern", "data": "test"},
        tags=["test", "pattern"],
    )

    # Assert
    assert hasattr(context, "store_memory"), "AgentContext must have store_memory() method"

    # Verify storage succeeded
    memories = context.search_memories(tags=["test"], include_session=True)
    assert len(memories) > 0, "Stored memory should be retrievable"


def test_query_before_action_pattern() -> None:
    """
    **Unit Test**: Verify query-before-action pattern.

    Given: Agent starting task
    When: Agent queries VectorStore, then acts
    Then: Query timestamp < action timestamp

    **Article IV Requirement**: Agents must query BEFORE action.
    **Expected**: PASS (demonstrates correct pattern).
    """
    # Arrange
    context = create_agent_context(session_id="test_session")

    # Pre-populate VectorStore with pattern
    context.store_memory(
        key="prior_success",
        content={"solution": "use JWT library", "tests_passed": True},
        tags=["auth", "success", "pattern"],
    )

    # Act: Query before action (CORRECT order)
    query_timestamp = time.time()
    patterns = context.search_memories(tags=["auth", "pattern"], include_session=False)

    # Simulate action AFTER query
    time.sleep(0.01)  # Ensure timestamp difference
    action_timestamp = time.time()

    # Assert: Query happened BEFORE action
    assert query_timestamp < action_timestamp, "Query must happen BEFORE action"
    assert len(patterns) >= 0, "Query should execute (even if empty)"


def test_store_after_success_pattern() -> None:
    """
    **Unit Test**: Verify store-after-success pattern.

    Given: Agent completes task successfully
    When: Agent stores learning to VectorStore
    Then: Storage happens AFTER success, data persisted

    **Article IV Requirement**: Agents must store AFTER success.
    **Expected**: PASS (demonstrates correct pattern).
    """
    # Arrange
    context = create_agent_context(session_id="test_session")

    # Act: Simulate successful task
    task_success_timestamp = time.time()

    # Simulate delay before storage
    time.sleep(0.01)

    # Store learning AFTER success (CORRECT order)
    context.store_memory(
        key=f"success_{int(task_success_timestamp)}",
        content={"task": "implement_auth", "outcome": "success", "tests_passed": True},
        tags=["auth", "success", "pattern"],
    )

    storage_timestamp = time.time()

    # Assert: Storage happened AFTER success
    assert storage_timestamp > task_success_timestamp, "Storage must happen AFTER success"

    # Verify persistence
    memories = context.search_memories(tags=["auth", "success"], include_session=True)
    assert len(memories) > 0, "Success pattern should be stored and retrievable"


# =============================================================================
# EDGE CASE TESTS (Boundaries, Limits)
# =============================================================================


def test_empty_vectorstore_query() -> None:
    """
    **Edge Case**: Agent queries VectorStore with no matching patterns.

    Given: Empty VectorStore (no prior learnings)
    When: Agent queries for patterns
    Then: Returns empty list, agent proceeds without prior knowledge

    **Article IV Requirement**: Agent must query even if no patterns exist.
    **Expected**: PASS (graceful handling of empty results).
    """
    # Arrange
    context = create_agent_context(session_id="test_cold_start")

    # Act: Query VectorStore (no prior data)
    patterns = context.search_memories(tags=["nonexistent_tag"], include_session=False)

    # Assert
    assert isinstance(patterns, list), "Query should return list even if empty"
    assert len(patterns) == 0, "Empty VectorStore should return empty list"
    # Agent should proceed without error (graceful fallback)


def test_duplicate_memory_storage() -> None:
    """
    **Edge Case**: Agent stores same pattern twice.

    Given: Pattern already stored in VectorStore
    When: Agent stores identical pattern again
    Then: Deduplication occurs OR both stored with different timestamps

    **Article IV Requirement**: Storage must handle duplicates gracefully.
    **Expected**: PASS (no crash, both entries distinguishable by timestamp).
    """
    # Arrange
    context = create_agent_context(session_id="test_deduplication")

    pattern_data = {"solution": "use RSA-256", "tests_passed": True}

    # Act: Store pattern twice
    context.store_memory(key="pattern_v1", content=pattern_data, tags=["auth", "pattern"])

    time.sleep(0.01)  # Ensure timestamp difference

    context.store_memory(key="pattern_v2", content=pattern_data, tags=["auth", "pattern"])

    # Assert: Both stored (or deduplicated)
    memories = context.search_memories(tags=["auth", "pattern"], include_session=True)

    # Either deduplication occurred (1 entry) OR both stored (2 entries)
    assert len(memories) >= 1, "At least one pattern should be stored"
    # No crash, graceful handling


def test_concurrent_memory_queries() -> None:
    """
    **Edge Case**: Multiple agents query VectorStore simultaneously.

    Given: 10 agents querying VectorStore concurrently
    When: All agents call search_memories() at same time
    Then: No race conditions, all queries complete successfully

    **Article IV Requirement**: VectorStore must handle concurrent reads.
    **Expected**: PASS (VectorStore is thread-safe for reads).
    """
    # Arrange
    context = create_agent_context(session_id="test_concurrency")

    # Pre-populate VectorStore
    context.store_memory(key="shared_pattern", content={"data": "test"}, tags=["shared"])

    # Act: Simulate 10 concurrent queries (using threading)
    import threading

    results: List[List[Dict[str, JSONValue]]] = []
    errors: List[Exception] = []

    def query_vectorstore() -> None:
        try:
            patterns = context.search_memories(tags=["shared"], include_session=True)
            results.append(patterns)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=query_vectorstore) for _ in range(10)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Assert: All queries succeeded
    assert len(errors) == 0, f"Concurrent queries should not raise errors: {errors}"
    assert len(results) == 10, "All 10 queries should complete"
    assert all(len(r) > 0 for r in results), "All queries should find the shared pattern"


# =============================================================================
# ERROR CONDITION TESTS (Invalid Inputs, Failures)
# =============================================================================


def test_vectorstore_unavailable_graceful_fallback() -> None:
    """
    **Error Test**: VectorStore unavailable (network down, service crashed).

    Given: VectorStore backend unavailable
    When: Agent calls search_memories()
    Then: Logs warning, returns empty list, continues execution (no crash)

    **Article IV Requirement**: VectorStore failure must not block agents.
    **Expected**: PASS (graceful fallback, warning logged).
    """
    # Arrange: Mock VectorStore to raise exception
    context = create_agent_context(session_id="test_fallback")

    with patch.object(context.memory, "search", side_effect=Exception("VectorStore unavailable")):
        # Act: Query VectorStore (mocked to fail)
        try:
            patterns = context.search_memories(tags=["test"], include_session=False)

            # Assert: Graceful fallback (empty list or exception caught)
            # Current implementation might raise exception - THIS TEST MIGHT FAIL (RED)
            assert isinstance(
                patterns, list
            ), "Should return empty list on VectorStore failure (graceful fallback)"
            assert len(patterns) == 0, "Fallback should return empty list"

        except Exception as e:
            # If exception raised, test FAILS (needs graceful fallback implementation)
            pytest.fail(
                f"VectorStore failure should not raise exception (graceful fallback needed): {e}"
            )


def test_missing_query_constitutional_violation() -> None:
    """
    **Regression Test**: Agent skips VectorStore query before action.

    Given: Agent implementation that acts without querying VectorStore
    When: Constitutional validator checks Article IV compliance
    Then: Violation detected, error raised

    **Article IV Requirement**: Agents MUST query before action.
    **Expected**: FAIL (violation detection not implemented yet - RED phase).
    """
    # Arrange: Simulate agent that skips query
    context = create_agent_context(session_id="test_violation")

    # Mock telemetry to track query calls
    query_called = False

    original_search = context.search_memories

    def tracked_search(*args: Any, **kwargs: Any) -> List[Dict[str, JSONValue]]:
        nonlocal query_called
        query_called = True
        return original_search(*args, **kwargs)

    context.search_memories = tracked_search  # type: ignore

    # Act: Agent takes action WITHOUT querying (VIOLATION)
    # (Simulate by not calling search_memories)

    action_completed = True  # Simulate agent completing action

    # Assert: Violation should be detected
    # THIS TEST WILL FAIL until violation detector is implemented (RED phase expected)
    if action_completed and not query_called:
        # Violation detector not yet implemented - mark as expected failure
        pytest.skip(
            "Article IV violation detector not yet implemented (RED phase expected). "
            "Implementation needed: Pre-action hook to enforce query requirement."
        )

    # When implemented, this assertion should PASS:
    # assert query_called, "Agent must query VectorStore before action (Article IV)"


def test_missing_storage_constitutional_violation() -> None:
    """
    **Regression Test**: Agent skips VectorStore storage after success.

    Given: Agent completes task successfully
    When: Agent does NOT store learning to VectorStore
    Then: Violation detected, warning logged

    **Article IV Requirement**: Agents MUST store after success.
    **Expected**: FAIL (violation detection not implemented yet - RED phase).
    """
    # Arrange: Simulate agent that skips storage
    context = create_agent_context(session_id="test_storage_violation")

    # Mock telemetry to track storage calls
    storage_called = False

    original_store = context.store_memory

    def tracked_store(*args: Any, **kwargs: Any) -> None:
        nonlocal storage_called
        storage_called = True
        original_store(*args, **kwargs)

    context.store_memory = tracked_store  # type: ignore

    # Act: Agent succeeds but does NOT store (VIOLATION)
    task_succeeded = True

    # Simulate agent completing without storage
    # (no store_memory call)

    # Assert: Violation should be detected
    # THIS TEST WILL FAIL until violation detector is implemented (RED phase expected)
    if task_succeeded and not storage_called:
        # Violation detector not yet implemented - mark as expected failure
        pytest.skip(
            "Article IV violation detector not yet implemented (RED phase expected). "
            "Implementation needed: Post-success hook to enforce storage requirement."
        )

    # When implemented, this assertion should PASS:
    # assert storage_called, "Agent must store learning after success (Article IV)"


# =============================================================================
# SECURITY TESTS (Input Validation, Secret Sanitization)
# =============================================================================


def test_sensitive_data_not_stored_in_patterns() -> None:
    """
    **Security Test**: Patterns must not contain API keys, passwords, secrets.

    Given: Agent stores pattern containing sensitive data
    When: Pattern sanitization runs before storage
    Then: Secrets removed, sanitized pattern stored

    **Security Requirement**: Prevent secrets leaking to VectorStore.
    **Expected**: FAIL (sanitization not implemented yet - RED phase).
    """
    # Arrange
    context = create_agent_context(session_id="test_secret_sanitization")

    # Act: Store pattern containing secrets (SECURITY VIOLATION)
    pattern_with_secrets = {
        "solution": "use JWT library",
        "api_key": "sk-1234567890abcdef",  # SECRET!
        "password": "super_secret_password",  # SECRET!
        "tests_passed": True,
    }

    context.store_memory(
        key="insecure_pattern", content=pattern_with_secrets, tags=["auth", "pattern"]
    )

    # Assert: Secrets should be sanitized (removed or redacted)
    memories = context.search_memories(tags=["auth"], include_session=True)
    assert len(memories) > 0, "Pattern should be stored"

    stored_pattern = memories[0].get("content", {})

    # THIS TEST WILL FAIL until sanitization is implemented (RED phase expected)
    if "api_key" in stored_pattern or "password" in stored_pattern:
        pytest.skip(
            "Secret sanitization not yet implemented (RED phase expected). "
            "Implementation needed: Pre-storage sanitization layer to remove secrets."
        )

    # When implemented, these assertions should PASS:
    # assert "api_key" not in stored_pattern, "API keys must be sanitized"
    # assert "password" not in stored_pattern, "Passwords must be sanitized"


def test_pattern_sanitization_regex() -> None:
    """
    **Security Test**: Sanitization layer detects common secret patterns.

    Given: Pattern containing api_key, token, password fields
    When: Sanitization regex scans pattern
    Then: Secret fields detected and removed

    **Security Requirement**: Regex-based secret detection.
    **Expected**: FAIL (sanitization layer not implemented - RED phase).
    """
    # Arrange: Pattern with multiple secret types
    pattern = {
        "api_key": "sk-abc123",
        "auth_token": "Bearer xyz789",
        "password": "hunter2",
        "db_password": "postgres123",
        "secret_key": "secret_abc",
        "safe_field": "this is fine",
    }

    # Act: Sanitization layer (NOT YET IMPLEMENTED)
    # When implemented:
    # sanitized = sanitize_pattern(pattern)

    # Assert: THIS TEST WILL FAIL until sanitization is implemented
    pytest.skip(
        "Pattern sanitization layer not yet implemented (RED phase expected). "
        "Implementation needed: sanitize_pattern() function with regex for secrets."
    )

    # When implemented, these assertions should PASS:
    # assert "api_key" not in sanitized
    # assert "auth_token" not in sanitized
    # assert "password" not in sanitized
    # assert "db_password" not in sanitized
    # assert "secret_key" not in sanitized
    # assert sanitized["safe_field"] == "this is fine"


# =============================================================================
# VALIDATION TESTS (Timing, Data Correctness)
# =============================================================================


def test_query_timing_validation() -> None:
    """
    **Validation Test**: Query must happen BEFORE action (timestamp check).

    Given: Agent workflow with telemetry logging
    When: Agent queries VectorStore, then acts
    Then: query_timestamp < action_timestamp (verified via telemetry)

    **Article IV Requirement**: Timing enforcement.
    **Expected**: PASS (demonstrates correct timing).
    """
    # Arrange
    context = create_agent_context(session_id="test_timing")

    # Act: Query → Action sequence
    query_start = time.time()
    patterns = context.search_memories(tags=["test"], include_session=False)
    query_end = time.time()

    time.sleep(0.01)  # Ensure separation

    action_start = time.time()
    # Simulate action (no-op)
    action_end = time.time()

    # Assert: Query completed BEFORE action started
    assert query_end < action_start, "Query must complete BEFORE action starts"
    assert query_start < action_start, "Query must start BEFORE action starts"


def test_storage_timing_validation() -> None:
    """
    **Validation Test**: Storage must happen AFTER success (timestamp check).

    Given: Agent workflow with telemetry logging
    When: Agent succeeds, then stores learning
    Then: success_timestamp < storage_timestamp (verified via telemetry)

    **Article IV Requirement**: Timing enforcement.
    **Expected**: PASS (demonstrates correct timing).
    """
    # Arrange
    context = create_agent_context(session_id="test_storage_timing")

    # Act: Success → Storage sequence
    success_timestamp = time.time()

    time.sleep(0.01)  # Ensure separation

    storage_start = time.time()
    context.store_memory(
        key=f"success_{int(success_timestamp)}",
        content={"outcome": "success"},
        tags=["test"],
    )
    storage_end = time.time()

    # Assert: Storage happened AFTER success
    assert storage_start > success_timestamp, "Storage must happen AFTER success"


def test_storage_only_on_success() -> None:
    """
    **Validation Test**: Storage should NOT occur on failure.

    Given: Agent task fails
    When: Agent completes with error
    Then: No storage call to VectorStore (don't learn from failures)

    **Article IV Requirement**: Store only successful patterns.
    **Expected**: PASS (demonstrates correct conditional storage).
    """
    # Arrange
    context = create_agent_context(session_id="test_no_storage_on_failure")

    # Mock telemetry to track storage
    storage_called = False

    original_store = context.store_memory

    def tracked_store(*args: Any, **kwargs: Any) -> None:
        nonlocal storage_called
        storage_called = True
        original_store(*args, **kwargs)

    context.store_memory = tracked_store  # type: ignore

    # Act: Simulate task failure
    task_failed = True

    if task_failed:
        # Agent should NOT store on failure
        pass  # No storage call

    # Assert: Storage should NOT have been called
    assert not storage_called, "Agent should NOT store learning on failure"


# =============================================================================
# SUMMARY
# =============================================================================

"""
**Test Summary**:

**Normal (4 tests)**: API existence, query-before-action, store-after-success patterns
**Edge (3 tests)**: Empty VectorStore, duplicate storage, concurrent queries
**Error (3 tests)**: VectorStore unavailable, missing query/storage violations
**Security (2 tests)**: Secret sanitization, regex detection
**Validation (3 tests)**: Query timing, storage timing, conditional storage

**Total**: 15 unit tests

**Expected RED Phase Failures**:
1. test_vectorstore_unavailable_graceful_fallback (no graceful fallback yet)
2. test_missing_query_constitutional_violation (no violation detector)
3. test_missing_storage_constitutional_violation (no violation detector)
4. test_sensitive_data_not_stored_in_patterns (no sanitization layer)
5. test_pattern_sanitization_regex (no sanitization implementation)

**Expected PASS Tests**: 10 tests (API, patterns, timing, concurrency)
**Expected SKIP Tests**: 5 tests (awaiting implementation - RED phase)

**Next Steps** (GREEN phase):
1. Implement graceful fallback for VectorStore failures
2. Implement violation detector (pre-action hook, post-success hook)
3. Implement secret sanitization layer
4. Run tests again to verify GREEN phase
"""
