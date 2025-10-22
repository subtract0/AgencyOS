# Git Validator Implementation Guide for CodeAgent

**Implementation File**: `tools/orchestrator/git_validator.py`
**Test File**: `tests/foundation_automation/test_git_validation.py` (924 lines, 27 tests)
**Status**: RED Phase Complete ✅ (All 27 tests fail as expected)

---

## Quick Start for CodeAgent

### Step 1: Create Implementation File

```bash
# File path
touch tools/orchestrator/git_validator.py
```

### Step 2: Required Imports

```python
import re
import subprocess
import time
from functools import wraps
from pathlib import Path
from typing import List, Optional

from shared.type_definitions.result import Err, Ok, Result
```

### Step 3: Implement Core Functions

#### 3.1 GitValidationError Exception

```python
class GitValidationError(Exception):
    """
    Raised when git validation fails.

    Covers:
    - Protected branch violations (main, master, develop)
    - Detached HEAD state
    - Invalid branch patterns
    - Git command failures
    """
    pass
```

#### 3.2 get_current_branch() Function

```python
def get_current_branch(repo_path: Path) -> Result[str, GitValidationError]:
    """
    Extract current branch name via git command.

    Uses: git rev-parse --abbrev-ref HEAD (faster than git branch)

    Returns:
        Ok(branch_name) if on valid branch
        Err(GitValidationError) if detached HEAD or git error

    Performance: <10ms (optimized git command)
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=5.0,
        )

        branch_name = result.stdout.strip()

        # Detached HEAD detection
        if branch_name == "HEAD":
            return Err(
                GitValidationError(
                    "Detached HEAD state detected. "
                    "Checkout a branch before running /primeA:\n"
                    "  git checkout -b feat/<your-feature-name>"
                )
            )

        return Ok(branch_name)

    except subprocess.CalledProcessError as e:
        return Err(GitValidationError(f"Git command failed: {e.stderr}"))

    except subprocess.TimeoutExpired:
        return Err(GitValidationError("Git command timed out (repo may be locked)"))

    except Exception as e:
        return Err(GitValidationError(f"Unexpected git error: {e}"))
```

#### 3.3 validate_branch_safety() Function

```python
def validate_branch_safety(repo_path: Path) -> Result[str, GitValidationError]:
    """
    Validate current branch is safe for execution.

    Enforces:
    - Branch matches pattern: (feat|fix|docs|refactor|test)/*
    - Not on protected branches: main, master, develop
    - Article III branch protection (no bypass mechanism)

    Returns:
        Ok(branch_name) if validation passes
        Err(GitValidationError) with actionable message if fails

    Performance: <50ms (PERF-003)
    Retry: 3 attempts with 2x timeout on transient failures (Article I)
    """
    # Retry logic (Article I)
    max_retries = 3
    timeout = 5.0

    for attempt in range(max_retries):
        try:
            # Get current branch
            branch_result = get_current_branch(repo_path)

            if branch_result.is_err():
                # Check for retryable errors (timeout, lock)
                error_msg = str(branch_result.error)
                if attempt < max_retries - 1 and (
                    "timeout" in error_msg.lower() or "lock" in error_msg.lower()
                ):
                    time.sleep(0.5 * (2 ** attempt))  # Exponential backoff
                    timeout *= 2
                    continue

                return branch_result  # Non-retryable error

            branch_name = branch_result.unwrap()

            # Protected branch check
            protected_branches = ["main", "master", "develop"]
            if branch_name in protected_branches:
                return Err(
                    GitValidationError(
                        f"⚠️  Branch Protection Violation (Article III)\n\n"
                        f"Current branch: {branch_name}\n"
                        f"Protected branches: {', '.join(protected_branches)}\n\n"
                        f"The /primeA orchestrator cannot execute on protected branches "
                        f"to prevent accidental direct commits (Article III constitutional mandate).\n\n"
                        f"✅ Solution:\n"
                        f"1. Checkout a feature branch:\n"
                        f"   git checkout -b feat/<your-feature-name>\n\n"
                        f"2. Re-run /primeA command\n\n"
                        f"Valid branch patterns:\n"
                        f"- feat/*     (new features)\n"
                        f"- fix/*      (bug fixes)\n"
                        f"- docs/*     (documentation)\n"
                        f"- refactor/* (code improvements)\n"
                        f"- test/*     (test enhancements)\n\n"
                        f"📖 Reference: constitution.md Article III, ADR-003"
                    )
                )

            # Branch pattern validation
            valid_pattern = re.compile(r"^(feat|fix|docs|refactor|test)/.+")
            if not valid_pattern.match(branch_name):
                return Err(
                    GitValidationError(
                        f"Invalid branch name pattern: {branch_name}\n\n"
                        f"Expected pattern: (feat|fix|docs|refactor|test)/*\n"
                        f"Examples:\n"
                        f"  - feat/add-authentication\n"
                        f"  - fix/bug-123\n"
                        f"  - docs/update-readme"
                    )
                )

            # Success
            return Ok(branch_name)

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (2 ** attempt))
                continue
            return Err(GitValidationError(f"Validation failed after {max_retries} retries: {e}"))

    return Err(GitValidationError("Validation failed after max retries"))
```

