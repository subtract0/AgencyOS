# ADR-022: Autonomous-Development-Ready Auditor - Executive Summary

## The Vision: From 5/5 Stars to 6/5 Stars

**Current State (Phase 4 Complete - 5/5 Stars)**:
```
Continuous Auditor (M4 Pro Local)
  ↓
328 Accurate Recommendations (AST-based, zero false positives)
  ↓
Human Interpretation Required ← BOTTLENECK
  ↓
Manual Fix Application (days/weeks)
```

**Target State (Autonomous-Ready - 6/5 Stars)**:
```
Continuous Auditor (M4 Pro Local)
  ↓
Enhanced Recommendations (with autonomous metadata)
  ↓
Auto-Classification (confidence + risk scores)
  ↓
AgencyCodeAgent Autonomous Fixes (60-70% automated)
  ↓
Human Review (30-40% high-risk only)
```

## The Problem

The Phase 4 continuous audit system generates **328 high-quality recommendations**, but each recommendation requires **human interpretation** before AgencyCodeAgent can act:

1. **No Confidence Scores** - Is this safe to auto-fix?
2. **No Fix Code** - What's the actual patch?
3. **No Dependency Analysis** - What order to apply fixes?
4. **No Risk Assessment** - What could go wrong?
5. **No Validation Strategy** - Which tests to run?
6. **No Learning Integration** - Have we done this before successfully?

**Result**: 328 recommendations sit idle, waiting for human bandwidth.

## The Solution: Enhanced Recommendation Model

Add **autonomous execution metadata** to each recommendation:

```python
class EnhancedRecommendation(BaseModel):
    # Existing fields (title, summary, locations, steps...)

    # NEW: Autonomous Metadata
    auto_fixable: bool              # Can be fixed without human review
    fix_confidence: float           # 0.0-1.0 confidence score
    fix_difficulty: FixDifficulty   # trivial/simple/moderate/complex

    generated_fix: GeneratedFix     # LLM-generated patch (ready to apply)
    dependencies: DependencyInfo    # Safe ordering info
    risk_factors: RiskFactors       # Quantified risk (0.0-1.0)
    validation_plan: ValidationPlan # Exact test commands
    learning_metadata: LearningMetadata  # VectorStore success patterns
```

## Key Innovations

### 1. Auto-Fixability Classification

**Algorithm**:
- **TRIVIAL** (auto=True, conf=0.95): Pure deletions, <5 lines, syntax-only validation
- **SIMPLE** (auto=True, conf=0.85): Single function edits, unit tests
- **MODERATE** (auto=False, conf=0.65): Multi-function, integration tests
- **COMPLEX** (auto=False, conf=0.40): Architectural, full suite

**Example**:
```markdown
Recommendation 042: Remove commented code (38 lines)
  ↓
Classification: TRIVIAL
  auto_fixable: True
  fix_confidence: 0.95
  fix_difficulty: trivial
  validation: syntax-only
```

### 2. LLM-Generated Fix Code

**Using qwen2.5-coder:32b** (already available locally):

```python
fix_generator.generate_fix(recommendation)
  ↓
Generated Fix:
  - original_code: "# commented block..."
  - fixed_code: ""  (deletion)
  - patch_format: unified diff
  - validation_code: compile check
  - confidence: 0.90
```

**Ready for `apply_and_verify_patch.py`** tool (existing infrastructure).

### 3. Dependency-Aware Ordering

**AST-based import graph**:

```python
File A imports File B
Recommendation 42: Refactor File B
Recommendation 43: Update File A

Dependencies:
  Rec 43 depends_on: [Rec 42]

Execution Order: 42 → 43 (safe)
```

Prevents cascading test failures.

### 4. Risk Quantification

**Risk score calculation** (0.0-1.0):
- Modifies public API: +0.25
- No test coverage: +0.20
- Changes core logic: +0.15
- Multi-file impact: +0.15
- External dependencies: +0.10
- Database changes: +0.10
- Affects critical path: +0.05

**Risk levels**:
- **ZERO** (0.0-0.1): Apply immediately
- **LOW** (0.1-0.3): Apply with notification
- **MEDIUM** (0.3-0.6): Human review required
- **HIGH** (0.6-0.8): Architectural decision
- **CRITICAL** (0.8-1.0): Manual only

### 5. Specific Validation Strategies

**No more vague "run tests"**:

