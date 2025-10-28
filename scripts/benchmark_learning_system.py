#!/usr/bin/env python3
"""
Benchmark script for Continuous Learning System.

Demonstrates pattern extraction performance and validates
the implementation against audit requirements.

Usage:
    python scripts/benchmark_learning_system.py
"""

import tempfile
import time

from agency_memory.learning import LearningSystem
from agency_memory.vector_store import VectorStore


def benchmark_pattern_extraction():
    """Benchmark pattern extraction performance."""
    print("=" * 60)
    print("Learning System Benchmark")
    print("=" * 60)

    # Use temporary storage to avoid pollution
    with tempfile.TemporaryDirectory() as tmpdir:
        vector_store = VectorStore(storage_path=tmpdir)

        # Store diverse memories
        print("\n1. Storing memories...")

        # 15 tool usage memories (5 tools × 3 examples)
        tools = ["Read", "Write", "Edit", "Bash", "Glob"]
        for tool in tools:
            for i in range(3):
                vector_store.store(
                    key=f"tool_{tool}_{i}",
                    content={"tool": tool, "status": "success"},
                    tags=["tool", tool, "success"],
                    confidence=0.9,
                )
        print(f"   - Stored 15 tool usage memories")

        # 10 error resolution memories
        for i in range(10):
            vector_store.store(
                key=f"error_nonetype_{i}",
                content={"error_type": "NoneType", "resolution": "added null check"},
                tags=["error", "fixed", "NoneType"],
                confidence=0.9,
            )
        print(f"   - Stored 10 error resolution memories")

        # 6 interaction memories
        for i in range(6):
            vector_store.store(
                key=f"handoff_{i}",
                content={"source_agent": "Planner", "target_agent": "Coder"},
                tags=["agent", "handoff"],
                confidence=0.9,
            )
        print(f"   - Stored 6 interaction memories")
        print(f"   - Total: 31 memories")

        # Initialize LearningSystem
        learning = LearningSystem(vector_store=vector_store, min_confidence=0.6)

        # Benchmark pattern extraction
        print("\n2. Extracting patterns...")
        start_time = time.perf_counter()
        result = learning.extract_patterns()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if result.is_err():
            print(f"   ❌ Error: {result.unwrap_err()}")
            return

        patterns = result.unwrap()

        # Display results
        print(f"   ✅ Extracted {len(patterns)} patterns in {elapsed_ms:.2f}ms")
        print(f"   - Target: <5000ms (PASSED)" if elapsed_ms < 5000 else f"   - Target: <5000ms (FAILED)")

        # Pattern breakdown
        print("\n3. Pattern Breakdown:")
        tool_patterns = [p for p in patterns if p.pattern_type == "tool"]
        error_patterns = [p for p in patterns if p.pattern_type == "error"]
        interaction_patterns = [p for p in patterns if p.pattern_type == "interaction"]

        print(f"   - Tool patterns: {len(tool_patterns)}")
        for pattern in tool_patterns:
            print(f"     • {pattern.description} (confidence: {pattern.confidence:.2f}, evidence: {pattern.evidence_count})")

        print(f"   - Error patterns: {len(error_patterns)}")
        for pattern in error_patterns:
            print(f"     • {pattern.description} (confidence: {pattern.confidence:.2f}, evidence: {pattern.evidence_count})")

        print(f"   - Interaction patterns: {len(interaction_patterns)}")
        for pattern in interaction_patterns:
            print(f"     • {pattern.description} (confidence: {pattern.confidence:.2f}, evidence: {pattern.evidence_count})")

        # Statistics
        print("\n4. Pattern Statistics:")
        stats = learning.get_pattern_statistics()
        print(f"   - Total patterns: {stats['total_patterns']}")
        print(f"   - Average confidence: {stats['avg_confidence']:.2f}")
        print(f"   - High confidence (≥0.9): {stats['high_confidence_count']}")

        # Confidence calculation examples
        print("\n5. Confidence Calculation Examples:")
        conf_recent = learning.calculate_pattern_confidence(
            evidence_count=3, recency_days=0
        )
        print(f"   - Recent pattern (3 examples, today): {conf_recent:.2f}")

        conf_old = learning.calculate_pattern_confidence(
            evidence_count=3, recency_days=90
        )
        print(f"   - Old pattern (3 examples, 90 days): {conf_old:.2f}")

        conf_inconsistent = learning.calculate_pattern_confidence(
            evidence_count=3, consistency_score=0.5
        )
        print(f"   - Inconsistent pattern (3 examples, 50% consistency): {conf_inconsistent:.2f}")

        # Auto-extraction trigger
        print("\n6. Auto-Extraction Trigger:")
        print(f"   - Trigger threshold: {learning.auto_extraction_trigger} memories")
        print(f"   - Current memory count: 31")
        print(f"   - Should trigger: {learning.should_trigger_extraction()}")

        print("\n" + "=" * 60)
        print("Benchmark Complete ✅")
        print("=" * 60)


if __name__ == "__main__":
    benchmark_pattern_extraction()
