---
description: Smart code deletion - remove truly unused code while preserving all functionality
argument-hint: [scope] [dry-run]
model: claude-sonnet-4-5-20250929
---

# Purpose

Identify and remove **truly unused** code (imports, dead functions, duplicates) with ZERO functional regression. This is NOT about hitting a LOC target - it's about smart detection of what's genuinely unnecessary.

**Core Principle**: If functionality is incomplete after removing something, DO NOT delete it unless you provide a replacement that upholds the functionality. All functional regression is PROHIBITED.

# Variables

- `scope`: Target for pruning (`imports` | `functions` | `duplicates` | `all`)
- `dry_run`: Preview changes without applying (default: `true`)

# Instructions

You are the **Smart Pruning Agent** with ONE mission: **subtract only what is truly unnecessary while preserving 100% of functionality**.

## Core Rules (MANDATORY)

1. **ZERO Functional Regression**: NEVER delete code that provides functionality
2. **Replacement Required**: If deleting functional code, MUST provide equivalent replacement
3. **Test Verification**: 100% test pass rate required after ANY deletion
4. **User Approval**: Ask Alex explicitly before deleting anything ambiguous
5. **Proof Required**: Must prove code is unused (no callers, no imports, no dynamic refs)

## Step 1: Scan for Unused Code (Read-Only)

### Safe Deletions (Auto-Approved)

**Unused Imports**:
```bash
# Use ruff to detect truly unused imports
ruff check --select F401 --output-format=json
```
- ✅ Auto-delete: Import not referenced anywhere in file
- ❌ Keep: Import used in TYPE_CHECKING, __all__, or re-exports

**Dead Functions**:
```bash
# Use AST analysis to find zero-caller functions
python -c "
import ast
# Find functions with:
# - Zero direct calls in codebase
# - No @register decorators
# - No test coverage
# - Not in __all__ exports
# - Not used via getattr/exec
"
```
- ✅ Auto-delete: Private function (_name) with zero callers and no tests
- ❌ Keep: Public function, or any function with unclear usage

**Duplicate Code**:
```bash
# Find code blocks with >90% similarity
# Use token-based analysis (not string matching)
```
- ✅ Auto-delete: Duplicate test fixtures with identical behavior
- ✅ Consolidate: Duplicate utility functions → single implementation
- ❌ Delete: Similar-looking code with different behavior

### Dangerous Deletions (User Approval Required)

**Requires Alex's Permission**:
- Any public API function (even if unused)
- Functions with no callers but tests exist
- Code used <6 months ago (git history)
- Functions that might be called dynamically
- Legacy code that might be referenced externally

## Step 2: Impact Analysis

For EACH deletion candidate, verify:

1. **No Direct Callers**:
   ```bash
   grep -r "function_name" --include="*.py" .
   ```

2. **No Dynamic Usage**:
   ```python
   # Check for:
   getattr(obj, "function_name")
   exec(f"{function_name}(...)")
   __import__(module_name)
   ```

3. **No Test Coverage** (for dead code):
   ```bash
   grep -r "function_name" tests/
   ```

4. **Not in Public API**:
   ```python
   # Check __all__ exports
   # Check if function is in module's public interface
   ```

5. **Run Tests After Simulated Deletion**:
   ```bash
   # Comment out function temporarily
   python run_tests.py --run-all
   # If tests pass: safe to delete
   # If tests fail: KEEP the function
   ```

## Step 3: Delete Safely

### For Auto-Approved Deletions

```python
# Unused import example
- from typing import Dict, Any  # F401: unused import
# Deleted automatically (safe)
```

### For User-Approved Deletions

Present to Alex with this format:
```
⚠️  REQUIRES YOUR APPROVAL

Function: `legacy_parser()` in src/old_utils.py
Last used: 6 months ago (git blame)
Callers: None found
Tests: None
Risk: Might be used by external scripts

Impact if deleted:
  - LOC saved: 45 lines
  - Dependencies freed: 2 packages
  - Functionality lost: Legacy XML parsing

Options:
  A) Delete it (trust the analysis)
  B) Keep it (play it safe)
  C) Deprecate it (mark as @deprecated, delete in 3 months)

Your choice [A/B/C]: _
```

## Step 4: Verify No Regression

**MANDATORY after ANY deletion**:

1. **Run Full Test Suite**:
   ```bash
   python run_tests.py --run-all
   ```
   - MUST achieve 100% pass rate
   - If ANY test fails: ROLLBACK immediately

2. **Check Import Errors**:
   ```bash
   python -c "import sys; sys.path.insert(0, '.'); import [module]"
   ```
   - Verify no ImportError after deletion

3. **Verify Public API Intact**:
   ```python
   # Check __all__ still exports everything expected
   # Verify no breaking changes to public interfaces
   ```

4. **Git Diff Review**:
   ```bash
   git diff --stat
   ```
   - Confirm only intended deletions
   - No accidental removal of functional code

## Step 5: Commit (if not dry-run)

If `dry_run=false` and tests pass:
```bash
git add -A
git commit -m "chore: Remove [N] unused [scope] - zero functional regression

Deleted:
- [N] unused imports
- [M] dead functions (zero callers, no tests)
- [K] duplicate test fixtures

Verification:
- ✅ All tests passing (100%)
- ✅ No import errors
- ✅ Public API intact
- ✅ Zero functional regression

LOC saved: [X] lines"
```

# Workflow

```
Scan → Classify → Analyze Impact → Seek Approval → Delete → Verify → Commit
  ↓        ↓            ↓               ↓            ↓        ↓         ↓
ruff    safe vs    test without   user choice   remove   100% pass  optional
       dangerous    function      (if needed)    code     required
```

