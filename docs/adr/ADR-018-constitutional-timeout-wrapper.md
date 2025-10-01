# ADR-018: Constitutional Timeout Wrapper

## Status
Accepted

## Context

**Constitutional Gap Identified**: Article I (Complete Context Before Action) mandates timeout handling with exponential retries (2x, 3x, up to 10x) across all operations. Currently:

- **Article I Compliance Score**: 90/100 (missing 10 points)
- **Tools with timeout retry**: 2/35 (6%)
- **Missing Pattern**: `ensure_complete_context()` from constitution.md lines 51-72

**Current State Analysis**:
1. **bash.py** fully implements Article I timeout pattern (lines 535-599)
2. **grep.py** has no timeout handling
3. **apply_and_verify_patch.py** has no timeout handling
4. **33 other tools** lack constitutional timeout compliance

**Constitutional Requirement** (Article I Section 1.2):
```python
# Required pattern for all agents
def ensure_complete_context(operation_func, max_retries=3):
    timeout = 120000  # Start with 2 minutes

    for attempt in range(max_retries):
        result = operation_func(timeout=timeout)

        if result.timed_out:
            timeout *= 2  # Double timeout for retry
            continue

        if result.incomplete:
            continue  # Retry with same timeout

        if result.has_failures():
            raise Exception("STOP: Fix failures before proceeding")

        return result

    raise Exception("Unable to obtain complete context")
```

**Problem Statement**: We need a reusable, decorator-based timeout wrapper that:
- Implements constitutional timeout pattern (1x, 2x, 3x, 5x, 10x multipliers)
- Works with both sync and async operations
- Integrates with telemetry for monitoring
- Supports Result<T,E> pattern for error handling
- Requires minimal changes to existing tool code

---

## Decision

Create a **shared constitutional timeout wrapper utility** at `shared/timeout_wrapper.py` that provides:

1. **Decorator Pattern**: `@with_constitutional_timeout` for easy tool integration
2. **Function Wrapper**: `run_with_constitutional_timeout()` for programmatic usage
3. **Async Support**: `@with_constitutional_timeout_async` for async operations
4. **Telemetry Integration**: Automatic logging of timeout events and retry attempts
5. **Result Pattern**: Returns `Result<T, TimeoutError>` for type-safe error handling

**Architecture**: Centralized timeout logic that tools can adopt via minimal code changes (1-2 lines per tool).

---

## Rationale

### Why Decorator Pattern?

1. **Minimal Code Changes**: Tools add `@with_constitutional_timeout` decorator → instant compliance
2. **Zero Breaking Changes**: Existing tool signatures unchanged
3. **Consistent Behavior**: All tools use identical retry logic
4. **Easy Testing**: Decorators are testable in isolation
5. **Progressive Migration**: Tools can adopt incrementally (no big-bang deployment)

### Why These Timeout Multipliers?

Following `bash.py` proven implementation (line 546):
```python
multipliers = [1, 2, 3, 5, 10]  # Article I: up to 10x timeout multiplier
```

**Rationale**:
- **1x** (baseline): Normal operations complete within default timeout
- **2x**: Handles temporary slowdowns (network lag, CPU contention)
- **3x**: Accommodates large file operations
- **5x**: Heavy computation (test suites, large builds)
- **10x**: Extreme cases (constitutional maximum per Article I)

**Total Retry Budget**: 1x + 2x + 3x + 5x + 10x = 21x baseline timeout
- Default 120s → Maximum 25 minutes total retry time
- Prevents infinite loops while maximizing completion probability

### Why Telemetry Integration?

Constitutional Article IV (Continuous Learning) requires:
- Pattern recognition of timeout causes
- Learning from retry successes/failures
- Adaptive timeout optimization over time

### Alternative Approaches Considered

**Alternative 1: Modify Each Tool Individually**
- **Pros**: Maximum control per tool
- **Cons**: 35 tools × 50 lines = 1,750 lines of duplicated code
- **Cons**: Inconsistent implementations, high maintenance burden
- **Rejected**: Violates DRY principle, Article II quality standards

**Alternative 2: Global Subprocess Wrapper**
- **Pros**: Zero tool changes needed
- **Cons**: Breaks tools that don't use subprocess (e.g., pure Python logic)
- **Cons**: Harder to configure per-tool timeouts
- **Rejected**: Inflexible, incomplete coverage

