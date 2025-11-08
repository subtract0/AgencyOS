# Specification: Fix Leap3 M5 Subprocess Import Failures

**Mission**: Fix 3 failing tests in `tests/test_leap3_m5_validation.py` where subprocess-executed tools cannot import `shared` module

**Leap**: 3 (Adaptive Model Router)
**Milestone**: M5 (Validation)
**Created**: 2025-11-08
**Status**: Stage 1 - Specification Approved (Pending User Review)

---

## 1. Problem Statement

### Current State
Three tests in `tests/test_leap3_m5_validation.py` are failing with `ModuleNotFoundError: No module named 'shared'`:

1. **TestCostSavingsValidation::test_cost_validation_can_run**
   - Line 220: `subprocess.run([sys.executable, "tools/validate_cost_savings.py", "--synthetic"])`
   - Error: `ModuleNotFoundError: No module named 'shared'` at line 20

2. **TestSkillDashboardVisualization::test_skill_dashboard_can_run**
   - Line 251: `subprocess.run([sys.executable, "tools/skill_dashboard.py", "--agent", "coder"])`
   - Error: `ModuleNotFoundError: No module named 'shared'` at line 23

3. **TestSkillDashboardVisualization::test_skill_dashboard_comparison_mode**
   - Line 271: `subprocess.run([sys.executable, "tools/skill_dashboard.py", "--compare", "coder", "planner"])`
   - Error: `ModuleNotFoundError: No module named 'shared'` at line 23

### Root Cause
When tests execute tools via `subprocess.run([sys.executable, "tools/..."])`, the subprocess environment:
- Does **not** inherit the parent pytest process's `sys.path`
- Does **not** have project root in `PYTHONPATH`
- Cannot resolve imports like `from shared.adaptive_model_router import ModelRouter`

### Why This Matters
- **Article II Violation**: 96.3% pass rate (should be 100%)
- **Leap 3 M5 Incomplete**: Cost validation and skill dashboard features unverified
- **Integration Gap**: Tools work when run directly but fail in test subprocess

---

## 2. Goals & Objectives

### Primary Goal
**Fix all 3 failing tests** to achieve 100% test pass rate for Leap3 M5 validation suite

### Specific Objectives
1. ✅ Enable subprocess-executed tools to import `shared` module
2. ✅ Maintain backward compatibility (tools still work when run directly)
3. ✅ Follow NECESSARY pattern (Normal + Edge + Security test coverage)
4. ✅ Constitutional compliance (Article I-V)
5. ✅ Zero code duplication (DRY principle)

---

## 3. Proposed Solution

### Approach: Modify Tests to Set PYTHONPATH

**Rationale**:
- ✅ **Minimal code changes**: Only 3 test methods modified
- ✅ **No tool modifications**: Tools remain simple, no sys.path hacks
- ✅ **Explicit intent**: Tests explicitly configure subprocess environment
- ✅ **Standard pattern**: Common pattern for subprocess testing with local imports

**Implementation**:
```python
import os
import subprocess
import sys
from pathlib import Path

# Get project root (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent

def test_cost_validation_can_run(self):
    """Test that cost validation tool executes without errors."""
    # Arrange: Set up environment with PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    # Act: Run subprocess with explicit environment
    result = subprocess.run(
        [sys.executable, "tools/validate_cost_savings.py", "--synthetic"],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,  # <-- KEY CHANGE
        cwd=PROJECT_ROOT  # <-- Ensure correct working directory
    )

    # Assert: Check output contains expected content
    assert result.returncode in [0, 1], f"Tool crashed: {result.stderr}"
    assert "Cost Analysis" in result.stdout
    assert "Savings" in result.stdout
    assert "%" in result.stdout
```

### Alternative Approaches Considered

