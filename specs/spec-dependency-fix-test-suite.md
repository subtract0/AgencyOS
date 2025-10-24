# Specification: Test Suite Dependency Resolution

**Version**: 1.0.0
**Date**: 2025-10-24
**Status**: Active
**Author**: PrimeA Orchestrator

## 1. Overview

Fix all test suite failures caused by missing Python dependencies, achieving 100% green test suite (Article II constitutional requirement).

## 2. Problem Statement

**Current State**:
- 25+ test files failing at collection stage (import errors)
- Missing dependencies: `aiofiles`, `joblib`, `scikit-learn`
- Dependencies present in requirements.txt but not installed
- `joblib` missing from requirements.txt (implicit scikit-learn dependency)

**Impact**:
- Cannot run test_leap5_phase4_e2e.py (target file)
- Cannot run test_leap5_*.py files (4 files)
- Cannot run test_*ml*.py files (15+ files)
- Cannot run test_async_memory*.py files (4 files)

## 3. Acceptance Criteria

### 3.1 Dependency Resolution
- ✅ All missing dependencies identified (aiofiles, joblib, scikit-learn)
- ✅ `joblib>=1.3.0` added to requirements.txt
- ✅ `aiofiles>=23.2.0` confirmed present in requirements.txt
- ✅ `scikit-learn>=1.0.0` confirmed present in requirements.txt

### 3.2 Installation Success
- ✅ `pip install -r requirements.txt` completes without errors
- ✅ `pip show aiofiles` confirms version >=23.2.0
- ✅ `pip show joblib` confirms version >=1.3.0
- ✅ `pip show scikit-learn` confirms version >=1.0.0
- ✅ No dependency conflicts reported

### 3.3 Test Collection Success
- ✅ `pytest --collect-only` exits with code 0
- ✅ Zero 'ModuleNotFoundError' or 'ImportError' messages
- ✅ 1762+ tests collected successfully
- ✅ All test_leap5_*.py files collected (4 files)
- ✅ All test_*ml*.py files collected (15+ files)
- ✅ All test_async_memory*.py files collected (4 files)

### 3.4 Target File Success
- ✅ `pytest tests/test_leap5_phase4_e2e.py -v` runs without collection errors
- ✅ All Pydantic validation errors resolved
- ✅ 100% pass rate for target file

### 3.5 Full Suite Success (Article II)
- ✅ `python run_tests.py --run-all` completes successfully
- ✅ 100% pass rate (1762/1762 or higher)
- ✅ Zero failures, zero errors, zero collection errors
- ✅ Article II constitutional compliance verified

## 4. Implementation Strategy

### 4.1 Dependency Installation Order
```bash
# Step 1: Add missing dependency to requirements.txt
echo "joblib>=1.3.0  # Model persistence for ML routing (scikit-learn dependency)" >> requirements.txt

# Step 2: Install all dependencies
pip install -r requirements.txt

# Step 3: Verify installation
pip list | grep -E "aiofiles|joblib|scikit-learn"
pip show aiofiles joblib scikit-learn
```

### 4.2 Test Collection Validation
```bash
# Verify zero collection errors
python -m pytest tests/ --collect-only -q 2>&1 | tee collection_report.txt
grep -c "ERROR" collection_report.txt  # Should be 0

# Verify test count
python -m pytest tests/ --collect-only -q 2>&1 | tail -1  # Should show "1762+ tests"
```

### 4.3 Target File Validation
```bash
# Run target file
python -m pytest tests/test_leap5_phase4_e2e.py -v 2>&1 | tee target_test_output.txt

# Check for Pydantic errors
grep -i "validationerror\|pydantic" target_test_output.txt

# Verify pass rate
pytest tests/test_leap5_phase4_e2e.py --tb=no -q 2>&1 | tail -1
```

### 4.4 Full Suite Validation
```bash
# Run full suite
FORCE_RUN_ALL_TESTS=1 python run_tests.py --run-all 2>&1 | tee full_suite_output.txt

# Verify 100% pass rate
grep "passed" full_suite_output.txt | tail -1
```

## 5. Rollback Strategy

If dependency installation fails:
1. Restore previous requirements.txt from git: `git checkout requirements.txt`
2. Document conflict in issue tracker
3. Investigate version conflicts: `pip check`
4. Create isolated venv for testing: `python -m venv test_env`

## 6. Success Metrics

| Metric | Target | Validation Command |
|--------|--------|-------------------|
| Collection errors | 0 | `pytest --collect-only -q 2>&1 \| grep -c ERROR` |
| Import errors | 0 | `pytest --collect-only -q 2>&1 \| grep -c ModuleNotFoundError` |
| Tests collected | ≥1762 | `pytest --collect-only -q 2>&1 \| tail -1` |
| Pass rate | 100% | `python run_tests.py --run-all 2>&1 \| tail -5` |
| Pydantic errors | 0 | `pytest tests/test_leap5_phase4_e2e.py -v 2>&1 \| grep -c ValidationError` |

## 7. Constitutional Compliance

### Article I: Complete Context Before Action
- All dependencies resolved before test execution
- No partial installations (atomic pip install operation)
- Retry with backoff if installation fails (2x, 3x multiplier)

### Article II: 100% Verification and Stability
- Zero tolerance for test failures
- 100% pass rate required (1762/1762)
- All tests run to completion (no skips)

### Article III: Automated Local Enforcement
- Pre-commit hooks validate dependencies exist
- pytest collection gates test execution
- No manual override authority

### Article IV: Continuous Learning
- Store successful dependency resolution pattern
- Tag with: ['dependency', 'pip', 'test_fixes', 'success']
- Confidence: 1.0 (proven successful)

### Article V: Spec-Driven Development
- This specification defines acceptance criteria
- Task graph traces to this spec
- All validation gates explicitly defined

## 8. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Version conflicts | High | Use `pip install --upgrade`, check conflicts first |
| Additional failures | Medium | 5 retry attempts, high token budget for fixes |
| Timeout on full suite | Low | Use `LOCAL_MODEL_TEST_WORKERS=3`, pytest-xdist |
| Multiple Pydantic errors | Medium | Follow ADR-008 strict typing patterns |

## 9. References

- **ADR-001**: Complete Context Before Action
- **ADR-002**: 100% Verification and Stability
- **ADR-003**: Automated Local Enforcement
- **ADR-004**: Continuous Learning and Improvement
- **ADR-008**: Strict Typing (Pydantic patterns)

## 10. Traceability

| Task | Acceptance Criteria Section |
|------|---------------------------|
| code_add_joblib_dependency | 3.1 Dependency Resolution |
| code_install_dependencies | 3.2 Installation Success |
| test_verify_imports | 3.3 Test Collection Success |
| code_fix_pydantic_validation_errors | 3.4 Target File Success |
| test_verify_100_percent_pass | 3.5 Full Suite Success |
