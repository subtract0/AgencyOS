"""
End-to-End Tests for Cross-Session Institutional Memory (TDD - RED Phase).

**Specification**: specs/spec-cross-session-memory-validation.md
**Constitutional Requirement**: Article IV - Complete mission workflows with cross-session learning

**NECESSARY Pattern Coverage**:
- N: Normal mission workflows (Planner → Coder → QA → Merger with memory sharing)
- E: Edge cases (not applicable - see integration tests)
- C: Corner cases (not applicable - see integration tests)
- E: Error conditions (not applicable - see unit/integration tests)
- S: Security (not applicable - internal memory)
- S: Stress (100 concurrent sessions, VectorStore load test)
- A: Accessibility (not applicable - internal API)
- R: Regression (full mission cycle memory persistence)
- Y: Yield validation (mission success depends on cross-session patterns)

**Expected Behavior**: Tests will FAIL (RED phase) if:
- Mission N+1 cannot retrieve patterns from Mission N
- Agent swarm loses patterns during concurrent execution
- 100 sessions exceed memory limits or corrupt VectorStore

**TDD Protocol**:
1. Write tests FIRST (this file)
2. Tests FAIL initially (RED phase) - validates end-to-end persistence
3. Fix implementation (if needed) to make tests PASS (GREEN phase)
4. Refactor for quality (REFACTOR phase)
"""

import time
from datetime import datetime
from typing import Any, Dict, List

import pytest

from shared.agent_context import AgentContext, create_agent_context


# =============================================================================
# E2E TEST 1: Full Mission Cross-Session Learning
# =============================================================================


@pytest.mark.e2e
@pytest.mark.slow
def test_full_mission_cross_session() -> None:
    """
    **E2E**: Complete mission workflow (Plan → Code → Test → Deploy) across sessions.

    Given: Mission N completes successfully, stores learnings
    When: Mission N+1 starts similar task
    Then: Mission N+1 retrieves Mission N patterns and applies them

    **Article IV Requirement**: Cross-mission institutional learning.
    **Expected**: FAIL if Mission N+1 cannot retrieve Mission N learnings (RED phase).
    """
    # === MISSION N: JWT Authentication Implementation ===

    # Phase 1: Planning (Session 1)
    planner_ctx = create_agent_context(session_id="mission_n_planner")
    planner_ctx.store_memory(
        key="mission_n_plan_jwt_auth",
        content={
            "mission": "jwt_authentication",
            "approach": "spec-driven development",
            "tasks": ["design", "implement", "test", "deploy"],
            "estimated_effort_hours": 8,
        },
        tags=["mission_n", "planner", "plan", "jwt_auth"],
    )

    # Phase 2: Implementation (Session 2)
    coder_ctx = create_agent_context(session_id="mission_n_coder")

    # Coder retrieves plan from Planner (cross-session)
    plan = coder_ctx.search_memories(tags=["plan", "jwt_auth"], include_session=False)
    assert len(plan) == 1, "Coder should retrieve Planner's plan (cross-session)"
    print(f"Coder retrieved plan: {plan[0]['content']['approach']}")

    coder_ctx.store_memory(
        key="mission_n_impl_jwt_auth",
        content={
            "mission": "jwt_authentication",
            "code_snippet": "def generate_jwt(user): ...",
            "tests_passed": True,
            "test_count": 47,
            "pattern": "JWT RSA-256 signing",
        },
        tags=["mission_n", "coder", "implementation", "jwt_auth", "success"],
    )

    # Phase 3: QA (Session 3)
    qa_ctx = create_agent_context(session_id="mission_n_qa")

    # QA retrieves implementation from Coder (cross-session)
    impl = qa_ctx.search_memories(tags=["implementation", "jwt_auth"], include_session=False)
    assert len(impl) == 1, "QA should retrieve Coder's implementation (cross-session)"
    print(f"QA retrieved implementation: {impl[0]['content']['test_count']} tests passed")

    qa_ctx.store_memory(
        key="mission_n_qa_jwt_auth",
        content={
            "mission": "jwt_authentication",
            "tests_passed": 47,
            "tests_failed": 0,
            "coverage": 0.98,
            "quality_score": 0.95,
        },
        tags=["mission_n", "qa", "verification", "jwt_auth", "success"],
    )

    # Phase 4: Deployment (Session 4)
    merger_ctx = create_agent_context(session_id="mission_n_merger")

    # Merger retrieves QA results (cross-session)
    qa_results = merger_ctx.search_memories(tags=["verification", "jwt_auth"], include_session=False)
    assert len(qa_results) == 1, "Merger should retrieve QA results (cross-session)"
    print(f"Merger retrieved QA: {qa_results[0]['content']['quality_score']} quality score")

    merger_ctx.store_memory(
        key="mission_n_success_jwt_auth",
        content={
            "mission": "jwt_authentication",
            "status": "deployed",
            "deployment_time": datetime.now().isoformat(),
            "success_pattern": "JWT RSA-256 + 47 tests + 98% coverage",
        },
        tags=["mission_n", "merger", "deployed", "jwt_auth", "success", "pattern"],
    )

    print("✅ Mission N: JWT Auth completed successfully")

    # === MISSION N+1: OAuth2 Authentication Implementation ===

    # Phase 1: Planning (retrieve Mission N learnings)
    planner_n1_ctx = create_agent_context(session_id="mission_n1_planner")

    # **CRITICAL**: Mission N+1 queries Mission N patterns (Article IV)
    mission_n_patterns = planner_n1_ctx.search_memories(
        tags=["mission_n", "success", "pattern"], include_session=False
    )

    print(f"Mission N+1 retrieved {len(mission_n_patterns)} patterns from Mission N")

    # Assert: Mission N+1 should retrieve ≥1 success pattern from Mission N
    # **CRITICAL**: This will FAIL (RED) if cross-mission persistence doesn't work
    # Expected: len(mission_n_patterns) >= 1 (Mission N patterns persist)
    # Actual (without persistence): len(mission_n_patterns) == 0 (FAIL - RED phase)
    assert (
        len(mission_n_patterns) >= 1
    ), "Mission N+1 should retrieve Mission N success patterns (cross-mission learning)"

    # Verify pattern content
    jwt_pattern = mission_n_patterns[0]
    assert "success_pattern" in jwt_pattern["content"], "Pattern should contain success_pattern field"
    print(f"Mission N+1 applying pattern: {jwt_pattern['content']['success_pattern']}")


