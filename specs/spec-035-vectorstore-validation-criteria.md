# Specification: VectorStore Validation Criteria for Test Recovery Patterns

**Spec ID**: `spec-035-vectorstore-validation-criteria`
**Status**: Draft
**Author**: PlannerAgent
**Created**: 2025-10-24
**Last Updated**: 2025-10-24
**Version**: 1.0.0
**Tier**: Tier 1 (Specification)

---

## Executive Summary

This specification defines comprehensive validation criteria for VectorStore test recovery patterns stored during the recent test suite recovery work (achieving 100% test pass rate from 38 failures). The goal is to verify that the 8 test recovery patterns stored in VectorStore are queryable, have correct metadata, follow the expected schema, and are accessible cross-session per Article IV (Continuous Learning) requirements.

**Context**: During test suite recovery (spec-test-suite-recovery-38-failures.md), successful patterns were stored to VectorStore for future reuse. We need validation criteria to ensure these patterns meet quality standards and are actually usable for learning.

**Current State**:
- 8 test recovery patterns stored in VectorStore
- Patterns include: signature mismatch fixes, Pydantic validation fixes, mock replacement strategies
- Unknown: Pattern queryability, metadata completeness, schema compliance

**Target State**:
- All 8 patterns validated against comprehensive criteria
- Queryable via AgentContext.search_memories() with expected tags
- Metadata complete (confidence ≥0.6, proper tags, timestamps)
- Cross-session accessible
- Schema-compliant with expected structure

---

## Goals

### Primary Goals

1. **Define Queryability Criteria**: Specify how patterns should be searchable via VectorStore
2. **Define Metadata Schema**: Document required metadata fields (confidence, tags, timestamps)
3. **Define Validation Thresholds**: Set minimum confidence scores and evidence counts
4. **Define Cross-Session Requirements**: Ensure patterns persist and are discoverable across sessions
5. **Define Failure Conditions**: Explicitly state what constitutes an invalid pattern

### Success Metrics

- ✅ All 8 test recovery patterns pass validation criteria
- ✅ Patterns queryable with tags: `["test_recovery", "success", "pattern"]`
- ✅ All patterns have confidence ≥0.6 (Article IV minimum)
- ✅ 100% of patterns have required metadata fields
- ✅ Cross-session queries return patterns stored in previous sessions

---

## Non-Goals

- Creating new test recovery patterns (validation only, not generation)
- Modifying VectorStore implementation (use existing API)
- Changing Article IV requirements (validate against current constitution)
- Testing VectorStore performance (focus on correctness, not speed)

---

## Personas

### Primary Persona: LearningAgent
- **Needs**: Retrieve high-quality test recovery patterns for future fixes
- **Pain Point**: Cannot trust VectorStore patterns if quality is unknown
- **Success Metric**: 100% of retrieved patterns are actionable and correct

### Secondary Persona: CodingAgent
- **Needs**: Apply learned patterns when fixing similar test failures
- **Pain Point**: Patterns with incomplete metadata or low confidence are risky to apply
- **Success Metric**: Can filter patterns by confidence (≥0.6) and tags reliably

### Tertiary Persona: QualityEnforcerAgent
- **Needs**: Validate that learning system meets Article IV requirements
- **Pain Point**: No formal validation criteria for VectorStore patterns
- **Success Metric**: Constitutional compliance verified through automated validation

---

## Acceptance Criteria

### Functional Criteria

#### Criterion 1: Queryability (Tag-Based Search)
**Requirement**: All 8 test recovery patterns must be queryable via tag-based search.

**Validation Steps**:
1. Query VectorStore with tags: `["test_recovery", "success"]`
2. Query VectorStore with tags: `["pattern", "pydantic"]`
3. Query VectorStore with tags: `["signature_mismatch", "fix"]`
4. Query VectorStore with tags: `["mock_replacement"]`

**Expected Behavior**:
- Each query returns ≥1 pattern (no zero results for valid tag combinations)
- Results are sorted by relevance (most recent or highest confidence first)
- No duplicate patterns in results (unique by key)