**Alternative 3: Agent-Level Timeout Handler**
- **Pros**: Central control point
- **Cons**: Agent layer has no visibility into tool-level operations
- **Cons**: Cannot distinguish between "tool slow" vs "tool hung"
- **Rejected**: Wrong abstraction level

---

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Tool Layer (35 tools)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ grep.py  │  │ read.py  │  │ edit.py  │  │   ...    │   │
│  │ @timeout │  │ @timeout │  │ @timeout │  │ @timeout │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                        │
        ┌───────────────▼────────────────────────────────────┐
        │      shared/timeout_wrapper.py                     │
        │  ┌──────────────────────────────────────────────┐ │
        │  │ @with_constitutional_timeout (decorator)     │ │
        │  │  - Wraps tool.run() methods                  │ │
        │  │  - Implements 1x→2x→3x→5x→10x retry logic    │ │
        │  │  - Validates output completeness             │ │
        │  │  - Emits telemetry events                    │ │
        │  └──────────────────────────────────────────────┘ │
        │  ┌──────────────────────────────────────────────┐ │
        │  │ run_with_constitutional_timeout (function)   │ │
        │  │  - Programmatic wrapper for non-decoratable  │ │
        │  │  - Same retry logic as decorator             │ │
        │  └──────────────────────────────────────────────┘ │
        │  ┌──────────────────────────────────────────────┐ │
        │  │ @with_constitutional_timeout_async (async)   │ │
        │  │  - Async version for asyncio operations      │ │
        │  └──────────────────────────────────────────────┘ │
        └───────────────┬────────────────────────────────────┘
                        │
        ┌───────────────▼────────────────────────────────────┐
        │         core/telemetry.py (SimpleTelemetry)        │
        │  - emit("timeout_retry", {...})                    │
        │  - emit("timeout_success", {...})                  │
        │  - emit("timeout_exhausted", {...})                │
        └───────────────┬────────────────────────────────────┘
                        │
        ┌───────────────▼────────────────────────────────────┐
        │     logs/events/run_*.jsonl (Telemetry JSONL)      │
        │  - Retention: 10 runs (per SimpleTelemetry)        │
        │  - Learning agent source data                      │
        └────────────────────────────────────────────────────┘
```

### Integration Points

1. **Tool Layer**: Tools import and apply decorator/wrapper
2. **Timeout Wrapper**: Centralized retry logic with telemetry
3. **Telemetry System**: Constitutional learning and monitoring
4. **Learning Agent**: Pattern extraction for timeout optimization

---

## API Design

### 1. Decorator Pattern (Primary Usage)

```python
from shared.timeout_wrapper import with_constitutional_timeout, TimeoutConfig
from shared.type_definitions.result import Result

class MyTool(BaseTool):
    """Tool with constitutional timeout compliance."""

    # Optional: Configure per-tool timeout behavior
    timeout_config = TimeoutConfig(
        base_timeout_ms=120000,  # 2 minutes default
        max_retries=5,           # Constitutional maximum
        multipliers=[1, 2, 3, 5, 10],  # Article I pattern
        completeness_check=True  # Validate output completeness
    )

    @with_constitutional_timeout()  # Uses class.timeout_config or defaults
    def run(self) -> str:
        # Existing tool implementation unchanged
        result = subprocess.run(["rg", self.pattern], timeout=self.timeout/1000)
        return result.stdout
```

**Decorator Signature**:
```python
def with_constitutional_timeout(
    config: Optional[TimeoutConfig] = None,
    telemetry_prefix: str = "tool"
) -> Callable:
    """
    Decorator for constitutional timeout compliance.

    Args:
        config: Optional TimeoutConfig (uses tool.timeout_config if None)
        telemetry_prefix: Prefix for telemetry events (e.g., "grep", "bash")

    Returns:
        Decorated function with timeout retry logic

    Raises:
        TimeoutExhaustedError: After max_retries exceeded
        IncompleteContextError: If output validation fails after retries
    """
```

### 2. Function Wrapper (Programmatic Usage)

```python
from shared.timeout_wrapper import run_with_constitutional_timeout, TimeoutConfig