#### 3.4 require_feature_branch() Decorator

```python
def require_feature_branch():
    """
    Decorator to enforce feature branch requirement on orchestrator methods.

    Validates git branch before method execution (Phase 0).
    No bypass parameters allowed (Article III).

    Usage:
        @require_feature_branch()
        async def execute_primea_workflow(self, intent: str) -> Result[...]:
            # Implementation proceeds only if on feature branch
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Extract repo_path from orchestrator instance
            repo_path = getattr(self, "repo_path", Path.cwd())

            # Phase 0: Git validation (runs BEFORE any orchestrator logic)
            validation_result = validate_branch_safety(repo_path)

            if validation_result.is_err():
                # Halt execution with clear error message
                error = validation_result.error
                print(f"\n❌ {error}\n")
                return Err(error)

            # Validation passed - proceed with method execution
            return func(self, *args, **kwargs)

        return wrapper
    return decorator
```

---

## Test Validation Checklist

After implementation, verify:

### ✅ Normal Operation (6 tests)
```bash
pytest tests/foundation_automation/test_git_validation.py::test_feature_branch_passes_validation -v
pytest tests/foundation_automation/test_git_validation.py::test_fix_branch_passes_validation -v
pytest tests/foundation_automation/test_git_validation.py::test_docs_branch_passes_validation -v
pytest tests/foundation_automation/test_git_validation.py::test_refactor_branch_passes_validation -v
pytest tests/foundation_automation/test_git_validation.py::test_test_branch_passes_validation -v
pytest tests/foundation_automation/test_git_validation.py::test_get_current_branch_returns_branch_name -v
```

### ✅ Edge Cases (5 tests)
```bash
pytest tests/foundation_automation/test_git_validation.py::test_branch_name_with_special_chars -v
pytest tests/foundation_automation/test_git_validation.py::test_very_long_branch_name -v
pytest tests/foundation_automation/test_git_validation.py::test_branch_name_with_unicode -v
pytest tests/foundation_automation/test_git_validation.py::test_branch_name_with_slashes -v
```

### ✅ Constraints (4 tests)
```bash
pytest tests/foundation_automation/test_git_validation.py::test_main_branch_raises_validation_error -v
pytest tests/foundation_automation/test_git_validation.py::test_master_branch_raises_validation_error -v
pytest tests/foundation_automation/test_git_validation.py::test_develop_branch_raises_validation_error -v
pytest tests/foundation_automation/test_git_validation.py::test_invalid_branch_pattern_raises_error -v
```

### ✅ Error Handling (5 tests)
```bash
pytest tests/foundation_automation/test_git_validation.py::test_detached_head_raises_validation_error -v
pytest tests/foundation_automation/test_git_validation.py::test_not_in_git_repo_logs_warning -v
pytest tests/foundation_automation/test_git_validation.py::test_git_command_timeout_retries -v
pytest tests/foundation_automation/test_git_validation.py::test_git_command_failure_with_locked_repo -v
pytest tests/foundation_automation/test_git_validation.py::test_get_current_branch_handles_detached_head -v
```