**Success Threshold**: 100% of tag queries return expected patterns

#### Criterion 2: Metadata Completeness
**Requirement**: All patterns must have complete metadata following the expected schema.

**Required Metadata Fields**:
```python
{
    "key": str,                    # Unique identifier (required)
    "content": dict,               # Pattern content (required)
    "tags": list[str],             # Categorization tags (required, ≥3 tags)
    "confidence": float,           # Confidence score 0.0-1.0 (required, ≥0.6)
    "timestamp": str,              # ISO 8601 timestamp (required)
    "evidence_count": int,         # Number of supporting occurrences (required, ≥3)
    "session_id": str,             # Session where pattern was created (required)
    "pattern_type": str,           # Category: "signature_fix", "pydantic_fix", etc. (required)
    "success_rate": float,         # Success rate 0.0-1.0 (optional, default 1.0)
    "description": str,            # Human-readable description (required)
    "actionable_insight": str,     # How to apply this pattern (required)
}
```

**Validation Steps**:
1. Read all 8 patterns from VectorStore
2. For each pattern, verify all required fields are present
3. For each field, verify type correctness (e.g., confidence is float, not string)
4. Verify field constraints (e.g., confidence ≥0.6, evidence_count ≥3)

**Success Threshold**: 100% of patterns have all required metadata fields with valid values

#### Criterion 3: Schema Compliance
**Requirement**: Pattern content must follow the standardized test recovery pattern schema.

**Expected Pattern Content Schema**:
```python
# Pattern content structure (stored in "content" field)
{
    "problem_description": str,        # What test failure was fixed
    "root_cause": str,                 # Why test was failing
    "solution_strategy": str,          # How fix was applied
    "code_changes": list[dict],        # Specific code changes made
    "tests_affected": list[str],       # Test files/functions fixed
    "constitutional_article": str,     # Which article this supports (e.g., "Article II")
    "similar_patterns": list[str],     # Related patterns (VectorStore keys)
}
```

**Validation Steps**:
1. Extract `content` field from each pattern
2. Verify all required content fields are present
3. Verify `code_changes` list is non-empty (≥1 change)
4. Verify `tests_affected` list is non-empty (≥1 test)
5. Verify `constitutional_article` references valid article (I-V)

**Success Threshold**: 100% of patterns follow the schema

#### Criterion 4: Confidence Score Validation
**Requirement**: All patterns must meet Article IV confidence threshold (≥0.6).

**Validation Logic**:
```python
def validate_confidence(pattern: dict) -> bool:
    """Article IV requirement: min confidence 0.6"""
    confidence = pattern.get("confidence", 0.0)
    evidence_count = pattern.get("evidence_count", 0)

    # Basic threshold check
    if confidence < 0.6:
        return False

    # Confidence should correlate with evidence
    # Formula: confidence ≈ min(1.0, evidence_count / 3)
    expected_confidence = min(1.0, evidence_count / 3)
    tolerance = 0.2  # Allow 20% deviation

    if abs(confidence - expected_confidence) > tolerance:
        return False

    return True
```

**Validation Steps**:
1. For each pattern, extract confidence and evidence_count
2. Verify confidence ≥0.6 (constitutional minimum)
3. Verify confidence correlates with evidence (not arbitrary)
4. Verify evidence_count ≥3 (minimum for high confidence)

**Success Threshold**: 100% of patterns pass confidence validation

#### Criterion 5: Cross-Session Accessibility
**Requirement**: Patterns stored in previous sessions must be queryable in new sessions.

**Validation Steps**:
1. Create new AgentContext with fresh session_id
2. Query VectorStore with `include_session=False` (cross-session search)
3. Query for test recovery patterns: `["test_recovery", "success"]`
4. Verify patterns from original session are returned

**Expected Behavior**:
- Patterns stored in session A are queryable from session B
- Cross-session queries return patterns with original session_id preserved
- No session isolation (patterns are globally accessible by default)

**Success Threshold**: 100% of patterns accessible cross-session

