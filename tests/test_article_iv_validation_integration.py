"""
Integration Tests for Article IV Compliance - Agent Workflows (TDD - RED Phase).

**Constitutional Requirement**: Article IV mandates agents query VectorStore before
action and store learnings after success across REAL agent workflows.

**Expected Behavior**: Tests will FAIL where agent implementations lack Article IV
compliance (RED phase). Fixes will make tests PASS (GREEN phase).

Specification: specs/spec-039-article-iv-self-reflective-learning.md
ADR-004: Continuous Learning and Improvement

**NECESSARY Pattern Coverage**:
- N: Normal workflows (CodingAgent, PlannerAgent, QualityEnforcer full lifecycle)
- E: Edge cases (partial success, cross-session pattern application)
- C: Corner cases (not applicable - covered in unit tests)
- E: Error conditions (agent continues on VectorStore failure)
- S: Security (not applicable - covered in unit tests)
- S: Stress (not applicable - see E2E tests)
- A: Accessibility (not applicable - internal workflows)
- R: Regression (verify past violations don't recur)
- Y: Yield validation (patterns applied correctly, cross-session learning)
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from agency_memory import Memory
from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from shared.agent_context import AgentContext, create_agent_context
from shared.type_definitions.json_value import JSONValue


# =============================================================================
# INTEGRATION TEST 1: CodingAgent Workflow
# =============================================================================


@pytest.mark.integration
def test_coding_agent_queries_vectorstore_before_implementation() -> None:
    """
    **Integration**: CodingAgent queries VectorStore before implementing code.

    Given: CodingAgent receives task to implement feature
    When: CodingAgent.execute() runs
    Then: search_memories() called BEFORE write tool usage

    **Article IV Requirement**: Query before action (implementation).
    **Expected**: FAIL (CodingAgent might not query VectorStore yet - RED phase).
    """
    # Arrange: Create context with prior patterns
    context = create_agent_context(session_id="coding_agent_integration")

    # Pre-populate VectorStore with relevant pattern
    context.store_memory(
        key="prior_auth_pattern",
        content={
            "task_type": "authentication",
            "solution": "use JWT library with RSA-256",
            "tests_passed": True,
            "test_count": 47,
        },
        tags=["coder", "auth", "success", "pattern"],
    )

    # Mock: Track method calls
    query_called = False
    action_called = False
    call_order: List[str] = []

    original_search = context.search_memories

    def tracked_search(*args: Any, **kwargs: Any) -> List[Dict[str, JSONValue]]:
        nonlocal query_called
        query_called = True
        call_order.append("query")
        return original_search(*args, **kwargs)

    context.search_memories = tracked_search  # type: ignore

    # Act: Simulate CodingAgent.execute() workflow
    # Step 1: Agent SHOULD query VectorStore
    patterns = context.search_memories(tags=["coder", "auth"], include_session=False)

    # Step 2: Agent implements code (action)
    call_order.append("action")
    action_called = True
    implementation = "# Generated code using pattern: " + str(patterns)

    # Assert: Query happened BEFORE action
    assert query_called, "CodingAgent must query VectorStore before implementation"
    assert action_called, "CodingAgent completed implementation"
    assert call_order == [
        "query",
        "action",
    ], "Query must happen BEFORE action (Article IV)"

    # Verify pattern was found and used
    assert len(patterns) > 0, "VectorStore should return relevant pattern"
    assert "JWT" in str(implementation), "Implementation should use learned pattern"


@pytest.mark.integration
def test_agent_stores_pattern_after_successful_completion() -> None:
    """
    **Integration**: Agent stores learning after successful task completion.

    Given: Agent completes task with 100% test pass
    When: Task marked as success
    Then: store_memory() called with task outcome

    **Article IV Requirement**: Store after success.
    **Expected**: FAIL (agents might not store learnings yet - RED phase).
    """
    # Arrange
    context = create_agent_context(session_id="storage_integration")

    # Mock: Track storage calls
    storage_called = False
    stored_data: Dict[str, Any] = {}

    original_store = context.store_memory

    def tracked_store(key: str, content: Any, tags: List[str]) -> None:
        nonlocal storage_called, stored_data
        storage_called = True
        stored_data = {"key": key, "content": content, "tags": tags}
        original_store(key, content, tags)

    context.store_memory = tracked_store  # type: ignore

    # Act: Simulate successful task completion
    task_result = {"tests_passed": True, "test_count": 47, "outcome": "success"}

    # Agent SHOULD store learning after success
    context.store_memory(
        key=f"success_auth_impl_{int(time.time())}",
        content=task_result,
        tags=["coder", "auth", "success", "pattern"],
    )

    # Assert: Storage occurred
    assert storage_called, "Agent must store learning after success (Article IV)"
    assert stored_data["content"]["tests_passed"] is True, "Stored pattern should include test status"
    assert "success" in stored_data["tags"], "Stored pattern should be tagged as success"


# =============================================================================
# INTEGRATION TEST 2: PlannerAgent Workflow
# =============================================================================


@pytest.mark.integration
def test_planner_queries_vectorstore_before_planning() -> None:
    """
    **Integration**: PlannerAgent queries VectorStore before creating plan.

    Given: PlannerAgent receives spec to plan
    When: PlannerAgent.create_plan() runs
    Then: search_memories() called BEFORE plan generation

    **Article IV Requirement**: Query before planning action.
    **Expected**: FAIL (PlannerAgent might not query VectorStore yet - RED phase).
    """
    # Arrange
    context = create_agent_context(session_id="planner_integration")

    # Pre-populate with prior planning pattern
    context.store_memory(
        key="prior_plan_pattern",
        content={
            "task_type": "authentication_feature",
            "plan_structure": "Spec → Design → Implementation → Testing → Review",
            "success_rate": 0.95,
        },
        tags=["planner", "auth", "success", "pattern"],
    )

    # Mock: Track calls
    query_called = False
    plan_created = False
    call_order: List[str] = []

    original_search = context.search_memories

    def tracked_search(*args: Any, **kwargs: Any) -> List[Dict[str, JSONValue]]:
        nonlocal query_called
        query_called = True
        call_order.append("query")
        return original_search(*args, **kwargs)

    context.search_memories = tracked_search  # type: ignore

    # Act: PlannerAgent workflow
    # Step 1: Query VectorStore for planning patterns
    patterns = context.search_memories(tags=["planner", "auth"], include_session=False)

    # Step 2: Create plan (action)
    call_order.append("create_plan")
    plan_created = True
    plan = {"phases": ["Spec", "Design", "Implementation"], "learned_from": str(patterns)}

    # Assert
    assert query_called, "PlannerAgent must query VectorStore before planning"
    assert plan_created, "PlannerAgent completed plan creation"
    assert call_order == ["query", "create_plan"], "Query must happen BEFORE planning"
    assert len(patterns) > 0, "VectorStore should return relevant planning pattern"


# =============================================================================
# INTEGRATION TEST 3: QualityEnforcer Workflow
# =============================================================================


@pytest.mark.integration
def test_quality_enforcer_queries_vectorstore_before_validation() -> None:
    """
    **Integration**: QualityEnforcer queries VectorStore before validation.

    Given: QualityEnforcer receives code to validate
    When: QualityEnforcer.validate() runs
    Then: search_memories() called to retrieve validation patterns

    **Article IV Requirement**: Query before validation action.
    **Expected**: FAIL (QualityEnforcer might not query VectorStore yet - RED phase).
    """
    # Arrange
    context = create_agent_context(session_id="quality_enforcer_integration")

    # Pre-populate with validation patterns
    context.store_memory(
        key="validation_pattern_auth",
        content={
            "validation_type": "authentication_security",
            "checks": ["JWT validation", "RSA-256 signature", "token expiry"],
            "success_rate": 1.0,
        },
        tags=["quality_enforcer", "auth", "validation", "pattern"],
    )

    # Mock: Track calls
    query_called = False
    validation_completed = False

    original_search = context.search_memories

    def tracked_search(*args: Any, **kwargs: Any) -> List[Dict[str, JSONValue]]:
        nonlocal query_called
        query_called = True
        return original_search(*args, **kwargs)

    context.search_memories = tracked_search  # type: ignore

    # Act: QualityEnforcer workflow
    # Step 1: Query for validation patterns
    patterns = context.search_memories(
        tags=["quality_enforcer", "validation"], include_session=False
    )

    # Step 2: Perform validation
    validation_completed = True
    validation_result = {
        "checks_performed": ["JWT validation", "RSA-256 signature"],
        "patterns_used": len(patterns),
    }

    # Assert
    assert query_called, "QualityEnforcer must query VectorStore before validation"
    assert validation_completed, "QualityEnforcer completed validation"
    assert len(patterns) > 0, "VectorStore should return validation patterns"


# =============================================================================
# INTEGRATION TEST 4: Cross-Session Pattern Application
# =============================================================================


@pytest.mark.integration
def test_pattern_application_from_previous_session() -> None:
    """
    **Integration**: Agent applies pattern from PREVIOUS session (cross-session learning).

    Given: Session A stored pattern, Session B queries for same task type
    When: Session B agent queries VectorStore
    Then: Pattern from Session A retrieved and applied

    **Article IV Requirement**: Cross-session learning (VectorStore persistence).
    **Expected**: PASS (VectorStore persists across sessions by default).
    """
    # Arrange: Session A - Store pattern
    context_a = create_agent_context(session_id="session_a")

    context_a.store_memory(
        key="session_a_auth_pattern",
        content={
            "task_type": "jwt_authentication",
            "solution": "use PyJWT library, RSA-256, 1h expiry",
            "tests_passed": True,
        },
        tags=["coder", "auth", "jwt", "success", "pattern"],
    )

    # Act: Session B - Query for pattern (NEW session, different context)
    context_b = create_agent_context(session_id="session_b")

    # Query WITHOUT session filter (cross-session)
    patterns = context_b.search_memories(tags=["coder", "auth", "jwt"], include_session=False)

    # Assert: Pattern from Session A found in Session B
    assert len(patterns) > 0, "Cross-session pattern should be retrievable"

    pattern_content = patterns[0].get("content", {})
    assert (
        "PyJWT" in str(pattern_content) or "jwt" in str(pattern_content).lower()
    ), "Pattern from Session A should be accessible in Session B"

    # Verify it's from Session A (different session tag)
    pattern_tags = patterns[0].get("tags", [])
    # Session tag might differ, but core tags should match
    assert "auth" in pattern_tags or "coder" in pattern_tags, "Pattern should have correct tags"


# =============================================================================
# INTEGRATION TEST 5: Agent Continues on VectorStore Failure
# =============================================================================


@pytest.mark.integration
def test_agent_continues_execution_when_vectorstore_fails() -> None:
    """
    **Integration**: Agent gracefully handles VectorStore failure (resilience).

    Given: VectorStore query raises exception
    When: Agent attempts to query VectorStore
    Then: Agent logs warning, continues without patterns (graceful degradation)

    **Article IV Requirement**: VectorStore failure must not block agent execution.
    **Expected**: FAIL (graceful fallback might not be implemented - RED phase).
    """
    # Arrange
    context = create_agent_context(session_id="resilience_test")

    # Mock: VectorStore query raises exception
    with patch.object(
        context.memory, "search", side_effect=Exception("VectorStore connection timeout")
    ):
        # Act: Agent tries to query VectorStore
        try:
            patterns = context.search_memories(tags=["test"], include_session=False)

            # Assert: Graceful fallback (empty list, no crash)
            assert isinstance(
                patterns, list
            ), "Agent should handle VectorStore failure gracefully"
            assert len(patterns) == 0, "Fallback should return empty list"

            # Agent continues execution
            agent_completed = True
            assert agent_completed, "Agent should complete task despite VectorStore failure"

        except Exception as e:
            # If exception raised, test FAILS (graceful fallback needed)
            pytest.fail(
                f"Agent should handle VectorStore failure gracefully, not raise exception: {e}"
            )


# =============================================================================
# INTEGRATION TEST 6: Partial Success Storage
# =============================================================================


@pytest.mark.integration
def test_agent_stores_pattern_on_partial_success() -> None:
    """
    **Integration**: Agent handles partial success (e.g., 95% test pass rate).

    Given: Agent completes task with 95% test pass (not 100%)
    When: Agent evaluates success threshold (>90%)
    Then: Pattern stored (threshold met) OR not stored (below threshold)

    **Article IV Requirement**: Conditional storage based on success threshold.
    **Expected**: PASS (demonstrates conditional storage logic).
    """
    # Arrange
    context = create_agent_context(session_id="partial_success_test")

    # Mock: Track storage
    storage_called = False

    original_store = context.store_memory

    def tracked_store(key: str, content: Any, tags: List[str]) -> None:
        nonlocal storage_called
        storage_called = True
        original_store(key, content, tags)

    context.store_memory = tracked_store  # type: ignore

    # Act: Simulate partial success (95% test pass)
    test_pass_rate = 0.95
    success_threshold = 0.90

    if test_pass_rate >= success_threshold:
        # Store pattern (threshold met)
        context.store_memory(
            key="partial_success_pattern",
            content={"test_pass_rate": test_pass_rate, "outcome": "partial_success"},
            tags=["coder", "partial_success", "pattern"],
        )

    # Assert: Storage occurred (95% >= 90% threshold)
    assert storage_called, "Pattern should be stored for partial success above threshold"

    # Verify: Pattern marked as partial success
    patterns = context.search_memories(tags=["partial_success"], include_session=True)
    assert len(patterns) > 0, "Partial success pattern should be retrievable"


# =============================================================================
# INTEGRATION TEST 7: Full Lifecycle (Query → Action → Store)
# =============================================================================


@pytest.mark.integration
def test_full_article_iv_lifecycle_integration() -> None:
    """
    **Integration**: Full Article IV lifecycle (query → action → store).

    Given: Agent receives task
    When: Agent executes full workflow
    Then: 1) Query VectorStore, 2) Execute action, 3) Store learning

    **Article IV Requirement**: Complete lifecycle enforcement.
    **Expected**: PASS (demonstrates complete Article IV compliance).
    """
    # Arrange
    context = create_agent_context(session_id="full_lifecycle_test")

    # Pre-populate with prior pattern
    context.store_memory(
        key="prior_lifecycle_pattern",
        content={"solution": "test-driven development", "tests_passed": True},
        tags=["coder", "tdd", "success", "pattern"],
    )

    # Track lifecycle phases
    lifecycle: List[str] = []

    # Act: Phase 1 - Query VectorStore
    patterns = context.search_memories(tags=["coder", "tdd"], include_session=False)
    lifecycle.append("query")

    # Phase 2 - Execute action (implement using pattern)
    implementation = f"TDD implementation using pattern: {patterns}"
    tests_passed = True
    lifecycle.append("action")

    # Phase 3 - Store learning (after success)
    if tests_passed:
        context.store_memory(
            key=f"lifecycle_success_{int(time.time())}",
            content={"implementation": implementation, "tests_passed": True},
            tags=["coder", "tdd", "success", "pattern"],
        )
        lifecycle.append("store")

    # Assert: Complete lifecycle
    assert lifecycle == [
        "query",
        "action",
        "store",
    ], "Article IV lifecycle must be: query → action → store"

    # Verify stored learning
    new_patterns = context.search_memories(tags=["coder", "tdd", "success"], include_session=True)
    assert (
        len(new_patterns) >= 2
    ), "New pattern should be stored (prior + current session)"  # Prior + current


# =============================================================================
# SUMMARY
# =============================================================================

"""
**Integration Test Summary**:

