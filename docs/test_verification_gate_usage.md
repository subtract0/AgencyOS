# Test Verification Gate Usage Guide

## Overview

The `TestVerificationGate` enforces constitutional requirements for test execution:

- **Article I**: Complete context before action (retry with 2x, 3x, 10x timeout)
- **Article II**: 100% pass requirement (zero failures allowed)
- **Article III**: Automated enforcement (no manual overrides)
- **Article IV**: Store verification patterns for learning

## Basic Usage

### Quick Verification (Convenience Function)

```python
import asyncio
from tools.orchestrator import verify_tests

async def main():
    # Verify all tests pass
    result = await verify_tests("all")

    if result.is_ok():
        test_results = result.unwrap()
        print(test_results.get_summary())
        # Output: ✅ PASS - 1725 tests: 1725 passed (45.67s, 10 workers)
    else:
        error = result.unwrap_err()
        print(f"❌ Tests failed: {error.message}")
        # Output: ❌ Tests failed: Article II violation: 5 tests failed (100% pass required)

asyncio.run(main())
```

### Full Gate Control

```python
from pathlib import Path
from tools.orchestrator import TestVerificationGate

# Initialize gate
gate = TestVerificationGate(project_root=Path("/Users/am/Code/Agency"))

# Verify with specific mode
result = await gate.verify(mode="unit")  # Options: "all", "unit", "fast"

if result.is_ok():
    results = result.unwrap()

    # Check constitutional compliance
    assert results.is_constitutional()  # True if 100% pass rate

    # Access metrics
    print(f"Passed: {results.passed}")
    print(f"Failed: {results.failed}")
    print(f"Duration: {results.duration}s")
    print(f"Workers: {results.worker_count}")

    # Get human-readable summary
    print(results.get_summary())
else:
    error = result.unwrap_err()
    print(f"Reason: {error.reason}")  # "timeout", "failures", "no_tests_run", etc.
    print(f"Message: {error.message}")
    print(f"Failed tests: {error.failed_tests}")
```

## Constitutional Enforcement

### Article I: Retry on Timeout

The gate automatically retries with exponential backoff on timeouts:

```python
# First attempt: 600s (10 minutes)
# Second attempt: 1200s (20 minutes)  - 2x multiplier
# Third attempt: 1800s (30 minutes)   - 3x multiplier
# Fourth attempt: 6000s (100 minutes) - 10x multiplier

result = await gate.verify()  # Retries up to 4 times on timeout
```

### Article II: 100% Pass Requirement

Even 1 test failure causes an error:

```python
result = await verify_tests("all")

if result.is_err():
    error = result.unwrap_err()

    if error.reason == "failures":
        # Article II violation: not 100% pass rate
        print(f"Failed tests: {error.failed_tests}")
        # ['tests/test_example.py::test_feature1', ...]
```

### Memory-Aware Execution

The gate automatically adjusts test workers based on available memory:

```python
# Integrated with memory_aware_test_runner.py
# - 1 worker if <10GB available (critical memory)
# - 3 workers if local model ON + <15GB (safe for 48GB Mac with 38GB model)
# - 10 workers if local model OFF + >20GB (full parallelism)
# - 6 workers otherwise (moderate parallelism)

result = await gate.verify()  # Worker count auto-calculated
```

## Test Modes

```python
# Full test suite (1725+ tests)
result = await verify_tests("all")

# Unit tests only (excludes integration, slow, benchmark)
result = await verify_tests("unit")

# Fast tests only (excludes slow, integration, benchmark)
result = await verify_tests("fast")
```

## Error Handling

```python
from tools.orchestrator import VerificationError

result = await verify_tests("all")

if result.is_err():
    error: VerificationError = result.unwrap_err()

    match error.reason:
        case "timeout":
            # Test execution timed out (Article I violation)
            print(f"Timeout after {error.exit_code} retries")

        case "failures":
            # Tests failed (Article II violation)
            print(f"Failed: {error.failed_tests}")

        case "no_tests_run":
            # No tests executed (configuration error)
            print("Check pytest configuration")

        case "process_error":
            # Failed to execute tests
            print(f"Error: {error.message}")

        case "parse_error":
            # Failed to parse test output
            print(f"Parse error: {error.output}")
```