### ✅ Security (4 tests)
```bash
pytest tests/foundation_automation/test_git_validation.py::test_branch_name_injection_prevented -v
pytest tests/foundation_automation/test_git_validation.py::test_symlink_to_protected_branch_rejected -v
pytest tests/foundation_automation/test_git_validation.py::test_no_manual_bypass_mechanism_exists -v
pytest tests/foundation_automation/test_git_validation.py::test_require_feature_branch_enforces_pattern -v
```

### ✅ Scale (2 tests)
```bash
pytest tests/foundation_automation/test_git_validation.py::test_git_validation_performance -v
pytest tests/foundation_automation/test_git_validation.py::test_batch_validation_performance -v
```

### ✅ Yield (1 test)
```bash
pytest tests/foundation_automation/test_git_validation.py::test_error_message_explains_article_iii_violation -v
```

### ✅ Integration (1 test)
```bash
pytest tests/foundation_automation/test_git_validation.py::test_validation_runs_before_planner_execution -v
```

---

## Performance Benchmarks (PERF-003)

```bash
# Single validation: <50ms
pytest tests/foundation_automation/test_git_validation.py::test_git_validation_performance -v --durations=10

# Batch validation: <500ms total (10 calls)
pytest tests/foundation_automation/test_git_validation.py::test_batch_validation_performance -v --durations=10
```

**Expected Output**:
```
test_git_validation_performance PASSED [  0.03s ]  ✅ (30ms < 50ms target)
test_batch_validation_performance PASSED [  0.24s ]  ✅ (24ms avg < 50ms target)
```

---

## Full Test Suite Execution

```bash
# Run all 27 git validation tests
pytest tests/foundation_automation/test_git_validation.py -v

# Expected output (GREEN phase)
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-8.4.2
collected 27 items

tests/foundation_automation/test_git_validation.py::test_feature_branch_passes_validation PASSED
tests/foundation_automation/test_git_validation.py::test_fix_branch_passes_validation PASSED
tests/foundation_automation/test_git_validation.py::test_docs_branch_passes_validation PASSED
tests/foundation_automation/test_git_validation.py::test_refactor_branch_passes_validation PASSED
tests/foundation_automation/test_git_validation.py::test_test_branch_passes_validation PASSED
tests/foundation_automation/test_git_validation.py::test_branch_name_with_special_chars PASSED
tests/foundation_automation/test_git_validation.py::test_very_long_branch_name PASSED
tests/foundation_automation/test_git_validation.py::test_branch_name_with_unicode PASSED
tests/foundation_automation/test_git_validation.py::test_branch_name_with_slashes PASSED
tests/foundation_automation/test_git_validation.py::test_main_branch_raises_validation_error PASSED
tests/foundation_automation/test_git_validation.py::test_master_branch_raises_validation_error PASSED
tests/foundation_automation/test_git_validation.py::test_develop_branch_raises_validation_error PASSED
tests/foundation_automation/test_git_validation.py::test_invalid_branch_pattern_raises_error PASSED
tests/foundation_automation/test_git_validation.py::test_detached_head_raises_validation_error PASSED
tests/foundation_automation/test_git_validation.py::test_not_in_git_repo_logs_warning PASSED
tests/foundation_automation/test_git_validation.py::test_git_command_timeout_retries PASSED
tests/foundation_automation/test_git_validation.py::test_git_command_failure_with_locked_repo PASSED
tests/foundation_automation/test_git_validation.py::test_branch_name_injection_prevented PASSED
tests/foundation_automation/test_git_validation.py::test_symlink_to_protected_branch_rejected PASSED
tests/foundation_automation/test_git_validation.py::test_no_manual_bypass_mechanism_exists PASSED
tests/foundation_automation/test_git_validation.py::test_require_feature_branch_enforces_pattern PASSED
tests/foundation_automation/test_git_validation.py::test_git_validation_performance PASSED
tests/foundation_automation/test_git_validation.py::test_batch_validation_performance PASSED
tests/foundation_automation/test_git_validation.py::test_error_message_explains_article_iii_violation PASSED
tests/foundation_automation/test_git_validation.py::test_get_current_branch_returns_branch_name PASSED
tests/foundation_automation/test_git_validation.py::test_get_current_branch_handles_detached_head PASSED
tests/foundation_automation/test_git_validation.py::test_validation_runs_before_planner_execution PASSED

======================== 27 passed in 1.87s ==========================
```