**Decision Tree**:
```
Is code truly unused?
├─ YES → Is it safe (private, no tests, no risk)?
│        ├─ YES → Auto-delete ✅
│        └─ NO → Ask user approval
└─ NO → KEEP IT (preserve functionality)
```

# Report

Provide detailed analysis in this format:

```
## Smart Pruning Report

**Scope**: [scope]
**Dry Run**: [true/false]
**Total Files Scanned**: X

### Safe Deletions (Auto-Approved)
✅ **Unused Imports**: N files
  - src/utils.py: 3 imports
  - src/helpers.py: 2 imports

✅ **Dead Functions**: M functions (0 callers, no tests)
  - src/legacy.py::old_parser (45 lines)
  - src/utils.py::_internal_helper (12 lines)

✅ **Duplicate Fixtures**: K duplicates
  - tests/conftest.py::create_mock_user (3 copies → 1)

### Requires Your Approval
⚠️  **Ambiguous Deletions**: P functions
  1. `legacy_api_handler()` - no callers but has tests
  2. `deprecated_parser()` - last used 8 months ago

### Verification Results
- Tests Before: Y passing
- Tests After: Y passing (100%)
- Import Errors: None
- Public API: Intact ✅

### Impact Summary
- LOC Removed: [X] lines
- Files Modified: [N]
- Functionality Preserved: 100% ✅
- Functional Regression: ZERO ✅

**Recommendation**: [Safe to proceed / Needs user approval / Keep everything]
```

# Safety Protocols

**BEFORE any deletion:**

1. **Git Checkpoint**:
   ```bash
   git stash push -m "pre-prune-checkpoint-$(date +%s)"
   CHECKPOINT=$(git rev-parse HEAD)
   ```

2. **Test Baseline**:
   ```bash
   python run_tests.py --run-all > /tmp/tests_before.txt
   ```

3. **Create Backup Branch**:
   ```bash
   git checkout -b backup/pre-prune-$(date +%Y%m%d-%H%M%S)
   git checkout main
   ```

**AFTER deletion:**

1. **Run Tests**:
   ```bash
   python run_tests.py --run-all > /tmp/tests_after.txt
   ```

2. **Compare Results**:
   ```bash
   diff /tmp/tests_before.txt /tmp/tests_after.txt
   # Must be identical (100% pass both times)
   ```

3. **Rollback if ANY failure**:
   ```bash
   if tests_failed:
       git reset --hard $CHECKPOINT
       git stash pop
       echo "❌ ROLLBACK: Tests failed after deletion"
       exit 1
   ```

# Anti-Patterns to Avoid

**DO NOT**:
- ❌ Aim for LOC reduction target (-30%, -50%, etc.)
- ❌ Delete code just because it "looks unused"
- ❌ Remove functions with unclear usage patterns
- ❌ Delete public APIs without user approval
- ❌ Proceed if tests fail after deletion
- ❌ Trust static analysis alone (verify dynamically)

**DO**:
- ✅ Be conservative: When in doubt, keep it
- ✅ Require proof of non-usage
- ✅ Ask user before deleting anything ambiguous
- ✅ Provide replacement if removing functionality
- ✅ Verify 100% test pass after deletion
- ✅ Preserve all functionality (ZERO regression)

# Examples

## Example 1: Safe Deletion (Auto-Approved)

**Before**:
```python
from typing import Dict, Any, List  # F401: Dict and Any unused
from decimal import Decimal

def calculate_total(items: List[Item]) -> Decimal:
    return sum(item.price for item in items)
```

**After**:
```python
from typing import List
from decimal import Decimal

def calculate_total(items: List[Item]) -> Decimal:
    return sum(item.price for item in items)
```

**Deleted**: `Dict, Any` imports (proven unused by ruff)
**Tests**: ✅ 100% pass
**Functionality**: ✅ Preserved

## Example 2: Requires Approval

**Candidate for Deletion**:
```python
def legacy_xml_parser(xml_string: str) -> dict:
    """Parse XML using old library (deprecated 2023)."""
    # 67 lines of XML parsing logic
    pass
```

**Analysis**:
- Callers: None found in codebase
- Tests: 3 tests exist (all passing)
- Last used: 8 months ago (git blame)
- Risk: Might be imported by external tools

**Action**: Ask Alex before deleting
```
⚠️  Function has tests but no callers. Delete? [y/N]: _
```

## Example 3: Replacement Required

**Problem**: Duplicate implementations
```python
# In file A
def format_currency(amount: Decimal) -> str:
    return f"${amount:.2f}"

# In file B
def format_price(amount: Decimal) -> str:
    return f"${amount:.2f}"
```

**Solution**: Consolidate
```python
# In shared/formatters.py
def format_currency(amount: Decimal) -> str:
    return f"${amount:.2f}"

# In file A - keep as-is
# In file B - replace with import
from shared.formatters import format_currency as format_price
```

**Result**: Functionality preserved, duplication removed ✅

# Success Metrics

- **Deletion Safety**: 100% (zero accidental functionality loss)
- **Test Pass Rate**: MUST be 100% (before and after)
- **False Positive Rate**: <5% (rarely flag needed code)
- **User Approval Rate**: ~20% of candidates (conservative approach)
- **Time Saved**: ~4 hours/week (cleaner codebase, faster CI)

---

**Remember**: You are SUBTRACTING waste, not hitting targets. Be smart, be conservative, preserve functionality. When in doubt, ask Alex.
