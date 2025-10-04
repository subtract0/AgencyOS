# Chaos Testing Guide

## Overview

Chaos testing (also known as chaos engineering) is a discipline that validates system resilience by intentionally injecting failures into the system and verifying it handles them gracefully. This guide explains Agency OS's chaos testing framework and how to use it to ensure Mars Rover-grade reliability.

## What is Chaos Testing?

Chaos testing answers the question: **"What happens when things go wrong?"**

Instead of assuming your code will run in perfect conditions, chaos testing:
- **Injects random failures** into your system (network timeouts, disk errors, memory pressure)
- **Verifies graceful degradation** (system slows down but doesn't crash)
- **Validates recovery mechanisms** (system recovers when failures stop)
- **Prevents catastrophic failures** in production

### Why Chaos Testing Matters

Real-world systems face constant failures:
- Network calls timeout 5-15% of the time
- Disk writes fail due to space, permissions, or hardware issues
- Memory allocation fails under pressure
- External processes crash unexpectedly
- Operations take longer than expected

**Without chaos testing**: Your code works in development, crashes in production.

**With chaos testing**: Your code survives production chaos because you've already tested it.

## The Chaos Testing Framework

Agency OS provides a comprehensive chaos testing framework in `tools/chaos_testing.py`.

### Supported Chaos Types

| Chaos Type | What It Does | Real-World Scenario |
|------------|--------------|---------------------|
| `NETWORK` | Randomly fails network calls with timeouts/connection errors | API calls to LLM providers, web scraping failures |
| `DISK_IO` | Randomly fails file read/write operations | Disk full, permission denied, I/O errors |
| `TIMEOUT` | Adds random delays to operations | Slow networks, CPU pressure, context switching |
| `MEMORY` | Fails memory allocations | OOM conditions, memory leaks |
| `PROCESS` | Fails subprocess executions | Command not found, permission denied, crashes |

### Configuration

```python
from tools.chaos_testing import ChaosConfig, ChaosType

config = ChaosConfig(
    chaos_types=[ChaosType.NETWORK, ChaosType.DISK_IO],
    failure_rate=0.3,        # 30% of operations fail
    seed=42,                 # For reproducible tests
    duration_seconds=60,     # How long to inject chaos
    enabled=True             # Enable/disable chaos
)
```

## Using the Chaos Framework

### Method 1: Decorator (Simplest)

Use the `@chaos` decorator for quick tests:

```python
from tools.chaos_testing import chaos, ChaosType

@chaos(chaos_types=[ChaosType.NETWORK], failure_rate=0.3)
def test_my_function():
    # Your test code here
    result = call_external_api()
    assert result is not None  # Should handle failures gracefully
```

### Method 2: Context Manager

Use `chaos_context` for more control:

```python
from tools.chaos_testing import chaos_context, ChaosConfig, ChaosType

def test_with_context():
    config = ChaosConfig(
        chaos_types=[ChaosType.DISK_IO],
        failure_rate=0.5
    )

    with chaos_context(config) as engine:
        # Chaos active here
        write_to_disk()

    # Chaos cleaned up here
    # Verify results
    assert engine.injections > 0
```

### Method 3: Engine (Most Control)

Use `ChaosEngine` directly for maximum control:

```python
from tools.chaos_testing import ChaosEngine, ChaosConfig, ChaosType

def test_with_engine():
    config = ChaosConfig(
        chaos_types=[ChaosType.NETWORK, ChaosType.TIMEOUT],
        failure_rate=0.4,
        seed=42
    )

    engine = ChaosEngine(config)

    def my_test():
        # Test code here
        perform_operations()

    result = engine.run_chaos_test(my_test)

    # Analyze results
    if result.is_ok():
        chaos_result = result.value
        print(f"Recovery rate: {chaos_result.recovery_rate * 100}%")
        print(f"Total injections: {chaos_result.total_injections}")
```

## Writing Chaos Tests

### Test Structure

Chaos tests should verify **graceful degradation**, not success:

```python
# ❌ BAD: Expects operation to succeed
@chaos(chaos_types=[ChaosType.NETWORK], failure_rate=0.5)
def test_api_call():
    result = call_api()
    assert result.is_ok()  # Will fail when chaos injects errors!

# ✅ GOOD: Expects graceful handling
@chaos(chaos_types=[ChaosType.NETWORK], failure_rate=0.5)
def test_api_call():
    result = call_api()
    # Should not crash, should return error or retry
    assert result is not None
    assert not crashed()
```

### Example: Testing an Agent

```python
from tools.chaos_testing import chaos, ChaosType

@chaos(
    chaos_types=[ChaosType.NETWORK, ChaosType.DISK_IO, ChaosType.TIMEOUT],
    failure_rate=0.5
)
def test_agent_survives_chaos():
    """Agent should handle 50% failure rate across all operations."""
    agent = MyAgent()

    # Run agent task
    result = agent.execute_task("complex task")

    # Verify graceful handling:
    # 1. No crash
    assert result is not None

    # 2. Errors logged properly
    assert len(agent.error_log) >= 0

    # 3. State remains consistent
    assert agent.state in ["idle", "error", "recovered"]

    # 4. No data corruption
    if agent.output_file.exists():
        content = agent.output_file.read_text()
        assert is_valid_format(content)  # Not partially written
```

### Example: Testing Retry Logic

```python
from tools.chaos_testing import ChaosEngine, ChaosConfig, ChaosType

def test_retry_logic_under_chaos():
    """Verify retry mechanism works during failures."""
    config = ChaosConfig(
        chaos_types=[ChaosType.NETWORK],
        failure_rate=0.7,  # High failure rate
        seed=42
    )

    engine = ChaosEngine(config)

    retry_counts = []

    def task_with_retry():
        max_retries = 3
        for attempt in range(max_retries):
            try:
                call_external_service()
                retry_counts.append(attempt)
                break
            except Exception:
                if attempt == max_retries - 1:
                    retry_counts.append(attempt)

    result = engine.run_chaos_test(task_with_retry)

    assert result.is_ok()
    # Should have attempted retries
    assert max(retry_counts) > 0
```

## Running Chaos Tests

### Via CLI Script

The easiest way to run chaos tests:

```bash
# Run with default settings (30% failure rate)
./scripts/run_chaos_tests.sh

# Custom configuration
./scripts/run_chaos_tests.sh \
  --chaos-types network,disk,timeout,memory,process \
  --failure-rate 0.5 \
  --duration 120 \
  --seed 42 \
  --output-report docs/testing/MY_CHAOS_REPORT.md \
  --verbose

# Get help
./scripts/run_chaos_tests.sh --help
```

### Via pytest Directly

```bash
# Run chaos framework tests
pytest tests/unit/tools/test_chaos_testing.py -v

# Run agent chaos tests
pytest tests/chaos/ -v

# Run all chaos tests
pytest tests/unit/tools/test_chaos_testing.py tests/chaos/ -v
```

### In CI/CD Pipeline

Add to your CI configuration:

```yaml
# .github/workflows/chaos.yml
name: Chaos Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Run nightly
  workflow_dispatch:     # Allow manual trigger

jobs:
  chaos:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run chaos tests
        run: |
          ./scripts/run_chaos_tests.sh \
            --failure-rate 0.4 \
            --output-report chaos-report.md

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: chaos-report
          path: chaos-report.md
```

## Interpreting Results

### Chaos Report Structure

After running chaos tests, you'll get a report like:

```markdown
# Chaos Testing Report

**Duration**: 10.50s
**Total Injections**: 45
**Successful Recoveries**: 42
**Failed Recoveries**: 3
**Crashes**: 0
**Recovery Rate**: 93.3%

## Injection Details

- ✅ [network] requests.get: Chaos: Network connection failed
- ✅ [disk_io] builtins.open: Chaos: Disk write failure
- ❌ [timeout] time.sleep: Added 2.34s delay
  Error: Operation timed out
```

### What to Look For

1. **Recovery Rate**: Should be >80% for production readiness
   - Below 80%: Need better error handling
   - 80-95%: Good resilience
   - Above 95%: Excellent

2. **Crash Count**: Should be 0
   - Any crashes indicate catastrophic failure mode
   - Fix immediately before production

3. **Failed Recoveries**: Investigate each one
   - Why did the system not recover?
   - Is there missing error handling?
   - Can we add retries or fallbacks?

4. **Injection Distribution**: Verify all chaos types triggered
   - If no injections for a type, increase failure rate or duration
   - Seed-based reproducibility helps debug specific scenarios

### Example Analysis

```
Recovery Rate: 85% ✅ (Good - production ready)
Crashes: 0 ✅ (Excellent - no catastrophic failures)
Failed Recoveries: 7 ⚠️ (Investigate these)

Recommendations:
1. Add retry logic for network operations (3 failures)
2. Implement atomic file writes (2 failures)
3. Add timeout handling for long-running ops (2 failures)
```

## Best Practices

### 1. Start with Low Failure Rates

```python
# Start here
failure_rate=0.1  # 10% - gentle introduction

# Then increase
failure_rate=0.3  # 30% - realistic production
failure_rate=0.5  # 50% - stress test
failure_rate=0.7  # 70% - extreme conditions
```

### 2. Use Seeds for Reproducibility

```python
# Reproducible chaos
config = ChaosConfig(
    chaos_types=[ChaosType.NETWORK],
    failure_rate=0.3,
    seed=42  # Same failures every run
)
```

### 3. Test One Chaos Type at a Time

```python
# First understand each type individually
test_network_chaos()
test_disk_chaos()
test_timeout_chaos()

# Then combine
test_full_chaos_storm()
```

### 4. Focus on Critical Paths

Prioritize chaos testing for:
- User-facing operations
- Data persistence
- External API calls
- Payment processing
- Authentication

### 5. Monitor Real Failure Rates

Track production failures to set realistic chaos rates:

```python
# If production shows 15% network failures
failure_rate=0.15  # Match reality

# Test 2x production rate for safety margin
failure_rate=0.30  # 2x safety factor
```

### 6. Add Chaos Tests to CI

Run chaos tests regularly:
- **Unit tests**: Every commit (low failure rate, fast)
- **Integration tests**: Every PR (medium failure rate)
- **Nightly**: Full chaos storm (high failure rate, all types)

## Common Patterns

### Pattern 1: Graceful Degradation

```python
@chaos(chaos_types=[ChaosType.NETWORK], failure_rate=0.5)
def test_graceful_degradation():
    """System should degrade gracefully, not catastrophically."""
    agent = Agent()

    # Try operation
    result = agent.call_llm()

    # Should either succeed or fail gracefully
    if result.is_ok():
        assert result.value is not None
    else:
        # Error handling is graceful
        assert "timeout" in str(result.error).lower()
        assert agent.state == "error"  # Clean error state
```

### Pattern 2: Retry Logic

```python
def resilient_operation(max_retries=3):
    """Operation with built-in retry logic."""
    for attempt in range(max_retries):
        try:
            return perform_operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Pattern 3: Circuit Breaker

```python
class CircuitBreaker:
    """Prevent cascading failures."""

    def __init__(self, failure_threshold=5):
        self.failures = 0
        self.threshold = failure_threshold
        self.open = False

    def call(self, func):
        if self.open:
            raise Exception("Circuit breaker open")

        try:
            result = func()
            self.failures = 0  # Reset on success
            return result
        except Exception as e:
            self.failures += 1
            if self.failures >= self.threshold:
                self.open = True
            raise
```

### Pattern 4: Atomic Operations

```python
def atomic_write(path, content):
    """Write file atomically to prevent corruption."""
    temp_path = f"{path}.tmp"

    try:
        # Write to temp file first
        with open(temp_path, 'w') as f:
            f.write(content)

        # Atomic rename
        os.rename(temp_path, path)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
```

## Troubleshooting

### Issue: Tests fail with chaos enabled

**Problem**: `@chaos` decorator causes tests to fail.

**Solution**: Your code doesn't handle failures gracefully. Add error handling:

```python
# Before
def my_function():
    result = external_call()
    return result.data

# After
def my_function():
    try:
        result = external_call()
        return result.data
    except Exception as e:
        log.error(f"External call failed: {e}")
        return None  # Or raise custom error
```

### Issue: No chaos injections recorded

**Problem**: `chaos_result.total_injections == 0`

**Solution**:
1. Increase `failure_rate`
2. Increase `duration_seconds`
3. Ensure your test actually triggers the operations being monitored

### Issue: Recovery rate is 0%

**Problem**: System never recovers from failures.

**Solution**: Add recovery logic:
- Retry mechanisms
- Fallback values
- Error handling
- State cleanup

### Issue: Chaos persists after test

**Problem**: Monkey patches not cleaned up.

**Solution**: Always use context manager or engine:

```python
# ✅ Cleanup guaranteed
with chaos_context(config) as engine:
    run_test()

# ✅ Cleanup in finally
engine.run_chaos_test(test_func)
```

## Integration with Constitutional Standards

Chaos testing follows Agency OS constitutional principles:

1. **TDD**: Write chaos tests before implementing resilience
2. **Result Pattern**: Use `Result<T, E>` for error handling
3. **Type Safety**: All chaos configs are Pydantic models
4. **Focused Functions**: Each chaos type has dedicated injection function (<50 lines)
5. **Validation**: All inputs validated via Pydantic

## Mars Rover Standard

To meet Mars Rover-grade reliability:

- ✅ **90%+ recovery rate** under 30% failure rate
- ✅ **0 crashes** during chaos tests
- ✅ **Atomic operations** for all state changes
- ✅ **Retry logic** for network operations
- ✅ **Circuit breakers** for external dependencies
- ✅ **Graceful degradation** under pressure
- ✅ **Data integrity** maintained during failures

## Resources

- **Framework Code**: `tools/chaos_testing.py`
- **Unit Tests**: `tests/unit/tools/test_chaos_testing.py`
- **Example Tests**: `tests/chaos/test_agent_chaos.py`
- **CLI Runner**: `scripts/run_chaos_tests.sh`
- **This Guide**: `docs/testing/CHAOS_TESTING_GUIDE.md`

## Further Reading

- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Netflix Chaos Monkey](https://netflix.github.io/chaosmonkey/)
- [Google SRE Book - Testing for Reliability](https://sre.google/sre-book/testing-reliability/)

---

**Remember**: The best time to discover your system crashes under network failures is during chaos testing, not in production.

*Generated by Agency OS - Mars Rover Week 3*