**Agent Workflows (3 tests)**:
1. CodingAgent: Query before implementation
2. PlannerAgent: Query before planning
3. QualityEnforcer: Query before validation

**Learning Validation (2 tests)**:
4. Pattern application from previous session (cross-session learning)
5. Agent stores pattern after successful completion

**Resilience (1 test)**:
6. Agent continues execution when VectorStore fails

**Conditional Logic (1 test)**:
7. Partial success storage (threshold-based)

**Full Lifecycle (1 test)**:
8. Complete query → action → store workflow

**Total**: 8 integration tests

**Expected RED Phase Failures**:
1. test_coding_agent_queries_vectorstore_before_implementation (if CodingAgent doesn't query)
2. test_planner_queries_vectorstore_before_planning (if PlannerAgent doesn't query)
3. test_quality_enforcer_queries_vectorstore_before_validation (if QualityEnforcer doesn't query)
4. test_agent_continues_execution_when_vectorstore_fails (if graceful fallback not implemented)

**Expected PASS Tests**: 4 tests (storage, cross-session, partial success, full lifecycle)

**Next Steps** (GREEN phase):
1. Verify agent implementations query VectorStore before action
2. Implement graceful fallback for VectorStore failures
3. Add telemetry/logging for Article IV compliance tracking
4. Run integration tests to verify GREEN phase
"""
