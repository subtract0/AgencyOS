# Specification: Fix run_tests.py --run-all Regression from Ollama Health Check

**Mission**: Restore `./run_tests.py --run-all` functionality by making Ollama health check non-fatal during test discovery

**Status**: Stage 1 - Specification
**Priority**: HIGH (blocks full test suite execution and artifact generation)
**Complexity**: Simple
**Estimated Effort**: 30-45 minutes

---

## Problem Statement

`./run_tests.py --run-all` dies immediately with error:
```
No models available for inference test
```

**Root Cause**:
- The `ollama_available()` fixture in `tests/conftest.py:253-323` is session-scoped
- It runs during pytest session setup (before tests execute)
- It calls `check_ollama_health()` which logs `logger.warning("No models available for inference test")` at `tools/ollama_health_check.py:180`
- This warning output during test collection causes the test run to abort
- The `--no-sandbox` workaround succeeds but we need `--run-all` to produce complete test artifacts

**Impact**:
- Cannot generate full-suite JSON test reports
- Blocks CI/CD artifact collection
- Forces use of `--no-sandbox` workaround (suboptimal)
- Prevents comprehensive test coverage validation

---

## Current Behavior

**Failed Command**:
```bash
./run_tests.py --run-all
```

**Output**:
```
No models available for inference test
[Process exits immediately]
```

**Workaround** (functional but undesirable):
```bash
./run_tests.py --run-all --no-sandbox
```

---

## Proposed Solution

**Option 1: Downgrade Log Level** (RECOMMENDED)

Change `logger.warning()` to `logger.debug()` at `tools/ollama_health_check.py:180`:

**Before**:
```python
else:
    logger.warning("No models available for inference test")
```

**After**:
```python
else:
    logger.debug("No models available for inference test - inference checks skipped")
```

**Rationale**:
- Missing models is an expected condition (not a warning-level event)
- Health check already returns graceful status (`inference_working=False`)
- `logger.debug()` preserves diagnostic info without alarming output
- Maintains existing error handling and Result pattern

**Alternative Solutions** (not recommended):
- **Option 2**: Add warning filter to `pyproject.toml` - overly complex
- **Option 3**: Suppress warnings in fixture - masks other legitimate warnings
- **Option 4**: Skip health check entirely - loses valuable diagnostics

---

## Acceptance Criteria

### Functional Requirements

1. **`./run_tests.py --run-all` executes successfully**
   - No immediate abort from health check warning
   - Collects all tests (unit + integration)
   - Generates complete JSON artifact

2. **Health check maintains graceful degradation**
   - Returns `Ok(OllamaHealthStatus)` even without models
   - Sets `inference_working=False` when no models available
   - Preserves diagnostic information via debug logging

3. **Test fixture behavior unchanged**
   - `ollama_available()` fixture still returns `False` when models missing
   - Fast-path optimizations remain functional (<1ms via marker file)
   - Session-scoped caching still active

4. **Backward compatibility**
   - `--no-sandbox` flag continues to work
   - Existing Ollama integration tests unaffected
   - Docker healthcheck marker file logic intact

### Non-Functional Requirements

5. **Constitutional Compliance**
   - Article I: Complete context (full test collection, no premature abort)
   - Article II: 100% verification (all tests discoverable and executable)
   - Article III: Quality gates (maintain test infrastructure reliability)

6. **Logging Hygiene**
   - Debug-level message preserves diagnostic value
   - No alarming warnings for expected conditions
   - Consistent with logging best practices

---

## Test Plan (NECESSARY Pattern)

### Normal Cases
1. **Test: Health check with models available**
   - Setup: Ollama running with ≥1 model
   - Execute: `check_ollama_health()`
   - Verify: Returns `Ok(...)` with `inference_working=True`, no debug output unless verbose

2. **Test: Full test suite with healthy Ollama**
   - Execute: `./run_tests.py --run-all`
   - Verify: Discovers all tests, generates JSON artifact, exits 0

### Edge Cases
3. **Test: Health check without models** (PRIMARY REGRESSION FIX)
   - Setup: Ollama running but `ollama list` returns empty
   - Execute: `check_ollama_health()`
   - Verify:
     - Returns `Ok(...)` with `inference_working=False`
     - Logs debug message (not warning)
     - No test discovery abortion

4. **Test: Full test suite without Ollama**
   - Setup: No Ollama service available
   - Execute: `./run_tests.py --run-all`
   - Verify:
     - Discovers all tests
     - Skips Ollama integration tests (via `ollama_available` fixture)
     - Generates complete JSON artifact

5. **Test: Fast-path optimization still works**
   - Setup: Create `/tmp/ollama-running` marker file
   - Execute: `ollama_available()` fixture
   - Verify: Returns `True` in <1ms without health check call

### Security Cases
6. **Test: Malicious marker file**
   - Setup: `/tmp/ollama-running` with future timestamp
   - Execute: `ollama_available()` fixture
   - Verify: Ignores stale marker, falls back to health check

7. **Test: Permission errors on marker file**
   - Setup: `/tmp/ollama-running` not writable
   - Execute: Health check attempts to cache result
   - Verify: Gracefully skips caching, continues normally

---

## Implementation Notes

### Files to Modify

1. **`tools/ollama_health_check.py:180`**
   - Change: `logger.warning()` → `logger.debug()`
   - Lines: 180
   - Impact: One-line change, minimal risk

### Files to Test

2. **`tests/test_ollama_health_check.py`**
   - Verify: Existing tests still pass
   - Add: Test for debug logging level

3. **`tests/conftest.py`**
   - Verify: `ollama_available()` fixture behavior unchanged

### Rollback Plan

If regression occurs:
- Revert one-line change to `logger.warning()`
- Use `--no-sandbox` workaround temporarily
- Investigate alternative solutions

---

## Success Metrics

**Before Fix**:
```bash
$ ./run_tests.py --run-all
No models available for inference test
[EXIT]
```

**After Fix**:
```bash
$ ./run_tests.py --run-all
🚀 FORCE MODE: Running ALL tests EXCEPT slow E2E (>5min each)
⏰ Dynamic timeout: 3600s (60.0 minutes) for ~5,891 items
🔍 Running command: pytest -v --strict-markers ...
[Tests discover and execute normally]
✅ All tests passed!
📊 JSON report saved to: test-results/full-suite-run-all.json
```

---

## Dependencies

**Required**:
- Python 3.11+ (existing)
- pytest 8.0+ (existing)
- Logging module (stdlib)

**Optional**:
- Ollama service (for full integration tests)
- Docker Compose (for containerized Ollama)

---

## References

- **Codex Comment**: Phase-1 wrap analysis (2025-11-08)
- **File**: `tools/ollama_health_check.py:180`
- **File**: `tests/conftest.py:253-323`
- **ADR-028**: Ollama Docker Integration
- **Constitutional Articles**: I (Complete Context), II (100% Verification), III (Quality Gates)

---

## Changelog

- **2025-11-08**: Initial specification created via /primeA two-stage workflow