#### Criterion 6: Tag Consistency
**Requirement**: All patterns must have consistent, well-structured tags.

**Required Tag Structure**:
- **Agent tag**: One of `["coder", "planner", "auditor", "test_generator", "quality_enforcer"]`
- **Category tag**: One of `["test_recovery", "pattern", "learning"]`
- **Outcome tag**: One of `["success", "failure"]`
- **Domain tag**: One of `["signature_fix", "pydantic_fix", "mock_replacement", "e2e_fix"]`
- **Session tag**: `f"session:{session_id}"` (auto-added by AgentContext)

**Validation Steps**:
1. For each pattern, extract tags list
2. Verify ≥3 tags present (minimum for categorization)
3. Verify at least one tag from each required category
4. Verify no invalid/typo tags (e.g., "successs" instead of "success")

**Success Threshold**: 100% of patterns have well-formed tags

---

### Non-Functional Criteria

#### Criterion 7: Performance (Query Latency)
**Requirement**: Tag-based queries should return results in <100ms (90th percentile).

**Validation Steps**:
1. Run 100 tag-based queries for test recovery patterns
2. Measure query latency for each
3. Calculate 90th percentile latency

**Success Threshold**: p90 latency <100ms

**Note**: This is a quality check, not a blocking requirement (focus is correctness, not speed).

#### Criterion 8: Storage Durability
**Requirement**: Patterns should persist across VectorStore restarts (if using persistence backend).

**Validation Steps**:
1. Store a test pattern to VectorStore
2. Restart VectorStore (if applicable - e.g., Firestore backend)
3. Query for the test pattern
4. Verify pattern is still present with correct metadata

**Success Threshold**: 100% of patterns persist across restarts (if persistence enabled)

**Note**: If using in-memory VectorStore (no persistence), this criterion is N/A.

---

### Constitutional Compliance Criteria

#### Criterion 9: Article IV Compliance
**Requirement**: VectorStore integration meets Article IV requirements.

**Article IV Requirements**:
- VectorStore integration is mandatory (not optional)
- Agents MUST query learnings before decisions
- Agents MUST store successful patterns after operations
- Min confidence: 0.6
- Min evidence: 3 occurrences

**Validation Steps**:
1. Verify USE_ENHANCED_MEMORY environment variable is "true"
2. Verify all 8 patterns have confidence ≥0.6
3. Verify all 8 patterns have evidence_count ≥3
4. Verify patterns are tagged with agent name (e.g., "coder", "test_generator")
5. Verify patterns have actionable insights (reusable by future agents)

**Success Threshold**: 100% Article IV compliance

#### Criterion 10: Pattern Actionability
**Requirement**: Patterns must be actionable (future agents can apply them).

**Actionability Criteria**:
- Pattern has clear description (what problem was solved)
- Pattern has solution strategy (how to apply fix)
- Pattern has code changes (concrete examples)
- Pattern has success rate (evidence it works)

**Validation Steps**:
1. For each pattern, extract `description` and `actionable_insight`
2. Verify description is non-empty and descriptive (≥20 chars)
3. Verify actionable_insight provides clear guidance (≥50 chars)
4. Verify `code_changes` includes concrete examples (≥1 change)

**Success Threshold**: 100% of patterns are actionable

---

## Expected Schema Definition

### VectorStore Memory Record Schema

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class TestRecoveryPattern(BaseModel):
    """
    VectorStore pattern for test recovery learnings.

    Article IV compliance: All patterns stored via AgentContext.store_memory()
    must conform to this schema for quality assurance.
    """

    # Required metadata (VectorStore standard)
    key: str = Field(..., description="Unique pattern identifier")
    timestamp: datetime = Field(..., description="When pattern was created")
    confidence: float = Field(..., ge=0.6, le=1.0, description="Confidence score (Article IV: ≥0.6)")
    evidence_count: int = Field(..., ge=3, description="Number of supporting occurrences")
    session_id: str = Field(..., description="Session where pattern was created")

    # Pattern categorization
    pattern_type: Literal[
        "signature_fix",
        "pydantic_fix",
        "mock_replacement",
        "e2e_fix",
        "general_fix"
    ] = Field(..., description="Category of test recovery pattern")

    tags: list[str] = Field(..., min_items=3, description="Categorization tags (≥3 required)")

    # Pattern content (test recovery specific)
    description: str = Field(..., min_length=20, description="Human-readable description")
    actionable_insight: str = Field(..., min_length=50, description="How to apply this pattern")

    # Success metrics
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Success rate of pattern")

    # Pattern details
    content: dict = Field(..., description="Structured pattern content")

    class Config:
        extra = "forbid"  # Article II: Strict typing, no extra fields


