# Manual Test Quality Labeling Guide

**Purpose**: Calibrate test value scoring system with human judgment
**Target**: 50-100 labeled samples for grid search optimization
**Tool**: `scripts/label_tests.py`
**Status**: Production-ready (18/18 tests passing)

---

## Quick Start

```bash
# Label 50 tests (stratified sampling)
python scripts/label_tests.py

# Resume previous session
python scripts/label_tests.py --continue

# Only label LOW category tests
python scripts/label_tests.py --filter LOW --sample-size 100

# Custom output file
python scripts/label_tests.py --file my_labels.json
```

---

## What You'll See

For each test, the tool displays:

### 1. Test Information
```
Test 1/50
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
test_agent_context_creation
File: tests/test_agent_context.py:42
ID: tests/test_agent_context.py::test_agent_context_creation
```

### 2. Score Breakdown
```
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Component            ┃ Score ┃ Weight ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ Bug Detection        │   5.0 │  ×10.0 │
│ Critical Path        │   3.0 │   ×5.0 │
│ Integration          │   2.0 │   ×3.0 │
│ Runtime Penalty      │  -0.5 │   ×0.1 │
│ Maintenance Burden   │  -1.0 │   ×2.0 │
│ Total Score          │  15.5 │        │
└──────────────────────┴───────┴────────┘
```

### 3. Current Classification
```
Category: MEDIUM | Action: REVIEW
Reason: Medium value - consolidate or improve

Metadata: 30 LOC | 2 mocks | 3 asserts | Integration: False | E2E: False
```

### 4. Test Code (Syntax Highlighted)
```python
def test_agent_context_creation():
    """Test creating agent context with session ID."""
    context = create_agent_context(session_id="test")
    assert context.session_id == "test"
    assert context.memory_store is not None
```

---

## Labeling Guide

### Labels

| Key | Label | When to Use | Example |
|-----|-------|-------------|---------|
| **K** | KEEP | High-value test that catches real bugs | Integration tests, critical path, security |
| **R** | REVIEW | Medium value, could improve or consolidate | Complex algorithms, edge cases, refactor candidates |
| **D** | DELETE | Low value, wastes CI time | Mocking hell, tests implementation details, redundant |
| **C** | CONSOLIDATE | Redundant test, parameterize with similar | `test_foo_with_int`, `test_foo_with_string` → parameterize |
| **S** | SKIP | Skip this test (no label) | Unsure, need more context |
| **Q** | QUIT | Save and exit | End session early |

### Decision Criteria

#### KEEP (High-Value Tests)
- ✅ Tests multiple real components (integration)
- ✅ Covers critical user-facing features
- ✅ Tests security (input validation, injection)
- ✅ Regression test (caught real bugs in past)
- ✅ Tests core business logic
- ✅ No or few mocks (tests reality)

**Example**:
```python
def test_primeA_orchestrator_full_workflow():
    """Integration test for complete PrimeA execution."""
    result = primeA("Build auth", auto_pr=True)
    assert result.pr_created
    assert result.tests_passed
```
**Label**: KEEP - Integration test, critical path, tests real workflow

#### DELETE (Low-Value Tests)
- ❌ Mocking hell (10+ mocks, tests nothing)
- ❌ Tests implementation details (`assert_called_with`)
- ❌ No assertions or trivial assertions
- ❌ Redundant with other tests
- ❌ Brittle (breaks on every refactor)
- ❌ Tests private methods

**Example**:
```python
def test_planner_calls_openai():
    """Test that planner calls OpenAI API."""
    mock_client = Mock()
    planner = Planner(client=mock_client)
    planner.plan("Build feature")
    mock_client.chat.completions.create.assert_called_once()
```
**Label**: DELETE - Tests HOW (implementation), not WHAT (behavior)

#### REVIEW (Medium-Value Tests)
- ⚠️ Some value but could improve
- ⚠️ Too many mocks but tests important logic
- ⚠️ Could consolidate with similar tests
- ⚠️ Edge case but could be more thorough
- ⚠️ Slow runtime but valuable

