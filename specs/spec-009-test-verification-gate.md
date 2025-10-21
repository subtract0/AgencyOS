# Specification: Test Verification Gate

**Spec ID**: `spec-009-test-verification-gate`
**Status**: `Draft`
**Author**: ChiefArchitectAgent
**Created**: 2025-10-11
**Last Updated**: 2025-10-11
**Related Plan**: `plan-009-test-verification-gate.md` (to be created)
**Related ADRs**: `ADR-001` (Complete Context), `ADR-002` (100% Verification), `ADR-023` (Memory-Aware Execution)

---

## Executive Summary

Define a mandatory test verification checkpoint that runs after all Code task completions with constitutional retry logic (2x, 3x, up to 10x timeout), memory-aware worker calculation, automatic rollback on failure, and integration with TodoWrite progress tracking. This checkpoint enforces Articles I & II by ensuring 100% test pass rate with complete context before proceeding to subsequent tasks.

**Problem**: Current workflows allow proceeding without full test verification, violating Article II's 100% verification requirement and creating broken windows.

**Solution**: Mandatory test gate that blocks progression until all tests pass, with intelligent retry on timeout (Article I) and memory-safe parallel execution (ADR-023).

---

## Goals

### Primary Goals

- **Goal 1**: Enforce 100% test pass rate as mandatory gate (Article II compliance)
- **Goal 2**: Implement constitutional retry logic (2x, 3x, up to 10x timeout on incomplete results per Article I)
- **Goal 3**: Integrate memory-aware worker calculation preventing system crashes during test execution
- **Goal 4**: Provide automatic rollback strategy on test failure to last known good state

### Success Metrics

- **Gate Enforcement**: 100% of Code tasks blocked until tests pass (no bypass mechanisms)
- **Complete Context**: >95% of test runs complete without timeout (Article I: retry until completion)
- **Memory Safety**: 0 kernel panics or OOM errors during test execution (ADR-023 compliance)
- **Rollback Success**: >98% of failed gates successfully rollback to pre-change state
- **Integration Success**: TodoWrite task state accurately reflects test gate status (in_progress, completed, failed)

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Test generation or test quality assessment (delegated to TestGeneratorAgent)
- **Non-Goal 2**: Pre-commit git hooks (this is a workflow-level gate, not git-level)
- **Non-Goal 3**: Parallel test execution optimization beyond memory-aware worker calculation
- **Non-Goal 4**: Test result caching or incremental test running (run all tests every time)

### Future Considerations

- **Future Enhancement 1**: Intelligent test subset selection based on changed files (for faster feedback)
- **Future Enhancement 2**: Test flakiness detection and retry logic for known flaky tests
- **Future Enhancement 3**: Visual test progress dashboard with real-time pass/fail updates
- **Future Enhancement 4**: Integration with CI/CD pipeline for branch protection enforcement

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: CodingAgent (Primary User)
- **Description**: Primary development agent implementing features and fixes
- **Goals**: Complete tasks efficiently while maintaining 100% test pass rate
- **Pain Points**: Proceeding with broken tests wastes time debugging later, unclear when tests are "done"
- **Technical Proficiency**: Autonomous agent with access to all tools

#### Persona 2: QualityEnforcerAgent (Secondary User)
- **Description**: Constitutional compliance guardian ensuring quality gates enforced
- **Goals**: Verify all code changes meet Article I & II standards before merge
- **Pain Points**: Manual verification is error-prone, needs automated enforcement
- **Technical Proficiency**: Autonomous agent with healing capabilities

#### Persona 3: Development Team (Tertiary User)
- **Description**: Human engineers reviewing agent-generated code and test results
- **Goals**: Trust that code quality is guaranteed by automated gates
- **Pain Points**: Need clear signals when gates pass/fail, want automatic rollback on failure
- **Technical Proficiency**: Senior engineers familiar with constitution

### User Journeys

#### Journey 1: Code Task with Test Verification (Primary Use Case - Success Path)
```
1. CodingAgent starts with: TodoWrite task "Implement feature X" marked in_progress
2. Agent performs:
   - Writes tests first (TDD mandate)
   - Implements feature code
   - Marks task as complete in TodoWrite
3. Test Verification Gate triggers:
   - Calculates memory-aware worker count (3 if local model ON, 10 if OFF)
   - Runs `python run_tests.py --run-all` with 120s base timeout
   - Tests complete successfully: 1,725 passed, 0 failed (100% pass rate)
4. Gate validation:
   - Article I: ✅ Complete context (all tests ran to completion)
   - Article II: ✅ 100% verification (pass rate == 1.0)
   - Memory safety: ✅ No crashes, 38GB peak memory usage (safe for 48GB Mac)
5. Gate outcome:
   - Status: PASS ✅
   - TodoWrite task state: completed
   - Next task: Proceeds to next task in queue
6. Agent achieves: Feature implemented with guaranteed quality
```

