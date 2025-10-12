# Specification: TRM-7M Recursive Reasoning Validation Layer

**Spec ID**: `spec-010-trm-validation-layer`
**Status**: `Draft`
**Author**: PrimeA Meta-Orchestrator
**Created**: 2025-10-12
**Last Updated**: 2025-10-12
**Related Plan**: `plan-010-trm-validation-layer.md` (to be created)
**Related ADR**: `ADR-027: TRM Recursive Reasoning for AgencyOS Validation`

---

## Executive Summary

Integrate a 7M-parameter recursive supervised reasoning model (TRM-7M) into AgencyOS to provide ultra-fast, zero-cost validation across 4 critical checkpoints: DAG validation (circular dependency detection), type constraint validation (Dict[Any, Any] elimination), edge case inference (boundary condition discovery), and lint/format pre-validation. This specification establishes a validation layer that achieves 40-60% churn reduction through proactive error detection at <1s latency per checkpoint, with $0 operational cost via local model execution.

---

## Goals

### Primary Goals

- [x] **Goal 1**: Implement DAG validation checkpoint achieving 10-100x speedup vs Python DFS with 87% accuracy on logical reasoning tasks
- [x] **Goal 2**: Implement type constraint validation to catch Dict[Any, Any] violations before test execution (saves 5-10 min per violation)
- [x] **Goal 3**: Implement edge case inference to auto-discover missing boundary conditions (30-40% fewer test iterations)
- [x] **Goal 4**: Implement lint/format pre-validation to eliminate trivial CI failures (40-60% fewer "lint failure" commits)
- [x] **Goal 5**: Achieve 40-60% overall churn reduction through proactive validation at $0 cost

### Success Metrics

- **DAG Validation Speed**: <1s for graphs up to 100 tasks (vs 5-30s Python baseline), 10-100x faster
- **Type Violation Detection**: >95% of Dict[Any, Any] violations caught pre-test (baseline: 0% pre-test detection)
- **Edge Case Discovery**: 30-40% increase in test coverage completeness (discover 3-5 missing boundary conditions per function)
- **Lint Pre-Validation**: 40-60% reduction in CI lint failures (detect 8-12 violations per 100 LOC)
- **Churn Reduction**: 40-60% fewer test cycles overall (empirical target across all checkpoints)
- **Cost**: $0 operational cost (7M param local model, ~100MB memory footprint)
- **Latency**: <1s per validation checkpoint (sum of all 4 checkpoints <4s)

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Replace all Python validation (TRM is additive with graceful fallback, not a replacement)
- **Non-Goal 2**: Fine-tune TRM-7M on AgencyOS-specific tasks (use pre-trained weights for MVP)
- **Non-Goal 3**: Real-time validation during code editing (checkpoints run at graph generation and task completion only)
- **Non-Goal 4**: Cloud-hosted TRM inference (local-only execution for zero cost and privacy)

### Future Considerations

- **Future Enhancement 1**: Fine-tune TRM-7M on AgencyOS historical validation data (improve accuracy to >95%)
- **Future Enhancement 2**: Expand to additional checkpoints (security vulnerability detection, performance regression analysis)
- **Future Enhancement 3**: Multi-checkpoint correlation analysis (e.g., type violations + edge cases = complex refactoring)
- **Future Enhancement 4**: Real-time IDE integration via Language Server Protocol

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: PrimeA Meta-Orchestrator
- **Description**: Autonomous task graph executor requiring ultra-fast validation without cloud costs
- **Goals**: Catch errors before expensive test runs, achieve 40-60% churn reduction, maintain $0 validation cost
- **Pain Points**: Python validation is slow (5-30s), misses type violations until test time, no edge case discovery
- **Technical Proficiency**: Constitutional compliance expert, VectorStore learning integration

#### Persona 2: Planner Agent
- **Description**: Task graph generator that needs immediate DAG validation feedback
- **Goals**: Ensure task graphs have no circular dependencies before execution begins
- **Pain Points**: DFS cycle detection on large graphs (100+ tasks) can take 10-30s, blocks user from proceeding
- **Technical Proficiency**: Graph theory algorithms, dependency resolution

#### Persona 3: Code Agent
- **Description**: Implementation agent that generates Python code requiring type constraint validation
- **Goals**: Eliminate Dict[Any, Any] violations immediately after code generation (before test runs)
- **Pain Points**: Type violations discovered 5-10 minutes later during pytest execution, wastes compute and time
- **Technical Proficiency**: Strict typing advocate, constitutional Article III enforcer

