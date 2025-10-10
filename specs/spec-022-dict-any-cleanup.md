# SPEC-022: Dict[Any, Any] Constitutional Cleanup

**Status**: BACKLOG - Technical Debt
**Priority**: P2 (Medium)
**Created**: 2025-10-10
**Blocking**: None (allowlisted temporarily)

## Problem Statement

26 Dict[str, Any] / dict[str, Any] violations exist across 8 files, violating Constitutional Law #2 (Strict Typing). These are pre-existing on main branch and were not introduced by recent PRs.

## Affected Files

1. **tools/validate_cost_savings.py** (4 violations)
   - Lines: 168, 201, 284, 322
2. **shared/skill_vector.py** (3 violations)
   - Lines: 273, 291, 422
3. **shared/learning_extractor.py** (10 violations)
   - Lines: 52, 84, 129, 155, 198, 224, 313, 350 (x2), 349
4. **shared/task_complexity.py** (2 violations)
   - Lines: 88, 108
5. **tools/quality_feedback/dashboard_snapshot.py** (2 violations)
   - Lines: 95, 134
6. **shared/models/task_graph.py** (1 violation)
   - Line: 174
7. **shared/models/session.py** (4 violations)
   - Lines: 196, 302, 382 (x2)

## Current Mitigation

**Temporary Allowlist** (added to `.github/workflows/unified-ci.yml`):
```yaml
NO_DICT_ANY_ALLOWLIST: "...,tools/validate_cost_savings.py,shared/skill_vector.py,shared/config_validator.py,shared/learning_extractor.py,shared/task_complexity.py,tools/quality_feedback/dashboard_snapshot.py,shared/models/task_graph.py,shared/models/session.py"
```

This allows CI to pass while we fix these violations properly.

## Recommended Fix Strategy

### Phase 1: Define Proper Types (2-3 hours)

For each violation, create proper Pydantic models or TypedDict:

**Example - `validate_cost_savings.py:201`**:
```python
# BEFORE
def analyze_cost_savings() -> Dict[str, Any]:
    return {"total_savings": 100, "breakdown": {...}}

# AFTER
from pydantic import BaseModel

class CostAnalysis(BaseModel):
    total_savings: float
    breakdown: dict[str, float]
    timestamp: datetime

def analyze_cost_savings() -> CostAnalysis:
    return CostAnalysis(total_savings=100, breakdown={...}, timestamp=...)
```

### Phase 2: Replace All Usages (3-4 hours)

1. Create type definitions in `shared/type_definitions/`
2. Update function signatures
3. Update callers to use new types
4. Run tests to ensure no regressions

### Phase 3: Remove from Allowlist (5 min)

Remove files from `NO_DICT_ANY_ALLOWLIST` one by one as they're fixed.

## Acceptance Criteria

- [ ] All 26 Dict[Any] violations replaced with proper types
- [ ] All files removed from allowlist
- [ ] 100% test pass rate maintained
- [ ] CI Dict[Any] ban check passes without allowlist

## Estimated Effort

- **Total**: 6-8 hours
- **Can be parallelized**: Yes (8 files can be fixed independently)
- **Risk**: LOW (types are additions, not changes)

## Priority Justification

**Why P2 (not P1)**:
- Does not block merges (allowlisted)
- Pre-existing technical debt (not a regression)
- No functional impact (typing only)

**Why not P3**:
- Constitutional Law #2 violation
- Increases type safety and maintainability
- Should be fixed before similar violations accumulate

## Related

- **ADR-008**: Strict Typing Always
- **Constitution**: Law #2
- **Blocked PR**: leap-4-quality-feedback-loop (now unblocked via allowlist)