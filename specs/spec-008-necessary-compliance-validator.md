# Specification: AST-Based NECESSARY Pattern Compliance Validator

**Spec ID**: `spec-008-necessary-compliance-validator`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-11
**Last Updated**: 2025-10-11
**Related ADRs**: ADR-002 (100% Verification), ADR-004 (Continuous Learning), ADR-011 (NECESSARY Pattern)

---

## Executive Summary

Design and implement an AST-based validation system for NECESSARY pattern compliance in generated tests. This validator will analyze test files using Python's Abstract Syntax Tree (AST) to detect quality violations including non-descriptive test names, missing AAA structure, absent docstrings, and insufficient edge case coverage. The system will provide confidence-scored auto-fix recommendations learned from VectorStore patterns, ensuring test quality compliance before merge.

---

## Goals

### Primary Goals
- [ ] **Goal 1**: Create AST-based parser for comprehensive pytest test file analysis
- [ ] **Goal 2**: Implement validation rules for NECESSARY pattern compliance (naming, structure, documentation)
- [ ] **Goal 3**: Design auto-fix strategies with confidence scoring (≥0.6 threshold)
- [ ] **Goal 4**: Integrate with TestGeneratorAgent output validation workflow
- [ ] **Goal 5**: Enable VectorStore-driven learning of proven test quality patterns

### Success Metrics
- **Validation Accuracy**: 100% detection of NECESSARY violations (zero false negatives)
- **Auto-Fix Confidence**: ≥85% fixes accepted without manual intervention (confidence ≥0.6)
- **Integration Performance**: <2s validation overhead per test file
- **Learning Effectiveness**: ≥70% auto-fix success rate after 20 validated patterns
- **Constitutional Compliance**: 100% adherence to Articles I, II, IV (context, verification, learning)

---

## Non-Goals

### Explicit Exclusions
- **Runtime Test Execution**: Validator analyzes static structure only (not test outcomes)
- **Non-Python Tests**: Focused on pytest files only (no TypeScript/JavaScript support)
- **Semantic Correctness**: Detects structural violations, not logical test flaws
- **Manual Fix Enforcement**: Provides recommendations, doesn't force changes
- **Cross-File Analysis**: Single-file scope (no inter-test dependencies)

### Future Considerations
- **Multi-Language Support**: Extend to TypeScript/Jest validation
- **Semantic Analysis**: LLM-powered test logic quality assessment
- **Test Mutation Analysis**: Verify tests catch real bugs
- **Real-Time IDE Integration**: VS Code extension with inline suggestions

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: TestGeneratorAgent
- **Description**: Automated agent generating NECESSARY-compliant tests from AuditorAgent violations
- **Goals**: Produce high-quality test code with zero manual review required
- **Pain Points**: Inconsistent test structure, non-descriptive names, missing edge cases
- **Technical Proficiency**: Expert in pytest patterns, AAA structure, TDD methodology

#### Persona 2: QualityEnforcerAgent
- **Description**: Constitutional compliance guardian ensuring Article II (100% verification)
- **Goals**: Prevent merge of substandard tests, enforce NECESSARY pattern constitutionally
- **Pain Points**: Manual test review overhead, delayed feedback on quality issues
- **Technical Proficiency**: Expert in quality gates, constitutional validation, pattern recognition

#### Persona 3: Human Developer (@am)
- **Description**: Development lead reviewing auto-generated tests for approval
- **Goals**: Quick validation of test quality, confidence in auto-generated code
- **Pain Points**: Time-consuming test reviews, unclear quality signals, inconsistent patterns
- **Technical Proficiency**: Expert in Python testing, code review best practices

### User Journeys

#### Journey 1: TestGeneratorAgent Output Validation
```
1. Agent starts with: Generated test file from NECESSARY violation report
2. Agent needs to: Validate compliance before submitting to CodeAgent
3. Agent performs: Invokes NECESSARYValidator.validate(test_file_path)
4. System responds: AST analysis detects 3 violations (naming, missing AAA, no docstrings)
5. System continues: Provides confidence-scored auto-fixes (0.85, 0.92, 0.78)
6. Agent applies: High-confidence fixes (≥0.6) automatically
7. Agent re-validates: Zero violations after fixes applied
8. Agent achieves: 100% compliant test file ready for integration
```

#### Journey 2: Pre-Commit Quality Gate
```
1. User starts with: Commit containing modified test files
2. System needs to: Enforce NECESSARY compliance before merge (Article II)
3. System performs: Pre-commit hook runs NECESSARYValidator on all test_*.py files
4. System responds: Validation report: 2 files clean, 1 file with 4 violations
5. System continues: Auto-fix suggestions displayed with confidence scores
6. User reviews: Applies 3 high-confidence fixes, manually adjusts 1 edge case
7. User re-commits: All tests pass NECESSARY validation
8. User achieves: Constitutional compliance verified before merge
```