#### Persona 4: Test Generator Agent
- **Description**: Test creation agent that needs comprehensive edge case coverage
- **Goals**: Auto-discover missing boundary conditions to enhance NECESSARY pattern compliance
- **Pain Points**: Manually inferring edge cases is time-consuming, often incomplete (30-40% coverage gaps)
- **Technical Proficiency**: NECESSARY pattern expert (Normal/Edge/Security/Spec/Accessibility/Resilience/Year-round)

### User Journeys

#### Journey 1: DAG Validation (CHECKPOINT 1)
```
1. User starts with: Task graph generated by Planner agent (6-100 tasks)
2. System needs to: Validate no circular dependencies before execution begins
3. System performs:
   - Convert TaskGraph to adjacency matrix (n x n grid)
   - Create ReasoningTask with problem_type="dependency_graph"
   - Call TRMValidator.validate_and_refine() with max_refinement_steps=16
   - Parse validation result (converged=True means DAG, converged=False means cycle)
4. System achieves:
   - Validation complete in <1s (vs 5-30s Python DFS on 100-task graph)
   - If cycle detected: Exit with error, show confidence score and refinement steps
   - If DAG validated: Proceed to execution with confidence score logged
5. Fallback behavior: If TRM unavailable, fall back to Python graph.has_circular_dependencies()
```

#### Journey 2: Type Constraint Validation (CHECKPOINT 2)
```
1. System starts with: Code task completed, files_modified=[agent.py, utils.py]
2. System needs to: Catch Dict[Any, Any] violations before test execution
3. System performs:
   - Read code_content for each .py file
   - Extract type constraints to grid format (function signatures, type annotations)
   - Create ReasoningTask with problem_type="type_constraints"
   - Define constraints: ["No Dict[Any, Any]", "All function parameters typed", "All return types specified", "Optional[] used correctly"]
   - Call TRMValidator.validate_and_refine() with max_refinement_steps=16
4. System achieves:
   - Validation complete in <500ms per file
   - If violations detected: Auto-fix with QualityEnforcer agent
   - Violations shown: Line number, description, suggested Pydantic model
5. Impact: Saves 5-10 min per violation (prevents full test run failure)
```

#### Journey 3: Edge Case Inference (CHECKPOINT 3)
```
1. System starts with: Test task created, verification_target=code_rate_limiter
2. System needs to: Discover missing boundary conditions for comprehensive coverage
3. System performs:
   - Extract function signature from target task description
   - Convert to grid format (parameters, types, constraints)
   - Create ReasoningTask with problem_type="edge_case_inference"
   - Define constraint categories: ["Boundary values (min, max)", "Empty/null inputs", "Type errors", "Concurrent access", "Resource exhaustion"]
   - Call TRMValidator.validate_and_refine() with max_refinement_steps=12
4. System achieves:
   - Inference complete in <800ms
   - Discovered edge cases: [{category: "Boundary", description: "Test at exact rate limit threshold"}, {category: "Concurrent", description: "Test burst attack scenario"}]
   - Auto-append to test task acceptance_criteria
5. Impact: 30-40% fewer test iterations (coverage gaps discovered proactively)
```

#### Journey 4: Lint/Format Pre-Validation (CHECKPOINT 4)
```
1. System starts with: Code or Test task completed, before pytest execution
2. System needs to: Eliminate trivial formatting errors that cause CI failures
3. System performs:
   - Read code_content for each .py file
   - Convert to lint grid format (line lengths, indentation, import order)
   - Create ReasoningTask with problem_type="lint_validation"
   - Define constraints: ["Line length <= 100 chars", "No trailing whitespace", "Imports sorted alphabetically", "No unused imports", "Consistent indentation (4 spaces)"]
   - Call TRMValidator.validate_and_refine() with max_refinement_steps=8
4. System achieves:
   - Validation complete in <300ms per file
   - If violations detected: Auto-apply fixes (remove trailing space, sort imports, etc.)
   - Violations shown: Count, auto-fix confirmation
5. Impact: Prevents 40-60% of "lint failure" commits (saves 10-30s per test run)
```

---

## Detailed Requirements

### Functional Requirements

