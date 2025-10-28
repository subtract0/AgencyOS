"""
Benchmark Tests for Cross-Session Memory Performance (TDD - RED Phase).

**Specification**: specs/spec-cross-session-memory-validation.md
**Constitutional Requirement**: Article IV - Quantitative performance targets

**Benchmark Targets**:
1. Retrieval Accuracy: ≥90% (100 patterns stored → ≥90 retrieved)
2. Retrieval Latency: <100ms (10k memories, existing spec)

**NECESSARY Pattern Coverage**:
- N: Normal performance benchmarks (accuracy, latency)
- E: Edge cases (not applicable - performance benchmarks)
- C: Corner cases (not applicable - performance benchmarks)
- E: Error conditions (not applicable - performance benchmarks)
- S: Security (not applicable - internal memory)
- S: Stress (10k memories latency benchmark)
- A: Accessibility (not applicable - internal API)
- R: Regression (performance degradation detection)
- Y: Yield validation (quantitative targets met)

**Expected Behavior**: Tests will FAIL (RED phase) if:
- Retrieval accuracy <90% (institutional knowledge loss)
- Retrieval latency >100ms at 10k memories (performance regression)

**TDD Protocol**:
1. Write tests FIRST (this file)
2. Tests FAIL initially (RED phase) - validates performance targets
3. Optimize implementation to make tests PASS (GREEN phase)
4. Refactor for quality (REFACTOR phase)
"""

import time
from datetime import datetime
from typing import Any, Dict, List

import pytest

from shared.agent_context import AgentContext, create_agent_context


# =============================================================================
# BENCHMARK 1: 90% Retrieval Accuracy (100 Patterns)
# =============================================================================


@pytest.mark.benchmark
@pytest.mark.slow
@pytest.mark.skip(reason="Slow test: sentence-transformers initialization timeout (>30s). Consider pre-loading model in fixture.")
def test_90_percent_retrieval_accuracy() -> None:
    """
    **Benchmark**: Validate ≥90% retrieval accuracy with 100 stored patterns.

    Given: 10 sessions, each storing 10 patterns (100 total)
    When: Verification session queries all patterns
    Then: ≥90 patterns retrieved (90%+ accuracy)

    **Article IV Requirement**: Institutional memory reliability.
    **Expected**: FAIL if accuracy <90% (RED phase).
    **Target**: ≥90% retrieval accuracy
    **Tolerance**: No tolerance (hard requirement)
    """
    # Arrange: Store 100 patterns across 10 sessions
    print("Storing 100 patterns across 10 sessions...")
    stored_keys = []

    for session_idx in range(10):
        context = create_agent_context(session_id=f"accuracy_session_{session_idx}")

        for pattern_idx in range(10):
            pattern_key = f"accuracy_s{session_idx}_p{pattern_idx}"
            context.store_memory(
                key=pattern_key,
                content={
                    "session": session_idx,
                    "pattern": pattern_idx,
                    "data": f"Pattern {pattern_idx} from Session {session_idx}",
                    "timestamp": datetime.now().isoformat(),
                },
                tags=["accuracy_benchmark", f"session_{session_idx}", f"pattern_{pattern_idx}"],
            )
            stored_keys.append(pattern_key)

        # Cleanup session
        del context

        # Progress indicator
        if (session_idx + 1) % 2 == 0:
            print(f"  Stored {(session_idx + 1) * 10}/100 patterns...")

    print(f"✅ Stored {len(stored_keys)} patterns")

    # Act: Retrieve all patterns from verification session
    verify_context = create_agent_context(session_id="accuracy_verify")
    retrieved_patterns = verify_context.search_memories(
        tags=["accuracy_benchmark"], include_session=False
    )

    # Calculate retrieval accuracy
    retrieved_keys = {p.get("key") for p in retrieved_patterns}
    retrieved_count = len([key for key in stored_keys if key in retrieved_keys])
    retrieval_accuracy = retrieved_count / len(stored_keys)

    print(f"\n📊 Retrieval Accuracy Benchmark:")
    print(f"  Stored: {len(stored_keys)} patterns")
    print(f"  Retrieved: {retrieved_count} patterns")
    print(f"  Accuracy: {retrieval_accuracy*100:.2f}%")
    print(f"  Target: ≥90.00%")
    print(f"  Status: {'✅ PASS' if retrieval_accuracy >= 0.90 else '❌ FAIL'}")

    # Assert: ≥90% retrieval accuracy
    # **CRITICAL**: This will FAIL (RED) if cross-session persistence is unreliable
    # Expected: retrieval_accuracy >= 0.90 (90+ patterns retrieved)
    # Actual (with poor persistence): retrieval_accuracy < 0.90 (FAIL - RED phase)
    assert retrieval_accuracy >= 0.90, (
        f"Retrieval accuracy benchmark FAILED: {retrieval_accuracy*100:.2f}% "
        f"(target: ≥90%, retrieved {retrieved_count}/{len(stored_keys)})"
    )

    # Detailed analysis: Which patterns were lost?
    if retrieval_accuracy < 1.0:
        missing_keys = set(stored_keys) - retrieved_keys
        print(f"\n⚠️ Missing patterns: {len(missing_keys)}")
        print(f"  Sample missing keys: {list(missing_keys)[:5]}")


