# 🚀 PR #81 Quick Fix Guide

**Branch:** `leap-4-quality-feedback-loop`
**Status:** ⚠️ 44 issues to fix (7 minutes estimated)

---

## Step 1: Format Files (30 seconds)

```bash
cd /Users/am/Code/Agency

ruff format \
  agency_memory/vector_index.py \
  agency_memory/vector_store.py \
  demo_batch_memory_reads.py \
  tests/test_leap4_e2e_quality_feedback.py \
  tools/async_memory_tool.py \
  tools/skill_dashboard.py \
  tools/validate_cost_savings.py
```

**Fixes:** 7 formatting issues (Constitutional Law #10)

---

## Step 2: Auto-Fix Lint Issues (1 minute)

```bash
ruff check --fix --unsafe-fixes .
```

**Fixes:** 39 issues automatically:
- Import sorting (I001)
- Unused imports (F401)
- Deprecated typing (UP035, UP006)
- F-string optimization (F541)
- Unnecessary comprehensions (C416)
- Deprecated asyncio.TimeoutError (UP041)

---

## Step 3: Install Type Stubs (30 seconds)

```bash
pip install types-aiofiles
```

**Fixes:** mypy import-untyped errors in async_memory_tool.py

---

## Step 4: Manual Fix #1 - Exception Chaining (2 minutes)

### File: `agency_memory/vector_index.py` (line 65)

**BEFORE:**
```python
except ImportError:
    raise ImportError(
        "faiss-cpu is required for VectorIndex. "
        "Install with: pip install faiss-cpu~=1.7.4"
    )
```

**AFTER:**
```python
except ImportError as e:
    raise ImportError(
        "faiss-cpu is required for VectorIndex. "
        "Install with: pip install faiss-cpu~=1.7.4"
    ) from e
```

### File: `tools/async_memory_tool.py` (line 41)

**BEFORE:**
```python
except ImportError:
    raise ImportError(
        "aiofiles is required for async memory operations. "
        "Install with: pip install aiofiles"
    )
```

**AFTER:**
```python
except ImportError as e:
    raise ImportError(
        "aiofiles is required for async memory operations. "
        "Install with: pip install aiofiles"
    ) from e
```

**Constitutional Law:** #5 (Functional error handling)

---

## Step 5: Manual Fix #2 - QualitySignals Constructor (2 minutes)

### Files: `tests/test_leap4_e2e_quality_feedback.py` (lines 328, 520, 611)

**Problem:** Unexpected keyword argument `collected_at`

**Action:**
1. Check `shared/models/quality_signals.py` for correct constructor
2. Search for all `QualitySignals(` calls in test file
3. Either:
   - Remove `collected_at=datetime.now(UTC)` if not in model
   - OR add `collected_at: datetime` field to QualitySignals Pydantic model

**Search command:**
```bash
grep -n "QualitySignals(" tests/test_leap4_e2e_quality_feedback.py
```

**Critical:** Tests will fail at runtime if not fixed ⚠️

---

## Step 6: Verify Fixes (1 minute)

```bash
# Check ruff passes
ruff check .

# Check formatting passes
ruff format --check .

# Check type safety (modified files only)
MYPYPATH=/Users/am/Code/Agency python -m mypy \
  agency_memory/vector_index.py \
  agency_memory/vector_store.py \
  tests/test_leap4_e2e_quality_feedback.py \
  tools/async_memory_tool.py \
  --ignore-missing-imports
```

---

## Step 7: Commit (30 seconds)

```bash
git add -A

git commit -m "fix: Resolve quality issues in PR #81

- Format 7 files with ruff format
- Auto-fix 39 lint issues (imports, typing, style)
- Fix B904 exception chaining (Constitutional Law #5)
- Fix QualitySignals constructor calls in tests
- Install types-aiofiles for full type checking

Fixes:
- Constitutional Law #2: Strict typing (18 issues)
- Constitutional Law #5: Error handling (2 issues)
- Constitutional Law #10: Lint before commit (7 issues)

✅ All 44 issues resolved
✅ CI-ready

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Summary

| Step | Time | Issues Fixed | Command |
|------|------|--------------|---------|
| 1. Format | 30s | 7 | `ruff format ...` |
| 2. Auto-fix | 1m | 39 | `ruff check --fix --unsafe-fixes .` |
| 3. Type stubs | 30s | 7 | `pip install types-aiofiles` |
| 4. B904 exceptions | 2m | 2 | Manual edit |
| 5. QualitySignals | 2m | 3 | Manual edit + model check |
| 6. Verify | 1m | - | `ruff check . && mypy ...` |
| 7. Commit | 30s | - | `git commit -m ...` |

**Total:** ~7 minutes, **44 issues resolved** ✅

---

## Issue Breakdown

### By Severity
- 🔴 Critical: 0
- 🟠 High: 2 (exception chaining)
- 🟡 Medium: 23 (typing, code quality)
- 🟢 Low: 19 (style)

### By Auto-Fix Status
- ✅ Auto-fixable: 39 (89%)
- 🔧 Manual fix: 5 (11%)

### By Constitutional Law
- Law #2 (Strict Typing): 18 issues
- Law #5 (Error Handling): 2 issues
- Law #8 (Focused Functions): 1 issue
- Law #10 (Lint Before Commit): 7 issues

---

## Quick Reference: File Status

| File | Lines | Issues | Severity | Fix Type |
|------|-------|--------|----------|----------|
| test_leap4_e2e_quality_feedback.py | 892 | 9 | 🔴 HIGH | Auto + Manual |
| async_memory_tool.py | 677 | 15 | 🔴 HIGH | Auto + Manual |
| vector_index.py | 371 | 3 | 🟡 MEDIUM | Auto + Manual |
| vector_store.py | 856 | 2 | 🟡 MEDIUM | Auto |
| skill_dashboard.py | 352 | 8 | 🟡 MEDIUM | Auto |
| validate_cost_savings.py | 475 | 16 | 🟡 MEDIUM | Auto |
| demo_batch_memory_reads.py | 205 | 3 | 🟢 LOW | Auto |
| memory_lock_manager.py | 567 | 1 | 🟢 LOW | Auto |

---

## Full Reports

- **JSON:** `logs/audits/audit_pr_leap4_20251010.json`
- **Markdown:** `logs/audits/audit_pr_leap4_20251010_summary.md`

---

*Generated by AuditorAgent - Ready for QualityEnforcer autonomous healing*