#### Journey 2: Code Task with Timeout Retry (Article I Retry Path)
```
1. CodingAgent starts with: TodoWrite task "Fix performance bug" marked in_progress
2. Agent performs: Code changes, marks task complete
3. Test Verification Gate triggers:
   - Attempt 1: timeout=120s → TIMEOUT (VectorStore initialization slow)
   - Gate detects: Incomplete results (Article I violation detected)
4. Constitutional retry (Article I):
   - Attempt 2: timeout=240s (2x multiplier) → SUCCESS
   - Tests complete: 1,725 passed, 0 failed
5. Gate validation:
   - Article I: ✅ Complete context (retry achieved full results)
   - Article II: ✅ 100% verification
6. Gate outcome: PASS ✅ (after retry)
7. Agent achieves: Complete verification despite initial timeout
```

#### Journey 3: Code Task with Test Failures (Article II Failure Path)
```
1. CodingAgent starts with: TodoWrite task "Add authentication" marked in_progress
2. Agent performs: Code changes, marks task complete
3. Test Verification Gate triggers:
   - Memory-aware workers: 3 (local model active)
   - Runs tests with 120s timeout → SUCCESS (complete)
   - Test results: 1,722 passed, 3 failed (99.8% pass rate)
4. Gate validation:
   - Article I: ✅ Complete context (tests ran to completion)
   - Article II: ❌ BLOCKED (pass rate < 100%)
5. Gate outcome:
   - Status: FAIL ❌
   - TodoWrite task state: in_progress (reverted from completed)
   - Rollback: git restore --staged . && git restore .
6. Agent receives:
   - Failure report with 3 failing test names
   - Remediation guidance: "Fix failing tests before proceeding"
   - Blocking signal: Cannot proceed to next task
7. Agent must: Fix the 3 failing tests, re-trigger gate
```

#### Journey 4: Memory Exhaustion Prevention (ADR-023 Safety Path)
```
1. CodingAgent starts with: TodoWrite task "Optimize search" marked in_progress
2. Agent performs: Code changes in VectorStore module
3. Test Verification Gate triggers:
   - System state: Ollama running (Qwen3-Coder Q8_0, 38GB loaded)
   - Available memory: 12GB (48GB - 38GB model - 8GB system)
   - Memory-aware calculation: 3 workers (9GB budget, safe)
4. Gate execution:
   - Runs tests with reduced parallelism: pytest -n 3
   - Memory usage: 38GB (model) + 9GB (tests) + 8GB (system) = 47GB peak
   - Result: SUCCESS, no kernel panic
5. Gate validation:
   - Article I: ✅ Complete context
   - Article II: ✅ 100% pass rate
   - Memory safety: ✅ No OOM, stayed under 48GB limit
6. Agent achieves: Test execution without system crash
```

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CodingAgent Workflow                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. TodoWrite: Mark task in_progress                  │   │
│  │ 2. Write tests (TDD)                                 │   │
│  │ 3. Implement code                                    │   │
│  │ 4. Mark task complete → TRIGGER TEST GATE           │   │
│  └────────────────────┬─────────────────────────────────┘   │
└────────────────────────┼──────────────────────────────────────┘
                         │
        ┌────────────────▼────────────────────────────────────┐
        │       Test Verification Gate (Mandatory)           │
        │  ┌──────────────────────────────────────────────┐  │
        │  │ Phase 1: Pre-Execution Analysis              │  │
        │  │  - Check Ollama running (local model state)  │  │
        │  │  - Calculate memory-aware worker count       │  │
        │  │  - Validate 5GB+ memory available            │  │
        │  └────────────┬─────────────────────────────────┘  │
        │               │                                     │
        │  ┌────────────▼─────────────────────────────────┐  │
        │  │ Phase 2: Test Execution with Retry           │  │
        │  │  - Attempt 1: timeout=120s (2 min)           │  │
        │  │  - If timeout: Attempt 2 (timeout=240s, 2x)  │  │
        │  │  - If timeout: Attempt 3 (timeout=360s, 3x)  │  │
        │  │  - If timeout: Attempt 4 (timeout=600s, 5x)  │  │
        │  │  - If timeout: Attempt 5 (timeout=1200s, 10x)│  │
        │  │  - Max retries: 5 (Article I: up to 10x)     │  │
        │  └────────────┬─────────────────────────────────┘  │
        │               │                                     │
        │  ┌────────────▼─────────────────────────────────┐  │
        │  │ Phase 3: Result Validation                   │  │
        │  │  - Article I: Tests completed? (no timeout)  │  │
        │  │  - Article II: Pass rate == 100%?            │  │
        │  │  - Parse pytest JSON output for metrics      │  │
        │  └────────────┬─────────────────────────────────┘  │
        │               │                                     │
        │       ┌───────┴────────┐                           │
        │       │                │                           │
        │  ┌────▼─────┐    ┌────▼─────┐                     │
        │  │  PASS ✅  │    │  FAIL ❌  │                     │
        │  └────┬─────┘    └────┬─────┘                     │
        └───────┼───────────────┼────────────────────────────┘
                │               │
     ┌──────────▼────┐   ┌──────▼─────────────────────────┐
     │ Success Path   │   │ Failure Path                   │
     │ - Update       │   │ - Rollback: git restore        │
     │   TodoWrite:   │   │ - Revert TodoWrite: in_progress│
     │   completed    │   │ - Emit failure report          │
     │ - Store        │   │ - Block next task              │
     │   patterns     │   │ - Store failure patterns       │
     │   (Article IV) │   │   (Article IV learning)        │
     │ - Proceed to   │   │ - Agent must fix tests         │
     │   next task    │   │                                │
     └────────────────┘   └────────────────────────────────┘