class ApplyAndVerifyPatch(Tool):
    def _run_tests(self) -> Dict[str, Any]:
        """Run tests with constitutional timeout handling."""

        config = TimeoutConfig(base_timeout_ms=300000)  # 5 minutes for tests

        result = run_with_constitutional_timeout(
            operation=lambda timeout_ms: self._execute_tests(timeout_ms),
            config=config,
            telemetry_prefix="test_verification"
        )

        if result.is_err():
            return {"success": False, "error": result.unwrap_err()}

        return {"success": True, "output": result.unwrap()}
```

**Function Signature**:
```python
def run_with_constitutional_timeout(
    operation: Callable[[int], T],  # Callable receives timeout_ms
    config: Optional[TimeoutConfig] = None,
    telemetry_prefix: str = "operation"
) -> Result[T, TimeoutError]:
    """
    Execute operation with constitutional timeout retry logic.

    Args:
        operation: Callable that accepts timeout_ms and returns result
        config: Optional TimeoutConfig (uses defaults if None)
        telemetry_prefix: Prefix for telemetry events

    Returns:
        Result[T, TimeoutError]: Ok(value) or Err(timeout_error)
    """
```

### 3. Async Support

```python
from shared.timeout_wrapper import with_constitutional_timeout_async

class AsyncTool(BaseTool):
    @with_constitutional_timeout_async()
    async def run(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, timeout=self.timeout/1000) as resp:
                return await resp.text()
```

### 4. Configuration Model

```python
from pydantic import BaseModel, Field
from typing import List

class TimeoutConfig(BaseModel):
    """Configuration for constitutional timeout behavior."""

    base_timeout_ms: int = Field(
        default=120000,
        description="Base timeout in milliseconds (default: 2 minutes)",
        ge=5000,  # Minimum 5 seconds
        le=600000  # Maximum 10 minutes base (can be multiplied to 100 minutes)
    )

    max_retries: int = Field(
        default=5,
        description="Maximum retry attempts (default: 5 per Article I)",
        ge=1,
        le=10
    )

    multipliers: List[int] = Field(
        default=[1, 2, 3, 5, 10],
        description="Timeout multipliers for each retry (Article I: up to 10x)"
    )

    completeness_check: bool = Field(
        default=True,
        description="Validate output completeness (Article I: Context Verification)"
    )

    telemetry_enabled: bool = Field(
        default=True,
        description="Enable telemetry events for learning (Article IV)"
    )

    pause_between_retries_sec: float = Field(
        default=2.0,
        description="Pause duration between retries for analysis (Article I)",
        ge=0.0,
        le=10.0
    )
```

### 5. Error Types

```python
class TimeoutError(Exception):
    """Base class for timeout-related errors."""
    pass

class TimeoutExhaustedError(TimeoutError):
    """Raised when all retry attempts exhausted."""

    def __init__(self, attempts: int, total_time_ms: int, last_error: Optional[Exception]):
        self.attempts = attempts
        self.total_time_ms = total_time_ms
        self.last_error = last_error
        super().__init__(
            f"Constitutional timeout exhausted after {attempts} attempts "
            f"({total_time_ms}ms total). Article I: Unable to obtain complete context."
        )

class IncompleteContextError(TimeoutError):
    """Raised when output appears incomplete (Article I violation)."""

    def __init__(self, indicator: str):
        self.indicator = indicator
        super().__init__(
            f"Incomplete context detected: {indicator}. Article I: NEVER proceed with incomplete data."
        )
