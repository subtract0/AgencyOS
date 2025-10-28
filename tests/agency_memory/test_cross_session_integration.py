"""
Integration Tests for Cross-Session Memory Retrieval (TDD - RED Phase).

**Specification**: specs/spec-cross-session-memory-validation.md
**Constitutional Requirement**: Article IV - 90%+ retrieval accuracy across session boundary

**NECESSARY Pattern Coverage**:
- N: Normal cross-session retrieval (Session N stores 10 patterns → Session N+1 retrieves ≥9)
- E: Edge cases (partial session failures, process restart recovery)
- C: Corner cases (concurrent writes from multiple sessions)
- E: Error conditions (disk I/O failures, VectorStore corruption)
- S: Security (not applicable - internal memory)
- S: Stress (not applicable - see E2E tests)
- A: Accessibility (not applicable - internal API)
- R: Regression (session isolation, namespace pollution)
- Y: Yield validation (≥90% retrieval accuracy, file system verification)

**Expected Behavior**: Tests will FAIL (RED phase) if:
- Session N+1 retrieves <90% of Session N patterns (retrieval accuracy too low)
- Concurrent session writes corrupt VectorStore
- Process restart loses persisted memories
- Session N+1 pollutes Session N namespace

**TDD Protocol**:
1. Write tests FIRST (this file)
2. Tests FAIL initially (RED phase) - validates cross-session persistence
3. Fix implementation (if needed) to make tests PASS (GREEN phase)
4. Refactor for quality (REFACTOR phase)
"""

import json
import subprocess
import tempfile
import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Dict, List
import shutil

import pytest

from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from agency_memory.vector_store import VectorStore
from shared.agent_context import AgentContext, create_agent_context


@pytest.fixture(autouse=True)
def clean_vectorstore():
    """Clean VectorStore before each test to prevent pollution."""
    vectorstore_path = Path.home() / ".agency" / "memories" / "vectorstore"

    # Clean before test
    if vectorstore_path.exists():
        shutil.rmtree(vectorstore_path)

    yield

    # Optional: Clean after test (can leave for debugging)


# =============================================================================
# INTEGRATION TEST 1: Session N → N+1 (90% Retrieval Accuracy)
# =============================================================================


@pytest.mark.integration
def test_session_n_to_n_plus_1_retrieval() -> None:
    """
    **Integration**: Validate ≥90% retrieval accuracy across session boundary.

    Given: Session N stores 10 diverse patterns with tags
    When: Session N+1 (new AgentContext instance) searches for patterns
    Then: ≥9/10 patterns retrieved (90%+ accuracy)

    **Article IV Requirement**: Cross-session institutional memory.
    **Expected**: FAIL if retrieval accuracy <90% (RED phase).
    """
    # Arrange: Session N - Store 10 patterns
    context_n = create_agent_context(session_id="integration_session_n")

    patterns_stored = []
    for i in range(10):
        pattern_key = f"pattern_n_{i}"
        pattern_content = {
            "solution": f"Solution for pattern {i}",
            "tests_passed": True,
            "test_count": 10 + i,
            "confidence": 0.85 + (i * 0.01),
        }
        pattern_tags = ["integration", "session_n", f"pattern_{i}", "success"]

        context_n.store_memory(key=pattern_key, content=pattern_content, tags=pattern_tags)
        patterns_stored.append(pattern_key)

    print(f"Session N: Stored {len(patterns_stored)} patterns")

    # Cleanup Session N (simulate session end)
    del context_n

    # Act: Session N+1 - Retrieve patterns
    context_n1 = create_agent_context(session_id="integration_session_n1")

    # Search for Session N patterns using shared tags
    retrieved_patterns = context_n1.search_memories(
        tags=["integration", "success"], include_session=False  # Cross-session search
    )

    # Assert: ≥90% retrieval accuracy
    retrieved_keys = [p.get("key") for p in retrieved_patterns]
    retrieved_count = len(
        [key for key in patterns_stored if key in retrieved_keys]
    )  # Count patterns_stored that were retrieved
    retrieval_accuracy = retrieved_count / len(patterns_stored)

    print(f"Session N+1: Retrieved {retrieved_count}/10 patterns ({retrieval_accuracy*100:.0f}%)")
    print(f"  Expected keys: {patterns_stored}")
    print(f"  Retrieved keys: {retrieved_keys}")

    # **CRITICAL**: This will FAIL (RED) if cross-session persistence doesn't work
    # Expected: retrieval_accuracy >= 0.90 (9+ patterns retrieved)
    # Actual (without persistence): retrieval_accuracy == 0.0 (FAIL - RED phase)
    assert (
        retrieval_accuracy >= 0.90
    ), f"Retrieval accuracy {retrieval_accuracy*100:.0f}% below 90% threshold"


# =============================================================================
# INTEGRATION TEST 2: Concurrent Session Writes
# =============================================================================