#### Journey 3: Learning Pattern Extraction
```
1. System starts with: 50 validated test files with successful fixes applied
2. System needs to: Extract patterns for improved auto-fix accuracy (Article IV)
3. System performs: LearningAgent analyzes fix history from VectorStore
4. System identifies: "test_when_then" naming pattern has 95% acceptance rate
5. System updates: NECESSARYValidator confidence scores for this pattern (+0.15)
6. System stores: Refined pattern in VectorStore with tags ["test_quality", "naming"]
7. System achieves: Continuous improvement of auto-fix recommendations
```

---

## Functional Requirements

### FR-1: AST Parsing and Analysis

#### FR-1.1: Test File Discovery
- **Input**: File path (string) or directory path for batch analysis
- **Output**: List of `.py` files matching pattern `test_*.py` or `*_test.py`
- **Validation**: Filter non-test files, exclude `__init__.py`, respect `.gitignore`

#### FR-1.2: Python AST Construction
- **Parser**: Use `ast.parse()` with error handling for syntax errors
- **Node Types**: Extract `FunctionDef`, `AsyncFunctionDef`, `ClassDef`, `Module`, `Expr` (docstrings)
- **Error Handling**: Return structured error for unparseable files (syntax errors)
- **Example**:
```python
import ast

def parse_test_file(file_path: str) -> TestFileAST | ParseError:
    """
    Parse test file into AST representation.

    Returns:
        TestFileAST with functions, classes, imports, docstrings
        ParseError if file has syntax errors
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=file_path)
        return extract_test_components(tree, file_path)
    except SyntaxError as e:
        return ParseError(file=file_path, line=e.lineno, message=str(e))
```

#### FR-1.3: Test Function Extraction
- **Target Nodes**: `FunctionDef` nodes with names starting with `test_`
- **Extracted Data**:
  - Function name (full identifier)
  - Line number and column offset
  - Docstring (first `Expr` node with `Constant` string)
  - Parameters (for fixtures, parametrization detection)
  - Decorators (`@pytest.mark.*`, `@pytest.fixture`)
  - Body structure (statement types, comment nodes)
- **Pydantic Model**:
```python
class TestFunction(BaseModel):
    """Parsed test function metadata."""
    name: str
    line_number: int
    col_offset: int
    docstring: str | None
    parameters: list[str]
    decorators: list[str]
    has_aaa_comments: bool  # Detected from comment nodes
    assertion_count: int
    complexity: int  # Cyclomatic complexity from AST
```

#### FR-1.4: Class-Based Test Extraction
- **Target Nodes**: `ClassDef` nodes with names starting with `Test`
- **Extracted Data**:
  - Class name
  - Docstring
  - All test methods (same extraction as FR-1.3)
  - Setup/teardown methods (`setup_method`, `teardown_method`)
- **Pydantic Model**:
```python
class TestClass(BaseModel):
    """Parsed test class metadata."""
    name: str
    line_number: int
    docstring: str | None
    test_methods: list[TestFunction]
    setup_methods: list[str]
    teardown_methods: list[str]
```

---

### FR-2: NECESSARY Pattern Validation Rules

#### FR-2.1: Descriptive Test Naming (N - No Missing Behaviors)
- **Rule**: Test names MUST describe what/when/then clearly
- **Good Pattern**: `test_<function>_when_<condition>_then_<outcome>`
- **Alternative Pattern**: `test_<function>_<scenario>_<expected_result>`
- **Violation Detection**:
  - Generic names: `test_1`, `test_function`, `test_basic`
  - Ambiguous names: `test_edge_case`, `test_error`, `test_success`
  - Non-descriptive: `test_foo`, `test_bar`, `test_temp`
- **Regex Patterns**:
```python
VIOLATION_PATTERNS = [
    r"^test_[0-9]+$",  # Numeric tests
    r"^test_(basic|simple|test)$",  # Too generic
    r"^test_(foo|bar|baz|temp)(_|$)",  # Placeholder names
]

RECOMMENDED_PATTERN = r"^test_[a-z_]+_when_[a-z_]+_then_[a-z_]+$"
ALTERNATIVE_PATTERN = r"^test_[a-z_]+_[a-z_]+_[a-z_]+$"  # Min 3 segments
```
- **Auto-Fix Strategy**:
  - Extract function name from test body (first function call)
  - Analyze assertion type (equality, exception, boolean)
  - Generate descriptive name using VectorStore patterns
  - Confidence: 0.7 (requires semantic context)