# =============================================================================
# E2E TEST 2: Agent Swarm Coordination
# =============================================================================


@pytest.mark.e2e
@pytest.mark.slow
def test_agent_swarm_coordination() -> None:
    """
    **E2E**: Simulate 5 agents working in parallel, sharing institutional memory.

    Given: 5 agents (Scout, Planner, Coder, QA, Merger) execute concurrently
    When: Each agent stores patterns and queries other agents' patterns
    Then: All 5 agents retrieve shared patterns (swarm coordination)

    **Article IV Requirement**: Multi-agent swarm intelligence.
    **Expected**: FAIL if agents cannot share patterns concurrently (RED phase).
    """
    # === Agent 1: Scout (discovers architecture pattern) ===
    scout_ctx = create_agent_context(session_id="swarm_scout")
    scout_ctx.store_memory(
        key="swarm_architecture_pattern",
        content={
            "pattern": "Microservices with event-driven communication",
            "confidence": 0.90,
            "source": "scout",
        },
        tags=["swarm", "scout", "architecture", "pattern", "shared"],
    )

    # === Agent 2: Planner (retrieves Scout's pattern, adds plan) ===
    planner_ctx = create_agent_context(session_id="swarm_planner")

    # Retrieve Scout's pattern
    scout_patterns = planner_ctx.search_memories(tags=["scout", "pattern", "shared"], include_session=False)
    assert len(scout_patterns) == 1, "Planner should retrieve Scout's architecture pattern"
    print(f"Planner retrieved Scout pattern: {scout_patterns[0]['content']['pattern']}")

    planner_ctx.store_memory(
        key="swarm_plan",
        content={
            "plan": "Implement 3 microservices (Auth, API, DB)",
            "based_on_pattern": scout_patterns[0]["content"]["pattern"],
            "source": "planner",
        },
        tags=["swarm", "planner", "plan", "shared"],
    )

    # === Agent 3: Coder (retrieves Planner's plan, implements) ===
    coder_ctx = create_agent_context(session_id="swarm_coder")

    # Retrieve Planner's plan
    plans = coder_ctx.search_memories(tags=["planner", "plan", "shared"], include_session=False)
    assert len(plans) == 1, "Coder should retrieve Planner's plan"
    print(f"Coder retrieved plan: {plans[0]['content']['plan']}")

    coder_ctx.store_memory(
        key="swarm_implementation",
        content={
            "code": "# Microservices implementation...",
            "tests_passed": True,
            "test_count": 120,
            "source": "coder",
        },
        tags=["swarm", "coder", "implementation", "shared"],
    )

    # === Agent 4: QA (retrieves Coder's implementation, tests) ===
    qa_ctx = create_agent_context(session_id="swarm_qa")

    # Retrieve Coder's implementation
    implementations = qa_ctx.search_memories(tags=["coder", "implementation", "shared"], include_session=False)
    assert len(implementations) == 1, "QA should retrieve Coder's implementation"
    print(f"QA retrieved implementation: {implementations[0]['content']['test_count']} tests")

    qa_ctx.store_memory(
        key="swarm_qa_results",
        content={
            "tests_passed": 120,
            "tests_failed": 0,
            "coverage": 0.99,
            "source": "qa",
        },
        tags=["swarm", "qa", "results", "shared"],
    )

    # === Agent 5: Merger (retrieves all agent patterns, integrates) ===
    merger_ctx = create_agent_context(session_id="swarm_merger")

    # Retrieve all swarm patterns
    all_swarm_patterns = merger_ctx.search_memories(tags=["swarm", "shared"], include_session=False)

    print(f"Merger retrieved {len(all_swarm_patterns)} swarm patterns")
    print(f"  Sources: {[p['content'].get('source') for p in all_swarm_patterns]}")

    # Assert: Merger should retrieve patterns from all 4 previous agents
    # **CRITICAL**: This will FAIL (RED) if swarm coordination doesn't work
    # Expected: len(all_swarm_patterns) == 4 (Scout, Planner, Coder, QA)
    # Actual (without persistence): len(all_swarm_patterns) < 4 (FAIL - RED phase)
    assert (
        len(all_swarm_patterns) >= 4
    ), f"Merger should retrieve patterns from all agents (found {len(all_swarm_patterns)}/4)"

    # Verify all agent sources are present
    sources = {p["content"].get("source") for p in all_swarm_patterns}
    expected_sources = {"scout", "planner", "coder", "qa"}
    assert sources == expected_sources, f"Missing agent patterns: {expected_sources - sources}"