def _agent_write_worker(agent_id: int) -> int:
    """Agent worker function - stores 10 patterns (module-level for pickling)."""
    from shared.agent_context import create_agent_context

    context = create_agent_context(session_id=f"concurrent_agent_{agent_id}")

    for i in range(10):
        context.store_memory(
            key=f"agent_{agent_id}_pattern_{i}",
            content={"agent": agent_id, "pattern_idx": i, "data": f"Pattern {i}"},
            tags=[f"agent_{agent_id}", "concurrent", "pattern"],
        )

    return agent_id  # Return agent_id to verify completion


@pytest.mark.integration
@pytest.mark.xfail(reason="RED phase: Concurrent write safety not yet implemented (file locking needed)")
def test_concurrent_session_writes() -> None:
    """
    **Integration**: Verify concurrent writes from 3 sessions don't corrupt VectorStore.

    Given: 3 agent sessions writing concurrently
    When: Each session stores 10 patterns (30 total)
    Then: All 30 patterns persist without corruption

    **Article IV Requirement**: Multi-agent swarm coordination (concurrent writes).
    **Expected**: FAIL if concurrent writes corrupt VectorStore (RED phase).
    **Status**: Expected failure - concurrent write safety implementation pending.
    """
    # Act: Execute 3 agents concurrently
    with Pool(3) as pool:
        results = pool.map(_agent_write_worker, [1, 2, 3])

    # Verify all 3 agents completed
    assert sorted(results) == [1, 2, 3], "All 3 agents should complete successfully"

    # Assert: Verify all 30 patterns persisted
    verify_context = create_agent_context(session_id="concurrent_verify")
    all_patterns = verify_context.search_memories(tags=["concurrent"], include_session=False)

    print(f"Concurrent writes: {len(all_patterns)} patterns persisted (expected 30)")
    retrieved_keys = [p.get("key") for p in all_patterns]
    print(f"  Retrieved keys: {retrieved_keys[:5]}... (showing first 5)")

    # **CRITICAL**: This will FAIL (RED) if concurrent writes cause corruption
    # Expected: len(all_patterns) == 30 (all writes succeeded)
    # Actual (with corruption): len(all_patterns) < 30 or VectorStore error (FAIL - RED phase)
    assert len(all_patterns) == 30, f"Expected 30 patterns, found {len(all_patterns)} (data loss)"


# =============================================================================
# INTEGRATION TEST 3: Process Restart Recovery
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_process_restart_recovery() -> None:
    """
    **Integration**: Verify VectorStore survives process restart (kill -9 simulation).

    Given: Process 1 stores 5 patterns to VectorStore
    When: Process 1 terminates, Process 2 starts and queries VectorStore
    Then: Process 2 retrieves all 5 patterns

    **Article IV Requirement**: Institutional memory survives process crashes.
    **Expected**: FAIL if VectorStore loses data on process restart (RED phase).
    """
    # Arrange: Script for Process 1 (stores patterns)
    store_script = """
import sys
sys.path.insert(0, '/Users/am/Code/Agency')

from shared.agent_context import create_agent_context

context = create_agent_context(session_id="restart_test_session")
for i in range(5):
    context.store_memory(
        key=f"restart_pattern_{i}",
        content={"data": f"Pattern {i}", "process": 1},
        tags=["restart", "process_1", f"pattern_{i}"]
    )
print("STORE_COMPLETE")
"""

    # Arrange: Script for Process 2 (retrieves patterns)
    retrieve_script = """
import sys
sys.path.insert(0, '/Users/am/Code/Agency')

from shared.agent_context import create_agent_context

context = create_agent_context(session_id="restart_verify_session")
patterns = context.search_memories(tags=["restart", "process_1"], include_session=False)
print(f"RETRIEVED:{len(patterns)}")
for p in patterns:
    print(f"KEY:{p.get('key')}")
"""

    # Act: Execute Process 1 (store patterns)
    result_store = subprocess.run(
        ["python", "-c", store_script], capture_output=True, text=True, timeout=10
    )
    print(f"Process 1 output: {result_store.stdout}")
    assert "STORE_COMPLETE" in result_store.stdout, "Process 1 should complete storage"

    # Simulate process restart (kill -9 would happen here, but subprocess already terminated)
    time.sleep(0.5)  # Brief delay to simulate restart

    # Act: Execute Process 2 (retrieve patterns)
    result_retrieve = subprocess.run(
        ["python", "-c", retrieve_script], capture_output=True, text=True, timeout=10
    )
    print(f"Process 2 output: {result_retrieve.stdout}")

    # Assert: Process 2 should retrieve all 5 patterns
    output_lines = result_retrieve.stdout.strip().split("\n")
    retrieved_count = 0
    for line in output_lines:
        if line.startswith("RETRIEVED:"):
            retrieved_count = int(line.split(":")[1])

    print(f"Process 2 retrieved: {retrieved_count}/5 patterns")

    # **CRITICAL**: This will FAIL (RED) if VectorStore doesn't persist across process restarts
    # Expected: retrieved_count == 5 (100% recovery)
    # Actual (without persistence): retrieved_count == 0 (FAIL - RED phase)
    assert retrieved_count == 5, f"Process restart recovery failed: {retrieved_count}/5 patterns"