#### Alternative 1: Modify Tools to Add sys.path (REJECTED)
```python
# At top of tools/validate_cost_savings.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```
**Why Rejected**:
- ❌ Adds complexity to every tool
- ❌ Violates single responsibility (tools shouldn't manage import paths)
- ❌ Code duplication across 64 tools

#### Alternative 2: Install Package in Editable Mode (REJECTED)
```bash
pip install -e .
```
**Why Rejected**:
- ❌ Requires setup.py or pyproject.toml package configuration
- ❌ Adds installation step to test execution
- ❌ May conflict with existing test infrastructure

#### Alternative 3: Use python -m Module Syntax (REJECTED)
```python
subprocess.run([sys.executable, "-m", "tools.validate_cost_savings", "--synthetic"])
```
**Why Rejected**:
- ❌ Requires tools/ to be a package (needs __init__.py)
- ❌ Changes tool invocation pattern (not backward compatible with CLI usage)
- ❌ May break other places where tools are called

---

## 4. Acceptance Criteria

### Functional Requirements
1. ✅ **All 3 tests pass**: `pytest tests/test_leap3_m5_validation.py -v` shows 15/15 passing
2. ✅ **No import errors**: Subprocess-executed tools successfully import `shared` modules
3. ✅ **Output validation**: Tests correctly validate tool output (e.g., "Cost Analysis" present)
4. ✅ **Exit codes correct**: Tools return 0 for success, non-zero for expected failures

### Non-Functional Requirements
5. ✅ **Backward compatibility**: Tools still work when run directly: `python tools/skill_dashboard.py --agent coder`
6. ✅ **No performance regression**: Test execution time ≤ 2 seconds (current: 1.4s)
7. ✅ **No new dependencies**: Solution uses stdlib only (os, subprocess, sys, pathlib)

### Quality Requirements (NECESSARY Pattern)
8. ✅ **Normal case**: Valid subprocess execution with correct PYTHONPATH
9. ✅ **Edge case**: Test handles tool timeout (60s limit)
10. ✅ **Security**: No shell injection (using list args, not shell=True)
11. ✅ **Error handling**: Test fails gracefully with clear error message

### Constitutional Compliance
12. ✅ **Article I (Complete Context)**: All 3 tests execute to completion
13. ✅ **Article II (100% Verification)**: 15/15 tests passing (100% pass rate)
14. ✅ **Article III (Automated Enforcement)**: CI validates fixes automatically
15. ✅ **Article V (Spec-Driven)**: Implementation traces to this specification

---

## 5. Test Plan

### Pre-Fix Baseline
```bash
$ pytest tests/test_leap3_m5_validation.py -v
# Expected: 3 FAILED, 12 PASSED
```

### Post-Fix Verification
```bash
$ pytest tests/test_leap3_m5_validation.py -v
# Expected: 15 PASSED in ~1.5s
```

### Regression Prevention
```bash
# Verify tools still work standalone (no PYTHONPATH required)
$ python tools/validate_cost_savings.py --synthetic
# Expected: Exit 0, "Cost Analysis" in output

$ python tools/skill_dashboard.py --agent coder
# Expected: Exit 0, "AGENT SKILL DASHBOARD" in output
```

### Full Suite Impact
```bash
$ ./run_tests.py --run-all --no-sandbox
# Expected: Pass rate 96.3% → 96.3% (3 failures resolved, but other failures remain)
# Note: Isolated fix, no impact on other test failures
```

---

## 6. Implementation Tasks

### Phase 1: Fix Test Methods (Tier 2 - Code)
**Agent**: `coder`
**File**: `tests/test_leap3_m5_validation.py`
**Lines**: 214-233, 245-264, 266-282

**Changes**:
1. Import `os` and `Path` at top of file
2. Define `PROJECT_ROOT = Path(__file__).parent.parent` as module constant
3. For each of 3 test methods:
   - Create `env = os.environ.copy()`
   - Set `env["PYTHONPATH"] = str(PROJECT_ROOT)`
   - Add `env=env` and `cwd=PROJECT_ROOT` to `subprocess.run()` call

**Estimated Tokens**: 1,500 (simple code modification)

### Phase 2: Verification (Tier 2 - Test)
**Agent**: `test_generator`
**File**: `tests/test_leap3_m5_validation.py` (same file, verification only)

**Verification Steps**:
1. Run modified tests: `pytest tests/test_leap3_m5_validation.py -v`
2. Verify 15/15 passing (0 failures)
3. Verify output contains expected strings
4. Check execution time ≤ 2 seconds

**Estimated Tokens**: 800 (verification commands)

### Phase 3: Regression Testing (Tier 2 - Test)
**Agent**: `test_generator`

**Test Cases**:
1. Standalone tool execution (without PYTHONPATH):
   ```bash
   python tools/validate_cost_savings.py --synthetic
   python tools/skill_dashboard.py --agent coder
   ```
2. Full test suite run:
   ```bash
   ./run_tests.py --run-all --no-sandbox | grep "test_leap3_m5_validation"
   ```

**Estimated Tokens**: 600 (regression validation)

---

## 7. Estimated Effort & Cost

### Effort Breakdown
| Phase | Tasks | Agent | Tier | Est. Tokens | Est. Time |
|-------|-------|-------|------|-------------|-----------|
| 1 | Code fix | coder | T2 | 1,500 | 5 min |
| 2 | Verification | test_generator | T2 | 800 | 3 min |
| 3 | Regression | test_generator | T2 | 600 | 2 min |
| **Total** | **3 tasks** | **2 agents** | **T2** | **2,900** | **10 min** |

### Cost Estimate
- **Tier 2**: 100% (simple code + test tasks)
- **Model**: vcoder-120b (local network model, $0 cost)
- **Total Cost**: **$0.00**

### Risk Assessment
- **Risk Level**: LOW
- **Complexity**: SIMPLE (single file, 3 method modifications)
- **Dependencies**: NONE (stdlib only)
- **Rollback**: EASY (git revert single commit)

---

## 8. Success Metrics

### Primary Metrics
1. ✅ **Test Pass Rate**: 15/15 tests passing (100%)
2. ✅ **Failure Count**: 0 failures in `test_leap3_m5_validation.py`
3. ✅ **Execution Time**: ≤ 2 seconds

### Secondary Metrics
4. ✅ **Code Churn**: ≤ 30 lines changed (minimal diff)
5. ✅ **Test Coverage**: 100% (all 3 failing tests now pass)
6. ✅ **Regression Risk**: ZERO (isolated change, no tool modifications)

### Constitutional Metrics
7. ✅ **Article II Compliance**: 100% test pass rate for Leap3 M5 validation
8. ✅ **Article V Compliance**: Full traceability (spec → code → tests)

---

## 9. Risks & Mitigations

### Risk 1: PYTHONPATH Conflicts
**Scenario**: Setting PYTHONPATH may conflict with other modules
**Likelihood**: LOW (isolated to subprocess environment)
**Mitigation**: Use `env.copy()` to avoid modifying parent process environment

### Risk 2: Platform Differences
**Scenario**: Path separators differ on Windows vs Unix
**Likelihood**: LOW (pathlib.Path handles cross-platform paths)
**Mitigation**: Use `Path` objects, convert to string only for env var

### Risk 3: Tool Refactoring Breaks Fix
**Scenario**: Future tool changes may break subprocess invocation
**Likelihood**: MEDIUM (tools may be refactored)
**Mitigation**: Document pattern in test docstring, add comment explaining PYTHONPATH

---

## 10. Out of Scope

### Explicitly Not Included
1. ❌ **Fixing other test failures**: This spec targets only Leap3 M5 validation (3 tests)
2. ❌ **Tool refactoring**: Tools remain unchanged (no sys.path modifications)
3. ❌ **Package installation**: No setup.py or pyproject.toml changes
4. ❌ **pytest configuration**: No pytest.ini or conftest.py changes

### Future Work
- **ADR Creation**: Document subprocess testing pattern (if this becomes common)
- **Test Utilities**: Create helper function for subprocess with PYTHONPATH (if pattern repeats)
- **CI Validation**: Ensure GitHub Actions CI also passes (already configured)

---

## 11. References

### Related Documents
- **ACTUAL_TEST_STATUS.md**: Section 4 (Leap3 M5 Validation Tests)
- **constitution.md**: Article II (100% Verification)
- **test-results/full-suite-final-20251108.json**: Baseline test results (96.3% pass rate)

### Code References
- **Test File**: `tests/test_leap3_m5_validation.py:214-282`
- **Tools**: `tools/validate_cost_savings.py:20-22`, `tools/skill_dashboard.py:23-24`
- **Shared Modules**: `shared/adaptive_model_router.py`, `shared/agent_context.py`, `shared/skill_vector.py`

### Constitutional References
- **Article I**: Complete Context Before Action
- **Article II**: 100% Verification and Stability
- **Article III**: Automated Local Enforcement
- **Article V**: Spec-Driven Development

---

## 12. Approval & Sign-Off

### Specification Status
- **Stage**: Stage 1 Complete (Specification Generated)
- **Next**: User approval checkpoint
- **Approver**: User (human review)

### Checkpoint Questions
1. ✅ Is the proposed solution (PYTHONPATH in subprocess env) acceptable?
2. ✅ Are the acceptance criteria clear and measurable?
3. ✅ Is the estimated effort (10 min, $0 cost) reasonable?
4. ✅ Should we proceed to Stage 2 (TDD implementation)?

---

**Specification Version**: 1.0
**Generated**: 2025-11-08 by /primeA Two-Stage Orchestrator
**Constitutional Compliance**: Articles I, II, III, V
**Estimated Delivery**: 10 minutes from approval
