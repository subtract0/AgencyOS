---
description: Run tests with constitutional retry logic (Article I & II compliance)
argument-hint: [scope] [timeout-multiplier]
model: claude-sonnet-4-5-20250929
---

# Agent Test Verify

## Purpose

**MANDATORY Article I & II tool** for test execution with constitutional compliance. Implements automatic retry logic (2x, 3x, up to 10x timeout) and enforces 100% pass rate.

## Variables

- `scope`: Test scope (`all` | `unit` | `integration` | `e2e` | `file:<path>`)
- `timeout_multiplier`: Timeout scaling factor (default: `1`, max: `10`)

## Instructions

You are running tests with **zero tolerance for incomplete results**. Per Article I, you MUST retry on timeout. Per Article II, you MUST achieve 100% pass rate.

## Step 1: Determine Test Command

Based on scope, select appropriate command:

**Full Test Suite** (`scope=all`):
```bash
python run_tests.py --run-all
```

**Unit Tests Only** (`scope=unit`):
```bash
python run_tests.py
```

**Integration Tests** (`scope=integration`):
```bash
python run_tests.py --integration-only
```

**Backend Tests** (`scope=backend`):
```bash
uv run pytest
```

**Frontend Tests** (`scope=frontend`):
```bash
bun run test
```

**Specific File** (`scope=file:<path>`):
```bash
uv run pytest <path> -v
```

## Step 2: Execute with Timeout Retry Logic

**Constitutional Retry Protocol (Article I)**:

```python
def run_tests_with_retry(command: str, base_timeout: int = 120000) -> TestResult:
    """
    Execute tests with exponential timeout retry.
    
    Article I: Complete context before action - NEVER accept partial results.
    """
    
    attempts = [1, 2, 3, 10]  # Timeout multipliers
    
    for attempt, multiplier in enumerate(attempts, 1):
        timeout = base_timeout * multiplier
        
        print(f"Attempt {attempt}/{len(attempts)}: timeout={timeout}ms ({timeout/1000}s)")
        
        result = execute_bash_command(command, timeout=timeout)
        
        if result.completed and not result.timed_out:
            # Success - tests ran to completion
            return result
        
        if result.timed_out:
            print(f"⚠️ Timeout on attempt {attempt}. Retrying with {multiplier}x timeout...")
            continue
        
        # Other error - do not retry
        return result
    
    # Exhausted all retries
    raise ConstitutionalViolation(
        article="Article I",
        reason="Tests timed out after 10x retry. Cannot proceed with incomplete data."
    )
```

## Step 3: Analyze Results

**Parse Test Output**:

```python
def parse_test_results(output: str) -> TestMetrics:
    """Extract test metrics from output."""
    
    # Python pytest format
    if "passed" in output:
        passed = extract_number(output, r"(\d+) passed")
        failed = extract_number(output, r"(\d+) failed")
        errors = extract_number(output, r"(\d+) error")
        total = passed + failed + errors
        
    # Jest/Vitest format
    elif "Test Suites:" in output:
        passed = extract_number(output, r"(\d+) passed")
        failed = extract_number(output, r"(\d+) failed")
        total = passed + failed
    
    return TestMetrics(
        total=total,
        passed=passed,
        failed=failed,
        pass_rate=passed / total if total > 0 else 0,
        duration=extract_duration(output)
    )
```

**Validate Article II Compliance**:

```python
def validate_article_ii_compliance(metrics: TestMetrics) -> ComplianceResult:
    """
    Article II: 100% verification and stability.
    
    All tests MUST pass. No exceptions.
    """
    
    if metrics.pass_rate < 1.0:
        return ComplianceResult(
            compliant=False,
            article="Article II",
            violation=f"Test pass rate: {metrics.pass_rate*100:.1f}% (required: 100%)",
            blocking=True,  # BLOCKS merge/commit
            remediation="Fix all failing tests before proceeding"
        )
    
    return ComplianceResult(compliant=True)
```

## Step 4: Report Results

Provide detailed test report:

```
## Test Verification Report

**Scope**: [scope]
**Command**: `[command]`
**Timeout**: [Xms] ([multiplier]x base timeout)
**Duration**: [X.XX]s

### Results
- **Total Tests**: [N]
- **Passed**: [N] ✅
- **Failed**: [N] ❌
- **Errors**: [N] ⚠️
- **Pass Rate**: [XX.X]%

### Constitutional Compliance
- **Article I** (Complete Context): ✅ Tests ran to completion
- **Article II** (100% Verification): [✅ PASS | ❌ FAIL]

### Verdict
[✅ COMPLIANT - Proceed with next step]
[❌ BLOCKED - Fix failing tests (Article II violation)]

### Failing Tests (if any)
```
[List of failing test names with file:line references]
```

### Next Action
[What to do based on results]
```

## Use Cases

### 1. Code Agent After Implementation
```
Agent: Implemented new feature, need to verify tests
Tool: Runs tests with 2-minute timeout
Result: Tests complete, 100% pass → PROCEED
```

### 2. Quality Enforcer During Healing
```
Agent: Applied fix for violations, need verification
Tool: Runs tests with retry (timed out on 1st attempt)
Result: 2nd attempt (4-minute timeout) → 100% pass → PROCEED
```

### 3. Pre-Commit Hook
```
Agent: Developer attempting commit
Tool: Runs tests on changed files
Result: 98% pass rate (2 failures) → BLOCK commit (Article II)
```

## Retry Scenarios

**Scenario 1: Timeout on First Attempt**
```
Attempt 1: timeout=120s → TIMEOUT
Attempt 2: timeout=240s → SUCCESS (98% pass)
Result: BLOCKED (Article II - not 100%)
```

**Scenario 2: All Attempts Timeout**
```
Attempt 1: timeout=120s → TIMEOUT
Attempt 2: timeout=240s → TIMEOUT
Attempt 3: timeout=360s → TIMEOUT
Attempt 4: timeout=1200s → TIMEOUT
Result: THROW ConstitutionalViolation (Article I)
```

**Scenario 3: Immediate Success**
```
Attempt 1: timeout=120s → SUCCESS (100% pass)
Result: PROCEED ✅
```

## Integration with Agent Workflows

**MANDATORY in Agent Definitions**:

```markdown
## Implementation Workflow

[steps 1-4: write tests, implement code]

### 5. Verify with Tests (MANDATORY - Articles I & II)
Use `/agent-test-verify all` to run full test suite with retry logic

**Requirements**:
- MUST run to completion (retry on timeout)
- MUST achieve 100% pass rate (no exceptions)
- BLOCKS proceed if either fails

[remaining steps]
```

## Error Handling

**Test Failures** (Article II Violation):
```
❌ **Test Failures Detected**

Article II requires 100% test success. You CANNOT proceed.

**Options**:
1. Fix failing tests
2. Rollback changes (git reset --hard)
3. Debug with specific test: `/agent-test-verify file:tests/test_failing.py`

**Do NOT**:
- Ignore failures
- Commit with failing tests
- Merge to main branch
```

**Persistent Timeouts** (Article I Violation):
```
❌ **Tests Timed Out After 10x Retry**

Article I requires complete context. Timeout indicates:
- Infinite loops in code
- External dependency hangs
- Resource exhaustion
- Test suite too large

**Options**:
1. Debug infinite loops
2. Mock slow external dependencies
3. Split test suite into smaller scopes
4. Increase resources (RAM, CPU)
```

## Success Metrics

- **Completion Rate**: 100% (all tests run to completion)
- **Pass Rate Required**: 100% (Article II enforcement)
- **Timeout Retry Success**: >95% (2nd attempt succeeds)
- **Execution Time**: <5 minutes for full suite (optimized)
- **False Positive Rate**: <1% (flaky tests eliminated)

## Article I & II Compliance

This tool enforces:

**Article I: Complete Context Before Action**
- NEVER accept partial test results
- Retry with 2x, 3x, 10x timeout on failure
- Throw constitutional violation if exhausted

**Article II: 100% Verification and Stability**
- Enforce 100% test pass rate
- BLOCK commits/merges if < 100%
- No exceptions, no manual overrides

---

**Remember**: Incomplete tests = incomplete context. Zero tolerance for failures.
