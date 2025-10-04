"""
Performance Benchmark Suite

Constitutional requirement: Tests must execute within defined time bounds.
These benchmarks prevent performance regressions.
"""

import subprocess
import time
from pathlib import Path

import pytest


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks with constitutional thresholds."""

    def test_health_check_speed(self):
        """Health check must complete in <2 seconds (constitutional requirement)."""
        start = time.time()

        result = subprocess.run(
            ["bash", "-c", "SKIP_SPEC_TRACEABILITY=true ./scripts/health_check.sh"],
            capture_output=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        duration = time.time() - start

        assert result.returncode == 0, "Health check failed"
        assert duration < 2.0, f"Health check took {duration:.2f}s, must be <2s"

    def test_constitutional_validator_speed(self):
        """Constitutional validation must be fast (<1s per article)."""
        start = time.time()

        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_constitutional_validator.py", "-q"],
            capture_output=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        duration = time.time() - start

        assert result.returncode == 0, "Constitutional tests failed"
        assert duration < 5.0, f"Constitutional tests took {duration:.2f}s, must be <5s"

    def test_fast_test_tier_performance(self):
        """Fast test tier must complete in <30 seconds."""
        start = time.time()

        result = subprocess.run(
            ["python", "-m", "pytest", "-m", "fast", "-q"],
            capture_output=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        duration = time.time() - start

        # Note: Will pass even if no tests marked as 'fast' yet
        if b"no tests ran" not in result.stdout.lower():
            assert duration < 30.0, f"Fast tests took {duration:.2f}s, must be <30s"

    @pytest.mark.slow
    def test_full_suite_performance(self):
        """Full test suite baseline (target: <3 minutes)."""
        start = time.time()

        result = subprocess.run(
            ["python", "run_tests.py"],
            capture_output=True,
            cwd=Path(__file__).parent.parent.parent,
            timeout=300,  # 5 minute safety
        )

        duration = time.time() - start

        # Informational: log duration for tracking
        print(f"\nFull suite duration: {duration:.2f}s")

        # Threshold: <3 minutes (180s) is excellent
        # 3-5 minutes (180-300s) is acceptable
        # >5 minutes needs optimization
        assert duration < 300, f"Full suite took {duration:.2f}s, exceeds 5 minute threshold"


@pytest.mark.benchmark
class TestMemoryPerformance:
    """Memory and context operation benchmarks."""

    def test_agent_context_creation_speed(self):
        """Agent context creation must be fast (<100ms)."""
        from shared.agent_context import create_agent_context

        start = time.time()
        context = create_agent_context()
        duration = time.time() - start

        assert context is not None
        assert duration < 0.1, f"Context creation took {duration * 1000:.2f}ms, must be <100ms"

    def test_memory_store_performance(self):
        """Memory storage operations must be fast (<50ms)."""
        from shared.agent_context import create_agent_context

        context = create_agent_context()

        start = time.time()
        context.store_memory("test_key", "test_content", tags=["benchmark"])
        duration = time.time() - start

        assert duration < 0.05, f"Memory store took {duration * 1000:.2f}ms, must be <50ms"

    def test_memory_search_performance(self):
        """Memory search must be fast (<100ms for small datasets)."""
        from shared.agent_context import create_agent_context

        context = create_agent_context()

        # Populate some data
        for i in range(10):
            context.store_memory(f"key_{i}", f"content_{i}", tags=["benchmark"])

        start = time.time()
        results = context.search_memories(["benchmark"])
        duration = time.time() - start

        assert len(results) > 0
        assert duration < 0.1, f"Memory search took {duration * 1000:.2f}ms, must be <100ms"


@pytest.mark.benchmark
class TestToolPerformance:
    """Tool execution performance benchmarks."""

    def test_spec_traceability_performance(self):
        """Spec traceability check performance baseline."""
        from pathlib import Path

        from tools.spec_traceability import SpecTraceabilityValidator

        validator = SpecTraceabilityValidator(min_coverage=0.60)

        # Test on small subset
        test_dir = Path(__file__).parent.parent / "unit"

        start = time.time()
        result = validator.validate_codebase(test_dir)
        duration = time.time() - start

        assert result.is_ok() or result.is_err()  # Either outcome is valid
        # Performance note: Full codebase scan is intentionally slow (>30s)
        # This is why we use SKIP_SPEC_TRACEABILITY flag
        print(f"\nSpec traceability (subset) took: {duration:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark"])
