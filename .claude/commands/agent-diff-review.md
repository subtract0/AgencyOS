---
description: Review git diff before commit with constitutional checklist
argument-hint: [scope] [strict]
model: claude-sonnet-4-5-20250929
---

# Agent Diff Review

## Purpose

**Pre-commit quality gate** that reviews git diff against all constitutional laws and coding standards. Prevents accidental violations before they reach the repository.

## Variables

- `scope`: Diff scope (`staged` | `unstaged` | `branch` | `commit:<hash>`)
- `strict`: Enforcement level (`true` = block on violations, `false` = warn only)

## Instructions

You are the **last line of defense** before code enters the repository. Review changes against all 10 constitutional laws and quality standards.

## Step 1: Get Diff

**Staged Changes** (`scope=staged`):
```bash
git diff --staged
```

**Unstaged Changes** (`scope=unstaged`):
```bash
git diff
```

**Branch Comparison** (`scope=branch`):
```bash
git diff main...HEAD
```

**Specific Commit** (`scope=commit:<hash>`):
```bash
git show <hash>
```

## Step 2: Constitutional Compliance Check

Review against ALL 10 laws:

### Law #1: TDD - Tests Before Implementation

**Check**:
- Are test files modified/created? (`test_*.py`, `*.test.ts`)
- For new features, do tests exist BEFORE implementation?
- Are tests comprehensive (normal, edge, error cases)?

**Violations**:
- ❌ New feature without corresponding tests
- ❌ Tests added AFTER implementation (git history shows impl first)
- ❌ Incomplete test coverage

### Law #2: Strict Typing Always

**Check**:
- NO `any` type in TypeScript
- NO `Dict[Any, Any]` in Python
- All functions have type annotations
- Pydantic models used for complex types

**Pattern Scan**:
```bash
# Detect violations in diff
grep -E "(: any|Dict\[Any, ?Any\])" <(git diff --staged)
```

**Violations**:
- ❌ `user_data: Dict[Any, Any]` → Use Pydantic model
- ❌ `const user: any` → Explicit interface
- ❌ `def process(data)` → Missing type annotation

### Law #3: Validate All Inputs

**Check**:
- Public API functions validate inputs
- Zod schemas (TypeScript) or Pydantic (Python) used
- Error handling for invalid inputs

**Violations**:
- ❌ API endpoint without input validation
- ❌ Missing parameter validation

### Law #4: Use Repository Pattern

**Check**:
- NO direct database queries in business logic
- All data access through repository layer

**Pattern Scan**:
```bash
# Detect direct SQL/ORM in non-repository files
grep -E "(SELECT|INSERT|UPDATE|DELETE|\.query\(|\.execute\()" <(git diff --staged) \
  | grep -v "repository"
```

**Violations**:
- ❌ `db.query("SELECT * FROM users")` in controller
- ❌ Direct ORM calls outside repository

### Law #5: Embrace Functional Error Handling

**Check**:
- Result<T, E> pattern used for error-prone functions
- NO try/catch for control flow
- Errors returned, not thrown

**Violations**:
- ❌ `raise ValueError` for expected errors → Use Result
- ❌ Try/catch used for business logic flow

### Law #6: Standardize API Responses

**Check**:
- Consistent response format across endpoints
- Status codes follow REST conventions

**Violations**:
- ❌ Inconsistent JSON structure

### Law #7: Clarity Over Cleverness

**Check**:
- Code is readable and self-documenting
- NO clever tricks or obfuscation
- Variable names are descriptive

**Violations**:
- ❌ `x = lambda a,b: a if a>b else b` → Use clear function
- ❌ Variable names like `tmp`, `data`, `x`

### Law #8: Focused Functions

**Check**:
- Functions under 50 lines
- Single responsibility per function
- Low cyclomatic complexity

**Line Count**:
```bash
# Check function lengths in diff
awk '/^+.*def |^+.*function / { start=NR; name=$0 }
     /^+\}|^+^$/ { if (start) { len=NR-start; if (len>50) print name, len " lines" } }' \
     <(git diff --staged)
```

**Violations**:
- ❌ Function with 75 lines → Refactor into smaller functions

### Law #9: Document Public APIs

**Check**:
- Docstrings (Python) or JSDoc (TypeScript) on public functions
- Parameters documented
- Return types documented

**Violations**:
- ❌ Public function without docstring

### Law #10: Lint Before Commit

**Check**:
- NO linting errors in changes
- Consistent formatting