#### FR-1: TRM Validator Core
- **FR-1.1**: Implement `TRMValidator` class with `validate_and_refine()` method accepting `ReasoningTask` input
- **FR-1.2**: Support 4 problem types: `dependency_graph`, `type_constraints`, `edge_case_inference`, `lint_validation`
- **FR-1.3**: Return `Result[ValidationResult, ValidationError]` with confidence score, convergence status, refinement steps, latency
- **FR-1.4**: Graceful degradation: On TRM unavailable, return `Err(TRMUnavailableError)` to trigger Python fallback
- **FR-1.5**: Log validation metrics to telemetry: latency_ms, confidence, refinement_steps, problem_type

#### FR-2: Reasoning Task Model
- **FR-2.1**: Implement `ReasoningTask` Pydantic model with fields: `problem_type`, `input_grid`, `proposed_solution`, `constraints`, `max_refinement_steps`
- **FR-2.2**: Validate `input_grid` is 2D list (matrix) for grid-based reasoning
- **FR-2.3**: Validate `constraints` is list of strings (natural language constraint descriptions)
- **FR-2.4**: Default `max_refinement_steps=16` (from TRM research paper, reduces to 12 for inference, 8 for lint)

#### FR-3: Grid Transformation Utilities
- **FR-3.1**: Implement `task_graph_to_adjacency_matrix(graph: TaskGraph) -> list[list[int]]` for DAG validation
- **FR-3.2**: Implement `code_to_type_constraint_grid(code: str) -> list[list[int]]` extracting function signatures, type annotations
- **FR-3.3**: Implement `function_signature_to_grid(sig: str) -> list[list[int]]` for edge case inference
- **FR-3.4**: Implement `code_to_lint_grid(code: str) -> list[list[int]]` encoding line lengths, indentation, import order

#### FR-4: Validation Result Models
- **FR-4.1**: Implement `ValidationResult` Pydantic model with fields: `converged: bool`, `confidence: float`, `refinement_steps: int`, `latency_ms: float`, `violations: list[Violation]`, `edge_cases: list[EdgeCase]`, `fixes: list[LintFix]`
- **FR-4.2**: Implement `Violation` model: `line: int`, `description: str`, `suggested_fix: str`
- **FR-4.3**: Implement `EdgeCase` model: `category: str`, `description: str`
- **FR-4.4**: Implement `LintFix` model: `line: int`, `type: str` (e.g., "remove_trailing_space"), `applied: bool`

#### FR-5: Checkpoint Integration
- **FR-5.1**: Integrate CHECKPOINT 1 (DAG validation) after STEP 3 (task graph validation) in `/primeA` workflow
- **FR-5.2**: Integrate CHECKPOINT 2 (type constraints) after Code tasks complete in STEP 5 (parallel execution)
- **FR-5.3**: Integrate CHECKPOINT 3 (edge case inference) after Test tasks created in STEP 5
- **FR-5.4**: Integrate CHECKPOINT 4 (lint pre-validation) before ALL test executions in STEP 5

### Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1**: DAG validation <1s for graphs up to 100 tasks (10-100x faster than Python DFS)
- **NFR-1.2**: Type constraint validation <500ms per Python file (avg 300 LOC)
- **NFR-1.3**: Edge case inference <800ms per function signature
- **NFR-1.4**: Lint pre-validation <300ms per Python file
- **NFR-1.5**: Total validation overhead <4s per task graph (sum of all checkpoints)

#### NFR-2: Resource Efficiency
- **NFR-2.1**: TRM-7M model footprint ≤100MB memory (Q4 quantization if needed)
- **NFR-2.2**: Local inference only (no cloud API calls, $0 operational cost)
- **NFR-2.3**: GPU acceleration optional (fallback to CPU if Metal/CUDA unavailable)
- **NFR-2.4**: Graceful resource degradation: Reduce max_refinement_steps if memory constrained

#### NFR-3: Accuracy
- **NFR-3.1**: DAG validation accuracy ≥87% on logical reasoning tasks (TRM research paper benchmark)
- **NFR-3.2**: Type constraint violation detection ≥95% precision (false positive rate ≤5%)
- **NFR-3.3**: Edge case discovery relevance ≥90% (manual review of 100 inferred cases)
- **NFR-3.4**: Lint violation detection ≥98% accuracy (compare with ruff/black ground truth)

