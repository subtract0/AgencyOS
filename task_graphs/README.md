# Task Graphs Directory

**Purpose**: Declarative task graphs for /primeA autonomous orchestration.

---

## Available Task Graphs

### 1. Foundation Validation Mission

**File**: `foundation_validation_mission.json`
**Status**: Ready for Execution
**Cost**: $14.50 (145K tokens)
**Duration**: 8-12 days
**Reference**: `docs/FOUNDATION_VALIDATION_MISSION.md`

**Mission**: Validate 10 architectural claims from `docs/vision/EPIC_OF_EPICS.md` before proceeding to Leap 9 (Autopoietic Evolution).

**Strategic Sequencing** (Exponential Compounding):
```
Phase 1: Learning Infrastructure (Force Multiplier)
    ↓ VectorStore patterns stored
Phase 2: Quality Enforcement (Risk Reducer)
    ↓ Uses Phase 1 patterns (20-25% faster)
Phase 3: Meta-Cognitive Capability (Intelligence Amplifier)
    ↓ Uses Phase 1-2 patterns (30-35% better quality)
Phase 4: Optimization & Autonomy (Efficiency & Proof)
    ✓ Uses all patterns (40-50% better, full autonomy)
```

**Claims Validated**:
1. VectorStore pattern extraction (confidence ≥0.6)
2. 96% cost reduction (documented proof)
3. Constitutional governance (automated enforcement)
4. Test-driven autonomy (100% test-before-code)
5. Meta-cognitive reasoning (/primeA orchestrator)
6. Autonomous completion validation (zero false positives)
7. Mission validation before execution (confidence 0.95)
8. Zero-human-intervention development cycles

**Execution**:
```bash
# Validate task graph
python validate_foundation_mission.py

# Execute full mission
/primeA --task-graph=task_graphs/foundation_validation_mission.json

# Execute single phase
/primeA --task-graph=task_graphs/foundation_validation_mission.json --phase=phase_1_learning_infrastructure
```

**Visualization**:
- ASCII tree: `python validate_foundation_mission.py`
- Mermaid diagram: `foundation_validation_mission.mmd`

---

## Task Graph Schema

**Pydantic Model**: `shared/models/task_graph.py`

**Required Fields**:
```python
{
  "mission": str,  # Mission title
  "phases": [      # Sequential phases
    {
      "id": str,   # phase_1, phase_2, etc.
      "title": str,
      "tasks": [   # Tasks in this phase
        {
          "id": str,                    # Unique task ID
          "title": str,                 # Human-readable title
          "type": "Spec"|"Code"|"Test", # Task category
          "tier": "Tier 1"|"Tier 2",    # Complexity tier
          "agent": str,                 # Agent to execute
          "description": str,           # Actionable instruction
          "dependencies": [str],        # Task IDs that must complete first
          "acceptance_criteria": [str], # Verification criteria
          "estimated_tokens": int,      # Token estimate
          "verification_target": str    # For Test tasks: Code task ID
        }
      ]
    }
  ],
  "checkpoints": [  # Human review or auto-validation
    {
      "after_phase": str,                         # Phase ID
      "type": "human_review"|"auto_validate",     # Checkpoint type
      "prompt": str                               # User prompt (if human_review)
    }
  ]
}
```

**Constitutional Compliance**:
- Article II: Every Code task MUST have Test dependency (TDD enforced)
- Article IV: VectorStore integration (query before, store after)
- Article V: Task graph is the specification

**Validation**:
- No circular dependencies (DAG validation)
- All dependencies reference valid task IDs
- Test tasks have `verification_target` (Article II)
- Spec tasks have `acceptance_criteria` (Article V)

---

## Creating New Task Graphs

### 1. Define Mission and Phases

```json
{
  "mission": "Your Mission Title",
  "phases": [
    {
      "id": "phase_1_foundation",
      "title": "Phase 1: Foundation",
      "tasks": []
    }
  ]
}
```

### 2. Add Tasks with TDD Dependencies

**Pattern** (Spec → Test → Code):
```json
{
  "tasks": [
    {
      "id": "spec_feature_x",
      "title": "Feature X Specification",
      "type": "Spec",
      "tier": "Tier 1",
      "agent": "planner",
      "description": "Create specification for feature X",
      "dependencies": [],
      "acceptance_criteria": ["Criterion 1", "Criterion 2"]
    },
    {
      "id": "test_feature_x",
      "title": "Feature X Tests (RED Phase)",
      "type": "Test",
      "tier": "Tier 2",
      "agent": "test_generator",
      "description": "Write tests FIRST (must fail initially)",
      "dependencies": ["spec_feature_x"],
      "verification_target": "code_feature_x"
    },
    {
      "id": "code_feature_x",
      "title": "Feature X Implementation (GREEN Phase)",
      "type": "Code",
      "tier": "Tier 2",
      "agent": "coder",
      "description": "Implement to make tests pass (100% success)",
      "dependencies": ["test_feature_x"]
    }
  ]
}
```

