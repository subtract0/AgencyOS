# Test Suite Performance Guidelines

## Overview

This document defines mandatory performance standards for all Agency OS tests. Fast tests are not optional - they are a **constitutional requirement** (Article II: 100% Verification and Stability). Slow tests create bottlenecks that prevent rapid iteration and continuous validation.

**Target Audience**: Test authors, code reviewers, CI/CD engineers

**Version**: 1.0.0
**Status**: Active
**Last Updated**: 2025-10-22

---

## Table of Contents

1. [Unit vs Integration Test Rules](#unit-vs-integration-test-rules)
2. [Timeout Requirements](#timeout-requirements)
3. [asyncio.sleep Mocking](#asynciosleep-mocking)
4. [Process Cleanup Best Practices](#process-cleanup-best-practices)
5. [Performance Budgets](#performance-budgets)
6. [Good vs Bad Patterns](#good-vs-bad-patterns)
7. [Constitutional Compliance](#constitutional-compliance)
8. [Validation Tools](#validation-tools)

---

## Unit vs Integration Test Rules

### Unit Tests

**Purpose**: Test single functions/components in isolation

**Performance Standards**:
- **Individual**: <100ms each (ideal)
- **Suite Total**: <500ms for all unit tests in a file
- **No Real I/O**: Mock all file, network, database operations
- **No Real Delays**: Mock `asyncio.sleep()` and `time.sleep()`

**Markers**:
```python
@pytest.mark.unit
@pytest.mark.timeout(5)  # Fail after 5 seconds
@pytest.mark.asyncio     # If testing async code
```

**Example**:
```python
@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_audit_report_creation(monkeypatch):
    """Test audit report creation without I/O delays."""
    # Mock asyncio.sleep for instant execution
    monkeypatch.setattr(asyncio, 'sleep', lambda x: None)

    report = await create_audit_report()

    assert report.total_cycles == 0
    assert report.final_health_score >= 0.0
```

### Integration Tests

**Purpose**: Test complete workflows with real component interactions

**Performance Standards**:
- **Individual**: <10s each (maximum)
- **No Suite Limit**: Each test is independent
- **Real I/O Allowed**: Can use real file operations if needed
- **Real Delays Allowed**: Use `asyncio.sleep()` only if testing timing behavior

**Markers**:
```python
@pytest.mark.integration
@pytest.mark.timeout(10)  # Fail after 10 seconds
@pytest.mark.asyncio      # If testing async code
```

**Example**:
```python
@pytest.mark.integration
@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_full_audit_loop():
    """Test complete autonomous audit loop (3 iterations)."""
    result = await autonomous_audit_loop(
        codebase_path="/Users/am/Code/Agency",
        max_iterations=3
    )

    assert result.is_ok()
    report = result.unwrap()
    assert report.total_cycles > 0
```

---

## Timeout Requirements

**MANDATORY**: All async tests MUST have `@pytest.mark.timeout()` decorator.

### Why Timeouts Are Required

1. **Fail Fast**: Detect infinite loops and hangs immediately
2. **CI Protection**: Prevent CI/CD pipeline bottlenecks
3. **Developer Experience**: Rapid feedback on broken tests
4. **Resource Management**: Prevent runaway processes

### Timeout Standards

| Test Type | Timeout | Rationale |
|-----------|---------|-----------|
| **Unit** | 5 seconds | Should be <1s, but 5s buffer for CI variability |
| **Integration** | 10 seconds | Allow workflow completion with safety margin |
| **Performance** | 2 seconds | Strict budget for regression detection |

### Example: Adding Timeouts

```python
# ❌ BAD: No timeout (test can hang forever)
@pytest.mark.unit
@pytest.mark.asyncio
async def test_without_timeout():
    await function_that_might_hang()

# ✅ GOOD: Timeout enforced (fails after 5s)
@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_with_timeout():
    await function_that_might_hang()
```

### Validation

Run `tests/validation/test_function_timeouts.py` to verify all async functions have timeout decorators:

```bash
pytest tests/validation/test_function_timeouts.py -v
```

---

## asyncio.sleep Mocking

**POLICY**: Unit tests MUST NOT use real `asyncio.sleep()` or `time.sleep()`. Integration tests MAY use real sleep if testing timing behavior.

### Why Mock Sleep?

1. **Performance**: Real sleep adds seconds/minutes to test suite
2. **Determinism**: Avoid timing-dependent flakiness
3. **Testing Value**: We test logic, not timing
4. **Article II Compliance**: Fast tests enable 100% verification

### Mocking Patterns

#### Pattern 1: Basic Mocking with unittest.mock

```python
from unittest.mock import AsyncMock, patch
import asyncio
import time

@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_with_mocked_sleep():
    """Test async function with mocked sleep."""
    async def function_with_sleep():
        await asyncio.sleep(10.0)  # Would take 10 seconds
        return "done"

    # Mock sleep to be instantaneous
    with patch('asyncio.sleep', new_callable=AsyncMock):
        start = time.time()
        result = await function_with_sleep()
        elapsed = time.time() - start

    # Assert: Instant execution (not 10 seconds)
    assert elapsed < 0.1, "Mocked sleep should be instant"
    assert result == "done"
```

#### Pattern 2: Verify Mock Call Count

```python
@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_verify_sleep_calls():
    """Verify asyncio.sleep was called with correct arguments."""
    async def function_with_multiple_sleeps():
        await asyncio.sleep(0.1)
        await asyncio.sleep(0.2)
        return "done"

    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        await function_with_multiple_sleeps()

    # Assert: Mock was called twice with correct durations
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(0.1)
    mock_sleep.assert_any_call(0.2)
```

#### Pattern 3: Pytest Fixture (Reusable)

```python
@pytest.fixture
def mock_sleep(monkeypatch):
    """Mock asyncio.sleep for instant test execution."""
    async def instant_sleep(duration):
        pass  # No delay

    monkeypatch.setattr(asyncio, 'sleep', instant_sleep)

@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_with_fixture(mock_sleep):
    """Test using reusable mock_sleep fixture."""
    # asyncio.sleep is automatically mocked
    await asyncio.sleep(10.0)  # Instant, not 10 seconds
    result = await function_under_test()
    assert result is not None
```

#### Pattern 4: Module-Level Mocking (Best for Multiple Tests)

```python
import asyncio
from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_asyncio_sleep_for_all_tests(monkeypatch):
    """Automatically mock asyncio.sleep for all tests in module."""
    monkeypatch.setattr(asyncio, 'sleep', AsyncMock())

@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_one():
    """All tests in module automatically use mocked sleep."""
    await asyncio.sleep(5.0)  # Instant
    assert True

@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_two():
    """Another test with automatic mocking."""
    await asyncio.sleep(10.0)  # Instant
    assert True
```

### Validation

Run `tests/integration/test_mock_asyncio_sleep.py` to verify mocking patterns:

```bash
pytest tests/integration/test_mock_asyncio_sleep.py -v
```

This test suite includes:
- 16 tests covering all mocking patterns
- NECESSARY compliance validation (Normal, Edge, Security, etc.)
- Examples for future test authors

---

## Process Cleanup Best Practices

When tests spawn processes (e.g., pytest, local models), cleanup must be **non-blocking** and **secure**.

### Use psutil Instead of Subprocess Pipes

**❌ BAD: Blocking subprocess with shell pipes**
```python
import subprocess

def cleanup_old_way():
    """SLOW, FRAGILE, INSECURE - Don't do this!"""
    subprocess.run(
        "ps aux | grep pytest | awk '{print $2}' | xargs kill",
        shell=True,
        check=False
    )
    # Problems:
    # 1. Blocks for 500-1000ms on macOS
    # 2. Fragile parsing (varies by OS)
    # 3. Security risk (shell=True with untrusted input)
    # 4. No error handling
```

**✅ GOOD: Non-blocking psutil with security**
```python
import os
import psutil

def cleanup_new_way():
    """FAST, ROBUST, SECURE - Use this pattern!"""
    current_pid = os.getpid()
    killed_count = 0

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Security: Skip current process
            if proc.info['pid'] == current_pid:
                continue

            # Security: Whitelist only test processes
            cmdline = ' '.join(proc.info['cmdline'] or [])
            is_test_process = 'pytest' in cmdline.lower()

            if is_test_process:
                proc.kill()  # Non-blocking
                killed_count += 1

        except psutil.NoSuchProcess:
            # Process disappeared - not an error
            continue
        except psutil.AccessDenied:
            # Permission denied - continue with others
            continue

    return killed_count
```

### Performance Impact

| Method | Duration | Blocking | Security |
|--------|----------|----------|----------|
| **subprocess + pipes** | 500-1000ms | Yes | Low |
| **psutil** | <200ms | No | High |

**Improvement**: **80% faster**, non-blocking, more secure

### Security Requirements

1. **Whitelist Processes**: Only kill test-related processes
2. **Exclude Current PID**: Never kill the test process itself
3. **No Shell Injection**: Use `psutil.process_iter()`, not shell commands
4. **Graceful Degradation**: Best-effort cleanup, don't fail tests on errors

### Example: Secure Pre-Flight Cleanup

```python
import os
import psutil

async def pre_flight_cleanup() -> Result[str, str]:
    """
    Pre-flight cleanup with security and performance best practices.

    Performance: <200ms (non-blocking)
    Security: Whitelist-only, excludes current PID
    """
    current_pid = os.getpid()
    killed_count = 0
    errors = []

    try:
        # Iterate over processes (non-blocking, no shell pipes)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Security: Skip current process
                if proc.info['pid'] == current_pid:
                    continue

                # Security: Whitelist test processes only
                cmdline = ' '.join(proc.info['cmdline'] or [])
                name = proc.info['name'] or ''

                is_test_process = (
                    'pytest' in cmdline.lower() or
                    'test_autonomous' in cmdline.lower() or
                    ('python' in name.lower() and 'test' in cmdline.lower())
                )

                if is_test_process:
                    proc.kill()  # Non-blocking kill
                    killed_count += 1

            except psutil.NoSuchProcess:
                # Process disappeared - not an error
                continue
            except psutil.AccessDenied as e:
                # Permission denied - continue with other processes
                errors.append(f"Access denied for PID {proc.info['pid']}")
                continue

        # Success even with some errors (best-effort cleanup)
        return Ok(f"Cleanup complete: {killed_count} killed")

    except Exception as e:
        return Err(f"Cleanup failed: {e}")
```

### Validation

Run `tests/integration/test_non_blocking_cleanup.py` to verify cleanup patterns:

```bash
pytest tests/integration/test_non_blocking_cleanup.py -v
```

This test suite includes:
- 24 tests covering security, performance, error handling
- Validation of <200ms cleanup duration
- Security whitelist enforcement

---

## Performance Budgets

### Individual Test Budgets

| Test Type | Budget | Rationale |
|-----------|--------|-----------|
| **Unit Test** | <100ms each | Instant feedback, rapid iteration |
| **Integration Test** | <10s each | Allow workflow completion |

### Suite Budgets

| Suite Type | Budget | Enforcement |
|------------|--------|-------------|
| **Unit tests (per file)** | <500ms | Automated regression tests |
| **Integration tests** | <10s per test | Timeout decorators |
| **Full suite** | <2s | CI/CD pipeline checks |

### Regression Detection

**20% Margin for Variability**: Performance tests allow 20% variance to account for:
- CI/CD environment differences
- System load fluctuations
- Network latency (integration tests)

**Example Baseline**:
```python
# test_autonomous_audit_loop.py baseline
BEFORE_OPTIMIZATION = 3.91  # seconds
AFTER_OPTIMIZATION = 0.53   # seconds
IMPROVEMENT = 86.4          # percent

# Acceptable range (20% margin)
MIN_DURATION = 0.53 * 0.8   # 0.42s
MAX_DURATION = 0.53 * 1.2   # 0.64s
```

### Automated Regression Suite

Run `tests/validation/test_performance_regression.py` to detect regressions:

```bash
pytest tests/validation/test_performance_regression.py -v
```

This suite validates:
- Individual test durations
- Suite total duration
- Performance baselines (before/after optimization)

### CI/CD Enforcement

Use `pytest --durations=0` to identify slow tests:

```bash
# Show all test durations (sorted slowest first)
pytest --durations=0 tests/integration/test_autonomous_audit_loop.py

# Show top 10 slowest tests
pytest --durations=10 tests/
```

**Action on Violations**:
1. Tests >100ms (unit): Investigate for real I/O or sleep
2. Tests >10s (integration): Refactor or split into smaller tests
3. Suite >2s: Profile with `pytest-profiling` to identify bottlenecks

---

## Good vs Bad Patterns

### Pattern 1: Fast Unit Tests

**❌ BAD: Real sleep in unit test (too slow)**
```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_slow_unit():
    """This test takes 11 seconds - UNACCEPTABLE!"""
    await asyncio.sleep(10.0)  # Real delay
    await asyncio.sleep(1.0)   # More real delay
    result = await function_under_test()
    assert result is not None
```

**✅ GOOD: Mocked sleep for instant execution**
```python
@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_fast_unit(monkeypatch):
    """This test takes <100ms - EXCELLENT!"""
    # Mock sleep for instant execution
    monkeypatch.setattr(asyncio, 'sleep', lambda x: None)

    await asyncio.sleep(10.0)  # Instant
    await asyncio.sleep(1.0)   # Instant
    result = await function_under_test()
    assert result is not None
```

### Pattern 2: Process Cleanup

**❌ BAD: Blocking subprocess with pipes**
```python
def cleanup_old_way():
    """SLOW (500-1000ms), FRAGILE, INSECURE"""
    subprocess.run(
        "ps aux | grep pytest | awk '{print $2}' | xargs kill",
        shell=True,
        check=False
    )
```

**✅ GOOD: Non-blocking psutil with security**
```python
def cleanup_new_way():
    """FAST (<200ms), ROBUST, SECURE"""
    current_pid = os.getpid()

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] == current_pid:
                continue

            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'pytest' in cmdline.lower():
                proc.kill()

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
```

### Pattern 3: Timeout Decorators

**❌ BAD: No timeout (test can hang forever)**
```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_timeout():
    """If function_that_might_hang() hangs, CI blocks forever!"""
    result = await function_that_might_hang()
    assert result is not None
```

**✅ GOOD: Timeout enforced (fails after 5s)**
```python
@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_with_timeout():
    """If function_that_might_hang() hangs, fails after 5s"""
    result = await function_that_might_hang()
    assert result is not None
```

### Pattern 4: Test Markers

**❌ BAD: No markers (unclear test type)**
```python
@pytest.mark.asyncio
async def test_unclear_type():
    """Is this unit or integration? What's the timeout?"""
    result = await some_function()
    assert result is not None
```

**✅ GOOD: Clear markers (explicit test type)**
```python
@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio
async def test_clear_type():
    """Clearly marked as unit test with 5s timeout"""
    result = await some_function()
    assert result is not None
```

### Pattern 5: Integration Test Performance

**❌ BAD: Integration test with unnecessary delays**
```python
@pytest.mark.integration
@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_slow_integration():
    """Takes 15 seconds - TOO SLOW!"""
    result = await run_audit_loop(max_iterations=10)  # Too many
    await asyncio.sleep(5.0)  # Unnecessary cooldown
    assert result.is_ok()
```

**✅ GOOD: Integration test with minimal iterations**
```python
@pytest.mark.integration
@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_fast_integration():
    """Takes <3 seconds - EXCELLENT!"""
    result = await run_audit_loop(max_iterations=3)  # Sufficient
    # No unnecessary delays
    assert result.is_ok()
```

---

## Constitutional Compliance

### Article I: Complete Context Before Action

**Requirement**: Tests must run to completion, not timeout due to missing context.

**Implementation**:
- Retry protocol: 2x, 3x, up to 10x timeout on incomplete data
- Never accept partial results
- Fast tests enable rapid retries

**Example**:
```python
@pytest.mark.timeout(10)
async def test_with_retry_protocol():
    """Test with Article I retry protocol."""
    timeout_ms = 5000
    max_retries = 3

    for attempt in range(max_retries):
        result = await run_test(timeout=timeout_ms)

        if result.is_ok():
            return result

        # Article I: Exponential backoff
        timeout_ms *= 2

    pytest.fail("Test timed out after retries")
```

### Article II: 100% Verification and Stability

**Requirement**: Fast tests enable 100% verification (main branch always passes).

**Implementation**:
- Unit tests: <500ms per file (rapid iteration)
- Integration tests: <10s each (workflow validation)
- No merge without 100% test pass

**Why Fast Tests Matter**:
- Slow tests → Developers skip tests → Bugs slip through
- Fast tests → Tests run always → 100% verification

**Example**:
```python
# Fast tests enable pre-commit hooks
@pytest.mark.unit
@pytest.mark.timeout(5)
def test_fast_validation():
    """Runs in <100ms, enabling pre-commit validation."""
    result = validate_input(data)
    assert result.is_ok()
```

### Article III: Automated Local Enforcement

**Requirement**: Quality gates are automated and absolute (no manual overrides).

**Implementation**:
- Pre-commit hooks: Run fast unit tests (<500ms)
- CI/CD pipeline: Run full suite (<2s)
- Performance regression suite: Automated baselines

**Example**:
```bash
# .git/hooks/pre-commit (automated enforcement)
pytest -m "unit and not integration" --timeout=5 -v
if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed (Article III violation)"
    exit 1
fi
```

### Article IV: Continuous Learning

**Requirement**: Document successful patterns for institutional knowledge.

**Implementation**:
- This document captures performance patterns
- VectorStore stores successful test optimizations
- Learning agents extract patterns from test suite

**Example**:
```python
# After successful optimization, store pattern
context.store_memory(
    key="test_performance_optimization",
    content={
        "pattern": "mock_asyncio_sleep_for_unit_tests",
        "before": "3.91s",
        "after": "0.53s",
        "improvement": "86.4%"
    },
    tags=["performance", "testing", "pattern"]
)
```

### Article V: Spec-Driven Development

**Requirement**: All implementation traces to specification.

**Implementation**:
- Performance optimization spec: `specs/spec-performance-optimization.md`
- ADR references: `docs/adr/ADR-XXX-test-performance.md`
- Task graph: Links tests to specs

**Example**:
```python
"""
Test suite for autonomous audit loop.

Spec: specs/spec-performance-optimization.md
ADR: docs/adr/ADR-XXX-test-performance.md
Task: remove_intentional_delays (Phase 2)
Task: add_asyncio_sleep_mocks (Phase 3)
"""
```

---

## Validation Tools

### Tool 1: Performance Regression Suite

**Location**: `tests/validation/test_performance_regression.py`

**Purpose**: Detect performance regressions by comparing against baselines.

**Usage**:
```bash
pytest tests/validation/test_performance_regression.py -v
```

**Validates**:
- Individual test durations (<100ms for unit, <10s for integration)
- Suite total duration (<2s)
- Before/after optimization baselines (86.4% improvement)

### Tool 2: Function Timeout Validator

**Location**: `tests/validation/test_function_timeouts.py`

**Purpose**: Ensure all async tests have `@pytest.mark.timeout()` decorator.

**Usage**:
```bash
pytest tests/validation/test_function_timeouts.py -v
```

**Validates**:
- All async tests have timeout decorator
- Timeout values are reasonable (5s for unit, 10s for integration)

### Tool 3: asyncio.sleep Mocking Validator

**Location**: `tests/integration/test_mock_asyncio_sleep.py`

**Purpose**: Validate no real sleep in unit tests, document mocking patterns.

**Usage**:
```bash
pytest tests/integration/test_mock_asyncio_sleep.py -v
```

**Validates**:
- 16 mocking patterns (NECESSARY compliance)
- No real sleep in unit tests (security requirement)
- Examples for future authors (accessibility)

### Tool 4: Unit/Integration Separation Validator

**Location**: `tests/validation/test_unit_integration_separation.py`

**Purpose**: Ensure unit tests are marked correctly (no real I/O).

**Usage**:
```bash
pytest tests/validation/test_unit_integration_separation.py -v
```

**Validates**:
- Unit tests have `@pytest.mark.unit` marker
- Integration tests have `@pytest.mark.integration` marker
- No mixing of markers

### Tool 5: pytest --durations (Built-in)

**Purpose**: Identify slow tests in any suite.

**Usage**:
```bash
# Show all test durations (sorted slowest first)
pytest --durations=0 tests/

# Show top 10 slowest tests
pytest --durations=10 tests/
```

**Action Items**:
1. Tests >100ms (unit): Investigate for real I/O or sleep
2. Tests >10s (integration): Refactor or split
3. Suite >2s: Profile with `pytest-profiling`

---

## Quick Reference Card

### Test Type Cheat Sheet

| Test Type | Marker | Timeout | Performance | I/O Allowed |
|-----------|--------|---------|-------------|-------------|
| **Unit** | `@pytest.mark.unit` | 5s | <100ms each | No (mock all) |
| **Integration** | `@pytest.mark.integration` | 10s | <10s each | Yes (if needed) |

### Mandatory Decorators

```python
# Unit test template
@pytest.mark.unit
@pytest.mark.timeout(5)
@pytest.mark.asyncio  # If async
async def test_unit_example(monkeypatch):
    # Mock asyncio.sleep
    monkeypatch.setattr(asyncio, 'sleep', lambda x: None)

    result = await function_under_test()
    assert result.is_ok()

# Integration test template
@pytest.mark.integration
@pytest.mark.timeout(10)
@pytest.mark.asyncio  # If async
async def test_integration_example():
    result = await complete_workflow()
    assert result.is_ok()
```

### Performance Checklist

Before committing new tests, verify:

- [ ] Unit tests: <100ms each
- [ ] Integration tests: <10s each
- [ ] All async tests have `@pytest.mark.timeout()`
- [ ] Unit tests mock `asyncio.sleep()`
- [ ] Process cleanup uses `psutil` (not subprocess)
- [ ] Test markers are correct (`@pytest.mark.unit` or `@pytest.mark.integration`)
- [ ] No real I/O in unit tests (file, network, database)
- [ ] Run regression suite: `pytest tests/validation/test_performance_regression.py`

---

## References

### Documentation
- **Constitution**: `constitution.md` (Article I-V compliance)
- **ADR Index**: `docs/adr/ADR-INDEX.md` (architectural decisions)
- **Test Suite Audit**: `docs/testing/TEST_SUITE_AUDIT_PLAN.md` (comprehensive analysis)

### Specifications
- **Performance Optimization**: `specs/spec-performance-optimization.md`
- **Autonomous Audit Loop**: `specs/spec-autonomous-audit-loop.md`

### Validation Tests
- **Performance Regression**: `tests/validation/test_performance_regression.py`
- **Function Timeouts**: `tests/validation/test_function_timeouts.py`
- **asyncio.sleep Mocking**: `tests/integration/test_mock_asyncio_sleep.py`
- **Unit/Integration Separation**: `tests/validation/test_unit_integration_separation.py`
- **Non-Blocking Cleanup**: `tests/integration/test_non_blocking_cleanup.py`

### Example Tests
- **Autonomous Audit Loop**: `tests/integration/test_autonomous_audit_loop.py` (7 tests, 0.53s)
- **Performance Baselines**: Before 3.91s → After 0.53s (86.4% improvement)

---

## Changelog

### Version 1.0.0 (2025-10-22)
- Initial release
- Performance budgets defined
- Unit vs integration rules documented
- Timeout requirements specified
- asyncio.sleep mocking patterns documented
- Process cleanup best practices added
- Good/bad pattern examples provided
- Constitutional compliance references added
- Validation tools documented

---

## Contact

For questions or suggestions:
- **GitHub Issues**: [Agency OS Repository](https://github.com/subtract0/AgencyOS/issues)
- **ADR Proposals**: Submit via `/architect-review-proposals`

---

**Version**: 1.0.0
**Status**: Active
**Last Updated**: 2025-10-22
**Next Review**: 2025-11-22
