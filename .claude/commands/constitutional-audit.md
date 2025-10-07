---
description: Real-time constitutional compliance audit with auto-healing suggestions
argument-hint: [article] [fix-mode]
model: claude-sonnet-4-5-20250929
---

# Purpose

Validate codebase against all 5 constitutional articles, suggest fixes with confidence scores from VectorStore. Proactive compliance checking to prevent violations before they reach main.

# Variables

- `article`: Target article (`I` | `II` | `III` | `IV` | `V` | `all`, default: `all`)
- `fix_mode`: Fix mode (`suggest` | `auto`, default: `suggest`)

# Instructions

## Step 1: Run Constitutional Validator

Validate codebase against selected article(s):

**Article I: Complete Context Before Action**
- Timeout handling with retry logic
- No broken windows (TODO/FIXME tracking)
- Complete verification before proceeding

**Article II: 100% Verification and Stability**
- All tests passing
- No skipped tests without justification
- No mocks in production code

**Article III: Automated Merge Enforcement**
- No bypass mechanisms in code
- Quality gates intact
- Pre-commit hooks enabled

**Article IV: Continuous Learning**
- VectorStore integration present
- context.search_memories() usage
- context.store_memory() after successes

**Article V: Spec-Driven Development**
- Complex features have spec.md
- Spec-kit methodology followed
- TodoWrite task breakdown

## Step 2: Categorize Violations

Group by:
- Severity (BLOCKER | HIGH | MEDIUM | LOW)
- Auto-fixable (Yes/No based on VectorStore patterns)
- Article violated

## Step 3: Query VectorStore for Fixes

For each violation:
```python
fixes = context.search_memories(
    tags=["healing", violation.type, "success"],
    include_session=False
)
proven_fixes = [f for f in fixes if f.confidence >= 0.6]
```

## Step 4: Apply or Suggest Fixes

**If `fix_mode=suggest`**:
- Present violations with fix confidence scores
- User chooses which to apply

**If `fix_mode=auto`**:
- Only apply fixes with confidence ≥ 0.9
- Only quality fixes (no functional changes)
- Require user approval for anything else

## Step 5: Verify Compliance

After fixes:
- Run tests (100% pass required)
- Re-run constitutional validator
- Confirm violations resolved

# Report

```
## Constitutional Audit Report

**Target**: Article [article] (or ALL)
**Fix Mode**: [suggest/auto]
**Violations Found**: X total

### Article I: Complete Context (ADR-001)
- ✅ Timeout handling: Compliant
- ❌ Broken windows: 3 TODO comments without tracking
  - Fix available: confidence 0.85

### Article II: 100% Verification (ADR-002)
- ❌ Test failures: 2 tests failing
  - Fix available: confidence 0.92
- ✅ No skipped tests: Compliant

### Article III: Automated Enforcement (ADR-003)
- ✅ No bypass mechanisms: Compliant
- ✅ Pre-commit hooks: Active

### Article IV: Continuous Learning (ADR-004)
- ❌ VectorStore queries: Missing in 5 files
  - Fix available: confidence 0.78
- ✅ Memory storage: Present

### Article V: Spec-Driven Development (ADR-007)
- ⚠️  Spec coverage: 45% (target: 60%)
  - Fix suggestion: Create specs for 3 features

### Auto-Fix Candidates (Confidence ≥ 0.9)
1. Test failures in `test_auth.py` (conf: 0.92) - READY
2. Missing VectorStore queries (conf: 0.78) - NEEDS APPROVAL

### Constitutional Compliance Score
- Overall: 73% (Target: 100%)
- Article I: 75%
- Article II: 50%
- Article III: 100%
- Article IV: 80%
- Article V: 45%

**Recommendation**: Fix 2 auto-fixable violations, then address Article V gap
```

---

**Remember**: Proactive compliance prevents violations. Run before commits for best results.