### 3. Add Checkpoints

```json
{
  "checkpoints": [
    {
      "after_phase": "phase_1_foundation",
      "type": "human_review",
      "prompt": "Review Phase 1 results. Proceed to Phase 2?"
    }
  ]
}
```

### 4. Validate Task Graph

```python
from shared.models.task_graph import TaskGraph
import json

with open("your_task_graph.json") as f:
    graph_data = json.load(f)

# Validate with Pydantic
task_graph = TaskGraph(**graph_data)

# Print summary
print(task_graph.to_ascii_tree())

# Estimate cost
print(f"Estimated cost: ${task_graph.estimate_cost():.2f}")

# Topological sort (execution layers)
layers = task_graph.topological_sort()
print(f"Execution plan: {len(layers)} parallel layers")
```

---

## Best Practices

### 1. Exponential Compounding Sequencing

**DO** (Force Multipliers First):
```
Phase 1: Learning/Foundation (stores patterns)
    ↓
Phase 2: Quality/Risk Reduction (uses Phase 1 patterns)
    ↓
Phase 3: Meta-Capability (uses Phase 1-2 patterns)
    ↓
Phase 4: Demonstration (uses all patterns)
```

**DON'T** (Arbitrary Order):
```
Phase 1: Implementation
Phase 2: Testing
Phase 3: Documentation
Phase 4: Learning (too late!)
```

### 2. Constitutional TDD Workflow

**DO** (Article VI Compliance):
```json
// Step 1: Spec
{"id": "spec_x", "type": "Spec", "dependencies": []}

// Step 2: Test (depends on Spec)
{"id": "test_x", "type": "Test", "dependencies": ["spec_x"], "verification_target": "code_x"}

// Step 3: Code (depends on Test)
{"id": "code_x", "type": "Code", "dependencies": ["test_x"]}
```

**DON'T** (Article VI Violation):
```json
// ❌ Code before Test
{"id": "code_x", "type": "Code", "dependencies": ["spec_x"]}  // No Test dependency!

// ❌ Test after Code
{"id": "test_x", "type": "Test", "dependencies": ["code_x"]}  // Tests AFTER implementation!
```

### 3. VectorStore Learning Integration

**DO** (Article IV Compliance):
```json
{
  "description": "Query VectorStore for Phase 1-2 learnings on validation patterns. Implement using learned patterns.",
  "metadata": {
    "vectorstore_query": ["validation", "patterns", "phase_1", "phase_2"],
    "compounding": "Uses Phase 1-2 patterns (30% better quality)"
  }
}
```

**DON'T** (Isolated Execution):
```json
{
  "description": "Implement feature X",
  "metadata": {}  // No learning integration!
}
```

### 4. Clear Acceptance Criteria

**DO** (Verifiable):
```json
{
  "acceptance_criteria": [
    "All tests pass (100% success rate - Article II)",
    "Confidence scoring validated (≥0.95 threshold)",
    "Result<T,E> pattern used (no try/catch control flow)",
    "Functions <50 lines (ADR-009 complexity limit)"
  ]
}
```

**DON'T** (Vague):
```json
{
  "acceptance_criteria": [
    "Feature works",
    "Tests pass",
    "Good quality"
  ]
}
```

### 5. Realistic Token Estimates

**Tier 1 (Strategic/Architecture)**:
- Spec tasks: 3,000-4,000 tokens
- Complex reasoning: 5,000-6,000 tokens

**Tier 2 (Implementation)**:
- Test tasks: 2,500-3,500 tokens
- Code tasks: 4,000-6,000 tokens

**Tier 3 (Simple)**:
- Formatting/typos: 500-1,000 tokens
- Simple refactors: 1,000-2,000 tokens

---

## Validation Tools

### 1. Pydantic Validation

```python
from shared.models.task_graph import TaskGraph

task_graph = TaskGraph(**graph_data)  # Raises ValidationError if invalid
```

**Checks**:
- DAG validation (no circular dependencies)
- TDD compliance (Code tasks have Test dependencies)
- Dependency resolution (all dependencies exist)
- Checkpoint validation (phases exist)