```python
ValidationPlan(
    strategy: ValidationStrategy.UNIT_TESTS,
    test_commands: [
        "pytest tests/test_validator.py::test_input_validation",
        "pytest tests/test_validator.py::test_edge_cases"
    ],
    estimated_time: 2.3,  # seconds
    success_criteria: ["All tests pass", "No syntax errors"],
    rollback_plan: "git revert HEAD"
)
```

### 6. Learning-Driven Confidence Boost

**VectorStore integration**:

```python
# Query for similar past fixes
similar_fixes = VectorStore.search(
    "remove commented code validator.py",
    tags=["autonomous_fix", "success", "pruning"]
)

# 8/10 similar fixes succeeded
success_rate = 0.80

# Boost confidence
if success_rate > 0.80:
    fix_confidence += 0.10  # 0.85 → 0.95
```

## Autonomous Safety Thresholds

**AgencyCodeAgent applies fix autonomously IF**:
```python
recommendation.auto_fixable == True
AND recommendation.fix_confidence >= 0.80
AND recommendation.risk_score < 0.30
AND len(recommendation.constitutional_violations) == 0
AND recommendation.validation_strategy != MANUAL_REVIEW
```

**Otherwise**: Create GitHub issue for human review.

## Impact Projections

### Quantified Benefits

| Metric | Current | With ADR-022 | Improvement |
|--------|---------|--------------|-------------|
| Auto-fixable recommendations | 0% | 60-70% | ∞ |
| Human fix time (per rec) | 30 min | 6 min | 80% reduction |
| Time to fix 328 recs | 164 hours | 33 hours | 131 hours saved |
| Rollback rate | N/A | <5% | Low risk |
| Fix success rate | N/A | >90% | High confidence |

### Graduated Autonomy Distribution

**Out of 328 recommendations**:
- **TRIVIAL** (auto=True, conf=0.95): ~100 recommendations (30%)
  - Pure deletions, unused imports
  - Apply immediately, zero risk

- **SIMPLE** (auto=True, conf=0.85): ~130 recommendations (40%)
  - Extract functions, simple refactors
  - Apply with unit test validation

- **MODERATE** (auto=False, conf=0.65): ~65 recommendations (20%)
  - Multi-function changes
  - Human review → then apply

- **COMPLEX** (auto=False, conf=0.40): ~33 recommendations (10%)
  - Architectural decisions
  - Manual implementation

**Autonomous Rate**: 70% (230/328 recommendations)

## Constitutional Compliance

### Article I: Complete Context Before Action ✓

**How**:
- Classifiers read entire files before classification
- Dependency analyzer builds complete import graph
- Fix generator reads full code sections
- Risk scorer examines test coverage, critical paths

**Example**: Before marking as "trivial", classifier reads function, checks imports, analyzes test coverage.

### Article II: 100% Verification and Stability ✓

**How**:
- Validation strategies specify exact pytest commands
- Generated fixes include validation code
- Test execution required before commit
- Rollback automated on test failure

**Example**: SIMPLE fixes require unit tests. Fix not applied if ANY test fails.

### Article III: Automated Merge Enforcement ✓

**How**:
- Auto-fixability thresholds enforced programmatically
- No manual override of risk scores
- Validation strategies automated (pytest execution)
- Confidence/risk gates are absolute barriers

**Example**: `risk_score >= 0.30` → `auto_fixable = False` (no exceptions).

### Article IV: Continuous Learning and Improvement ✓ (PRIMARY)

**How**:
- VectorStore queries for similar fix success patterns
- Success probability calculated from historical data
- Successful fixes stored as learning patterns
- Confidence boosted by learning metadata

**Example**: Query VectorStore for similar fixes. If 8/10 succeeded, boost confidence +0.10.

### Article V: Spec-Driven Development ✓

**How**:
- Audit recommendations ARE specifications
- Fix generator treats recommendations as formal specs
- Validation strategies enforce spec compliance
- Constitutional compliance section maps to articles

**Example**: Recommendation → Fix generator implements spec → Tests validate → Commit references spec.

## Implementation Roadmap

### Phase 1: Data Models (Week 1)
- Create `shared/models/auditor.py`
- Define EnhancedRecommendation + sub-models
- Write unit tests for validation
- **Deliverable**: Type-safe Pydantic models

### Phase 2: Classifiers (Week 2)
- Implement AutoFixabilityClassifier
- Add trivial/simple/moderate/complex logic
- Integrate VectorStore learning
- **Deliverable**: Classification algorithm with >80% accuracy

### Phase 3: Fix Generation (Week 3)
- Implement FixCodeGenerator
- Prompt engineering for qwen2.5-coder:32b
- Unified diff patch generation
- **Deliverable**: LLM-generated fixes for 30 test recommendations