```

### Integration Points

1. **TodoWrite Tool**: Task state management (in_progress, completed, failed)
2. **memory_aware_test_runner.py**: Worker count calculation (ADR-023)
3. **run_tests.py**: Test execution wrapper with timeout handling
4. **AgentContext/VectorStore**: Pattern storage for learning (Article IV)
5. **Git**: Rollback mechanism on test failure

---

## Detailed Design

### 1. Test Verification Gate Configuration

**Pydantic Model** (`shared/models/test_verification_config.py`):

```python
from pydantic import BaseModel, Field
from typing import Literal


class TestVerificationConfig(BaseModel):
    """Configuration for test verification gate (Articles I & II compliance)."""

    base_timeout_ms: int = Field(
        default=120000,
        description="Base timeout in milliseconds (2 minutes default)",
        ge=30000,  # Minimum 30 seconds
        le=600000  # Maximum 10 minutes base
    )

    timeout_multipliers: list[int] = Field(
        default=[1, 2, 3, 5, 10],
        description="Article I: Timeout multipliers for retry attempts"
    )

    max_retries: int = Field(
        default=5,
        description="Maximum retry attempts (matches timeout_multipliers length)",
        ge=1,
        le=10
    )

    required_pass_rate: float = Field(
        default=1.0,
        description="Article II: Required test pass rate (1.0 = 100%, non-negotiable)",
        ge=1.0,
        le=1.0  # Enforces exactly 1.0 (100%)
    )

    memory_safety_check: bool = Field(
        default=True,
        description="Enable memory-aware worker calculation (ADR-023)"
    )

    rollback_on_failure: bool = Field(
        default=True,
        description="Automatically rollback git changes on test failure"
    )

    test_scope: Literal["all", "unit", "integration", "fast"] = Field(
        default="all",
        description="Test scope to run (default: all tests)"
    )


class TestVerificationResult(BaseModel):
    """Result of test verification gate execution."""

    gate_passed: bool = Field(description="True if all validation criteria met")
    article_i_compliant: bool = Field(
        description="Tests ran to completion (no timeout)"
    )
    article_ii_compliant: bool = Field(
        description="100% test pass rate achieved"
    )

    total_tests: int = Field(ge=0)
    passed_tests: int = Field(ge=0)
    failed_tests: int = Field(ge=0)
    pass_rate: float = Field(ge=0.0, le=1.0)

    duration_seconds: float = Field(ge=0.0)
    retry_attempts: int = Field(ge=1, le=10)
    timeout_multiplier_used: int = Field(ge=1, le=10)

    memory_safe: bool = Field(
        description="Execution completed without memory exhaustion"
    )
    worker_count_used: int = Field(ge=1, le=10)

    rollback_performed: bool = Field(default=False)
    failure_report: str | None = Field(default=None)

    blocking_reason: str | None = Field(
        default=None,
        description="Reason for blocking (if gate_passed=False)"
    )
```

### 2. Memory-Aware Worker Calculation (from ADR-023)

**Integration with `memory_aware_test_runner.py`**:

```python
from tools.memory_aware_test_runner import (
    get_safe_worker_count,
    verify_memory_safe,
    check_ollama_running
)