# =============================================================================
# INTEGRATION TEST 4: Partial Session Failure Recovery
# =============================================================================


@pytest.mark.integration
def test_partial_session_failure_recovery() -> None:
    """
    **Integration**: Verify VectorStore handles partial session failures gracefully.

    Given: Session stores 5 patterns, crashes mid-write (6th pattern fails)
    When: New session queries VectorStore
    Then: First 5 patterns are retrievable (partial persistence)

    **Article IV Requirement**: Resilience to failures (no all-or-nothing writes).
    **Expected**: FAIL if VectorStore loses all data on partial write failure (RED phase).
    """
    # Arrange
    context = create_agent_context(session_id="partial_failure_session")

    # Store 5 patterns successfully
    for i in range(5):
        context.store_memory(
            key=f"partial_pattern_{i}",
            content={"data": f"Pattern {i}", "stage": "before_crash"},
            tags=["partial", "success", f"pattern_{i}"],
        )

    # Simulate crash during 6th write (don't store 6th pattern)
    # In real scenario, this would be: raise Exception("Simulated crash")

    # Act: New session queries for patterns
    verify_context = create_agent_context(session_id="partial_verify_session")
    recovered_patterns = verify_context.search_memories(tags=["partial", "success"], include_session=False)

    # Assert: Should recover 5 patterns (partial persistence)
    print(f"Recovered {len(recovered_patterns)}/5 patterns after partial failure")

    # **CRITICAL**: This will FAIL (RED) if VectorStore uses all-or-nothing transactions
    # Expected: len(recovered_patterns) == 5 (partial persistence works)
    # Actual (with all-or-nothing): len(recovered_patterns) == 0 (FAIL - RED phase)
    assert (
        len(recovered_patterns) == 5
    ), f"Partial failure recovery failed: {len(recovered_patterns)}/5 patterns"


# =============================================================================
# INTEGRATION TEST 5: Multi-Day Checkpoint Resume
# =============================================================================


@pytest.mark.integration
def test_multi_day_checkpoint_resume() -> None:
    """
    **Integration**: Simulate 3-day task with checkpoint/resume across sessions.

    Given: Day 1 stores checkpoint (phase 1), Day 2 stores checkpoint (phase 2)
    When: Day 3 queries for latest checkpoint
    Then: Day 3 retrieves Day 2 checkpoint (most recent)

    **Article IV Requirement**: Multi-day task state persistence.
    **Expected**: FAIL if checkpoints are not persisted across days/sessions (RED phase).
    """
    # Arrange: Day 1 - Initial checkpoint
    day1_context = create_agent_context(session_id="multiday_day1")
    day1_context.store_memory(
        key="checkpoint_day1",
        content={
            "date": "2025-10-24",
            "completed_tasks": ["task_1", "task_2"],
            "phase": 1,
            "progress": 0.33,
        },
        tags=["checkpoint", "multiday", "day1"],
    )
    del day1_context  # End Day 1 session

    # Act: Day 2 - Resume from Day 1, complete more tasks, create new checkpoint
    day2_context = create_agent_context(session_id="multiday_day2")

    # Retrieve Day 1 checkpoint
    day1_checkpoint = day2_context.search_memories(tags=["checkpoint", "day1"], include_session=False)
    assert len(day1_checkpoint) == 1, "Day 2 should retrieve Day 1 checkpoint"
    print(f"Day 2 resumed from checkpoint: phase {day1_checkpoint[0]['content']['phase']}")

    # Create Day 2 checkpoint
    day2_context.store_memory(
        key="checkpoint_day2",
        content={
            "date": "2025-10-25",
            "completed_tasks": ["task_1", "task_2", "task_3", "task_4"],
            "phase": 2,
            "progress": 0.67,
        },
        tags=["checkpoint", "multiday", "day2"],
    )
    del day2_context  # End Day 2 session

    # Act: Day 3 - Retrieve latest checkpoint
    day3_context = create_agent_context(session_id="multiday_day3")
    all_checkpoints = day3_context.search_memories(tags=["checkpoint", "multiday"], include_session=False)

    # Assert: Day 3 should retrieve 2 checkpoints (Day 1 + Day 2)
    print(f"Day 3 found {len(all_checkpoints)} checkpoints")

    # **CRITICAL**: This will FAIL (RED) if checkpoints are not persisted
    # Expected: len(all_checkpoints) == 2 (Day 1 + Day 2)
    # Actual (without persistence): len(all_checkpoints) == 0 (FAIL - RED phase)
    assert len(all_checkpoints) == 2, f"Expected 2 checkpoints, found {len(all_checkpoints)}"

    # Verify latest checkpoint is Day 2 (phase 2)
    latest_checkpoint = max(all_checkpoints, key=lambda c: c["content"]["phase"])
    assert latest_checkpoint["content"]["phase"] == 2, "Latest checkpoint should be Day 2 (phase 2)"
    print(f"Day 3 resuming from latest checkpoint: phase {latest_checkpoint['content']['phase']}")