```

---

## Implementation Notes

### Core Retry Logic (from bash.py proven pattern)

```python
def _execute_with_retry(
    operation: Callable[[int], T],
    config: TimeoutConfig,
    telemetry_prefix: str
) -> Result[T, TimeoutError]:
    """Core constitutional retry logic."""

    from core.telemetry import emit
    from datetime import datetime
    import time

    start_time = datetime.now()
    last_result = None

    for attempt in range(config.max_retries):
        # Calculate timeout for this attempt
        if attempt < len(config.multipliers):
            current_timeout_ms = config.base_timeout_ms * config.multipliers[attempt]
        else:
            current_timeout_ms = config.base_timeout_ms * 10  # Cap at 10x

        try:
            # Emit telemetry for retry attempt
            if config.telemetry_enabled:
                emit(f"{telemetry_prefix}_timeout_attempt", {
                    "attempt": attempt + 1,
                    "max_retries": config.max_retries,
                    "timeout_ms": current_timeout_ms,
                    "multiplier": config.multipliers[attempt] if attempt < len(config.multipliers) else 10
                }, level="info")

            # Execute operation with current timeout
            result = operation(current_timeout_ms)

            # Article I: Validate completeness if enabled
            if config.completeness_check:
                is_complete, indicator = _validate_completeness(result)
                if not is_complete:
                    if config.telemetry_enabled:
                        emit(f"{telemetry_prefix}_incomplete_output", {
                            "attempt": attempt + 1,
                            "indicator": indicator
                        }, level="warning")
                    last_result = result
                    continue  # Retry with next timeout

            # Success - emit telemetry and return
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            if config.telemetry_enabled:
                emit(f"{telemetry_prefix}_timeout_success", {
                    "attempts": attempt + 1,
                    "elapsed_ms": elapsed_ms,
                    "final_timeout_ms": current_timeout_ms
                }, level="info")

            return Ok(result)

        except TimeoutException as e:
            # Timeout occurred - log and retry if attempts remain
            if config.telemetry_enabled:
                emit(f"{telemetry_prefix}_timeout_retry", {
                    "attempt": attempt + 1,
                    "timeout_ms": current_timeout_ms,
                    "max_retries": config.max_retries
                }, level="warning")

            last_result = e

            # Article I: Brief pause for analysis before retry
            if attempt < config.max_retries - 1:
                time.sleep(config.pause_between_retries_sec)
                continue
            else:
                # Final attempt failed
                elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                if config.telemetry_enabled:
                    emit(f"{telemetry_prefix}_timeout_exhausted", {
                        "attempts": config.max_retries,
                        "elapsed_ms": elapsed_ms
                    }, level="error")

                return Err(TimeoutExhaustedError(
                    attempts=config.max_retries,
                    total_time_ms=elapsed_ms,
                    last_error=e
                ))

    # Should never reach here, but handle gracefully
    return Err(TimeoutExhaustedError(
        attempts=config.max_retries,
        total_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
        last_error=None
    ))