class PatternContent(BaseModel):
    """
    Structured content for test recovery patterns.

    Stored in the 'content' field of TestRecoveryPattern.
    """

    problem_description: str = Field(..., description="What test failure was fixed")
    root_cause: str = Field(..., description="Why test was failing")
    solution_strategy: str = Field(..., description="How fix was applied")

    code_changes: list[dict] = Field(..., min_items=1, description="Specific code changes made")
    tests_affected: list[str] = Field(..., min_items=1, description="Test files/functions fixed")

    constitutional_article: Literal["Article I", "Article II", "Article III", "Article IV", "Article V"] = Field(
        ..., description="Which constitutional article this pattern supports"
    )

    similar_patterns: list[str] = Field(default_factory=list, description="Related patterns (VectorStore keys)")

    class Config:
        extra = "forbid"
```

---

## Validation Test Plan (NECESSARY Pattern)

### Normal (N) - Happy Path Tests

**N1: Query patterns by tags**
- Query: `["test_recovery", "success"]`
- Expected: All 8 patterns returned
- Validation: Verify count = 8

**N2: Extract metadata from patterns**
- Action: Read all patterns, extract metadata
- Expected: All required fields present
- Validation: 100% metadata completeness

**N3: Cross-session query**
- Action: Create new session, query patterns from old session
- Expected: Patterns from old session returned
- Validation: Cross-session accessibility works

### Edge (E) - Boundary Conditions

**E1: Minimum confidence threshold**
- Query: Patterns with confidence = 0.6 (minimum)
- Expected: Patterns with confidence = 0.6 are included
- Validation: Threshold is inclusive (≥ not >)

**E2: Empty tag query**
- Query: `tags=[]`
- Expected: No results or all results (implementation-dependent)
- Validation: No crash, graceful handling

**E3: Unknown tag query**
- Query: `["nonexistent_tag"]`
- Expected: Empty results (no patterns with this tag)
- Validation: No error, empty list returned

### Cascading (C) - Integration Impact

**C1: Query + filter by confidence**
- Action: Query patterns, filter by confidence ≥0.8
- Expected: Only high-confidence patterns returned
- Validation: Filtering works correctly

**C2: Query + sort by timestamp**
- Action: Query patterns, sort by newest first
- Expected: Most recent patterns first
- Validation: Sorting works correctly

**C3: Store new pattern, verify queryability**
- Action: Store new test pattern, immediately query
- Expected: New pattern is queryable
- Validation: No caching issues

### Essential (E) - Critical Functionality

**E1: All 8 patterns queryable**
- Action: Query for each pattern individually by key
- Expected: 8/8 patterns found
- Validation: No missing patterns

**E2: All patterns have confidence ≥0.6**
- Action: Extract confidence from all patterns
- Expected: min(confidences) ≥ 0.6
- Validation: Article IV threshold met

**E3: All patterns have required metadata**
- Action: Validate schema for all patterns
- Expected: 100% schema compliance
- Validation: Pydantic validation passes

### Security (S) - Threat Validation

**S1: Pattern content sanitization**
- Action: Verify patterns don't contain sensitive data (API keys, passwords)
- Expected: No secrets in pattern content
- Validation: Regex scan for secret patterns

**S2: Tag injection prevention**
- Action: Attempt to store pattern with malicious tags (e.g., `"; DROP TABLE--"`)
- Expected: Tags sanitized or rejected
- Validation: No code injection via tags

**S3: Confidence score manipulation**
- Action: Attempt to store pattern with confidence >1.0
- Expected: Validation error (confidence ∈ [0.0, 1.0])
- Validation: Pydantic validation enforces bounds

### Spec (S) - Requirements Traceability

**S1: All acceptance criteria covered**
- Action: Map each acceptance criterion to test case
- Expected: 1:1 mapping (10 criteria → 10 test cases)
- Validation: Traceability matrix complete

**S2: Schema validation**
- Action: Validate all patterns against TestRecoveryPattern schema
- Expected: 100% validation success
- Validation: Pydantic model_validate() passes

**S3: Constitutional compliance**
- Action: Verify Article IV requirements met
- Expected: All patterns meet Article IV criteria
- Validation: Confidence ≥0.6, evidence ≥3, tags present

### Accessibility (A) - Usability

**A1: Error messages clear**
- Action: Trigger validation error (e.g., missing metadata field)
- Expected: Clear error message explaining what's missing
- Validation: Error message includes field name and expected type

**A2: Pattern descriptions readable**
- Action: Read pattern descriptions for all 8 patterns
- Expected: Descriptions are human-readable (≥20 chars, descriptive)
- Validation: Manual review of descriptions

**A3: Query results sorted**
- Action: Query patterns, verify sort order
- Expected: Results sorted by relevance (timestamp or confidence)
- Validation: Sort order is predictable and documented

### Resilience (R) - Fault Tolerance

**R1: Handle missing metadata gracefully**
- Action: Store pattern with incomplete metadata (e.g., missing confidence)
- Expected: Validation error or default value applied
- Validation: No crash, graceful handling

**R2: Handle corrupted VectorStore**
- Action: Simulate VectorStore corruption (e.g., delete internal data)
- Expected: Graceful degradation (return empty results, not crash)
- Validation: No exceptions, error logged

**R3: Retry on query failure**
- Action: Simulate transient VectorStore failure
- Expected: Query retries with exponential backoff
- Validation: Retry logic executes, query succeeds on retry

### Year-round (Y) - Long-term Stability

**Y1: Patterns remain valid over time**
- Action: Store pattern, query after 7 days (simulated)
- Expected: Pattern still queryable, metadata unchanged
- Validation: No time-based degradation

**Y2: Schema evolution support**
- Action: Add new optional field to schema, verify backward compatibility
- Expected: Old patterns still valid, new patterns include new field
- Validation: Backward compatibility maintained

**Y3: Cross-version compatibility**
- Action: Store pattern in VectorStore v1, query from VectorStore v2
- Expected: Pattern queryable across versions
- Validation: No version lock-in

---

## Validation Thresholds

### Quality Thresholds

| Metric | Minimum Threshold | Target | Critical |
|--------|------------------|--------|----------|
| Queryability rate | 100% | 100% | Yes |
| Metadata completeness | 100% | 100% | Yes |
| Schema compliance | 100% | 100% | Yes |
| Confidence score (min) | 0.6 | 0.8 | Yes |
| Evidence count (min) | 3 | 5 | No |
| Tag count (min) | 3 | 5 | No |
| Cross-session accessibility | 100% | 100% | Yes |
| Pattern actionability | 80% | 100% | No |

### Performance Thresholds

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Query latency (p90) | <50ms | <100ms | <500ms |
| Query latency (p99) | <100ms | <200ms | <1000ms |
| Pattern storage time | <10ms | <50ms | <200ms |
| Memory usage (patterns) | <10MB | <50MB | <200MB |

**Note**: Performance thresholds are quality goals, not blocking requirements. Correctness > speed.

---

## Failure Conditions

### Critical Failures (Block Validation)

1. **Missing Required Metadata**: Pattern lacks key, confidence, or tags
   - **Impact**: Pattern cannot be queried or applied
   - **Mitigation**: Validation at storage time (Pydantic model)

2. **Confidence Below Threshold**: Pattern has confidence <0.6
   - **Impact**: Violates Article IV constitutional requirement
   - **Mitigation**: Reject pattern at storage, require more evidence

3. **Schema Violation**: Pattern content doesn't match expected structure
   - **Impact**: Future agents cannot parse or apply pattern
   - **Mitigation**: Pydantic strict mode validation

4. **Zero Query Results**: Tag query returns no patterns when patterns should exist
   - **Impact**: Learning system is broken, patterns not discoverable
   - **Mitigation**: Investigate VectorStore indexing, verify tags

### Non-Critical Failures (Warning Only)

1. **Low Evidence Count**: Pattern has evidence_count <3
   - **Impact**: Confidence score may be inflated
   - **Mitigation**: Flag for manual review, request more evidence

2. **Missing Actionable Insight**: Pattern lacks clear guidance
   - **Impact**: Pattern is less useful for future agents
   - **Mitigation**: Enhance pattern description, add examples

3. **Slow Query Performance**: Query latency >100ms (p90)
   - **Impact**: User experience degraded
   - **Mitigation**: Optimize VectorStore indexing (FAISS)

4. **Duplicate Patterns**: Multiple patterns with same content
   - **Impact**: VectorStore clutter, redundant results
   - **Mitigation**: Deduplication logic, merge similar patterns

---

## Dependencies

### Prerequisites
- ✅ VectorStore implementation (agency_memory/vector_store.py)
- ✅ AgentContext with memory API (shared/agent_context.py)
- ✅ 8 test recovery patterns stored (from spec-test-suite-recovery-38-failures)
- ✅ Article IV constitutional requirements (constitution.md)

### External Dependencies
- Pydantic 2.0+ (schema validation)
- Python 3.11+ (type hints, dataclasses)
- pytest 8.0+ (test framework)

### Internal Dependencies
- EnhancedMemoryStore (agency_memory/enhanced_memory_store.py)
- MemorySearchResult model (shared/models/memory.py)
- Constitutional validator (tools/constitutional_intelligence/)

---

## Implementation Phases

### Phase 1: Schema Definition (Tier 3, Simple)
**Goal**: Define Pydantic models for validation

**Tasks**:
1. Create `TestRecoveryPattern` Pydantic model
2. Create `PatternContent` Pydantic model
3. Add schema to `shared/models/memory.py`
4. Document schema in this spec

**Estimated Tokens**: 3,000 (schema definition, documentation)

### Phase 2: Validation Implementation (Tier 2, Moderate)
**Goal**: Implement validation logic

**Tasks**:
1. Create `validate_test_recovery_pattern()` function
2. Implement queryability checks
3. Implement metadata completeness checks
4. Implement schema compliance checks
5. Implement confidence threshold checks

**Estimated Tokens**: 10,000 (validation logic, error handling)

### Phase 3: Test Coverage (Tier 2, Moderate)
**Goal**: Write tests for all NECESSARY categories

**Tasks**:
1. Write Normal (N) tests (3 tests)
2. Write Edge (E) tests (3 tests)
3. Write Cascading (C) tests (3 tests)
4. Write Essential (E) tests (3 tests)
5. Write Security (S) tests (3 tests)
6. Write Spec (S) tests (3 tests)
7. Write Accessibility (A) tests (3 tests)
8. Write Resilience (R) tests (3 tests)
9. Write Year-round (Y) tests (3 tests)

**Estimated Tokens**: 15,000 (27 tests, AAA pattern)

### Phase 4: Pattern Validation (Tier 1, Complex)
**Goal**: Validate all 8 test recovery patterns

**Tasks**:
1. Load all 8 patterns from VectorStore
2. Run validation for each pattern
3. Generate validation report
4. Fix any invalid patterns
5. Re-validate and confirm 100% compliance

**Estimated Tokens**: 8,000 (analysis, reporting, fixes)

### Phase 5: Documentation (Tier 3, Simple)
**Goal**: Document validation process and results

**Tasks**:
1. Create validation report template
2. Document validation criteria
3. Create usage examples
4. Update this spec with findings

**Estimated Tokens**: 4,000 (documentation)

---

## Risk Assessment

### High Risk
- **Risk**: Pattern schema changes during validation
- **Mitigation**: Lock Pydantic schema version, version control
- **Impact**: Medium (could invalidate validation logic)

### Medium Risk
- **Risk**: VectorStore queries return incomplete results
- **Mitigation**: Verify VectorStore indexing, add retry logic
- **Impact**: Low (patterns exist, just not queryable)

### Low Risk
- **Risk**: Performance thresholds not met
- **Mitigation**: Optimize queries, add FAISS indexing
- **Impact**: Very Low (correctness > speed)

---

## Estimated Cost

**Total Tokens**: ~40,000
**Tier Breakdown**:
- Tier 1 (complex): 8,000 tokens @ $4.00/1M = $0.032
- Tier 2 (moderate): 25,000 tokens @ $1.50/1M = $0.038
- Tier 3 (simple): 7,000 tokens @ $0/1M (local) = $0.000

**Total Estimated Cost**: $0.070 (~7 cents)

**Value Proposition**: Validate VectorStore learning system for Article IV compliance, ensure 8 test recovery patterns are reusable.

**Estimated Time**: 45-60 minutes (phases run sequentially)

---

## Constitutional Alignment

### Article I: Complete Context Before Action
- ✅ All 8 patterns identified and validated
- ✅ Complete schema definition before validation
- ✅ No partial validation (all 10 criteria or none)

### Article II: 100% Verification and Stability
- ✅ Target: 100% of patterns pass validation
- ✅ Zero invalid patterns tolerated
- ✅ Validation enforced at storage time

### Article III: Automated Enforcement
- ✅ Pydantic validation enforces schema (no manual checks)
- ✅ Validation runs automatically on pattern storage
- ✅ No bypass authority for quality standards

### Article IV: Continuous Learning and Improvement
- ✅ **PRIMARY MANDATE**: Validate VectorStore patterns meet Article IV requirements
- ✅ All patterns have confidence ≥0.6 (constitutional minimum)
- ✅ All patterns have evidence ≥3 (quality threshold)
- ✅ Patterns are queryable and actionable (reusable by future agents)
- ✅ Cross-session accessibility verified (institutional knowledge)

### Article V: Spec-Driven Development
- ✅ This specification drives all validation implementation
- ✅ Acceptance criteria explicit and measurable
- ✅ Test plan follows NECESSARY pattern

---

## Review & Approval

**Stakeholders**: @am
**Technical Reviewers**: LearningAgent, QualityEnforcerAgent, ChiefArchitect

**Review Checklist**:
- [ ] Spec completeness: All validation criteria defined?
- [ ] Acceptance criteria: Clear, measurable, testable?
- [ ] Schema definition: Complete, type-safe, Pydantic-compliant?
- [ ] Test plan: NECESSARY pattern compliance (9/9 categories)?
- [ ] Risk assessment: Mitigation strategies reasonable?
- [ ] Cost estimate: Within budget ($0.070 << $10 limit)?
- [ ] Constitutional alignment: Articles I-V compliance verified?

**Approval Decision**: _______________
**Reason (if rejected)**: _______________
**Suggested Improvements**: _______________

---

## Appendices

### Appendix A: Example Valid Pattern

```python
# Example test recovery pattern (valid)
valid_pattern = {
    "key": "test_recovery_signature_fix_20251015_143022",
    "timestamp": "2025-10-15T14:30:22.123456",
    "confidence": 0.95,
    "evidence_count": 5,
    "session_id": "session_20251015_140000_abc123",
    "pattern_type": "signature_fix",
    "tags": [
        "test_recovery",
        "success",
        "pattern",
        "signature_mismatch",
        "two_stage_orchestrator",
        "coder"
    ],
    "description": "Fix two-stage orchestrator test signature mismatch by updating tests to use input_value parameter",
    "actionable_insight": "When tests fail with 'unexpected keyword argument', check if test signature matches actual API. Update test calls to use correct parameter names (e.g., input_value instead of user_input).",
    "success_rate": 1.0,
    "content": {
        "problem_description": "14 tests in test_two_stage_orchestrator.py failing with TypeError: orchestrate() got an unexpected keyword argument 'user_input'",
        "root_cause": "Implementation changed to orchestrate(input_value=None) but tests still using old signature orchestrate(user_input=..., input_mode=...)",
        "solution_strategy": "Update all test calls to use input_value parameter, remove input_mode (auto-detected)",
        "code_changes": [
            {
                "file": "tests/orchestrator/test_two_stage_orchestrator.py",
                "before": "orchestrate(user_input='Add JWT', input_mode=InputMode.NATURAL_LANGUAGE)",
                "after": "orchestrate(input_value='Add JWT')",
                "lines_changed": 14
            }
        ],
        "tests_affected": [
            "test_orchestrate_natural_language",
            "test_orchestrate_auto_select",
            "test_orchestrate_with_context"
        ],
        "constitutional_article": "Article II",
        "similar_patterns": [
            "test_recovery_pydantic_fix_20251015_150000"
        ]
    }
}