### Phase 4: Risk & Dependencies (Week 4)
- Implement DependencyAnalyzer (AST import graph)
- Implement RiskScorer (quantified 0.0-1.0)
- **Deliverable**: Risk scores + dependency ordering for all recommendations

### Phase 5: Integration (Week 5)
- Update continuous_audit_m4pro.py
- Migrate to EnhancedRecommendation
- Async fix generation
- **Deliverable**: Full codebase scan with autonomous metadata

### Phase 6: Autonomous Fixer Enhancement (Week 6)
- Update autonomous_recommendation_fixer.py
- Confidence/risk-based decision logic
- VectorStore learning storage
- **Deliverable**: Autonomous application of 50 recommendations

### Validation (Weeks 7-8)
- Test autonomous fixes on 100 recommendations
- Measure success rate, rollback rate
- Tune thresholds (confidence, risk)
- **Deliverable**: >90% success rate, <5% rollback rate

### Production Deployment (Week 9)
- Deploy to continuous audit pipeline
- Monitor telemetry for 1 week
- **Deliverable**: 60-70% autonomous fix rate

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Auto-fix rate | >60% | % of recommendations with auto_fixable=True |
| Fix confidence | >0.80 | Average confidence for auto-fixable items |
| Success rate | >90% | % of auto-fixes passing validation |
| Rollback rate | <5% | % of applied fixes rolled back |
| Time savings | 80% | Reduction in human fix time |
| Constitutional compliance | 100% | All 5 articles satisfied |

## Risks & Mitigations

### Risk 1: Bad Auto-Fixes
**Likelihood**: Medium
**Impact**: High (code breakage)

**Mitigation**:
- Confidence threshold (>0.80)
- Risk threshold (<0.30)
- Test validation before commit
- Automated rollback on failure

### Risk 2: LLM Hallucination
**Likelihood**: Low
**Impact**: Medium (incorrect fix)

**Mitigation**:
- Syntax validation first
- Test execution second
- Compare fix against recommendation steps
- Human review for confidence <0.90

### Risk 3: Dependency Graph Errors
**Likelihood**: Low
**Impact**: Medium (wrong fix order)

**Mitigation**:
- Conservative dependency analysis (err safe)
- Manual ordering fallback
- Dry-run mode for validation

### Risk 4: Performance Degradation
**Likelihood**: Low
**Impact**: Low (2-5s per recommendation)

**Mitigation**:
- Async fix generation (parallel processing)
- Batch processing (10 fixes at once)
- Telemetry monitoring

## Cost-Benefit Analysis

### Costs
- **Development time**: 30 hours (6 weeks part-time)
- **Initial setup**: 2-5s per recommendation (one-time)
- **Ongoing overhead**: Minimal (automated after setup)
- **Storage**: ~3x larger recommendation JSON files

### Benefits
- **Time savings**: 131 hours saved (328 recs × 24 min saved)
- **Quality improvement**: Consistent fix application
- **Learning accumulation**: VectorStore patterns grow over time
- **Developer focus**: Humans review only high-risk changes

**ROI**: 437% (131 hours saved / 30 hours invested)

## Alternatives Rejected

### 1. Rule-Based Classifiers (No LLM)
- **Pro**: Deterministic, faster (<100ms)
- **Con**: Brittle, limited to simple patterns
- **Rejected**: qwen2.5-coder:32b already available, superior quality

### 2. GitHub Issues + Manual Fixes
- **Pro**: Zero automation risk
- **Con**: Slow (days/weeks), contradicts autonomous goal
- **Rejected**: Defeats purpose of autonomous auditor

### 3. Diff-Based Fix Generation
- **Pro**: No LLM needed, deterministic
- **Con**: Requires before/after examples, inflexible
- **Rejected**: Insufficient for varied fix types

## Recommendation

**APPROVE ADR-022** for implementation.

**Rationale**:
1. **Massive ROI**: 437% return on 30-hour investment
2. **Constitutional Compliance**: Satisfies all 5 articles
3. **Low Risk**: Safety thresholds + test validation + rollback
4. **Proven Technology**: Builds on Phase 4 (5/5 stars) foundation
5. **Graduated Autonomy**: 70% auto, 30% human (optimal balance)

**Next Steps**:
1. Approve ADR-022
2. Begin Phase 1 (Data Models) next week
3. Target production deployment in 9 weeks

---

**Document Version**: 1.0
**Author**: ChiefArchitect (via Claude Code)
**Date**: 2025-10-07
**Review Date**: 2025-11-01