def calculate_test_workers() -> tuple[int, bool, str]:
    """
    Calculate safe pytest worker count based on system state.

    Returns:
        Tuple of (worker_count, memory_safe, rationale)

    Constitutional Compliance:
    - Article I: Prevents incomplete execution from memory crashes
    - Article II: Ensures stable test environment
    - ADR-023: Hardware-aware execution
    """
    import psutil

    # Get current system state
    mem = psutil.virtual_memory()
    available_gb = mem.available / (1024 ** 3)
    local_model_active = check_ollama_running()

    # Safety check: require 5GB+ available memory
    if not verify_memory_safe(required_gb=5):
        return (1, False, f"Critical memory: {available_gb:.1f}GB available, "
                          "forcing sequential execution")

    # Calculate safe worker count
    worker_count = get_safe_worker_count()

    # Build rationale
    if local_model_active:
        rationale = (f"Local model active (Ollama running), using {worker_count} "
                    f"workers to prevent memory exhaustion (available: {available_gb:.1f}GB)")
    else:
        rationale = (f"Local model OFF, using {worker_count} workers "
                    f"(available: {available_gb:.1f}GB)")

    memory_safe = available_gb >= 10.0  # Require 10GB+ for "safe" status

    return (worker_count, memory_safe, rationale)
```

### 3. Test Execution with Constitutional Retry

**Core retry logic implementing Article I**:

```python
import subprocess
import time
from datetime import datetime
from shared.type_definitions.result import Result, Ok, Err


def execute_tests_with_retry(
    config: TestVerificationConfig
) -> Result[TestVerificationResult, str]:
    """
    Execute tests with Article I constitutional retry logic.

    Retry pattern: 1x → 2x → 3x → 5x → 10x timeout multipliers
    Maximum total time: 21x base timeout (e.g., 42 minutes with 2-min base)

    Returns:
        Result[TestVerificationResult, str]: Ok(result) or Err(error_message)
    """
    start_time = datetime.now()
    last_error = None

    # Calculate workers and memory state
    worker_count, memory_safe, worker_rationale = calculate_test_workers()

    print(f"🧪 Test Verification Gate: Starting")
    print(f"   Workers: {worker_count} ({worker_rationale})")
    print(f"   Scope: {config.test_scope}")
    print(f"   Base timeout: {config.base_timeout_ms / 1000}s")

    for attempt in range(config.max_retries):
        # Calculate timeout for this attempt
        multiplier = config.timeout_multipliers[attempt]
        timeout_ms = config.base_timeout_ms * multiplier
        timeout_seconds = timeout_ms / 1000

        print(f"\n📋 Attempt {attempt + 1}/{config.max_retries}: "
              f"timeout={timeout_seconds:.0f}s ({multiplier}x)")

        # Build pytest command
        cmd = _build_test_command(config.test_scope, worker_count)

        try:
            # Execute tests with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=_get_test_environment()
            )

            # Parse test results
            metrics = _parse_test_output(result.stdout, result.stderr)

            # Calculate elapsed time
            elapsed_seconds = (datetime.now() - start_time).total_seconds()

            # Article I: Validate completeness
            is_complete = _validate_completeness(result, metrics)
            if not is_complete:
                print(f"⚠️  Incomplete results detected, retrying...")
                last_error = "Incomplete test execution"
                time.sleep(2.0)  # Brief pause for analysis (Article I)
                continue

            # Article II: Validate 100% pass rate
            pass_rate = (metrics["passed"] / metrics["total"]
                        if metrics["total"] > 0 else 0.0)

            article_ii_compliant = pass_rate >= config.required_pass_rate

            # Build result
            verification_result = TestVerificationResult(
                gate_passed=(is_complete and article_ii_compliant),
                article_i_compliant=is_complete,
                article_ii_compliant=article_ii_compliant,
                total_tests=metrics["total"],
                passed_tests=metrics["passed"],
                failed_tests=metrics["failed"],
                pass_rate=pass_rate,
                duration_seconds=elapsed_seconds,
                retry_attempts=attempt + 1,
                timeout_multiplier_used=multiplier,
                memory_safe=memory_safe,
                worker_count_used=worker_count,
                rollback_performed=False,  # Will be set by caller
                failure_report=None if article_ii_compliant else _build_failure_report(result),
                blocking_reason=None if (is_complete and article_ii_compliant)
                               else _get_blocking_reason(is_complete, pass_rate)
            )

            # Success path: tests completed
            return Ok(verification_result)

        except subprocess.TimeoutExpired as e:
            # Timeout occurred - retry with next multiplier
            print(f"⏱️  Timeout after {timeout_seconds}s")
            last_error = f"Timeout after {timeout_seconds}s"

            if attempt < config.max_retries - 1:
                print(f"   Retrying with {config.timeout_multipliers[attempt + 1]}x timeout...")
                time.sleep(2.0)  # Article I: pause for analysis
                continue
            else:
                # Exhausted all retries
                elapsed_seconds = (datetime.now() - start_time).total_seconds()
                return Err(
                    f"Article I violation: Tests timed out after {config.max_retries} "
                    f"attempts ({elapsed_seconds:.1f}s total). "
                    f"Unable to obtain complete context."
                )

        except Exception as e:
            # Unexpected error
            return Err(f"Test execution error: {str(e)}")

    # Should never reach here, but handle gracefully
    return Err(f"Test verification failed after {config.max_retries} attempts: {last_error}")