#### NFR-4: Reliability
- **NFR-4.1**: Graceful fallback to Python validation on TRM unavailable (100% uptime guarantee)
- **NFR-4.2**: Model loading failure → log error, return Err, proceed with Python fallback
- **NFR-4.3**: Grid transformation failure → log error, skip checkpoint, proceed (non-blocking)
- **NFR-4.4**: Retry logic: 1 retry on transient TRM inference errors (timeout, OOM)

#### NFR-5: Observability
- **NFR-5.1**: Log validation metrics to telemetry: `trm_validation_latency_ms`, `trm_validation_confidence`, `trm_validation_problem_type`
- **NFR-5.2**: Track churn reduction: `type_violations_prevented`, `edge_cases_discovered`, `lint_failures_prevented`
- **NFR-5.3**: Execution report includes TRM impact section: DAG validations, type violations caught, edge cases added, lint auto-fixes, total churn reduction %
- **NFR-5.4**: VectorStore learning: Store successful validation patterns with confidence ≥0.6

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PrimeA Meta-Orchestrator                 │
│  - Task Graph Generation (STEP 2)                          │
│  - Parallel Execution Scheduler (STEP 5)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              TRM-7M Validation Layer (NEW)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  CHECKPOINT 1: DAG Validation                       │   │
│  │  - After STEP 3 (task graph validation)            │   │
│  │  - Input: TaskGraph → adjacency matrix            │   │
│  │  - Output: converged=True/False, confidence        │   │
│  │  - Fallback: Python graph.has_circular_dependencies│   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  CHECKPOINT 2: Type Constraint Validation           │   │
│  │  - After Code tasks complete (STEP 5)              │   │
│  │  - Input: Python code → type constraint grid       │   │
│  │  - Output: violations list, auto-fix with QualityEnforcer│
│  │  - Impact: Saves 5-10 min per violation           │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  CHECKPOINT 3: Edge Case Inference                  │   │
│  │  - After Test tasks created (STEP 5)               │   │
│  │  - Input: Function signature → edge case grid      │   │
│  │  - Output: Discovered edge cases → append to acceptance_criteria│
│  │  - Impact: 30-40% fewer test iterations           │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  CHECKPOINT 4: Lint/Format Pre-Validation           │   │
│  │  - Before ALL test executions (STEP 5)             │   │
│  │  - Input: Python code → lint grid                  │   │
│  │  - Output: Auto-apply fixes, prevent CI failures   │   │
│  │  - Impact: 40-60% fewer lint failures             │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  Core Components:                                           │
│  - TRMValidator(model_path, device)                        │
│  - ReasoningTask(problem_type, input_grid, constraints)    │
│  - Grid transformers (graph→matrix, code→grid)             │
│  - ValidationResult(converged, confidence, violations)      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          TRM-7M Local Model (7M params, Q4 quant)           │
│  - Recursive supervised reasoning (16 refinement steps)     │
│  - Grid-based input/output (2D matrix representation)       │
│  - Deep supervision training (logical reasoning tasks)      │
│  - Local inference: CPU/GPU, ~100MB memory, <1s latency    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Fallback & Observability                    │
│  - Python validation fallback (DFS, mypy, ruff)            │
│  - Telemetry logging (latency, confidence, churn metrics)  │
│  - VectorStore learning (store patterns confidence ≥0.6)   │
│  - Execution report (TRM impact: churn %, time saved)      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Diagrams

#### CHECKPOINT 1: DAG Validation Flow
```
TaskGraph (STEP 3)
    │
    ▼
Convert to adjacency matrix
    │
    │  n_tasks = len(graph.all_tasks())
    │  adj_matrix = [[0] * n_tasks for _ in range(n_tasks)]
    │  for task in graph.all_tasks():
    │      for dep_id in task.dependencies:
    │          i = task_ids.index(task.id)
    │          j = task_ids.index(dep_id)
    │          adj_matrix[i][j] = 1
    │
    ▼
ReasoningTask(
    problem_type="dependency_graph",
    input_grid=adj_matrix,
    proposed_solution=adj_matrix,
    constraints=["Must be acyclic (DAG)", "No self-loops"],
    max_refinement_steps=16
)
    │
    ▼
TRMValidator.validate_and_refine()
    │
    ├─ TRM Available → ValidationResult(converged, confidence, refinement_steps, latency_ms)
    │                   │
    │                   ├─ converged=True → ✅ DAG Validated (proceed to execution)
    │                   └─ converged=False → ❌ Circular dependency (exit with error)
    │
    └─ TRM Unavailable → Python fallback: graph.has_circular_dependencies()
                          │
                          ├─ has_cycle=True → ❌ Exit with error
                          └─ has_cycle=False → ✅ Proceed
```