**Run Linters**:
```bash
ruff check --select ALL --output-format=json <changed_files>  # Python
eslint <changed_files> --format json  # TypeScript
```

**Violations**:
- ❌ Any linting errors

## Step 3: Additional Quality Checks

**Beyond Constitutional Laws**:

### Code Duplication
```bash
# Look for copy-paste patterns
git diff --staged | grep -E "^\+.*def |^\+.*function " | sort | uniq -d
```

### Dead Code
```bash
# Detect commented-out code blocks
git diff --staged | grep -E "^\+\s*#.*def |^\+\s*//.*function "
```

### TODOs Without Issues
```bash
# Find TODOs without issue tracking
git diff --staged | grep -E "^\+.*TODO|^\+.*FIXME" | grep -v "#[0-9]"
```

### Sensitive Data
```bash
# Detect potential secrets
git diff --staged | grep -iE "(password|secret|api_key|token)" | grep -v "test"
```

## Step 4: Generate Review Report

Provide comprehensive analysis:

```
## Git Diff Review Report

**Scope**: [scope]
**Files Changed**: [N]
**Lines Added**: +[N]
**Lines Removed**: -[N]
**Strict Mode**: [true/false]

### Constitutional Compliance

#### Law #1: TDD ✅
- Tests created/updated: [N] files
- Test coverage: Adequate

#### Law #2: Strict Typing ❌ [VIOLATION]
- Found `Dict[Any, Any]` in src/models.py:42
- **Fix**: Replace with Pydantic model

#### Law #3: Input Validation ✅
- All API endpoints validate inputs

[... all 10 laws ...]

### Additional Quality Issues

#### Code Duplication
- `calculate_total()` duplicated in 2 files
- **Recommendation**: Extract to shared utility

#### TODOs Without Issues
- Line 67: `# TODO: optimize this` (no issue #)
- **Action**: Create issue or remove TODO

### Security Scan
✅ No sensitive data detected

### Verdict

[if strict=true]
❌ **BLOCKED** - Fix 2 constitutional violations before commit
[else]
⚠️ **WARNINGS** - 2 constitutional violations detected (not blocking)

### Violations Summary
1. **Law #2** - src/models.py:42 - Dict[Any, Any] usage
2. **Law #8** - src/utils.py:120 - Function exceeds 50 lines (67 lines)

### Required Actions
1. Replace Dict[Any, Any] with typed Pydantic model
2. Refactor 67-line function into smaller functions
3. Re-run `/agent-diff-review staged strict` to verify fixes
```

## Step 5: Block or Warn

**Strict Mode** (`strict=true`):
```python
if violations_found and strict:
    raise PreCommitBlocked(
        violations=violations,
        message="Fix all violations before commit (Article III enforcement)"
    )
```

**Warn Mode** (`strict=false`):
```python
if violations_found:
    log_warning(violations)
    # Allow commit but record violation
```

## Integration with Pre-Commit Hook

**Git Hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Run agent diff review in strict mode
claude-code /agent-diff-review staged true

if [ $? -ne 0 ]; then
    echo "❌ Pre-commit blocked by constitutional violations"
    echo "Fix violations or use 'git commit --no-verify' (NOT recommended)"
    exit 1
fi
```

## Use Cases

### 1. Code Agent Before Commit
```
Agent: Ready to commit feature implementation
Tool: Reviews staged diff with strict=true
Result: Found Dict[Any, Any] violation → BLOCKED
Agent: Fixes violation, re-runs review → PASS → Commits
```

### 2. Developer Manual Commit
```
Developer: git commit -m "feature"
Hook: Triggers /agent-diff-review staged true
Result: 67-line function detected → BLOCKED
Developer: Refactors → Re-commits → PASS
```

### 3. Merger Agent Before PR
```
Agent: Ready to merge feature branch
Tool: Reviews full branch diff with strict=true
Result: All laws compliant → PROCEED with merge
```

## Success Metrics

- **Violation Detection Rate**: >95% (catch violations before commit)
- **False Positive Rate**: <5% (accurate detection)
- **Blocking Accuracy**: 100% (block only true violations in strict mode)
- **Review Time**: <3 seconds for typical diff
- **Prevention Rate**: >80% reduction in post-commit violations

## Article III Compliance

This tool enforces **Article III: Automated Merge Enforcement**:

1. **Zero manual overrides** (strict mode blocks unconditionally)
2. **Pre-commit quality gate** (violations caught before commit)
3. **Automated enforcement** (no human approval bypass)

---

**Remember**: This is the last checkpoint. Review thoroughly, block strictly, protect quality.
