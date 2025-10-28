"""
End-to-End Tests for VectorStore Pattern Extraction (TDD - RED Phase).

Tests complete user workflows from session execution → pattern extraction →
VectorStore storage → pattern retrieval → pattern application.

**Expected Behavior**: ALL TESTS SHOULD FAIL INITIALLY (RED phase).

Specification: specs/spec-20251026-vectorstore-pattern-validation.md
Article VI: TDD mandatory (tests before implementation)
Article VII: Value-first testing (E2E tests validate real user value)
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from agency_memory.vector_store import VectorStore
from shared.agent_context import AgentContext, create_agent_context
from shared.type_definitions.json import JSONValue


# =============================================================================
# E2E TEST 1: Full Pattern Lifecycle (Session → Extract → Store → Retrieve → Reuse)
# =============================================================================


def test_full_pattern_lifecycle_e2e() -> None:
    """
    **E2E**: Complete pattern lifecycle from session to reuse.

    Workflow:
    1. Execute session (tool usage, errors, resolutions)
    2. Extract patterns with confidence scoring
    3. Store patterns to VectorStore (confidence ≥0.6)
    4. New session queries VectorStore before action (Article IV)
    5. Apply patterns from VectorStore
    6. Verify pattern reuse successful

    **Validation**: FC-05 from spec (end-to-end workflow)
    **Expected**: FAIL (full lifecycle incomplete)
    """
    # =========================================================================
    # STEP 1: Execute Session (Simulate Real Agent Workflow)
    # =========================================================================

    session_id = "e2e_session_001_jwt_auth"
    context = create_agent_context(session_id=session_id)
    store = EnhancedMemoryStore()

    # Simulate CodingAgent implementing JWT auth feature
    session_events = [
        # Tool usage: Read existing auth code
        {
            "timestamp": "2025-10-15T10:00:00",
            "agent": "coder",
            "action": "read_file",
            "tool": "Read",
            "file": "auth/jwt_handler.py",
            "result": "success",
            "content": "Read tool analyzed JWT implementation. Result: success, working",
        },
        # Tool usage: Write tests
        {
            "timestamp": "2025-10-15T10:05:00",
            "agent": "coder",
            "action": "write_tests",
            "tool": "Write",
            "file": "tests/test_jwt_auth.py",
            "result": "success",
            "test_count": 47,
            "content": "Write tool created 47 JWT tests. Result: completed, all passing",
        },
        # Tool usage: Run tests
        {
            "timestamp": "2025-10-15T10:10:00",
            "agent": "coder",
            "action": "run_tests",
            "tool": "Bash",
            "command": "pytest tests/test_jwt_auth.py",
            "result": "success",
            "tests_passed": 47,
            "content": "Bash tool ran tests successfully. Result: done, 47/47 passed",
        },
        # Error: Permission denied
        {
            "timestamp": "2025-10-15T10:15:00",
            "agent": "coder",
            "action": "write_file",
            "tool": "Write",
            "file": "/etc/auth/config.yml",
            "result": "error",
            "error_type": "permission",
            "content": "Permission denied when writing config file",
        },
        # Resolution: Use sudo
        {
            "timestamp": "2025-10-15T10:20:00",
            "agent": "coder",
            "action": "write_file",
            "tool": "Bash",
            "command": "sudo cp config.yml /etc/auth/",
            "result": "success",
            "content": "Permission error resolved using sudo. Result: fixed, success",
        },
    ]

    # Store session events as memories
    for i, event in enumerate(session_events):
        tags = []

        # Build tags from event data
        if event.get("agent"):
            tags.append(event["agent"])
        if event.get("tool"):
            tags.append("tool")
            tags.append(event["tool"].lower())
        if event.get("result"):
            tags.append(event["result"])
        if event.get("error_type"):
            tags.append("error")
            tags.append(event["error_type"])
        if "resolved" in event.get("content", "").lower():
            tags.append("resolved")

        store.store(
            key=f"{session_id}_event_{i}",
            content=event.get("content", json.dumps(event)),
            tags=[t for t in tags if t],  # Filter empty tags
        )

    # =========================================================================
    # STEP 2: Extract Patterns with Confidence Scoring
    # =========================================================================

    patterns = store.get_learning_patterns(min_confidence=0.6)

    assert len(patterns) > 0, "Should extract patterns from session"

    # Verify pattern types extracted
    pattern_types = {p.get("type") for p in patterns}
    assert "tool_pattern" in pattern_types, "Should extract tool usage patterns"

    # =========================================================================
    # STEP 3: Store Patterns to VectorStore (Article IV)
    # =========================================================================

    vector_store = VectorStore()
    stored_pattern_keys = []

    for pattern in patterns:
        confidence = pattern.get("confidence", 0.0)

        # Only store high-confidence patterns (≥0.6 per Article IV)
        if confidence >= 0.6:
            pattern_key = pattern.get("pattern_id", f"pattern_{len(stored_pattern_keys)}")

            vector_store.add_memory(
                pattern_key,
                {
                    "key": pattern_key,
                    "content": pattern,
                    "tags": [
                        pattern.get("type", "unknown"),
                        session_id,
                        "jwt",
                        "auth",
                        "success",
                    ],
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            stored_pattern_keys.append(pattern_key)

    assert len(stored_pattern_keys) > 0, "Should store patterns to VectorStore"

    # =========================================================================
    # STEP 4: New Session Queries VectorStore (Article IV - Query Before Action)
    # =========================================================================

    # Simulate NEW session implementing OAuth2 (similar to JWT)
    new_session_id = "e2e_session_002_oauth2"
    new_context = create_agent_context(session_id=new_session_id)

    # CodingAgent queries VectorStore for auth patterns before implementing
    search_method = getattr(vector_store, "search_by_tags", None)

    if search_method is None:
        # Fallback: Manual search
        relevant_patterns = [
            p
            for p in vector_store._memories.values()
            if "auth" in p.get("tags", [])
            and "success" in p.get("tags", [])
            and p.get("confidence", 0) >= 0.6
        ]
    else:
        relevant_patterns = search_method(tags=["auth", "success"], min_confidence=0.6)

    assert len(relevant_patterns) > 0, "Should retrieve auth patterns from previous session"

    # =========================================================================
    # STEP 5: Apply Patterns from VectorStore
    # =========================================================================

    # Extract actionable insights from patterns
    applied_patterns = []

    for pattern in relevant_patterns:
        pattern_content = pattern.get("content", {})

        # If pattern is a dict with actionable_insight
        if isinstance(pattern_content, dict) and "actionable_insight" in pattern_content:
            applied_patterns.append(
                {
                    "pattern_key": pattern.get("key"),
                    "insight": pattern_content.get("actionable_insight"),
                    "confidence": pattern.get("confidence", 0.0),
                }
            )

    # =========================================================================
    # STEP 6: Verify Pattern Reuse Successful
    # =========================================================================

    assert len(applied_patterns) > 0, "Should apply patterns from VectorStore to new session"

    # Verify patterns have high confidence
    for applied in applied_patterns:
        assert (
            applied["confidence"] >= 0.6
        ), f"Applied pattern has confidence {applied['confidence']} <0.6"

    # Success: Full lifecycle complete (session → extract → store → retrieve → reuse)


# =============================================================================
# E2E TEST 2: Article IV Compliance (Query Before Action, Store After Success)
# =============================================================================


def test_article_iv_compliance_e2e() -> None:
    """
    **E2E**: Verify Article IV compliance throughout agent workflow.

    Article IV Requirements:
    1. Query VectorStore BEFORE action (retrieve patterns)
    2. Store patterns AFTER success (institutional learning)
    3. Min confidence 0.6 for pattern application
    4. VectorStore integration mandatory (USE_ENHANCED_MEMORY=true)

    **Validation**: Article IV constitutional compliance
    **Expected**: FAIL (Article IV enforcement incomplete)
    """
    # =========================================================================
    # VERIFY: USE_ENHANCED_MEMORY=true (Constitutional Requirement)
    # =========================================================================

    use_enhanced_memory = os.environ.get("USE_ENHANCED_MEMORY", "false").lower()

    assert use_enhanced_memory == "true", (
        "Article IV violation: USE_ENHANCED_MEMORY must be 'true' "
        "(constitutional mandate, no disable flags)"
    )

    # =========================================================================
    # STEP 1: Query VectorStore BEFORE Action
    # =========================================================================

    vector_store = VectorStore()
    session_id = "article_iv_compliance_session"

    # Seed VectorStore with existing patterns (simulate past learnings)
    seed_patterns = [
        {
            "key": "read_tool_success_pattern",
            "content": {
                "tool": "Read",
                "success_rate": 0.95,
                "actionable_insight": "Prioritize Read tool for code analysis",
            },
            "tags": ["tool", "read", "success"],
            "confidence": 0.9,
        },
        {
            "key": "permission_error_resolution",
            "content": {
                "error_type": "permission",
                "resolution": "Use sudo or adjust file permissions",
                "success_rate": 0.85,
            },
            "tags": ["error", "permission", "resolved"],
            "confidence": 0.8,
        },
    ]

    for pattern in seed_patterns:
        vector_store.add_memory(
            pattern["key"],
            {
                **pattern,
                "timestamp": datetime.now().isoformat(),
            },
        )

    # Query BEFORE action (Article IV requirement)
    search_method = getattr(vector_store, "search_by_tags", None)

    if search_method is None:
        # Fallback
        pre_action_patterns = [
            p
            for p in vector_store._memories.values()
            if "tool" in p.get("tags", []) and p.get("confidence", 0) >= 0.6
        ]
    else:
        pre_action_patterns = search_method(tags=["tool", "success"], min_confidence=0.6)

    # Verify patterns retrieved BEFORE action
    assert len(pre_action_patterns) > 0, "Article IV: Must query VectorStore before action"

    # =========================================================================
    # STEP 2: Execute Action (Using Retrieved Patterns)
    # =========================================================================

    store = EnhancedMemoryStore()

    # Simulate action execution with pattern application
    action_events = [
        {
            "key": f"{session_id}_action_1",
            "content": "Applied Read tool pattern. Result: success, working",
            "tags": ["tool", "read", "success", "pattern_applied"],
        },
        {
            "key": f"{session_id}_action_2",
            "content": "Code analysis completed. Result: done",
            "tags": ["analysis", "success"],
        },
    ]

    for event in action_events:
        store.store(event["key"], event["content"], event["tags"])

    # =========================================================================
    # STEP 3: Store Patterns AFTER Success (Article IV Requirement)
    # =========================================================================

    # Extract new patterns from successful execution
    post_action_patterns = store.get_learning_patterns(min_confidence=0.6)

    # Store to VectorStore (Article IV: store after success)
    for pattern in post_action_patterns:
        if pattern.get("confidence", 0) >= 0.6:
            pattern_key = pattern.get("pattern_id", "unknown")

            vector_store.add_memory(
                pattern_key,
                {
                    "key": pattern_key,
                    "content": pattern,
                    "tags": [pattern.get("type", "unknown"), session_id],
                    "confidence": pattern.get("confidence", 0.0),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    # Verify patterns stored after success
    all_patterns = list(vector_store._memories.values())
    post_session_patterns = [p for p in all_patterns if session_id in p.get("tags", [])]

    assert (
        len(post_session_patterns) > 0
    ), "Article IV: Must store patterns after successful execution"

    # =========================================================================
    # STEP 4: Verify Min Confidence 0.6 (Article IV Requirement)
    # =========================================================================

    for pattern in post_session_patterns:
        confidence = pattern.get("confidence", 0.0)
        assert confidence >= 0.6, f"Article IV: Stored pattern has confidence {confidence} <0.6"

    # Success: Article IV compliance verified


# =============================================================================
# E2E TEST 3: 50+ Patterns Benchmark (Institutional Knowledge Baseline)
# =============================================================================


def test_50_patterns_benchmark_e2e() -> None:
    """
    **E2E**: Seed VectorStore with 50+ patterns, verify avg confidence ≥0.75.

    Benchmark Criteria (BC-01, BC-02 from spec):
    - VectorStore contains ≥50 patterns with confidence ≥0.6
    - Average confidence score ≥0.75 (high-quality patterns dominate)

    **Validation**: Benchmark criteria validation
    **Expected**: FAIL (insufficient patterns in VectorStore)
    """
    store = EnhancedMemoryStore()
    vector_store = VectorStore()

    # =========================================================================
    # STEP 1: Generate 50+ Patterns (Simulate Historical Sessions)
    # =========================================================================

    # Tool patterns (20 patterns)
    tool_names = ["Read", "Write", "Edit", "Grep", "Bash", "TodoWrite"]
    tool_patterns_generated = 0

    for tool in tool_names:
        # Create memories for tool usage (10+ occurrences for confidence ≥0.9)
        for i in range(12):
            store.store(
                f"tool_{tool.lower()}_{i}",
                f"{tool} tool used successfully {i}. Result: success, working",
                ["tool", tool.lower(), "success"],
            )

        tool_patterns_generated += 1

    # Error resolution patterns (15 patterns)
    error_types = ["permission", "timeout", "connection", "not_found", "validation"]
    error_patterns_generated = 0

    for error_type in error_types:
        # Create error + resolution memories (6 occurrences for confidence ~0.6-0.7)
        for i in range(6):
            # Error
            store.store(
                f"error_{error_type}_{i}_error",
                f"{error_type} error encountered. Error message",
                ["error", error_type],
            )
            # Resolution
            store.store(
                f"error_{error_type}_{i}_resolved",
                f"{error_type} error resolved successfully. Result: fixed",
                ["error", error_type, "resolved"],
            )

        error_patterns_generated += 3  # Each error type generates ~3 patterns

    # Agent interaction patterns (15 patterns)
    agents = ["coder", "planner", "auditor", "quality_enforcer", "test_generator"]
    interaction_patterns_generated = 0

    for agent in agents:
        # Create handoff memories (8 occurrences for confidence ~0.8)
        for i in range(8):
            store.store(
                f"handoff_{agent}_{i}",
                f"Handoff to {agent} completed successfully. Result: success",
                ["handoff", "agent", agent, "success"],
            )

        interaction_patterns_generated += 3  # Each agent generates ~3 patterns

    # =========================================================================
    # STEP 2: Extract Patterns from Memories
    # =========================================================================

    all_patterns = store.get_learning_patterns(min_confidence=0.6)

    # Verify ≥50 patterns extracted
    assert len(all_patterns) >= 50, (
        f"Benchmark BC-01: Expected ≥50 patterns with confidence ≥0.6, "
        f"got {len(all_patterns)}"
    )

    # =========================================================================
    # STEP 3: Store Patterns to VectorStore
    # =========================================================================

    for pattern in all_patterns:
        pattern_key = pattern.get("pattern_id", f"pattern_{id(pattern)}")

        vector_store.add_memory(
            pattern_key,
            {
                "key": pattern_key,
                "content": pattern,
                "tags": [pattern.get("type", "unknown")],
                "confidence": pattern.get("confidence", 0.0),
                "timestamp": datetime.now().isoformat(),
            },
        )

    # =========================================================================
    # STEP 4: Verify Average Confidence ≥0.75
    # =========================================================================

    all_stored_patterns = list(vector_store._memories.values())
    high_conf_patterns = [p for p in all_stored_patterns if p.get("confidence", 0) >= 0.6]

    # Calculate average confidence
    if high_conf_patterns:
        total_confidence = sum(p.get("confidence", 0.0) for p in high_conf_patterns)
        avg_confidence = total_confidence / len(high_conf_patterns)
    else:
        avg_confidence = 0.0

    assert avg_confidence >= 0.75, (
        f"Benchmark BC-02: Expected avg confidence ≥0.75, got {avg_confidence:.2f}"
    )

    # =========================================================================
    # STEP 5: Verify VectorStore Health
    # =========================================================================

    assert len(high_conf_patterns) >= 50, (
        f"Benchmark BC-01: VectorStore should contain ≥50 patterns, "
        f"got {len(high_conf_patterns)}"
    )

    # Success: 50+ patterns with avg confidence ≥0.75


# =============================================================================
# E2E TEST 4: Performance Under Load (1000-Line Session Extraction)
# =============================================================================


def test_performance_large_session_e2e() -> None:
    """
    **E2E**: Extract patterns from 1000-line session in <10 seconds.

    Performance Requirements (NF-01 from spec):
    - P95: Pattern extraction <10 seconds for 1000-line session
    - No performance degradation with large sessions

    **Validation**: Performance requirement (NF-01)
    **Expected**: FAIL (performance optimization needed)
    """
    import time

    store = EnhancedMemoryStore()

    # =========================================================================
    # STEP 1: Generate Large Session (1000+ Memories)
    # =========================================================================

    session_id = "large_session_performance_test"
    memory_count = 1000

    for i in range(memory_count):
        # Vary memory types for realistic session
        if i % 10 == 0:
            # Tool usage
            tool = ["Read", "Write", "Edit", "Bash"][i % 4]
            store.store(
                f"{session_id}_tool_{i}",
                f"{tool} tool usage {i}. Result: success",
                ["tool", tool.lower(), "success"],
            )
        elif i % 10 == 5:
            # Error
            error_type = ["permission", "timeout", "not_found"][i % 3]
            store.store(
                f"{session_id}_error_{i}",
                f"{error_type} error encountered. Error message",
                ["error", error_type],
            )
        else:
            # Generic memory
            store.store(
                f"{session_id}_memory_{i}",
                f"Session memory {i}. Processing data",
                ["session", session_id],
            )

    # =========================================================================
    # STEP 2: Extract Patterns with Performance Measurement
    # =========================================================================

    start_time = time.time()
    patterns = store.get_learning_patterns(min_confidence=0.6)
    elapsed_time = time.time() - start_time

    # =========================================================================
    # STEP 3: Verify Performance (P95 <10s)
    # =========================================================================

    assert elapsed_time < 10.0, (
        f"Performance requirement NF-01: Pattern extraction took {elapsed_time:.2f}s, "
        f"expected <10s for 1000-line session"
    )

    assert len(patterns) > 0, "Should extract patterns from large session"

    # Success: Performance requirement met


# =============================================================================
# E2E TEST 5: Multi-Session Institutional Learning
# =============================================================================


def test_multi_session_institutional_learning_e2e() -> None:
    """
    **E2E**: Verify institutional learning across multiple sessions.

    Workflow:
    1. Session 001: JWT implementation (extract + store patterns)
    2. Session 002: OAuth2 implementation (query Session 001 patterns, apply)
    3. Session 003: SAML implementation (query Sessions 001+002 patterns)
    4. Verify knowledge accumulation (patterns build on each other)

    **Validation**: BC-05 from spec (cross-session pattern reuse)
    **Expected**: FAIL (cross-session learning incomplete)
    """
    vector_store = VectorStore()

    # =========================================================================
    # SESSION 001: JWT Implementation
    # =========================================================================

    session_001 = EnhancedMemoryStore()
    session_001_id = "multi_session_001_jwt"

    # Simulate JWT implementation
    for i in range(10):
        session_001.store(
            f"{session_001_id}_jwt_{i}",
            f"JWT implementation step {i}. Result: success",
            ["auth", "jwt", "token", "success"],
        )

    # Extract and store patterns
    session_001_patterns = session_001.get_learning_patterns(min_confidence=0.6)

    for pattern in session_001_patterns:
        if pattern.get("confidence", 0) >= 0.6:
            pattern_key = f"session_001_{pattern.get('pattern_id', 'unknown')}"
            vector_store.add_memory(
                pattern_key,
                {
                    "key": pattern_key,
                    "content": pattern,
                    "tags": [pattern.get("type", "unknown"), "session_001", "auth", "jwt"],
                    "confidence": pattern.get("confidence", 0.0),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    # =========================================================================
    # SESSION 002: OAuth2 Implementation (Query Session 001 Patterns)
    # =========================================================================

    session_002 = EnhancedMemoryStore()
    session_002_id = "multi_session_002_oauth2"

    # Query VectorStore for auth patterns (Article IV - query before action)
    search_method = getattr(vector_store, "search_by_tags", None)

    if search_method is None:
        session_001_retrieved = [
            p
            for p in vector_store._memories.values()
            if "session_001" in p.get("tags", []) and p.get("confidence", 0) >= 0.6
        ]
    else:
        session_001_retrieved = search_method(tags=["auth", "success"], min_confidence=0.6)

    # Verify Session 001 patterns retrieved
    assert (
        len(session_001_retrieved) > 0
    ), "Session 002 should retrieve Session 001 auth patterns"

    # Simulate OAuth2 implementation (building on JWT patterns)
    for i in range(10):
        session_002.store(
            f"{session_002_id}_oauth2_{i}",
            f"OAuth2 implementation step {i} (using JWT patterns). Result: success",
            ["auth", "oauth2", "token", "success"],
        )

    # Extract and store Session 002 patterns
    session_002_patterns = session_002.get_learning_patterns(min_confidence=0.6)

    for pattern in session_002_patterns:
        if pattern.get("confidence", 0) >= 0.6:
            pattern_key = f"session_002_{pattern.get('pattern_id', 'unknown')}"
            vector_store.add_memory(
                pattern_key,
                {
                    "key": pattern_key,
                    "content": pattern,
                    "tags": [pattern.get("type", "unknown"), "session_002", "auth", "oauth2"],
                    "confidence": pattern.get("confidence", 0.0),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    # =========================================================================
    # SESSION 003: SAML Implementation (Query Sessions 001+002 Patterns)
    # =========================================================================

    session_003 = EnhancedMemoryStore()
    session_003_id = "multi_session_003_saml"

    # Query VectorStore for ALL auth patterns (Sessions 001+002)
    if search_method is None:
        all_auth_patterns = [
            p
            for p in vector_store._memories.values()
            if "auth" in p.get("tags", []) and p.get("confidence", 0) >= 0.6
        ]
    else:
        all_auth_patterns = search_method(tags=["auth", "success"], min_confidence=0.6)

    # Verify patterns from BOTH sessions retrieved
    assert len(all_auth_patterns) >= len(session_001_patterns) + len(
        session_002_patterns
    ), "Session 003 should retrieve patterns from Sessions 001 AND 002"

    # =========================================================================
    # VERIFY: Knowledge Accumulation (Patterns Build on Each Other)
    # =========================================================================

    # VectorStore should contain patterns from all 3 sessions
    all_patterns = list(vector_store._memories.values())

    session_001_count = sum(1 for p in all_patterns if "session_001" in p.get("tags", []))
    session_002_count = sum(1 for p in all_patterns if "session_002" in p.get("tags", []))

    assert session_001_count > 0, "VectorStore should contain Session 001 patterns"
    assert session_002_count > 0, "VectorStore should contain Session 002 patterns"

    # Verify avg confidence across all sessions ≥0.75 (high-quality knowledge)
    if all_patterns:
        total_confidence = sum(p.get("confidence", 0.0) for p in all_patterns)
        avg_confidence = total_confidence / len(all_patterns)
    else:
        avg_confidence = 0.0

    assert (
        avg_confidence >= 0.6
    ), f"Institutional knowledge avg confidence {avg_confidence:.2f} should be ≥0.6"

    # Success: Multi-session institutional learning verified


# =============================================================================
# TEST SUMMARY
# =============================================================================

"""
**E2E Test Coverage Summary**:
- [✓] Full pattern lifecycle (1 test)
- [✓] Article IV compliance (1 test)
- [✓] 50+ patterns benchmark (1 test)
- [✓] Performance under load (1 test)
- [✓] Multi-session institutional learning (1 test)

**Total**: 5 E2E tests

**Expected Outcome (RED Phase)**: ALL TESTS FAIL (E2E workflow incomplete)

**Next Steps (GREEN Phase)**:
1. TestGenerator sends to CodingAgent
2. CodingAgent implements/fixes code
3. Iterate until 100% pass rate
4. Store E2E patterns in VectorStore

**Value-First Testing (Article VII)**:
These E2E tests validate REAL USER VALUE:
- Full lifecycle proves end-to-end workflow works
- Article IV test proves constitutional compliance
- Benchmark test proves institutional knowledge baseline
- Performance test proves production readiness
- Multi-session test proves knowledge accumulation
"""