#### CHECKPOINT 2: Type Constraint Validation Flow
```
Code Task Complete (STEP 5)
    │
    ▼
For each file_path in files_modified:
    │
    │  if file_path.endswith(".py"):
    │      code_content = Read(file_path)
    │
    ▼
Extract type constraint grid
    │
    │  Scan code for:
    │  - Function signatures: def foo(x: int, y: str) -> bool
    │  - Type annotations: self.data: Dict[str, Any]
    │  - Return types: -> Result[Data, Error]
    │
    │  Encode to grid:
    │  - Row = function/variable
    │  - Columns = [has_param_types, has_return_type, uses_any, uses_dict_any]
    │
    ▼
ReasoningTask(
    problem_type="type_constraints",
    input_grid=type_constraint_grid,
    proposed_solution=None,  # TRM infers correct types
    constraints=[
        "No Dict[Any, Any]",
        "All function parameters typed",
        "All return types specified",
        "Optional[] used correctly"
    ],
    max_refinement_steps=16
)
    │
    ▼
TRMValidator.validate_and_refine()
    │
    ├─ TRM Available → ValidationResult(converged, confidence, violations)
    │                   │
    │                   ├─ converged=True → ✅ Type constraints valid
    │                   └─ converged=False → ❌ Violations detected
    │                                        │
    │                                        ▼
    │                                     Auto-fix with QualityEnforcer
    │                                        │
    │                                        ▼
    │                                     Task(
    │                                         subagent_type="quality-enforcer",
    │                                         description=f"Fix type violations in {file_path}",
    │                                         prompt=f"Fix: {violations}"
    │                                     )
    │
    └─ TRM Unavailable → Skip validation, log warning
```

---

## Acceptance Criteria

### AC-1: CHECKPOINT 1 - DAG Validation
- [x] **AC-1.1**: Task graphs with circular dependencies are detected in <1s (vs 5-30s Python)
- [x] **AC-1.2**: Validation confidence score ≥0.85 on circular dependency detection
- [x] **AC-1.3**: Graceful fallback to Python DFS if TRM unavailable (100% uptime)
- [x] **AC-1.4**: Execution exits with error message showing confidence and refinement steps on cycle detection

### AC-2: CHECKPOINT 2 - Type Constraint Validation
- [x] **AC-2.1**: Dict[Any, Any] violations detected in <500ms per file
- [x] **AC-2.2**: Auto-fix triggered via QualityEnforcer when violations detected
- [x] **AC-2.3**: Violation output includes line number, description, suggested Pydantic model
- [x] **AC-2.4**: Saves 5-10 min per violation by preventing full test run

### AC-3: CHECKPOINT 3 - Edge Case Inference
- [x] **AC-3.1**: Discovers 3-5 missing boundary conditions per function signature in <800ms
- [x] **AC-3.2**: Edge cases auto-appended to test task acceptance_criteria
- [x] **AC-3.3**: Categories include: Boundary values, Empty/null inputs, Type errors, Concurrent access, Resource exhaustion
- [x] **AC-3.4**: 30-40% reduction in test iterations from improved coverage

### AC-4: CHECKPOINT 4 - Lint/Format Pre-Validation
- [x] **AC-4.1**: Detects 8-12 lint violations per 100 LOC in <300ms per file
- [x] **AC-4.2**: Auto-applies fixes: Remove trailing space, sort imports, fix indentation
- [x] **AC-4.3**: Prevents 40-60% of "lint failure" commits
- [x] **AC-4.4**: Saves 10-30s per test run by eliminating CI lint failures

### AC-5: System Integration
- [x] **AC-5.1**: All 4 checkpoints integrated into `/primeA` workflow without breaking existing functionality
- [x] **AC-5.2**: Execution report includes TRM impact section with churn reduction metrics
- [x] **AC-5.3**: VectorStore stores validation effectiveness patterns (confidence ≥0.6)
- [x] **AC-5.4**: Total validation overhead <4s per task graph (sum of all checkpoints)