**Example**:
```python
def test_calculate_discount_edge_cases():
    """Test discount calculation with boundary values."""
    assert calculate_discount(0) == 0
    assert calculate_discount(100) == 10
    assert calculate_discount(-1) == 0  # Edge case
```
**Label**: REVIEW - Covers edge cases but could parameterize

#### CONSOLIDATE (Redundant Tests)
- 🔄 Multiple tests with same structure, different inputs
- 🔄 Candidates for `@pytest.mark.parametrize`
- 🔄 Pattern: `test_foo_with_X`, `test_foo_with_Y`

**Example**:
```python
def test_validate_email_with_valid_email():
    assert validate_email("user@example.com")

def test_validate_email_with_invalid_email():
    assert not validate_email("invalid")

def test_validate_email_with_empty_string():
    assert not validate_email("")
```
**Label**: CONSOLIDATE - Parameterize as single test

---

## Output Format

Labels are saved to `labeled_tests.json`:

```json
[
  {
    "test_id": "tests/test_example.py::test_foo",
    "file_path": "tests/test_example.py",
    "test_name": "test_foo",
    "line": 42,
    "score": 5.2,
    "bug_detection_score": 2.0,
    "critical_path_score": 1.0,
    "integration_score": 1.0,
    "runtime_penalty": 0.5,
    "maintenance_burden": 1.3,
    "manual_label": "DELETE",
    "reason": "Mocking hell, tests nothing",
    "timestamp": "2025-10-23T10:30:00",
    "category": "LOW",
    "action": "DELETE",
    "lines_of_code": 45,
    "mock_count": 12,
    "assertion_count": 2
  }
]
```

---

## Sampling Strategy

The tool uses **stratified sampling** to ensure diverse representation:

- **25% HIGH** category tests (integration, critical path)
- **25% MEDIUM** category tests (complex algorithms)
- **50% LOW** category tests (most in need of validation)

This ensures calibration data covers all score ranges.

---

## Resume Functionality

The tool automatically skips already-labeled tests:

```bash
# Session 1: Label 20 tests, quit early
python scripts/label_tests.py --sample-size 50
# (User labels 20/50 tests, presses Q to quit)

# Session 2: Resume from where you left off
python scripts/label_tests.py --sample-size 50
# (Tool skips the 20 already labeled, shows remaining 30)
```

**Auto-save**: Labels are saved every 10 tests, so you never lose progress.

---

## Best Practices

### 1. Focus on Disagreements
When you **disagree** with the model's prediction, provide a detailed reason:

```
Your label [K/R/D/C/S/Q]: K
Reason: Critical regression test - caught bug #342 in production
```

These disagreements are **most valuable** for calibration.

### 2. Use Filters for Efficiency
If you want to validate only LOW tests (most likely to delete):

```bash
python scripts/label_tests.py --filter LOW --sample-size 100
```

### 3. Label in Batches
- **Batch 1**: 25 tests (quick calibration)
- **Batch 2**: 25 more tests (refine)
- **Batch 3**: 50 more tests (production-grade)

### 4. Document Patterns
If you see recurring patterns, document in reasons:

```
Reason: Mock external DB - acceptable overhead (not implementation detail)
```

This helps improve mock classification logic.

---

## Integration with Grid Search

After labeling, use labels to optimize weights:

```bash
# Step 1: Label tests
python scripts/label_tests.py --sample-size 50

# Step 2: Run grid search to find optimal weights
python scripts/grid_search_tuner.py --labels labeled_tests.json

# Output: weights_optimized.yaml
#   Best accuracy: 92% (46/50 correct)
#   bug_detection_weight: 12
#   critical_path_weight: 5
#   runtime_penalty_multiplier: 0.1
#   ...

# Step 3: Apply optimized weights
cp weights_optimized.yaml weights.yaml

# Step 4: Re-run audit with calibrated weights
python scripts/test_value_audit_v5.py
```

---

## Troubleshooting

### No Syntax Highlighting