def _build_test_command(scope: str, worker_count: int) -> list[str]:
    """Build pytest command based on scope and worker count."""
    if scope == "all":
        cmd = ["python", "run_tests.py", "--run-all"]
    elif scope == "unit":
        cmd = ["python", "run_tests.py"]
    elif scope == "integration":
        cmd = ["python", "run_tests.py", "--integration-only"]
    elif scope == "fast":
        cmd = ["python", "run_tests.py", "--fast"]
    else:
        cmd = ["python", "run_tests.py"]

    # Note: worker count already handled by memory_aware_test_runner.py
    # which is integrated into run_tests.py
    return cmd


def _get_test_environment() -> dict:
    """Get environment variables for test execution."""
    import os
    env = os.environ.copy()
    env["AGENCY_NESTED_TEST"] = "1"  # Prevent recursive test runs
    env["PYTHONUNBUFFERED"] = "1"  # Immediate output
    env["TOKENIZERS_PARALLELISM"] = "false"  # Prevent PyTorch segfault (SPEC-021)
    env["OMP_NUM_THREADS"] = "1"  # Limit OpenMP threads
    return env


def _parse_test_output(stdout: str, stderr: str) -> dict:
    """
    Parse pytest output to extract metrics.

    Returns:
        Dict with keys: total, passed, failed, errors
    """
    import re

    # Combine stdout and stderr for parsing
    output = stdout + stderr

    # Python pytest format: "1725 passed, 3 failed in 45.2s"
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    error_match = re.search(r"(\d+) error", output)

    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errors = int(error_match.group(1)) if error_match else 0

    total = passed + failed + errors

    return {
        "total": total,
        "passed": passed,
        "failed": failed + errors  # Combine failures and errors
    }


def _validate_completeness(result: subprocess.CompletedProcess, metrics: dict) -> bool:
    """
    Article I: Validate test execution completed successfully.

    Checks:
    - Exit code 0 or 1 (0 = all passed, 1 = some failed but completed)
    - No truncation indicators in output
    - Metrics parsed successfully
    """
    # Check for incomplete indicators
    incomplete_indicators = [
        'Terminated',
        'Killed',
        '... (truncated)',
        'Connection timed out',
        'Signal received',
        'Process interrupted'
    ]

    output = result.stdout + result.stderr
    for indicator in incomplete_indicators:
        if indicator in output:
            return False

    # Check metrics parsed
    if metrics["total"] == 0:
        return False

    # Exit code validation (0 = success, 1 = tests failed but ran to completion)
    if result.returncode not in [0, 1]:
        return False

    return True


def _build_failure_report(result: subprocess.CompletedProcess) -> str:
    """Build detailed failure report from pytest output."""
    import re

    output = result.stdout + result.stderr

    # Extract failing test names
    # Pytest format: "FAILED tests/test_example.py::test_function - AssertionError: ..."
    failures = re.findall(r"FAILED ([\w/\.]+::\w+)", output)

    report_lines = ["Test Verification Gate: FAILED ❌", ""]

    if failures:
        report_lines.append(f"Failing Tests ({len(failures)}):")
        for i, failure in enumerate(failures, 1):
            report_lines.append(f"  {i}. {failure}")
    else:
        report_lines.append("Unable to parse failure details. Check full output.")

    report_lines.append("")
    report_lines.append("Article II Requirement: 100% test pass rate (no exceptions)")
    report_lines.append("Action Required: Fix failing tests before proceeding")

    return "\n".join(report_lines)


def _get_blocking_reason(is_complete: bool, pass_rate: float) -> str:
    """Get human-readable blocking reason."""
    if not is_complete:
        return "Article I: Incomplete test execution (timed out or truncated)"

    if pass_rate < 1.0:
        return f"Article II: Test pass rate {pass_rate*100:.1f}% (required: 100%)"

    return "Unknown blocking reason"
```

### 4. Rollback Strategy

**Git rollback on test failure**:

```python
import subprocess