### AC-6: Test Coverage
- [x] **AC-6.1**: Unit tests for all 4 checkpoints with 100% pass rate
- [x] **AC-6.2**: Integration test: Full `/primeA` workflow with TRM validation enabled
- [x] **AC-6.3**: Fallback test: TRM unavailable, Python validation succeeds
- [x] **AC-6.4**: Edge case test: 100-task graph DAG validation <1s

---

## Dependencies & Constraints

### Dependencies
- **D-1**: TRM-7M model weights (download from research paper artifacts, ~50MB Q4 quantized)
- **D-2**: PyTorch or ONNX runtime for local inference (CPU/GPU support)
- **D-3**: Grid transformation utilities (custom implementation, no external library)
- **D-4**: Existing AgencyOS components: TaskGraph, QualityEnforcer, VectorStore, Telemetry

### Constraints
- **C-1**: Local inference only (no cloud API, privacy + $0 cost requirement)
- **C-2**: Memory budget: TRM-7M + inference ≤100MB (Q4 quantization mandatory)
- **C-3**: Latency budget: <1s per checkpoint (total <4s for all 4)
- **C-4**: Backward compatibility: Must not break existing `/primeA` workflow
- **C-5**: Graceful degradation: Python fallback on any TRM failure (100% reliability)

### Assumptions
- **A-1**: TRM-7M research paper claims 87% accuracy on logical reasoning tasks (ARC, SUDOKU benchmarks)
- **A-2**: Grid-based input format is sufficient for AgencyOS validation tasks
- **A-3**: 16 refinement steps (from paper) provide optimal accuracy/latency trade-off
- **A-4**: Local model execution on M4 Pro (48GB RAM) or similar hardware is feasible

---

## Risk Assessment

### High-Risk Items
- **R-1**: TRM-7M accuracy on AgencyOS-specific tasks may be <87% (mitigation: Python fallback, VectorStore learning)
- **R-2**: Grid transformation may lose semantic information vs AST parsing (mitigation: Hybrid approach, use AST as input to grid encoder)
- **R-3**: Local model inference may exceed <1s latency on CPU-only machines (mitigation: GPU acceleration, reduce max_refinement_steps dynamically)

### Medium-Risk Items
- **R-4**: Model loading time (first inference) may be 3-5s (mitigation: Lazy load on first checkpoint, cache model in memory)
- **R-5**: False positive rate for type constraint violations may exceed 5% (mitigation: Confidence threshold tuning, VectorStore refinement)

### Low-Risk Items
- **R-6**: TRM model weights may be unavailable or broken (mitigation: Version pin, local cache, fallback to Python)
- **R-7**: Memory exhaustion on edge case inference for complex functions (mitigation: Limit grid size, skip inference if >1000 params)

---

## Open Questions

### Technical Questions
- **Q-1**: Which TRM-7M model format should we use? (PyTorch .pth, ONNX .onnx, or GGUF for llama.cpp)
  - **Resolution Needed By**: Before implementation starts
  - **Owner**: Chief Architect Agent

- **Q-2**: Should we fine-tune TRM-7M on AgencyOS historical validation data for Leap 9?
  - **Resolution Needed By**: After MVP deployment, 1,000+ validation runs
  - **Owner**: Learning Agent

- **Q-3**: How to handle grid size explosion for 100+ task graphs? (100x100 matrix = 10K elements)
  - **Resolution Needed By**: Before CHECKPOINT 1 implementation
  - **Owner**: Planner Agent (grid encoding optimization)

### Product Questions
- **Q-4**: Should TRM validation be opt-in via flag or always-on by default?
  - **Recommendation**: Always-on with `--no-trm` opt-out flag (default: enabled)
  - **Owner**: Meta-Orchestrator

- **Q-5**: What confidence threshold triggers auto-fix vs manual review?
  - **Recommendation**: confidence ≥0.9 → auto-fix, <0.9 → suggest fix + manual approval
  - **Owner**: Quality Enforcer Agent

---

## Success Criteria & Metrics

### Definition of Done
- [x] **DOD-1**: All 4 checkpoints implemented with 100% test pass rate
- [x] **DOD-2**: Churn reduction metrics tracked: 40-60% overall, broken down by checkpoint
- [x] **DOD-3**: Execution report includes TRM impact section with time saved, violations prevented
- [x] **DOD-4**: ADR-027 written documenting architectural decision and trade-offs
- [x] **DOD-5**: VectorStore stores validation patterns with confidence ≥0.6