- **Example Fix**:
```python
# BEFORE (violation)
def test_1():
    """Test validation."""
    result = validate_email("test@example.com")
    assert result.is_ok()

# AFTER (auto-fix applied)
def test_validate_email_when_valid_format_then_returns_ok():
    """Test email validation with valid format."""
    result = validate_email("test@example.com")
    assert result.is_ok()
```

#### FR-2.2: AAA Pattern Structure (C - Comprehensive Coverage)
- **Rule**: Tests MUST use Arrange-Act-Assert structure with comments
- **Detection Method**: Parse comment nodes within function body
- **Required Comments**:
  - `# Arrange` (or `# Setup`, `# Given`)
  - `# Act` (or `# Execute`, `# When`)
  - `# Assert` (or `# Verify`, `# Then`)
- **AST Analysis**:
```python
def detect_aaa_structure(test_func: ast.FunctionDef) -> AAAStructure:
    """
    Analyze test body for AAA pattern.

    Returns:
        AAAStructure with flags for arrange/act/assert presence
    """
    comments = [
        node.value for node in ast.walk(test_func)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str) and node.value.value.startswith("#")
    ]

    has_arrange = any("arrange" in c.lower() or "setup" in c.lower() for c in comments)
    has_act = any("act" in c.lower() or "execute" in c.lower() for c in comments)
    has_assert = any("assert" in c.lower() or "verify" in c.lower() for c in comments)

    return AAAStructure(
        has_arrange=has_arrange,
        has_act=has_act,
        has_assert=has_assert,
        is_compliant=has_arrange and has_act and has_assert
    )
```
- **Auto-Fix Strategy**:
  - Analyze statement types to infer section boundaries
  - Insert AAA comments before corresponding statement groups
  - Confidence: 0.9 (high confidence, structural fix)
- **Example Fix**:
```python
# BEFORE (missing AAA comments)
def test_user_creation():
    """Test user creation."""
    user_data = {"email": "test@example.com", "name": "Test"}
    result = create_user(user_data)
    assert result.is_ok()
    assert result.value.email == "test@example.com"

# AFTER (auto-fix applied)
def test_user_creation():
    """Test user creation."""
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test"}

    # Act
    result = create_user(user_data)

    # Assert
    assert result.is_ok()
    assert result.value.email == "test@example.com"
```

#### FR-2.3: Docstring Presence (Y - Yielding Confidence)
- **Rule**: All test functions MUST have descriptive docstrings
- **Detection**: Check for docstring as first statement (ast.Expr with ast.Constant string)
- **Quality Criteria**:
  - Minimum length: 20 characters
  - Describes test purpose (what is being tested)
  - No generic text: "Test function", "TODO", "TBD"
- **Violation Examples**:
```python
# Missing docstring
def test_validation():
    pass

# Too generic
def test_validation():
    """Test."""
    pass

# Placeholder
def test_validation():
    """TODO: Add description"""
    pass
```
- **Auto-Fix Strategy**:
  - Generate docstring from test name (convert snake_case to sentence)
  - Add behavior description from AAA sections
  - Confidence: 0.65 (moderate, semantic generation)
- **Example Fix**:
```python
# BEFORE (missing docstring)
def test_validate_email_when_invalid_format_then_returns_error():
    # Arrange
    invalid_email = "not-an-email"

    # Act
    result = validate_email(invalid_email)

    # Assert
    assert result.is_err()

# AFTER (auto-fix applied)
def test_validate_email_when_invalid_format_then_returns_error():
    """Test email validation when invalid format then returns error result."""
    # Arrange
    invalid_email = "not-an-email"

    # Act
    result = validate_email(invalid_email)

    # Assert
    assert result.is_err()
```

#### FR-2.4: Edge Case Coverage Detection (E - Edge Cases Covered)
- **Rule**: Tests should cover boundary conditions, empty/null inputs, extreme values
- **Detection Heuristics**:
  - Test name contains: `edge`, `boundary`, `empty`, `null`, `none`, `zero`, `max`, `min`
  - Assertions with: `None`, `[]`, `{}`, `""`, `0`, `-1`
  - Exception testing: `pytest.raises`, `with pytest.raises`
  - Parametrized tests: `@pytest.mark.parametrize` with multiple values