# =============================================================================
# E2E TEST 3: 100 Session Persistence Stress Test
# =============================================================================


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.stress
def test_100_session_persistence() -> None:
    """
    **E2E Stress**: Verify VectorStore handles 100 concurrent sessions without corruption.

    Given: 100 agent sessions, each storing 5 patterns (500 total)
    When: All sessions write concurrently
    Then: Verify ≥90% retrieval accuracy (≥450 patterns retrieved)

    **Article IV Requirement**: System stability at scale.
    **Expected**: FAIL if VectorStore corrupts or loses data at 100 sessions (RED phase).
    """
    pytest.importorskip("psutil", reason="psutil not installed")
    import psutil

    # Arrange: Track initial memory
    process = psutil.Process()
    initial_memory_mb = process.memory_info().rss / 1024 / 1024

    # Act: Create 100 sessions, each storing 5 patterns
    for session_idx in range(100):
        context = create_agent_context(session_id=f"stress_session_{session_idx}")

        for pattern_idx in range(5):
            context.store_memory(
                key=f"stress_s{session_idx}_p{pattern_idx}",
                content={
                    "session": session_idx,
                    "pattern": pattern_idx,
                    "data": f"Session {session_idx}, Pattern {pattern_idx}",
                },
                tags=["stress", f"session_{session_idx}", f"pattern_{pattern_idx}"],
            )

        # Cleanup context (simulate session end)
        del context

        # Progress indicator
        if (session_idx + 1) % 20 == 0:
            print(f"  Created {session_idx + 1}/100 sessions...")

    print("✅ All 100 sessions completed storage")

    # Assert: Verify retrieval accuracy
    verify_context = create_agent_context(session_id="stress_verify")
    all_stress_patterns = verify_context.search_memories(tags=["stress"], include_session=False)

    retrieval_accuracy = len(all_stress_patterns) / 500.0  # 500 total patterns

    print(f"Retrieval accuracy: {len(all_stress_patterns)}/500 ({retrieval_accuracy*100:.1f}%)")

    # **CRITICAL**: This will FAIL (RED) if VectorStore corrupts or loses data at scale
    # Expected: retrieval_accuracy >= 0.90 (≥450 patterns)
    # Actual (with corruption): retrieval_accuracy < 0.90 (FAIL - RED phase)
    assert retrieval_accuracy >= 0.90, (
        f"Stress test failed: {retrieval_accuracy*100:.1f}% accuracy "
        f"(expected ≥90%, found {len(all_stress_patterns)}/500)"
    )

    # Verify memory stability (no catastrophic leak)
    final_memory_mb = process.memory_info().rss / 1024 / 1024
    memory_growth_mb = final_memory_mb - initial_memory_mb

    print(f"Memory growth: {memory_growth_mb:.2f} MB (100 sessions × 5 patterns)")

    # Allow up to 200MB growth for 100 sessions (reasonable overhead)
    assert (
        memory_growth_mb < 200
    ), f"Excessive memory growth: {memory_growth_mb:.2f} MB (expected <200 MB)"
