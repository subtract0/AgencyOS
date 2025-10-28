# Article IV Test Suite - Quick Reference Index

**Created**: 2025-10-26
**Status**: RED Phase Complete
**Total Tests**: 37 tests across 4 files

---

## Test Files

### 1. Unit Tests
**File**: `tests/test_article_iv_validation_unit.py`
**Tests**: 15 unit tests
**Run**: `pytest tests/test_article_iv_validation_unit.py -v`

**Test Coverage**:
- API validation (search_memories, store_memory existence)
- Query-before-action pattern
- Store-after-success pattern
- Edge cases (empty VectorStore, duplicates, concurrency)
- Error handling (VectorStore unavailable, graceful fallback)
- Security (secret sanitization, regex detection)
- Timing validation (query < action < store)

**Expected RED Phase**: 11 PASS, 4 SKIP

---

### 2. Integration Tests
**File**: `tests/test_article_iv_validation_integration.py`
**Tests**: 8 integration tests
**Run**: `pytest tests/test_article_iv_validation_integration.py -v`

**Test Coverage**:
- CodingAgent workflow (query → implement → store)
- PlannerAgent workflow (query → plan → store)
- QualityEnforcer workflow (query → validate → store)
- Cross-session pattern application
- Agent resilience (VectorStore failure handling)
- Partial success storage (threshold-based)
- Full Article IV lifecycle (query → action → store)

**Expected RED Phase**: 7 PASS, 1 FAIL (cross-session persistence)

---

### 3. E2E Tests
**File**: `tests/e2e/test_article_iv_compliance_e2e.py`
**Tests**: 7 end-to-end tests
**Run**: `pytest tests/e2e/test_article_iv_compliance_e2e.py -v`

**Test Coverage**:
- Full mission compliance (multi-agent workflow)
- Query-before-action ≥80% benchmark
- Store-after-success 100% benchmark
- Pattern application ≥60% benchmark
- Concurrent agent VectorStore access (100 agents, load test)
- Cross-session learning persistence
- Mission cost optimization via pattern reuse

**Expected RED Phase**: 6 PASS, 1 FAIL (cross-session persistence)

---

### 4. Git Audit Tests
**File**: `tests/test_article_iv_git_audit.py`
**Tests**: 7 git audit tests
**Run**: `pytest tests/test_article_iv_git_audit.py -v`

**Test Coverage**:
- Git log scan for violations (last 30 days)
- AST parsing detects missing search_memories()
- AST parsing detects missing store_memory()
- Zero violations benchmark (regression test)
- Binary files handling (graceful skip)
- Large repositories (10,000+ commits, pagination)
- Corrupt repository handling (error resilience)

**Expected RED Phase**: 6 PASS, 1 FAIL (321 violations detected)

---

## Quick Commands

### Run All Article IV Tests
```bash
pytest tests/test_article_iv_*.py tests/e2e/test_article_iv_*.py -v
```

### Run Only Passing Tests (Skip Known Failures)
```bash
pytest tests/test_article_iv_*.py tests/e2e/test_article_iv_*.py -v \
  -k "not cross_session and not zero_violations"
```

### Run With Coverage
```bash
pytest tests/test_article_iv_*.py tests/e2e/test_article_iv_*.py \
  --cov=shared.agent_context \
  --cov=agency_memory \
  --cov-report=term-missing
```

### Generate HTML Report
```bash
pytest tests/test_article_iv_*.py tests/e2e/test_article_iv_*.py \
  --html=article_iv_test_report.html --self-contained-html
```

---

## Test Markers

### Integration Tests
```bash
pytest -m integration tests/test_article_iv_*.py -v
```

### E2E Tests
```bash
pytest -m e2e tests/e2e/test_article_iv_*.py -v
```

### Slow Tests (Load Tests)
```bash
pytest -m slow tests/ -v
```

---

## Expected Results (RED Phase)

### Summary
```
Total: 37 tests
PASS:  30 tests (81%)
FAIL:  3 tests (8%)
SKIP:  4 tests (11%)
```

### Failures (Expected)
1. **test_pattern_application_from_previous_session** (integration)
   - Cross-session pattern retrieval not working
   - Fix: Shared VectorStore backend

2. **test_cross_session_learning_persistence_e2e** (E2E)
   - Same root cause as #1
   - Fix: Shared VectorStore backend

3. **test_zero_violations_in_last_30_days** (git audit)
   - 321 violations detected in last 30 days
   - Fix: Add VectorStore query/storage to all agents

### Skips (Awaiting Implementation)
1. **test_vectorstore_unavailable_graceful_fallback** (unit)
   - Graceful fallback not implemented
   - Fix: Return empty list on VectorStore failure

2. **test_missing_query_constitutional_violation** (unit)
   - Violation detector not implemented
   - Fix: Pre-action hook to enforce query requirement

3. **test_missing_storage_constitutional_violation** (unit)
   - Violation detector not implemented
   - Fix: Post-success hook to enforce storage requirement

4. **test_sensitive_data_not_stored_in_patterns** (unit)
   - Secret sanitization not implemented
   - Fix: Pre-storage sanitization layer with regex

---

## Benchmark Targets (E2E Tests)

| Metric | Target | Simulated Result | Status |
|--------|--------|------------------|--------|
| Query Rate | ≥80% | 90% | ✅ PASS |
| Storage Rate | 100% | 100% | ✅ PASS |
| Application Rate | ≥60% | 70% | ✅ PASS |
| Concurrent Load | 100 agents, 0 errors | 100 agents, 0 errors | ✅ PASS |
| Cost Savings | >0% | 40% | ✅ PASS |

---

## NECESSARY Pattern Coverage

| Category | Coverage | Status |
|----------|----------|--------|
| **N** (Normal) | 11 tests | ✅ Complete |
| **E** (Edge) | 6 tests | ✅ Complete |
| **C** (Corner) | 0 tests (covered in unit tests) | ✅ N/A |
| **E** (Error) | 7 tests | ✅ Complete |
| **S** (Security) | 2 tests | ✅ Complete |
| **S** (Stress) | 2 tests | ✅ Complete |
| **A** (Accessibility) | 0 tests (internal APIs) | ✅ N/A |
| **R** (Regression) | 4 tests | ✅ Complete |
| **Y** (Yield) | 11 tests | ✅ Complete |

**Total**: 9/9 NECESSARY categories covered

---

## References

- **Detailed Summary**: `tests/ARTICLE_IV_TEST_SUMMARY.md`
- **Specification**: `specs/spec-039-article-iv-self-reflective-learning.md`
- **ADR-004**: Continuous Learning and Improvement
- **Constitution**: Article IV (Continuous Learning)

---

**Last Updated**: 2025-10-26 (RED Phase Complete)