# Validate with Pydantic
pattern_model = TestRecoveryPattern(**valid_pattern)
assert pattern_model.confidence >= 0.6  # Article IV requirement
assert len(pattern_model.tags) >= 3  # Minimum categorization
```

### Appendix B: Example Invalid Pattern (Missing Metadata)

```python
# Example test recovery pattern (invalid - missing confidence)
invalid_pattern = {
    "key": "test_recovery_broken_pattern",
    "timestamp": "2025-10-15T14:30:22.123456",
    # "confidence": 0.95,  # ❌ MISSING - validation will fail
    "evidence_count": 5,
    "session_id": "session_20251015_140000_abc123",
    "pattern_type": "signature_fix",
    "tags": ["test_recovery", "success"],
    "description": "Some fix",
    "actionable_insight": "Do something",
    "content": {...}
}

# Pydantic validation raises ValidationError
try:
    pattern_model = TestRecoveryPattern(**invalid_pattern)
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Output: 1 validation error for TestRecoveryPattern
    #         confidence
    #           field required (type=value_error.missing)
```

### Appendix C: Validation Report Template

```markdown
# VectorStore Pattern Validation Report

**Date**: 2025-10-24
**Patterns Validated**: 8
**Validation Status**: PASS/FAIL

## Summary

- **Queryability**: 8/8 patterns queryable (100%)
- **Metadata Completeness**: 8/8 patterns complete (100%)
- **Schema Compliance**: 8/8 patterns valid (100%)
- **Confidence Threshold**: 8/8 patterns ≥0.6 (100%)
- **Cross-Session Accessibility**: 8/8 patterns accessible (100%)