- **AST Analysis**:
```python
def detect_edge_case_coverage(test_func: ast.FunctionDef) -> EdgeCaseCoverage:
    """
    Analyze test for edge case patterns.

    Returns:
        EdgeCaseCoverage with detected edge case types
    """
    edge_case_indicators = {
        "boundary": False,
        "empty_null": False,
        "exception": False,
        "parametrized": False
    }

    # Check test name
    name_lower = test_func.name.lower()
    if any(kw in name_lower for kw in ["edge", "boundary", "extreme"]):
        edge_case_indicators["boundary"] = True
    if any(kw in name_lower for kw in ["empty", "null", "none", "zero"]):
        edge_case_indicators["empty_null"] = True

    # Check decorators
    for dec in test_func.decorator_list:
        if isinstance(dec, ast.Call) and hasattr(dec.func, 'attr'):
            if dec.func.attr == "parametrize":
                edge_case_indicators["parametrized"] = True

    # Check for pytest.raises
    for node in ast.walk(test_func):
        if isinstance(node, ast.Call):
            if hasattr(node.func, 'attr') and node.func.attr == "raises":
                edge_case_indicators["exception"] = True

    return EdgeCaseCoverage(**edge_case_indicators)
```
- **Violation Detection**: Module has <30% edge case tests (heuristic threshold)
- **Auto-Fix Strategy**:
  - Suggest additional test cases with edge values
  - Generate parametrize decorator with boundary values
  - Confidence: 0.55 (low, requires domain knowledge)

#### FR-2.5: Assertion Strength (A - Assertions Meaningful)
- **Rule**: Assertions MUST be specific (not just `assert x is not None`)
- **Weak Assertion Patterns**:
```python
WEAK_ASSERTIONS = [
    "assert result",  # Boolean check only
    "assert result is not None",  # Existence check only
    "assert x",  # Truthy check only
    "pass  # TODO: Add assertions",  # No assertions
]
```
- **Strong Assertion Patterns**:
```python
STRONG_ASSERTIONS = [
    "assert result == expected",  # Value comparison
    "assert result.is_ok()",  # State validation
    "assert result.value.field == 'value'",  # Property check
    "assert len(items) == 5",  # Quantity validation
]
```
- **Auto-Fix Strategy**:
  - Suggest specific assertions based on variable types
  - Recommend Result pattern checks (`is_ok()`, `is_err()`)
  - Confidence: 0.60 (moderate, requires type inference)

---

### FR-3: Auto-Fix Generation System

#### FR-3.1: Fix Strategy Selection
- **Input**: Violation type, test context (name, body, docstring)
- **Output**: Ordered list of fix strategies with confidence scores
- **Strategy Registry**:
```python
class FixStrategy(BaseModel):
    """Auto-fix strategy with confidence scoring."""
    violation_type: Literal["naming", "aaa_structure", "docstring", "edge_case", "assertion"]
    fix_function: str  # Function name to apply fix
    confidence: float  # 0.0 to 1.0
    requires_context: bool  # Needs VectorStore patterns
    description: str

FIX_STRATEGIES: dict[str, list[FixStrategy]] = {
    "naming": [
        FixStrategy(
            violation_type="naming",
            fix_function="generate_descriptive_name_from_body",
            confidence=0.70,
            requires_context=True,
            description="Generate name from test body analysis"
        ),
        FixStrategy(
            violation_type="naming",
            fix_function="apply_when_then_pattern",
            confidence=0.85,
            requires_context=False,
            description="Apply test_X_when_Y_then_Z pattern"
        )
    ],
    "aaa_structure": [
        FixStrategy(
            violation_type="aaa_structure",
            fix_function="insert_aaa_comments",
            confidence=0.92,
            requires_context=False,
            description="Insert Arrange/Act/Assert comments"
        )
    ],
    # ... more strategies
}
```

#### FR-3.2: VectorStore Pattern Matching
- **Query**: Search for similar violations and successful fixes
- **Pattern Format**:
```python
class FixPattern(BaseModel):
    """VectorStore-stored successful fix pattern."""
    violation_type: str
    original_code: str
    fixed_code: str
    confidence: float  # Historical success rate
    tags: list[str]  # ["naming", "test_quality", "pytest"]
    metadata: dict[str, Any]  # {"function_type": "validation", "domain": "email"}
```
- **Matching Logic**:
```python
def find_similar_fix_patterns(
    violation: Violation,
    context: AgentContext
) -> list[FixPattern]:
    """
    Query VectorStore for proven fix patterns (Article IV compliance).

    Args:
        violation: Detected violation with context
        context: AgentContext for VectorStore access

    Returns:
        List of FixPattern sorted by confidence (descending)
    """
    # Query VectorStore with tags
    patterns = context.search_memories(
        tags=["test_quality", violation.type, "fix_success"],
        query=f"fix for {violation.description}",
        include_session=False  # Cross-session learning
    )

    # Filter by confidence threshold
    return [
        FixPattern(**p) for p in patterns
        if p.get("confidence", 0) >= 0.6
    ]
```