## Integration Example: Pre-Merge Gate

```python
async def pre_merge_validation():
    """Validate all tests pass before allowing merge (Article III enforcement)."""

    print("🚦 Running pre-merge test verification...")

    result = await verify_tests("all")

    if result.is_ok():
        results = result.unwrap()
        print(f"✅ {results.get_summary()}")
        return True  # Allow merge
    else:
        error = result.unwrap_err()
        print(f"❌ Merge blocked: {error.message}")

        if error.failed_tests:
            print("\nFailed tests:")
            for test in error.failed_tests:
                print(f"  - {test}")

        return False  # Block merge

# Usage in CI/CD pipeline
if __name__ == "__main__":
    allowed = asyncio.run(pre_merge_validation())
    sys.exit(0 if allowed else 1)
```

## Advanced: Custom Timeout Configuration

```python
from pathlib import Path

# Create gate with custom timeout
gate = TestVerificationGate(project_root=Path.cwd())

# Override default timeout (600s)
gate.base_timeout = 300  # 5 minutes

# Override retry multipliers (default: [1, 2, 3, 10])
gate.timeout_multipliers = [1, 2, 4]  # Try 3 times with 1x, 2x, 4x

result = await gate.verify()
```

## Metrics for Learning (Article IV)

```python
result = await verify_tests("all")

if result.is_ok():
    results = result.unwrap()

    # Extract metrics for VectorStore storage
    metrics = {
        "passed": results.passed,
        "failed": results.failed,
        "skipped": results.skipped,
        "duration": results.duration,
        "worker_count": results.worker_count,
        "exit_code": results.exit_code,
        "constitutional": results.is_constitutional(),
    }

    # Store in AgentContext for pattern learning
    context.store_memory(
        key=f"test_verification_{timestamp}",
        content=metrics,
        tags=["verification", "testing", "success"]
    )
```

## Performance Benchmarks

**Expected performance on M4 Pro (48GB RAM):**

- **Unit tests** (1500+ tests): ~30-45s with 10 workers
- **All tests** (1725+ tests): ~60-90s with 10 workers
- **Memory-safe mode** (local model ON): ~90-120s with 3 workers

**Timeout configuration:**
- Base timeout: 600s (10 minutes)
- Retry multipliers: 2x, 3x, 10x
- Maximum total time: ~100 minutes (after all retries)

## Constitutional Compliance Checklist

Before using the gate, ensure:

- ✅ **Article I**: Gate retries on timeout (automatic)
- ✅ **Article II**: Gate enforces 100% pass rate (automatic)
- ✅ **Article III**: Gate has no manual overrides (by design)
- ✅ **Article IV**: Store verification patterns after execution (manual)

## Troubleshooting

### "No tests were executed"

```python
# Check pytest configuration
result = await verify_tests("unit")

if result.is_err():
    error = result.unwrap_err()
    if error.reason == "no_tests_run":
        print("Check: pytest.ini, conftest.py, test markers")
```

### "Process timeout after retries"

```python
# Increase base timeout or reduce worker count
gate = TestVerificationGate()
gate.base_timeout = 900  # 15 minutes instead of 10

result = await gate.verify()
```

### "Memory exhaustion during tests"

```python
# Memory-aware runner automatically reduces workers
# But you can force it lower:
import os
os.environ["LOCAL_MODEL_TEST_WORKERS"] = "1"  # Force single worker

result = await verify_tests("all")
```

## See Also

- `constitution.md` - Constitutional requirements (Articles I-V)
- `docs/adr/ADR-001.md` - Complete Context Before Action
- `docs/adr/ADR-002.md` - 100% Verification and Stability
- `tools/memory_aware_test_runner.py` - Memory-aware worker calculation
- `run_tests.py` - Underlying test runner