## Detailed Results

### Pattern 1: test_recovery_signature_fix_20251015_143022
- ✅ Queryable: YES
- ✅ Metadata Complete: YES
- ✅ Schema Valid: YES
- ✅ Confidence: 0.95 (≥0.6)
- ✅ Evidence Count: 5 (≥3)
- ✅ Tags: 6 tags (≥3)
- ✅ Cross-Session: YES

### Pattern 2: ...
(Repeat for all 8 patterns)

## Failures

(List any validation failures, root causes, and remediation steps)

## Recommendations

1. Continue storing patterns with current schema
2. Monitor confidence scores (target ≥0.8)
3. Increase evidence count threshold to 5 (currently 3)
4. Add deduplication logic for similar patterns

## Constitutional Compliance

- ✅ Article I: Complete context (all 8 patterns validated)
- ✅ Article II: 100% verification (zero invalid patterns)
- ✅ Article III: Automated enforcement (Pydantic validation)
- ✅ Article IV: Learning integration (patterns meet quality standards)
- ✅ Article V: Spec-driven (validation follows spec-035)
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-24 | PlannerAgent | Initial specification |

---

**End of Specification**

**Next Steps**:
1. Review and approve specification
2. Proceed to implementation (Phase 1-5)
3. Generate validation report
4. Store validation results to VectorStore (meta-learning)