#### FR-3.3: Fix Application Engine
- **Input**: Test file AST, violation, selected fix strategy
- **Output**: Modified AST with fix applied
- **Process**:
  1. Locate violation node in AST
  2. Apply transformation (add comment, rename function, insert docstring)
  3. Validate transformed AST (ensure syntactic correctness)
  4. Generate diff for review
- **Example - AAA Comment Insertion**:
```python
def insert_aaa_comments(test_func: ast.FunctionDef) -> ast.FunctionDef:
    """
    Insert AAA comments into test function body.

    Identifies statement groups:
    - Arrange: assignments, object creation
    - Act: function calls, operations
    - Assert: assert statements
    """
    new_body = []
    section_inserted = {"arrange": False, "act": False, "assert": False}

    for i, stmt in enumerate(test_func.body):
        # Insert Arrange comment before first assignment
        if not section_inserted["arrange"] and isinstance(stmt, ast.Assign):
            new_body.append(create_comment_node("# Arrange"))
            section_inserted["arrange"] = True

        # Insert Act comment before first expression/call
        if not section_inserted["act"] and isinstance(stmt, ast.Expr):
            if section_inserted["arrange"]:
                new_body.append(create_comment_node("# Act"))
                section_inserted["act"] = True

        # Insert Assert comment before first assert
        if not section_inserted["assert"] and isinstance(stmt, ast.Assert):
            if section_inserted["act"]:
                new_body.append(create_comment_node("# Assert"))
                section_inserted["assert"] = True

        new_body.append(stmt)

    test_func.body = new_body
    return test_func
```

#### FR-3.4: Confidence Scoring System
- **Factors**:
  - Strategy base confidence (0.5-0.95)
  - VectorStore pattern match confidence (0.6-1.0)
  - Context completeness (0.0-1.0 based on available metadata)
  - Historical success rate (0.0-1.0 from past applications)
- **Formula**:
```python
def calculate_fix_confidence(
    strategy: FixStrategy,
    pattern_match: FixPattern | None,
    context_completeness: float
) -> float:
    """
    Calculate final fix confidence score.

    Returns:
        Float between 0.0 and 1.0
    """
    base = strategy.confidence

    # Boost if VectorStore pattern matched
    if pattern_match:
        pattern_boost = pattern_match.confidence * 0.2
    else:
        pattern_boost = 0.0

    # Context penalty if incomplete
    context_factor = context_completeness * 0.1

    # Cap at 1.0
    return min(1.0, base + pattern_boost + context_factor)
```
- **Thresholds**:
  - ≥0.9: Auto-apply without review
  - ≥0.6: Recommend with confidence level
  - <0.6: Suggest manual review

---

### FR-4: Integration with TestGeneratorAgent

#### FR-4.1: Post-Generation Validation Hook
- **Trigger**: After `GenerateTests.run()` completes
- **Process**:
```python
class GenerateTests(Tool):
    def run(self):
        # ... existing generation logic ...

        # NEW: Validate generated tests
        validation_result = validate_necessary_compliance(test_file_path)

        if validation_result.has_violations():
            # Apply high-confidence auto-fixes
            auto_fixes_applied = apply_auto_fixes(
                test_file_path,
                validation_result.violations,
                confidence_threshold=0.6
            )

            # Re-validate after fixes
            final_validation = validate_necessary_compliance(test_file_path)

            return {
                "status": "success",
                "violations_detected": len(validation_result.violations),
                "auto_fixes_applied": len(auto_fixes_applied),
                "final_compliance": final_validation.is_compliant(),
                "remaining_violations": final_validation.violations
            }
```

#### FR-4.2: Validation Report Format
```python
class ValidationReport(BaseModel):
    """NECESSARY compliance validation results."""
    file_path: str
    is_compliant: bool
    violations: list[Violation]
    auto_fixes: list[AppliedFix]
    score: NECESSARYScore
    timestamp: str

class Violation(BaseModel):
    """Detected NECESSARY violation."""
    type: Literal["naming", "aaa_structure", "docstring", "edge_case", "assertion"]
    severity: Literal["critical", "high", "medium", "low"]
    line_number: int
    description: str
    suggested_fixes: list[SuggestedFix]

class SuggestedFix(BaseModel):
    """Auto-fix suggestion with confidence."""
    strategy: str
    confidence: float
    preview: str  # Code preview after fix
    requires_manual_review: bool

class AppliedFix(BaseModel):
    """Record of applied auto-fix."""
    violation_type: str
    line_number: int
    strategy: str
    confidence: float
    success: bool
```

---

## Non-Functional Requirements

### NFR-1: Performance
- **Parsing Speed**: <100ms per test file (1000 lines)
- **Batch Analysis**: <2s for 50 test files
- **Memory Usage**: <50MB for full repository analysis
- **Scalability**: Handle 1000+ test files without degradation