### 2. Cost Estimation

```python
estimated_cost = task_graph.estimate_cost()
# Tier 1: gpt-5 @ $4/1M tokens
# Tier 2: 60% local (free), 40% gpt-4o @ $1.5/1M tokens
```

### 3. Execution Planning

```python
layers = task_graph.topological_sort()
# Returns parallelizable layers (tasks per layer)
# Layer 1: Tasks with no dependencies (run in parallel)
# Layer 2: Tasks depending on Layer 1 (run after Layer 1 completes)
# ...
```

### 4. Visualization

```python
# ASCII tree
print(task_graph.to_ascii_tree())

# Mermaid diagram
mermaid = task_graph.to_mermaid()
with open("diagram.mmd", "w") as f:
    f.write(mermaid)
```

---

## Common Patterns

### Pattern 1: Simple Feature (3 tasks)

```json
{
  "tasks": [
    {"id": "spec_feature", "type": "Spec", "dependencies": []},
    {"id": "test_feature", "type": "Test", "dependencies": ["spec_feature"], "verification_target": "code_feature"},
    {"id": "code_feature", "type": "Code", "dependencies": ["test_feature"]}
  ]
}
```

### Pattern 2: Multi-Phase Mission (4 phases, 12 tasks)

```json
{
  "phases": [
    {
      "id": "phase_1_foundation",
      "tasks": [
        {"id": "spec_foundation", "type": "Spec"},
        {"id": "test_foundation", "type": "Test"},
        {"id": "code_foundation", "type": "Code"}
      ]
    },
    {
      "id": "phase_2_implementation",
      "tasks": [
        {"id": "spec_impl", "type": "Spec", "dependencies": ["code_foundation"]},
        {"id": "test_impl", "type": "Test"},
        {"id": "code_impl", "type": "Code"}
      ]
    }
  ]
}
```

### Pattern 3: Parallel Execution (2 independent features)

```json
{
  "tasks": [
    // Feature A
    {"id": "spec_a", "type": "Spec", "dependencies": []},
    {"id": "test_a", "type": "Test", "dependencies": ["spec_a"]},
    {"id": "code_a", "type": "Code", "dependencies": ["test_a"]},

    // Feature B (parallel to A)
    {"id": "spec_b", "type": "Spec", "dependencies": []},
    {"id": "test_b", "type": "Test", "dependencies": ["spec_b"]},
    {"id": "code_b", "type": "Code", "dependencies": ["test_b"]}
  ]
}
```

**Execution**: Layer 1 (spec_a, spec_b), Layer 2 (test_a, test_b), Layer 3 (code_a, code_b)

---

## Troubleshooting

### Error: "Circular dependency detected"

**Cause**: Task A depends on Task B, and Task B depends on Task A.

**Solution**: Remove circular dependency. Use intermediate task if needed.

```json
// ❌ WRONG
{"id": "a", "dependencies": ["b"]},
{"id": "b", "dependencies": ["a"]}

// ✅ CORRECT
{"id": "a", "dependencies": []},
{"id": "b", "dependencies": ["a"]},
{"id": "c", "dependencies": ["a", "b"]}
```

### Error: "Code task missing Test dependency"

**Cause**: Code task doesn't have corresponding Test task (Article VI violation).

**Solution**: Add Test task with `verification_target` set to Code task ID.

```json
// ❌ WRONG
{"id": "code_x", "type": "Code", "dependencies": ["spec_x"]}  // No Test!

// ✅ CORRECT
{"id": "test_x", "type": "Test", "dependencies": ["spec_x"], "verification_target": "code_x"},
{"id": "code_x", "type": "Code", "dependencies": ["test_x"]}
```

### Error: "Task depends on non-existent task"

**Cause**: Dependency ID doesn't match any task ID.

**Solution**: Fix typo or add missing task.

```json
// ❌ WRONG
{"id": "test_x", "dependencies": ["spec_feature_x"]}  // Typo!

// ✅ CORRECT
{"id": "test_x", "dependencies": ["spec_x"]}  // Matches existing task ID
```

---

## References

- **Task Graph Model**: `shared/models/task_graph.py`
- **Constitution**: `constitution.md` (Articles I-VI)
- **ADR-007**: Spec-Driven Development
- **ADR-026**: Test-Driven Autonomy (Leap 7)
- **/primeA Documentation**: `.claude/commands/primeA.md`

---

**Last Updated**: 2025-10-25
**Maintainer**: Chief Architect + Master Orchestrator