```

### Completeness Validation (from bash.py)

```python
def _validate_completeness(result: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate if operation result appears complete (Article I: Context Verification).

    Returns:
        Tuple[is_complete, incomplete_indicator]
    """
    # Handle different result types
    result_str = str(result)

    # Check for common incomplete output indicators
    incomplete_indicators = [
        'Terminated',
        'Killed',
        '... (truncated)',
        'Connection timed out',
        'Resource temporarily unavailable',
        'Signal received',
        'Process interrupted'
    ]

    for indicator in incomplete_indicators:
        if indicator in result_str:
            return (False, indicator)

    return (True, None)
```

### Decorator Implementation

```python
import functools
from typing import TypeVar, Callable, Optional

T = TypeVar('T')

def with_constitutional_timeout(
    config: Optional[TimeoutConfig] = None,
    telemetry_prefix: str = "tool"
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator factory for constitutional timeout compliance.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Get config from tool instance if available
            actual_config = config
            if actual_config is None and args and hasattr(args[0], 'timeout_config'):
                actual_config = args[0].timeout_config
            if actual_config is None:
                actual_config = TimeoutConfig()  # Use defaults

            # Extract tool name for telemetry
            tool_name = telemetry_prefix
            if args and hasattr(args[0], '__class__'):
                tool_name = args[0].__class__.__name__.lower()

            # Wrap the original function in timeout retry logic
            def operation_wrapper(timeout_ms: int) -> T:
                # Inject timeout into function if it accepts it
                if 'timeout' in func.__code__.co_varnames:
                    kwargs['timeout'] = timeout_ms
                return func(*args, **kwargs)

            # Execute with constitutional timeout pattern
            result = _execute_with_retry(
                operation=operation_wrapper,
                config=actual_config,
                telemetry_prefix=tool_name
            )

            # Unwrap Result or raise error
            if result.is_ok():
                return result.unwrap()
            else:
                raise result.unwrap_err()

        return wrapper

    return decorator
```

---

## Migration Plan

### Phase 1: Foundation (Week 1)
**Objective**: Create and test timeout wrapper infrastructure

**Tasks**:
1. Implement `shared/timeout_wrapper.py` with all components
2. Create comprehensive unit tests (test coverage >95%)
3. Add integration test with mock tool
4. Document API in docstrings
5. Update constitution compliance checker

**Deliverables**:
- `shared/timeout_wrapper.py` (fully tested)
- `tests/shared/test_timeout_wrapper.py` (95%+ coverage)
- `docs/guides/timeout-wrapper-usage.md` (migration guide)

**Success Criteria**:
- All unit tests passing
- Integration test demonstrates 1x→10x retry progression
- Telemetry events captured correctly

---

### Phase 2: Critical Tools (Week 2)
**Objective**: Migrate top 10 critical tools (highest timeout risk)

**Tool Prioritization** (based on subprocess usage and timeout risk):

| Priority | Tool | Timeout Risk | Migration Effort | Current Timeout |
|----------|------|--------------|------------------|-----------------|
| 1 | `grep.py` | HIGH | 15 min | None |
| 2 | `bash.py` | MEDIUM | 30 min (refactor) | Full (reference) |
| 3 | `apply_and_verify_patch.py` | HIGH | 20 min | None |
| 4 | `git_workflow.py` | HIGH | 20 min | Partial |
| 5 | `document_generator.py` | MEDIUM | 15 min | None |
| 6 | `read.py` | LOW | 10 min | None |
| 7 | `edit.py` | LOW | 10 min | None |
| 8 | `multi_edit.py` | MEDIUM | 15 min | None |
| 9 | `auto_fix_nonetype.py` | MEDIUM | 15 min | None |
| 10 | `analyze_type_patterns.py` | MEDIUM | 15 min | None |

**Migration Pattern** (Example: `grep.py`):

**Before**:
```python
class Grep(BaseTool):
    def run(self):
        cmd = ["rg", self.pattern]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout
```

**After**:
```python
from shared.timeout_wrapper import with_constitutional_timeout, TimeoutConfig

class Grep(BaseTool):
    timeout_config = TimeoutConfig(
        base_timeout_ms=30000,  # 30 seconds base (current hardcoded value)
        completeness_check=True
    )

    @with_constitutional_timeout()
    def run(self):
        cmd = ["rg", self.pattern]
        # timeout now passed via wrapper, remove hardcoded timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout/1000)
        return result.stdout
```

**Changes Required**: 3 lines added, 1 line modified → ~5 minutes per tool

**Validation**:
- Run tool's existing test suite (must maintain 100% pass rate)
- Add timeout retry test case
- Verify telemetry events emitted

---

### Phase 3: Remaining Tools (Week 3)
**Objective**: Achieve 100% tool coverage

**Batch Migration**:
- Tools 11-20: File operations (`write.py`, `glob.py`, `ls.py`, etc.)
- Tools 21-30: Specialized tools (`todo_write.py`, `constitution_check.py`, etc.)
- Tools 31-35: Utility tools (`undo_snapshot.py`, `learning_dashboard.py`, etc.)

**Parallel Execution**: Migrate 5 tools/day × 5 tools = 25 tools in 5 days

**Quality Gates**:
- Each tool migration must pass existing tests
- New timeout retry test added per tool
- Telemetry validated in integration tests
- Article I compliance score updated daily

---

### Phase 4: Validation & Optimization (Week 4)
**Objective**: Verify 100% compliance and optimize performance

**Tasks**:
1. Run full test suite (1,562 tests) - must maintain 100% pass rate
2. Analyze telemetry data for timeout patterns
3. Optimize timeout multipliers based on real data
4. Update learning agent with timeout pattern extraction
5. Generate compliance audit report

**Success Metrics**:
- Article I compliance: 90 → 100 (target achieved)
- Tool coverage: 6% → 100% (target achieved)
- Test pass rate: 100% (maintained)
- Zero regressions introduced

---

## Rollout Strategy

### Incremental Deployment (Low Risk)

**Week 1**: Foundation only (no tool changes)
- Deploy `shared/timeout_wrapper.py`
- Run tests to verify no side effects
- Enable telemetry monitoring

**Week 2**: Critical tools (10 tools, 29% coverage)
- Deploy high-risk tools first
- Monitor telemetry for timeout events
- Rollback mechanism ready (revert decorator, restore hardcoded timeout)

**Week 3**: Bulk migration (25 tools, 100% coverage)
- Batch deployments (5 tools/day)
- Daily compliance score tracking
- Immediate rollback if test failures

**Week 4**: Optimization & audit
- Learning integration
- Performance tuning
- Compliance certification

### Rollback Plan

**Scenario**: Tool migration causes test failures

**Rollback Steps** (< 5 minutes):
1. Remove `@with_constitutional_timeout` decorator
2. Restore hardcoded `timeout=X` parameter
3. Run tool's test suite to verify rollback success
4. Investigate root cause (timeout too short, completeness check too strict)

**Example Rollback** (`grep.py`):
```python
# Rollback: Remove decorator
# @with_constitutional_timeout()  # DISABLED - rollback
def run(self):
    # Restore hardcoded timeout
    result = subprocess.run(cmd, timeout=30)  # Hardcoded 30s (rollback)
```

---

## Testing Strategy

### 1. Unit Tests (`tests/shared/test_timeout_wrapper.py`)

**Coverage Targets**: >95%

**Test Cases**:
```python
class TestConstitutionalTimeoutWrapper:
    """Unit tests for timeout wrapper components."""

    def test_decorator_basic_success(self):
        """Test decorator with operation that succeeds on first attempt."""
        @with_constitutional_timeout()
        def fast_operation():
            return "success"

        result = fast_operation()
        assert result == "success"

    def test_decorator_retry_then_success(self):
        """Test decorator retries on timeout, succeeds on 2nd attempt."""
        attempt_count = 0

        @with_constitutional_timeout()
        def slow_operation(timeout=None):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise subprocess.TimeoutExpired("cmd", timeout)
            return "success_after_retry"

        result = slow_operation()
        assert result == "success_after_retry"
        assert attempt_count == 2

    def test_timeout_multipliers_progression(self):
        """Verify timeout multipliers follow Article I pattern (1x→2x→3x→5x→10x)."""
        config = TimeoutConfig(base_timeout_ms=1000)
        expected_timeouts = [1000, 2000, 3000, 5000, 10000]

        actual_timeouts = []

        @with_constitutional_timeout(config=config)
        def failing_operation(timeout=None):
            actual_timeouts.append(timeout)
            raise subprocess.TimeoutExpired("cmd", timeout)

        with pytest.raises(TimeoutExhaustedError):
            failing_operation()

        assert actual_timeouts == expected_timeouts

    def test_completeness_validation_incomplete(self):
        """Test completeness check detects truncated output."""
        @with_constitutional_timeout()
        def truncated_operation():
            return "Output... (truncated)"

        with pytest.raises(IncompleteContextError) as exc:
            truncated_operation()

        assert "truncated" in str(exc.value).lower()

    def test_telemetry_events_emitted(self):
        """Verify telemetry events emitted for retry attempts."""
        from core.telemetry import get_telemetry

        telemetry = get_telemetry()

        @with_constitutional_timeout()
        def operation_with_retry(timeout=None):
            # Succeed on first attempt
            return "success"

        operation_with_retry()

        # Verify success event logged
        events = telemetry.query(event_filter="timeout_success", limit=10)
        assert len(events) >= 1
        assert events[0]["data"]["attempts"] == 1

    def test_result_pattern_integration(self):
        """Test run_with_constitutional_timeout returns Result<T,E>."""
        config = TimeoutConfig(base_timeout_ms=1000, max_retries=2)

        # Success case
        result = run_with_constitutional_timeout(
            operation=lambda timeout_ms: "success",
            config=config
        )
        assert result.is_ok()
        assert result.unwrap() == "success"

        # Failure case
        def always_timeout(timeout_ms):
            raise subprocess.TimeoutExpired("cmd", timeout_ms)

        result = run_with_constitutional_timeout(
            operation=always_timeout,
            config=config
        )
        assert result.is_err()
        assert isinstance(result.unwrap_err(), TimeoutExhaustedError)
```

### 2. Integration Tests (`tests/tools/test_timeout_integration.py`)

**Test Real Tools**:
```python
class TestToolTimeoutIntegration:
    """Integration tests for tools using timeout wrapper."""

    def test_grep_timeout_retry(self):
        """Test grep.py with timeout wrapper on large codebase."""
        grep = Grep(pattern="def.*timeout", path="/Users/am/Code/Agency")

        # Should succeed (possibly after retry)
        result = grep.run()
        assert "timeout" in result.lower()

    def test_bash_timeout_compatibility(self):
        """Test bash.py maintains existing timeout behavior."""
        bash = Bash(command="sleep 0.5 && echo 'done'", timeout=120000)

        result = bash.run()
        assert "done" in result
        assert "Exit code: 0" in result

    def test_apply_patch_test_timeout(self):
        """Test apply_and_verify_patch with long test suite."""
        # Create dummy patch that takes time to test
        tool = ApplyAndVerifyPatch(
            file_path="dummy.py",
            original_code="x = 1",
            fixed_code="x = 2",
            error_description="Test timeout handling"
        )

        # Should handle test execution with constitutional timeout
        result = tool.run()
        # Verify result format (success or failure, but not timeout)
        assert "timeout" not in result.lower() or "success" in result.lower()
```

### 3. Performance Benchmarks

**Measure Impact**:
```python
def benchmark_timeout_overhead():
    """Measure performance overhead of timeout wrapper."""

    import time

    # Baseline: no wrapper
    def fast_func():
        return "result"

    start = time.perf_counter()
    for _ in range(1000):
        fast_func()
    baseline_ms = (time.perf_counter() - start) * 1000

    # With wrapper
    @with_constitutional_timeout()
    def wrapped_func():
        return "result"

    start = time.perf_counter()
    for _ in range(1000):
    wrapped_func()
    wrapped_ms = (time.perf_counter() - start) * 1000

    overhead_pct = ((wrapped_ms - baseline_ms) / baseline_ms) * 100

    # Overhead should be < 5% for fast operations
    assert overhead_pct < 5.0, f"Timeout wrapper overhead too high: {overhead_pct:.2f}%"
```

**Expected Results**:
- Fast operations (< 100ms): Overhead < 5%
- Medium operations (1-10s): Overhead < 1%
- Slow operations (> 10s): Overhead negligible (< 0.1%)

---

## Success Metrics

### Primary Metrics (Constitutional Compliance)

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Article I Compliance Score | 90/100 | 100/100 | Constitution checker |
| Tools with timeout retry | 2/35 (6%) | 35/35 (100%) | Code analysis |
| Test pass rate | 100% | 100% | `run_tests.py --run-all` |
| Zero regressions | N/A | 0 failures | Integration tests |

### Secondary Metrics (Learning & Optimization)

| Metric | Target | Source |
|--------|--------|--------|
| Timeout events logged | >100/day | Telemetry |
| Retry success rate | >80% | Telemetry analysis |
| Average retries to success | <2 attempts | Telemetry |
| Timeout pattern learnings | >5 patterns | Learning agent |

### Telemetry Dashboard (Article IV Integration)

**Metrics to Track**:
```python
# Timeout retry distribution
{
    "tool": "grep",
    "retry_attempts": [1, 2, 1, 1, 3, 1, 2],  # Per operation
    "avg_retries": 1.57,
    "success_rate": 1.0  # 100% eventually succeeded
}

# Timeout optimization recommendations
{
    "tool": "apply_and_verify_patch",
    "current_base_timeout_ms": 120000,
    "recommended_base_timeout_ms": 180000,  # Learning suggests 3min better
    "rationale": "95% of operations complete within 2.5min, current timeout too aggressive"
}
```

---

## Consequences

### Positive Consequences

1. **Article I Compliance**: Achieves 100/100 constitutional compliance (90 → 100)
2. **Tool Reliability**: 35 tools gain automatic retry on timeout
3. **Consistent Behavior**: All tools follow identical retry logic (no variance)
4. **Learning Integration**: Telemetry enables Article IV pattern extraction
5. **Zero Broken Windows**: No partial results, no incomplete context violations
6. **Minimal Code Changes**: Average 5 lines changed per tool (175 lines total vs 1,750 if duplicated)
7. **Easy Testing**: Decorator testable in isolation, high confidence in coverage
8. **Future-Proof**: New tools automatically compliant by adding decorator

### Negative Consequences

1. **Performance Overhead**: ~2-5% overhead for fast operations (< 100ms)
   - **Mitigation**: Acceptable trade-off for constitutional compliance
   - **Evidence**: bash.py already demonstrates negligible impact

2. **Increased Execution Time**: Operations may take 21x base timeout in worst case
   - **Mitigation**: Only affects failing operations (would fail anyway)
   - **Evidence**: Article I mandates complete context over speed

3. **Telemetry Volume**: +300-500 events/day (timeout attempts logged)
   - **Mitigation**: SimpleTelemetry handles this (10-run retention)
   - **Evidence**: Article IV requires learning data

4. **Migration Effort**: ~35 tools × 15 min = 8.75 hours total developer time
   - **Mitigation**: Spread over 3 weeks, low risk per-tool
   - **Evidence**: Proven migration pattern from bash.py

### Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tool tests fail after migration | MEDIUM | HIGH | Rollback plan (< 5 min), comprehensive testing |
| Timeout too short for some tools | LOW | MEDIUM | Per-tool TimeoutConfig customization |
| Completeness check too strict | LOW | MEDIUM | Configurable via `completeness_check=False` |
| Performance degradation | LOW | LOW | Benchmarks validate < 5% overhead |
| Telemetry storage growth | LOW | LOW | SimpleTelemetry retention handles this |

---

## Implementation Checklist

### Phase 1: Foundation ✅
- [ ] Create `shared/timeout_wrapper.py` with all components
- [ ] Implement `TimeoutConfig` Pydantic model
- [ ] Implement `@with_constitutional_timeout` decorator
- [ ] Implement `run_with_constitutional_timeout()` function
- [ ] Implement `@with_constitutional_timeout_async` async decorator
- [ ] Implement completeness validation logic
- [ ] Implement telemetry integration
- [ ] Create error classes (`TimeoutExhaustedError`, `IncompleteContextError`)
- [ ] Write unit tests (target: >95% coverage)
- [ ] Write integration tests
- [ ] Write performance benchmarks
- [ ] Document API in docstrings
- [ ] Create migration guide (`docs/guides/timeout-wrapper-usage.md`)
- [ ] Update constitution compliance checker
- [ ] Verify no regressions (run full test suite)

### Phase 2: Critical Tools (Week 2) ✅
- [ ] Migrate `grep.py` + tests
- [ ] Refactor `bash.py` to use wrapper + tests
- [ ] Migrate `apply_and_verify_patch.py` + tests
- [ ] Migrate `git_workflow.py` + tests
- [ ] Migrate `document_generator.py` + tests
- [ ] Migrate `read.py` + tests
- [ ] Migrate `edit.py` + tests
- [ ] Migrate `multi_edit.py` + tests
- [ ] Migrate `auto_fix_nonetype.py` + tests
- [ ] Migrate `analyze_type_patterns.py` + tests
- [ ] Verify telemetry events for each tool
- [ ] Run integration tests for migrated tools
- [ ] Update compliance score (should reach ~30/35 = 86%)

### Phase 3: Remaining Tools (Week 3) ✅
- [ ] Migrate tools 11-20 (file operations)
- [ ] Migrate tools 21-30 (specialized)
- [ ] Migrate tools 31-35 (utility)
- [ ] Verify 100% tool coverage
- [ ] Run full test suite (1,562 tests)
- [ ] Update compliance score (should reach 100%)

### Phase 4: Validation (Week 4) ✅
- [ ] Analyze telemetry data (1 week of production usage)
- [ ] Optimize timeout multipliers if needed
- [ ] Integrate with learning agent
- [ ] Generate compliance audit report
- [ ] Update ADR-INDEX.md
- [ ] Update constitution compliance tracker
- [ ] Celebrate 100/100 Article I compliance 🎉

---

## References

### Constitutional References
- **Article I Section 1.2**: Timeout Handling (constitution.md lines 27-31)
- **Article I Section 1.3**: Implementation Requirements (constitution.md lines 50-72)
- **Article II**: 100% Verification and Stability (constitution.md lines 76-117)
- **Article IV**: Continuous Learning (constitution.md lines 161-203)

### Related ADRs
- **ADR-001**: Complete Context Before Action (constitutional basis)
- **ADR-002**: 100% Verification and Stability (test coverage requirements)
- **ADR-004**: Continuous Learning (telemetry integration)
- **ADR-010**: Result Pattern for Error Handling (error return type)

### Implementation References
- **bash.py lines 535-599**: Proven constitutional timeout implementation
- **core/telemetry.py**: SimpleTelemetry API for event logging
- **shared/type_definitions/result.py**: Result<T,E> pattern

### External Documentation
- Python `subprocess.TimeoutExpired` exception handling
- Python decorators and `functools.wraps`
- Pydantic configuration models
- Exponential backoff best practices

---

**Author**: ChiefArchitectAgent (Trinity Protocol)
**Date**: 2025-10-02
**Status**: Accepted
**Implementation Target**: Q4 2025 (4 weeks)
**Constitutional Impact**: Article I compliance 90 → 100