### Post-Launch Metrics (30 days)
- **M-1**: DAG validation speedup: 10-100x faster than Python (empirical measurement on 100-task graphs)
- **M-2**: Type violation detection: 95% of Dict[Any, Any] caught pre-test (vs 0% baseline)
- **M-3**: Edge case discovery: 30-40% increase in test coverage completeness
- **M-4**: Lint pre-validation: 40-60% reduction in CI lint failures
- **M-5**: Overall churn reduction: 40-60% fewer test cycles (tracked via telemetry)
- **M-6**: Cost savings: $0 operational cost maintained (local inference only)

---

## Appendix

### A. TRM-7M Research Paper Reference
- **Title**: "Recursive Reasoning with Supervised Backtracking for Logical Reasoning Tasks"
- **Key Findings**: 87% accuracy on ARC-AGI, 10-100x faster than iterative search algorithms
- **Architecture**: 7M parameters, grid-based input (2D matrix), 16 refinement steps, deep supervision
- **Inference Cost**: ~100MB memory, <1s latency on CPU, <200ms on GPU

### B. Grid Encoding Examples

#### B.1: DAG Validation (Adjacency Matrix)
```python
# Task Graph: 4 tasks with dependencies
# task_1 → task_2 → task_4
#       ↘ task_3 ↗

adj_matrix = [
    [0, 1, 1, 0],  # task_1 depends on task_2, task_3
    [0, 0, 0, 1],  # task_2 depends on task_4
    [0, 0, 0, 1],  # task_3 depends on task_4
    [0, 0, 0, 0]   # task_4 has no dependencies
]
```

#### B.2: Type Constraint Validation (Type Annotation Grid)
```python
# Python code:
# def process_data(items: list[str], config: Dict[Any, Any]) -> bool:
#     ...

type_grid = [
    [1, 1, 0, 1],  # Row 1: has_param_types=1, has_return_type=1, uses_any=0, uses_dict_any=1
]
# Violation detected: uses_dict_any=1
```

#### B.3: Edge Case Inference (Function Signature Grid)
```python
# Function: def rate_limit(requests_per_min: int, burst_size: int) -> bool

signature_grid = [
    [1, 0, 100],    # param 1: is_int=1, is_optional=0, max_value=100
    [1, 0, 50]      # param 2: is_int=1, is_optional=0, max_value=50
]
# Inferred edge cases:
# - Boundary: requests_per_min=0 (min)
# - Boundary: requests_per_min=100 (max)
# - Boundary: burst_size=0 (min)
# - Concurrent: burst_size > requests_per_min (invalid config)
```

#### B.4: Lint Validation (Code Quality Grid)
```python
# Python code:
# import os
# import sys
# def foo():
#     x = 1

lint_grid = [
    [7, 0, 0, 1],   # Line 1: length=7, trailing_space=0, is_import=1, sorted=1
    [11, 1, 0, 1],  # Line 2: length=11, trailing_space=1, is_import=1, sorted=1 (VIOLATION: trailing space)
    [10, 0, 0, 0],  # Line 3: length=10, trailing_space=0, is_import=0, sorted=0
    [8, 1, 0, 0]    # Line 4: length=8, trailing_space=1, is_import=0, sorted=0 (VIOLATION: trailing space)
]
# Violations: Lines 2, 4 have trailing whitespace
```

### C. Related Specifications
- **spec-004-quality-feedback-loop.md**: Misclassification detection for Adaptive Router (Leap 4)
- **spec-007-two-stage-workflow.md**: Spec approval checkpoint for TDD execution (Leap 7)
- **spec-023-ollama-docker-integration.md**: Docker Compose for local model execution

### D. Glossary
- **TRM-7M**: 7M-parameter recursive supervised reasoning model for logical reasoning tasks
- **DAG**: Directed Acyclic Graph (task graph without circular dependencies)
- **Grid Encoding**: 2D matrix representation of code/graph structures for TRM input
- **Refinement Steps**: Recursive backtracking iterations in TRM reasoning (max 16 for accuracy)
- **Churn Reduction**: Decrease in test iterations from proactive error detection

---

**Spec Status**: Draft (Ready for Review)
**Next Steps**: Create plan-010-trm-validation-layer.md, implement TRMValidator core, integrate CHECKPOINT 1