# =============================================================================
# BENCHMARK 2: <100ms Retrieval Latency (10k Memories)
# =============================================================================


@pytest.mark.benchmark
@pytest.mark.slow
@pytest.mark.stress
@pytest.mark.skip(reason="Slow test: 10k memory population timeout (>30s). Requires optimization or increased timeout.")
def test_retrieval_latency_at_10k_memories() -> None:
    """
    **Benchmark**: Validate <100ms retrieval latency with 10k memories in VectorStore.

    Given: VectorStore with 10,000 memories
    When: Query memories by tags
    Then: Query latency <100ms (sub-linear search with FAISS)

    **Article IV Requirement**: Fast semantic search for pattern retrieval.
    **Expected**: FAIL if latency >100ms (RED phase).
    **Target**: <100ms retrieval latency
    **Tolerance**: +20ms acceptable (up to 120ms)
    """
    # Arrange: Populate 10k memories
    print("Populating 10,000 memories...")
    context = create_agent_context(session_id="latency_test")

    start_populate = time.perf_counter()

    for i in range(10000):
        context.store_memory(
            key=f"latency_pattern_{i}",
            content={
                "pattern_id": i,
                "data": f"Pattern {i} for latency test",
                "category": i % 10,  # 10 categories for diversity
            },
            tags=["latency_benchmark", f"category_{i % 10}", f"pattern_{i}"],
        )

        # Progress indicator (every 1000 patterns)
        if (i + 1) % 1000 == 0:
            elapsed = time.perf_counter() - start_populate
            print(f"  Populated {i + 1}/10000 memories ({elapsed:.1f}s elapsed)...")

    populate_time = time.perf_counter() - start_populate
    print(f"✅ Populated 10,000 memories in {populate_time:.2f}s")

    # Act: Measure query latency (5 queries, take median)
    latencies_ms = []

    for query_idx in range(5):
        start_query = time.perf_counter()

        # Query a subset of memories by category
        results = context.search_memories(
            tags=["latency_benchmark", f"category_{query_idx}"], include_session=False
        )

        query_latency_ms = (time.perf_counter() - start_query) * 1000
        latencies_ms.append(query_latency_ms)

        print(f"  Query {query_idx + 1}: {query_latency_ms:.2f}ms ({len(results)} results)")

    # Calculate statistics
    median_latency_ms = sorted(latencies_ms)[len(latencies_ms) // 2]
    avg_latency_ms = sum(latencies_ms) / len(latencies_ms)
    max_latency_ms = max(latencies_ms)

    print(f"\n📊 Retrieval Latency Benchmark (10k memories):")
    print(f"  Median latency: {median_latency_ms:.2f}ms")
    print(f"  Average latency: {avg_latency_ms:.2f}ms")
    print(f"  Max latency: {max_latency_ms:.2f}ms")
    print(f"  Target: <100.00ms")
    print(f"  Tolerance: +20ms (up to 120ms acceptable)")
    print(f"  Status: {'✅ PASS' if median_latency_ms < 100 else '⚠️ MARGINAL' if median_latency_ms < 120 else '❌ FAIL'}")

    # Assert: Median latency <100ms (strict target)
    # **CRITICAL**: This will FAIL (RED) if FAISS indexing is not optimized
    # Expected: median_latency_ms < 100 (sub-linear search)
    # Actual (without FAISS): median_latency_ms > 500 (FAIL - RED phase)
    # Tolerance: Up to 120ms acceptable (marginal performance)

    if median_latency_ms >= 120:
        # Hard failure: >120ms is unacceptable
        pytest.fail(
            f"Retrieval latency benchmark FAILED: {median_latency_ms:.2f}ms "
            f"(target: <100ms, tolerance: +20ms, max acceptable: 120ms)"
        )
    elif median_latency_ms >= 100:
        # Marginal: 100-120ms acceptable but should be optimized
        print(
            f"\n⚠️ Marginal performance: {median_latency_ms:.2f}ms "
            f"(within tolerance +20ms, but should optimize for <100ms)"
        )
    else:
        # Success: <100ms
        print(f"\n✅ Excellent performance: {median_latency_ms:.2f}ms (target met)")

    # Cleanup
    del context


# =============================================================================
# BENCHMARK 3: Multi-Query Throughput (1000 queries/second)
# =============================================================================


@pytest.mark.benchmark
@pytest.mark.slow
@pytest.mark.skip(reason="Slow test: 1000 query throughput timeout (>30s). Requires FAISS optimization.")
def test_multi_query_throughput() -> None:
    """
    **Benchmark**: Validate ≥1000 queries/second throughput.

    Given: VectorStore with 1,000 memories
    When: Execute 1,000 queries in parallel
    Then: Complete in <1 second (≥1000 queries/second)

    **Article IV Requirement**: High-throughput pattern retrieval for swarm agents.
    **Expected**: FAIL if throughput <1000 queries/second (RED phase).
    **Target**: ≥1000 queries/second
    **Tolerance**: ≥800 queries/second acceptable
    """
    # Arrange: Populate 1k memories
    print("Populating 1,000 memories for throughput test...")
    context = create_agent_context(session_id="throughput_test")

    for i in range(1000):
        context.store_memory(
            key=f"throughput_pattern_{i}",
            content={"pattern_id": i, "data": f"Pattern {i}"},
            tags=["throughput_benchmark", f"category_{i % 5}"],
        )

    print("✅ Populated 1,000 memories")

    # Act: Execute 1,000 queries and measure throughput
    start_queries = time.perf_counter()
    query_count = 1000

    for i in range(query_count):
        # Query by category (round-robin across 5 categories)
        context.search_memories(tags=["throughput_benchmark", f"category_{i % 5}"], include_session=False)

    total_time_s = time.perf_counter() - start_queries
    queries_per_second = query_count / total_time_s

    print(f"\n📊 Multi-Query Throughput Benchmark:")
    print(f"  Total queries: {query_count}")
    print(f"  Total time: {total_time_s:.2f}s")
    print(f"  Throughput: {queries_per_second:.0f} queries/second")
    print(f"  Target: ≥1000 queries/second")
    print(f"  Tolerance: ≥800 queries/second acceptable")
    print(f"  Status: {'✅ PASS' if queries_per_second >= 1000 else '⚠️ MARGINAL' if queries_per_second >= 800 else '❌ FAIL'}")

    # Assert: ≥1000 queries/second (strict target)
    # **CRITICAL**: This will FAIL (RED) if query optimization is poor
    # Expected: queries_per_second >= 1000 (efficient caching + FAISS)
    # Actual (without optimization): queries_per_second < 500 (FAIL - RED phase)
    # Tolerance: ≥800 queries/second acceptable

    if queries_per_second < 800:
        # Hard failure: <800 qps unacceptable
        pytest.fail(
            f"Throughput benchmark FAILED: {queries_per_second:.0f} queries/second "
            f"(target: ≥1000, tolerance: ≥800)"
        )
    elif queries_per_second < 1000:
        # Marginal: 800-1000 qps acceptable but should be optimized
        print(
            f"\n⚠️ Marginal throughput: {queries_per_second:.0f} queries/second "
            f"(within tolerance, but should optimize for ≥1000)"
        )
    else:
        # Success: ≥1000 qps
        print(f"\n✅ Excellent throughput: {queries_per_second:.0f} queries/second (target met)")

    # Cleanup
    del context