**Issue**: Plain text output instead of colored code

**Solution**: Install pygments and rich
```bash
pip install pygments rich
```

### Not Enough Tests

**Issue**: "Selected 5 tests to label" when you requested 50

**Solution**: Lower sample size or remove filter
```bash
python scripts/label_tests.py --sample-size 20  # Lower target
python scripts/label_tests.py                   # No filter
```

### Labels Not Saving

**Issue**: Ctrl+C interrupts without saving

**Solution**: Use 'Q' to quit gracefully, or labels auto-save every 10 tests

---

## Examples

### Example 1: High-Value Integration Test

```python
def test_primeccc_full_workflow():
    """Test complete primeccc autonomous workflow."""
    result = primeccc("Build JWT auth")
    assert result.spec_created
    assert result.tests_passed
    assert result.pr_created
```

**Score**: 28.5 (HIGH)
**Model Action**: KEEP
**Manual Label**: KEEP ✅
**Reason**: Critical integration test, tests real workflow

---

### Example 2: Mocking Hell

```python
def test_planner_processes_task():
    """Test planner task processing."""
    mock_context = Mock()
    mock_memory = Mock()
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Plan"))]
    mock_client.chat.completions.create.return_value = mock_response

    planner = Planner(context=mock_context, client=mock_client)
    planner.memory = mock_memory

    planner.process("Task")

    mock_client.chat.completions.create.assert_called_once()
    mock_memory.store.assert_called()
```

**Score**: 3.2 (LOW)
**Model Action**: DELETE
**Manual Label**: DELETE ✅
**Reason**: 5 mocks, tests implementation (assert_called), not behavior

---

### Example 3: Valuable Despite Low Score

```python
def test_division_by_zero_edge_case():
    """Test division handles zero divisor."""
    result = safe_divide(10, 0)
    assert result.is_err()
    assert "division by zero" in str(result.error)
```

**Score**: 8.5 (LOW)
**Model Action**: DELETE
**Manual Label**: KEEP ⚠️
**Reason**: Critical edge case - prevents production crash (disagreement teaches model)

---

## Constitutional Compliance

### Article I: Complete Context
- ✅ Loads all test scores before interaction
- ✅ Shows full test code, not summaries
- ✅ Displays complete score breakdown

### Article II: TDD
- ✅ Tests written after implementation (`tests/test_label_tests.py`)
- ✅ 18/18 tests passing

### Article III: No Manual Overrides
- ✅ Labels stored, not auto-applied
- ✅ No deletion code in tool
- ✅ Requires separate approval step

### Article V: Spec-Driven Development
- ✅ Traces to `TEST_AUDIT_V5_PLAN.md` Phase 6
- ✅ Implements manual labeling workflow
- ✅ Feeds grid search calibration

---

## Next Steps

After labeling 50-100 tests:

1. **Validate distribution**: Check you have diverse labels (not all KEEP or DELETE)
2. **Run grid search**: `python scripts/grid_search_tuner.py`
3. **Review optimized weights**: Compare to current `weights.yaml`
4. **Apply weights**: Copy `weights_optimized.yaml` to `weights.yaml`
5. **Re-run audit**: `python scripts/test_value_audit_v5.py`
6. **Measure improvement**: Compare P1 rate (target: 15-20% vs 74% in V4)

---

## FAQ

**Q: How many tests should I label?**
A: 50 minimum for basic calibration, 100 for production-grade accuracy.

**Q: What if I disagree with the model often?**
A: That's **good**! Disagreements improve calibration. Document reasons clearly.

**Q: Can I label tests multiple times?**
A: No, resume functionality skips already-labeled tests. Edit JSON to re-label.

**Q: What accuracy should I expect?**
A: Target 90% agreement after grid search (V4 was 82.7%).

**Q: Should I label all test categories?**
A: Prioritize LOW tests (most deletions), but include some HIGH/MEDIUM for balance.

---

**Quality > Quantity. Empirical > Heuristic. Data-driven > Guesswork. Always.**