### NFR-2: Accuracy
- **False Positive Rate**: <5% (violations flagged incorrectly)
- **False Negative Rate**: <2% (missed violations)
- **Auto-Fix Success Rate**: ≥85% after 20 pattern learnings

### NFR-3: Constitutional Compliance

#### Article I: Complete Context Before Action
- MUST parse entire test file before validation
- MUST query VectorStore for patterns before auto-fix generation
- MUST retry on timeout (2x, 3x) for VectorStore queries
- MUST NOT proceed with partial AST (syntax errors fail immediately)

#### Article II: 100% Verification and Stability
- MUST validate all generated tests before merge
- MUST ensure auto-fixes don't break existing tests
- MUST re-run pytest after fixes applied
- MUST rollback if tests fail after auto-fix

#### Article IV: Continuous Learning
- MUST query VectorStore for similar violations BEFORE fix generation
- MUST store successful fix patterns AFTER manual approval
- MUST update confidence scores based on fix acceptance rates
- MUST enable cross-session pattern recognition

### NFR-4: Maintainability
- **Extensibility**: New validation rules added via plugin system
- **Configurability**: Rule severity/thresholds adjustable per project
- **Testability**: 100% unit test coverage for validator components
- **Documentation**: All validation rules documented with examples

---

## Acceptance Criteria

### AC-1: AST Parsing
- [ ] **AC-1.1**: Parser handles all valid Python 3.10+ syntax
- [ ] **AC-1.2**: Syntax errors return structured ParseError (file, line, message)
- [ ] **AC-1.3**: Extracted TestFunction/TestClass models match pytest conventions
- [ ] **AC-1.4**: Parsing completes in <100ms for 1000-line files

### AC-2: Validation Rules
- [ ] **AC-2.1**: Naming rule detects generic names with 100% accuracy (test_1, test_basic)
- [ ] **AC-2.2**: AAA structure rule identifies missing comments in 95% of cases
- [ ] **AC-2.3**: Docstring rule flags missing/generic docstrings with <5% false positives
- [ ] **AC-2.4**: Edge case rule detects absence of boundary tests in modules
- [ ] **AC-2.5**: Assertion strength rule identifies weak assertions (is not None)

### AC-3: Auto-Fix Generation
- [ ] **AC-3.1**: AAA comment insertion has ≥0.9 confidence (high accuracy)
- [ ] **AC-3.2**: Descriptive name generation has ≥0.7 confidence (context-dependent)
- [ ] **AC-3.3**: Docstring generation has ≥0.65 confidence (semantic)
- [ ] **AC-3.4**: VectorStore patterns boost confidence by +0.1 to +0.2
- [ ] **AC-3.5**: Generated fixes pass pytest validation (no syntax errors)

### AC-4: Integration
- [ ] **AC-4.1**: TestGeneratorAgent validates output before returning
- [ ] **AC-4.2**: QualityEnforcerAgent runs validator in pre-commit hook
- [ ] **AC-4.3**: Validation report includes all violations with suggested fixes
- [ ] **AC-4.4**: Auto-fixes with confidence ≥0.6 applied automatically
- [ ] **AC-4.5**: Remaining violations (confidence <0.6) require manual review

### AC-5: Learning & Improvement
- [ ] **AC-5.1**: VectorStore queries return patterns with confidence ≥0.6
- [ ] **AC-5.2**: Successful fixes stored in VectorStore with tags
- [ ] **AC-5.3**: Confidence scores updated after 10+ fix applications
- [ ] **AC-5.4**: Cross-session learning enabled (include_session=False)
- [ ] **AC-5.5**: Auto-fix success rate improves by ≥10% after 20 learnings

### AC-6: Constitutional Compliance
- [ ] **AC-6.1**: Article I: Complete context validation (full AST required)
- [ ] **AC-6.2**: Article II: Tests re-run after auto-fixes (100% pass required)
- [ ] **AC-6.3**: Article IV: VectorStore integration mandatory (query before fix)
- [ ] **AC-6.4**: No disable flags for learning system (constitutional mandate)

---

## Technical Architecture

### Component Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                   NECESSARY Compliance Validator                │
└─────────────────────────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐         ┌───────────────┐         ┌────────────────┐
│  AST Parser   │         │   Validator   │         │  Fix Generator │
│               │         │     Engine    │         │                │
│ - parse_file  │────────▶│ - validate()  │────────▶│ - generate()   │
│ - extract_    │         │ - check_rules │         │ - apply_fix()  │
│   tests()     │         │ - score()     │         │ - confidence() │
└───────────────┘         └───────────────┘         └────────────────┘
        │                          │                          │
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐         ┌───────────────┐         ┌────────────────┐
│  Pydantic     │         │   Violation   │         │  AgentContext  │
│    Models     │         │    Detector   │         │  (VectorStore) │
│               │         │               │         │                │
│ - TestFile    │         │ - naming      │         │ - search_      │
│ - TestFunc    │         │ - aaa         │         │   memories()   │
│ - Violation   │         │ - docstring   │         │ - store_       │
└───────────────┘         └───────────────┘         │   memory()     │
                                                     └────────────────┘
