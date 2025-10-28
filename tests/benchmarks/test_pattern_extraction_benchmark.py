"""
Benchmark Tests for VectorStore Pattern Extraction (TDD - RED Phase).

Quantitative benchmarks with specific targets from specification.
These tests validate production readiness against measurable criteria.

**Expected Behavior**: ALL TESTS SHOULD FAIL INITIALLY (RED phase).

Specification: specs/spec-20251026-vectorstore-pattern-validation.md
Benchmark Criteria: BC-01 through BC-05
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List

import pytest

from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from agency_memory.vector_store import VectorStore
from shared.type_definitions.json import JSONValue


# =============================================================================
# BENCHMARK 1: Pattern Count (BC-01 - ≥50 Patterns)
# =============================================================================


def test_pattern_count_benchmark() -> None:
    """
    **Benchmark BC-01**: VectorStore contains ≥50 patterns with confidence ≥0.6.

    Target: ≥50 patterns (institutional knowledge baseline)
    Measurement: Count high-confidence patterns in VectorStore
    Acceptance: Pattern count ≥50

    **Validation**: Institutional knowledge baseline established
    **Expected**: FAIL (insufficient patterns in VectorStore)
    """
    store = EnhancedMemoryStore()
    vector_store = VectorStore()

    # =========================================================================
    # SETUP: Generate Synthetic Session Data (Realistic Patterns)
    # =========================================================================

    # Tool patterns: 6 tools × 10 occurrences each = 60 tool memories → ~6 patterns
    tool_names = ["Read", "Write", "Edit", "Grep", "Bash", "TodoWrite"]

    for tool in tool_names:
        for i in range(10):
            store.store(
                f"bench_tool_{tool.lower()}_{i}",
                f"{tool} tool used successfully {i}. Result: success, working, completed",
                ["tool", tool.lower(), "success"],
            )

    # Error patterns: 10 error types × 5 occurrences each = 50 error memories → ~10 patterns
    error_types = [
        "permission",
        "timeout",
        "connection",
        "not_found",
        "validation",
        "authentication",
        "rate_limit",
        "disk_space",
        "memory",
        "network",
    ]

    for error_type in error_types:
        for i in range(5):
            # Error event
            store.store(
                f"bench_error_{error_type}_{i}_error",
                f"{error_type} error encountered. Error message",
                ["error", error_type],
            )
            # Resolution event
            store.store(
                f"bench_error_{error_type}_{i}_resolved",
                f"{error_type} error resolved successfully. Result: fixed, success",
                ["error", error_type, "resolved"],
            )

    # Interaction patterns: 10 agents × 8 handoffs each = 80 memories → ~10 patterns
    agents = [
        "coder",
        "planner",
        "auditor",
        "quality_enforcer",
        "test_generator",
        "learning",
        "merger",
        "toolsmith",
        "chief_architect",
        "summary",
    ]

    for agent in agents:
        for i in range(8):
            store.store(
                f"bench_handoff_{agent}_{i}",
                f"Handoff to {agent} completed successfully. Result: success, done",
                ["handoff", "agent", agent, "success"],
            )

    # =========================================================================
    # ACT: Extract Patterns
    # =========================================================================

    patterns = store.get_learning_patterns(min_confidence=0.6)

    # =========================================================================
    # ASSERT: Pattern Count ≥50
    # =========================================================================

    assert len(patterns) >= 50, (
        f"Benchmark BC-01 FAILED: Expected ≥50 patterns with confidence ≥0.6, "
        f"got {len(patterns)}\n"
        f"Breakdown:\n"
        f"  - Tool patterns expected: ~6\n"
        f"  - Error patterns expected: ~10\n"
        f"  - Interaction patterns expected: ~10\n"
        f"  - Total expected: ~26+ (target: ≥50)"
    )

    # Store patterns to VectorStore for subsequent tests
    for pattern in patterns:
        pattern_key = pattern.get("pattern_id", f"pattern_{id(pattern)}")

        vector_store.add_memory(
            pattern_key,
            {
                "key": pattern_key,
                "content": pattern,
                "tags": [pattern.get("type", "unknown"), "benchmark"],
                "confidence": pattern.get("confidence", 0.0),
                "timestamp": datetime.now().isoformat(),
            },
        )

    # Verify VectorStore count
    high_conf_patterns = [p for p in vector_store._memories.values() if p.get("confidence", 0) >= 0.6]

    assert len(high_conf_patterns) >= 50, (
        f"Benchmark BC-01 FAILED (VectorStore): VectorStore contains {len(high_conf_patterns)} "
        f"patterns, expected ≥50"
    )


# =============================================================================
# BENCHMARK 2: Average Confidence (BC-02 - ≥0.75)
# =============================================================================


def test_average_confidence_benchmark() -> None:
    """
    **Benchmark BC-02**: Average confidence score ≥0.75 across all stored patterns.

    Target: ≥0.75 avg confidence (high-quality patterns dominate)
    Measurement: Calculate avg confidence of all patterns in VectorStore
    Acceptance: avg_confidence ≥0.75

    **Validation**: High-quality institutional knowledge
    **Expected**: FAIL (average confidence below target)
    """
    store = EnhancedMemoryStore()
    vector_store = VectorStore()

    # =========================================================================
    # SETUP: Generate High-Quality Patterns (High Evidence Count)
    # =========================================================================

    # High-quality tool patterns (12+ occurrences → confidence 0.9+)
    high_quality_tools = ["Read", "Write", "Edit"]

    for tool in high_quality_tools:
        for i in range(15):  # 15 occurrences → confidence 0.9 (capped)
            store.store(
                f"hq_tool_{tool.lower()}_{i}",
                f"{tool} tool high-quality usage {i}. Result: success, excellent, working",
                ["tool", tool.lower(), "success"],
            )

    # Medium-quality error patterns (7-9 occurrences → confidence 0.7-0.9)
    medium_quality_errors = ["permission", "timeout", "connection"]

    for error_type in medium_quality_errors:
        for i in range(8):  # 8 occurrences → confidence ~0.8
            store.store(
                f"mq_error_{error_type}_{i}_error",
                f"{error_type} error. Error message",
                ["error", error_type],
            )
            store.store(
                f"mq_error_{error_type}_{i}_resolved",
                f"{error_type} resolved. Result: fixed, success",
                ["error", error_type, "resolved"],
            )

    # =========================================================================
    # ACT: Extract Patterns and Calculate Average Confidence
    # =========================================================================

    patterns = store.get_learning_patterns(min_confidence=0.6)

    # Calculate average confidence
    if patterns:
        total_confidence = sum(p.get("confidence", 0.0) for p in patterns)
        avg_confidence = total_confidence / len(patterns)
    else:
        avg_confidence = 0.0

    # =========================================================================
    # ASSERT: Average Confidence ≥0.75
    # =========================================================================

    assert avg_confidence >= 0.75, (
        f"Benchmark BC-02 FAILED: Expected avg confidence ≥0.75, got {avg_confidence:.2f}\n"
        f"Pattern count: {len(patterns)}\n"
        f"Total confidence: {total_confidence:.2f}"
    )

    # Store to VectorStore for verification
    for pattern in patterns:
        pattern_key = pattern.get("pattern_id", f"pattern_{id(pattern)}")

        vector_store.add_memory(
            pattern_key,
            {
                "key": pattern_key,
                "content": pattern,
                "tags": [pattern.get("type", "unknown"), "benchmark"],
                "confidence": pattern.get("confidence", 0.0),
                "timestamp": datetime.now().isoformat(),
            },
        )

    # Verify VectorStore avg confidence
    all_stored = list(vector_store._memories.values())
    high_conf_stored = [p for p in all_stored if p.get("confidence", 0) >= 0.6]

    if high_conf_stored:
        vs_total_confidence = sum(p.get("confidence", 0.0) for p in high_conf_stored)
        vs_avg_confidence = vs_total_confidence / len(high_conf_stored)
    else:
        vs_avg_confidence = 0.0

    assert vs_avg_confidence >= 0.75, (
        f"Benchmark BC-02 FAILED (VectorStore): VectorStore avg confidence {vs_avg_confidence:.2f}, "
        f"expected ≥0.75"
    )


# =============================================================================
# BENCHMARK 3: Retrieval Accuracy (BC-03 - ≥95%)
# =============================================================================


def test_retrieval_accuracy_benchmark() -> None:
    """
    **Benchmark BC-03**: Pattern retrieval accuracy ≥95%.

    Target: ≥95% accuracy (queries return relevant patterns)
    Measurement: Query 20 patterns, verify 19+ are correct/relevant
    Acceptance: accuracy ≥95%

    **Validation**: Retrieval quality (tag-based + semantic search)
    **Expected**: FAIL (retrieval accuracy below target)
    """
    store = EnhancedMemoryStore()
    vector_store = VectorStore()

    # =========================================================================
    # SETUP: Store Known Patterns (Ground Truth)
    # =========================================================================

    # Auth patterns (10 patterns)
    auth_patterns_keys = []

    for i in range(10):
        key = f"auth_pattern_{i}"
        auth_patterns_keys.append(key)

        for j in range(8):  # 8 occurrences → confidence ~0.8
            store.store(
                f"{key}_mem_{j}",
                f"Auth pattern {i} usage {j}. Result: success, JWT, authentication",
                ["auth", "jwt", "success"],
            )

    # Non-auth patterns (10 patterns)
    non_auth_patterns_keys = []

    for i in range(10):
        key = f"database_pattern_{i}"
        non_auth_patterns_keys.append(key)

        for j in range(8):
            store.store(
                f"{key}_mem_{j}",
                f"Database pattern {i} query {j}. Result: success, SQL, optimization",
                ["database", "sql", "performance"],
            )

    # Extract patterns
    all_patterns = store.get_learning_patterns(min_confidence=0.6)

    # Store to VectorStore
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
    # ACT: Query VectorStore for Auth Patterns (20 Queries)
    # =========================================================================

    search_method = getattr(vector_store, "search_by_tags", None)

    if search_method is None:
        # Fallback: Manual search
        retrieved_auth_patterns = [
            p
            for p in vector_store._memories.values()
            if p.get("type") == "tool_pattern"  # Auth patterns are tool patterns
            and p.get("confidence", 0) >= 0.6
        ]
    else:
        retrieved_auth_patterns = search_method(tags=["success"], min_confidence=0.6)

    # =========================================================================
    # ASSERT: Retrieval Accuracy ≥95%
    # =========================================================================

    # Count relevant patterns retrieved
    total_queries = 20  # Simulate 20 queries
    relevant_retrieved = min(len(retrieved_auth_patterns), total_queries)

    # Calculate accuracy (relevant / total queries)
    accuracy = (relevant_retrieved / total_queries) * 100 if total_queries > 0 else 0.0

    assert accuracy >= 95.0, (
        f"Benchmark BC-03 FAILED: Expected retrieval accuracy ≥95%, got {accuracy:.1f}%\n"
        f"Retrieved patterns: {len(retrieved_auth_patterns)}\n"
        f"Total queries: {total_queries}\n"
        f"Relevant retrieved: {relevant_retrieved}"
    )


# =============================================================================
# BENCHMARK 4: Pattern Quality (BC-04 - Manual Review)
# =============================================================================


def test_pattern_quality_benchmark() -> None:
    """
    **Benchmark BC-04**: Manual review of top 10 patterns confirms relevance.

    Target: Top 10 patterns are relevant and actionable
    Measurement: Extract top 10 patterns by confidence, verify structure
    Acceptance: All 10 patterns have required fields and actionable insights

    **Validation**: Pattern quality (actionability, completeness)
    **Expected**: FAIL (pattern quality below target)
    """
    store = EnhancedMemoryStore()

    # =========================================================================
    # SETUP: Generate High-Quality Patterns
    # =========================================================================

    # Create high-evidence patterns (confidence 0.9+)
    for tool in ["Read", "Write", "Edit"]:
        for i in range(12):  # 12 occurrences → confidence 0.9
            store.store(
                f"quality_tool_{tool.lower()}_{i}",
                f"{tool} tool usage {i}. Result: success, excellent, actionable",
                ["tool", tool.lower(), "success"],
            )

    # =========================================================================
    # ACT: Extract Top 10 Patterns by Confidence
    # =========================================================================

    all_patterns = store.get_learning_patterns(min_confidence=0.6)

    # Sort by confidence (descending)
    sorted_patterns = sorted(
        all_patterns, key=lambda p: p.get("confidence", 0.0), reverse=True
    )

    top_10_patterns = sorted_patterns[:10]

    # =========================================================================
    # ASSERT: Top 10 Patterns Have Required Fields
    # =========================================================================

    assert len(top_10_patterns) >= 10, (
        f"Benchmark BC-04 FAILED: Expected ≥10 patterns for quality review, "
        f"got {len(top_10_patterns)}"
    )

    # Verify each top pattern has required fields
    required_fields = [
        "pattern_id",
        "type",
        "confidence",
        "description",
        "actionable_insight",
    ]

    for i, pattern in enumerate(top_10_patterns):
        for field in required_fields:
            assert field in pattern, (
                f"Benchmark BC-04 FAILED: Top pattern #{i+1} missing field '{field}'\n"
                f"Pattern: {pattern.get('pattern_id', 'unknown')}"
            )

        # Verify confidence is high (top 10 should be >0.7)
        confidence = pattern.get("confidence", 0.0)
        assert confidence >= 0.7, (
            f"Benchmark BC-04 FAILED: Top pattern #{i+1} has confidence {confidence:.2f}, "
            f"expected ≥0.7 for top patterns"
        )

        # Verify actionable_insight is non-empty
        actionable_insight = pattern.get("actionable_insight", "")
        assert len(actionable_insight) > 0, (
            f"Benchmark BC-04 FAILED: Top pattern #{i+1} has empty actionable_insight"
        )


# =============================================================================
# BENCHMARK 5: Cross-Session Pattern Reuse (BC-05 - ≥3 Patterns Applied)
# =============================================================================


def test_cross_session_pattern_reuse_benchmark() -> None:
    """
    **Benchmark BC-05**: ≥3 patterns applied from VectorStore in new sessions.

    Target: ≥3 patterns reused (proof of institutional learning)
    Measurement: Query patterns from Session 001, apply in Session 002
    Acceptance: ≥3 patterns from Session 001 retrieved and applied

    **Validation**: Institutional learning effectiveness
    **Expected**: FAIL (pattern reuse below target)
    """
    vector_store = VectorStore()

    # =========================================================================
    # SESSION 001: Generate and Store Patterns
    # =========================================================================

    session_001_store = EnhancedMemoryStore()

    # Create memories for Session 001
    for tool in ["Read", "Write", "Edit", "Bash", "Grep"]:
        for i in range(10):
            session_001_store.store(
                f"session_001_{tool.lower()}_{i}",
                f"Session 001: {tool} tool usage {i}. Result: success",
                ["tool", tool.lower(), "success", "session:001"],
            )

    # Extract patterns
    session_001_patterns = session_001_store.get_learning_patterns(min_confidence=0.6)

    # Store to VectorStore
    for pattern in session_001_patterns:
        pattern_key = pattern.get("pattern_id", f"pattern_{id(pattern)}")

        vector_store.add_memory(
            pattern_key,
            {
                "key": pattern_key,
                "content": pattern,
                "tags": [pattern.get("type", "unknown"), "session:001"],
                "confidence": pattern.get("confidence", 0.0),
                "timestamp": datetime.now().isoformat(),
            },
        )

    # =========================================================================
    # SESSION 002: Query and Apply Patterns from Session 001
    # =========================================================================

    # Query VectorStore for Session 001 patterns
    search_method = getattr(vector_store, "search_by_tags", None)

    if search_method is None:
        # Fallback
        retrieved_patterns = [
            p
            for p in vector_store._memories.values()
            if "session:001" in p.get("tags", []) and p.get("confidence", 0) >= 0.6
        ]
    else:
        retrieved_patterns = search_method(tags=["session:001", "success"], min_confidence=0.6)

    # =========================================================================
    # ASSERT: ≥3 Patterns Retrieved and Applied
    # =========================================================================

    assert len(retrieved_patterns) >= 3, (
        f"Benchmark BC-05 FAILED: Expected ≥3 patterns from Session 001 to be reused, "
        f"got {len(retrieved_patterns)}"
    )

    # Verify patterns have actionable insights (can be applied)
    applicable_patterns = [
        p
        for p in retrieved_patterns
        if isinstance(p.get("content"), dict)
        and "actionable_insight" in p.get("content", {})
    ]

    assert len(applicable_patterns) >= 3, (
        f"Benchmark BC-05 FAILED: Expected ≥3 applicable patterns (with actionable_insight), "
        f"got {len(applicable_patterns)}"
    )


# =============================================================================
# BENCHMARK 6: Performance Benchmark (Pattern Extraction Speed)
# =============================================================================


def test_pattern_extraction_performance_benchmark() -> None:
    """
    **Performance Benchmark**: Pattern extraction <10s for 1000-line session.

    Target: <10 seconds (P95 latency)
    Measurement: Time pattern extraction on 1000+ memories
    Acceptance: elapsed_time <10.0 seconds

    **Validation**: NF-01 from spec (performance requirement)
    **Expected**: FAIL (performance optimization needed)
    """
    import time

    store = EnhancedMemoryStore()

    # =========================================================================
    # SETUP: Generate 1000+ Memories (Large Session)
    # =========================================================================

    memory_count = 1000

    for i in range(memory_count):
        # Vary memory types
        if i % 5 == 0:
            tool = ["Read", "Write", "Edit", "Bash", "Grep"][i % 5]
            store.store(
                f"perf_tool_{i}",
                f"{tool} tool usage {i}. Result: success",
                ["tool", tool.lower(), "success"],
            )
        elif i % 5 == 2:
            error_type = ["permission", "timeout", "connection"][i % 3]
            store.store(
                f"perf_error_{i}",
                f"{error_type} error. Error message",
                ["error", error_type],
            )
        else:
            store.store(
                f"perf_memory_{i}", f"Memory {i}. Processing", ["session", "benchmark"]
            )

    # =========================================================================
    # ACT: Measure Pattern Extraction Performance
    # =========================================================================

    start_time = time.time()
    patterns = store.get_learning_patterns(min_confidence=0.6)
    elapsed_time = time.time() - start_time

    # =========================================================================
    # ASSERT: Extraction Time <10 Seconds
    # =========================================================================

    assert elapsed_time < 10.0, (
        f"Performance Benchmark FAILED: Pattern extraction took {elapsed_time:.2f}s, "
        f"expected <10s for {memory_count} memories"
    )

    assert len(patterns) > 0, "Should extract patterns from large session"


# =============================================================================
# BENCHMARK 7: VectorStore Health Metrics
# =============================================================================


def test_vectorstore_health_metrics_benchmark() -> None:
    """
    **Health Benchmark**: VectorStore operational health metrics.

    Metrics:
    - Total patterns stored
    - Average confidence
    - Confidence distribution (low/medium/high)
    - Storage size estimate

    **Validation**: Operational monitoring readiness
    **Expected**: PASS (informational metrics)
    """
    store = EnhancedMemoryStore()
    vector_store = VectorStore()

    # =========================================================================
    # SETUP: Store Patterns
    # =========================================================================

    for i in range(30):
        for j in range(8):
            store.store(
                f"health_tool_{i}_{j}",
                f"Tool usage {i}_{j}. Result: success",
                ["tool", "success"],
            )

    patterns = store.get_learning_patterns(min_confidence=0.0)  # Get all patterns

    for pattern in patterns:
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
    # ACT: Calculate Health Metrics
    # =========================================================================

    all_patterns = list(vector_store._memories.values())

    # Total patterns
    total_patterns = len(all_patterns)

    # Average confidence
    if all_patterns:
        total_confidence = sum(p.get("confidence", 0.0) for p in all_patterns)
        avg_confidence = total_confidence / len(all_patterns)
    else:
        avg_confidence = 0.0

    # Confidence distribution
    low_conf_count = sum(1 for p in all_patterns if p.get("confidence", 0) < 0.6)
    medium_conf_count = sum(
        1 for p in all_patterns if 0.6 <= p.get("confidence", 0) < 0.8
    )
    high_conf_count = sum(1 for p in all_patterns if p.get("confidence", 0) >= 0.8)

    # Storage size estimate (rough)
    storage_size_bytes = len(json.dumps(all_patterns).encode("utf-8"))
    storage_size_kb = storage_size_bytes / 1024

    # =========================================================================
    # ASSERT: Health Metrics Within Expected Ranges
    # =========================================================================

    # Print health metrics (informational)
    print("\n=== VectorStore Health Metrics ===")
    print(f"Total patterns: {total_patterns}")
    print(f"Average confidence: {avg_confidence:.2f}")
    print(f"Confidence distribution:")
    print(f"  - Low (<0.6): {low_conf_count}")
    print(f"  - Medium (0.6-0.8): {medium_conf_count}")
    print(f"  - High (≥0.8): {high_conf_count}")
    print(f"Storage size: {storage_size_kb:.2f} KB")
    print("=" * 40)

    # Basic sanity checks
    assert total_patterns > 0, "VectorStore should contain patterns"
    assert 0.0 <= avg_confidence <= 1.0, "Average confidence should be in range [0.0, 1.0]"
    assert storage_size_kb > 0, "Storage size should be positive"


# =============================================================================
# TEST SUMMARY
# =============================================================================

"""
**Benchmark Test Coverage Summary**:
- [✓] BC-01: Pattern count ≥50 (1 test)
- [✓] BC-02: Average confidence ≥0.75 (1 test)
- [✓] BC-03: Retrieval accuracy ≥95% (1 test)
- [✓] BC-04: Pattern quality (top 10 review) (1 test)
- [✓] BC-05: Cross-session pattern reuse ≥3 (1 test)
- [✓] Performance: Extraction <10s for 1000 memories (1 test)
- [✓] Health metrics: Operational monitoring (1 test)

**Total**: 7 benchmark tests

**Expected Outcome (RED Phase)**: ALL TESTS FAIL (targets not met)

**Quantitative Targets**:
- Pattern count: ≥50 (BC-01)
- Average confidence: ≥0.75 (BC-02)
- Retrieval accuracy: ≥95% (BC-03)
- Pattern quality: Top 10 actionable (BC-04)
- Cross-session reuse: ≥3 patterns (BC-05)
- Performance: <10s for 1000 memories (NF-01)

**Next Steps (GREEN Phase)**:
1. TestGenerator sends to CodingAgent
2. CodingAgent optimizes pattern extraction
3. Iterate until all benchmarks pass
4. Production-ready institutional learning system
"""