def perform_rollback() -> Result[str, str]:
    """
    Rollback git changes to last known good state.

    Rollback steps:
    1. Unstage all changes: git restore --staged .
    2. Discard working directory changes: git restore .
    3. Clean untracked files: git clean -fd (optional, configurable)

    Returns:
        Result[str, str]: Ok(success_message) or Err(error_message)
    """
    try:
        # Step 1: Unstage changes
        result = subprocess.run(
            ["git", "restore", "--staged", "."],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return Err(f"Failed to unstage changes: {result.stderr}")

        # Step 2: Discard working directory changes
        result = subprocess.run(
            ["git", "restore", "."],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return Err(f"Failed to discard changes: {result.stderr}")

        # Optional: Clean untracked files (commented out for safety)
        # result = subprocess.run(
        #     ["git", "clean", "-fd"],
        #     capture_output=True,
        #     text=True,
        #     timeout=10
        # )

        return Ok("Rollback successful: Changes discarded, working directory clean")

    except subprocess.TimeoutExpired:
        return Err("Rollback timeout: Git operations took too long")
    except Exception as e:
        return Err(f"Rollback failed: {str(e)}")
```

### 5. TodoWrite Integration

**Update TodoWrite task state based on gate result**:

```python
def update_todowrite_state(
    task_index: int,
    gate_result: TestVerificationResult
) -> None:
    """
    Update TodoWrite task state based on test verification gate result.

    State transitions:
    - Gate passed: Keep status=completed
    - Gate failed: Revert status=in_progress

    Args:
        task_index: Index of task in TodoWrite list
        gate_result: Result of test verification gate
    """
    from tools.todo_write import read_todos, write_todos

    # Read current todos
    todos = read_todos()

    if task_index >= len(todos):
        print(f"⚠️  Warning: Task index {task_index} out of range")
        return

    task = todos[task_index]

    if gate_result.gate_passed:
        # Gate passed: keep completed status
        task["status"] = "completed"
        print(f"✅ Task '{task['content']}' verified: Tests passed")
    else:
        # Gate failed: revert to in_progress
        task["status"] = "in_progress"
        print(f"❌ Task '{task['content']}' blocked: Tests failed")
        print(f"   Reason: {gate_result.blocking_reason}")

    # Write updated todos
    write_todos(todos)
```

### 6. VectorStore Learning Integration (Article IV)

**Store test verification patterns for learning**:

```python
def store_verification_pattern(
    gate_result: TestVerificationResult,
    task_description: str
) -> None:
    """
    Store test verification pattern in VectorStore for Article IV learning.

    Patterns stored:
    - Successful verifications (confidence: 0.8)
    - Failed verifications (confidence: 0.7, for learning from mistakes)
    - Timeout retry patterns (confidence: 0.6, for timeout optimization)
    """
    from shared.agent_context import get_agent_context

    context = get_agent_context()

    # Build pattern metadata
    pattern_type = "test_verification_success" if gate_result.gate_passed else "test_verification_failure"

    metadata = {
        "pattern_type": pattern_type,
        "task_description": task_description,
        "gate_passed": gate_result.gate_passed,
        "pass_rate": gate_result.pass_rate,
        "retry_attempts": gate_result.retry_attempts,
        "timeout_multiplier": gate_result.timeout_multiplier_used,
        "worker_count": gate_result.worker_count_used,
        "duration_seconds": gate_result.duration_seconds,
        "article_i_compliant": gate_result.article_i_compliant,
        "article_ii_compliant": gate_result.article_ii_compliant,
    }

    # Determine confidence score
    if gate_result.gate_passed and gate_result.retry_attempts == 1:
        confidence = 0.85  # High confidence: passed on first try
    elif gate_result.gate_passed:
        confidence = 0.75  # Medium confidence: passed after retry
    else:
        confidence = 0.65  # Lower confidence: failed (but useful for learning)

    # Store pattern
    context.store_memory(
        key=f"test_verification_{datetime.now().isoformat()}",
        content=metadata,
        tags=["test_verification", "article_i", "article_ii", pattern_type],
        confidence=confidence
    )

    print(f"📚 Stored verification pattern: {pattern_type} (confidence: {confidence})")
```

---

## Implementation Workflow

### Phase 1: Core Gate Implementation (Week 1)

**Tasks**:
1. Create `shared/models/test_verification_config.py` with Pydantic models
2. Implement `tools/test_verification_gate.py` with core logic
3. Integrate with `memory_aware_test_runner.py` for worker calculation
4. Implement constitutional retry logic (1x → 2x → 3x → 5x → 10x)
5. Add rollback mechanism using git restore
6. Write unit tests (target: >90% coverage)

**Deliverables**:
- `shared/models/test_verification_config.py`
- `tools/test_verification_gate.py`
- `tests/test_test_verification_gate.py`

**Success Criteria**:
- All unit tests passing
- Retry logic validated (1x → 10x progression)
- Memory-aware worker calculation working

### Phase 2: TodoWrite Integration (Week 1)

**Tasks**:
1. Add gate trigger after TodoWrite task completion
2. Implement task state reversion on gate failure
3. Add gate result reporting in TodoWrite UI
4. Test integration with sample tasks

**Deliverables**:
- TodoWrite integration code
- Integration tests

**Success Criteria**:
- Task state correctly updates based on gate result
- Failed gates block next task progression

### Phase 3: VectorStore Learning (Week 2)

**Tasks**:
1. Implement pattern storage in VectorStore
2. Add pattern retrieval for timeout optimization
3. Create learning dashboard for verification patterns
4. Test pattern extraction and reuse

**Deliverables**:
- VectorStore integration
- Learning dashboard

**Success Criteria**:
- Patterns stored with correct confidence scores
- Learning dashboard shows verification history

### Phase 4: Agent Integration (Week 2)

**Tasks**:
1. Update CodingAgent to trigger gate after code changes
2. Update QualityEnforcerAgent to use gate for validation
3. Add gate status to agent communication protocol
4. Update agent documentation

**Deliverables**:
- Agent integration code
- Updated agent instructions

**Success Criteria**:
- All agents respect gate enforcement
- No agent can bypass gate (zero override mechanisms)

---

## Acceptance Criteria

### Functional Requirements

1. **Gate Enforcement** ✅
   - [ ] Gate triggers automatically after TodoWrite task marked complete
   - [ ] Gate blocks progression on test failure (Article II)
   - [ ] Gate allows progression only on 100% pass rate
   - [ ] No bypass mechanisms exist

2. **Constitutional Retry** ✅
   - [ ] Implements Article I retry logic (2x, 3x, 5x, 10x)
   - [ ] Retries up to 5 attempts on timeout
   - [ ] Pauses 2 seconds between retries for analysis
   - [ ] Reports retry attempts in result

3. **Memory Safety** ✅
   - [ ] Calculates memory-aware worker count (ADR-023)
   - [ ] Uses 3 workers when local model active
   - [ ] Uses 10 workers when local model inactive
   - [ ] Validates 5GB+ available memory before execution

4. **Rollback** ✅
   - [ ] Performs git restore on test failure
   - [ ] Reverts TodoWrite task state to in_progress
   - [ ] Preserves untracked files (safe rollback)
   - [ ] Reports rollback success/failure

5. **Learning** ✅
   - [ ] Stores verification patterns in VectorStore
   - [ ] Tags patterns with article_i, article_ii
   - [ ] Assigns confidence scores (0.65-0.85)
   - [ ] Enables timeout optimization learning

### Non-Functional Requirements

1. **Performance** ✅
   - [ ] Gate execution overhead < 5 seconds (excluding test time)
   - [ ] Memory usage stays under 48GB limit (ADR-023)
   - [ ] No kernel panics or OOM errors
   - [ ] Retry logic completes within 42 minutes max (21x base)

2. **Reliability** ✅
   - [ ] 100% gate enforcement (no false passes)
   - [ ] >95% retry success rate (tests complete after retry)
   - [ ] >98% rollback success rate
   - [ ] Zero false positives (incorrectly passing bad tests)

3. **Observability** ✅
   - [ ] Detailed failure reports with test names
   - [ ] Retry attempt logging
   - [ ] Memory usage reporting
   - [ ] VectorStore pattern storage

---

## Testing Strategy

### Unit Tests (`tests/test_test_verification_gate.py`)

**Coverage Target**: >90%

```python
class TestTestVerificationGate:
    """Unit tests for test verification gate."""

    def test_gate_pass_first_attempt(self):
        """Test gate passes on first attempt with 100% pass rate."""
        config = TestVerificationConfig()
        # Mock test execution: 100 passed, 0 failed
        result = execute_tests_with_retry(config)
        assert result.is_ok()
        assert result.unwrap().gate_passed
        assert result.unwrap().retry_attempts == 1

    def test_gate_retry_then_pass(self):
        """Test gate retries on timeout, passes on 2nd attempt."""
        config = TestVerificationConfig()
        # Mock: 1st attempt timeout, 2nd attempt success
        result = execute_tests_with_retry(config)
        assert result.is_ok()
        assert result.unwrap().retry_attempts == 2

    def test_gate_fail_not_100_percent(self):
        """Test gate blocks on <100% pass rate (Article II)."""
        config = TestVerificationConfig()
        # Mock: 98 passed, 2 failed
        result = execute_tests_with_retry(config)
        assert result.is_ok()
        assert not result.unwrap().gate_passed
        assert not result.unwrap().article_ii_compliant

    def test_timeout_multipliers(self):
        """Verify timeout progression: 1x→2x→3x→5x→10x."""
        config = TestVerificationConfig()
        # Mock: all attempts timeout
        result = execute_tests_with_retry(config)
        assert result.is_err()
        assert "Article I violation" in result.unwrap_err()

    def test_memory_aware_workers(self):
        """Test worker count calculation respects local model state."""
        # Mock: local model active
        worker_count, memory_safe, rationale = calculate_test_workers()
        assert worker_count == 3  # Reduced for local model
        assert "Local model active" in rationale

    def test_rollback_success(self):
        """Test git rollback on test failure."""
        result = perform_rollback()
        assert result.is_ok()
        assert "Rollback successful" in result.unwrap()

    def test_todowrite_state_reversion(self):
        """Test TodoWrite task state reverts on gate failure."""
        # Mock: TodoWrite task completed, gate fails
        gate_result = TestVerificationResult(gate_passed=False, ...)
        update_todowrite_state(task_index=0, gate_result=gate_result)
        # Verify task status reverted to in_progress
        todos = read_todos()
        assert todos[0]["status"] == "in_progress"
```

### Integration Tests

```python
class TestTestVerificationGateIntegration:
    """Integration tests with real test execution."""

    def test_real_test_execution(self):
        """Test gate with real pytest execution."""
        config = TestVerificationConfig(test_scope="fast")
        result = execute_tests_with_retry(config)
        assert result.is_ok()
        assert result.unwrap().gate_passed  # Assumes fast tests pass

    def test_memory_safe_execution(self):
        """Test gate does not exceed memory limits."""
        import psutil
        mem_before = psutil.virtual_memory().used

        config = TestVerificationConfig()
        result = execute_tests_with_retry(config)

        mem_after = psutil.virtual_memory().used
        mem_used_gb = (mem_after - mem_before) / (1024 ** 3)

        # Should not exceed 12GB (10 workers × 1.2GB worst case)
        assert mem_used_gb < 12.0
```

---

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Gate Enforcement Rate | 100% | All Code tasks trigger gate |
| False Pass Rate | 0% | Gate never allows <100% pass rate |
| Retry Success Rate | >95% | Timeouts resolved by 2nd/3rd attempt |
| Memory Safety | 0 crashes | No OOM errors during 1000 test runs |
| Rollback Success | >98% | Git restore succeeds on test failure |
| Learning Storage | 100% | All gate results stored in VectorStore |

---

## Constitutional Alignment

### Article I: Complete Context Before Action ✅

**Compliance**:
- Retry logic implements 2x, 3x, 5x, 10x timeout multipliers (constitution.md lines 27-31)
- Maximum 5 attempts ensure complete test results
- Timeout pause (2 seconds) allows analysis before retry
- Completeness validation prevents proceeding with truncated output

**Evidence**:
- `timeout_multipliers: [1, 2, 3, 5, 10]` (Article I compliant)
- `_validate_completeness()` checks for truncation indicators
- Retry loop exits only on complete results or exhaustion

### Article II: 100% Verification and Stability ✅

**Compliance**:
- `required_pass_rate: 1.0` enforces 100% test pass rate (constitution.md lines 84-87)
- Gate blocks progression on <100% pass rate
- No bypass mechanisms (zero override authority)
- Rollback ensures no broken windows

**Evidence**:
- `article_ii_compliant = pass_rate >= config.required_pass_rate` (strict equality check)
- `gate_passed = (is_complete and article_ii_compliant)` (both required)
- TodoWrite task state reverted on failure

### Article III: Automated Merge Enforcement ✅

**Compliance**:
- Gate automatically enforced (no manual triggers)
- No bypass flags or override parameters
- Integration into agent workflows

**Evidence**:
- Gate triggers automatically after TodoWrite completion
- Agents cannot proceed without gate pass

### Article IV: Continuous Learning ✅

**Compliance**:
- All verification patterns stored in VectorStore
- Confidence scores assigned (0.65-0.85)
- Timeout optimization enabled via pattern analysis

**Evidence**:
- `store_verification_pattern()` stores all gate results
- Tags: `["test_verification", "article_i", "article_ii"]`
- Learning dashboard for pattern visualization

---

## References

- **ADR-001**: Complete Context Before Action (retry logic foundation)
- **ADR-002**: 100% Verification and Stability (100% pass rate mandate)
- **ADR-023**: Memory-Aware Test Execution (worker calculation)
- **Constitution Article I Section 1.2**: Timeout handling (lines 27-31)
- **Constitution Article II Section 2.2**: 100% test success (lines 84-87)
- **tools/memory_aware_test_runner.py**: Memory-safe worker calculation
- **run_tests.py**: Test execution wrapper

---

## Glossary

- **Test Verification Gate**: Mandatory checkpoint ensuring 100% test pass rate before task completion
- **Constitutional Retry**: Article I-compliant retry logic with exponential timeout multipliers
- **Memory-Aware Workers**: Dynamic pytest worker count based on local model state and available memory
- **Rollback**: Git restore operation reverting changes to last known good state
- **Gate Pass**: Test verification result meeting Articles I & II requirements (complete + 100% pass rate)
- **Blocking Reason**: Human-readable explanation for why gate failed

---

**Author**: ChiefArchitectAgent
**Date**: 2025-10-11
**Status**: Draft
**Constitutional Impact**: Enforces Articles I & II, enables Article IV learning
**Implementation Effort**: 2 weeks (4 phases)