```

### Data Flow
```
[Test File] → [AST Parser] → [TestFileAST]
                                    │
                                    ▼
                           [Validation Rules]
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              [Naming Check]  [AAA Check]  [Docstring Check]
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
                           [Violation List]
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            [VectorStore Query]              [Fix Strategy]
            (Pattern Matching)               (Selection)
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                           [Confidence Scoring]
                                    │
                                    ▼
                           [Auto-Fix Application]
                                    │
                                    ▼
                           [Modified Test File]
                                    │
                                    ▼
                           [Pytest Validation]
```

---

## Implementation Phases

### Phase 1: Core AST Parser (Week 1)
**Deliverables**:
- [ ] `tools/test_validation/ast_parser.py` with `parse_test_file()` function
- [ ] Pydantic models: `TestFileAST`, `TestFunction`, `TestClass`, `ParseError`
- [ ] Unit tests: 30+ tests covering all pytest patterns
- [ ] Performance benchmark: <100ms per 1000-line file

**Tasks**:
1. Create Pydantic models for AST representation
2. Implement file discovery (`glob_test_files()`)
3. Build AST extractor for test functions/classes
4. Add docstring/comment extraction logic
5. Write comprehensive unit tests with edge cases
6. Performance profiling and optimization

### Phase 2: Validation Rules Engine (Week 2)
**Deliverables**:
- [ ] `tools/test_validation/validator.py` with rule implementations
- [ ] Validation rules: naming, AAA structure, docstrings, assertions
- [ ] `ValidationReport` and `Violation` Pydantic models
- [ ] Rule configuration system (severity thresholds)
- [ ] 50+ unit tests for each validation rule

**Tasks**:
1. Implement naming validation with regex patterns
2. Build AAA structure detector (comment analysis)
3. Create docstring quality checker
4. Add edge case coverage heuristics
5. Implement assertion strength analyzer
6. Develop configurable rule system

### Phase 3: Auto-Fix Generation System (Week 3)
**Deliverables**:
- [ ] `tools/test_validation/fix_generator.py` with strategy registry
- [ ] Fix strategies: AAA insertion, name generation, docstring creation
- [ ] VectorStore integration for pattern matching
- [ ] Confidence scoring system
- [ ] 40+ tests for fix generation accuracy

**Tasks**:
1. Design FixStrategy and FixPattern models
2. Implement AAA comment insertion (high confidence)
3. Build descriptive name generator (moderate confidence)
4. Create docstring generator from test body
5. Integrate VectorStore pattern queries (Article IV)
6. Develop confidence calculation logic

### Phase 4: Integration & Learning (Week 4)
**Deliverables**:
- [ ] TestGeneratorAgent integration hook
- [ ] QualityEnforcerAgent pre-commit validation
- [ ] VectorStore pattern storage workflow
- [ ] Learning dashboard for fix success rates
- [ ] End-to-end integration tests

**Tasks**:
1. Add validation hook to `GenerateTests.run()`
2. Create pre-commit hook for NECESSARY validation
3. Implement learning pattern extraction
4. Build confidence score update mechanism
5. Write integration tests (TestGenerator → Validator → CodeAgent)
6. Create monitoring dashboard for fix acceptance rates

---

## Dependencies

### Internal Dependencies
- **shared/agent_context.py**: VectorStore access for pattern matching (Article IV)
- **test_generator_agent/test_generator_agent.py**: Integration point for validation
- **quality_enforcer_agent/quality_enforcer_agent.py**: Pre-commit hook integration
- **tools/bash.py**: Pytest execution for post-fix validation

### External Dependencies
- **ast (stdlib)**: Python Abstract Syntax Tree parsing
- **pytest**: Test framework for validation
- **pydantic**: Type-safe models for validation results
- **typing**: Type hints for strict typing (Article II)

### ADR References
- **ADR-001**: Complete Context Before Action (full AST parsing)
- **ADR-002**: 100% Verification (tests re-run after fixes)
- **ADR-004**: Continuous Learning (VectorStore mandatory)
- **ADR-008**: Strict Typing (all models use Pydantic)
- **ADR-010**: Result Pattern (error handling in parser)
- **ADR-011**: NECESSARY Pattern (validation target)

---

## Risks & Mitigations

### Risk 1: AST Parsing Complexity
- **Impact**: High (core functionality)
- **Probability**: Medium (Python AST is well-documented)
- **Mitigation**:
  - Use stdlib `ast` module (battle-tested)
  - Comprehensive test suite with edge cases
  - Fallback to syntax error reporting for unparseable files

### Risk 2: Auto-Fix Accuracy
- **Impact**: High (incorrect fixes break tests)
- **Probability**: Medium (semantic understanding required)
- **Mitigation**:
  - Confidence thresholds (only apply ≥0.6)
  - Mandatory pytest validation after fixes
  - Rollback mechanism if tests fail
  - VectorStore learning improves accuracy over time

### Risk 3: Performance on Large Codebases
- **Impact**: Medium (user experience)
- **Probability**: Low (AST parsing is fast)
- **Mitigation**:
  - Performance benchmarks in CI
  - Parallel file processing for batch analysis
  - Caching of parsed ASTs
  - Incremental validation (changed files only)

### Risk 4: Learning System Cold Start
- **Impact**: Medium (low confidence initially)
- **Probability**: High (no patterns in VectorStore yet)
- **Mitigation**:
  - Seed VectorStore with proven patterns from existing tests
  - Use reasonable base confidence scores (0.65-0.9)
  - Manual review for low confidence (<0.6) initially
  - Rapid learning after 10-20 fix applications

---

## Success Metrics & KPIs

### Validation Accuracy
- **Target**: ≥95% violation detection accuracy
- **Measurement**: Manual review of 100 test files (known violations)
- **Threshold**: ≤5% false positives, ≤2% false negatives

### Auto-Fix Success Rate
- **Target**: ≥85% fixes applied without manual changes
- **Measurement**: Track fix acceptance rate in VectorStore
- **Threshold**: After 20 learnings, success rate ≥85%

### Integration Performance
- **Target**: <2s validation overhead per commit
- **Measurement**: Pre-commit hook execution time
- **Threshold**: P95 latency <2s for typical commits (5-10 test files)

### Learning Effectiveness
- **Target**: +10% confidence improvement after 20 patterns
- **Measurement**: Compare initial vs learned confidence scores
- **Threshold**: Confidence boost ≥0.1 for naming/docstring fixes

### Constitutional Compliance
- **Target**: 100% Article IV compliance
- **Measurement**: Audit VectorStore integration (query before fix, store after success)
- **Threshold**: Zero violations in constitutional audit

---

## Future Enhancements

### Phase 5: Semantic Analysis (Future)
- LLM-powered test logic quality assessment
- Detect redundant tests (duplicate behavior coverage)
- Suggest missing test scenarios from code analysis

### Phase 6: Multi-Language Support (Future)
- TypeScript/Jest validation rules
- JavaScript/Mocha patterns
- Go testing package support

### Phase 7: IDE Integration (Future)
- VS Code extension with inline suggestions
- Real-time validation as tests are written
- Quick-fix actions in editor

### Phase 8: Mutation Testing Integration (Future)
- Verify tests catch real bugs (mutation score)
- Identify weak tests with high mutation survival
- Generate additional tests for uncaught mutations

---

## Glossary

- **AAA Pattern**: Arrange-Act-Assert testing structure
- **AST**: Abstract Syntax Tree (code structure representation)
- **NECESSARY**: 9-property test quality framework (Named, Executable, Comprehensive, Error-validated, State-verified, Side-effects controlled, Assertions meaningful, Repeatable, Yield fast)
- **Q(T) Score**: Quantitative test quality metric (0.0-1.0)
- **Confidence Score**: Probability of auto-fix correctness (0.0-1.0)
- **VectorStore**: Institutional memory system for pattern learning
- **Article IV**: Constitutional mandate for continuous learning integration

---

## References

### ADRs
- **ADR-001**: Complete Context Before Action
- **ADR-002**: 100% Verification and Stability
- **ADR-004**: Continuous Learning (VectorStore mandatory)
- **ADR-007**: Spec-Driven Development
- **ADR-008**: Strict Typing Requirements
- **ADR-010**: Result Pattern for Error Handling
- **ADR-011**: NECESSARY Pattern Compliance (target framework)

### Related Specifications
- **spec-001**: Spec-Driven Development Integration
- **spec-007**: Toolsmith Agent (tool creation methodology)

### External References
- Python AST Documentation: https://docs.python.org/3/library/ast.html
- Pytest Best Practices: https://docs.pytest.org/en/stable/goodpractices.html
- NECESSARY Pattern Origin: Agency internal testing framework

---

**Approval Status**: Awaiting PlannerAgent approval
**Next Steps**: Create `plan-008-necessary-compliance-validator.md` with implementation plan