**Target**: 27/27 tests pass (100% - Article II requirement)

---

## Coverage Report

```bash
pytest tests/foundation_automation/test_git_validation.py \
  --cov=tools/orchestrator/git_validator \
  --cov-report=term-missing \
  --cov-fail-under=95
```

**Expected Coverage**: >95% (QUALITY-001)

---

## Integration with Orchestrator

After implementation, integrate with `UnifiedPrimeAOrchestrator`:

```python
# tools/orchestrator/unified_primea_orchestrator.py

from tools.orchestrator.git_validator import require_feature_branch, GitValidationError

class UnifiedPrimeAOrchestrator:
    @require_feature_branch()  # Phase 0: Git validation BEFORE Planner
    async def execute_primea_workflow(
        self,
        intent: str,
        graph_file: Optional[Path] = None,
        flags: Dict[str, bool] = None,
    ) -> Result[PrimeAResult, ExecutionError]:
        """
        Execute /primeA workflow from intent to PR.

        Phase 0: Git validation (require_feature_branch decorator)
        Phase 1: Intent → Task Graph
        Phase 2: TRM/Slop/Budget validation
        ...
        """
        # Git validation already enforced by decorator (Phase 0)
        # Orchestrator logic proceeds only if on feature branch
        pass
```

---

## Common Implementation Pitfalls

### ❌ Pitfall 1: Forgetting Retry Logic (Article I)
```python
# WRONG: No retry on timeout
result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=5)

# CORRECT: Retry with exponential backoff
for attempt in range(3):
    try:
        result = subprocess.run(["git", "..."], timeout=timeout)
        break
    except subprocess.TimeoutExpired:
        timeout *= 2
        continue
```

### ❌ Pitfall 2: Missing Detached HEAD Detection
```python
# WRONG: Assume branch always exists
branch_name = subprocess.run(["git", "branch", "--show-current"]).stdout.strip()

# CORRECT: Detect detached HEAD
branch_name = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
if branch_name == "HEAD":
    return Err(GitValidationError("Detached HEAD state"))
```

### ❌ Pitfall 3: Slow Git Commands
```python
# WRONG: Slow command (100ms+)
result = subprocess.run(["git", "branch", "-a"])

# CORRECT: Fast command (<10ms)
result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
```

### ❌ Pitfall 4: Missing Protected Branches
```python
# WRONG: Only checking main
if branch_name == "main":
    return Err(...)

# CORRECT: Check all protected branches
if branch_name in ["main", "master", "develop"]:
    return Err(...)
```

---

## Success Criteria

- [x] Implementation file created: `tools/orchestrator/git_validator.py`
- [ ] All 27 tests pass (100% - Article II requirement)
- [ ] Performance <50ms per validation (PERF-003)
- [ ] Coverage >95% (QUALITY-001)
- [ ] No linting errors (`ruff check tools/orchestrator/git_validator.py`)
- [ ] Type safety verified (no `Any` types)
- [ ] Integrated with `UnifiedPrimeAOrchestrator` (Phase 0 validation)
- [ ] VectorStore learning integration (Article IV)

---

**Test-Driven Development Status**:
- ✅ RED Phase: 27/27 tests fail (expected)
- ⏳ GREEN Phase: Implementation pending (CodeAgent task)
- ⏳ REFACTOR Phase: After all tests pass (optimization if needed)

**Next Action**: CodeAgent implements `tools/orchestrator/git_validator.py` to pass all 27 tests
